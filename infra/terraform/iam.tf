resource "aws_iam_user" "thesis" {
  name = "thesis"
  force_destroy = true
}

resource "aws_iam_access_key" "thesis" {
  user = aws_iam_user.thesis.name
}

data "aws_iam_policy_document"  "thesis" {
 statement {
   effect = "Allow"
   actions = ["erc:*", "ecs:*"]
   resources = ["*"]
 }
}

resource "aws_iam_user_policy" "thesis" {
  name = "thesis"
  user = aws_iam_user.thesis.name
  policy = data.aws_iam_policy_document.thesis.json
}


resource "aws_iam_role" "ecs_task_execution" {
  name = "thesis-ecs-task-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
