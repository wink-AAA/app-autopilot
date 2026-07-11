"""Abstract base class for platform adapters.

Every platform integration must subclass ``PlatformAdapter`` and implement
its abstract methods.  This ensures a uniform interface regardless of the
underlying platform (job boards, social networks, messaging apps, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class BrowseResult:
    """Result from a browse operation."""

    items: List[Dict[str, Any]] = field(default_factory=list)
    has_more: bool = False
    cursor: Optional[str] = None
    raw: Any = None


@dataclass
class Message:
    """A normalized message from any platform."""

    message_id: str
    sender_id: str
    sender_name: str = ""
    content: str = ""
    timestamp: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InteractionResult:
    """Result from an interaction operation (like, apply, follow, etc.)."""

    success: bool
    item_id: str = ""
    action: str = ""
    message: str = ""
    raw: Any = None


class PlatformAdapter(ABC):
    """Abstract base class that every platform adapter must implement.

    Subclass this and implement all abstract methods to integrate a new
    platform with App Autopilot.

    Example::

        class MyJobBoardAdapter(PlatformAdapter):
            async def setup(self, config):
                self.session = await create_session(config["api_key"])

            async def browse(self, **kwargs):
                return BrowseResult(items=await self.session.fetch_jobs())

            async def interact(self, action, item_id, **kwargs):
                await self.session.apply(item_id)
                return InteractionResult(success=True, action=action, item_id=item_id)

            async def read_messages(self, **kwargs):
                return [Message(...)]

            async def send_message(self, recipient_id, text, **kwargs):
                await self.session.send(recipient_id, text)

            async def post_content(self, content, **kwargs):
                await self.session.post(content)

            async def teardown(self):
                await self.session.close()
    """

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the human-readable name of the platform."""
        ...

    @abstractmethod
    async def setup(self, config: Dict[str, Any]) -> None:
        """Initialize the adapter (login, create sessions, etc.).

        Args:
            config: Platform-specific configuration dict.
        """
        ...

    @abstractmethod
    async def browse(self, **kwargs: Any) -> BrowseResult:
        """Browse available content (jobs, posts, profiles, etc.).

        Keyword Args:
            cursor: Pagination cursor from a previous call.
            limit: Maximum number of items to return.
            filters: Arbitrary platform-specific filters.

        Returns:
            A ``BrowseResult`` containing the discovered items.
        """
        ...

    @abstractmethod
    async def interact(
        self,
        action: str,
        item_id: str,
        **kwargs: Any,
    ) -> InteractionResult:
        """Perform an interaction on an item.

        Args:
            action: The type of interaction (e.g. "apply", "like", "follow").
            item_id: The identifier of the target item.

        Returns:
            An ``InteractionResult`` indicating success or failure.
        """
        ...

    @abstractmethod
    async def read_messages(self, **kwargs: Any) -> List[Message]:
        """Read incoming messages.

        Returns:
            A list of ``Message`` objects.
        """
        ...

    @abstractmethod
    async def send_message(
        self,
        recipient_id: str,
        text: str,
        **kwargs: Any,
    ) -> bool:
        """Send a message to a recipient.

        Args:
            recipient_id: Identifier of the message recipient.
            text: Message content.

        Returns:
            ``True`` if the message was sent successfully.
        """
        ...

    @abstractmethod
    async def post_content(self, content: str, **kwargs: Any) -> InteractionResult:
        """Publish content to the platform.

        Args:
            content: The content text to publish.

        Returns:
            An ``InteractionResult`` indicating success or failure.
        """
        ...

    @abstractmethod
    async def teardown(self) -> None:
        """Clean up resources (close sessions, logout, etc.)."""
        ...

    # -- optional hooks (override as needed) --------------------------------

    async def on_error(self, error: Exception) -> None:
        """Called when an unrecoverable error occurs. Override for custom handling."""
        pass

    async def heartbeat(self) -> bool:
        """Check whether the adapter session is still alive.

        Returns:
            ``True`` if the session is healthy.
        """
        return True
