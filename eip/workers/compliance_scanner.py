"""
Async worker for continuous compliance scanning.
"""

from __future__ import annotations

import structlog

from eip.core.event_bus import emit
from eip.core.models import DeploymentEvent
from eip.core.provider_registry import get_provider_registry
from eip.pillars.compliance.drift_detector import DriftDetector
from eip.pillars.compliance.policy_engine import PolicyEngine
from eip.pillars.compliance.scanner import ComplianceScanner


log = structlog.get_logger()


async def process_compliance_scan(event: DeploymentEvent) -> None:
    """
    Run continuous compliance scans against IaC or Code upon deployment.
    """
    log.info(
        "compliance_scan_started",
        service_name=event.service_name,
        commit=event.commit_sha[:8],
        event_type="deployment.scan",
    )

    providers = get_provider_registry()
    scanner = ComplianceScanner()
    violations = scanner.scan_deployment(event, event.changed_files)

    policy_engine = PolicyEngine()
    evaluation = policy_engine.evaluate_violations(violations)

    drift_detector = DriftDetector()
    drifts = drift_detector.detect_drift(providers.compliance.get_account_configs())

    log.info(
        "compliance_scan_completed",
        service_name=event.service_name,
        commit=event.commit_sha[:8],
        event_type="deployment.scan",
        status=evaluation.get("status"),
        critical_count=evaluation.get("critical_count"),
        high_count=evaluation.get("high_count"),
        drift_count=len(drifts),
    )

    if evaluation.get("status") in ("FAIL", "WARNING") or drifts:
        await emit(
            "eip.compliance.violation_detected",
            {
                "service_name": event.service_name,
                "commit_sha": event.commit_sha,
                "policy_evaluation": evaluation,
                "drifts": drifts,
            },
        )
