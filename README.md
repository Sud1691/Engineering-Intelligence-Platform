# Engineering Intelligence Platform (EIP) — Current Implementation Status

This repository is running in **stub-only mode by default** and is wired end-to-end for local execution without live AWS/Slack/PagerDuty/Jenkins dependencies.

- Runtime mode default: `stub`
- Live mode guard: `EIP_RUNTIME_MODE=live` requires `EIP_ENABLE_LIVE_MODE=true`
- Stub provider backbone: [eip/core/provider_registry.py](/Users/sudhanshujain/Desktop/automation_idea/eip/core/provider_registry.py), [eip/stubs/providers.py](/Users/sudhanshujain/Desktop/automation_idea/eip/stubs/providers.py)
- Terraform-module style user configuration: `platform.auto.tfvars` (see [platform.auto.tfvars.example](/Users/sudhanshujain/Desktop/automation_idea/platform.auto.tfvars.example))
- Terraform core infrastructure module: [infra/terraform/README.md](/Users/sudhanshujain/Desktop/automation_idea/infra/terraform/README.md)

For usage and prerequisites, see [setup.md](/Users/sudhanshujain/Desktop/automation_idea/setup.md).  
For exact live dependency replacement steps, see [docs/live_setup.md](/Users/sudhanshujain/Desktop/automation_idea/docs/live_setup.md).  
For architecture, see [docs/architecture.md](/Users/sudhanshujain/Desktop/automation_idea/docs/architecture.md).

## Stage Summary

- Stub-mode product baseline (all pillars reachable): **implemented**
- Missing-link wiring (API -> workers -> pillars -> store/event bus): **implemented**
- Production/live integrations: **pending**
- Infra provisioning (`infra/terraform` core module scaffold): **implemented**

## Pillar 1 — Deployment Risk Engine

### Done
- [x] Deterministic deployment scoring (0–100) in [scorer.py](/Users/sudhanshujain/Desktop/automation_idea/eip/pillars/risk_engine/scorer.py)
- [x] LLM explanation path via central wrapper in [explainer.py](/Users/sudhanshujain/Desktop/automation_idea/eip/pillars/risk_engine/explainer.py)
- [x] Synchronous and webhook risk API in [risk.py](/Users/sudhanshujain/Desktop/automation_idea/eip/api/routers/risk.py)
- [x] End-to-end deployment worker in [deployment_scorer.py](/Users/sudhanshujain/Desktop/automation_idea/eip/workers/deployment_scorer.py)
- [x] Feedback-loop data helpers in [historical_db.py](/Users/sudhanshujain/Desktop/automation_idea/eip/pillars/risk_engine/store/historical_db.py)
- [x] Weekly recalibration worker baseline in [risk_recalibration.py](/Users/sudhanshujain/Desktop/automation_idea/eip/workers/risk_recalibration.py)

### Stubbed But Wired
- [x] HistoricalDB persistence in stub mode (in-memory)
- [x] EventBridge emits in stub mode (structured log only)
- [x] Slack high-risk notifications in stub mode (no outbound API call)
- [x] LLM calls in stub mode (deterministic responses)

### Pending
- [ ] Live DynamoDB tables with GSIs and PITR
- [ ] Live Slack delivery/DM workflows

### Required Live Objects
- [ ] DynamoDB tables: `eip-deployments`, `eip-risk-scores`
- [ ] EventBridge bus: `eip-event-bus`
- [ ] Secrets Manager secret: `eip/integrations` (Slack, PagerDuty tokens)

## Pillar 2 — Living Architecture Map

### Done
- [x] Graph build/query engine in [graph_builder.py](/Users/sudhanshujain/Desktop/automation_idea/eip/pillars/architecture_map/graph_builder.py) and [query_engine.py](/Users/sudhanshujain/Desktop/automation_idea/eip/pillars/architecture_map/query_engine.py)
- [x] `has_service()` API-safe query method in [query_engine.py](/Users/sudhanshujain/Desktop/automation_idea/eip/pillars/architecture_map/query_engine.py)
- [x] Router backed by provider-fed snapshots in [architecture.py](/Users/sudhanshujain/Desktop/automation_idea/eip/api/routers/architecture.py)
- [x] Worker now parses payload, applies snapshot, and logs counts in [graph_updater.py](/Users/sudhanshujain/Desktop/automation_idea/eip/workers/graph_updater.py)

### Stubbed But Wired
- [x] Snapshot source comes from deterministic stub provider data
- [x] CloudTrail/Terraform/X-Ray adapters are simplified extractors

### Pending
- [ ] Incremental graph updates and reconciliation logic
- [ ] Neptune-backed persistent graph storage
- [ ] Multi-account discovery and ownership metadata enrichment

### Required Live Objects
- [ ] Neptune cluster and query endpoint
- [ ] CloudTrail event stream inputs
- [ ] Terraform state source (S3/state backend)
- [ ] X-Ray service map ingestion path

## Pillar 3 — Organisational Incident Intelligence

### Done
- [x] Incident webhook validation in [incidents.py](/Users/sudhanshujain/Desktop/automation_idea/eip/api/routers/incidents.py)
- [x] Incident persistence + deployment linking worker flow in [incident_linker.py](/Users/sudhanshujain/Desktop/automation_idea/eip/workers/incident_linker.py)
- [x] Link event emit (`eip.incident.linked_to_deployment`) and risk-score outcome marking
- [x] IncidentDB supports stub-mode in-memory persistence
- [x] Incident intelligence API endpoints implemented for patterns, trajectory, and postmortem draft generation

### Stubbed But Wired
- [x] Incident matching uses recent-deployment heuristic
- [x] Pattern/trajectory/postmortem modules rely on stub LLM in local mode

### Pending
- [ ] Strong time-window correlation logic and confidence scoring
- [ ] Action-item tracking lifecycle integration
- [ ] Org-wide recurrence trend analytics

### Required Live Objects
- [ ] PagerDuty webhook + service mapping source of truth
- [ ] Incident data store durability and retention policy
- [ ] Team ownership catalog integration

## Pillar 4 — Cost Intelligence Engine

### Done
- [x] Cost router now reads provider-fed inputs (no inline mocks) in [cost.py](/Users/sudhanshujain/Desktop/automation_idea/eip/api/routers/cost.py)
- [x] Nightly worker now reads provider-fed inputs in [cost_analyser.py](/Users/sudhanshujain/Desktop/automation_idea/eip/workers/cost_analyser.py)
- [x] Anomaly + optimization + narrative + report pipeline wired

### Stubbed But Wired
- [x] Cost/resource datasets come from deterministic stub provider
- [x] Narrative generation uses stub LLM in local mode

### Pending
- [ ] Live Cost Explorer ingestion and trend baselines
- [ ] Team attribution model for spend changes
- [ ] Scheduled executive report delivery channel

### Required Live Objects
- [ ] AWS Cost Explorer read access
- [ ] Resource utilization feeds (CloudWatch/Prometheus/Wavefront as chosen)
- [ ] Slack/email destination for executive cost reports

## Pillar 5 — Compliance & Security Copilot

### Done
- [x] Compliance router now reads provider-fed inputs (no inline mocks) in [compliance.py](/Users/sudhanshujain/Desktop/automation_idea/eip/api/routers/compliance.py)
- [x] Compliance worker now includes provider-backed drift checks in [compliance_scanner.py](/Users/sudhanshujain/Desktop/automation_idea/eip/workers/compliance_scanner.py)
- [x] Scanner + policy + drift + dashboard modules wired together

### Stubbed But Wired
- [x] Violations and account configs come from deterministic stub provider
- [x] Scanner remains heuristic-based for local mode

### Pending
- [ ] Real scanner execution (e.g., Checkov/tfsec wrapper integration)
- [ ] Control mapping against CIS/custom controls at scale
- [ ] Historical compliance trend tracking

### Required Live Objects
- [ ] AWS Config/Organization account inventory
- [ ] Security scanner runtime + policy bundle source
- [ ] Audit evidence storage path

## API & Intelligence Layer

### Done
- [x] Unified FastAPI app in [main.py](/Users/sudhanshujain/Desktop/automation_idea/eip/api/main.py)
- [x] Standardized API metadata (`source_mode`, `generated_at`) in APIResponse `meta`
- [x] NLQ router now returns real intent metadata + sources in [nlq.py](/Users/sudhanshujain/Desktop/automation_idea/eip/api/nlq.py)
- [x] NLQ engine now uses adapter-backed data sourcing (risk/architecture/incident/cost/compliance) in [nlq_engine.py](/Users/sudhanshujain/Desktop/automation_idea/eip/intelligence/nlq_engine.py)

### Stubbed But Wired
- [x] NLQ intent data comes from stub providers through adapter routing
- [x] NLQ synthesis uses stub LLM in local mode

### Pending
- [ ] Source attribution with direct object IDs/links
- [ ] Multi-intent parallel fetch optimization
- [ ] Confidence scoring per answer section

### Required Live Objects
- [ ] Live data source adapters per pillar
- [ ] Access-controlled NLQ context enrichment sources

## Core Platform & Runtime Backbone

### Done
- [x] Runtime settings and live-mode guard in [settings.py](/Users/sudhanshujain/Desktop/automation_idea/eip/core/settings.py)
- [x] Typed provider contracts in [providers.py](/Users/sudhanshujain/Desktop/automation_idea/eip/core/providers.py)
- [x] Single provider registry in [provider_registry.py](/Users/sudhanshujain/Desktop/automation_idea/eip/core/provider_registry.py)
- [x] Stub datasets/providers in [eip/stubs/providers.py](/Users/sudhanshujain/Desktop/automation_idea/eip/stubs/providers.py)
- [x] Event bus stub-mode behavior in [event_bus.py](/Users/sudhanshujain/Desktop/automation_idea/eip/core/event_bus.py)
- [x] Secrets stub-mode behavior in [secrets.py](/Users/sudhanshujain/Desktop/automation_idea/eip/core/secrets.py)
- [x] LLM stub-mode behavior in [llm.py](/Users/sudhanshujain/Desktop/automation_idea/eip/core/llm.py)

### Pending
- [ ] Live provider implementations for all contracts
- [ ] Runtime health checks for provider readiness

### Required Live Objects
- [ ] Full secrets inventory in AWS Secrets Manager
- [ ] IAM roles/policies for every integration and datastore

## Infrastructure (Terraform)

### Done
- [x] Core Terraform module added in [infra/terraform](/Users/sudhanshujain/Desktop/automation_idea/infra/terraform)
- [x] EventBridge bus + core event rules scaffolded in [eventbridge.tf](/Users/sudhanshujain/Desktop/automation_idea/infra/terraform/eventbridge.tf)
- [x] DynamoDB tables (deployments, risk scores, incidents) scaffolded in [dynamodb.tf](/Users/sudhanshujain/Desktop/automation_idea/infra/terraform/dynamodb.tf)
- [x] Worker IAM role/policy scaffolded in [iam.tf](/Users/sudhanshujain/Desktop/automation_idea/infra/terraform/iam.tf)
- [x] Optional integrations secret scaffolded in [secrets.tf](/Users/sudhanshujain/Desktop/automation_idea/infra/terraform/secrets.tf)

### Stubbed But Wired
- [x] Provisioning is opt-in (`provision_core_resources=false` by default), so local stub mode remains no-cloud by default
- [x] Same `platform.auto.tfvars` variable names are reused by runtime and Terraform module

### Pending
- [ ] Event rule targets for concrete worker runtimes (Lambda/SQS/ECS target wiring)
- [ ] Additional infra modules for API Gateway/Lambda packaging/ECS services
- [ ] Data layer infra for S3/Athena/Neptune and org-scale observability

### Required Live Objects
- [ ] Runtime compute resources (Lambda/ECS) bound to EventBridge rules
- [ ] Remote Terraform backend and state locking (S3 + DynamoDB lock table)

## Testing Status

### Done
- [x] Existing unit tests for risk scoring/explainer and architecture graph
- [x] Compile check path available via `python3 -m compileall eip tests`

### Pending
- [ ] Integration tests with LocalStack or equivalent

## Run Locally

1. Follow [setup.md](/Users/sudhanshujain/Desktop/automation_idea/setup.md).

If you want to force a mode:

```bash
export EIP_RUNTIME_MODE=stub
# live mode is intentionally guarded:
# export EIP_RUNTIME_MODE=live
# export EIP_ENABLE_LIVE_MODE=true
```
