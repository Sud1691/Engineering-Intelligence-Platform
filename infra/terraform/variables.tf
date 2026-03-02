variable "eip_runtime_mode" {
  description = "Runtime mode used by the platform application."
  type        = string
  default     = "stub"

  validation {
    condition     = contains(["stub", "live"], var.eip_runtime_mode)
    error_message = "eip_runtime_mode must be either \"stub\" or \"live\"."
  }
}

variable "eip_enable_live_mode" {
  description = "Live mode guard. Keep false for stub-only local execution."
  type        = bool
  default     = false
}

variable "eip_aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "us-east-1"
}

variable "eip_event_bus_name" {
  description = "EventBridge bus name consumed by eip/core/event_bus.py."
  type        = string
  default     = "eip-event-bus"
}

variable "eip_deployments_table_name" {
  description = "DynamoDB table for deployment history."
  type        = string
  default     = "eip-deployments"
}

variable "eip_risk_scores_table_name" {
  description = "DynamoDB table for risk score records."
  type        = string
  default     = "eip-risk-scores"
}

variable "eip_incidents_table_name" {
  description = "DynamoDB table for incidents."
  type        = string
  default     = "eip-incidents"
}

variable "eip_integrations_secret_name" {
  description = "AWS Secrets Manager secret name for integration credentials."
  type        = string
  default     = "eip/integrations"
}

variable "eip_slack_default_channel" {
  description = "Default Slack destination channel used by platform logic."
  type        = string
  default     = "#deployments"
}

variable "eip_incident_link_window_hours" {
  description = "Correlation window used by incident linker worker."
  type        = number
  default     = 2

  validation {
    condition     = var.eip_incident_link_window_hours > 0
    error_message = "eip_incident_link_window_hours must be greater than 0."
  }
}

variable "provision_core_resources" {
  description = "Create core AWS objects (EventBridge, DynamoDB, IAM, optional secret)."
  type        = bool
  default     = false
}

variable "create_worker_role" {
  description = "Create a least-privilege IAM role for EIP workers."
  type        = bool
  default     = true
}

variable "worker_role_name" {
  description = "Name of IAM role created for workers."
  type        = string
  default     = "eip-worker-role"
}

variable "create_integrations_secret" {
  description = "Create the integrations secret container in Secrets Manager."
  type        = bool
  default     = false
}

variable "create_integrations_secret_version" {
  description = "Create an initial secret version. Keep false to avoid placeholder values in state."
  type        = bool
  default     = false
}

variable "integrations_secret_payload" {
  description = "Initial JSON payload for integrations secret (only used when create_integrations_secret_version=true)."
  type        = map(string)
  default = {
    slack_bot_token       = "REPLACE_ME"
    slack_default_channel = "#deployments"
    pagerduty_token       = "REPLACE_ME"
  }
  sensitive = true
}

variable "enable_point_in_time_recovery" {
  description = "Enable PITR on DynamoDB tables."
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "Optional KMS CMK ARN for DynamoDB table encryption."
  type        = string
  default     = null
}

variable "environment" {
  description = "Environment tag value (dev/staging/prod)."
  type        = string
  default     = "dev"
}

variable "tags" {
  description = "Additional tags applied to all resources."
  type        = map(string)
  default     = {}
}

variable "enable_worker_lambdas" {
  description = "Provision worker Lambda functions and supporting DLQ/alarm resources."
  type        = bool
  default     = false
}

variable "eip_workers_zip_path" {
  description = "Path to worker deployment package zip."
  type        = string
  default     = "../../dist/eip-workers.zip"
}

variable "lambda_timeout_seconds" {
  description = "Default Lambda timeout in seconds."
  type        = number
  default     = 300
}

variable "lambda_memory_mb" {
  description = "Default Lambda memory in MB."
  type        = number
  default     = 512
}

variable "enable_ecs_api" {
  description = "Provision ECS/Fargate resources for the EIP API."
  type        = bool
  default     = false
}

variable "eip_docker_image" {
  description = "Docker image URI for eip-api container."
  type        = string
  default     = null
}

variable "vpc_id" {
  description = "VPC ID used for ALB/ECS networking."
  type        = string
  default     = null
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for ALB."
  type        = list(string)
  default     = []
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for ECS tasks."
  type        = list(string)
  default     = []
}

variable "ecs_desired_count" {
  description = "Desired number of API tasks in ECS service."
  type        = number
  default     = 2
}
