from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from eip.core.models import ServiceNode, ServiceTier
from eip.core.providers import (
    ArchitectureDataProvider,
    ComplianceDataProvider,
    CostDataProvider,
    IncidentDataProvider,
    NLQDataProvider,
    RiskDataProvider,
)
from eip.intelligence.adapters import (
    ArchitectureNLQAdapter,
    ComplianceNLQAdapter,
    CostNLQAdapter,
    GeneralNLQAdapter,
    IncidentNLQAdapter,
    RiskNLQAdapter,
)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_SERVICES: list[ServiceNode] = [
    ServiceNode(
        name="payments-api",
        tier=ServiceTier.CRITICAL,
        team="finance-platform",
        aws_account="111111111111",
        dependencies=["auth-service", "ledger-db"],
        consumers=["checkout-ui"],
        health="healthy",
        monthly_cost=1500.0,
    ),
    ServiceNode(
        name="auth-service",
        tier=ServiceTier.CRITICAL,
        team="identity",
        aws_account="111111111111",
        dependencies=["user-db"],
        consumers=["payments-api", "checkout-ui"],
        health="healthy",
        monthly_cost=780.0,
    ),
    ServiceNode(
        name="checkout-ui",
        tier=ServiceTier.IMPORTANT,
        team="web-commerce",
        aws_account="111111111111",
        dependencies=["payments-api", "auth-service"],
        consumers=[],
        health="degraded",
        monthly_cost=430.0,
    ),
]

_EXTRA_DEPENDENCIES: list[tuple[str, str]] = [
    ("payments-api", "fraud-service"),
    ("checkout-ui", "feature-flag-service"),
]

_INCIDENTS: list[dict[str, Any]] = [
    {
        "id": "INC-1001",
        "service_name": "payments-api",
        "severity": "SEV-2",
        "root_cause": "database connection pool exhaustion",
        "started_at": "2026-02-24T09:10:00+00:00",
        "status": "resolved",
    },
    {
        "id": "INC-1002",
        "service_name": "auth-service",
        "severity": "SEV-3",
        "root_cause": "cache stampede under traffic spike",
        "started_at": "2026-02-25T18:15:00+00:00",
        "status": "resolved",
    },
    {
        "id": "INC-1003",
        "service_name": "payments-api",
        "severity": "SEV-3",
        "root_cause": "retry storm after downstream timeout",
        "started_at": "2026-02-26T11:05:00+00:00",
        "status": "triggered",
    },
]

_COST_DATA: list[dict[str, Any]] = [
    {
        "service_name": "payments-api",
        "current_spend": 1500.0,
        "baseline_spend": 1000.0,
    },
    {
        "service_name": "auth-service",
        "current_spend": 500.0,
        "baseline_spend": 520.0,
    },
]

_RESOURCE_METRICS: list[dict[str, Any]] = [
    {
        "id": "i-stub-underutilized-1",
        "type": "EC2_INSTANCE",
        "avg_cpu_7d": 1.2,
        "monthly_cost": 45.0,
    },
    {
        "id": "vol-stub-unattached-1",
        "type": "EBS_VOLUME",
        "state": "available",
        "monthly_cost": 12.5,
    },
]

_VIOLATIONS: list[dict[str, Any]] = [
    {
        "rule_id": "SEC_001",
        "resource": "infra/main.tf",
        "description": "Potential open security group detected in Terraform",
        "severity": "HIGH",
        "remediation": "Restrict ingress CIDR block",
    }
]

_ACCOUNT_CONFIGS: list[dict[str, Any]] = [
    {
        "account_id": "111111111111",
        "s3_public_access_block": False,
    }
]


class StubRiskDataProvider(RiskDataProvider):
    def get_risk_overview(self, service_name: str | None = None) -> dict[str, Any]:
        target = service_name or "all-services"
        return {
            "service_name": target,
            "high_risk_deployments_last_7d": 3 if target == "payments-api" else 1,
            "critical_risk_deployments_last_7d": 1 if target == "payments-api" else 0,
            "generated_at": _utc_iso(),
        }


class StubArchitectureDataProvider(ArchitectureDataProvider):
    def get_services(self) -> list[ServiceNode]:
        return [service.model_copy(deep=True) for service in _SERVICES]

    def get_extra_dependencies(self) -> list[tuple[str, str]]:
        return list(_EXTRA_DEPENDENCIES)


class StubIncidentDataProvider(IncidentDataProvider):
    def get_recent_incidents(
        self,
        service_name: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        incidents = _INCIDENTS
        if service_name:
            incidents = [inc for inc in incidents if inc["service_name"] == service_name]
        return incidents[:limit]


class StubCostDataProvider(CostDataProvider):
    def get_cost_data(self) -> list[dict[str, Any]]:
        return list(_COST_DATA)

    def get_resource_metrics(self) -> list[dict[str, Any]]:
        return list(_RESOURCE_METRICS)


class StubComplianceDataProvider(ComplianceDataProvider):
    def get_violations(self) -> list[dict[str, Any]]:
        return list(_VIOLATIONS)

    def get_account_configs(self) -> list[dict[str, Any]]:
        return list(_ACCOUNT_CONFIGS)


class StubNLQDataProvider(NLQDataProvider):
    def __init__(
        self,
        risk_provider: RiskDataProvider,
        architecture_provider: ArchitectureDataProvider,
        incident_provider: IncidentDataProvider,
        cost_provider: CostDataProvider,
        compliance_provider: ComplianceDataProvider,
    ) -> None:
        self._risk = RiskNLQAdapter(risk_provider)
        self._architecture = ArchitectureNLQAdapter(architecture_provider)
        self._incident = IncidentNLQAdapter(incident_provider)
        self._cost = CostNLQAdapter(cost_provider)
        self._compliance = ComplianceNLQAdapter(compliance_provider)
        self._general = GeneralNLQAdapter(
            risk_adapter=self._risk,
            architecture_adapter=self._architecture,
            incident_adapter=self._incident,
            cost_adapter=self._cost,
            compliance_adapter=self._compliance,
        )

    async def fetch_for_intent(
        self,
        intent: str,
        context: dict[str, Any],
    ) -> tuple[str, list[str]]:
        if intent == "deployment_risk_query":
            return await self._risk.fetch(context)
        if intent in {"blast_radius_query", "architecture_query"}:
            return await self._architecture.fetch(context)
        if intent == "incident_pattern_query":
            return await self._incident.fetch(context)
        if intent == "cost_query":
            return await self._cost.fetch(context)
        if intent == "compliance_query":
            return await self._compliance.fetch(context)
        if intent == "team_health_query":
            return await self._general.fetch(context)
        return await self._general.fetch(context)

