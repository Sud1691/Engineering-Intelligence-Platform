"""
Terraform extractor for the Deployment Risk Engine.
"""

from __future__ import annotations

from typing import Any, Dict

import structlog

from eip.core.models import DeploymentEvent


log = structlog.get_logger()


class TerraformExtractor:
    """
    Extracts risk signals from Terraform changes.
    """

    def has_iac_changes(self, event: DeploymentEvent) -> bool:
        """
        Determine if the deployment event includes any infrastructure-as-code changes.
        """
        iac_prefixes = ("infra/", "terraform/", "modules/")
        iac_extensions = (".tf", ".tfvars", ".hcl")
        
        for file_path in event.changed_files:
            if file_path.startswith(iac_prefixes) or file_path.endswith(iac_extensions):
                return True
        return False

    def analyze_plan(self, plan_output: str) -> Dict[str, Any]:
        """
        Parse raw Terraform plan output to detect risky operations.
        For MVP, we use naive text matching.
        """
        if not plan_output:
            return {"adds": 0, "changes": 0, "destroys": 0, "is_risky": False}

        # Look for the summary line: "Plan: X to add, Y to change, Z to destroy."
        adds = changes = destroys = 0
        is_risky = False

        if "to destroy" in plan_output:
            # Naive heuristic: any destroy is potentially risky
            is_risky = True
            
        return {
            "adds": adds,
            "changes": changes,
            "destroys": destroys, 
            "is_risky": is_risky
        }
