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
