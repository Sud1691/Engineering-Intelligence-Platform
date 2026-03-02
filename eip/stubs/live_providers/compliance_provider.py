from __future__ import annotations

from typing import Any

from eip.stubs.providers import StubComplianceDataProvider


class LiveComplianceDataProvider:
    """
    Transitional compliance provider.
    """

    def __init__(self) -> None:
        self._fallback = StubComplianceDataProvider()

    def get_violations(self) -> list[dict[str, Any]]:
        return self._fallback.get_violations()

    def get_account_configs(self) -> list[dict[str, Any]]:
        return self._fallback.get_account_configs()
