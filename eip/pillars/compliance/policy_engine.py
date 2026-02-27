"""
Compliance & Security Copilot: Policy Engine

Evaluates findings against CIS AWS Benchmarks, internal security policies, 
and custom organizational controls.
"""

from __future__ import annotations

from typing import Any, Dict, List

import structlog


log = structlog.get_logger()


class PolicyEngine:
    """
    Evaluates scan findings against organizational policies.
    """

    def evaluate_violations(self, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Categorize and evaluate severity of raw violations.
        """
        if not violations:
            return {"status": "PASS", "critical_count": 0, "high_count": 0, "findings": []}

        critical_count = sum(1 for v in violations if v.get("severity") == "CRITICAL")
        high_count = sum(1 for v in violations if v.get("severity") == "HIGH")

        status = "FAIL" if critical_count > 0 else "WARNING" if high_count > 0 else "PASS"

        return {
            "status": status,
            "critical_count": critical_count,
            "high_count": high_count,
            "findings": violations
        }
