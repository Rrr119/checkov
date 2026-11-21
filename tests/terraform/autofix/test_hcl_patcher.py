import unittest

from checkov.terraform.autofix.hcl_patcher import patch_s3_bucket_versioning


class TestHclPatcher(unittest.TestCase):
    def test_adds_versioning_block_before_closing_brace(self):
        lines = [
            'resource "aws_s3_bucket" "b" {\n',
            '  bucket = "b"\n',
            "\n",
            "  tags = {\n",
            '    Name = "b"\n',
            "  }\n",
            "}\n",
        ]

        outcome = patch_s3_bucket_versioning(lines)

        self.assertEqual("added_versioning_block", outcome.action)
        self.assertEqual(3, outcome.inserted_lines)
        self.assertEqual("}\n", outcome.lines[-1])
        self.assertIn("  versioning {\n", outcome.lines)
        self.assertIn("    enabled = true\n", outcome.lines)

    def test_flips_disabled_enabled_flag(self):
        lines = [
            'resource "aws_s3_bucket" "b" {\n',
            '  bucket = "b"\n',
            "  versioning {\n",
            "    enabled = false\n",
            "  }\n",
            "}\n",
        ]

        outcome = patch_s3_bucket_versioning(lines)

        self.assertEqual("enabled_versioning", outcome.action)
        self.assertEqual(0, outcome.inserted_lines)
        self.assertEqual(len(lines), len(outcome.lines))
        self.assertIn("    enabled = true\n", outcome.lines)
        self.assertNotIn("enabled = false", "".join(outcome.lines))

    def test_adds_enabled_attribute_when_block_has_other_keys(self):
        lines = [
            'resource "aws_s3_bucket" "b" {\n',
            '  bucket = "b"\n',
            "  versioning {\n",
            "    mfa_delete = false\n",
            "  }\n",
            "}\n",
        ]

        outcome = patch_s3_bucket_versioning(lines)

        self.assertEqual("added_enabled_attribute", outcome.action)
        self.assertEqual(1, outcome.inserted_lines)
        self.assertIn("    enabled = true\n", outcome.lines)

    def test_adds_enabled_to_empty_versioning_block(self):
        lines = [
            'resource "aws_s3_bucket" "b" {\n',
            '  bucket = "b"\n',
            "  versioning {\n",
            "  }\n",
            "}\n",
        ]

        outcome = patch_s3_bucket_versioning(lines)

        self.assertEqual("added_enabled_attribute", outcome.action)
        self.assertEqual("    enabled = true\n", outcome.lines[3])

    def test_preserves_four_space_indentation(self):
        lines = [
            'resource "aws_s3_bucket" "b" {\n',
            '    bucket = "b"\n',
            "}\n",
        ]

        outcome = patch_s3_bucket_versioning(lines)

        self.assertIn("    versioning {\n", outcome.lines)
        self.assertIn("        enabled = true\n", outcome.lines)

    def test_keeps_existing_attributes_unchanged(self):
        original = [
            'resource "aws_s3_bucket" "b" {\n',
            '  bucket = "b"\n',
            '  acl    = "private"\n',
            "  tags = {\n",
            '    Name = "b"\n',
            "  }\n",
            "}\n",
        ]

        outcome = patch_s3_bucket_versioning(original)
        patched = "".join(outcome.lines)

        for line in original[:-1]:
            self.assertIn(line, patched)


if __name__ == "__main__":
    unittest.main()
