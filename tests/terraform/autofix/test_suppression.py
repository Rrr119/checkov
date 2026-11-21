import unittest

from checkov.terraform.autofix.suppression import add_skip_comment


class TestSuppression(unittest.TestCase):
    CHECK_ID = "CKV_AWS_AUTOFIX_1"

    def test_inserts_directive_inside_resource_block(self):
        lines = [
            'resource "aws_s3_bucket" "b" {\n',
            '  bucket = "b"\n',
            "}\n",
        ]

        patched, inserted = add_skip_comment(lines, self.CHECK_ID, "accepted risk")

        self.assertTrue(inserted)
        self.assertEqual(lines[0], patched[0])
        self.assertIn(f"# checkov:skip={self.CHECK_ID}:accepted risk", patched[1])

    def test_is_idempotent_when_directive_already_exists(self):
        lines = [
            'resource "aws_s3_bucket" "b" {\n',
            f"  # checkov:skip={self.CHECK_ID}:accepted risk\n",
            '  bucket = "b"\n',
            "}\n",
        ]

        patched, inserted = add_skip_comment(lines, self.CHECK_ID, "another reason")

        self.assertFalse(inserted)
        self.assertEqual(lines, patched)

    def test_directives_for_other_checks_are_not_duplicated(self):
        lines = [
            'resource "aws_s3_bucket" "b" {\n',
            "  # checkov:skip=CKV_AWS_999:other check\n",
            '  bucket = "b"\n',
            "}\n",
        ]

        patched, inserted = add_skip_comment(lines, self.CHECK_ID, "reason")

        self.assertTrue(inserted)
        self.assertEqual(2, sum("checkov:skip" in line for line in patched))


if __name__ == "__main__":
    unittest.main()
