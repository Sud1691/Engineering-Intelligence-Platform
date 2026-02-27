"""
Prometheus Integration

Interacts with PromQL API to fetch metrics for cost and incidents.
"""

from __future__ import annotations

import structlog


log = structlog.get_logger()


class PrometheusClient:
    """Client for Prometheus HTTP API."""
    def __init__(self, endpoint: str | None = None) -> None:
        self._endpoint = endpoint

    async def query_cpu_usage(self, pod_label: str) -> float:
        """Fetch CPU usage for a pod or service."""
        log.info("prometheus_query_cpu", pod=pod_label)
        return 1.2  # cores
