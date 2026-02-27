"""
Cost Intelligence Engine: Anomaly Detector

Detects spend anomalies from AWS Cost Explorer data.
"""

from __future__ import annotations

from typing import Any, Dict, List

import structlog

from eip.core.models import ServiceNode


log = structlog.get_logger()


class CostAnomalyDetector:
    """
    Detects cost anomalies by analyzing historical spend versus current spend.
    """

    def detect_anomalies(self, recent_cost_data: List[Dict[str, Any]], threshold_pct: float = 20.0) -> List[Dict[str, Any]]:
        """
        Identify services or accounts where the cost has spiked more than `threshold_pct`.
        """
        anomalies = []
        
        # In a real implementation this would compare trailing 7 days vs previous 7 days
        # For the MVP, we assume recent_cost_data contains aggregated changes
        
        for data in recent_cost_data:
            service = data.get("service_name")
            current_spend = data.get("current_spend", 0.0)
            baseline_spend = data.get("baseline_spend", 0.0)
            
            if baseline_spend == 0:
                continue
                
            percent_change = ((current_spend - baseline_spend) / baseline_spend) * 100
            
            if percent_change >= threshold_pct:
                anomalies.append({
                    "service_name": service,
                    "percent_increase": round(percent_change, 2),
                    "absolute_increase": round(current_spend - baseline_spend, 2),
                    "current_spend": current_spend,
                    "baseline_spend": baseline_spend
                })
                
                log.info(
                    "cost_anomaly_detected",
                    service=service,
                    percent_increase=percent_change,
                    absolute_increase=current_spend - baseline_spend
                )
                
        return anomalies
