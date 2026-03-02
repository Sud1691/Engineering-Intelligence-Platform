"""
Critical integration cases derived from CLAUDE.md expectations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from eip.core.models import DeploymentEvent
from eip.pillars.risk_engine.extractors.jenkins_extractor import _detect_infra_flake
from eip.pillars.risk_engine.scorer import RiskScorer
from eip.pillars.risk_engine.store.historical_db import HistoricalDB
from eip.pillars.risk_engine.store.incident_db import IncidentDB
from eip.workers.incident_linker import process_pagerduty_webhook


def _high_risk_event() -> DeploymentEvent:
    return DeploymentEvent(
        service_name="payments-api",
        environment="production",
        branch="hotfix/db-migration-v3",
        commit_sha="abc123feed",
        commit_message="Friday migration rollout",
        commit_author="engineer",
        commit_author_email="engineer@example.com",
        changed_files=["migrations/0043.sql", "infra/network.tf", "src/payments.py"],
        lines_added=450,
        lines_deleted=10,
        deploy_hour=15,
        deploy_day=5,  # Friday
        build_url="https://jenkins.example.com/job/payments-api/301",
        coverage_delta=-8.0,
    )


def _low_risk_event() -> DeploymentEvent:
    return DeploymentEvent(
        service_name="reports-service",
        environment="dev",
        branch="fix/typo",
        commit_sha="def456beef",
        commit_message="Small text fix",
        commit_author="engineer",
        commit_author_email="engineer@example.com",
        changed_files=["reports/summary.py"],
        lines_added=4,
        lines_deleted=1,
        deploy_hour=11,
        deploy_day=2,  # Tuesday
        build_url="https://jenkins.example.com/job/reports-service/88",
        coverage_delta=2.0,
    )


def test_high_risk_friday_db_migration_payments() -> None:
    scorer = RiskScorer()
    score = scorer.score(_high_risk_event())
    assert score.score >= 75, f"Expected >= 75, got {score.score}"
    assert score.tier in {"CRITICAL", "HIGH"}


def test_low_risk_tuesday_small_change() -> None:
    scorer = RiskScorer()
    score = scorer.score(_low_risk_event())
    assert score.score <= 30, f"Expected <= 30, got {score.score}"
    assert score.tier == "LOW"


def test_infrastructure_flake_identified() -> None:
    infra_errors = ["Connection timed out", "Agent went offline", "OOMKilled"]
    for err in infra_errors:
        assert _detect_infra_flake(err), f"Should detect infra flake: {err}"

    code_errors = ["AssertionError: expected 200", "NullPointerException"]
    for err in code_errors:
        assert not _detect_infra_flake(err), f"Should not detect infra flake: {err}"


@pytest.mark.asyncio
async def test_feedback_loop_links_incident_and_marks_result(
    dynamodb_tables,  # noqa: ARG001
) -> None:
    IncidentDB.reset_stub_state()
    HistoricalDB.reset_stub_state()

    db = HistoricalDB()
    scorer = RiskScorer()
    deployment = DeploymentEvent(
        service_name="auth-service",
        environment="production",
        branch="feature/jwt-refresh",
        commit_sha="feed0001",
        commit_message="Add JWT refresh flow",
        commit_author="auth-dev",
        commit_author_email="auth-dev@example.com",
        changed_files=["src/auth/jwt.py"],
        lines_added=85,
        lines_deleted=20,
        deploy_hour=14,
        deploy_day=1,
        build_url="https://jenkins.example.com/job/auth-service/44",
        coverage_delta=0.5,
    )

    score = scorer.score(deployment)
    db.record_deployment(deployment)
    db.save_risk_score(deployment, score)

    initial = db.get_latest_risk_score("feed0001")
    assert initial is not None
    assert initial["resulted_in_incident"] is False

    pd_payload = {
        "event": {
            "event_type": "incident.triggered",
            "data": {
                "id": "PD-TEST-001",
                "service": {"summary": "auth-service"},
                "urgency": "high",
                "status": "triggered",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        }
    }

    # Avoid real EventBridge call in integration tests.
    with patch("eip.workers.incident_linker.emit", new_callable=AsyncMock):
        await process_pagerduty_webhook(pd_payload)

    updated = db.get_latest_risk_score("feed0001")
    assert updated is not None
    assert updated["resulted_in_incident"] is True
    assert updated["linked_incident_id"] == "PD-TEST-001"
