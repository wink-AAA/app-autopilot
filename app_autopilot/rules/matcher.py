"""Generic matching and filtering rule engine.

The matcher evaluates items against a set of configurable rules to determine
whether they should be included, excluded, or flagged.  Rules are composable
and can be combined with AND/OR logic.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


class MatchOperator(str, Enum):
    """Supported comparison operators for rule evaluation."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"
    IN = "in"
    NOT_IN = "not_in"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    EXISTS = "exists"


class MatchLogic(str, Enum):
    """Logical combinator for combining multiple rules."""

    AND = "and"
    OR = "or"


class Rule:
    """A single matching rule.

    Example::

        rule = Rule(field="city", operator=MatchOperator.EQUALS, value="Shanghai")
        assert rule.match({"city": "Shanghai"}) is True
    """

    def __init__(
        self,
        field: str,
        operator: MatchOperator,
        value: Any = None,
        label: str = "",
    ) -> None:
        self.field = field
        self.operator = operator
        self.value = value
        self.label = label or f"{field} {operator.value} {value}"

    def match(self, data: Dict[str, Any]) -> bool:
        """Evaluate this rule against the given data dict."""
        field_value = data.get(self.field)

        if self.operator == MatchOperator.EXISTS:
            return field_value is not None

        if field_value is None:
            return False

        op = self.operator

        if op == MatchOperator.EQUALS:
            return field_value == self.value
        if op == MatchOperator.NOT_EQUALS:
            return field_value != self.value
        if op == MatchOperator.CONTAINS:
            return str(self.value).lower() in str(field_value).lower()
        if op == MatchOperator.NOT_CONTAINS:
            return str(self.value).lower() not in str(field_value).lower()
        if op == MatchOperator.STARTS_WITH:
            return str(field_value).lower().startswith(str(self.value).lower())
        if op == MatchOperator.ENDS_WITH:
            return str(field_value).lower().endswith(str(self.value).lower())
        if op == MatchOperator.REGEX:
            return bool(re.search(str(self.value), str(field_value)))
        if op == MatchOperator.IN:
            return field_value in self.value
        if op == MatchOperator.NOT_IN:
            return field_value not in self.value
        if op == MatchOperator.GT:
            return float(field_value) > float(self.value)
        if op == MatchOperator.GTE:
            return float(field_value) >= float(self.value)
        if op == MatchOperator.LT:
            return float(field_value) < float(self.value)
        if op == MatchOperator.LTE:
            return float(field_value) <= float(self.value)

        return False


class RuleSet:
    """A composable collection of rules with AND/OR logic.

    Example::

        rules = RuleSet(logic=MatchLogic.AND)
        rules.add_rule(Rule(field="city", operator=MatchOperator.EQUALS, value="Shanghai"))
        rules.add_rule(Rule(field="salary_min", operator=MatchOperator.GTE, value=8000))
        assert rules.match({"city": "Shanghai", "salary_min": 10000}) is True
    """

    def __init__(self, logic: MatchLogic = MatchLogic.AND, label: str = "") -> None:
        self.logic = logic
        self.label = label
        self._rules: List[Rule] = []
        self._custom_predicates: List[Callable[[Dict[str, Any]], bool]] = []

    def add_rule(self, rule: Rule) -> None:
        """Add a rule to this set."""
        self._rules.append(rule)

    def add_predicate(self, func: Callable[[Dict[str, Any]], bool], label: str = "") -> None:
        """Add a custom predicate function.

        Args:
            func: A callable that takes a data dict and returns bool.
            label: Optional human-readable label.
        """
        self._custom_predicates.append(func)

    def match(self, data: Dict[str, Any]) -> bool:
        """Evaluate all rules according to the configured logic.

        Returns:
            ``True`` if the data matches according to AND/OR logic.
        """
        all_results: List[bool] = []

        for rule in self._rules:
            all_results.append(rule.match(data))

        for pred in self._custom_predicates:
            all_results.append(pred(data))

        if not all_results:
            return True  # Empty rule set matches everything

        if self.logic == MatchLogic.AND:
            return all(all_results)
        else:  # OR
            return any(all_results)


class Matcher:
    """High-level matcher that applies named RuleSets to filter items.

    Example::

        matcher = Matcher()
        matcher.add_filter("must_be_local", ruleset, mode="exclude")
        surviving = matcher.apply(items)
    """

    def __init__(self) -> None:
        self._filters: Dict[str, Dict[str, Any]] = {}

    def add_filter(
        self,
        name: str,
        ruleset: RuleSet,
        mode: str = "include",
    ) -> None:
        """Register a named filter.

        Args:
            name: Unique filter name.
            ruleset: The rule set to evaluate.
            mode: ``"include"`` keeps matching items; ``"exclude"`` removes them.
        """
        if mode not in ("include", "exclude"):
            raise ValueError(f"mode must be 'include' or 'exclude', got '{mode}'")
        self._filters[name] = {"ruleset": ruleset, "mode": mode}

    def remove_filter(self, name: str) -> None:
        """Remove a filter by name."""
        self._filters.pop(name, None)

    def apply(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply all registered filters to a list of items.

        Returns:
            The filtered list of items.
        """
        result = list(items)
        for name, filt in self._filters.items():
            ruleset: RuleSet = filt["ruleset"]
            mode: str = filt["mode"]
            if mode == "include":
                result = [item for item in result if ruleset.match(item)]
            else:  # exclude
                result = [item for item in result if not ruleset.match(item)]
        return result

    def match_item(self, item: Dict[str, Any]) -> bool:
        """Check whether a single item passes all filters."""
        for filt in self._filters.values():
            ruleset = filt["ruleset"]
            mode = filt["mode"]
            matched = ruleset.match(item)
            if mode == "include" and not matched:
                return False
            if mode == "exclude" and matched:
                return False
        return True
