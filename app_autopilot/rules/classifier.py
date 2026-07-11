"""Message classifier based on keywords and configurable rules.

Classifies incoming messages into categories, each of which can trigger
a specific action (notify, auto-reply, ignore, etc.).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


class Action(str, Enum):
    """Action to take when a message is classified."""

    NOTIFY = "notify"
    AUTO_REPLY = "auto_reply"
    IGNORE = "ignore"
    FLAG = "flag"
    FORWARD = "forward"


@dataclass
class ClassificationRule:
    """A rule that maps patterns to a message category.

    Attributes:
        category: The classification label (e.g. "interview_request").
        keywords: List of keywords to look for (case-insensitive).
        patterns: List of regex patterns to test.
        action: The action to trigger when matched.
        priority: Higher priority rules are checked first.
        reply_template: Optional template for auto-reply messages.
    """

    category: str
    keywords: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    action: Action = Action.NOTIFY
    priority: int = 0
    reply_template: str = ""

    def matches(self, text: str) -> bool:
        """Check if the given text matches this classification rule."""
        text_lower = text.lower()

        # Keyword matching (any keyword matches)
        for kw in self.keywords:
            if kw.lower() in text_lower:
                return True

        # Regex pattern matching
        for pattern in self.patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False


@dataclass
class ClassificationResult:
    """Result of classifying a message."""

    category: str
    action: Action
    confidence: float = 1.0
    matched_rule: Optional[ClassificationRule] = None
    reply_text: str = ""


class MessageClassifier:
    """Configurable message classifier.

    Example::

        classifier = MessageClassifier()
        classifier.add_rule(ClassificationRule(
            category="interview_request",
            keywords=["interview", "meeting", "schedule"],
            action=Action.NOTIFY,
        ))
        classifier.add_rule(ClassificationRule(
            category="resume_request",
            keywords=["resume", "CV", "portfolio"],
            action=Action.AUTO_REPLY,
            reply_template="Thank you! I'll send my resume shortly.",
        ))

        result = classifier.classify("Would you like to schedule an interview?")
        assert result.category == "interview_request"
    """

    def __init__(self) -> None:
        self._rules: List[ClassificationRule] = []
        self._custom_classifiers: List[Callable[[str], Optional[ClassificationResult]]] = []

    def add_rule(self, rule: ClassificationRule) -> None:
        """Add a classification rule."""
        self._rules.append(rule)
        # Keep sorted by priority (descending)
        self._rules.sort(key=lambda r: r.priority, reverse=True)

    def remove_rules_for_category(self, category: str) -> int:
        """Remove all rules for a given category.

        Returns:
            Number of rules removed.
        """
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.category != category]
        return before - len(self._rules)

    def add_custom_classifier(
        self, func: Callable[[str], Optional[ClassificationResult]]
    ) -> None:
        """Register a custom classifier function.

        The function receives the message text and should return a
        ``ClassificationResult`` or ``None`` if it cannot classify.
        """
        self._custom_classifiers.append(func)

    def classify(self, text: str) -> Optional[ClassificationResult]:
        """Classify a message.

        Tries custom classifiers first (in registration order), then
        built-in rules (in priority order).

        Returns:
            The first matching ``ClassificationResult``, or ``None``.
        """
        # Try custom classifiers first
        for custom_fn in self._custom_classifiers:
            result = custom_fn(text)
            if result is not None:
                return result

        # Try built-in rules (sorted by priority)
        for rule in self._rules:
            if rule.matches(text):
                return ClassificationResult(
                    category=rule.category,
                    action=rule.action,
                    confidence=1.0,
                    matched_rule=rule,
                    reply_text=rule.reply_template,
                )

        return None

    def classify_all(self, text: str) -> List[ClassificationResult]:
        """Return ALL matching classifications (not just the first).

        Useful when a message can belong to multiple categories.
        """
        results: List[ClassificationResult] = []

        for custom_fn in self._custom_classifiers:
            result = custom_fn(text)
            if result is not None:
                results.append(result)

        for rule in self._rules:
            if rule.matches(text):
                results.append(ClassificationResult(
                    category=rule.category,
                    action=rule.action,
                    confidence=1.0,
                    matched_rule=rule,
                    reply_text=rule.reply_template,
                ))

        return results

    def get_categories(self) -> Set[str]:
        """Return all configured category names."""
        return {r.category for r in self._rules}
