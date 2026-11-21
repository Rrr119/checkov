resource "aws_s3_bucket" "b15" {
  bucket = "bucket-fifteen"

  versioning {
    mfa_delete = false
  }
}
