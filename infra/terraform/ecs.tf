resource "aws_ecs_cluster" "thesis" {
  name = "thesis"

}

resource "aws_ecs_task_definition" "thesis" {
  family = "thesis"

  container_definitions = jsonencode([
    {
      name = "ui"
      image = "${aws_ecr_repository.thesis.repository_url}/thesis-ui:latest"
      cpu = 1
      memory = 256
      portMappings = [
        {
          containerPort = 3000
          hostPort = 3000
        }
      ]
    }
  ])
}

resource "aws_ecs_service" "ui" {
  name = "thesis-ui"
  cluster = aws_ecs_cluster.thesis.id
  task_definition = aws_ecs_task_definition.thesis.arn
  desired_count = 1
}

