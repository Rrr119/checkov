resource "aws_s3_bucket" "b20a" {
  bucket = "bucket-twenty-a"

  versioning {
    enabled = true
  }
}

resource "aws_s3_bucket" "b20b" {
  bucket = "bucket-twenty-b"

  tags = {
    Name = "twenty-b"
  }
}
