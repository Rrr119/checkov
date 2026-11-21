resource "aws_s3_bucket" "b13" {
  bucket = "bucket-thirteen"

  versioning {
    # enabled intentionally omitted
  }
}
