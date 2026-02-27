"""
AWS X-Ray Client for architecture maps.
"""
from __future__ import annotations

import structlog

log = structlog.get_logger()

class XRayClient:
    async def get_service_graph(self) -> list:
        log.info("xray_get_graph")
        return []
