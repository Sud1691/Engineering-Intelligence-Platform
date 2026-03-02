locals {
  create_resources = var.provision_core_resources
  create_lambdas   = local.create_resources && var.enable_worker_lambdas && var.create_worker_role
  create_ecs = (
    local.create_resources
    && var.enable_ecs_api
    && var.create_worker_role
    && var.vpc_id != null
    && length(var.private_subnet_ids) > 0
    && length(var.public_subnet_ids) > 0
    && var.eip_docker_image != null
  )

  worker_event_patterns = {
    deployment_scored = ["eip.deployment.scored"]
    incident_created  = ["eip.incident.created"]
    incident_linked   = ["eip.incident.linked_to_deployment"]
    snapshot_refreshed = [
      "eip.architecture.snapshot.updated",
      "eip.architecture.snapshot.received",
    ]
  }

  default_tags = merge(
    {
      Project     = "engineering-intelligence-platform"
      Service     = "eip"
      Environment = var.environment
      ManagedBy   = "terraform"
      RuntimeMode = var.eip_runtime_mode
    },
    var.tags,
  )
}
