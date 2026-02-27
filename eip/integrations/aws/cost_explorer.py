"""
AWS Cost Explorer Client.
"""
from __future__ import annotations

import structlog

log = structlog.get_logger()

class CostExplorerClient:
    async def get_cost_and_usage(self) -> list:
        log.info("ce_get_cost")
        return []
