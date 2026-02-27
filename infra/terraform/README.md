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

## Recommended Live Bootstrap Vars

Keep these in `platform.auto.tfvars` (or pass as `-var`):

```hcl
eip_runtime_mode = "live"
eip_enable_live_mode = true
provision_core_resources = true
create_worker_role = true
create_integrations_secret = true
create_integrations_secret_version = false
```

## Notes

- `create_integrations_secret_version=false` is recommended initially, so no placeholder secrets are written to Terraform state.
- Event rules are created without targets in this baseline; wire targets (Lambda/SQS/ECS) in your environment module.
- This module intentionally focuses on core runtime dependencies and does not yet provision API Gateway, Lambda packaging, ECS services, Neptune, or data lake components.
