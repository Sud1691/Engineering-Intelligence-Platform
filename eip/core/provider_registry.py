from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from time import perf_counter
from typing import Any
from uuid import uuid4

from eip.core.providers import (
    ArchitectureDataProvider,
    ComplianceDataProvider,
    CostDataProvider,
    IncidentDataProvider,
    NLQDataProvider,
    RiskDataProvider,
)
from eip.core.settings import get_settings
from eip.stubs.providers import (
    StubArchitectureDataProvider,
    StubComplianceDataProvider,
    StubCostDataProvider,
    StubIncidentDataProvider,
    StubNLQDataProvider,
    StubRiskDataProvider,
)


@dataclass(frozen=True)
class ProviderRegistry:
    source_mode: str
    risk: RiskDataProvider
    architecture: ArchitectureDataProvider
    incident: IncidentDataProvider
    cost: CostDataProvider
    compliance: ComplianceDataProvider
    nlq: NLQDataProvider


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_response_meta(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    registry = get_provider_registry()
    settings = get_settings()
    payload: dict[str, Any] = {
        "source_mode": registry.source_mode,
        "generated_at": _utc_now_iso(),
        "config_source": settings.tfvars_path or "defaults/env",
    }
    if extra:
        payload.update(extra)
    return payload


def build_endpoint_meta(
    *,
    pillar: str,
    started_at: float,
    extra: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    endpoint_meta: dict[str, Any] = {
        "pillar": pillar,
        "request_id": request_id or str(uuid4()),
        "duration_ms": max(0, int((perf_counter() - started_at) * 1000)),
    }
    if extra:
        endpoint_meta.update(extra)
    return build_response_meta(endpoint_meta)


@lru_cache(maxsize=1)
def get_provider_registry() -> ProviderRegistry:
    settings = get_settings()

    if settings.runtime_mode == "stub":
        risk = StubRiskDataProvider()
        architecture = StubArchitectureDataProvider()
        incident = StubIncidentDataProvider()
        cost = StubCostDataProvider()
        compliance = StubComplianceDataProvider()
        nlq = StubNLQDataProvider(
            risk_provider=risk,
            architecture_provider=architecture,
            incident_provider=incident,
            cost_provider=cost,
            compliance_provider=compliance,
        )
        return ProviderRegistry(
            source_mode=settings.runtime_mode,
            risk=risk,
            architecture=architecture,
            incident=incident,
            cost=cost,
            compliance=compliance,
            nlq=nlq,
        )

    raise NotImplementedError(
        "Live provider wiring is not implemented yet. See docs/live_setup.md."
    )


def clear_provider_registry_cache() -> None:
    get_provider_registry.cache_clear()
