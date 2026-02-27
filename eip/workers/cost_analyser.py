"""
Cost Analyser Worker

Async worker for nightly cost analysis.
"""

from __future__ import annotations

import structlog

from eip.core.event_bus import emit
from eip.core.provider_registry import get_provider_registry
from eip.pillars.cost_intelligence.anomaly_detector import CostAnomalyDetector
from eip.pillars.cost_intelligence.narrator import CostNarrator
from eip.pillars.cost_intelligence.optimizer import CostOptimizer
from eip.pillars.cost_intelligence.reporter import ExecutiveCostReporter


log = structlog.get_logger()


async def analyze_costs() -> None:
    """
    Run the nightly cost analysis job.
    
    1. Fetch latest cost data and resource metrics.
    2. Run anomaly and optimization detectors.
    3. Generate executive report via LLM.
    4. Emit event for downstream consumers (e.g., Slack notifications).
    """
    log.info(
        "nightly_cost_analysis_started",
        service_name="all-services",
        event_type="cost.nightly_analysis",
    )

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

    log.info(
        "nightly_cost_analysis_completed",
        service_name="all-services",
        event_type="cost.nightly_analysis",
        report_trend=report["trend"],
    )

    await emit(
        "eip.cost.analysis_completed",
        report
    )
