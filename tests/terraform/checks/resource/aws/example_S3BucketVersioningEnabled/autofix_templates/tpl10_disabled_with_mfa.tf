resource "aws_s3_bucket" "b10" {
  bucket = "bucket-ten"

  versioning {
    enabled = false
    mfa_delete = false
  }

  tags = {
    Name = "ten"
  }
}
