# Get AZs for the region
data "aws_availability_zones" "available" {
  state = "available"
}

# Two public subnets in different AZs
resource "aws_subnet" "public_1" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.4.0/24"  # Adjust CIDR as needed
  availability_zone = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "thesis-public-1"
  }
}

resource "aws_subnet" "public_2" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.3.0/24"  # Adjust CIDR as needed
  availability_zone = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = true

  tags = {
    Name = "thesis-public-2"
  }
}

resource "aws_route_table_association" "public_1" {
  subnet_id      = aws_subnet.public_1.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_2" {
  subnet_id      = aws_subnet.public_2.id
  route_table_id = aws_route_table.public.id
}

resource "aws_lb" "thesis" {
  name = "thesis-alb"
  internal = false
  load_balancer_type = "application"
  security_groups = [aws_security_group.alb.id]
  subnets = [aws_subnet.public_1.id, aws_subnet.public_2.id]
}

resource "aws_lb_listener" "ui" {
  load_balancer_arn = aws_lb.thesis.arn
  port = "80"
  protocol = "HTTP"

  default_action {
    type = "forward"
    target_group_arn = aws_lb_target_group.ui.arn
  }
}

resource "aws_lb_listener" "api" {
  load_balancer_arn = aws_lb.thesis.arn
  port = "8000"
  protocol = "HTTP"

  default_action {
    type = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

resource "aws_lb_target_group" "ui" {
  name = "thesis-ui"
  port = 3000
  protocol = "HTTP"
  vpc_id = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/"
    healthy_threshold   = 2
    unhealthy_threshold = 10
    timeout             = 30
    interval            = 60
  }
}

resource "aws_lb_target_group" "api" {
  name = "thesis-api"
  port = 8000
  protocol = "HTTP"
  vpc_id = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 10
    timeout             = 30
    interval            = 60
  }
}

resource "aws_security_group" "alb" {
  name   = "thesis-alb"
  vpc_id = aws_vpc.main.id

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

