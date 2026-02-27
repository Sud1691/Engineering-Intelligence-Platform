"""
Cost Intelligence Engine: Reporter

Aggregates data into a weekly executive report.
"""

from __future__ import annotations

from typing import Any, Dict

import structlog

from eip.pillars.cost_intelligence.narrator import CostNarrator


log = structlog.get_logger()


class ExecutiveCostReporter:
    """
    Compiles the weekly executive cost report.
    """

    def __init__(self) -> None:
        self._narrator = CostNarrator()

    async def generate_weekly_report(
        self, 
        total_spend: float, 
        previous_spend: float,
        narrative: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compile the full weekly report payload.
        """
        trend = "up" if total_spend > previous_spend else "down"
        diff = abs(total_spend - previous_spend)
        pct_change = (diff / previous_spend) * 100 if previous_spend > 0 else 0
        
        return {
            "period": "Last 7 Days",
            "total_spend": total_spend,
            "previous_spend": previous_spend,
            "trend": trend,
            "percent_change": round(pct_change, 2),
            "executive_summary": narrative.get("executive_summary", ""),
            "top_anomalies": narrative.get("top_anomalies", []),
            "optimization_recommendations": narrative.get("optimization_recommendations", [])
        }
