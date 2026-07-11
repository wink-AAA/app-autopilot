"""Webhook notification channel implementation."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from app_autopilot.notifications.base import NotificationChannel, NotificationPayload

logger = logging.getLogger(__name__)


class WebhookChannel(NotificationChannel):
    """Send notifications via HTTP webhook (POST).

    Example::

        channel = WebhookChannel(
            url="https://hooks.example.com/services/your_webhook_here",
            headers={"Authorization": "Bearer your_token_here"},
        )
        await channel.send(NotificationPayload(
            title="Alert",
            body="Something happened.",
            event_type="new_message",
        ))
    """

    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
        method: str = "POST",
    ) -> None:
        self.url = url
        self.headers = headers or {"Content-Type": "application/json"}
        self.timeout = timeout
        self.method = method.upper()

    @property
    def channel_name(self) -> str:
        return "webhook"

    async def send(self, payload: NotificationPayload) -> bool:
        """Send a notification via HTTP webhook."""
        try:
            import aiohttp
        except ImportError:
            logger.error(
                "WebhookChannel requires 'aiohttp'. Install it with: pip install aiohttp"
            )
            return False

        body = {
            "title": payload.title,
            "body": payload.body,
            "event_type": payload.event_type,
            "severity": payload.severity,
            "metadata": payload.metadata,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    self.method,
                    self.url,
                    json=body,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    if resp.status < 300:
                        logger.info(
                            "Webhook delivered to %s: %s (status=%d)",
                            self.url,
                            payload.title,
                            resp.status,
                        )
                        return True
                    else:
                        logger.warning(
                            "Webhook to %s returned status %d",
                            self.url,
                            resp.status,
                        )
                        return False
        except Exception:
            logger.exception("Failed to deliver webhook to %s", self.url)
            return False
