from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FixedResource:
    file_path: str
    resource: str
    check_id: str
    action: str
    inserted_lines: int


@dataclass
class SuppressedResource:
    file_path: str
    resource: str
    check_id: str
    comment: str


@dataclass
class AutoFixResult:
    check_id: str
    scanned_files: int = 0
    fixed_resources: list[FixedResource] = field(default_factory=list)
    suppressed_resources: list[SuppressedResource] = field(default_factory=list)
    remaining_failures: list[str] = field(default_factory=list)
    written_files: list[str] = field(default_factory=list)
    dry_run: bool = False

    @property
    def success(self) -> bool:
        return not self.remaining_failures
