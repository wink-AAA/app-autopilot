"""Multi-stage task orchestrator.

The ``TaskRunner`` executes a sequence of stages (functions) where each stage
can produce output that feeds into the next.  Stages support independent error
handling, retries, and fallbacks.

Example pipeline::

    runner = TaskRunner()
    runner.add_stage("browse", browse_jobs, retries=2)
    runner.add_stage("score", score_candidates)
    runner.add_stage("apply", submit_applications, fallback=notify_failure)
    runner.run()
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class StageStatus(str, Enum):
    """Execution status of a pipeline stage."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    """Result of a single stage execution."""

    name: str
    status: StageStatus = StageStatus.PENDING
    output: Any = None
    error: Optional[str] = None
    duration_seconds: float = 0.0
    attempts: int = 0


@dataclass
class PipelineResult:
    """Aggregate result of a full pipeline execution."""

    stage_results: List[StageResult] = field(default_factory=list)
    success: bool = True
    total_duration_seconds: float = 0.0
    shared_context: Dict[str, Any] = field(default_factory=dict)

    @property
    def failed_stages(self) -> List[StageResult]:
        return [r for r in self.stage_results if r.status == StageStatus.FAILED]


class TaskRunner:
    """Multi-stage task orchestrator.

    Each stage is a callable that receives the shared context dict and the
    output of the previous stage.  It may return a value that becomes
    ``previous_output`` for the next stage.
    """

    def __init__(self) -> None:
        self._stages: List[Dict[str, Any]] = []

    def add_stage(
        self,
        name: str,
        func: Callable[..., Any],
        retries: int = 0,
        retry_delay_seconds: float = 1.0,
        fallback: Optional[Callable[..., Any]] = None,
        skip_on_failure: bool = True,
    ) -> None:
        """Register a pipeline stage.

        Args:
            name: Human-readable stage name.
            func: The callable to execute.  Signature:
                  ``func(context: dict, previous_output: Any) -> Any``
            retries: Number of retries on failure.
            retry_delay_seconds: Delay between retries (seconds).
            fallback: Optional fallback callable invoked when all retries
                      are exhausted.  Signature:
                      ``fallback(context: dict, error: Exception) -> Any``
            skip_on_failure: If ``True`` and this stage fails (after retries),
                             subsequent stages are skipped.
        """
        self._stages.append({
            "name": name,
            "func": func,
            "retries": retries,
            "retry_delay": retry_delay_seconds,
            "fallback": fallback,
            "skip_on_failure": skip_on_failure,
        })

    def run(self, initial_context: Optional[Dict[str, Any]] = None) -> PipelineResult:
        """Execute all stages in order.

        Args:
            initial_context: Optional dict passed through all stages.

        Returns:
            A ``PipelineResult`` summarising all stage outcomes.
        """
        pipeline = PipelineResult()
        context: Dict[str, Any] = dict(initial_context or {})
        pipeline.shared_context = context
        previous_output: Any = None
        pipeline_start = time.monotonic()

        for stage_def in self._stages:
            stage_name: str = stage_def["name"]
            result = StageResult(name=stage_name)
            pipeline.stage_results.append(result)

            # Check if we should skip due to a previous failure
            if pipeline.failed_stages and stage_def.get("skip_on_failure", True):
                result.status = StageStatus.SKIPPED
                logger.warning("Skipping stage '%s' due to prior failure.", stage_name)
                continue

            result.status = StageStatus.RUNNING
            max_attempts = 1 + stage_def.get("retries", 0)
            retry_delay = stage_def.get("retry_delay", 1.0)
            stage_start = time.monotonic()

            for attempt in range(1, max_attempts + 1):
                result.attempts = attempt
                try:
                    logger.info(
                        "Running stage '%s' (attempt %d/%d)",
                        stage_name,
                        attempt,
                        max_attempts,
                    )
                    output = stage_def["func"](context, previous_output)
                    result.output = output
                    result.status = StageStatus.SUCCESS
                    previous_output = output
                    break
                except Exception as exc:
                    logger.warning(
                        "Stage '%s' attempt %d failed: %s",
                        stage_name,
                        attempt,
                        exc,
                    )
                    if attempt < max_attempts:
                        time.sleep(retry_delay)
            else:
                # All attempts exhausted
                result.status = StageStatus.FAILED
                result.error = str(exc)  # type: ignore[possibly-undefined]
                pipeline.success = False

                # Run fallback if provided
                fallback_fn = stage_def.get("fallback")
                if fallback_fn is not None:
                    try:
                        logger.info("Running fallback for stage '%s'.", stage_name)
                        fallback_output = fallback_fn(context, exc)  # type: ignore[possibly-undefined]
                        result.output = fallback_output
                    except Exception as fb_exc:
                        logger.error("Fallback for stage '%s' also failed: %s", stage_name, fb_exc)

            result.duration_seconds = time.monotonic() - stage_start

        pipeline.total_duration_seconds = time.monotonic() - pipeline_start
        return pipeline
