# App Autopilot

**A configurable framework for automating repetitive app operations — from job applications to social media management.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## What is App Autopilot?

App Autopilot is a **framework-level toolkit** that abstracts the common patterns behind repetitive app operations. Instead of writing one-off scripts for each platform, you define **adapters** and **rules** once, and the framework handles scoring, scheduling, state management, privacy, and notifications.

### Real-World Origins

This framework was abstracted from two production use cases:

1. **Job Board Auto-Application** — Browse job listings, score them against your preferences, auto-apply to high-scoring matches, and track application status.
2. **Social Media Auto-Management** — Post content on schedule, manage interactions, classify incoming messages, and maintain consistent personas across platforms.

> ⚠️ **Important:** App Autopilot is a **framework**. It does NOT include platform-specific automation code. You write the adapter for your target platform; the framework provides everything else.

---

## Features

- 🎯 **Multi-Dimensional Scoring Engine** — Configurable weighted scoring with hard requirements and bonus points
- 🔧 **Platform Adapter System** — Clean ABC interface for integrating any app or website
- 📋 **Rule-Based Filtering** — Composable AND/OR rule sets for matching and exclusion
- 💬 **Message Classification** — Keyword + regex based classifier with auto-reply support
- 🔒 **Privacy Protection** — Information isolation, sensitive data masking, persona management
- 📊 **State Management** — Lightweight JSON store with deduplication and exclusion lists
- 📅 **Flexible Scheduling** — Interval, cron, or manual trigger modes
- 📬 **Multi-Channel Notifications** — Email, webhook, and extensible notification routing
- 🔄 **Task Pipeline** — Multi-stage orchestrator with retries and fallbacks
- 📝 **YAML Configuration** — Hierarchical config with inheritance and validation

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      YAML Configuration                      │
│              (base.yaml → scenario.yaml)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     Scheduler                                │
│              (interval / cron / manual)                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Task Runner                                │
│         (multi-stage pipeline with retry/fallback)           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Scoring  │  │ Matcher  │  │Classifier│  │  Privacy  │  │
│  │ Engine   │  │ & Rules  │  │          │  │   Guard   │  │
│  └──────────┘  └──────────┘  └──────────┘  └───────────┘  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                  State Store (JSON)                          │
│        (dedup, exclusion lists, status tracking)            │
├─────────────────────────────────────────────────────────────┤
│               Platform Adapter Layer                         │
│     ┌────────────────┐    ┌────────────────┐               │
│     │  Job Board     │    │  Social App    │    ...        │
│     │  Adapter       │    │  Adapter       │               │
│     └────────────────┘    └────────────────┘               │
├─────────────────────────────────────────────────────────────┤
│                Notification Router                            │
│          (email / webhook / custom channels)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Installation

```bash
pip install -e ".[dev]"
```

### Basic Usage

```python
from app_autopilot.core.config import load_config
from app_autopilot.core.scoring import ScoringEngine
from app_autopilot.core.state import StateStore
from app_autopilot.rules.matcher import Matcher, RuleSet, Rule, MatchOperator

# 1. Load configuration
config = load_config("configs/examples/job_hunter.yaml", base_config_path="configs/base.yaml")

# 2. Initialize components
engine = ScoringEngine(config.scoring)
store = StateStore(config.state.storage_path)

# 3. Score a candidate
result = engine.score("job-12345", {
    "title": "Senior Python Engineer",
    "salary_min": 15000,
    "city": "Shanghai",
    "experience_years_required": 5,
})

if result.passed:
    print(f"Score: {result.total_score} — proceed with application!")
else:
    print(f"Score: {result.total_score} — skipped (failures: {result.hard_failures})")

# 4. Check deduplication before acting
if not store.exists("applications", "job-12345"):
    store.put("applications", "job-12345", {"status": "applied"})
    store.save()
```

---

## Configuration

App Autopilot uses hierarchical YAML configuration:

```yaml
# configs/examples/job_hunter.yaml
app_name: job-hunter

scoring:
  min_score_threshold: 40.0
  dimensions:
    - name: salary
      weight: 1.5
      rules:
        - type: range
          field: salary_min
          min: 15000
          score: 25

    - name: title
      weight: 2.0
      is_hard_requirement: true
      rules:
        - type: contains
          field: title
          value: engineer
          score: 20

scheduler:
  trigger_type: cron
  cron_expression: "0 9-18/2 * * 1-5"
```

See `configs/` for complete examples:
- `examples/job_hunter.yaml` — Job application automation
- `examples/social_manager.yaml` — Social media management

---

## Writing a Platform Adapter

Adapters are the bridge between App Autopilot and your target platform:

```python
from app_autopilot.adapters.base import PlatformAdapter, BrowseResult, InteractionResult, Message

class MyPlatformAdapter(PlatformAdapter):

    @property
    def platform_name(self) -> str:
        return "My Platform"

    async def setup(self, config):
        # Initialize your session/auth here
        pass

    async def browse(self, **kwargs) -> BrowseResult:
        # Fetch items from the platform
        return BrowseResult(items=[...])

    async def interact(self, action, item_id, **kwargs) -> InteractionResult:
        # Perform an action (apply, like, follow, etc.)
        return InteractionResult(success=True, action=action, item_id=item_id)

    async def read_messages(self, **kwargs) -> list[Message]:
        # Read incoming messages
        return []

    async def send_message(self, recipient_id, text, **kwargs) -> bool:
        # Send a message
        return True

    async def post_content(self, content, **kwargs) -> InteractionResult:
        # Publish content
        return InteractionResult(success=True, action="post")

    async def teardown(self):
        # Clean up
        pass
```

See `platforms/` for skeleton examples.

---

## Scoring Rules Reference

| Rule Type   | Description                                | Example Fields                     |
|-------------|--------------------------------------------|------------------------------------|
| `exact`     | Field equals a specific value              | `{"type": "exact", "field": "city", "value": "Shanghai", "score": 10}` |
| `range`     | Numeric field within [min, max]            | `{"type": "range", "field": "salary", "min": 8000, "score": 20}` |
| `contains`  | String field contains keyword (case-insensitive) | `{"type": "contains", "field": "title", "value": "engineer", "score": 15}` |
| `regex`     | String field matches regex                 | `{"type": "regex", "field": "bio", "pattern": "(?i)python", "score": 10}` |
| `in_list`   | Field value is in a list                   | `{"type": "in_list", "field": "city", "values": ["Shanghai", "Beijing"], "score": 10}` |

---

## Project Structure

```
app-autopilot/
├── app_autopilot/          # Core framework package
│   ├── core/               # Config, scoring, state, scheduler, task runner
│   ├── rules/              # Matching, classification, privacy
│   ├── adapters/           # Platform adapter ABC and registry
│   ├── notifications/      # Email, webhook notification channels
│   └── utils/              # Logging and utilities
├── configs/                # YAML configuration templates
│   ├── base.yaml           # Base configuration
│   └── examples/           # Scenario-specific examples
├── platforms/              # Platform adapter skeletons
├── docs/                   # Documentation
├── tests/                  # Unit tests
├── pyproject.toml          # Project metadata and dependencies
└── README.md               # This file
```

---

## Contributing

We welcome contributions! Please see [docs/contributing.md](docs/contributing.md) for guidelines.

### Development Setup

```bash
git clone https://github.com/your_org_here/app-autopilot.git
cd app-autopilot
pip install -e ".[dev]"
pytest
```

---

## Disclaimer

This framework is provided for **educational and productivity purposes**. Users are responsible for:
- Complying with the terms of service of any platform they automate
- Respecting rate limits and usage policies
- Ensuring their automated actions do not violate any laws or regulations

The maintainers are not responsible for any misuse of this software.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
