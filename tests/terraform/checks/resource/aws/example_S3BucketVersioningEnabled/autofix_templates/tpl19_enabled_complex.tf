resource "aws_s3_bucket" "b19" {
  bucket = "bucket-nineteen"
  acl    = "private"

  versioning {
    enabled = true
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "aws:kms"
      }
    }
  }

  tags = {
    Name = "nineteen"
  }
}
