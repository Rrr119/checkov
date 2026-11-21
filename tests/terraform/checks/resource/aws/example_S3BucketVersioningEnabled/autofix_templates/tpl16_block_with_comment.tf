resource "aws_s3_bucket" "b16" {
  bucket = "bucket-sixteen"

  versioning {
    # enabled flag must be set explicitly
  }
}
