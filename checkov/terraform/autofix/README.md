# Terraform auto-fix

Line-based HCL patching for Checkov Terraform checks that have a deterministic
remediation. Patches are applied against the parsed resource line ranges, so
unrelated resources, attributes and comments are never rewritten.

## Pipeline

1. Scan with the Terraform `Runner`, filtered to one check id.
2. For every failed record, look up the registered fixer in `registry.py`.
3. Patch only the affected resource lines; `--suppress` instead inserts an
   in-block `# checkov:skip=<id>:<reason>` directive for accepted false positives.
4. Re-scan the folder and fail when any targeted resource is still failing.

## CLI

```bash
python -m checkov.terraform.autofix.cli -d ./terraform
python -m checkov.terraform.autofix.cli -f main.tf --dry-run
python -m checkov.terraform.autofix.cli -d ./terraform \
  --suppress aws_s3_bucket.audit=versioning managed by account control
```

## Registered fixers

| Check id | Resource | Fix |
| --- | --- | --- |
| `CKV_AWS_AUTOFIX_1` | `aws_s3_bucket` | add/enable `versioning { enabled = true }` |

Skip directives must live inside the resource block because Checkov only
collects suppressions whose line numbers fall between the resource start and
end lines.
