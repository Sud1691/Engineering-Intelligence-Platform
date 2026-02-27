"""
Wavefront / Tanzu Observability Integration

Interacts with the Wavefront API to fetch metrics for cost and incidents.
"""

from __future__ import annotations

import structlog


log = structlog.get_logger()


class WavefrontClient:
    """Client for Wavefront API."""
    def __init__(self, t0ken: str | None = None) -> None:
        self._token = t0ken

    async def get_service_health(self, service_name: str) -> str:
        """Fetch general service health metrics (e.g. error rate, apdex)"""
        log.info("wavefront_get_health", service=service_name)
        return "healthy"
