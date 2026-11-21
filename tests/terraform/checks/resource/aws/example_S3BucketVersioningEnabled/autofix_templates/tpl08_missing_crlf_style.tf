resource "aws_s3_bucket" "b8" {
    bucket = "bucket-eight"
    tags = {
        Name = "eight"
    }
}
