from __future__ import annotations

import structlog

from eip.core.event_bus import emit
from eip.core.models import DeploymentEvent
from eip.integrations.slack import notify_high_risk_deployment
from eip.pillars.risk_engine.explainer import RiskExplanationService
from eip.pillars.risk_engine.scorer import RiskScorer
from eip.pillars.risk_engine.store.historical_db import HistoricalDB


log = structlog.get_logger()


async def process_deployment(event: DeploymentEvent) -> None:
    """
    Orchestrate end-to-end deployment scoring and notifications.

    - Persist deployment event
    - Compute deterministic risk score
    - Generate LLM explanation
    - Persist risk score
    - Emit EventBridge event
    - Notify Slack for high/critical risk
    """

    db = HistoricalDB()

    log.info(
        "deployment_processing_started",
        service_name=event.service_name,
        commit=event.commit_sha[:8],
        environment=event.environment,
        build_url=event.build_url,
        event_type="deployment.scoring",
    )

    db.record_deployment(event)

    scorer = RiskScorer()
    base_score = scorer.score(event)

    explainer = RiskExplanationService()
    scored = await explainer.explain(event, base_score, base_score.factors)

    db.save_risk_score(event, scored)

    await emit(
        "eip.deployment.scored",
        {
            "service_name": event.service_name,
            "commit_sha": event.commit_sha,
            "risk_score": scored.score,
            "risk_tier": scored.tier,
        },
    )

    await notify_high_risk_deployment(event, scored)

    log.info(
        "deployment_processing_completed",
        service_name=event.service_name,
        commit=event.commit_sha[:8],
        risk_score=scored.score,
        risk_tier=scored.tier,
        event_type="deployment.scoring",
    )
