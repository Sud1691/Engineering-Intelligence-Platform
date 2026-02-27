from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from eip.core.models import DeploymentEvent
from eip.pillars.risk_engine.store.historical_db import HistoricalDB
from eip.pillars.risk_engine.store.incident_db import IncidentDB
from eip.workers.deployment_scorer import process_deployment
from eip.workers.incident_linker import process_pagerduty_webhook


def _deployment_event() -> DeploymentEvent:
    return DeploymentEvent(
        service_name="payments-api",
        environment="production",
        branch="hotfix/payment-timeout",
        commit_sha="feedface",
        commit_message="Hotfix payment timeout",
        commit_author="Oncall Engineer",
        commit_author_email="oncall@example.com",
        changed_files=["src/payments.py", "infra/security.tf"],
        lines_added=320,
        lines_deleted=40,
        deploy_hour=19,
        deploy_day=5,
        build_url="https://jenkins.example.com/job/payments/99",
        coverage_delta=-1.0,
    )


def test_feedback_loop_marks_deployment_after_incident_link() -> None:
    HistoricalDB.reset_stub_state()
    IncidentDB.reset_stub_state()

    deployment = _deployment_event()
    asyncio.run(process_deployment(deployment))

    before_link = HistoricalDB().get_latest_risk_score("feedface")
    assert before_link is not None
    assert before_link["resulted_in_incident"] is False

    payload = {
        "event": {
            "event_type": "incident.triggered",
            "data": {
                "id": "INC-LOOP-1",
                "service": {"summary": "payments-api"},
                "urgency": "high",
                "status": "triggered",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        }
    }
    asyncio.run(process_pagerduty_webhook(payload))

    after_link = HistoricalDB().get_latest_risk_score("feedface")
    assert after_link is not None
    assert after_link["resulted_in_incident"] is True
    assert after_link["linked_incident_id"] == "INC-LOOP-1"
