resource "aws_sns_topic" "eip_alerts" {
  count = local.create_lambdas ? 1 : 0

  name = "eip-platform-alerts-${var.environment}"
}

resource "aws_sqs_queue" "incident_linker_dlq" {
  count = local.create_lambdas ? 1 : 0

  name                      = "eip-incident-linker-dlq-${var.environment}"
  message_retention_seconds = 1209600
}

resource "aws_cloudwatch_metric_alarm" "incident_linker_dlq_alarm" {
  count = local.create_lambdas ? 1 : 0

  alarm_name          = "eip-incident-linker-dlq-depth-${var.environment}"
  alarm_description   = "CRITICAL: Incident linker failed and DLQ has pending messages."
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  dimensions          = { QueueName = aws_sqs_queue.incident_linker_dlq[0].name }
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  alarm_actions       = [aws_sns_topic.eip_alerts[0].arn]
}

resource "aws_lambda_function" "incident_linker" {
  count = local.create_lambdas ? 1 : 0

  function_name = "eip-incident-linker-${var.environment}"
  description   = "Links PagerDuty incidents to deployments (feedback loop)."
  role          = aws_iam_role.worker[0].arn
  runtime       = "python3.12"
  handler       = "eip.workers.incident_linker.lambda_handler"
  timeout       = var.lambda_timeout_seconds
  memory_size   = var.lambda_memory_mb
  filename      = var.eip_workers_zip_path

  dead_letter_config {
    target_arn = aws_sqs_queue.incident_linker_dlq[0].arn
  }

  environment {
    variables = {
      EIP_RUNTIME_MODE     = "live"
      EIP_ENABLE_LIVE_MODE = "true"
    }
  }
}

resource "aws_lambda_function" "graph_updater" {
  count = local.create_lambdas ? 1 : 0

  function_name = "eip-graph-updater-${var.environment}"
  description   = "Applies architecture snapshots to graph state."
  role          = aws_iam_role.worker[0].arn
  runtime       = "python3.12"
  handler       = "eip.workers.graph_updater.lambda_handler"
  timeout       = var.lambda_timeout_seconds
  memory_size   = var.lambda_memory_mb
  filename      = var.eip_workers_zip_path

  environment {
    variables = {
      EIP_RUNTIME_MODE     = "live"
      EIP_ENABLE_LIVE_MODE = "true"
    }
  }
}
