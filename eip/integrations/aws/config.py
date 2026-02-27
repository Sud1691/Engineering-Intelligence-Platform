"""
AWS Config Client for compliance.
"""
from __future__ import annotations

import structlog

log = structlog.get_logger()

class AWSConfigClient:
    async def get_resource_config(self) -> list:
        log.info("config_get_resource")
        return []
