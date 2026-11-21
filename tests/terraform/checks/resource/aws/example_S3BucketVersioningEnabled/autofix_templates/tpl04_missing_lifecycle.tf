resource "aws_s3_bucket" "b4" {
  bucket = "bucket-four"

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name = "four"
  }
}
