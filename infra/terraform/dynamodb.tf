resource "aws_dynamodb_table" "deployments" {
  count = local.create_resources ? 1 : 0

  name         = var.eip_deployments_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }

  dynamic "server_side_encryption" {
    for_each = var.kms_key_arn == null ? [] : [var.kms_key_arn]
    content {
      enabled     = true
      kms_key_arn = server_side_encryption.value
    }
  }
}

resource "aws_dynamodb_table" "risk_scores" {
  count = local.create_resources ? 1 : 0

  name         = var.eip_risk_scores_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  attribute {
    name = "service_name"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  global_secondary_index {
    name            = "service-created-at-index"
    hash_key        = "service_name"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }

  dynamic "server_side_encryption" {
    for_each = var.kms_key_arn == null ? [] : [var.kms_key_arn]
    content {
      enabled     = true
      kms_key_arn = server_side_encryption.value
    }
  }
}

resource "aws_dynamodb_table" "incidents" {
  count = local.create_resources ? 1 : 0

  name         = var.eip_incidents_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  attribute {
    name = "id"
    type = "S"
  }

  global_secondary_index {
    name            = "incident-id-index"
    hash_key        = "id"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }

  dynamic "server_side_encryption" {
    for_each = var.kms_key_arn == null ? [] : [var.kms_key_arn]
    content {
      enabled     = true
      kms_key_arn = server_side_encryption.value
    }
  }
}
