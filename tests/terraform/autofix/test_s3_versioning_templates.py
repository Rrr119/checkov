import shutil
import tempfile
import unittest
from pathlib import Path

from checkov.common.models.enums import CheckResult
from checkov.runner_filter import RunnerFilter
from checkov.terraform.autofix.engine import AutoFixEngine
from checkov.terraform.checks.resource.aws.S3BucketVersioningEnabled import scanner
from checkov.terraform.runner import Runner
from checkov.terraform.tf_parser import TFParser

CHECK_ID = "CKV_AWS_AUTOFIX_1"
TEMPLATE_DIR = (
    Path(__file__).parents[1]
    / "checks"
    / "resource"
    / "aws"
    / "example_S3BucketVersioningEnabled"
    / "autofix_templates"
)

PASSING_TEMPLATES = {
    "tpl17_enabled_simple.tf",
    "tpl18_enabled_with_mfa.tf",
    "tpl19_enabled_complex.tf",
}


def _scan_folder(folder: str):
    report = Runner().run(
        root_folder=folder,
        runner_filter=RunnerFilter(checks=[CHECK_ID], show_progress_bar=False),
    )
    return report


def _bucket_configs(folder: str) -> dict[str, dict]:
    configs: dict[str, dict] = {}
    for tf_file in Path(folder).glob("*.tf"):
        definitions = TFParser().parse_file(str(tf_file), parsing_errors=[])
        for block in definitions.get("resource", []):
            for resource_type, named in block.items():
                for name, conf in named.items():
                    if resource_type == "aws_s3_bucket":
                        configs[f"{resource_type}.{name}"] = conf
    return configs


class TestS3VersioningTemplates(unittest.TestCase):
    templates = sorted(path.name for path in TEMPLATE_DIR.glob("*.tf"))

    def test_templates_are_complete(self):
        self.assertEqual(20, len(self.templates))

    def test_all_templates_are_valid_hcl(self):
        for template in self.templates:
            with self.subTest(template=template):
                definitions = TFParser().parse_file(str(TEMPLATE_DIR / template), parsing_errors=[])
                self.assertTrue(definitions.get("resource"))

    def test_each_template_scan_matches_expectation(self):
        for template in self.templates:
            with self.subTest(template=template):
                definitions = TFParser().parse_file(str(TEMPLATE_DIR / template), parsing_errors=[])
                results = []
                for block in definitions.get("resource", []):
                    for _, named in block.items():
                        for _, conf in named.items():
                            results.append(scanner.scan_resource_conf(conf))
                if template in PASSING_TEMPLATES:
                    self.assertEqual([CheckResult.PASSED], results)
                elif template == "tpl20_enabled_multi_resource.tf":
                    self.assertEqual([CheckResult.PASSED, CheckResult.FAILED], results)
                else:
                    self.assertEqual([CheckResult.FAILED], results)

    def test_autofix_then_rescan_for_each_template(self):
        for template in self.templates:
            with self.subTest(template=template), tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp) / template
                shutil.copyfile(TEMPLATE_DIR / template, target)

                before = _bucket_configs(tmp)
                before_text = target.read_text()

                result = AutoFixEngine(CHECK_ID).run(root_folder=tmp)

                self.assertTrue(result.success, msg=f"re-scan failures: {result.remaining_failures}")
                self.assertEqual(0, len(_scan_folder(tmp).failed_checks))

                after = _bucket_configs(tmp)
                self.assertEqual(set(before), set(after), msg="resource set must not change")
                for address, before_conf in before.items():
                    after_conf = after[address]
                    for key, value in before_conf.items():
                        if key.startswith("__") or key == "versioning":
                            continue
                        self.assertEqual(value, after_conf[key], msg=f"{address}.{key} changed in {template}")

                if template in PASSING_TEMPLATES:
                    self.assertEqual([], result.fixed_resources)
                    self.assertEqual(before_text, target.read_text(), msg="passing template must stay untouched")
                else:
                    self.assertEqual(1, len(result.fixed_resources))
                    for address in after:
                        self.assertTrue(after[address]["versioning"][0]["enabled"][0])

    def test_fix_is_idempotent_on_each_template(self):
        for template in self.templates:
            with self.subTest(template=template), tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp) / template
                shutil.copyfile(TEMPLATE_DIR / template, target)

                AutoFixEngine(CHECK_ID).run(root_folder=tmp)
                after_first_run = target.read_text()
                second = AutoFixEngine(CHECK_ID).run(root_folder=tmp)

                self.assertTrue(second.success)
                self.assertEqual([], second.fixed_resources)
                self.assertEqual(after_first_run, target.read_text())

    def test_dry_run_never_modifies_templates(self):
        for template in self.templates:
            with self.subTest(template=template), tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp) / template
                shutil.copyfile(TEMPLATE_DIR / template, target)
                original = target.read_text()

                result = AutoFixEngine(CHECK_ID).run(root_folder=tmp, dry_run=True)

                self.assertTrue(result.dry_run)
                self.assertEqual([], result.written_files)
                self.assertEqual(original, target.read_text())

    def test_suppression_repairs_failure_without_touching_other_attributes(self):
        template = "tpl01_missing_simple.tf"
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / template
            shutil.copyfile(TEMPLATE_DIR / template, target)

            result = AutoFixEngine(CHECK_ID).run(
                root_folder=tmp,
                suppressions={"aws_s3_bucket.b1": "managed at account level"},
            )

            self.assertTrue(result.success)
            self.assertEqual(1, len(result.suppressed_resources))
            self.assertEqual([], result.fixed_resources)
            report = _scan_folder(tmp)
            self.assertEqual([], report.failed_checks)
            self.assertEqual(1, len(report.skipped_checks))
            self.assertEqual("managed at account level", report.skipped_checks[0].check_result["suppress_comment"])
            configs = _bucket_configs(tmp)
            self.assertNotIn("versioning", configs["aws_s3_bucket.b1"])
            self.assertEqual(["bucket-one"], configs["aws_s3_bucket.b1"]["bucket"])

    def test_multi_resource_file_fixes_only_failing_resource(self):
        template = "tpl20_enabled_multi_resource.tf"
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / template
            shutil.copyfile(TEMPLATE_DIR / template, target)

            result = AutoFixEngine(CHECK_ID).run(root_folder=tmp)

            self.assertTrue(result.success)
            self.assertEqual(["aws_s3_bucket.b20b"], [item.resource for item in result.fixed_resources])
            configs = _bucket_configs(tmp)
            self.assertTrue(configs["aws_s3_bucket.b20a"]["versioning"][0]["enabled"][0])
            self.assertTrue(configs["aws_s3_bucket.b20b"]["versioning"][0]["enabled"][0])
            self.assertEqual(["bucket-twenty-a"], configs["aws_s3_bucket.b20a"]["bucket"])
            self.assertEqual(["bucket-twenty-b"], configs["aws_s3_bucket.b20b"]["bucket"])


if __name__ == "__main__":
    unittest.main()
