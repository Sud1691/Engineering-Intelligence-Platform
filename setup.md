# EIP Setup Guide (Platform Module + User tfvars)

This project is designed like a platform Terraform module:
- Platform team provides code + defaults.
- Product team/user provides environment-specific values using `platform.auto.tfvars`.

Use this guide to run the platform in stub mode now, and later switch to live mode.

## 1. Prerequisites

- Python 3.12+
- `pip`
- `terraform` 1.6+ (only needed when provisioning AWS resources)
- (Optional for tests now) `pytest`

## 2. Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Create Your tfvars File

Copy the example and customize values:

```bash
cp platform.auto.tfvars.example platform.auto.tfvars
```

Minimum keys:

```hcl
eip_runtime_mode = "stub"
eip_enable_live_mode = false
eip_aws_region = "us-east-1"
eip_event_bus_name = "eip-event-bus-dev"
eip_deployments_table_name = "eip-deployments-dev"
eip_risk_scores_table_name = "eip-risk-scores-dev"
eip_incidents_table_name = "eip-incidents-dev"
eip_integrations_secret_name = "eip/integrations/dev"
eip_slack_default_channel = "#eip-dev-alerts"
eip_incident_link_window_hours = 2
provision_core_resources = false
create_worker_role = false
create_integrations_secret = false
create_integrations_secret_version = false
```

## 4. Configuration Resolution Order

The platform resolves config in this order:
1. Environment variable
2. `platform.auto.tfvars` (or path in `EIP_TFVARS_PATH`)
3. Built-in defaults

Useful env overrides:
- `EIP_TFVARS_PATH`
- `EIP_RUNTIME_MODE`
- `EIP_ENABLE_LIVE_MODE`
- `EIP_AWS_REGION`
- `EIP_EVENT_BUS_NAME`

## 5. Provision Core Infrastructure (Optional)

By default, local stub mode requires no cloud resources.

To provision core AWS objects from `infra/terraform`:

```bash
terraform -chdir=infra/terraform init
terraform -chdir=infra/terraform plan \
  -var-file=../../platform.auto.tfvars \
  -var='provision_core_resources=true'
terraform -chdir=infra/terraform apply \
  -var-file=../../platform.auto.tfvars \
  -var='provision_core_resources=true'
```

What this provisions:
- EventBridge bus + baseline EIP event rules
- DynamoDB tables for deployments, risk scores, incidents
- Optional IAM worker role (`create_worker_role=true`)
- Optional integrations secret container (`create_integrations_secret=true`)

Module details:
- [infra/terraform/README.md](/Users/sudhanshujain/Desktop/automation_idea/infra/terraform/README.md)

## 6. Run the API

```bash
uvicorn eip.api.main:app --reload --host 0.0.0.0 --port 8000
```

Open:
- Swagger UI: `http://localhost:8000/docs`

## 7. Quick Smoke Calls

Risk scoring:

```bash
curl -X POST http://localhost:8000/risk/score \
  -H "Content-Type: application/json" \
  -d '{
    "service_name":"payments-api",
    "environment":"production",
    "branch":"main",
    "commit_sha":"abc123",
    "commit_message":"test deploy",
    "commit_author":"dev",
    "commit_author_email":"dev@example.com",
    "changed_files":["src/app.py"],
    "lines_added":10,
    "lines_deleted":2,
    "deploy_hour":11,
    "deploy_day":2,
    "build_url":"https://jenkins.example.com/job/1",
    "coverage_delta":0.5
  }'
```

NLQ:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is blast radius of payments-api?"}'
```

Cost report:

```bash
curl http://localhost:8000/cost/report
```

Compliance dashboard:

```bash
curl http://localhost:8000/compliance/dashboard
```

Incident patterns:

```bash
curl http://localhost:8000/incidents/payments-api/patterns
```

Incident trajectory:

```bash
curl http://localhost:8000/incidents/payments-api/trajectory
```

## 8. Run Tests

```bash
pytest
```

If `pytest` is unavailable:

```bash
python3 -m compileall eip tests
```

## 9. Switching to Live Mode Later

When real infra/integrations are ready:
1. Set `eip_runtime_mode = "live"` in tfvars.
2. Set `eip_enable_live_mode = true`.
3. Run Terraform apply with `provision_core_resources=true`.
4. Implement live providers in provider registry.

Detailed live replacement checklist is here:
- [docs/live_setup.md](/Users/sudhanshujain/Desktop/automation_idea/docs/live_setup.md)

Architecture diagram:
- [docs/architecture.md](/Users/sudhanshujain/Desktop/automation_idea/docs/architecture.md)
