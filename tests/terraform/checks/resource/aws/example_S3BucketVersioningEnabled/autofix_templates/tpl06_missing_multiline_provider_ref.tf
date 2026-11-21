resource "aws_s3_bucket" "b6" {
  bucket = "${var.name_prefix}-six"

  policy = data.aws_iam_policy_document.bucket_policy.json

  tags = merge(
    var.common_tags,
    {
      Owner = "platform"
    }
  )
}
