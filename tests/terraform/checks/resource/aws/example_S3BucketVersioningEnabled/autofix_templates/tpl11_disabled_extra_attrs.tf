resource "aws_s3_bucket" "b11" {
  bucket          = "bucket-eleven"
  object_lock_enabled = false

  versioning {
    enabled = false
  }
}
