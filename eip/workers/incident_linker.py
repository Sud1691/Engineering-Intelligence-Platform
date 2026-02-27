"""
Incident linker worker. The most critical part of the feedback loop.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

import structlog

from eip.core.event_bus import emit
from eip.core.models import Incident
from eip.core.settings import get_settings
from eip.pillars.risk_engine.store.historical_db import HistoricalDB
from eip.pillars.risk_engine.store.incident_db import IncidentDB


log = structlog.get_logger()


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def _deployment_happened_within_window(
    *,
    deployment_item: dict[str, Any],
    incident_started_at: datetime,
    window_hours: int,
) -> bool:
    deployment_created_raw = deployment_item.get("created_at")
    if not isinstance(deployment_created_raw, str):
        return False

    deployment_started_at = _parse_datetime(deployment_created_raw)
    delta_seconds = (incident_started_at - deployment_started_at).total_seconds()
    if delta_seconds < 0:
        return False

    window_seconds = max(1, window_hours) * 3600
    return delta_seconds <= window_seconds


def _build_incident(incident_data: Dict[str, Any]) -> Incident | None:
    incident_id = str(incident_data.get("id", "")).strip()
    if not incident_id:
        return None

    service = incident_data.get("service", {}) or {}
    service_name = (
        service.get("summary")
        or service.get("name")
        or service.get("id")
        or "unknown-service"
    )

    urgency = str(incident_data.get("urgency", "low")).lower()
    severity = "SEV-1" if urgency == "high" else "SEV-3"

    status = str(incident_data.get("status", "triggered")).lower()
    started_at = _parse_datetime(incident_data.get("created_at"))
    resolved_at = (
        _parse_datetime(incident_data.get("last_status_change_at"))
        if status == "resolved"
        else None
    )

    return Incident(
        id=incident_id,
        service_name=service_name,
        severity=severity,
        started_at=started_at,
        resolved_at=resolved_at,
        root_cause=incident_data.get("title"),
        action_items=[],
    )


async def process_pagerduty_webhook(payload: Dict[str, Any]) -> None:
    """
    Process an incoming PagerDuty webhook event to drive the feedback loop.

    1. Extract incident details and service.
    2. Persist incident payload into IncidentDB.
    3. Lookup recent deployments for that service.
    4. Link incident -> deployment, emit event, mark risk score outcome.
    """
    event = payload.get("event", {})
    if not isinstance(event, dict):
        log.warning("pagerduty_webhook_invalid_payload", reason="event_not_dict")
        return

    event_type = str(event.get("event_type", ""))
    if event_type not in {"incident.triggered", "incident.resolved"}:
        log.info("pagerduty_event_ignored", event_type=event_type)
        return

    incident_data = event.get("data", {})
    if not isinstance(incident_data, dict):
        log.warning("pagerduty_webhook_invalid_payload", reason="data_not_dict")
        return

    incident = _build_incident(incident_data)
    if incident is None:
        log.warning("pagerduty_webhook_invalid_payload", reason="missing_incident_id")
        return

    log.info(
        "incident_webhook_received",
        event_type=event_type,
        incident_id=incident.id,
        service_name=incident.service_name,
    )

    incident_db = IncidentDB()
    incident_db.record_incident(incident)

    if event_type == "incident.triggered":
        await link_incident_to_deployment(
            incident_id=incident.id,
            service_name=incident.service_name,
            linked_at=incident.started_at.isoformat(),
            event_type=event_type,
        )


async def link_incident_to_deployment(
    incident_id: str,
    service_name: str,
    linked_at: str,
    event_type: str = "incident.triggered",
) -> None:
    """
    Attempt to link an incident to a recent deployment and update feedback loop state.
    """
    db = HistoricalDB()
    deployments = db.get_recent_deployments(service_name, limit=5)

    if not deployments:
        log.info(
            "no_recent_deployments_found",
            incident_id=incident_id,
            service_name=service_name,
            event_type=event_type,
        )
        return

    incident_started_at = _parse_datetime(linked_at)
    window_hours = get_settings().incident_link_window_hours
    matched = next(
        (
            deployment
            for deployment in deployments
            if _deployment_happened_within_window(
                deployment_item=deployment,
                incident_started_at=incident_started_at,
                window_hours=window_hours,
            )
        ),
        None,
    )
    if matched is None:
        log.info(
            "no_deployments_within_link_window",
            incident_id=incident_id,
            service_name=service_name,
            event_type=event_type,
            incident_link_window_hours=window_hours,
        )
        return

    commit_sha = str(matched.get("commit_sha", "")).strip()
    if not commit_sha:
        log.warning(
            "incident_link_failed_missing_commit",
            incident_id=incident_id,
            service_name=service_name,
            event_type=event_type,
        )
        return

    updated = db.mark_resulted_in_incident(
        commit_sha=commit_sha,
        incident_id=incident_id,
        linked_at=linked_at,
    )

    log.info(
        "incident_linked_to_deployment",
        incident_id=incident_id,
        service_name=service_name,
        event_type=event_type,
        commit_sha=commit_sha,
        risk_score_updated=updated,
        incident_link_window_hours=window_hours,
    )

    await emit(
        "eip.incident.linked_to_deployment",
        {
            "incident_id": incident_id,
            "commit_sha": commit_sha,
            "service_name": service_name,
            "confidence": "high",
            "risk_score_updated": updated,
            "linked_at": linked_at,
        },
    )
