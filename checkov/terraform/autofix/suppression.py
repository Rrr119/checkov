from __future__ import annotations

import re

SKIP_DIRECTIVE_RE = re.compile(r"checkov:skip=(?P<check_id>[A-Za-z_\d-]+)")


def add_skip_comment(resource_lines: list[str], check_id: str, reason: str) -> tuple[list[str], bool]:
    """Insert a checkov:skip comment inside a resource block when it is not suppressed yet.

    Checkov only collects skip directives whose line numbers are strictly inside the
    resource block, so the comment must follow the resource header line.
    """
    header = resource_lines[0]
    indent = header[: len(header) - len(header.lstrip(" \t"))]
    inner_indent = f"{indent}  "
    directive = f"{inner_indent}# checkov:skip={check_id}:{reason}\n"

    for line in resource_lines:
        match = SKIP_DIRECTIVE_RE.search(line)
        if match and match.group("check_id") == check_id:
            return list(resource_lines), False

    return [resource_lines[0], directive] + resource_lines[1:], True
