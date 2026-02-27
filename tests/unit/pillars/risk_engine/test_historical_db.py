from __future__ import annotations

from eip.core.models import DeploymentEvent, RiskFactor, RiskScore
from eip.pillars.risk_engine.store.historical_db import HistoricalDB


def _event(service_name: str, commit_sha: str) -> DeploymentEvent:
    return DeploymentEvent(
        service_name=service_name,
        environment="production",
        branch="main",
        commit_sha=commit_sha,
        commit_message="Deploy commit",
        commit_author="Test User",
        commit_author_email="test@example.com",
        changed_files=["src/app.py"],
        lines_added=10,
        lines_deleted=2,
        deploy_hour=12,
        deploy_day=2,
        build_url="https://jenkins.example.com/job/test/1",
        coverage_delta=0.0,
    )


def _score(tier: str = "HIGH", score: int = 72) -> RiskScore:
    return RiskScore(
        score=score,
        tier=tier,
        probability_score=75,
        impact_score=67,
        recommended_action="Proceed with explicit approval.",
        explanation="",
        factors=[
            RiskFactor(
                name="environment_production",
                score=25.0,
                weight=1.0,
                evidence="environment=production",
            )
        ],
    )


def test_get_recent_deployments_returns_latest_first() -> None:
    HistoricalDB.reset_stub_state()
    db = HistoricalDB()

    event1 = _event("payments-api", "aaa111")
    event2 = _event("payments-api", "bbb222")

    db.record_deployment(event1)
    db.record_deployment(event2)

    deployments = db.get_recent_deployments("payments-api", limit=5)

    assert len(deployments) == 2
    assert deployments[0]["commit_sha"] == "bbb222"
    assert deployments[1]["commit_sha"] == "aaa111"


def test_mark_resulted_in_incident_updates_latest_risk_score() -> None:
    HistoricalDB.reset_stub_state()
    db = HistoricalDB()

    event = _event("payments-api", "deadbeef")
    db.record_deployment(event)
    db.save_risk_score(event, _score())

    updated = db.mark_resulted_in_incident(
        commit_sha="deadbeef",
        incident_id="INC-9001",
        linked_at="2026-02-27T00:00:00+00:00",
    )

    latest = db.get_latest_risk_score("deadbeef")

    assert updated is True
    assert latest is not None
    assert latest["resulted_in_incident"] is True
    assert latest["linked_incident_id"] == "INC-9001"
