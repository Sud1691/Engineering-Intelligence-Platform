resource "aws_ecs_cluster" "eip" {
  count = local.create_ecs ? 1 : 0

  name = "eip-platform-${var.environment}"
}

resource "aws_cloudwatch_log_group" "eip_api" {
  count = local.create_ecs ? 1 : 0

  name              = "/ecs/eip-api-${var.environment}"
  retention_in_days = 30
}

resource "aws_iam_role" "eip_api_task_execution" {
  count = local.create_ecs ? 1 : 0

  name = "eip-api-task-execution-${var.environment}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eip_api_task_execution_managed" {
  count = local.create_ecs ? 1 : 0

  role       = aws_iam_role.eip_api_task_execution[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_security_group" "eip_api_alb" {
  count = local.create_ecs ? 1 : 0

  name        = "eip-api-alb-${var.environment}"
  description = "Ingress for EIP API ALB"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "eip_api_task" {
  count = local.create_ecs ? 1 : 0

  name        = "eip-api-task-${var.environment}"
  description = "Task security group for EIP API"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.eip_api_alb[0].id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_lb" "eip_api" {
  count = local.create_ecs ? 1 : 0

  name               = "eip-api-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.eip_api_alb[0].id]
  subnets            = var.public_subnet_ids
}

resource "aws_lb_target_group" "eip_api" {
  count = local.create_ecs ? 1 : 0

  name        = "eip-api-tg-${var.environment}"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = "/docs"
    matcher             = "200-399"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
  }
}

resource "aws_lb_listener" "eip_api_http" {
  count = local.create_ecs ? 1 : 0

  load_balancer_arn = aws_lb.eip_api[0].arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.eip_api[0].arn
  }
}

resource "aws_ecs_task_definition" "eip_api" {
  count = local.create_ecs ? 1 : 0

  family                   = "eip-api-${var.environment}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 1024
  memory                   = 2048
  execution_role_arn       = aws_iam_role.eip_api_task_execution[0].arn
  task_role_arn            = aws_iam_role.worker[0].arn

  container_definitions = jsonencode(
    [
      {
        name    = "eip-api"
        image   = var.eip_docker_image
        command = ["uvicorn", "eip.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
        portMappings = [
          {
            containerPort = 8000
            protocol      = "tcp"
          }
        ]
        environment = [
          {
            name  = "EIP_RUNTIME_MODE"
            value = "live"
          },
          {
            name  = "EIP_ENABLE_LIVE_MODE"
            value = "true"
          },
          {
            name  = "EIP_AWS_REGION"
            value = var.eip_aws_region
          },
          {
            name  = "EIP_EVENT_BUS_NAME"
            value = var.eip_event_bus_name
          },
          {
            name  = "EIP_DEPLOYMENTS_TABLE_NAME"
            value = var.eip_deployments_table_name
          },
          {
            name  = "EIP_RISK_SCORES_TABLE_NAME"
            value = var.eip_risk_scores_table_name
          },
          {
            name  = "EIP_INCIDENTS_TABLE_NAME"
            value = var.eip_incidents_table_name
          },
          {
            name  = "EIP_INTEGRATIONS_SECRET_NAME"
            value = var.eip_integrations_secret_name
          },
        ]
        logConfiguration = {
          logDriver = "awslogs"
          options = {
            awslogs-group         = aws_cloudwatch_log_group.eip_api[0].name
            awslogs-region        = var.eip_aws_region
            awslogs-stream-prefix = "api"
          }
        }
      }
    ]
  )
}

resource "aws_ecs_service" "eip_api" {
  count = local.create_ecs ? 1 : 0

  name            = "eip-api-${var.environment}"
  cluster         = aws_ecs_cluster.eip[0].id
  task_definition = aws_ecs_task_definition.eip_api[0].arn
  desired_count   = var.ecs_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.eip_api_task[0].id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.eip_api[0].arn
    container_name   = "eip-api"
    container_port   = 8000
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  depends_on = [aws_lb_listener.eip_api_http]
}
