resource "aws_s3_bucket" "b3" {
  bucket = "bucket-three"
  acl    = "private"

  tags = {
    Name = "three"
  }
}
