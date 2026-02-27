from __future__ import annotations

from time import perf_counter

import structlog
from fastapi import APIRouter, BackgroundTasks, status

from eip.core.models import APIResponse, DeploymentEvent, RiskScore
from eip.core.provider_registry import (
    build_endpoint_meta,
    get_provider_registry,
)
from eip.core.settings import get_settings
from eip.pillars.risk_engine.explainer import RiskExplanationService
from eip.pillars.risk_engine.scorer import RiskScorer
from eip.workers.deployment_scorer import process_deployment


log = structlog.get_logger()
router = APIRouter()


def _build_risk_services() -> tuple[RiskScorer, RiskExplanationService]:
    # Keep dependency construction centralized on runtime settings/registry.
    _ = get_settings()
    _ = get_provider_registry()
    return RiskScorer(), RiskExplanationService()


@router.post(
    "/score",
    response_model=APIResponse[RiskScore],
    summary="Score a deployment event synchronously",
)
async def score_deployment(event: DeploymentEvent) -> APIResponse[RiskScore]:
    """
    Synchronously score a deployment event and return the detailed RiskScore.
    """

    started_at = perf_counter()
    scorer, explainer = _build_risk_services()
    base_score = scorer.score(event)

    scored = await explainer.explain(event, base_score, base_score.factors)

    log.info(
        "deployment_scored_sync",
        service=event.service_name,
        commit=event.commit_sha[:8],
        risk_score=scored.score,
        risk_tier=scored.tier,
    )

    return APIResponse[RiskScore](
        success=True,
        data=scored,
        error=None,
        meta=build_endpoint_meta(
            pillar="risk",
            started_at=started_at,
            extra={"service_name": event.service_name},
        ),
    )


@router.post(
    "/webhook/jenkins",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=APIResponse[dict[str, str]],
    summary="Jenkins deployment webhook",
)
async def jenkins_webhook(
    event: DeploymentEvent,
    bg: BackgroundTasks,
) -> APIResponse[dict[str, str]]:
    """
    Jenkins webhook endpoint.

    Must return quickly (202) and offload all heavy work to a background task.
    """

    started_at = perf_counter()
    log.info(
        "jenkins_webhook_received",
        service=event.service_name,
        commit=event.commit_sha[:8],
        environment=event.environment,
        build_url=event.build_url,
    )

    bg.add_task(process_deployment, event)

    return APIResponse[dict[str, str]](
        success=True,
        data={"status": "accepted"},
        error=None,
        meta=build_endpoint_meta(
            pillar="risk",
            started_at=started_at,
            extra={"service_name": event.service_name},
        ),
    )
