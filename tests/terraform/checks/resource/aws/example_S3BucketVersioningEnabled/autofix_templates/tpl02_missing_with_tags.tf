resource "aws_s3_bucket" "b2" {
  bucket = "bucket-two"

  tags = {
    Name        = "two"
    Environment = "dev"
  }
}
