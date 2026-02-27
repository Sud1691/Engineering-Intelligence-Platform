from __future__ import annotations

from typing import Any, Protocol

from eip.core.models import ServiceNode


class RiskDataProvider(Protocol):
    def get_risk_overview(self, service_name: str | None = None) -> dict[str, Any]:
        ...


class ArchitectureDataProvider(Protocol):
    def get_services(self) -> list[ServiceNode]:
        ...

    def get_extra_dependencies(self) -> list[tuple[str, str]]:
        ...


class IncidentDataProvider(Protocol):
    def get_recent_incidents(
        self,
        service_name: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        ...


class CostDataProvider(Protocol):
    def get_cost_data(self) -> list[dict[str, Any]]:
        ...

    def get_resource_metrics(self) -> list[dict[str, Any]]:
        ...


class ComplianceDataProvider(Protocol):
    def get_violations(self) -> list[dict[str, Any]]:
        ...

    def get_account_configs(self) -> list[dict[str, Any]]:
        ...


class NLQDataProvider(Protocol):
    async def fetch_for_intent(
        self,
        intent: str,
        context: dict[str, Any],
    ) -> tuple[str, list[str]]:
        ...

