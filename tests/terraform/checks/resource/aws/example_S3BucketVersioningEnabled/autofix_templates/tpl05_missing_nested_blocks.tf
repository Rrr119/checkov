resource "aws_s3_bucket" "b5" {
  bucket = "bucket-five"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  logging {
    target_bucket = "logs-bucket"
    target_prefix = "log/"
  }
}
