"""Generic multi-dimensional weighted scoring engine.

The scoring engine evaluates candidates (jobs, posts, contacts, etc.)
against a configurable set of dimensions.  Each dimension carries a weight
and a list of rules.  Hard-requirement dimensions act as gate-filters:
failing one immediately disqualifies the candidate regardless of other scores.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from app_autopilot.core.config import ScoringConfig, ScoringDimension


class ScoringResult:
    """Outcome of scoring a single candidate."""

    def __init__(self, candidate_id: str) -> None:
        self.candidate_id: str = candidate_id
        self.dimension_scores: Dict[str, float] = {}
        self.hard_failures: List[str] = []
        self.total_score: float = 0.0
        self.passed: bool = True

    def __repr__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return (
            f"ScoringResult(id={self.candidate_id!r}, score={self.total_score:.1f}, "
            f"status={status}, hard_failures={self.hard_failures})"
        )


class ScoringEngine:
    """Configurable multi-dimensional weighted scoring engine.

    Example::

        config = ScoringConfig(
            dimensions=[
                ScoringDimension(
                    name="salary",
                    weight=1.0,
                    rules=[{"type": "range", "field": "salary_min", "min": 8000, "score": 20}],
                ),
                ScoringDimension(
                    name="location",
                    weight=1.0,
                    rules=[{"type": "exact", "field": "city", "value": "Shanghai", "score": 10}],
                    is_hard_requirement=False,
                ),
            ],
            min_score_threshold=30.0,
        )
        engine = ScoringEngine(config)
        result = engine.score("job-001", {"salary_min": 10000, "city": "Shanghai"})
    """

    # Built-in rule evaluators keyed by rule ``type``
    _builtin_evaluators: Dict[str, Callable[..., float]] = {}

    def __init__(self, config: ScoringConfig) -> None:
        self.config = config
        self._custom_evaluators: Dict[str, Callable[..., float]] = {}

    # -- public API ---------------------------------------------------------

    def score(self, candidate_id: str, data: Dict[str, Any]) -> ScoringResult:
        """Score a single candidate against all configured dimensions.

        Args:
            candidate_id: Unique identifier for the candidate.
            data: Arbitrary key-value data describing the candidate.

        Returns:
            A ``ScoringResult`` with per-dimension scores and pass/fail status.
        """
        result = ScoringResult(candidate_id)

        for dim in self.config.dimensions:
            dim_score = self._evaluate_dimension(dim, data)

            # Hard-requirement check: score of 0 on a hard dimension = fail
            if dim.is_hard_requirement and dim_score <= 0:
                result.hard_failures.append(dim.name)
                result.passed = False

            result.dimension_scores[dim.name] = dim_score
            result.total_score += dim_score * dim.weight

        # Final threshold check (only if no hard failures)
        if result.passed and result.total_score < self.config.min_score_threshold:
            result.passed = False

        return result

    def score_batch(
        self, candidates: List[Tuple[str, Dict[str, Any]]]
    ) -> List[ScoringResult]:
        """Score multiple candidates and return results sorted by total score (descending)."""
        results = [self.score(cid, data) for cid, data in candidates]
        results.sort(key=lambda r: r.total_score, reverse=True)
        return results

    def register_evaluator(self, rule_type: str, func: Callable[..., float]) -> None:
        """Register a custom rule evaluator function.

        Args:
            rule_type: The ``type`` string used in rule definitions.
            func: A callable ``(rule_dict, candidate_data) -> float``.
        """
        self._custom_evaluators[rule_type] = func

    # -- internal -----------------------------------------------------------

    def _evaluate_dimension(self, dim: ScoringDimension, data: Dict[str, Any]) -> float:
        """Sum up scores from all rules in a dimension."""
        total = 0.0
        for rule in dim.rules:
            rule_type = rule.get("type", "")
            evaluator = self._resolve_evaluator(rule_type)
            if evaluator is not None:
                total += evaluator(rule, data)
        return total

    def _resolve_evaluator(self, rule_type: str) -> Optional[Callable[..., float]]:
        """Look up an evaluator by rule type (custom first, then built-in)."""
        if rule_type in self._custom_evaluators:
            return self._custom_evaluators[rule_type]
        return _BUILTIN_EVALUATORS.get(rule_type)


# ---------------------------------------------------------------------------
# Built-in rule evaluators
# ---------------------------------------------------------------------------

def _eval_exact(rule: Dict[str, Any], data: Dict[str, Any]) -> float:
    """Exact-match rule: field value equals expected value."""
    field = rule.get("field", "")
    expected = rule.get("value")
    score = float(rule.get("score", 0))
    if data.get(field) == expected:
        return score
    return 0.0


def _eval_range(rule: Dict[str, Any], data: Dict[str, Any]) -> float:
    """Range rule: numeric field falls within [min, max]."""
    field = rule.get("field", "")
    value = data.get(field)
    if value is None:
        return 0.0
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.0
    lo = rule.get("min", float("-inf"))
    hi = rule.get("max", float("inf"))
    score = float(rule.get("score", 0))
    if lo <= value <= hi:
        return score
    return 0.0


def _eval_contains(rule: Dict[str, Any], data: Dict[str, Any]) -> float:
    """Contains rule: string field contains a keyword (case-insensitive)."""
    field = rule.get("field", "")
    keyword = str(rule.get("value", "")).lower()
    score = float(rule.get("score", 0))
    field_value = str(data.get(field, "")).lower()
    if keyword and keyword in field_value:
        return score
    return 0.0


def _eval_regex(rule: Dict[str, Any], data: Dict[str, Any]) -> float:
    """Regex rule: string field matches a regular expression."""
    field = rule.get("field", "")
    pattern = rule.get("pattern", "")
    score = float(rule.get("score", 0))
    field_value = str(data.get(field, ""))
    if pattern and re.search(pattern, field_value):
        return score
    return 0.0


def _eval_in_list(rule: Dict[str, Any], data: Dict[str, Any]) -> float:
    """In-list rule: field value is in a specified list."""
    field = rule.get("field", "")
    allowed = rule.get("values", [])
    score = float(rule.get("score", 0))
    if data.get(field) in allowed:
        return score
    return 0.0


# Registry of built-in evaluators
_BUILTIN_EVALUATORS: Dict[str, Callable[..., float]] = {
    "exact": _eval_exact,
    "range": _eval_range,
    "contains": _eval_contains,
    "regex": _eval_regex,
    "in_list": _eval_in_list,
}
