from __future__ import annotations

import logging
from pathlib import Path

from checkov.runner_filter import RunnerFilter
from checkov.terraform.autofix.hcl_patcher import PatchOutcome
from checkov.terraform.autofix.models import AutoFixResult, FixedResource, SuppressedResource
from checkov.terraform.autofix.registry import get_fixer
from checkov.terraform.autofix.suppression import add_skip_comment
from checkov.terraform.runner import Runner
from checkov.terraform.tf_parser import TFParser

logger = logging.getLogger(__name__)


class AutoFixEngine:
    """Scan Terraform files, apply line-based HCL fix patches, then verify with a re-scan."""

    def __init__(self, check_id: str) -> None:
        self.check_id = check_id
        self._fixer = get_fixer(check_id)
        if self._fixer is None:
            raise ValueError(f"no auto-fixer registered for check {check_id}")

    def run(
        self,
        root_folder: str | None = None,
        files: list[str] | None = None,
        dry_run: bool = False,
        suppressions: dict[str, str] | None = None,
    ) -> AutoFixResult:
        suppressions = suppressions or {}
        runner_filter = RunnerFilter(checks=[self.check_id], show_progress_bar=False)
        report = Runner().run(root_folder=root_folder, files=files, runner_filter=runner_filter)
        if isinstance(report, list):  # pragma: no cover - terraform runner returns a single report
            raise RuntimeError("unexpected multi-report result from terraform runner")

        result = AutoFixResult(check_id=self.check_id, dry_run=dry_run)
        targets = self._collect_targets(report.failed_checks)
        result.scanned_files = len({record.file_path for record in report.failed_checks})

        file_patches: dict[str, list[tuple[int, int, list[str]]]] = {}
        for file_path, resources in targets.items():
            lines = Path(file_path).read_text().splitlines(keepends=True)
            for resource_name, start_line, end_line in resources:
                start_index = start_line - 1
                end_index = end_line
                resource_lines = lines[start_index:end_index]

                if resource_name in suppressions:
                    patched, inserted = add_skip_comment(resource_lines, self.check_id, suppressions[resource_name])
                    if inserted:
                        result.suppressed_resources.append(
                            SuppressedResource(
                                file_path=file_path,
                                resource=resource_name,
                                check_id=self.check_id,
                                comment=suppressions[resource_name],
                            )
                        )
                        file_patches.setdefault(file_path, []).append((start_index, end_index, patched))
                    continue

                outcome: PatchOutcome = self._fixer(resource_lines)
                result.fixed_resources.append(
                    FixedResource(
                        file_path=file_path,
                        resource=resource_name,
                        check_id=self.check_id,
                        action=outcome.action,
                        inserted_lines=outcome.inserted_lines,
                    )
                )
                file_patches.setdefault(file_path, []).append((start_index, end_index, outcome.lines))

        if not dry_run:
            for file_path, patches in file_patches.items():
                self._write_patched_file(file_path, patches)
                result.written_files.append(file_path)

            verification = Runner().run(
                root_folder=root_folder,
                files=files,
                runner_filter=RunnerFilter(checks=[self.check_id], show_progress_bar=False),
            )
            if isinstance(verification, list):  # pragma: no cover
                raise RuntimeError("unexpected multi-report result from terraform runner")
            result.remaining_failures = sorted({record.resource for record in verification.failed_checks})

            skipped = {record.resource for record in verification.skipped_checks if record.check_id == self.check_id}
            for item in result.suppressed_resources:
                if item.resource not in skipped:
                    result.remaining_failures.append(item.resource)

        return result

    @staticmethod
    def _collect_targets(records: list) -> dict[str, list[tuple[str, int, int]]]:
        targets: dict[str, list[tuple[str, int, int]]] = {}
        for record in records:
            line_range = record.file_line_range
            targets.setdefault(record.file_abs_path, []).append((record.resource, line_range[0], line_range[1]))
        return targets

    @staticmethod
    def _write_patched_file(file_path: str, patches: list[tuple[int, int, list[str]]]) -> None:
        lines = Path(file_path).read_text().splitlines(keepends=True)
        for start_index, end_index, replacement in sorted(patches, reverse=True):
            lines[start_index:end_index] = replacement
        Path(file_path).write_text("".join(lines))

    @staticmethod
    def parse_file_resources(file_path: str) -> dict[str, tuple[int, int]]:
        """Expose parsed resource line ranges, useful for tests and tooling."""
        definitions = TFParser().parse_file(file_path, parsing_errors=[])
        resources: dict[str, tuple[int, int]] = {}
        for block in definitions.get("resource", []):
            for resource_type, named in block.items():
                for name, conf in named.items():
                    resources[f"{resource_type}.{name}"] = (
                        conf["__start_line__"],
                        conf["__end_line__"],
                    )
        return resources
