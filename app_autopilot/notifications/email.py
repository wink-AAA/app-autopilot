"""Email notification channel implementation."""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

from app_autopilot.notifications.base import NotificationChannel, NotificationPayload

logger = logging.getLogger(__name__)


class EmailChannel(NotificationChannel):
    """Send notifications via SMTP email.

    Example::

        channel = EmailChannel(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="your_email_here",
            password="your_password_here",
            sender="your_email_here",
            recipients=["admin@example.com"],
        )
        await channel.send(NotificationPayload(
            title="Alert",
            body="Something happened.",
        ))
    """

    def __init__(
        self,
        smtp_host: str = "localhost",
        smtp_port: int = 587,
        username: str = "",
        password: str = "",
        sender: str = "",
        recipients: Optional[list[str]] = None,
        use_tls: bool = True,
    ) -> None:
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.sender = sender or username
        self.recipients = recipients or []
        self.use_tls = use_tls

    @property
    def channel_name(self) -> str:
        return "email"

    async def send(self, payload: NotificationPayload) -> bool:
        """Send an email notification via SMTP."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[App Autopilot] {payload.title}"
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)

        # Plain text body
        msg.attach(MIMEText(payload.body, "plain", "utf-8"))

        # HTML body (simple formatting)
        html = f"<html><body><h2>{payload.title}</h2><p>{payload.body}</p></body></html>"
        msg.attach(MIMEText(html, "html", "utf-8"))

        try:
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)

            if self.username and self.password:
                server.login(self.username, self.password)

            server.sendmail(self.sender, self.recipients, msg.as_string())
            server.quit()
            logger.info("Email sent to %s: %s", self.recipients, payload.title)
            return True
        except Exception:
            logger.exception("Failed to send email notification.")
            return False
