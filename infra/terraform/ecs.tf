resource "aws_ecs_cluster" "thesis" {
  name = "thesis"

}

resource "aws_cloudwatch_log_group" "ecs_logs" {
  name = "/ecs/thesis"
  retention_in_days = 1
}


resource "aws_ecs_task_definition" "thesis" {
  family = "thesis"
  requires_compatibilities = ["FARGATE"]
  cpu = 256
  memory = 512

#  cpu    = 4096  # 4 vCPU
#  memory = 8192  # 8GB RAM
  network_mode = "awsvpc"
  execution_role_arn = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([
    {
      name = "ui"
      image = "${aws_ecr_repository.thesis.repository_url}:ui"
      portMappings = [
        {
          containerPort = 3000
          hostPort = 3000
        }
      ]
    },
    {
      name = "api"
      image = "${aws_ecr_repository.thesis.repository_url}:api"
      portMappings = [
        {
          containerPort = 8000
          hostPort = 8000
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group" = aws_cloudwatch_log_group.ecs_logs.name
          "awslogs-region" = "us-east-1"
          "awslogs-stream-prefix" = "ecs"
        }
      }

    }
  ])

}

resource "aws_ecs_service" "thesis" {
  name = "thesis"
  cluster = aws_ecs_cluster.thesis.id
  task_definition = aws_ecs_task_definition.thesis.arn
  desired_count = 1
  launch_type = "FARGATE"

  network_configuration {
    subnets = [aws_subnet.public_1.id, aws_subnet.public_2.id]
    security_groups = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true
  }

  load_balancer {
    container_name = "ui"
    target_group_arn = aws_lb_target_group.ui.arn
    container_port = 3000
  }

  load_balancer {
    container_name = "api"
    target_group_arn = aws_lb_target_group.api.arn
    container_port = 8000
  }

  depends_on = [aws_lb_listener.ui, aws_lb_listener.api, aws_lb.thesis]
}

