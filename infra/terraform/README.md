# EIP Terraform (Platform Module)

This directory contains the baseline Terraform module for EIP infrastructure.

It is designed to work with the same variable names already used by the app runtime (`platform.auto.tfvars`).

## What This Module Provisions

When `provision_core_resources=true`, Terraform creates:
- EventBridge bus (`eip_event_bus_name`)
- DynamoDB tables:
  - deployments (`eip_deployments_table_name`)
  - risk scores (`eip_risk_scores_table_name`)
  - incidents (`eip_incidents_table_name`)
- EventBridge rules for core EIP events
- Optional worker IAM role (`create_worker_role=true`)
- Optional integrations secret container (`create_integrations_secret=true`)

Optional live wiring:
- Lambda worker resources + DLQ/alarm (`enable_worker_lambdas=true`)
- EventBridge targets for incident linker/graph updater (enabled with worker lambdas)
- ECS/Fargate API stack + ALB (`enable_ecs_api=true`)

By default, no cloud resources are created.

## Usage

From repository root:

```bash
terraform -chdir=infra/terraform init
terraform -chdir=infra/terraform plan -var-file=../../platform.auto.tfvars
```

To actually create resources:

```bash
terraform -chdir=infra/terraform apply \
  -var-file=../../platform.auto.tfvars \
  -var='provision_core_resources=true'
```

Enable Lambda/EventBridge wiring:

```bash
terraform -chdir=infra/terraform apply \
  -var-file=../../platform.auto.tfvars \
  -var='provision_core_resources=true' \
  -var='enable_worker_lambdas=true'
```

Enable ECS API stack (requires VPC/subnets/image vars):

```bash
terraform -chdir=infra/terraform apply \
  -var-file=../../platform.auto.tfvars \
  -var='provision_core_resources=true' \
  -var='enable_ecs_api=true'
```

## Recommended Live Bootstrap Vars

Keep these in `platform.auto.tfvars` (or pass as `-var`):

```hcl
eip_runtime_mode = "live"
eip_enable_live_mode = true
provision_core_resources = true
create_worker_role = true
create_integrations_secret = true
create_integrations_secret_version = false
enable_worker_lambdas = true
# enable_ecs_api = true
# eip_docker_image = "123456789012.dkr.ecr.us-east-1.amazonaws.com/eip-api:latest"
```

## Notes

- `create_integrations_secret_version=false` is recommended initially, so no placeholder secrets are written to Terraform state.
- Worker Lambda code package is expected at `eip_workers_zip_path` (default `../../dist/eip-workers.zip`) when `enable_worker_lambdas=true`.
- ECS creation is guarded and only activates when VPC/subnets and `eip_docker_image` are provided.
- API Gateway, Neptune, and data lake modules remain out of this scope.
