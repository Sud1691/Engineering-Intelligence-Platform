# CLAUDE.md Compliance Triage (Updated)

This file tracks what is now addressed in the current stub-first state, and what is intentionally deferred until live rollout.

## Resolved Now (Stub-Mode Compatible)

## R1) Credentials helper hardcoded stub token-like values
- Status: Resolved
- Update:
  - Replaced stub token literals with explicit placeholder values in [eip/core/secrets.py](../eip/core/secrets.py)

## R2) Feedback loop now enforces incident-to-deployment correlation window
- Status: Resolved
- Update:
  - Added configurable window (`eip_incident_link_window_hours`, default `2`) in [eip/core/settings.py](../eip/core/settings.py)
  - Added window-based matching logic in [eip/workers/incident_linker.py](../eip/workers/incident_linker.py)
  - Added test coverage in [test_incident_linker.py](../tests/unit/workers/test_incident_linker.py)

## R3) API envelope consistency for webhooks
- Status: Resolved
- Update:
  - Jenkins and PagerDuty webhooks now return `APIResponse` envelopes:
    - [eip/api/routers/risk.py](../eip/api/routers/risk.py)
    - [eip/api/routers/incidents.py](../eip/api/routers/incidents.py)

## R4) API meta contract now includes request tracing and duration
- Status: Resolved
- Update:
  - Added `build_endpoint_meta()` with `request_id`, `duration_ms`, `pillar` in [eip/core/provider_registry.py](../eip/core/provider_registry.py)
  - Applied across API routers.
  - Added route tests in [tests/unit/api/test_routes.py](../tests/unit/api/test_routes.py)

## R5) NLQ multi-pillar fetch now explicit parallel fan-out
- Status: Resolved
- Update:
  - Added `asyncio.gather` fan-out in [eip/intelligence/adapters.py](../eip/intelligence/adapters.py)

## R6) LLM budget/prompt standard alignment improved
- Status: Resolved for identified gaps
- Update:
  - Risk explainer token budget changed to `512`: [eip/pillars/risk_engine/explainer.py](../eip/pillars/risk_engine/explainer.py)
  - Postmortem generator token budget changed to `4096`: [eip/pillars/incident_intelligence/postmortem_gen.py](../eip/pillars/incident_intelligence/postmortem_gen.py)
  - Added explicit uncertainty/confidence guidance to relevant prompts:
    - [narrator.py](../eip/pillars/cost_intelligence/narrator.py)
    - [pattern_detector.py](../eip/pillars/incident_intelligence/pattern_detector.py)
    - [trajectory.py](../eip/pillars/incident_intelligence/trajectory.py)
    - [postmortem_gen.py](../eip/pillars/incident_intelligence/postmortem_gen.py)
    - [explainer.py](../eip/pillars/risk_engine/explainer.py)

## R7) Slack high-severity DM escalation path
- Status: Resolved
- Update:
  - Added optional critical-tier DM escalation using `users_lookupByEmail` in [eip/integrations/slack.py](../eip/integrations/slack.py)

## R8) Weekly recalibration workflow exists
- Status: Resolved (stub-capable baseline)
- Update:
  - Added worker [eip/workers/risk_recalibration.py](../eip/workers/risk_recalibration.py)
  - Added risk score listing helper in [historical_db.py](../eip/pillars/risk_engine/store/historical_db.py)
  - Added unit test [test_risk_recalibration.py](../tests/unit/workers/test_risk_recalibration.py)

## R9) Terraform infrastructure module baseline added
- Status: Resolved (core infra scaffold)
- Update:
  - Added core module in [infra/terraform](../infra/terraform)
  - Added EventBridge, DynamoDB, IAM, and optional Secrets Manager resources
  - Added Terraform usage guide in [infra/terraform/README.md](../infra/terraform/README.md)
  - Updated platform docs and tfvars example for shared runtime/provisioning variables

## R10) Repository link-path hygiene fixed
- Status: Resolved
- Update:
  - Removed machine-specific absolute links from docs and README
  - Updated markdown cross-links to repository-relative paths

## R11) Integration critical cases added
- Status: Resolved (moto-backed baseline)
- Update:
  - Added integration fixtures in [tests/integration/conftest.py](../tests/integration/conftest.py)
  - Added critical-case suite in [tests/integration/test_critical_cases.py](../tests/integration/test_critical_cases.py)
  - Added infra-flake detector helper used by tests in [jenkins_extractor.py](../eip/pillars/risk_engine/extractors/jenkins_extractor.py)

## R12) Live provider branch no longer hard-fails
- Status: Resolved (partial live implementation)
- Update:
  - Added live provider package in [eip/stubs/live_providers](../eip/stubs/live_providers)
  - Wired live registry mode in [provider_registry.py](../eip/core/provider_registry.py)
  - Added live registry unit coverage in [test_provider_registry_live.py](../tests/unit/core/test_provider_registry_live.py)

## R13) EventBridge targets and worker compute scaffolding added
- Status: Resolved (infrastructure scaffold)
- Update:
  - Added Lambda worker resources + DLQ/alarm in [lambda.tf](../infra/terraform/lambda.tf)
  - Added EventBridge targets + invoke permissions in [eventbridge.tf](../infra/terraform/eventbridge.tf)
  - Added ECS/Fargate API scaffolding in [ecs.tf](../infra/terraform/ecs.tf)

## Acceptable Deferred Items (Because Current Mode Is Stub-First)

## D1) Full production data providers for every pillar
- Deferred reason: architecture/cost/compliance live providers currently use transitional fallback data paths.
- Evidence: [eip/stubs/live_providers](../eip/stubs/live_providers) contains transitional providers pending real ingestion wiring.

## D2) LocalStack/CI integration harness
- Deferred reason: integration cases are moto-backed locally; CI-grade LocalStack wiring is still pending.
- Evidence: `tests/integration` exists, but no LocalStack CI pipeline yet.

## D3) Full CLAUDE.md Definition-of-Done closure
- Deferred reason: blocked on D1-D2 live rollout gates.
- Note: repository should be described as “stub-mode baseline complete,” not “live production complete.”
