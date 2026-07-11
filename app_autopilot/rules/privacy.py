"""Privacy protection rules: information isolation, sensitive-data masking, and persona management.

This module ensures that:
- Sensitive personal information is never leaked in automated messages.
- Different personas can be maintained for different platforms.
- Content is automatically checked and sanitized before being sent.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class Persona:
    """An identity persona for use on a specific platform or context.

    Attributes:
        name: Display name for this persona.
        title: Job title or role description.
        bio: Short biography / introduction text.
        platform: Which platform this persona is intended for.
        extra_fields: Arbitrary additional fields (e.g. avatar_url).
    """

    name: str
    title: str = ""
    bio: str = ""
    platform: str = ""
    extra_fields: Dict[str, str] = field(default_factory=dict)


@dataclass
class IsolationRule:
    """A rule that prevents specific information from appearing in certain contexts.

    Attributes:
        field_name: The data field to protect (e.g. "real_name", "phone").
        contexts: List of contexts where this field must NOT appear
                  (e.g. "job_application", "social_post").
        replacement: What to substitute if the field is detected.
    """

    field_name: str
    contexts: List[str]
    replacement: str = "[REDACTED]"


class PrivacyGuard:
    """Privacy protection engine.

    Example::

        guard = PrivacyGuard()
        guard.add_persona(Persona(name="Alex", title="Developer"), context="job_board")
        guard.add_sensitive_field("real_name", "John Doe")
        guard.add_sensitive_field("phone", "13800000000")
        guard.add_isolation_rule(IsolationRule(
            field_name="phone",
            contexts=["job_application"],
            replacement="via email only",
        ))

        safe_text = guard.sanitize("Call me at 13800000000", context="job_application")
        # => "Call me at [PHONE_REMOVED]"
    """

    def __init__(self) -> None:
        self._personas: Dict[str, Persona] = {}
        self._sensitive_fields: Dict[str, str] = {}  # field_name -> value
        self._blocked_keywords: List[str] = []
        self._isolation_rules: List[IsolationRule] = []

    # -- persona management -------------------------------------------------

    def add_persona(self, persona: Persona, context: str = "") -> None:
        """Register a persona for a given context (or platform)."""
        key = context or persona.platform or "default"
        self._personas[key] = persona

    def get_persona(self, context: str) -> Optional[Persona]:
        """Retrieve the persona for a context."""
        return self._personas.get(context) or self._personas.get("default")

    # -- sensitive data management ------------------------------------------

    def add_sensitive_field(self, field_name: str, value: str) -> None:
        """Register a sensitive field value that must be masked."""
        self._sensitive_fields[field_name] = value

    def add_blocked_keyword(self, keyword: str) -> None:
        """Add a keyword that should be filtered from outgoing messages."""
        self._blocked_keywords.append(keyword)

    def add_isolation_rule(self, rule: IsolationRule) -> None:
        """Add an information-isolation rule."""
        self._isolation_rules.append(rule)

    # -- sanitization -------------------------------------------------------

    def sanitize(self, text: str, context: str = "") -> str:
        """Sanitize text by masking sensitive data and applying isolation rules.

        Args:
            text: The raw text to sanitize.
            context: The current context (e.g. "job_application").

        Returns:
            Sanitized text with sensitive data masked.
        """
        result = text

        # 1. Mask sensitive field values
        for field_name, value in self._sensitive_fields.items():
            if value and value in result:
                tag = f"[{field_name.upper()}_REMOVED]"
                result = result.replace(value, tag)

        # 2. Apply isolation rules for the current context
        for rule in self._isolation_rules:
            if context and context not in rule.contexts:
                continue
            # If the field has a known value, replace it
            field_value = self._sensitive_fields.get(rule.field_name, "")
            if field_value and field_value in result:
                result = result.replace(field_value, rule.replacement)

        # 3. Filter blocked keywords
        for keyword in self._blocked_keywords:
            if keyword.lower() in result.lower():
                # Case-insensitive replacement
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                result = pattern.sub("[FILTERED]", result)

        return result

    def check(self, text: str, context: str = "") -> List[str]:
        """Check text for privacy violations without modifying it.

        Returns:
            A list of violation descriptions.  Empty list means no violations.
        """
        violations: List[str] = []

        for field_name, value in self._sensitive_fields.items():
            if value and value in text:
                violations.append(
                    f"Sensitive field '{field_name}' detected in text."
                )

        for rule in self._isolation_rules:
            if context and context not in rule.contexts:
                continue
            field_value = self._sensitive_fields.get(rule.field_name, "")
            if field_value and field_value in text:
                violations.append(
                    f"Isolation violation: '{rule.field_name}' exposed in context '{context}'."
                )

        for keyword in self._blocked_keywords:
            if keyword.lower() in text.lower():
                violations.append(f"Blocked keyword '{keyword}' found in text.")

        return violations

    def is_safe(self, text: str, context: str = "") -> bool:
        """Quick check whether text is free of privacy violations."""
        return len(self.check(text, context)) == 0
