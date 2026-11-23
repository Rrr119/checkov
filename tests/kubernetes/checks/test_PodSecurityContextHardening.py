import os
import unittest

from checkov.kubernetes.checks.resource.k8s.PodSecurityContextHardening import check
from checkov.kubernetes.checks.resource.registry import registry
from checkov.kubernetes.runner import Runner
from checkov.runner_filter import RunnerFilter


class TestPodSecurityContextHardening(unittest.TestCase):

    def test_summary(self):
        runner = Runner()
        current_dir = os.path.dirname(os.path.realpath(__file__))

        report = runner.run(
            root_folder=current_dir + "/example_PodSecurityContextHardening",
            runner_filter=RunnerFilter(checks=[check.id]),
        )
        summary = report.get_summary()

        self.assertEqual(summary["passed"], 10)
        self.assertEqual(summary["failed"], 10)
        self.assertEqual(summary["skipped"], 0)
        self.assertEqual(summary["parsing_errors"], 0)

    def test_each_manifest_matches_manual_audit(self):
        runner = Runner()
        current_dir = os.path.dirname(os.path.realpath(__file__))

        report = runner.run(
            root_folder=current_dir + "/example_PodSecurityContextHardening",
            runner_filter=RunnerFilter(checks=[check.id]),
        )

        passed_resources = {record.resource for record in report.passed_checks}
        failed_resources = {record.resource for record in report.failed_checks}

        expected_passed = {
            "Pod.default.p1-pod-non-root-runtime-default",
            "Pod.default.p2-pod-run-as-user",
            "Deployment.default.p3-hardened-deployment",
            "DaemonSet.default.p4-hardened-daemonset",
            "StatefulSet.default.p5-hardened-statefulset",
            "ReplicaSet.default.p6-hardened-replicaset",
            "ReplicationController.default.p7-hardened-replicationcontroller",
            "Job.default.p8-hardened-job",
            "CronJob.default.p9-hardened-cronjob",
            "Pod.default.p10-pod-full-restricted-context",
        }
        expected_failed = {
            "Pod.default.f11-pod-no-security-context",
            "Pod.default.f12-pod-non-root-without-seccomp",
            "Pod.default.f13-pod-seccomp-without-non-root",
            "Pod.default.f14-pod-run-as-non-root-false",
            "Pod.default.f15-pod-run-as-user-zero",
            "Pod.default.f16-pod-localhost-seccomp",
            "Deployment.default.f17-deployment-without-security-context",
            "StatefulSet.default.f18-statefulset-root-allowed",
            "DaemonSet.default.f19-daemonset-without-seccomp",
            "CronJob.default.f20-cronjob-without-security-context",
        }

        self.assertEqual(passed_resources, expected_passed)
        self.assertEqual(failed_resources, expected_failed)
        self.assertEqual(len(passed_resources) + len(failed_resources), 20)

    def test_remediation_guideline_is_reported(self):
        runner = Runner()
        current_dir = os.path.dirname(os.path.realpath(__file__))

        report = runner.run(
            root_folder=current_dir + "/example_PodSecurityContextHardening",
            runner_filter=RunnerFilter(checks=[check.id]),
        )

        self.assertTrue(report.failed_checks)
        for record in report.failed_checks:
            self.assertEqual(record.guideline, check.guideline)
            self.assertIn("runAsNonRoot", record.guideline)
            self.assertIn("seccompProfile", record.guideline)

    def test_registered_for_all_supported_workloads(self):
        registered_checks = registry.checks
        for entity in check.supported_entities:
            self.assertIn(entity, registered_checks)
            self.assertIn(check, registered_checks[entity])

    def test_compatible_with_existing_kubernetes_checks(self):
        runner = Runner()
        current_dir = os.path.dirname(os.path.realpath(__file__))

        report = runner.run(
            root_folder=current_dir + "/example_SecurityContexts",
            runner_filter=RunnerFilter(checks=["CKV_K8S_29", "CKV_K8S_30", check.id]),
        )

        check_ids = {record.check_id for record in report.passed_checks + report.failed_checks}
        self.assertEqual(check_ids, {"CKV_K8S_29", "CKV_K8S_30", check.id})
        self.assertEqual(report.get_summary()["parsing_errors"], 0)


if __name__ == "__main__":
    unittest.main()
