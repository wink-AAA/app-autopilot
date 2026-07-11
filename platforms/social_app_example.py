"""Example social media platform adapter (skeleton).

This is a reference implementation showing how to adapt a social media
platform to the App Autopilot framework.  It contains NO real automation
logic — only the structural skeleton with TODO placeholders.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from app_autopilot.adapters.base import (
    BrowseResult,
    InteractionResult,
    Message,
    PlatformAdapter,
)

logger = logging.getLogger(__name__)


class SocialAppExampleAdapter(PlatformAdapter):
    """Skeleton adapter for a generic social media platform.

    .. warning::
        This is a **skeleton only**.  You must implement the actual HTTP
        requests / browser automation for your target platform.
    """

    def __init__(self) -> None:
        self._config: Dict[str, Any] = {}
        self._session: Any = None

    @property
    def platform_name(self) -> str:
        return "Example Social App"

    async def setup(self, config: Dict[str, Any]) -> None:
        """Initialize session with the social platform.

        TODO: Replace with actual authentication logic.
        """
        self._config = config
        base_url = config.get("base_url", "")
        auth_token = config.get("auth_token", "")
        logger.info("Setting up social app adapter for %s", base_url)
        # TODO: Create HTTP session or browser instance
        # self._session = await create_session(auth_token)

    async def browse(self, **kwargs: Any) -> BrowseResult:
        """Browse trending content, suggested users, or feeds.

        TODO: Implement actual API call or page scraping.

        Keyword Args:
            cursor: Pagination token.
            limit: Max results per page.
            feed_type: "trending", "suggested", "timeline", etc.
        """
        limit = kwargs.get("limit", 20)
        cursor = kwargs.get("cursor")
        feed_type = kwargs.get("feed_type", "timeline")
        logger.info("Browsing social feed (type=%s, limit=%d)", feed_type, limit)

        # TODO: Replace with real data fetching
        # items = await self._session.get_feed(feed_type=feed_type, limit=limit)
        items: List[Dict[str, Any]] = []

        return BrowseResult(
            items=items,
            has_more=False,
            cursor=None,
        )

    async def interact(
        self,
        action: str,
        item_id: str,
        **kwargs: Any,
    ) -> InteractionResult:
        """Perform a social interaction.

        Supported actions: ``"like"``, ``"comment"``, ``"follow"``, ``"share"``.

        TODO: Implement actual interaction logic.
        """
        logger.info("Social interaction: action=%s, item=%s", action, item_id)

        if action in ("like", "follow", "share"):
            # TODO: Perform the interaction
            # await self._session.perform(action, item_id)
            return InteractionResult(
                success=True,
                item_id=item_id,
                action=action,
                message=f"{action.capitalize()} performed (skeleton).",
            )
        elif action == "comment":
            text = kwargs.get("text", "")
            # TODO: Post comment
            # await self._session.comment(item_id, text)
            return InteractionResult(
                success=True,
                item_id=item_id,
                action="comment",
                message="Comment posted (skeleton).",
            )
        else:
            return InteractionResult(
                success=False,
                item_id=item_id,
                action=action,
                message=f"Unknown action: {action}",
            )

    async def read_messages(self, **kwargs: Any) -> List[Message]:
        """Read direct messages and notifications.

        TODO: Implement actual message retrieval.
        """
        logger.info("Reading messages from social app.")
        # TODO: Replace with real message fetching
        # raw_messages = await self._session.get_direct_messages()
        return []

    async def send_message(
        self,
        recipient_id: str,
        text: str,
        **kwargs: Any,
    ) -> bool:
        """Send a direct message.

        TODO: Implement actual message sending.
        """
        logger.info("Sending DM to %s on social app.", recipient_id)
        # TODO: Replace with real message sending
        # return await self._session.send_dm(recipient_id, text)
        return True

    async def post_content(self, content: str, **kwargs: Any) -> InteractionResult:
        """Publish a post / status update.

        TODO: Implement actual content publishing.
        """
        logger.info("Publishing content on social app.")
        # TODO: Replace with real posting logic
        # post_id = await self._session.publish(content, **kwargs)
        return InteractionResult(
            success=True,
            action="post",
            message="Content published (skeleton).",
        )

    async def teardown(self) -> None:
        """Clean up resources."""
        logger.info("Tearing down social app adapter.")
        # TODO: Close HTTP session or browser
        # if self._session:
        #     await self._session.close()
