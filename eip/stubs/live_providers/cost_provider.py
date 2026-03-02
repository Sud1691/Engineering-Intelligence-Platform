from __future__ import annotations

from typing import Any

from eip.stubs.providers import StubCostDataProvider


class LiveCostDataProvider:
    """
    Transitional cost provider.

    Live Cost Explorer/resource-metric ingestion can replace this class without
    changing provider registry interfaces.
    """

    def __init__(self) -> None:
        self._fallback = StubCostDataProvider()

    def get_cost_data(self) -> list[dict[str, Any]]:
        return self._fallback.get_cost_data()

    def get_resource_metrics(self) -> list[dict[str, Any]]:
        return self._fallback.get_resource_metrics()
