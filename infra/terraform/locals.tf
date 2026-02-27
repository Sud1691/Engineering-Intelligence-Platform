locals {
  create_resources = var.provision_core_resources

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
