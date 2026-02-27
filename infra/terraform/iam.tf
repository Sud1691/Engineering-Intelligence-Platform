data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

locals {
  integrations_secret_arn = "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${var.eip_integrations_secret_name}*"
}

resource "aws_iam_role" "worker" {
  count = local.create_resources && var.create_worker_role ? 1 : 0

  name = var.worker_role_name
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = [
            "lambda.amazonaws.com",
            "ecs-tasks.amazonaws.com",
          ]
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "worker_access" {
  count = local.create_resources && var.create_worker_role ? 1 : 0

  name = "${var.worker_role_name}-access"
  role = aws_iam_role.worker[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DynamoDbWriteRead"
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:Query",
          "dynamodb:UpdateItem",
          "dynamodb:GetItem",
        ]
        Resource = [
          aws_dynamodb_table.deployments[0].arn,
          aws_dynamodb_table.risk_scores[0].arn,
          aws_dynamodb_table.incidents[0].arn,
          "${aws_dynamodb_table.risk_scores[0].arn}/index/*",
          "${aws_dynamodb_table.incidents[0].arn}/index/*",
        ]
      },
      {
        Sid      = "PutEvents"
        Effect   = "Allow"
        Action   = ["events:PutEvents"]
        Resource = [aws_cloudwatch_event_bus.eip[0].arn]
      },
      {
        Sid      = "ReadIntegrationsSecret"
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = [local.integrations_secret_arn]
      },
      {
        Sid    = "WorkerLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = ["*"]
      },
    ]
  })
}
