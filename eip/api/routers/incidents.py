"""
API router for Incident Intelligence.
"""

from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from fastapi import APIRouter, BackgroundTasks, status
from pydantic import BaseModel, Field
import structlog

from eip.core.models import APIResponse, Incident
from eip.core.provider_registry import build_endpoint_meta, get_provider_registry
from eip.pillars.incident_intelligence.pattern_detector import IncidentPatternDetector
from eip.pillars.incident_intelligence.postmortem_gen import PostmortemGenerator
from eip.pillars.incident_intelligence.trajectory import IncidentTrajectoryPredictor
from eip.workers.incident_linker import process_pagerduty_webhook


log = structlog.get_logger()
router = APIRouter()


class PagerDutyServiceModel(BaseModel):
    id: str | None = None
    summary: str | None = None


class PagerDutyIncidentDataModel(BaseModel):
    id: str
    service: PagerDutyServiceModel | None = None
    urgency: str | None = None
    status: str | None = None
    created_at: str | None = None
    last_status_change_at: str | None = None


class PagerDutyEventModel(BaseModel):
    event_type: str
    data: PagerDutyIncidentDataModel


class PagerDutyWebhookModel(BaseModel):
    event: PagerDutyEventModel


class PostmortemDraftRequest(BaseModel):
    incident_id: str
    service_name: str
    chat_transcript: str = Field(min_length=1)


def _parse_dt(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def _severity_from_raw(raw: dict[str, Any]) -> str:
    value = str(raw.get("severity", "SEV-3")).upper()
    if value in {"SEV-1", "SEV-2", "SEV-3", "SEV-4"}:
        return value
    return "SEV-3"


def _incident_from_dict(raw: dict[str, Any]) -> Incident:
    return Incident(
        id=str(raw.get("id", "unknown")),
        service_name=str(raw.get("service_name", "unknown-service")),
        severity=_severity_from_raw(raw),
        started_at=_parse_dt(raw.get("started_at")),
        resolved_at=_parse_dt(raw.get("resolved_at")) if raw.get("resolved_at") else None,
        root_cause=raw.get("root_cause"),
        linked_deploy=raw.get("linked_deploy"),
        action_items=[],
    )


@router.post(
    "/webhook/pagerduty",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=APIResponse[dict[str, str]],
    summary="PagerDuty incident webhook",
)
async def pagerduty_webhook(
    payload: PagerDutyWebhookModel,
    bg: BackgroundTasks,
) -> APIResponse[dict[str, str]]:
    """
    Receive incident webhooks from PagerDuty.

    Must return 202 quickly and offload processing.
    """
    started_at = perf_counter()
    bg.add_task(process_pagerduty_webhook, payload.model_dump(mode="python"))
    return APIResponse[dict[str, str]](
        success=True,
        data={"status": "accepted"},
        error=None,
        meta=build_endpoint_meta(
            pillar="incidents",
            started_at=started_at,
        ),
    )


@router.get(
    "/{service_name}/patterns",
    response_model=APIResponse[list[dict[str, Any]]],
    summary="Detect recurring incident patterns for a service",
)
async def get_incident_patterns(
    service_name: str,
    limit: int = 10,
) -> APIResponse[list[dict[str, Any]]]:
    started_at = perf_counter()
    providers = get_provider_registry()
    raw_incidents = providers.incident.get_recent_incidents(service_name=service_name, limit=limit)
    incidents = [_incident_from_dict(row) for row in raw_incidents]

    detector = IncidentPatternDetector()
    patterns = await detector.detect_patterns(incidents)

    return APIResponse[list[dict[str, Any]]](
        success=True,
        data=patterns,
        error=None,
        meta=build_endpoint_meta(
            pillar="incidents",
            started_at=started_at,
            extra={"service_name": service_name, "incident_count": len(incidents)},
        ),
    )


@router.get(
    "/{service_name}/trajectory",
    response_model=APIResponse[dict[str, Any]],
    summary="Predict incident escalation trajectory for a service",
)
async def get_incident_trajectory(service_name: str) -> APIResponse[dict[str, Any]]:
    started_at = perf_counter()
    providers = get_provider_registry()
    incident_rows = providers.incident.get_recent_incidents(service_name=service_name, limit=10)
    risk_overview = providers.risk.get_risk_overview(service_name=service_name)

    predictor = IncidentTrajectoryPredictor()
    prediction = await predictor.predict_trajectory(
        service_name=service_name,
        recent_data={
            "recent_incidents": incident_rows,
            "risk_overview": risk_overview,
            "open_action_items": [],
        },
    )

    return APIResponse[dict[str, Any]](
        success=True,
        data=prediction,
        error=None,
        meta=build_endpoint_meta(
            pillar="incidents",
            started_at=started_at,
            extra={"service_name": service_name},
        ),
    )


@router.post(
    "/postmortem/draft",
    response_model=APIResponse[dict[str, Any]],
    summary="Generate a draft postmortem",
)
async def generate_postmortem_draft(
    request: PostmortemDraftRequest,
) -> APIResponse[dict[str, Any]]:
    started_at = perf_counter()
    providers = get_provider_registry()
    candidate_rows = providers.incident.get_recent_incidents(
        service_name=request.service_name,
        limit=30,
    )

    selected = next(
        (row for row in candidate_rows if str(row.get("id")) == request.incident_id),
        None,
    )
    incident = _incident_from_dict(
        selected
        or {
            "id": request.incident_id,
            "service_name": request.service_name,
            "severity": "SEV-3",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    generator = PostmortemGenerator()
    draft = await generator.generate_draft(incident, request.chat_transcript)

    log.info(
        "postmortem_draft_generated",
        service_name=request.service_name,
        incident_id=request.incident_id,
    )

    return APIResponse[dict[str, Any]](
        success=True,
        data=draft,
        error=None,
        meta=build_endpoint_meta(
            pillar="incidents",
            started_at=started_at,
            extra={
                "service_name": request.service_name,
                "incident_id": request.incident_id,
            },
        ),
    )
