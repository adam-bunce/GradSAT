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