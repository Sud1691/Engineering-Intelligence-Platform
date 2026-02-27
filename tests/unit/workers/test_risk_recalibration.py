from __future__ import annotations

import asyncio

from eip.core.models import DeploymentEvent, RiskFactor, RiskScore
from eip.pillars.risk_engine.store.historical_db import HistoricalDB
from eip.workers.risk_recalibration import run_weekly_recalibration


def _event(commit_sha: str) -> DeploymentEvent:
    return DeploymentEvent(
        service_name="payments-api",
        environment="production",
        branch="main",
        commit_sha=commit_sha,
        commit_message="deploy",
        commit_author="test",
        commit_author_email="test@example.com",
        changed_files=["src/app.py"],
        lines_added=12,
        lines_deleted=2,
        deploy_hour=10,
        deploy_day=3,
        build_url="https://jenkins.example.com/job/1",
        coverage_delta=0.0,
    )


def _score(tier: str, score: int, resulted_in_incident: bool) -> RiskScore:
    return RiskScore(
        score=score,
        tier=tier,
        probability_score=score,
        impact_score=score,
        recommended_action="review",
        explanation="",
        factors=[
            RiskFactor(
                name="environment_production",
                score=25.0,
                weight=1.0,
                evidence="environment=production",
            )
        ],
        resulted_in_incident=resulted_in_incident,
    )


def test_weekly_recalibration_returns_metrics_and_recommendations() -> None:
    HistoricalDB.reset_stub_state()
    db = HistoricalDB()

    samples = [
        ("sha1", "CRITICAL", 88, True),
        ("sha2", "HIGH", 75, False),
        ("sha3", "HIGH", 72, False),
        ("sha4", "LOW", 20, False),
    ]
    for commit_sha, tier, score, incident in samples:
        event = _event(commit_sha)
        db.record_deployment(event)
        db.save_risk_score(event, _score(tier=tier, score=score, resulted_in_incident=incident))

    result = asyncio.run(run_weekly_recalibration(limit=100))

    assert result["metrics"]["total_scores"] == 4
    assert result["metrics"]["total_incidents"] == 1
    assert isinstance(result["recommendations"], list)
    assert len(result["recommendations"]) >= 1
