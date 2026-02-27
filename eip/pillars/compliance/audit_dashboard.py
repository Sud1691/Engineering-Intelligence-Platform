"""
Compliance & Security Copilot: Audit Dashboard

Maintains an audit readiness state machine so the organisation is always prepared.
"""

from __future__ import annotations

from typing import Any, Dict, List

import structlog


log = structlog.get_logger()


class AuditDashboard:
    """
    State machine for compiling the continuous audit readiness dashboard.
    """

    def compile_dashboard(
        self, 
        policy_evaluations: Dict[str, Any], 
        drifts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Aggregate evaluated policies and drifts into a dashboard view.
        """
        readiness_score = 100

        # Penalize for critical violations
        readiness_score -= (policy_evaluations.get("critical_count", 0) * 10)
        readiness_score -= sum(10 for d in drifts if d.get("severity") == "CRITICAL")
        
        # Penalize for high violations
        readiness_score -= (policy_evaluations.get("high_count", 0) * 5)
        
        readiness_score = max(0, readiness_score)

        return {
            "overall_readiness_score": readiness_score,
            "status": "READY" if readiness_score > 80 else "NEEDS_ATTENTION",
            "active_violations": policy_evaluations.get("findings", []),
            "infrastructure_drifts": drifts
        }
