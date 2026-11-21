from __future__ import annotations

from collections.abc import Callable

from checkov.terraform.autofix.hcl_patcher import PatchOutcome, patch_s3_bucket_versioning

Fixer = Callable[[list[str]], PatchOutcome]

FIXERS: dict[str, Fixer] = {
    "CKV_AWS_AUTOFIX_1": patch_s3_bucket_versioning,
}


def get_fixer(check_id: str) -> Fixer | None:
    return FIXERS.get(check_id)
