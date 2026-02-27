from __future__ import annotations

from fastapi.testclient import TestClient

from eip.api.main import create_app


client = TestClient(create_app())


def _assert_meta_contract(meta: dict) -> None:
    assert "source_mode" in meta
    assert "generated_at" in meta
    assert "request_id" in meta
    assert "duration_ms" in meta
    assert "pillar" in meta


def test_architecture_dependencies_endpoint_uses_provider_snapshot() -> None:
    response = client.get("/architecture/payments-api/dependencies")
    payload = response.json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert isinstance(payload["data"], list)
    _assert_meta_contract(payload["meta"])


def test_cost_report_endpoint_returns_meta_and_payload() -> None:
    response = client.get("/cost/report")
    payload = response.json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert "trend" in payload["data"]
    assert payload["meta"]["source_mode"] == "stub"
    _assert_meta_contract(payload["meta"])


def test_compliance_dashboard_endpoint_returns_meta_and_payload() -> None:
    response = client.get("/compliance/dashboard")
    payload = response.json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert "overall_readiness_score" in payload["data"]
    assert payload["meta"]["source_mode"] == "stub"
    _assert_meta_contract(payload["meta"])


def test_nlq_ask_endpoint_returns_selected_intent_and_sources() -> None:
    response = client.post(
        "/ask",
        json={"question": "What is the blast radius for payments-api?"},
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["data"]["selected_intent"] != "processed"
    assert isinstance(payload["data"]["sources"], list)
    assert payload["data"]["source_mode"] == "stub"
    _assert_meta_contract(payload["meta"])


def test_incident_patterns_endpoint_returns_list() -> None:
    response = client.get("/incidents/payments-api/patterns")
    payload = response.json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert isinstance(payload["data"], list)
    assert payload["meta"]["source_mode"] == "stub"
    _assert_meta_contract(payload["meta"])


def test_incident_trajectory_endpoint_returns_prediction() -> None:
    response = client.get("/incidents/payments-api/trajectory")
    payload = response.json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert "escalation_risk" in payload["data"]
    _assert_meta_contract(payload["meta"])


def test_postmortem_draft_endpoint_returns_payload() -> None:
    response = client.post(
        "/incidents/postmortem/draft",
        json={
            "incident_id": "INC-1001",
            "service_name": "payments-api",
            "chat_transcript": "We saw elevated latency and rolled back deployment.",
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert "summary" in payload["data"]
    _assert_meta_contract(payload["meta"])


def test_jenkins_webhook_uses_api_response_envelope() -> None:
    response = client.post(
        "/risk/webhook/jenkins",
        json={
            "service_name": "payments-api",
            "environment": "production",
            "branch": "main",
            "commit_sha": "abc123",
            "commit_message": "deploy",
            "commit_author": "dev",
            "commit_author_email": "dev@example.com",
            "changed_files": ["src/app.py"],
            "lines_added": 10,
            "lines_deleted": 2,
            "deploy_hour": 11,
            "deploy_day": 2,
            "build_url": "https://jenkins.example.com/job/1",
            "coverage_delta": 0.5,
        },
    )
    payload = response.json()

    assert response.status_code == 202
    assert payload["success"] is True
    assert payload["data"]["status"] == "accepted"
    _assert_meta_contract(payload["meta"])


def test_pagerduty_webhook_uses_api_response_envelope() -> None:
    response = client.post(
        "/incidents/webhook/pagerduty",
        json={
            "event": {
                "event_type": "incident.triggered",
                "data": {
                    "id": "INC-9000",
                    "service": {"summary": "payments-api"},
                    "urgency": "high",
                    "status": "triggered",
                    "created_at": "2026-02-27T00:00:00+00:00",
                },
            }
        },
    )
    payload = response.json()

    assert response.status_code == 202
    assert payload["success"] is True
    assert payload["data"]["status"] == "accepted"
    _assert_meta_contract(payload["meta"])
