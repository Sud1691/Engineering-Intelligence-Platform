"""
Compliance & Security Copilot: Scanner

Extends the existing IaC vulnerability CLI logic to continuously scan
infrastructure configurations.
"""

from __future__ import annotations

from typing import Any, Dict, List

import structlog

from eip.core.models import DeploymentEvent


log = structlog.get_logger()


class ComplianceScanner:
    """
    Scans Code and IaC for compliance violations.
    """

    def scan_deployment(self, event: DeploymentEvent, changed_files: List[str]) -> List[Dict[str, Any]]:
        """
        Scan a deployment payload's files for violations.
        In MVP, uses naive text matching to simulate a scanner.
        """
        violations = []

        for file_path in changed_files:
            if file_path.endswith(".tf"):
                # Simulate a scanner finding hardcoded secrets or open ingress
                # Real implementation would run checkov or tfsec
                violations.append({
                    "rule_id": "CKV_AWS_1",
                    "resource": file_path,
                    "description": "Potential open security group detected in Terraform",
                    "severity": "HIGH",
                    "remediation": "Restrict ingress CIDR block to specific IP ranges"
                })
            elif "password" in file_path.lower() or "secret" in file_path.lower():
                violations.append({
                    "rule_id": "SEC_001",
                    "resource": file_path,
                    "description": "Potential hardcoded secret in filename or path",
                    "severity": "CRITICAL",
                    "remediation": "Move secrets to AWS Secrets Manager"
                })

        return violations
