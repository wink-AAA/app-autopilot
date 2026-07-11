"""Configuration loading and validation with YAML support and Pydantic models.

This module provides a hierarchical configuration system that supports:
- YAML-based configuration files
- Configuration inheritance (base -> scenario-specific)
- Schema validation with Pydantic
- Environment variable overrides
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Pydantic models for configuration schema
# ---------------------------------------------------------------------------

class ScoringDimension(BaseModel):
    """A single scoring dimension with weight and rules."""

    name: str = Field(..., description="Human-readable dimension name")
    weight: float = Field(..., ge=0.0, description="Weight multiplier for this dimension")
    rules: List[Dict[str, Any]] = Field(default_factory=list, description="Scoring rules")
    is_hard_requirement: bool = Field(
        default=False,
        description="If True, failing this dimension disqualifies the candidate immediately",
    )


class ScoringConfig(BaseModel):
    """Scoring engine configuration."""

    dimensions: List[ScoringDimension] = Field(default_factory=list)
    min_score_threshold: float = Field(default=0.0, description="Minimum total score to proceed")


class StateConfig(BaseModel):
    """State management configuration."""

    storage_path: str = Field(default="data/state.json", description="Path to the state JSON file")
    max_history_size: int = Field(default=10000, description="Maximum records to keep in state")


class NotificationRoute(BaseModel):
    """Routing rule mapping event types to notification channels."""

    event_type: str
    channel: str  # e.g. "email", "webhook"


class NotificationConfig(BaseModel):
    """Notification system configuration."""

    default_channel: str = Field(default="console")
    routes: List[NotificationRoute] = Field(default_factory=list)
    email: Optional[Dict[str, Any]] = None
    webhook: Optional[Dict[str, Any]] = None


class PrivacyConfig(BaseModel):
    """Privacy and information-isolation configuration."""

    persona_name: str = Field(default="User", description="Display name used in interactions")
    sensitive_fields: List[str] = Field(default_factory=list, description="Fields to mask")
    blocked_keywords: List[str] = Field(default_factory=list, description="Keywords to filter out")
    isolation_rules: List[Dict[str, Any]] = Field(default_factory=list)


class SchedulerConfig(BaseModel):
    """Scheduler configuration."""

    trigger_type: str = Field(default="interval", description="interval | cron | manual")
    interval_seconds: int = Field(default=3600)
    cron_expression: Optional[str] = None


class AdapterConfig(BaseModel):
    """Platform adapter configuration."""

    name: str
    module_path: str = Field(..., description="Dotted import path to the adapter class")
    options: Dict[str, Any] = Field(default_factory=dict)


class AppConfig(BaseModel):
    """Top-level application configuration."""

    app_name: str = Field(default="app-autopilot")
    log_level: str = Field(default="INFO")
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    state: StateConfig = Field(default_factory=StateConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    adapters: List[AdapterConfig] = Field(default_factory=list)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}, got '{v}'")
        return upper


# ---------------------------------------------------------------------------
# Configuration loader
# ---------------------------------------------------------------------------

def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge *override* into *base*, returning a new dict."""
    merged = base.copy()
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(
    config_path: str | Path,
    base_config_path: Optional[str | Path] = None,
    env_prefix: str = "APP_AUTOPILOT_",
) -> AppConfig:
    """Load and validate application configuration from YAML files.

    Args:
        config_path: Path to the primary YAML config file.
        base_config_path: Optional path to a base config that *config_path* inherits from.
        env_prefix: Prefix for environment variable overrides.

    Returns:
        A validated ``AppConfig`` instance.

    Raises:
        FileNotFoundError: If *config_path* does not exist.
        ValueError: If configuration validation fails.
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as fh:
        raw: Dict[str, Any] = yaml.safe_load(fh) or {}

    # Merge with base config if provided
    if base_config_path is not None:
        base_path = Path(base_config_path)
        if base_path.exists():
            with open(base_path, "r", encoding="utf-8") as fh:
                base_raw: Dict[str, Any] = yaml.safe_load(fh) or {}
            raw = _deep_merge(base_raw, raw)

    # Apply environment variable overrides (flat, top-level keys only)
    for env_key, env_value in os.environ.items():
        if env_key.startswith(env_prefix):
            config_key = env_key[len(env_prefix):].lower()
            raw[config_key] = env_value

    return AppConfig.model_validate(raw)


def load_config_from_dict(data: Dict[str, Any]) -> AppConfig:
    """Create a validated ``AppConfig`` from a plain dictionary.

    Useful for testing and programmatic configuration.
    """
    return AppConfig.model_validate(data)
