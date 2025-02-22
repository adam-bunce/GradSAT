resource "aws_ecr_repository" "thesis" {
  name = "thesis"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

# keep last 5 images (really just need 1 tbh)
resource "aws_ecr_lifecycle_policy" "cleanup" {
  repository = aws_ecr_repository.thesis.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 5 images"
      selection = {
        tagStatus     = "any"
        countType     = "imageCountMoreThan"
        countNumber   = 5
      }
      action = {
        type = "expire"
      }
    }]
  })
}

