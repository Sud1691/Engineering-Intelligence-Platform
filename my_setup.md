# My Setup Guide (Hosting EIP on AWS)

This runbook hosts the current EIP solution using the repository as-is.

Assumption used in this guide:
- AWS Account ID: `2233445566`
- Region: `us-east-1`
- Environment: `dev`

## 1) Prerequisites

Install and verify:

```bash
python3 --version
terraform --version
aws --version
docker --version
```

Clone and enter repo:

```bash
git clone https://github.com/Sud1691/Engineering-Intelligence-Platform.git
cd Engineering-Intelligence-Platform
```

Configure AWS CLI profile:

```bash
aws configure
# Use account 2233445566 credentials
```

## 2) Create Runtime Config

Create your runtime+Terraform variables file:

```bash
cp platform.auto.tfvars.example platform.auto.tfvars
```

Use this baseline in `platform.auto.tfvars`:

```hcl
eip_runtime_mode = "live"
eip_enable_live_mode = true
eip_aws_region = "us-east-1"

eip_event_bus_name = "eip-event-bus-dev"
eip_deployments_table_name = "eip-deployments-dev"
eip_risk_scores_table_name = "eip-risk-scores-dev"
eip_incidents_table_name = "eip-incidents-dev"
eip_integrations_secret_name = "eip/integrations/dev"
eip_slack_default_channel = "#eip-dev-alerts"
eip_incident_link_window_hours = 2

provision_core_resources = true
create_worker_role = true
create_integrations_secret = true
create_integrations_secret_version = false

enable_worker_lambdas = true
eip_workers_zip_path = "../../dist/eip-workers.zip"

enable_ecs_api = true
eip_docker_image = "2233445566.dkr.ecr.us-east-1.amazonaws.com/eip-api:latest"

# Required for ECS+ALB
vpc_id = "vpc-REPLACE_ME"
public_subnet_ids = ["subnet-REPLACE_ME_1", "subnet-REPLACE_ME_2"]
private_subnet_ids = ["subnet-REPLACE_ME_3", "subnet-REPLACE_ME_4"]

environment = "dev"
```

If you want fast bootstrap using default VPC/subnets, discover IDs:

```bash
VPC_ID=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)
PUB_SUBNETS=$(aws ec2 describe-subnets --filters Name=vpc-id,Values=$VPC_ID Name=map-public-ip-on-launch,Values=true --query 'Subnets[*].SubnetId' --output text)
PRIV_SUBNETS=$(aws ec2 describe-subnets --filters Name=vpc-id,Values=$VPC_ID Name=map-public-ip-on-launch,Values=false --query 'Subnets[*].SubnetId' --output text)
echo "$VPC_ID"
echo "$PUB_SUBNETS"
echo "$PRIV_SUBNETS"
```

## 3) Build Worker Lambda Package

This repo expects: `dist/eip-workers.zip`.

```bash
rm -rf dist
mkdir -p dist/worker_build

# Build inside Linux container for Lambda compatibility
docker run --rm -v "$PWD":/var/task -w /var/task public.ecr.aws/sam/build-python3.12 \
  /bin/bash -lc "pip install -r requirements.txt -t dist/worker_build"

cp -r eip dist/worker_build/
cd dist/worker_build
zip -r ../eip-workers.zip .
cd ../..
ls -lh dist/eip-workers.zip
```

## 4) Build and Push API Image to ECR

This repo does not currently ship a Dockerfile. Create one:

```bash
cat > Dockerfile <<'EOF'
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY eip ./eip
EXPOSE 8000
CMD ["uvicorn", "eip.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
```

Create ECR repo, login, build, push:

```bash
aws ecr describe-repositories --repository-names eip-api --region us-east-1 >/dev/null 2>&1 || \
aws ecr create-repository --repository-name eip-api --region us-east-1

aws ecr get-login-password --region us-east-1 | \
docker login --username AWS --password-stdin 2233445566.dkr.ecr.us-east-1.amazonaws.com

docker build -t eip-api:latest .
docker tag eip-api:latest 2233445566.dkr.ecr.us-east-1.amazonaws.com/eip-api:latest
docker push 2233445566.dkr.ecr.us-east-1.amazonaws.com/eip-api:latest
```

## 5) Create and Populate Secrets

Create secret container once:

```bash
aws secretsmanager describe-secret --secret-id eip/integrations/dev --region us-east-1 >/dev/null 2>&1 || \
aws secretsmanager create-secret --name eip/integrations/dev --secret-string '{}' --region us-east-1
```

Populate required values:

```bash
aws secretsmanager put-secret-value \
  --secret-id eip/integrations/dev \
  --region us-east-1 \
  --secret-string '{
    "slack_bot_token": "xoxb-REPLACE_ME",
    "slack_default_channel": "#eip-dev-alerts",
    "pagerduty_token": "REPLACE_ME",
    "jenkins_api_token": "REPLACE_ME",
    "jenkins_user": "eip-service-account",
    "github_token": "REPLACE_ME",
    "anthropic_api_key": "sk-ant-REPLACE_ME"
  }'
```

## 6) Deploy Infrastructure

```bash
terraform -chdir=infra/terraform init
terraform -chdir=infra/terraform validate
terraform -chdir=infra/terraform plan -var-file=../../platform.auto.tfvars
terraform -chdir=infra/terraform apply -var-file=../../platform.auto.tfvars
```

## 7) Post-Deploy Checks

Get ALB URL:

```bash
terraform -chdir=infra/terraform output eip_api_alb_dns_name
```

Check API docs endpoint:

```bash
ALB=$(terraform -chdir=infra/terraform output -raw eip_api_alb_dns_name)
curl -i "http://$ALB/docs"
```

Smoke test risk scoring:

```bash
curl -X POST "http://$ALB/risk/score" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name":"payments-api",
    "environment":"production",
    "branch":"hotfix/test-live",
    "commit_sha":"live001",
    "commit_message":"live check",
    "commit_author":"ops",
    "commit_author_email":"ops@example.com",
    "changed_files":["infra/network.tf","src/payments.py"],
    "lines_added":120,
    "lines_deleted":25,
    "deploy_hour":15,
    "deploy_day":5,
    "build_url":"https://jenkins.example.com/job/100",
    "coverage_delta":-1.5
  }'
```

Smoke test incident webhook:

```bash
curl -X POST "http://$ALB/incidents/webhook/pagerduty" \
  -H "Content-Type: application/json" \
  -d '{
    "event": {
      "event_type": "incident.triggered",
      "data": {
        "id": "PD-LIVE-001",
        "service": {"summary": "payments-api"},
        "urgency": "high",
        "status": "triggered",
        "created_at": "2026-03-02T12:00:00+00:00"
      }
    }
  }'
```

## 8) Important Current Gaps (Known)

1. Live architecture/cost/compliance providers are transitional and still fallback to stub-like data paths.
2. ECS task definition currently does not inject `ANTHROPIC_API_KEY` from Secrets Manager automatically.
3. Lambda handlers are scaffolded for `incident_linker` and `graph_updater`; expand as more workers are wired.

Use `GO_LIVE_CHECKLIST.md` for full production readiness gating.
