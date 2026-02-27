# EIP Live Setup Guide (Replacing Stubbed Objects)

This document lists every stubbed dependency that must be replaced for full live operation.
For local usage and step-by-step startup, see [setup.md](/Users/sudhanshujain/Desktop/automation_idea/setup.md).
For architecture, see [docs/architecture.md](/Users/sudhanshujain/Desktop/automation_idea/docs/architecture.md).

Runtime guardrails:
- `EIP_RUNTIME_MODE=stub` is default.
- `EIP_RUNTIME_MODE=live` is allowed only when `EIP_ENABLE_LIVE_MODE=true`.

## 1. Runtime & Configuration

### Required
- Environment variables:
  - `EIP_RUNTIME_MODE`
  - `EIP_ENABLE_LIVE_MODE`
- Live provider implementations replacing stub classes in [eip/stubs/providers.py](/Users/sudhanshujain/Desktop/automation_idea/eip/stubs/providers.py)
- Registry wiring update in [eip/core/provider_registry.py](/Users/sudhanshujain/Desktop/automation_idea/eip/core/provider_registry.py)

### Replace Stub Targets
- `StubRiskDataProvider` -> `LiveRiskDataProvider`
- `StubArchitectureDataProvider` -> `LiveArchitectureDataProvider`
- `StubIncidentDataProvider` -> `LiveIncidentDataProvider`
- `StubCostDataProvider` -> `LiveCostDataProvider`
- `StubComplianceDataProvider` -> `LiveComplianceDataProvider`
- `StubNLQDataProvider` -> live-backed NLQ data provider (adapter router can remain)

## 2. Secrets Manager

### Required Secret
- Name: `eip/integrations`

### Required Keys
- `slack_bot_token`
- `slack_default_channel`
- `pagerduty_token`
- Add Jenkins/GitHub/API tokens as integration scope expands

### Stub Replacement Location
- Current stub fallback: [eip/core/secrets.py](/Users/sudhanshujain/Desktop/automation_idea/eip/core/secrets.py)
- Replace with live Secrets Manager payloads and remove fallback assumptions for production.

## 3. Event Bus

### Required AWS Object
- EventBridge bus: `eip-event-bus`

### Required IAM
- `events:PutEvents` on the target bus

### Stub Replacement Location
- Current stub emit path: [eip/core/event_bus.py](/Users/sudhanshujain/Desktop/automation_idea/eip/core/event_bus.py)
- Live mode should already call `put_events`; validate permissions + DLQ/retry policy.

## 4. Deployment Risk Persistence

### Required AWS Objects
- DynamoDB table: `eip-deployments`
- DynamoDB table: `eip-risk-scores`

### Required Key Patterns
- Deployments:
  - `pk = SERVICE#{service_name}`
  - `sk = DEPLOY#{timestamp}#{commit}`
- Risk scores:
  - `pk = DEPLOY#{commit_sha}`
  - `sk = SCORE#{timestamp}`

### Required IAM
- `dynamodb:PutItem`
- `dynamodb:Query`
- `dynamodb:UpdateItem`
- `dynamodb:GetItem` (if needed for diagnostics)

### Stub Replacement Location
- Current stub fallback/in-memory: [historical_db.py](/Users/sudhanshujain/Desktop/automation_idea/eip/pillars/risk_engine/store/historical_db.py)

## 5. Incident Persistence & Linking

### Required AWS Objects
- DynamoDB table: `eip-incidents`

### Required Integrations
- PagerDuty webhook endpoint pointed to:
  - `/incidents/webhook/pagerduty`
- Service mapping source (PagerDuty service ID -> internal service name)

### Required IAM
- `dynamodb:PutItem`
- `dynamodb:Query`
- `dynamodb:GetItem`

### Stub Replacement Location
- Current stub fallback/in-memory: [incident_db.py](/Users/sudhanshujain/Desktop/automation_idea/eip/pillars/risk_engine/store/incident_db.py)
- Worker linkage logic: [incident_linker.py](/Users/sudhanshujain/Desktop/automation_idea/eip/workers/incident_linker.py)

## 6. LLM (Anthropic)

### Required
- Anthropic SDK installed in runtime image
- Valid API key delivery via secure secret injection

### Stub Replacement Location
- Stub response mode in [llm.py](/Users/sudhanshujain/Desktop/automation_idea/eip/core/llm.py)
- In live mode, verify:
  - model access
  - timeouts/retries
  - token budget enforcement

## 7. Slack Notifications

### Required
- Slack app + bot token with permission to post messages
- Destination channels configured

### Required IAM/Secrets
- Secret key: `slack_bot_token`, `slack_default_channel`

### Stub Replacement Location
- Stub short-circuit in [slack.py](/Users/sudhanshujain/Desktop/automation_idea/eip/integrations/slack.py)

## 8. Architecture Data Sources

### Required
- CloudTrail event ingestion source
- Terraform state source (commonly S3 backend)
- X-Ray service map source
- Optional service catalog for ownership/team mapping

### Stub Replacement Location
- Provider data currently static in [eip/stubs/providers.py](/Users/sudhanshujain/Desktop/automation_idea/eip/stubs/providers.py)
- Router/worker consumers:
  - [architecture.py](/Users/sudhanshujain/Desktop/automation_idea/eip/api/routers/architecture.py)
  - [graph_updater.py](/Users/sudhanshujain/Desktop/automation_idea/eip/workers/graph_updater.py)

## 9. Cost Data Sources

### Required
- AWS Cost Explorer read access
- Resource utilization metrics source (CloudWatch/Prometheus/Wavefront)

### Stub Replacement Location
- Static source currently in [eip/stubs/providers.py](/Users/sudhanshujain/Desktop/automation_idea/eip/stubs/providers.py)
- Consumers:
  - [cost.py](/Users/sudhanshujain/Desktop/automation_idea/eip/api/routers/cost.py)
  - [cost_analyser.py](/Users/sudhanshujain/Desktop/automation_idea/eip/workers/cost_analyser.py)

## 10. Compliance Data Sources

### Required
- AWS Config/Organizations inventory data
- Scanner backend (e.g., Checkov/tfsec or internal scanner)
- Policy bundle source of truth

### Stub Replacement Location
- Static violations/account configs in [eip/stubs/providers.py](/Users/sudhanshujain/Desktop/automation_idea/eip/stubs/providers.py)
- Consumers:
  - [compliance.py](/Users/sudhanshujain/Desktop/automation_idea/eip/api/routers/compliance.py)
  - [compliance_scanner.py](/Users/sudhanshujain/Desktop/automation_idea/eip/workers/compliance_scanner.py)

## 11. Infrastructure (Now Added, Core Scope)

Terraform module now exists at:
- [infra/terraform](/Users/sudhanshujain/Desktop/automation_idea/infra/terraform)

Implemented in module baseline:
- EventBridge bus + baseline rules in [eventbridge.tf](/Users/sudhanshujain/Desktop/automation_idea/infra/terraform/eventbridge.tf)
- DynamoDB tables in [dynamodb.tf](/Users/sudhanshujain/Desktop/automation_idea/infra/terraform/dynamodb.tf)
- Worker IAM role/policy in [iam.tf](/Users/sudhanshujain/Desktop/automation_idea/infra/terraform/iam.tf)
- Optional integrations secret container in [secrets.tf](/Users/sudhanshujain/Desktop/automation_idea/infra/terraform/secrets.tf)

Still required for full live rollout:
- EventBridge targets bound to deployed worker runtimes (Lambda/SQS/ECS)
- API/Lambda/ECS deployment modules and packaging pipeline wiring
- Monitoring/alarms and remote Terraform backend/state-locking bootstrap

## 12. Validation Checklist Before Switching To Live

- [ ] All live provider classes implemented and bound in provider registry.
- [ ] Secrets exist and are readable from runtime role.
- [ ] EventBridge write path validated.
- [ ] DynamoDB tables created with expected keys/indexes.
- [ ] PagerDuty webhook tested with real payload.
- [ ] Slack notification tested in target channels.
- [ ] NLQ queries validated against real pillar data.
- [ ] Rollback path: switch back to `EIP_RUNTIME_MODE=stub` verified.
