from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from eip.core.models import DeploymentEvent, RiskFactor, RiskScore
from eip.pillars.risk_engine.store.historical_db import HistoricalDB
from eip.pillars.risk_engine.store.incident_db import IncidentDB
from eip.workers.incident_linker import process_pagerduty_webhook


def _event() -> DeploymentEvent:
    return DeploymentEvent(
        service_name="payments-api",
        environment="production",
        branch="main",
        commit_sha="abc12345",
        commit_message="Deploy",
        commit_author="Test",
        commit_author_email="test@example.com",
        changed_files=["src/payments.py"],
        lines_added=25,
        lines_deleted=3,
        deploy_hour=11,
        deploy_day=4,
        build_url="https://jenkins.example.com/job/1",
        coverage_delta=1.0,
    )


def _score() -> RiskScore:
    return RiskScore(
        score=70,
        tier="HIGH",
        probability_score=72,
        impact_score=67,
        recommended_action="Approval required.",
        explanation="",
        factors=[
            RiskFactor(
                name="change_size_medium",
                score=10.0,
                weight=1.0,
                evidence="lines_changed=28",
            )
        ],
    )


def test_incident_linker_persists_and_links_incident() -> None:
    HistoricalDB.reset_stub_state()
    IncidentDB.reset_stub_state()

    historical = HistoricalDB()
    deployment_event = _event()
    historical.record_deployment(deployment_event)
    historical.save_risk_score(deployment_event, _score())

    payload = {
        "event": {
            "event_type": "incident.triggered",
            "data": {
                "id": "INC-7001",
                "service": {"summary": "payments-api"},
                "urgency": "high",
                "status": "triggered",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        }
    }

    asyncio.run(process_pagerduty_webhook(payload))

    incident_rows = IncidentDB().get_incidents_by_service("payments-api")
    latest_score = historical.get_latest_risk_score("abc12345")

    assert len(incident_rows) == 1
    assert incident_rows[0]["id"] == "INC-7001"
    assert latest_score is not None
    assert latest_score["resulted_in_incident"] is True
    assert latest_score["linked_incident_id"] == "INC-7001"


def test_incident_linker_skips_when_deployment_outside_window() -> None:
    HistoricalDB.reset_stub_state()
    IncidentDB.reset_stub_state()

    historical = HistoricalDB()
    deployment_event = _event()
    historical.record_deployment(deployment_event)
    historical.save_risk_score(deployment_event, _score())

    deployments = historical.get_recent_deployments("payments-api")
    assert deployments
    deployments[0]["created_at"] = "2000-01-01T00:00:00+00:00"

    payload = {
        "event": {
            "event_type": "incident.triggered",
            "data": {
                "id": "INC-7002",
                "service": {"summary": "payments-api"},
                "urgency": "high",
                "status": "triggered",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        }
    }

    asyncio.run(process_pagerduty_webhook(payload))

    latest_score = historical.get_latest_risk_score("abc12345")
    assert latest_score is not None
    assert latest_score["resulted_in_incident"] is False
