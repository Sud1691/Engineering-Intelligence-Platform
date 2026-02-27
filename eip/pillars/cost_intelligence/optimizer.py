"""
Cost Intelligence Engine: Optimizer

Surfaces optimisation opportunities automatically.
"""

from __future__ import annotations

from typing import Any, Dict, List

import structlog


log = structlog.get_logger()


class CostOptimizer:
    """
    Finds optimization opportunities based on AWS usage metrics (e.g., underutilized EC2/ECS).
    """

    def find_opportunities(self, resource_metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Scan resources for under-utilization or waste.
        """
        opportunities = []

        # Example MVP heuristics:
        # - compute instances with <5% CPU utilization over 7 days
        # - unattached EBS volumes
        # - obsolete snapshots
        
        for resource in resource_metrics:
            resource_type = resource.get("type")
            
            if resource_type == "EC2_INSTANCE":
                cpu_utilization = resource.get("avg_cpu_7d", 100.0)
                if cpu_utilization < 5.0:
                    opportunities.append({
                        "resource_id": resource.get("id"),
                        "resource_type": resource_type,
                        "finding": "Severely underutilized compute",
                        "estimated_monthly_savings": resource.get("monthly_cost", 0.0),
                        "recommended_action": "Downsize or terminate instance"
                    })
            elif resource_type == "EBS_VOLUME":
                state = resource.get("state")
                if state == "available":  # Unattached
                    opportunities.append({
                        "resource_id": resource.get("id"),
                        "resource_type": resource_type,
                        "finding": "Unattached EBS volume",
                        "estimated_monthly_savings": resource.get("monthly_cost", 0.0),
                        "recommended_action": "Snapshot and delete volume"
                    })

        return opportunities
