import unittest

from checkov.common.models.enums import CheckResult
from checkov.terraform.checks.resource.aws.S3BucketVersioningEnabled import scanner


class TestS3BucketVersioningEnabled(unittest.TestCase):
    def test_missing_versioning_block_fails(self):
        conf = {"bucket": ["my-bucket"], "tags": [{"Name": "my-bucket"}]}

        result = scanner.scan_resource_conf(conf=conf)

        self.assertEqual(CheckResult.FAILED, result)

    def test_versioning_disabled_fails(self):
        conf = {"bucket": ["my-bucket"], "versioning": [{"enabled": [False]}]}

        result = scanner.scan_resource_conf(conf=conf)

        self.assertEqual(CheckResult.FAILED, result)

    def test_versioning_enabled_passes(self):
        conf = {"bucket": ["my-bucket"], "versioning": [{"enabled": [True]}]}

        result = scanner.scan_resource_conf(conf=conf)

        self.assertEqual(CheckResult.PASSED, result)

    def test_versioning_block_without_enabled_fails(self):
        conf = {"bucket": ["my-bucket"], "versioning": [{"mfa_delete": [False]}]}

        result = scanner.scan_resource_conf(conf=conf)

        self.assertEqual(CheckResult.FAILED, result)

    def test_variable_dependent_value_is_unknown(self):
        conf = {"bucket": ["my-bucket"], "versioning": [{"enabled": ["${var.enable_versioning}"]}]}

        result = scanner.scan_resource_conf(conf=conf)

        self.assertEqual(CheckResult.UNKNOWN, result)

    def test_check_metadata(self):
        self.assertEqual("CKV_AWS_AUTOFIX_1", scanner.id)
        self.assertIn("aws_s3_bucket", scanner.supported_resources)


if __name__ == "__main__":
    unittest.main()
