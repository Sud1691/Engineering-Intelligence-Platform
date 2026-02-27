"""
AWS Organizations & STS Assume Role utility.
"""
from __future__ import annotations

from typing import Any, Optional

import structlog

log = structlog.get_logger()

class MultiAccountClient:
    def assume_role(self, account_id: str, role_name: str) -> Optional[Any]:
        log.info("sts_assume_role", account_id=account_id)
        return None
