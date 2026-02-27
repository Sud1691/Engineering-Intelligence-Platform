# CLAUDE.md Compliance Triage (Updated)

This file tracks what is now addressed in the current stub-first state, and what is intentionally deferred until live rollout.

## Resolved Now (Stub-Mode Compatible)

## R1) Credentials helper hardcoded stub token-like values
- Status: Resolved
- Update:
  - Replaced stub token literals with explicit placeholder values in [eip/core/secrets.py](/Users/sudhanshujain/Desktop/automation_idea/eip/core/secrets.py)

## R2) Feedback loop now enforces incident-to-deployment correlation window
- Status: Resolved
- Update:
  - Added configurable window (`eip_incident_link_window_hours`, default `2`) in [eip/core/settings.py](/Users/sudhanshujain/Desktop/automation_idea/eip/core/settings.py)
  - Added window-based matching logic in [eip/workers/incident_linker.py](/Users/sudhanshujain/Desktop/automation_idea/eip/workers/incident_linker.py)
  - Added test coverage in [test_incident_linker.py](/Users/sudhanshujain/Desktop/automation_idea/tests/unit/workers/test_incident_linker.py)

## R3) API envelope consistency for webhooks
- Status: Resolved
- Update:
  - Jenkins and PagerDuty webhooks now return `APIResponse` envelopes:
    - [eip/api/routers/risk.py](/Users/sudhanshujain/Desktop/automation_idea/eip/api/routers/risk.py)
    - [eip/api/routers/incidents.py](/Users/sudhanshujain/Desktop/automation_idea/eip/api/routers/incidents.py)

## R4) API meta contract now includes request tracing and duration
- Status: Resolved
- Update:
  - Added `build_endpoint_meta()` with `request_id`, `duration_ms`, `pillar` in [eip/core/provider_registry.py](/Users/sudhanshujain/Desktop/automation_idea/eip/core/provider_registry.py)
  - Applied across API routers.
  - Added route tests in [tests/unit/api/test_routes.py](/Users/sudhanshujain/Desktop/automation_idea/tests/unit/api/test_routes.py)

## R5) NLQ multi-pillar fetch now explicit parallel fan-out
- Status: Resolved
- Update:
  - Added `asyncio.gather` fan-out in [eip/intelligence/adapters.py](/Users/sudhanshujain/Desktop/automation_idea/eip/intelligence/adapters.py)

## R6) LLM budget/prompt standard alignment improved
- Status: Resolved for identified gaps
- Update:
  - Risk explainer token budget changed to `512`: [eip/pillars/risk_engine/explainer.py](/Users/sudhanshujain/Desktop/automation_idea/eip/pillars/risk_engine/explainer.py)
  - Postmortem generator token budget changed to `4096`: [eip/pillars/incident_intelligence/postmortem_gen.py](/Users/sudhanshujain/Desktop/automation_idea/eip/pillars/incident_intelligence/postmortem_gen.py)
  - Added explicit uncertainty/confidence guidance to relevant prompts:
    - [narrator.py](/Users/sudhanshujain/Desktop/automation_idea/eip/pillars/cost_intelligence/narrator.py)
    - [pattern_detector.py](/Users/sudhanshujain/Desktop/automation_idea/eip/pillars/incident_intelligence/pattern_detector.py)
    - [trajectory.py](/Users/sudhanshujain/Desktop/automation_idea/eip/pillars/incident_intelligence/trajectory.py)
    - [postmortem_gen.py](/Users/sudhanshujain/Desktop/automation_idea/eip/pillars/incident_intelligence/postmortem_gen.py)
    - [explainer.py](/Users/sudhanshujain/Desktop/automation_idea/eip/pillars/risk_engine/explainer.py)

## R7) Slack high-severity DM escalation path
- Status: Resolved
- Update:
  - Added optional critical-tier DM escalation using `users_lookupByEmail` in [eip/integrations/slack.py](/Users/sudhanshujain/Desktop/automation_idea/eip/integrations/slack.py)

## R8) Weekly recalibration workflow exists
- Status: Resolved (stub-capable baseline)
- Update:
  - Added worker [eip/workers/risk_recalibration.py](/Users/sudhanshujain/Desktop/automation_idea/eip/workers/risk_recalibration.py)
  - Added risk score listing helper in [historical_db.py](/Users/sudhanshujain/Desktop/automation_idea/eip/pillars/risk_engine/store/historical_db.py)
  - Added unit test [test_risk_recalibration.py](/Users/sudhanshujain/Desktop/automation_idea/tests/unit/workers/test_risk_recalibration.py)

## R9) Terraform infrastructure module baseline added
- Status: Resolved (core infra scaffold)
- Update:
  - Added core module in [infra/terraform](/Users/sudhanshujain/Desktop/automation_idea/infra/terraform)
  - Added EventBridge, DynamoDB, IAM, and optional Secrets Manager resources
  - Added Terraform usage guide in [infra/terraform/README.md](/Users/sudhanshujain/Desktop/automation_idea/infra/terraform/README.md)
  - Updated platform docs and tfvars example for shared runtime/provisioning variables

## Acceptable Deferred Items (Because Current Mode Is Stub-First)

## D1) Live provider implementations
- Deferred reason: current target is deterministic stub runtime.
- Evidence: [eip/core/provider_registry.py](/Users/sudhanshujain/Desktop/automation_idea/eip/core/provider_registry.py): live branch intentionally not implemented.

## D2) LocalStack/pytest-httpx integration suite
- Deferred reason: unit/workflow coverage prioritized for stub baseline; integration harness is a live-readiness gate.
- Evidence: no `tests/integration` suite yet.

## D3) Full CLAUDE.md Definition-of-Done closure
- Deferred reason: blocked on D1-D2 live rollout gates.
- Note: repository should be described as “stub-mode baseline complete,” not “live production complete.”
