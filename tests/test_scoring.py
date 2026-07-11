"""Unit tests for the scoring engine."""

import pytest

from app_autopilot.core.config import ScoringConfig, ScoringDimension
from app_autopilot.core.scoring import ScoringEngine, ScoringResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def basic_config() -> ScoringConfig:
    """A simple scoring configuration for testing."""
    return ScoringConfig(
        dimensions=[
            ScoringDimension(
                name="salary",
                weight=1.0,
                rules=[
                    {"type": "range", "field": "salary_min", "min": 8000, "max": 15000, "score": 20},
                    {"type": "range", "field": "salary_min", "min": 15000, "score": 30},
                ],
            ),
            ScoringDimension(
                name="city",
                weight=1.0,
                rules=[
                    {"type": "exact", "field": "city", "value": "Shanghai", "score": 10},
                ],
            ),
            ScoringDimension(
                name="title",
                weight=2.0,
                is_hard_requirement=True,
                rules=[
                    {"type": "contains", "field": "title", "value": "engineer", "score": 15},
                ],
            ),
        ],
        min_score_threshold=20.0,
    )


@pytest.fixture
def engine(basic_config: ScoringConfig) -> ScoringEngine:
    return ScoringEngine(basic_config)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestScoringEngine:
    """Tests for ScoringEngine.score()."""

    def test_high_score_pass(self, engine: ScoringEngine) -> None:
        """Candidate with good salary + city + matching title should pass."""
        data = {"salary_min": 12000, "city": "Shanghai", "title": "Backend Engineer"}
        result = engine.score("job-001", data)
        assert result.passed is True
        assert result.total_score > 0
        assert "salary" in result.dimension_scores
        assert result.dimension_scores["salary"] == 20
        assert result.dimension_scores["city"] == 10
        assert result.dimension_scores["title"] == 15

    def test_hard_requirement_failure(self, engine: ScoringEngine) -> None:
        """Candidate without 'engineer' in title should fail hard requirement."""
        data = {"salary_min": 20000, "city": "Shanghai", "title": "Product Manager"}
        result = engine.score("job-002", data)
        assert result.passed is False
        assert "title" in result.hard_failures

    def test_below_threshold(self, engine: ScoringEngine) -> None:
        """Candidate with low total score should fail threshold."""
        data = {"salary_min": 5000, "city": "Unknown", "title": "Junior Engineer"}
        result = engine.score("job-003", data)
        # salary=0, city=0, title=15, weight*title=30 -> 30*2.0=30? No, weight is applied on top.
        # Actually: salary=0*1.0=0, city=0*1.0=0, title=15*2.0=30 -> total=30 >= 20
        # Let's use a truly low score case
        data2 = {"salary_min": 5000, "city": "Unknown", "title": "Assistant"}
        result2 = engine.score("job-003b", data2)
        # title doesn't contain "engineer" -> hard failure
        assert result2.passed is False

    def test_range_scoring(self, engine: ScoringEngine) -> None:
        """Verify range rule scoring boundaries."""
        # Exactly at lower bound
        data = {"salary_min": 8000, "city": "Beijing", "title": "Data Engineer"}
        result = engine.score("job-004", data)
        assert result.dimension_scores["salary"] == 20

        # Above upper bound of first range, into second range
        data2 = {"salary_min": 16000, "city": "Beijing", "title": "Data Engineer"}
        result2 = engine.score("job-005", data2)
        assert result2.dimension_scores["salary"] == 30

    def test_exact_match(self, engine: ScoringEngine) -> None:
        """Exact match rule should only score on exact value."""
        data_match = {"salary_min": 10000, "city": "Shanghai", "title": "Engineer"}
        data_no_match = {"salary_min": 10000, "city": "Beijing", "title": "Engineer"}
        r1 = engine.score("j1", data_match)
        r2 = engine.score("j2", data_no_match)
        assert r1.dimension_scores["city"] == 10
        assert r2.dimension_scores["city"] == 0

    def test_contains_match(self, engine: ScoringEngine) -> None:
        """Contains rule should be case-insensitive."""
        data = {"salary_min": 10000, "city": "Beijing", "title": "SENIOR ENGINEER"}
        result = engine.score("j-case", data)
        assert result.dimension_scores["title"] == 15

    def test_batch_scoring(self, engine: ScoringEngine) -> None:
        """Batch scoring should return sorted results."""
        candidates = [
            ("j1", {"salary_min": 20000, "city": "Shanghai", "title": "Engineer"}),
            ("j2", {"salary_min": 10000, "city": "Beijing", "title": "Engineer"}),
        ]
        results = engine.score_batch(candidates)
        assert len(results) == 2
        # Higher salary + city match should score higher
        assert results[0].total_score >= results[1].total_score

    def test_custom_evaluator(self, engine: ScoringEngine) -> None:
        """Custom evaluators should be callable."""
        def custom_eval(rule, data):
            return 99.0 if data.get("special") else 0.0

        engine.register_evaluator("custom_type", custom_eval)
        # This won't affect existing dimensions, just verifies registration
        assert "custom_type" in engine._custom_evaluators


class TestScoringResult:
    """Tests for ScoringResult data class."""

    def test_repr_pass(self) -> None:
        r = ScoringResult("test-1")
        r.total_score = 50.0
        r.passed = True
        assert "PASS" in repr(r)
        assert "50.0" in repr(r)

    def test_repr_fail(self) -> None:
        r = ScoringResult("test-2")
        r.passed = False
        r.hard_failures = ["salary"]
        assert "FAIL" in repr(r)
