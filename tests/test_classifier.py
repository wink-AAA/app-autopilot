"""Unit tests for the message classifier."""

import pytest

from app_autopilot.rules.classifier import (
    Action,
    ClassificationResult,
    ClassificationRule,
    MessageClassifier,
)


class TestClassificationRule:
    """Tests for individual ClassificationRule matching."""

    def test_keyword_match(self) -> None:
        rule = ClassificationRule(
            category="interview",
            keywords=["interview", "meeting"],
        )
        assert rule.matches("Can we schedule an interview?") is True
        assert rule.matches("Let's set up a meeting") is True
        assert rule.matches("What is your salary range?") is False

    def test_keyword_case_insensitive(self) -> None:
        rule = ClassificationRule(category="test", keywords=["Hello"])
        assert rule.matches("hello world") is True
        assert rule.matches("HELLO WORLD") is True

    def test_regex_match(self) -> None:
        rule = ClassificationRule(
            category="phone",
            patterns=[r"\d{3}[-.]?\d{4}"],
        )
        assert rule.matches("Call me at 123-4567") is True
        assert rule.matches("No number here") is False

    def test_combined_keywords_and_regex(self) -> None:
        rule = ClassificationRule(
            category="mixed",
            keywords=["urgent"],
            patterns=[r"ASAP"],
        )
        assert rule.matches("This is urgent") is True
        assert rule.matches("Please do this ASAP") is True
        assert rule.matches("Take your time") is False

    def test_no_patterns_no_keywords(self) -> None:
        rule = ClassificationRule(category="empty")
        assert rule.matches("anything") is False


class TestMessageClassifier:
    """Tests for MessageClassifier."""

    @pytest.fixture
    def classifier(self) -> MessageClassifier:
        c = MessageClassifier()
        c.add_rule(ClassificationRule(
            category="interview_request",
            keywords=["interview", "meeting", "schedule a call"],
            action=Action.NOTIFY,
            priority=10,
        ))
        c.add_rule(ClassificationRule(
            category="resume_request",
            keywords=["resume", "CV", "portfolio"],
            action=Action.AUTO_REPLY,
            priority=5,
            reply_template="Thank you! I'll send my resume shortly.",
        ))
        c.add_rule(ClassificationRule(
            category="salary_inquiry",
            keywords=["salary", "compensation", "pay range"],
            action=Action.IGNORE,
            priority=1,
        ))
        return c

    def test_classify_interview(self, classifier: MessageClassifier) -> None:
        result = classifier.classify("Would you like to schedule an interview?")
        assert result is not None
        assert result.category == "interview_request"
        assert result.action == Action.NOTIFY

    def test_classify_resume(self, classifier: MessageClassifier) -> None:
        result = classifier.classify("Could you send me your CV?")
        assert result is not None
        assert result.category == "resume_request"
        assert result.action == Action.AUTO_REPLY
        assert "resume" in result.reply_text.lower()

    def test_classify_salary(self, classifier: MessageClassifier) -> None:
        result = classifier.classify("What is your expected salary?")
        assert result is not None
        assert result.category == "salary_inquiry"
        assert result.action == Action.IGNORE

    def test_classify_no_match(self, classifier: MessageClassifier) -> None:
        result = classifier.classify("How is the weather today?")
        assert result is None

    def test_priority_ordering(self) -> None:
        """Higher priority rules should be checked first."""
        c = MessageClassifier()
        c.add_rule(ClassificationRule(
            category="low_priority",
            keywords=["hello"],
            priority=1,
        ))
        c.add_rule(ClassificationRule(
            category="high_priority",
            keywords=["hello"],
            priority=100,
        ))
        result = c.classify("hello there")
        assert result is not None
        assert result.category == "high_priority"

    def test_classify_all(self, classifier: MessageClassifier) -> None:
        """A message matching multiple rules should return all results."""
        result = classifier.classify_all("Send your resume and CV for the interview")
        categories = {r.category for r in result}
        assert "interview_request" in categories
        assert "resume_request" in categories

    def test_remove_rules_for_category(self, classifier: MessageClassifier) -> None:
        removed = classifier.remove_rules_for_category("salary_inquiry")
        assert removed == 1
        result = classifier.classify("What is your salary?")
        assert result is None

    def test_get_categories(self, classifier: MessageClassifier) -> None:
        cats = classifier.get_categories()
        assert "interview_request" in cats
        assert "resume_request" in cats
        assert "salary_inquiry" in cats

    def test_custom_classifier(self, classifier: MessageClassifier) -> None:
        def my_classifier(text: str):
            if "custom_trigger" in text:
                return ClassificationResult(
                    category="custom",
                    action=Action.FLAG,
                    confidence=0.99,
                )
            return None

        classifier.add_custom_classifier(my_classifier)
        result = classifier.classify("This has a custom_trigger word")
        assert result is not None
        assert result.category == "custom"
        assert result.action == Action.FLAG
