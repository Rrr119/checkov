from __future__ import annotations

import re
from dataclasses import dataclass

VERSIONING_OPEN_RE = re.compile(r"^(?P<indent>\s*)versioning\s*\{")
ENABLED_RE = re.compile(r"^(?P<indent>\s*)enabled\s*=\s*(?P<value>true|false)\s*$")


@dataclass
class PatchOutcome:
    lines: list[str]
    action: str
    inserted_lines: int


def _line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" \t"))


def _detect_inner_indent(lines: list[str], header_indent: int) -> int:
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("//"):
            indent = _line_indent(line)
            if indent > header_indent:
                return indent - header_indent
    return 2


def _find_versioning_block(lines: list[str]) -> tuple[int, int] | None:
    open_index = None
    for index, line in enumerate(lines):
        if VERSIONING_OPEN_RE.match(line):
            open_index = index
            break
    if open_index is None:
        return None

    depth = 0
    for index in range(open_index, len(lines)):
        depth += lines[index].count("{") - lines[index].count("}")
        if depth == 0:
            return open_index, index
    return None


def patch_s3_bucket_versioning(resource_lines: list[str]) -> PatchOutcome:
    """Add or enable the versioning block inside a single aws_s3_bucket resource."""
    if not resource_lines:
        raise ValueError("cannot patch an empty resource block")

    header_indent = _line_indent(resource_lines[0])
    unit = _detect_inner_indent(resource_lines, header_indent)
    inner_indent = " " * (header_indent + unit)
    value_indent = " " * (header_indent + unit * 2)

    block_range = _find_versioning_block(resource_lines)
    if block_range is None:
        close_index = next(
            index for index in range(len(resource_lines) - 1, -1, -1) if resource_lines[index].strip() == "}"
        )
        block = [
            f"{inner_indent}versioning {{\n",
            f"{value_indent}enabled = true\n",
            f"{inner_indent}}}\n",
        ]
        lines = resource_lines[:close_index] + block + resource_lines[close_index:]
        return PatchOutcome(lines=lines, action="added_versioning_block", inserted_lines=len(block))

    open_index, close_index = block_range
    for index in range(open_index + 1, close_index):
        match = ENABLED_RE.match(resource_lines[index])
        if match and match.group("value") == "false":
            updated = list(resource_lines)
            updated[index] = f"{match.group('indent')}enabled = true\n"
            return PatchOutcome(lines=updated, action="enabled_versioning", inserted_lines=0)

    updated = list(resource_lines)
    updated.insert(open_index + 1, f"{value_indent}enabled = true\n")
    return PatchOutcome(lines=updated, action="added_enabled_attribute", inserted_lines=1)
