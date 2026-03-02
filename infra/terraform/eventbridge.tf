resource "aws_cloudwatch_event_bus" "eip" {
  count = local.create_resources ? 1 : 0

  name = var.eip_event_bus_name
}

resource "aws_cloudwatch_event_rule" "worker_triggers" {
  for_each = local.create_resources ? local.worker_event_patterns : {}

  name           = "eip-${replace(each.key, "_", "-")}-${var.environment}"
  description    = "EIP event pattern for ${each.key}."
  event_bus_name = aws_cloudwatch_event_bus.eip[0].name
  event_pattern = jsonencode({
    "source"      = ["eip.platform"]
    "detail-type" = each.value
  })
}

resource "aws_cloudwatch_event_target" "incident_created_to_linker" {
  count = local.create_lambdas ? 1 : 0

  rule           = aws_cloudwatch_event_rule.worker_triggers["incident_created"].name
  event_bus_name = aws_cloudwatch_event_bus.eip[0].name
  target_id      = "incident-linker"
  arn            = aws_lambda_function.incident_linker[0].arn
}

resource "aws_cloudwatch_event_target" "deployment_scored_to_graph" {
  count = local.create_lambdas ? 1 : 0

  rule           = aws_cloudwatch_event_rule.worker_triggers["deployment_scored"].name
  event_bus_name = aws_cloudwatch_event_bus.eip[0].name
  target_id      = "graph-updater"
  arn            = aws_lambda_function.graph_updater[0].arn
}

resource "aws_cloudwatch_event_target" "snapshot_refreshed_to_graph" {
  count = local.create_lambdas ? 1 : 0

  rule           = aws_cloudwatch_event_rule.worker_triggers["snapshot_refreshed"].name
  event_bus_name = aws_cloudwatch_event_bus.eip[0].name
  target_id      = "graph-updater-snapshot"
  arn            = aws_lambda_function.graph_updater[0].arn
}

resource "aws_lambda_permission" "allow_eventbridge_incident_linker" {
  count = local.create_lambdas ? 1 : 0

  statement_id  = "AllowExecutionFromEventBridgeIncident"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.incident_linker[0].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.worker_triggers["incident_created"].arn
}

resource "aws_lambda_permission" "allow_eventbridge_graph_updater_deploy" {
  count = local.create_lambdas ? 1 : 0

  statement_id  = "AllowExecutionFromEventBridgeDeploy"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.graph_updater[0].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.worker_triggers["deployment_scored"].arn
}

resource "aws_lambda_permission" "allow_eventbridge_graph_updater_snapshot" {
  count = local.create_lambdas ? 1 : 0

  statement_id  = "AllowExecutionFromEventBridgeSnapshot"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.graph_updater[0].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.worker_triggers["snapshot_refreshed"].arn
}
