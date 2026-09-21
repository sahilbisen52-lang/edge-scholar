"""Network guard — tracks and enforces offline mode policy."""
from __future__ import annotations

import logging

from app.core.errors import PrivacyViolationError

logger = logging.getLogger("edge_scholar.privacy")


class NetworkGuard:
    """Enforces offline mode. Call check_allowed() before any network operation."""

    def __init__(self, offline_mode: bool = False) -> None:
        self.offline_mode = offline_mode

    def set_offline_mode(self, enabled: bool) -> None:
        self.offline_mode = enabled
        logger.info("Offline mode: %s", "ENABLED" if enabled else "DISABLED")

    def check_allowed(self, operation: str = "network request") -> None:
        if self.offline_mode:
            raise PrivacyViolationError(
                f"Blocked: {operation} (offline mode)",
                user_message=f"This operation requires network access but Offline Mode is enabled.",
            )

    def is_offline(self) -> bool:
        return self.offline_mode
