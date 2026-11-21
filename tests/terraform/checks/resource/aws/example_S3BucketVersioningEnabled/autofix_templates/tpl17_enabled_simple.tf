resource "aws_s3_bucket" "b17" {
  bucket = "bucket-seventeen"

  versioning {
    enabled = true
  }
}
