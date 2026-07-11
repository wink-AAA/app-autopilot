"""Unit tests for the matching / filtering rule engine."""

import pytest

from app_autopilot.rules.matcher import (
    MatchLogic,
    MatchOperator,
    Matcher,
    Rule,
    RuleSet,
)


class TestRule:
    """Tests for individual Rule evaluation."""

    def test_equals(self) -> None:
        r = Rule(field="city", operator=MatchOperator.EQUALS, value="Shanghai")
        assert r.match({"city": "Shanghai"}) is True
        assert r.match({"city": "Beijing"}) is False

    def test_not_equals(self) -> None:
        r = Rule(field="city", operator=MatchOperator.NOT_EQUALS, value="Shanghai")
        assert r.match({"city": "Beijing"}) is True
        assert r.match({"city": "Shanghai"}) is False

    def test_contains(self) -> None:
        r = Rule(field="title", operator=MatchOperator.CONTAINS, value="engineer")
        assert r.match({"title": "Senior Backend Engineer"}) is True
        assert r.match({"title": "Product Manager"}) is False

    def test_contains_case_insensitive(self) -> None:
        r = Rule(field="title", operator=MatchOperator.CONTAINS, value="ENGINEER")
        assert r.match({"title": "backend engineer"}) is True

    def test_not_contains(self) -> None:
        r = Rule(field="title", operator=MatchOperator.NOT_CONTAINS, value="intern")
        assert r.match({"title": "Engineer"}) is True
        assert r.match({"title": "Engineering Intern"}) is False

    def test_starts_with(self) -> None:
        r = Rule(field="company", operator=MatchOperator.STARTS_WITH, value="acme")
        assert r.match({"company": "Acme Corp"}) is True
        assert r.match({"company": "The Acme Corp"}) is False

    def test_ends_with(self) -> None:
        r = Rule(field="email", operator=MatchOperator.ENDS_WITH, value="@example.com")
        assert r.match({"email": "user@example.com"}) is True
        assert r.match({"email": "user@other.com"}) is False

    def test_regex(self) -> None:
        r = Rule(field="salary", operator=MatchOperator.REGEX, value=r"^\d{4,5}$")
        assert r.match({"salary": "10000"}) is True
        assert r.match({"salary": "abc"}) is False

    def test_in_list(self) -> None:
        r = Rule(field="city", operator=MatchOperator.IN, value=["Shanghai", "Beijing"])
        assert r.match({"city": "Shanghai"}) is True
        assert r.match({"city": "Guangzhou"}) is False

    def test_not_in_list(self) -> None:
        r = Rule(field="city", operator=MatchOperator.NOT_IN, value=["Remote", "Unknown"])
        assert r.match({"city": "Shanghai"}) is True
        assert r.match({"city": "Remote"}) is False

    def test_gt(self) -> None:
        r = Rule(field="salary", operator=MatchOperator.GT, value=8000)
        assert r.match({"salary": 10000}) is True
        assert r.match({"salary": 8000}) is False

    def test_gte(self) -> None:
        r = Rule(field="salary", operator=MatchOperator.GTE, value=8000)
        assert r.match({"salary": 8000}) is True
        assert r.match({"salary": 7999}) is False

    def test_lt(self) -> None:
        r = Rule(field="exp", operator=MatchOperator.LT, value=5)
        assert r.match({"exp": 3}) is True
        assert r.match({"exp": 5}) is False

    def test_lte(self) -> None:
        r = Rule(field="exp", operator=MatchOperator.LTE, value=5)
        assert r.match({"exp": 5}) is True
        assert r.match({"exp": 6}) is False

    def test_exists(self) -> None:
        r = Rule(field="phone", operator=MatchOperator.EXISTS)
        assert r.match({"phone": "123"}) is True
        assert r.match({"name": "Alice"}) is False

    def test_missing_field(self) -> None:
        r = Rule(field="city", operator=MatchOperator.EQUALS, value="Shanghai")
        assert r.match({"name": "Alice"}) is False


class TestRuleSet:
    """Tests for RuleSet with AND/OR logic."""

    def test_and_logic_all_pass(self) -> None:
        rs = RuleSet(logic=MatchLogic.AND)
        rs.add_rule(Rule(field="city", operator=MatchOperator.EQUALS, value="Shanghai"))
        rs.add_rule(Rule(field="salary", operator=MatchOperator.GTE, value=8000))
        assert rs.match({"city": "Shanghai", "salary": 10000}) is True

    def test_and_logic_one_fails(self) -> None:
        rs = RuleSet(logic=MatchLogic.AND)
        rs.add_rule(Rule(field="city", operator=MatchOperator.EQUALS, value="Shanghai"))
        rs.add_rule(Rule(field="salary", operator=MatchOperator.GTE, value=8000))
        assert rs.match({"city": "Shanghai", "salary": 5000}) is False

    def test_or_logic_one_passes(self) -> None:
        rs = RuleSet(logic=MatchLogic.OR)
        rs.add_rule(Rule(field="city", operator=MatchOperator.EQUALS, value="Shanghai"))
        rs.add_rule(Rule(field="city", operator=MatchOperator.EQUALS, value="Beijing"))
        assert rs.match({"city": "Beijing"}) is True

    def test_or_logic_none_pass(self) -> None:
        rs = RuleSet(logic=MatchLogic.OR)
        rs.add_rule(Rule(field="city", operator=MatchOperator.EQUALS, value="Shanghai"))
        rs.add_rule(Rule(field="city", operator=MatchOperator.EQUALS, value="Beijing"))
        assert rs.match({"city": "Guangzhou"}) is False

    def test_empty_ruleset_matches_all(self) -> None:
        rs = RuleSet()
        assert rs.match({"anything": "value"}) is True

    def test_custom_predicate(self) -> None:
        rs = RuleSet()
        rs.add_predicate(lambda d: d.get("score", 0) > 50, label="high_score")
        assert rs.match({"score": 60}) is True
        assert rs.match({"score": 40}) is False


class TestMatcher:
    """Tests for the high-level Matcher."""

    def test_include_filter(self) -> None:
        matcher = Matcher()
        rs = RuleSet()
        rs.add_rule(Rule(field="city", operator=MatchOperator.EQUALS, value="Shanghai"))
        matcher.add_filter("shanghai_only", rs, mode="include")

        items = [
            {"name": "A", "city": "Shanghai"},
            {"name": "B", "city": "Beijing"},
            {"name": "C", "city": "Shanghai"},
        ]
        result = matcher.apply(items)
        assert len(result) == 2
        assert all(i["city"] == "Shanghai" for i in result)

    def test_exclude_filter(self) -> None:
        matcher = Matcher()
        rs = RuleSet()
        rs.add_rule(Rule(field="status", operator=MatchOperator.EQUALS, value="blocked"))
        matcher.add_filter("no_blocked", rs, mode="exclude")

        items = [
            {"name": "A", "status": "active"},
            {"name": "B", "status": "blocked"},
        ]
        result = matcher.apply(items)
        assert len(result) == 1
        assert result[0]["name"] == "A"

    def test_combined_filters(self) -> None:
        matcher = Matcher()

        rs_include = RuleSet()
        rs_include.add_rule(Rule(field="city", operator=MatchOperator.EQUALS, value="Shanghai"))
        matcher.add_filter("shanghai", rs_include, mode="include")

        rs_exclude = RuleSet()
        rs_exclude.add_rule(Rule(field="salary", operator=MatchOperator.LT, value=8000))
        matcher.add_filter("low_salary", rs_exclude, mode="exclude")

        items = [
            {"name": "A", "city": "Shanghai", "salary": 10000},
            {"name": "B", "city": "Shanghai", "salary": 5000},
            {"name": "C", "city": "Beijing", "salary": 15000},
        ]
        result = matcher.apply(items)
        assert len(result) == 1
        assert result[0]["name"] == "A"

    def test_match_item(self) -> None:
        matcher = Matcher()
        rs = RuleSet()
        rs.add_rule(Rule(field="city", operator=MatchOperator.EQUALS, value="Shanghai"))
        matcher.add_filter("shanghai", rs, mode="include")
        assert matcher.match_item({"city": "Shanghai"}) is True
        assert matcher.match_item({"city": "Beijing"}) is False

    def test_invalid_mode(self) -> None:
        matcher = Matcher()
        rs = RuleSet()
        with pytest.raises(ValueError, match="mode must be"):
            matcher.add_filter("bad", rs, mode="invalid")
