"""
API router for the Compliance & Security Copilot.
"""

from __future__ import annotations

from time import perf_counter
from typing import Any, Dict

from fastapi import APIRouter
import structlog

from eip.core.models import APIResponse
from eip.core.provider_registry import build_endpoint_meta, get_provider_registry
from eip.pillars.compliance.audit_dashboard import AuditDashboard
from eip.pillars.compliance.drift_detector import DriftDetector
from eip.pillars.compliance.policy_engine import PolicyEngine


log = structlog.get_logger()
router = APIRouter()


@router.get(
    "/dashboard",
    response_model=APIResponse[Dict[str, Any]],
    summary="Get the Audit Readiness Dashboard",
)
async def get_audit_dashboard() -> APIResponse[Dict[str, Any]]:
    """
    Returns the real-time continuous compliance state.
    """
    started_at = perf_counter()
    log.info("compliance_audit_dashboard_requested")

    providers = get_provider_registry()
    violations = providers.compliance.get_violations()
    account_configs = providers.compliance.get_account_configs()

    policy_engine = PolicyEngine()
    evaluated_policies = policy_engine.evaluate_violations(violations)

    drift_detector = DriftDetector()
    drifts = drift_detector.detect_drift(account_configs)

    dashboard = AuditDashboard()
    result = dashboard.compile_dashboard(evaluated_policies, drifts)

    return APIResponse[Dict[str, Any]](
        success=True,
        data=result,
        error=None,
        meta=build_endpoint_meta(
            pillar="compliance",
            started_at=started_at,
        ),
    )
