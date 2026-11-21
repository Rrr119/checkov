resource "aws_s3_bucket" "b7" {
  # bucket used by the analytics pipeline
  bucket = "bucket-seven"

  # keep default encryption on
  tags = {
    Name = "seven"
  }
}
