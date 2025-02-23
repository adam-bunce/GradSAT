resource "aws_ecs_cluster" "thesis" {
  name = "thesis"

}

resource "aws_ecs_task_definition" "thesis" {
  family = "thesis"
  requires_compatibilities = ["FARGATE"]
  cpu = 256
  memory = 512
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
    subnets = [aws_subnet.public.id]
    security_groups = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true
  }
}

