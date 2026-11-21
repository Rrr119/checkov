resource "aws_s3_bucket" "b18" {
  bucket = "bucket-eighteen"

  versioning {
    enabled    = true
    mfa_delete = false
  }
}
