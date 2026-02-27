"""
API Router for Cost Intelligence.
"""

from __future__ import annotations

from time import perf_counter
from typing import Any, Dict

from fastapi import APIRouter
import structlog

from eip.core.models import APIResponse
from eip.core.provider_registry import build_endpoint_meta, get_provider_registry
from eip.pillars.cost_intelligence.anomaly_detector import CostAnomalyDetector
from eip.pillars.cost_intelligence.optimizer import CostOptimizer
from eip.pillars.cost_intelligence.narrator import CostNarrator
from eip.pillars.cost_intelligence.reporter import ExecutiveCostReporter


log = structlog.get_logger()
router = APIRouter()


@router.get(
    "/report",
    response_model=APIResponse[Dict[str, Any]],
    summary="Get the latest cost executive report",
)
async def get_cost_report() -> APIResponse[Dict[str, Any]]:
    """
    Return the synthesized weekly cost report.
    """
    started_at = perf_counter()
    log.info("cost_report_requested")

    providers = get_provider_registry()
    cost_data = providers.cost.get_cost_data()
    resource_metrics = providers.cost.get_resource_metrics()

    anomaly_detector = CostAnomalyDetector()
    anomalies = anomaly_detector.detect_anomalies(cost_data)

    optimizer = CostOptimizer()
    opportunities = optimizer.find_opportunities(resource_metrics)

    narrator = CostNarrator()
    narrative = await narrator.generate_narrative(anomalies, opportunities)

    reporter = ExecutiveCostReporter()
    total_spend = sum(item.get("current_spend", 0.0) for item in cost_data)
    previous_spend = sum(item.get("baseline_spend", 0.0) for item in cost_data)
    report = await reporter.generate_weekly_report(
        total_spend=total_spend,
        previous_spend=previous_spend,
        narrative=narrative
    )

    return APIResponse[Dict[str, Any]](
        success=True,
        data=report,
        error=None,
        meta=build_endpoint_meta(
            pillar="cost",
            started_at=started_at,
        ),
    )
