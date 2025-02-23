# NOTE: not sure if i need any of this anymore b/c i am now using a lb


resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
}


locals {
  ingress_ports = [
    {port = 3000, description = "ui"},
    {port = 8000, description = "api"},
    {port = 80, description = "web"},
    {port = 443, description = "web-secure"},
  ]
}

resource "aws_security_group" "ecs_tasks" {
  name   = "thesis-ecs-tasks"
  vpc_id = aws_vpc.main.id

  dynamic "ingress" {
    for_each = local.ingress_ports
    content {
      from_port = ingress.value.port
      to_port = ingress.value.port
      protocol = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
      description = ingress.value.description
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "all outbound traffic"
  }
}