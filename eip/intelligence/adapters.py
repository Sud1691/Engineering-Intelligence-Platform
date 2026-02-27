from __future__ import annotations

import asyncio
import json
from typing import Any

from eip.core.providers import (
    ArchitectureDataProvider,
    ComplianceDataProvider,
    CostDataProvider,
    IncidentDataProvider,
    RiskDataProvider,
)
from eip.pillars.architecture_map.graph_builder import ArchitectureGraphBuilder
from eip.pillars.architecture_map.query_engine import ArchitectureQueryEngine
from eip.pillars.compliance.drift_detector import DriftDetector
from eip.pillars.compliance.policy_engine import PolicyEngine
from eip.pillars.cost_intelligence.anomaly_detector import CostAnomalyDetector
from eip.pillars.cost_intelligence.optimizer import CostOptimizer


def _service_from_context(context: dict[str, Any]) -> str | None:
    return context.get("service") or context.get("service_name")


class RiskNLQAdapter:
    def __init__(self, provider: RiskDataProvider) -> None:
        self._provider = provider

    async def fetch(self, context: dict[str, Any]) -> tuple[str, list[str]]:
        service_name = _service_from_context(context)
        payload = self._provider.get_risk_overview(service_name=service_name)
        return json.dumps(payload), ["stub:risk_provider"]


class ArchitectureNLQAdapter:
    def __init__(self, provider: ArchitectureDataProvider) -> None:
        self._provider = provider
        self._builder = ArchitectureGraphBuilder()

    async def fetch(self, context: dict[str, Any]) -> tuple[str, list[str]]:
        services = self._provider.get_services()
        graph = self._builder.build(services)

        for caller, callee in self._provider.get_extra_dependencies():
            if caller not in graph:
                graph.add_node(caller)
            if callee not in graph:
                graph.add_node(callee)
            graph.add_edge(caller, callee)

        engine = ArchitectureQueryEngine(graph)
        service_name = _service_from_context(context)

        if service_name and engine.has_service(service_name):
            payload: dict[str, Any] = {
                "service_name": service_name,
                "dependencies": engine.get_dependencies(service_name, max_depth=3),
                "blast_radius": engine.get_blast_radius(service_name, max_depth=3),
            }
        else:
            payload = {
                "service_count": graph.number_of_nodes(),
                "dependency_count": graph.number_of_edges(),
                "known_services": sorted(list(graph.nodes))[:10],
            }

        return json.dumps(payload), ["stub:architecture_provider"]


class IncidentNLQAdapter:
    def __init__(self, provider: IncidentDataProvider) -> None:
        self._provider = provider

    async def fetch(self, context: dict[str, Any]) -> tuple[str, list[str]]:
        service_name = _service_from_context(context)
        incidents = self._provider.get_recent_incidents(service_name=service_name, limit=5)
        payload = {
            "service_name": service_name,
            "incident_count": len(incidents),
            "incidents": incidents,
        }
        return json.dumps(payload), ["stub:incident_provider"]


class CostNLQAdapter:
    def __init__(self, provider: CostDataProvider) -> None:
        self._provider = provider
        self._anomaly = CostAnomalyDetector()
        self._optimizer = CostOptimizer()

    async def fetch(self, context: dict[str, Any]) -> tuple[str, list[str]]:
        _ = context
        cost_data = self._provider.get_cost_data()
        resource_metrics = self._provider.get_resource_metrics()
        payload = {
            "anomalies": self._anomaly.detect_anomalies(cost_data),
            "opportunities": self._optimizer.find_opportunities(resource_metrics),
        }
        return json.dumps(payload), ["stub:cost_provider"]


class ComplianceNLQAdapter:
    def __init__(self, provider: ComplianceDataProvider) -> None:
        self._provider = provider
        self._policy = PolicyEngine()
        self._drift = DriftDetector()

    async def fetch(self, context: dict[str, Any]) -> tuple[str, list[str]]:
        _ = context
        violations = self._provider.get_violations()
        account_configs = self._provider.get_account_configs()
        payload = {
            "policy_evaluation": self._policy.evaluate_violations(violations),
            "drifts": self._drift.detect_drift(account_configs),
        }
        return json.dumps(payload), ["stub:compliance_provider"]


class GeneralNLQAdapter:
    def __init__(
        self,
        risk_adapter: RiskNLQAdapter,
        architecture_adapter: ArchitectureNLQAdapter,
        incident_adapter: IncidentNLQAdapter,
        cost_adapter: CostNLQAdapter,
        compliance_adapter: ComplianceNLQAdapter,
    ) -> None:
        self._risk_adapter = risk_adapter
        self._architecture_adapter = architecture_adapter
        self._incident_adapter = incident_adapter
        self._cost_adapter = cost_adapter
        self._compliance_adapter = compliance_adapter

    async def fetch(self, context: dict[str, Any]) -> tuple[str, list[str]]:
        (
            (risk_data, risk_sources),
            (architecture_data, architecture_sources),
            (incident_data, incident_sources),
            (cost_data, cost_sources),
            (compliance_data, compliance_sources),
        ) = await asyncio.gather(
            self._risk_adapter.fetch(context),
            self._architecture_adapter.fetch(context),
            self._incident_adapter.fetch(context),
            self._cost_adapter.fetch(context),
            self._compliance_adapter.fetch(context),
        )

        payload = {
            "risk": json.loads(risk_data),
            "architecture": json.loads(architecture_data),
            "incidents": json.loads(incident_data),
            "cost": json.loads(cost_data),
            "compliance": json.loads(compliance_data),
        }

        sources = (
            risk_sources
            + architecture_sources
            + incident_sources
            + cost_sources
            + compliance_sources
        )
        return json.dumps(payload), sources
