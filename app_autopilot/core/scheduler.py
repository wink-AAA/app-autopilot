"""Task scheduler abstraction supporting multiple trigger modes.

The scheduler is responsible for deciding *when* to run automation tasks.
It supports three trigger modes:

- **interval**: Run every N seconds.
- **cron**: Run according to a cron expression (requires ``croniter``).
- **manual**: Never auto-trigger; the caller invokes ``run_once()`` explicitly.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Optional

from app_autopilot.core.config import SchedulerConfig

logger = logging.getLogger(__name__)


class Scheduler:
    """Simple task scheduler.

    Example::

        config = SchedulerConfig(trigger_type="interval", interval_seconds=60)
        scheduler = Scheduler(config)
        scheduler.register("my_task", my_task_function)
        scheduler.start()  # blocks forever
    """

    def __init__(self, config: SchedulerConfig) -> None:
        self.config = config
        self._tasks: dict[str, Callable[..., Any]] = {}
        self._running = False

    def register(self, name: str, func: Callable[..., Any]) -> None:
        """Register a named task callable."""
        self._tasks[name] = func
        logger.info("Registered task: %s", name)

    def unregister(self, name: str) -> None:
        """Remove a previously registered task."""
        self._tasks.pop(name, None)

    def start(self) -> None:
        """Start the scheduler loop (blocking).

        For ``manual`` trigger type this raises immediately because there is
        nothing to schedule.
        """
        if self.config.trigger_type == "manual":
            logger.info("Scheduler in manual mode — use run_once() to trigger tasks.")
            return

        self._running = True
        logger.info("Scheduler started (mode=%s)", self.config.trigger_type)

        if self.config.trigger_type == "interval":
            self._run_interval()
        elif self.config.trigger_type == "cron":
            self._run_cron()
        else:
            raise ValueError(f"Unknown trigger type: {self.config.trigger_type}")

    def stop(self) -> None:
        """Signal the scheduler to stop after the current iteration."""
        self._running = False
        logger.info("Scheduler stop requested.")

    def run_once(self) -> None:
        """Execute all registered tasks a single time."""
        self._execute_all()

    # -- internal -----------------------------------------------------------

    def _run_interval(self) -> None:
        """Run tasks at a fixed interval."""
        interval = self.config.interval_seconds
        while self._running:
            self._execute_all()
            logger.debug("Sleeping %d seconds until next run.", interval)
            # Sleep in small increments so we can respond to stop() quickly
            for _ in range(interval):
                if not self._running:
                    break
                time.sleep(1)

    def _run_cron(self) -> None:
        """Run tasks according to a cron expression.

        Requires the ``croniter`` package.
        """
        try:
            from croniter import croniter  # type: ignore[import-untyped]
        except ImportError:
            raise ImportError(
                "cron-trigger scheduling requires the 'croniter' package. "
                "Install it with: pip install croniter"
            )

        expr = self.config.cron_expression
        if not expr:
            raise ValueError("cron_expression is required for cron trigger type")

        cron = croniter(expr)
        while self._running:
            next_run = cron.get_next(float)
            delay = next_run - time.time()
            if delay > 0:
                # Sleep in small increments for responsive shutdown
                end = time.time() + delay
                while time.time() < end and self._running:
                    time.sleep(min(1, end - time.time()))
            if self._running:
                self._execute_all()

    def _execute_all(self) -> None:
        """Execute all registered tasks with error isolation."""
        for name, func in list(self._tasks.items()):
            try:
                logger.info("Executing task: %s", name)
                func()
            except Exception:
                logger.exception("Task '%s' failed with an error.", name)
