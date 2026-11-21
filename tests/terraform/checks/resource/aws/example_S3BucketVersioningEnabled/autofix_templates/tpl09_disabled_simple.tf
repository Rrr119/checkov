resource "aws_s3_bucket" "b9" {
  bucket = "bucket-nine"

  versioning {
    enabled = false
  }
}
