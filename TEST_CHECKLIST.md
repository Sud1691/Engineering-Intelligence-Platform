# EIP Test Checklist

## Fresh Machine Setup

### Prerequisites

- Python 3.12+
- `pip`

### Setup Steps

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp platform.auto.tfvars.example platform.auto.tfvars
```

## Start The App

```bash
.venv/bin/uvicorn eip.api.main:app --host 0.0.0.0 --port 8000
```

Open:
- `http://localhost:8000/docs`

## Basic Health

```bash
curl http://localhost:8000/openapi.json
```

## Core Smoke Tests

### Risk

```bash
curl -X POST http://localhost:8000/risk/score \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "payments-api",
    "environment": "production",
    "branch": "hotfix/payment-timeout",
    "commit_sha": "abc123def456",
    "commit_message": "Hotfix payment timeout issue",
    "commit_author": "Oncall Engineer",
    "commit_author_email": "oncall@example.com",
    "changed_files": ["src/payments.py", "infra/security.tf", "migrations/0043.sql"],
    "lines_added": 320,
    "lines_deleted": 40,
    "deploy_hour": 19,
    "deploy_day": 5,
    "build_url": "https://jenkins.example.com/job/payments/99",
    "coverage_delta": -1.0
  }'
```

### Architecture

```bash
curl http://localhost:8000/architecture/payments-api/dependencies
```

```bash
curl http://localhost:8000/architecture/payments-api/blast-radius
```

### Incidents

```bash
curl http://localhost:8000/incidents/payments-api/patterns
```

```bash
curl http://localhost:8000/incidents/payments-api/trajectory
```

```bash
curl -X POST http://localhost:8000/incidents/postmortem/draft \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC-1001",
    "service_name": "payments-api",
    "chat_transcript": "We saw elevated latency and rolled back deployment."
  }'
```

### Cost

```bash
curl http://localhost:8000/cost/report
```

### Compliance

```bash
curl http://localhost:8000/compliance/dashboard
```

### NLQ

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the blast radius for payments-api?"}'
```

## Workflow Tests

### Jenkins Webhook

```bash
curl -X POST http://localhost:8000/risk/webhook/jenkins \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "payments-api",
    "environment": "production",
    "branch": "main",
    "commit_sha": "feedface123",
    "commit_message": "deploy",
    "commit_author": "dev",
    "commit_author_email": "dev@example.com",
    "changed_files": ["src/app.py"],
    "lines_added": 10,
    "lines_deleted": 2,
    "deploy_hour": 11,
    "deploy_day": 2,
    "build_url": "https://jenkins.example.com/job/1",
    "coverage_delta": 0.5
  }'
```

### PagerDuty Webhook

```bash
curl -X POST http://localhost:8000/incidents/webhook/pagerduty \
  -H "Content-Type: application/json" \
  -d '{
    "event": {
      "event_type": "incident.triggered",
      "data": {
        "id": "INC-9000",
        "service": {"summary": "payments-api"},
        "urgency": "high",
        "status": "triggered",
        "created_at": "2026-02-27T00:00:00+00:00"
      }
    }
  }'
```

## Automated Tests

### Full Test Suite

```bash
.venv/bin/pytest -v
```

### Integration Tests

```bash
.venv/bin/pytest tests/integration/test_critical_cases.py -v
```

### API Tests

```bash
.venv/bin/pytest tests/unit/api/test_routes.py -v
```

### Worker Tests

```bash
.venv/bin/pytest tests/unit/workers -v
```

### Pillar Tests

```bash
.venv/bin/pytest tests/unit/pillars -v
```

### Core Tests

```bash
.venv/bin/pytest tests/unit/core -v
```

### Compile Sanity Check

```bash
.venv/bin/python -m compileall eip tests
```

## Expected Signals

- Swagger UI loads.
- `POST /risk/score` returns `success: true`.
- Architecture endpoints return dependency lists.
- Incidents, cost, compliance, and NLQ endpoints return valid JSON.
- Webhook endpoints return `202 Accepted`.
- The pytest suite passes.
