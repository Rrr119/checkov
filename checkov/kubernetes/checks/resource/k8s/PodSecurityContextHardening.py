from __future__ import annotations

from typing import Any

from checkov.common.models.enums import CheckResult
from checkov.kubernetes.checks.resource.base_root_container_check import BaseK8sRootContainerCheck


class PodSecurityContextHardening(BaseK8sRootContainerCheck):
    def __init__(self) -> None:
        # Pod Security Standards, Restricted profile
        # https://kubernetes.io/docs/concepts/security/pod-security-standards/#restricted
        name = "Harden the Pod Security Context"
        # The pod-level securityContext must prevent the containers from running as root and must
        # keep the workload inside the runtime default seccomp profile.
        # Location: Pod.spec.securityContext
        # Location: CronJob.spec.jobTemplate.spec.template.spec.securityContext
        # Location: *.spec.template.spec.securityContext
        id = "CKV_K8S_160"
        guideline = (
            "https://kubernetes.io/docs/concepts/security/pod-security-standards/#restricted"
            " - set spec.securityContext.runAsNonRoot to true (or runAsUser to a non-zero UID) "
            "and set spec.securityContext.seccompProfile.type to RuntimeDefault"
        )
        super().__init__(name=name, id=id, guideline=guideline)

    def scan_spec_conf(self, conf: dict[str, Any]) -> CheckResult:
        spec = self.extract_spec(conf)

        if not spec or not isinstance(spec, dict):
            return CheckResult.FAILED

        security_context = spec.get("securityContext")
        if not security_context or not isinstance(security_context, dict):
            self.evaluated_keys = ["securityContext"]
            return CheckResult.FAILED

        self.evaluated_keys = [
            "securityContext/runAsNonRoot",
            "securityContext/runAsUser",
            "securityContext/seccompProfile/type",
        ]

        runs_as_non_root = self.check_runAsNonRoot(spec) == "PASSED" or self.check_runAsUser(spec, 1) == "PASSED"
        seccomp_profile = security_context.get("seccompProfile")
        uses_runtime_default_seccomp = (
            isinstance(seccomp_profile, dict) and seccomp_profile.get("type") == "RuntimeDefault"
        )

        if runs_as_non_root and uses_runtime_default_seccomp:
            return CheckResult.PASSED
        return CheckResult.FAILED


check = PodSecurityContextHardening()
