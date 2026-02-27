output "provision_core_resources" {
  description = "Whether this run was configured to provision core infrastructure."
  value       = var.provision_core_resources
}

output "event_bus_name" {
  description = "Configured EventBridge bus name."
  value       = var.eip_event_bus_name
}

output "event_bus_arn" {
  description = "Created EventBridge bus ARN when provisioned."
  value       = try(aws_cloudwatch_event_bus.eip[0].arn, null)
}

output "dynamodb_table_names" {
  description = "Configured DynamoDB table names for EIP workers."
  value = {
    deployments = var.eip_deployments_table_name
    risk_scores = var.eip_risk_scores_table_name
    incidents   = var.eip_incidents_table_name
  }
}

output "dynamodb_table_arns" {
  description = "Created DynamoDB table ARNs when provisioned."
  value = {
    deployments = try(aws_dynamodb_table.deployments[0].arn, null)
    risk_scores = try(aws_dynamodb_table.risk_scores[0].arn, null)
    incidents   = try(aws_dynamodb_table.incidents[0].arn, null)
  }
}

output "worker_role_arn" {
  description = "Worker role ARN when created."
  value       = try(aws_iam_role.worker[0].arn, null)
}

output "integrations_secret_name" {
  description = "Configured integrations secret name."
  value       = var.eip_integrations_secret_name
}

output "integrations_secret_arn" {
  description = "Created secret ARN when create_integrations_secret=true."
  value       = try(aws_secretsmanager_secret.integrations[0].arn, null)
}
