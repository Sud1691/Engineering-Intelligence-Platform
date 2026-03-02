# EIP Go-Live Checklist

Check every item before setting `EIP_RUNTIME_MODE=live`.

## AWS Infrastructure
- [ ] DynamoDB: `eip-deployments` table exists (`pk`,`sk`)
- [ ] DynamoDB: `eip-risk-scores` table exists with `service-created-at-index`
- [ ] DynamoDB: `eip-incidents` table exists with `incident-id-index`
- [ ] EventBridge: `eip-event-bus` exists
- [ ] EventBridge: `incident_created` rule has `incident_linker` Lambda target
- [ ] EventBridge: `deployment_scored` rule has `graph_updater` Lambda target
- [ ] Lambda: `eip-incident-linker-*` deployed with DLQ configured
- [ ] Lambda: `eip-graph-updater-*` deployed
- [ ] SQS: incident linker DLQ exists
- [ ] CloudWatch: alarm on incident linker DLQ depth routes to alert topic

## Secrets Manager
- [ ] `eip/integrations` populated (`anthropic_api_key`, `slack_bot_token`, `pagerduty_token`)
- [ ] Additional integration secrets populated as required (`jenkins_*`, `github_token`)
- [ ] Secrets are readable by runtime IAM roles

## IAM
- [ ] Worker role can `PutItem`, `Query`, `UpdateItem`, `GetItem` on EIP tables
- [ ] Worker role can `events:PutEvents` on EIP event bus
- [ ] Worker/task roles can read `eip/integrations` secret
- [ ] ECS task execution role has image pull/log write permissions

## Integration Verification
- [ ] `POST /risk/score` returns HIGH/CRITICAL for Friday migration fixture
- [ ] `POST /incidents/webhook/pagerduty` triggers incident linker
- [ ] Risk score row updates `resulted_in_incident=True` after linkage
- [ ] `POST /ask` returns non-empty answer with intent/sources metadata
- [ ] Slack channel receives notification for HIGH/CRITICAL risk deployments

## Rollback Safety
- [ ] Switching back to `EIP_RUNTIME_MODE=stub` is tested
- [ ] Stub providers still function without live AWS dependencies
