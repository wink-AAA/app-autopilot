"""Abstract base class for notification channels."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class NotificationPayload:
    """Standardised notification content.

    Attributes:
        title: Short summary / subject line.
        body: Full notification body (plain text or HTML).
        event_type: Category of event (e.g. "new_message", "application_sent").
        severity: One of "info", "warning", "error".
        metadata: Arbitrary extra data for templates or routing.
    """

    title: str
    body: str
    event_type: str = "general"
    severity: str = "info"
    metadata: Dict[str, Any] = field(default_factory=dict)


class NotificationChannel(ABC):
    """Abstract base for notification delivery channels.

    Subclass and implement ``send`` to add a new notification channel
    (e.g. Slack, Telegram, SMS, etc.).
    """

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Return the human-readable name of this channel."""
        ...

    @abstractmethod
    async def send(self, payload: NotificationPayload) -> bool:
        """Deliver a notification.

        Args:
            payload: The notification content.

        Returns:
            ``True`` if the notification was delivered successfully.
        """
        ...

    async def send_batch(self, payloads: List[NotificationPayload]) -> List[bool]:
        """Deliver multiple notifications.  Default: sequential ``send`` calls."""
        results: List[bool] = []
        for payload in payloads:
            results.append(await self.send(payload))
        return results


class NotificationRouter:
    """Routes notifications to channels based on event type.

    Example::

        router = NotificationRouter()
        router.add_channel("email", email_channel)
        router.add_channel("webhook", webhook_channel)
        router.add_route("new_message", "email")
        router.add_route("application_sent", "webhook")
        router.set_default_channel("email")

        await router.dispatch(NotificationPayload(
            title="New message",
            body="You have a new message from ...",
            event_type="new_message",
        ))
    """

    def __init__(self) -> None:
        self._channels: Dict[str, NotificationChannel] = {}
        self._routes: Dict[str, List[str]] = {}  # event_type -> [channel_names]
        self._default_channel: Optional[str] = None

    def add_channel(self, name: str, channel: NotificationChannel) -> None:
        """Register a notification channel."""
        self._channels[name] = channel

    def add_route(self, event_type: str, channel_name: str) -> None:
        """Map an event type to a notification channel."""
        self._routes.setdefault(event_type, []).append(channel_name)

    def set_default_channel(self, channel_name: str) -> None:
        """Set the fallback channel for unrouted event types."""
        self._default_channel = channel_name

    async def dispatch(self, payload: NotificationPayload) -> List[bool]:
        """Route and deliver a notification.

        Returns:
            List of delivery results (one per channel used).
        """
        target_channels = self._routes.get(payload.event_type, [])

        # Fallback to default channel if no routes match
        if not target_channels and self._default_channel:
            target_channels = [self._default_channel]

        results: List[bool] = []
        for ch_name in target_channels:
            channel = self._channels.get(ch_name)
            if channel is None:
                continue
            result = await channel.send(payload)
            results.append(result)

        return results
