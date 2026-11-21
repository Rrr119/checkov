resource "aws_s3_bucket" "b12" {
    bucket = "bucket-twelve"

    versioning {
        enabled = false
    }
}
