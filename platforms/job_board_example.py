"""Example job board platform adapter (skeleton).

This is a reference implementation showing how to adapt a job board
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


class JobBoardExampleAdapter(PlatformAdapter):
    """Skeleton adapter for a generic job board platform.

    .. warning::
        This is a **skeleton only**.  You must implement the actual HTTP
        requests / browser automation for your target platform.
    """

    def __init__(self) -> None:
        self._config: Dict[str, Any] = {}
        self._session: Any = None

    @property
    def platform_name(self) -> str:
        return "Example Job Board"

    async def setup(self, config: Dict[str, Any]) -> None:
        """Initialize session with the job board.

        TODO: Replace with actual authentication logic.
        """
        self._config = config
        base_url = config.get("base_url", "")
        api_key = config.get("api_key", "")
        logger.info("Setting up job board adapter for %s", base_url)
        # TODO: Create HTTP session or browser instance
        # self._session = await create_session(api_key)

    async def browse(self, **kwargs: Any) -> BrowseResult:
        """Browse job listings.

        TODO: Implement actual API call or page scraping.

        Keyword Args:
            cursor: Pagination token.
            limit: Max results per page.
            filters: Platform-specific search filters.
        """
        limit = kwargs.get("limit", 20)
        cursor = kwargs.get("cursor")
        logger.info("Browsing jobs (limit=%d, cursor=%s)", limit, cursor)

        # TODO: Replace with real data fetching
        # jobs = await self._session.search_jobs(**kwargs)
        jobs: List[Dict[str, Any]] = []

        return BrowseResult(
            items=jobs,
            has_more=False,
            cursor=None,
        )

    async def interact(
        self,
        action: str,
        item_id: str,
        **kwargs: Any,
    ) -> InteractionResult:
        """Perform an action on a job listing.

        Supported actions: ``"apply"``, ``"save"``, ``"dismiss"``.

        TODO: Implement actual submission logic.
        """
        logger.info("Interacting with job %s: action=%s", item_id, action)

        if action == "apply":
            # TODO: Submit application
            # await self._session.submit_application(item_id, **kwargs)
            return InteractionResult(
                success=True,
                item_id=item_id,
                action="apply",
                message="Application submitted (skeleton).",
            )
        elif action == "save":
            # TODO: Save job to favourites
            return InteractionResult(
                success=True,
                item_id=item_id,
                action="save",
                message="Job saved (skeleton).",
            )
        else:
            return InteractionResult(
                success=False,
                item_id=item_id,
                action=action,
                message=f"Unknown action: {action}",
            )

    async def read_messages(self, **kwargs: Any) -> List[Message]:
        """Read recruiter / platform messages.

        TODO: Implement actual message retrieval.
        """
        logger.info("Reading messages from job board.")
        # TODO: Replace with real message fetching
        # raw_messages = await self._session.get_messages()
        return []

    async def send_message(
        self,
        recipient_id: str,
        text: str,
        **kwargs: Any,
    ) -> bool:
        """Send a message to a recruiter or contact.

        TODO: Implement actual message sending.
        """
        logger.info("Sending message to %s on job board.", recipient_id)
        # TODO: Replace with real message sending
        # return await self._session.send_message(recipient_id, text)
        return True

    async def post_content(self, content: str, **kwargs: Any) -> InteractionResult:
        """Post content (e.g. a profile update or status).

        TODO: Implement if the platform supports content posting.
        """
        logger.info("Posting content on job board (not typically supported).")
        return InteractionResult(
            success=False,
            action="post",
            message="Content posting not supported on this platform.",
        )

    async def teardown(self) -> None:
        """Clean up resources."""
        logger.info("Tearing down job board adapter.")
        # TODO: Close HTTP session or browser
        # if self._session:
        #     await self._session.close()
