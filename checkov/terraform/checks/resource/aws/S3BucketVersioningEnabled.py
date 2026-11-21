from __future__ import annotations

from typing import Any

from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck


class S3BucketVersioningEnabled(BaseResourceCheck):
    def __init__(self) -> None:
        name = "Ensure S3 bucket has versioning enabled"
        check_id = "CKV_AWS_AUTOFIX_1"
        supported_resources = ("aws_s3_bucket",)
        categories = (CheckCategories.BACKUP_AND_RECOVERY,)
        super().__init__(
            name=name,
            id=check_id,
            categories=categories,
            supported_resources=supported_resources,
            guideline="Enable object versioning by adding a versioning block with enabled = true.",
        )

    def scan_resource_conf(self, conf: dict[str, list[Any]]) -> CheckResult:
        versioning = conf.get("versioning")
        if not versioning:
            self.evaluated_keys = ["versioning"]
            return CheckResult.FAILED

        block = versioning[0] if isinstance(versioning, list) else versioning
        if not isinstance(block, dict):
            self.evaluated_keys = ["versioning"]
            return CheckResult.FAILED

        enabled = block.get("enabled")
        if isinstance(enabled, list):
            enabled = enabled[0] if enabled else None
        if self._is_variable_dependant(enabled):
            self.evaluated_keys = ["versioning/[0]/enabled"]
            return CheckResult.UNKNOWN

        self.evaluated_keys = ["versioning/[0]/enabled"]
        return CheckResult.PASSED if enabled is True else CheckResult.FAILED


scanner = S3BucketVersioningEnabled()
