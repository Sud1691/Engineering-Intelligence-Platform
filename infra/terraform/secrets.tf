resource "aws_secretsmanager_secret" "integrations" {
  count = local.create_resources && var.create_integrations_secret ? 1 : 0

  name                    = var.eip_integrations_secret_name
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "integrations" {
  count = local.create_resources && var.create_integrations_secret && var.create_integrations_secret_version ? 1 : 0

  secret_id     = aws_secretsmanager_secret.integrations[0].id
  secret_string = jsonencode(var.integrations_secret_payload)
}
