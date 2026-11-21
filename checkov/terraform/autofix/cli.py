from __future__ import annotations

import argparse
import logging
import sys

from checkov.terraform.autofix.engine import AutoFixEngine


def _parse_suppressions(values: list[str] | None) -> dict[str, str]:
    suppressions: dict[str, str] = {}
    for value in values or []:
        if "=" not in value:
            raise argparse.ArgumentTypeError(f"invalid suppression '{value}', expected format resource_address=reason")
        resource, reason = value.split("=", 1)
        suppressions[resource.strip()] = reason.strip()
    return suppressions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="checkov-autofix",
        description="Scan Terraform files for a check, apply safe HCL fix patches and re-scan.",
    )
    parser.add_argument("--check-id", default="CKV_AWS_AUTOFIX_1", help="check id with a registered fixer")
    parser.add_argument("-d", "--directory", help="root folder containing Terraform files")
    parser.add_argument("-f", "--file", action="append", help="Terraform file to scan, repeatable")
    parser.add_argument("--dry-run", action="store_true", help="scan and report fixes without writing files")
    parser.add_argument(
        "--suppress",
        action="append",
        metavar="RESOURCE=REASON",
        help="add a checkov:skip comment instead of patching, repeatable",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")

    if not args.directory and not args.file:
        logging.error("provide at least --directory or --file")
        return 2

    engine = AutoFixEngine(check_id=args.check_id)
    result = engine.run(
        root_folder=args.directory,
        files=args.file,
        dry_run=args.dry_run,
        suppressions=_parse_suppressions(args.suppress),
    )

    for item in result.fixed_resources:
        logging.info("FIXED  %s (%s) in %s", item.resource, item.action, item.file_path)
    for item in result.suppressed_resources:
        logging.info("SKIPPED %s in %s: %s", item.resource, item.file_path, item.comment)

    if result.dry_run:
        logging.info("dry-run: no files were modified")
        return 0

    if result.success:
        logging.info("re-scan passed for %s, %s file(s) updated", result.check_id, len(result.written_files))
        return 0

    logging.error("re-scan still failing for: %s", ", ".join(result.remaining_failures))
    return 1


if __name__ == "__main__":
    sys.exit(main())
