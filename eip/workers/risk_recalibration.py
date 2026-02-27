"""
Weekly risk model recalibration worker.

This worker analyzes recent risk outcomes and emits recommendations that can
be used to tune deterministic weights.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

import structlog

from eip.core.event_bus import emit
from eip.pillars.risk_engine.store.historical_db import HistoricalDB


log = structlog.get_logger()


def _tier_is_high_or_critical(tier: str) -> bool:
    return tier in {"HIGH", "CRITICAL"}


def _compute_recommendations(metrics: Dict[str, Any]) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []

    total = metrics["total_scores"]
    if total == 0:
        return recommendations

    incident_rate = metrics["incident_rate"]
    false_positive_rate = metrics["high_or_critical_false_positive_rate"]

    if incident_rate > 0.35:
        recommendations.append(
            {
                "action": "increase_probability_weights",
                "reason": "High incident conversion from scored deployments.",
                "confidence": "MEDIUM",
            }
        )

    if false_positive_rate > 0.45:
        recommendations.append(
            {
                "action": "decrease_high_risk_sensitivity",
                "reason": "High false-positive rate for HIGH/CRITICAL tiers.",
                "confidence": "MEDIUM",
            }
        )

    if not recommendations:
        recommendations.append(
            {
                "action": "keep_weights_stable",
                "reason": "No significant drift detected in recent outcomes.",
                "confidence": "HIGH",
            }
        )

    return recommendations


async def run_weekly_recalibration(limit: int = 500) -> Dict[str, Any]:
    """
    Analyze recent scored deployments and emit recalibration guidance.
    """
    log.info(
        "risk_recalibration_started",
        service_name="risk-engine",
        event_type="risk.recalibration",
        limit=limit,
    )

    db = HistoricalDB()
    rows = db.list_recent_risk_scores(limit=limit)

    total_scores = len(rows)
    high_or_critical = [row for row in rows if _tier_is_high_or_critical(str(row.get("risk_tier", "")))]
    high_or_critical_count = len(high_or_critical)
    high_or_critical_incidents = sum(
        1 for row in high_or_critical if bool(row.get("resulted_in_incident"))
    )
    total_incidents = sum(1 for row in rows if bool(row.get("resulted_in_incident")))

    incident_rate = (total_incidents / total_scores) if total_scores else 0.0
    high_or_critical_false_positive_rate = (
        (high_or_critical_count - high_or_critical_incidents) / high_or_critical_count
        if high_or_critical_count
        else 0.0
    )

    metrics: Dict[str, Any] = {
        "total_scores": total_scores,
        "total_incidents": total_incidents,
        "incident_rate": round(incident_rate, 4),
        "high_or_critical_count": high_or_critical_count,
        "high_or_critical_incidents": high_or_critical_incidents,
        "high_or_critical_false_positive_rate": round(high_or_critical_false_positive_rate, 4),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    recommendations = _compute_recommendations(metrics)
    payload = {
        "metrics": metrics,
        "recommendations": recommendations,
    }

    log.info(
        "risk_recalibration_completed",
        service_name="risk-engine",
        event_type="risk.recalibration",
        total_scores=total_scores,
        total_incidents=total_incidents,
        recommendation_count=len(recommendations),
    )

    await emit("eip.risk.weights.recalibrated", payload)
    return payload

