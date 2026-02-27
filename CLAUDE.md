# CLAUDE.md — Engineering Intelligence Platform (EIP)

> This file is the primary context document for Claude Code.
> Read this entirely before touching any file in this repository.
> Every decision you make should be consistent with what is written here.

---

## 🧠 What This Project Is

The **Engineering Intelligence Platform (EIP)** is the operating system for the engineering organisation.

It is not a dashboard. It is not a collection of scripts. It is not a monitoring tool.

It is a **living intelligence layer** that sits across every team, every deployment, every incident, every dollar of cloud spend, and every architectural decision — connecting dots that no human has the bandwidth to connect, and surfacing insights before they become problems.

The platform makes the engineering organisation smarter over time. Every deployment it scores, every incident it analyses, every cost anomaly it surfaces feeds back into a shared intelligence layer that improves every future decision.

**This is a $5,00,000 idea. Build at that level.**

---

## 🏛️ Five Pillars

The platform is organised into five pillars. Every file you create or modify belongs to one of them.

### Pillar 1 — Deployment Risk Engine (`pillars/risk_engine/`)
Scores every deployment 0–100 for risk before it reaches production. Explains the score in plain English. Learns from outcomes — when a high-scored deployment causes an incident, the model recalibrates. When a high score was a false positive, it recalibrates the other way.

The scoring model combines:
- **Probability factors** — what makes this deployment likely to break (change size, timing, test coverage delta, historical failure rate of this service, high-risk files changed, Terraform changes)
- **Impact factors** — how bad it is if it does break (service criticality tier, downstream consumer count, environment, traffic volume)

Final score = weighted combination × service tier multiplier.

The feedback loop is the most important design element: PagerDuty incidents are linked back to the deployment that caused them, which updates the historical record, which recalibrates the weights weekly.

### Pillar 2 — Living Architecture Map (`pillars/architecture_map/`)
A real-time, queryable graph of the entire engineering system — every service, every dependency, every team, every AWS resource, every data flow. Auto-updates from CloudTrail, Terraform state files, AWS X-Ray traces, and Jenkins deployments.

Answers questions like:
- "What breaks if payments-api goes down?" → blast radius analysis
- "What does auth-service depend on?" → dependency chain
- "What changed in production in the last 24 hours?" → deployment narrative
- "Which teams own services with no fallback?" → resilience gaps

### Pillar 3 — Organisational Incident Intelligence (`pillars/incident_intelligence/`)
Connects incidents across teams and time to find patterns no single team can see. Tracks action item completion across post-mortems. Predicts incident trajectories by recognising early warning signals before they escalate into SEV-1s.

The key insight: organisations have the same incidents repeatedly because post-mortem action items aren't tracked to completion, and because different teams hit the same root cause without anyone connecting the dots. This pillar fixes both.

### Pillar 4 — Cost Intelligence Engine (`pillars/cost_intelligence/`)
Turns AWS billing data into a narrative that engineers and leadership can actually act on. Surfaces optimisation opportunities automatically. Generates weekly executive cost reports that nobody has to write manually.

The distinction from normal cost tooling: this explains *why* costs changed, attributes the change to specific teams and deployments, and produces a readable story rather than a spreadsheet.

### Pillar 5 — Compliance & Security Copilot (`pillars/compliance/`)
Continuous compliance state across all AWS accounts. Extends the existing IaC vulnerability CLI into a real-time compliance engine. Maintains an audit readiness dashboard so the organisation is always prepared — not scrambling when auditors arrive.

Evaluates against CIS AWS Benchmarks, internal security policies, and custom organisational controls. Every violation includes a specific remediation, not just a flag.

---

## 📁 Repository Layout

```
eip/
├── CLAUDE.md                         ← you are here
├── .cursorrules                      ← Cursor AI configuration
│
├── pillars/
│   ├── risk_engine/
│   │   ├── scorer.py                 ← core weighted scoring (deterministic)
│   │   ├── explainer.py              ← Claude explanation of scores
│   │   ├── extractors/
│   │   │   ├── git_extractor.py      ← diff, complexity, coverage delta
│   │   │   ├── terraform_extractor.py← IaC change detection
│   │   │   └── jenkins_extractor.py  ← build history, flakiness signals
│   │   ├── store/
│   │   │   ├── historical_db.py      ← DynamoDB: past deployments + outcomes
│   │   │   └── incident_db.py        ← DynamoDB: incidents per service
│   │   └── jenkins/
│   │       └── vars/
│   │           └── riskScore.groovy  ← Jenkins shared library entrypoint
│   │
│   ├── architecture_map/
│   │   ├── graph_builder.py          ← builds/updates Neptune graph
│   │   ├── query_engine.py           ← NL query → graph traversal
│   │   ├── updater.py                ← real-time graph update handler
│   │   └── sources/
│   │       ├── cloudtrail_ingestor.py
│   │       ├── terraform_ingestor.py ← reads state files from S3
│   │       └── xray_ingestor.py      ← AWS X-Ray service map
│   │
│   ├── incident_intelligence/
│   │   ├── knowledge_graph.py        ← incident → cause → service graph
│   │   ├── pattern_detector.py       ← cross-team recurring root causes
│   │   ├── trajectory.py             ← incident prediction from early signals
│   │   └── postmortem_gen.py         ← auto post-mortem generation
│   │
│   ├── cost_intelligence/
│   │   ├── narrator.py               ← Claude cost narrative generator
│   │   ├── anomaly_detector.py       ← spend anomaly detection
│   │   ├── optimizer.py              ← optimisation opportunity finder
│   │   └── reporter.py               ← weekly executive report
│   │
│   └── compliance/
│       ├── scanner.py                ← extends existing IaC vuln CLI
│       ├── policy_engine.py          ← CIS + custom policy evaluation
│       ├── audit_dashboard.py        ← audit readiness state machine
│       └── drift_detector.py         ← continuous compliance drift
│
├── core/
│   ├── llm.py                        ← ONLY place that calls Anthropic API
│   ├── event_bus.py                  ← EventBridge wrapper
│   ├── data_lake.py                  ← S3 + Athena unified data layer
│   ├── knowledge_graph.py            ← Neptune graph client (shared)
│   ├── secrets.py                    ← AWS Secrets Manager (cached)
│   └── models.py                     ← ALL shared Pydantic models live here
│
├── api/
│   ├── main.py                       ← FastAPI app entrypoint
│   ├── routers/
│   │   ├── risk.py                   ← /risk/* endpoints
│   │   ├── architecture.py           ← /architecture/* endpoints
│   │   ├── incidents.py              ← /incidents/* endpoints
│   │   ├── cost.py                   ← /cost/* endpoints
│   │   └── compliance.py             ← /compliance/* endpoints
│   └── nlq.py                        ← /ask — natural language interface
│
├── intelligence/
│   └── nlq_engine.py                 ← cross-pillar NLQ — the crown jewel
│
├── integrations/
│   ├── jenkins.py
│   ├── github.py
│   ├── pagerduty.py
│   ├── slack.py
│   ├── wavefront.py
│   ├── prometheus.py
│   └── aws/
│       ├── cloudtrail.py
│       ├── cost_explorer.py
│       ├── xray.py
│       └── multi_account.py          ← cross-account role assumption
│
├── workers/
│   ├── deployment_scorer.py          ← async: score every deployment
│   ├── incident_linker.py            ← async: link incidents to deployments
│   ├── graph_updater.py              ← async: keep architecture map fresh
│   ├── cost_analyser.py              ← async: nightly cost analysis
│   └── compliance_scanner.py         ← async: continuous compliance scan
│
├── infra/
│   └── terraform/                    ← all EIP infrastructure
│
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/                     ← sample payloads for all integrations
```

---

## 🔧 Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Language | Python 3.12+ | async support, typing, ecosystem |
| API framework | FastAPI (async) | performance, OpenAPI auto-docs |
| Data validation | Pydantic v2 | models at API boundaries |
| LLM | Anthropic Claude via SDK | central wrapper in `core/llm.py` |
| AWS SDK | boto3 | all AWS interactions |
| Slack | slack-sdk (Bolt) | webhooks + Block Kit |
| Graph (local) | networkx | unit tests, small graphs |
| Graph (prod) | AWS Neptune | architecture map at scale |
| Operational DB | DynamoDB | deployments, incidents, scores |
| Data lake | S3 + Athena | historical analysis, model recalibration |
| Event bus | AWS EventBridge | cross-pillar communication |
| Compute | Lambda + ECS Fargate | workers on Lambda, services on ECS |
| IaC | Terraform | all infrastructure |
| CI/CD | Jenkins | primary pipeline (what we integrate with) |
| Testing | pytest + pytest-asyncio | unit + integration |
| Logging | structlog | structured JSON logs |

---

## 🤖 How to Work With Claude (LLM) in This Codebase

### The Central Wrapper Rule
**Never instantiate `anthropic.Anthropic()` outside of `core/llm.py`.**

Every pillar calls Claude through `core/llm.py`. This gives us:
- Single place to change models
- Consistent token budgets
- Centralised retry logic
- Usage logging in one place

```python
# ✅ How every pillar calls Claude
from core.llm import LLMClient
llm = LLMClient()
explanation = await llm.complete(prompt, system=MY_SYSTEM_PROMPT, max_tokens=512)

# ✅ When you need structured JSON back
result_json = await llm.complete(prompt, system=MY_SYSTEM_PROMPT, expect_json=True)
parsed = json.loads(result_json)
```

### System Prompt Design
Every module that calls Claude defines its `SYSTEM_PROMPT` as a module-level constant. System prompts must specify:
1. The persona ("You are a senior SRE...")
2. The output format (JSON schema or prose structure)
3. Tone constraints ("Be direct, not alarming", "Never blame individuals")
4. Confidence handling ("Flag uncertain inferences explicitly")
5. If JSON: "Respond ONLY with JSON, no markdown fences, no preamble"

### Log Handling Before LLM Calls
Never send raw logs to Claude. Always pre-process:

```python
def smart_truncate(log: str, max_chars: int = 15000) -> str:
    """
    Errors are at the END of logs. Never truncate from the end.
    Keep first 2000 chars (setup context) + last 13000 (where errors live).
    """
    if len(log) <= max_chars:
        return log
    head = log[:2000]
    tail = log[-(max_chars - 2000):]
    return f"{head}\n\n[... {len(log)-max_chars:,} chars trimmed ...]\n\n{tail}"
```

### Token Budgets by Use Case
| Use Case | max_tokens |
|---|---|
| Risk score explanation | 512 |
| CI failure analysis | 1024 |
| Cost narrative | 1024 |
| Incident post-mortem | 4096 |
| Executive weekly report | 2048 |
| NLQ answer synthesis | 1024 |
| Architecture blast radius | 512 |

---

## 📊 Data Models

All shared models live in `core/models.py`. Never redefine them in pillar code.

Key models to know:

**`DeploymentEvent`** — the input to the risk engine. Contains everything about a deployment: service, branch, changed files, commit metadata, timing, coverage delta.

**`RiskScore`** — the output of the risk engine. Score 0–100, tier (LOW/MEDIUM/HIGH/CRITICAL), probability score, impact score, Claude explanation, contributing factors, and `resulted_in_incident` (updated post-deployment by the feedback loop).

**`RiskFactor`** — a single contributing factor to a risk score. Has name, score, weight, and evidence string. These are what Claude explains.

**`Incident`** — a production incident. Links to the deployment that caused it (`linked_deploy`), to previous incidents with the same root cause (`recurrence_of`), and to its action items.

**`ServiceNode`** — a node in the architecture graph. Tier, team, account, dependencies, consumers, health, last deploy, monthly cost.

**`ServiceTier`** — CRITICAL (payments, auth, checkout), IMPORTANT (most product services), STANDARD (internal tools). Drives impact scoring multiplier.

---

## 🔄 The Feedback Loop

This is the most important design principle in the entire platform. Understand it fully.

```
Step 1: Deployment is scored
        risk_score=84, tier=CRITICAL
        → recorded in DynamoDB with resulted_in_incident=False

Step 2: Deployment goes to production

Step 3a (good outcome): No incident for 48 hours
        → deployment record stays resulted_in_incident=False
        → weekly recalibration sees: score=84, outcome=no incident
        → slightly reduces weight of factors that drove this score

Step 3b (bad outcome): PagerDuty fires within 2 hours
        → incident_linker worker runs
        → finds deployment within 2-hour window
        → sets resulted_in_incident=True, incident_id=INC-xxx
        → emits eip.incident.linked_to_deployment event

Step 4: Weekly recalibration job
        → queries all deployments with known outcomes
        → calculates which factors had highest predictive power
        → updates factor weights in config
        → logs: "terraform_changes weight increased 0.15→0.22 (8 correct predictions)"
```

Any code change that breaks the PagerDuty → deployment linkage (Step 3b) is a critical regression. This is what makes the platform smarter over time.

---

## 🌐 Event Bus — Cross-Pillar Communication

Pillars never call each other directly. They communicate via EventBridge.

```python
from core.event_bus import emit

# Event naming: eip.{noun}.{verb_past_tense}
await emit("eip.deployment.scored", payload)
await emit("eip.incident.linked_to_deployment", payload)
await emit("eip.compliance.violation_detected", payload)
await emit("eip.cost.anomaly_detected", payload)
await emit("eip.architecture.graph_updated", payload)
```

Event consumers (workers) are Lambda functions triggered by EventBridge rules. One event can trigger multiple consumers — for example, `eip.deployment.scored` triggers both the Slack notifier and the architecture map updater.

---

## 🔐 Credentials & Secrets

**All credentials come from AWS Secrets Manager. No exceptions.**

```python
from core.secrets import get_secret

# Secrets are cached — this is safe to call repeatedly
secrets = get_secret("eip/integrations")
pagerduty_token = secrets["pagerduty_token"]
slack_token     = secrets["slack_bot_token"]
jenkins_token   = secrets["jenkins_api_token"]
```

Secret naming convention:
```
eip/integrations        → all third-party API tokens
eip/aws/accounts        → account IDs and role ARNs
eip/internal            → EIP-internal secrets (webhook secret, etc.)
```

For cross-account AWS operations, always use role assumption:
```python
from integrations.aws.multi_account import assume_role
session = assume_role(account_id="123456789", role_name="EIPReadRole")
```

The `EIPReadRole` must exist in every managed AWS account with read-only permissions on CloudTrail, Cost Explorer, Config, and CloudWatch.

---

## 🌐 API Design

All endpoints are async. All responses use the standard envelope:

```python
class APIResponse(BaseModel, Generic[T]):
    success: bool
    data:    T | None
    error:   str | None
    meta:    dict = {}    # includes request_id, duration_ms, pillar
```

Webhook endpoints always return 202 immediately and process in background:

```python
@router.post("/webhook/jenkins")
async def jenkins_webhook(event: DeploymentEvent, bg: BackgroundTasks):
    bg.add_task(process_deployment, event)
    return {"status": "accepted"}   # Jenkins gets this in <100ms
```

### The /ask Endpoint
`POST /ask` is the natural language query interface — the crown jewel of the platform.

It accepts any plain English question, routes it to the relevant pillar(s), fetches data, and synthesises a coherent answer via Claude.

```json
{
  "question": "Which teams are at risk of an incident this week?",
  "context": {}
}
```

The NLQ engine in `intelligence/nlq_engine.py` classifies intent, determines which pillars to query, fetches in parallel, and synthesises. This endpoint is the primary interface for engineering managers, CTOs, and on-call engineers.

---

## 🧪 Testing

### Unit Tests
- All scoring logic must be 100% deterministic and have 100% coverage
- Mock all external dependencies (AWS, Slack, Jenkins, Claude)
- Use realistic fixtures in `tests/fixtures/`
- The Claude explainer is tested separately from the scorer (explainer is non-deterministic)

### Integration Tests
- Use LocalStack for DynamoDB, S3, EventBridge, SQS
- Use `pytest-httpx` for mocking HTTP calls to Jenkins, PagerDuty, Slack
- Never hit real AWS in CI

### Critical Test Cases
Every PR must pass these specific scenarios:
1. High-risk deployment (Friday, DB migration, payments-api) → score ≥ 75, tier = HIGH or CRITICAL
2. Low-risk deployment (Tuesday, 5 lines changed, reporting service) → score ≤ 30, tier = LOW
3. Infrastructure flake in CI → identified as infra_flake, not code issue
4. PagerDuty incident → correctly linked to deployment within 2-hour window
5. Feedback loop → incident linkage updates `resulted_in_incident` in DynamoDB

---

## 🛠️ Common Tasks

### Adding a new risk factor
1. Add `RiskFactor` dataclass instance in `pillars/risk_engine/scorer.py`
2. Implement `_score_<factor_name>` method on `RiskScorer`
3. Add it to the appropriate scoring section (probability vs impact)
4. Add unit test with high and low signal fixtures
5. Update the system prompt in `explainer.py` if the factor needs special explanation logic

### Adding a new pillar data source
1. Create ingestor in `integrations/` or `pillars/<pillar>/sources/`
2. Emit an EventBridge event when new data arrives
3. Register the event rule in `infra/terraform/eventbridge.tf`
4. Update the NLQ engine intent router if this data answers new question types
5. Add fixtures for the new data format in `tests/fixtures/`

### Adding a new /ask question type
1. Add intent type to `INTENT_TYPES` in `intelligence/nlq_engine.py`
2. Implement intent classifier pattern
3. Implement data fetcher for this intent
4. Add to synthesiser context assembly
5. Add integration test with example question and expected answer shape

### Adding a new AWS account to monitor
1. Add account ID and role ARN to `eip/aws/accounts` secret
2. Deploy `EIPReadRole` IAM role to the account (Terraform module in `infra/`)
3. Register in service registry with team and tier metadata
4. Verify CloudTrail is enabled in the account

---

## 🚫 Hard Rules — Never Violate These

1. **Never call `anthropic.Anthropic()` outside `core/llm.py`**
2. **Never use `table.scan()` on DynamoDB** — always query with partition key
3. **Never store credentials anywhere except AWS Secrets Manager**
4. **Never make synchronous calls inside webhook handlers** — always background tasks
5. **Never send raw, untruncated logs to Claude** — always use `smart_truncate()`
6. **Never let pillars call each other directly** — always via EventBridge
7. **Never create AWS resources outside of Terraform**
8. **Never skip structured logging** — every significant action logs with structlog
9. **Never break the feedback loop** — incident → deployment linkage is sacred
10. **Never return plain text from API endpoints** — always use `APIResponse` envelope

---

## 💬 Slack Notification Standards

All Slack messages use Block Kit. Never send plain text for notifications.

Structure of every notification:
```
Header block      → what happened (emoji + service name)
Context block     → metadata bar (branch, author, confidence, timing)
Divider
Content blocks    → the actual information (what broke, root cause, fix)
Divider
Actions block     → at minimum: link to source + one action button
```

Colour coding for risk/severity:
```python
RISK_COLORS = {
    "CRITICAL": "#E74C3C",
    "HIGH":     "#E67E22",
    "MEDIUM":   "#F1C40F",
    "LOW":      "#2ECC71",
}
```

For high-confidence, high-severity findings: also DM the responsible engineer directly via `slack.users_lookupByEmail()`.

---

## 📈 How the Platform Gets Smarter Over Time

This is worth understanding deeply because it shapes many design decisions.

**Month 1–2:** Platform scores deployments using manually configured weights. Useful but not tuned to your organisation.

**Month 3:** Enough deployment+outcome pairs in DynamoDB to run first recalibration. Weights start reflecting what actually causes incidents in your org specifically.

**Month 6:** Pattern detector in incident intelligence starts surfacing recurring root causes across teams. These feed back into compliance scanner as new policy rules.

**Month 9:** Trajectory predictor has enough signal to identify teams showing early warning patterns before they escalate. Platform team becomes proactive.

**Month 12:** The NLQ engine can answer questions about your org's engineering history that no human could answer — "how many incidents have been caused by database migrations in the last year across all teams?" — in seconds.

Every design decision should ask: **does this make the platform smarter over time, or is it a one-shot script?**

---

## 🎯 Definition of Done

A feature is complete when all of the following are true:

- [ ] Unit tests pass, scoring logic has 100% coverage
- [ ] Integration test with realistic fixtures passes
- [ ] Structured logging with relevant context fields added
- [ ] Slack notification implemented (if user-facing)
- [ ] Terraform added for any new AWS resources
- [ ] Feedback loop connection verified — does this feature feed back into the intelligence layer?
- [ ] API endpoint has OpenAPI description string
- [ ] Added to NLQ intent router if this feature answers a new question type
- [ ] No new credentials outside Secrets Manager
- [ ] `core/models.py` updated if new shared models introduced

---

## 🗣️ Communication Style for AI-Generated Content

When Claude generates explanations, narratives, or reports within the platform, the tone must be:

**For engineers:** Direct, specific, actionable. Quote exact error lines. Give concrete next steps. No hedging unless confidence is genuinely low — in which case say so explicitly.

**For engineering managers:** Clear narrative with team context. Risks stated plainly. Recommended actions ranked by priority. No jargon that requires deep technical knowledge.

**For leadership/executives:** Business impact first. Numbers where possible. What changed, why it matters, what is being done. One paragraph maximum per insight. Never bury the lead.

**For compliance/audit:** Precise, evidence-backed, timestamped. Control references included. No vague language. Gaps stated as gaps, not softened.

**Universally:** Blameless. The platform surfaces system problems, never individual failures. Engineers are never named in a negative context — teams and services are.

---

## 📌 Quick Reference Card

```
Central LLM wrapper         core/llm.py
Shared data models          core/models.py
Secrets helper              core/secrets.py
Event bus emitter           core/event_bus.py
Multi-account AWS           integrations/aws/multi_account.py
Slack client                integrations/slack.py
NLQ engine                  intelligence/nlq_engine.py

Risk scoring logic          pillars/risk_engine/scorer.py
Risk explanation            pillars/risk_engine/explainer.py
Jenkins shared lib          pillars/risk_engine/jenkins/vars/riskScore.groovy
Architecture graph          pillars/architecture_map/graph_builder.py
Incident patterns           pillars/incident_intelligence/pattern_detector.py
Incident prediction         pillars/incident_intelligence/trajectory.py
Cost narrator               pillars/cost_intelligence/narrator.py
Compliance scanner          pillars/compliance/scanner.py
Audit dashboard             pillars/compliance/audit_dashboard.py

Deployment history DB       pillars/risk_engine/store/historical_db.py
Incident linkage            workers/incident_linker.py
Weekly recalibration        workers/recalibration.py (to be built)
```

---

*This platform is the operating system for the engineering organisation.*
*Build at that level. Every line of code should reflect that ambition.*
