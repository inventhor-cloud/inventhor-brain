import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from continuity.studio_factory_handoff import (
    StudioFactoryDenied, StudioFactorySnapshot, advise_studio_factory_handoff,
)

NOW = datetime(2026, 10, 26, 0, 10, tzinfo=timezone.utc)
HASH1 = "a" * 64
HASH2 = "b" * 64


def base():
    return StudioFactorySnapshot(
        native_task_id="EXISTING_TASK",
        project_id="INVENTHOR_PRODUCTION_ENGINE",
        design_document_id="STUDIO_REAL_PROJECT",
        native_task_revision=17,
        design_revision=4,
        phase="DESIGN_EDITED",
        observed_at=NOW,
    )


def judge(x=None, **changes):
    return advise_studio_factory_handoff(
        replace(base(), **changes) if x is None else x, now=NOW,
        expected_task_id="EXISTING_TASK",
        expected_project_id="INVENTHOR_PRODUCTION_ENGINE",
        expected_native_revision=17,
    )


def built(phase="BUILD_RUNNING", **changes):
    fields={
        "phase":phase, "build_sha256":HASH1,
        "real_preview_verified":True,
        "real_program_launch_verified":True,
    }
    fields.update(changes)
    return replace(base(),**fields)


class StudioFactoryHandoffTests(unittest.TestCase):
    def test_studio_design_next_is_real_build_and_launch(self):
        advice=judge()
        self.assertEqual(advice.disposition,"NATIVE_PREFLIGHT_REQUIRED")
        self.assertEqual(advice.next_action,
                         "OPERATOR_BUILD_LAUNCH_AND_VERIFY_REAL_STUDIO_PROGRAM")
        self.assertFalse(advice.may_create_task)
        self.assertFalse(advice.may_execute)
        self.assertFalse(advice.factory_pass_attested)

    def test_real_build_next_is_exact_factory_submission(self):
        advice=judge(built())
        self.assertEqual(advice.next_action,
                         "SUBMIT_EXACT_BUILD_TO_EXISTING_FACTORY")
        self.assertEqual(advice.disposition,"NATIVE_PREFLIGHT_REQUIRED")

    def test_fake_preview_does_not_qualify_as_running(self):
        s=built(real_preview_verified=False,
                real_program_launch_verified=False)
        advice=judge(s)
        self.assertIn("REAL_PREVIEW_NOT_VERIFIED",advice.blockers)
        self.assertIn("REAL_PROGRAM_NOT_VERIFIED",advice.blockers)
        self.assertEqual(advice.disposition,"BLOCKED")

    def test_factory_must_test_exact_artifact(self):
        s=built("QA_FAILED",factory_tested_sha256=HASH2,
                factory_run_id="QA_RUN_1",factory_verdict="FAIL",
                defect_evidence_ref="DEFECT_1",qa_witness_verified=True)
        advice=judge(s)
        self.assertIn("FACTORY_TESTED_DIFFERENT_BUILD",advice.blockers)

    def test_failed_factory_run_requires_evidence(self):
        s=built("QA_FAILED",factory_tested_sha256=HASH1,
                factory_run_id="QA_RUN_1",factory_verdict="FAIL",
                qa_witness_verified=False)
        blockers=judge(s).blockers
        self.assertIn("FACTORY_WITNESS_MISSING",blockers)
        self.assertIn("DEFECT_EVIDENCE_MISSING",blockers)

    def test_real_failed_build_routes_to_studio_repair(self):
        s=built("QA_FAILED",factory_tested_sha256=HASH1,
                factory_run_id="QA_RUN_1",factory_verdict="FAIL",
                defect_evidence_ref="BUG_1",qa_witness_verified=True)
        advice=judge(s)
        self.assertEqual(advice.disposition,"NATIVE_PREFLIGHT_REQUIRED")
        self.assertEqual(advice.next_action,
                         "REPAIR_DOCUMENT_IN_STUDIO_THEN_REBUILD")

    def test_repair_changes_build_and_document_revision(self):
        s=built("REPAIRED_RUNNING",iteration=2,build_sha256=HASH2,
                previous_failed_build_sha256=HASH1,
                previous_failed_factory_run_id="QA_FAILURE_1",
                previous_failure_evidence_ref="BUG_1",
                prior_design_revision=3,design_revision=4)
        advice=judge(s)
        self.assertEqual(advice.disposition,"NATIVE_PREFLIGHT_REQUIRED")
        self.assertEqual(advice.next_action,
                         "RESUBMIT_CHANGED_BUILD_TO_EXISTING_FACTORY")

    def test_uncorrected_source_rejected_for_retest(self):
        s=built("REPAIRED_RUNNING",iteration=2,build_sha256=HASH1,
                previous_failed_build_sha256=HASH1,
                prior_design_revision=4,design_revision=4)
        blockers=judge(s).blockers
        self.assertIn("REPAIR_DID_NOT_CHANGE_BUILD",blockers)
        self.assertIn("STUDIO_REVISION_DID_NOT_ADVANCE",blockers)

    def test_old_factory_result_must_not_be_reused_as_retest(self):
        s=built("REPAIRED_RUNNING",iteration=2,build_sha256=HASH2,
                previous_failed_build_sha256=HASH1,
                previous_failed_factory_run_id="QA_FAILURE_1",
                previous_failure_evidence_ref="BUG_1",
                prior_design_revision=3,design_revision=4,
                factory_tested_sha256=HASH1,
                factory_run_id="PREVIOUS_QA_RUN",
                factory_verdict="FAIL")
        blockers=judge(s).blockers
        self.assertIn("OLD_QA_RESULT_REUSED",blockers)
        self.assertIn("OLD_FACTORY_RUN_REUSED",blockers)
        self.assertIn("STALE_FACTORY_VERDICT",blockers)

    def test_matching_qa_pass_still_does_not_release(self):
        s=built("QA_PASSED",iteration=2,build_sha256=HASH2,
                previous_failed_build_sha256=HASH1,
                previous_failed_factory_run_id="QA_FAILURE_1",
                previous_failure_evidence_ref="BUG_1",
                prior_design_revision=3,design_revision=4,
                factory_tested_sha256=HASH2,
                factory_run_id="RETEST_QA_2",
                factory_verdict="PASS",qa_witness_verified=True,
                rollback_verified=True)
        a=judge(s)
        self.assertEqual(a.disposition,"NATIVE_PREFLIGHT_REQUIRED")
        self.assertEqual(a.next_action,
                         "REQUEST_SEPARATE_NATIVE_OWNER_RELEASE_PREFLIGHT")
        self.assertFalse(a.may_release)
        self.assertFalse(a.may_install)
        self.assertFalse(a.factory_pass_attested)
        self.assertFalse(a.native_evidence_authenticated)

    def test_repaired_build_must_carry_prior_failed_run_and_defect(self):
        s=built("REPAIRED_RUNNING",iteration=2,build_sha256=HASH2,
                previous_failed_build_sha256=HASH1,
                prior_design_revision=3,design_revision=4)
        advice=judge(s)
        self.assertEqual(advice.disposition,"BLOCKED")
        self.assertIn("PRIOR_FAILED_FACTORY_RUN_MISSING",advice.blockers)
        self.assertIn("PRIOR_FAILURE_EVIDENCE_MISSING",advice.blockers)
        self.assertFalse(advice.may_execute)

    def test_retest_cannot_reuse_failed_factory_run_id(self):
        s=built("QA_PASSED",iteration=2,build_sha256=HASH2,
                previous_failed_build_sha256=HASH1,
                previous_failed_factory_run_id="QA_RUN_1",
                previous_failure_evidence_ref="BUG_1",
                prior_design_revision=3,design_revision=4,
                factory_tested_sha256=HASH2,
                factory_run_id="QA_RUN_1",
                factory_verdict="PASS",qa_witness_verified=True,
                rollback_verified=True)
        self.assertIn("SAME_FACTORY_RUN_REUSED_FOR_RETEST",judge(s).blockers)

    def test_edited_design_cannot_claim_old_build_launch_or_qa(self):
        s=replace(base(),build_sha256=HASH1,
                  factory_tested_sha256=HASH1,factory_run_id="QA_OLD",
                  real_program_launch_verified=True,
                  qa_witness_verified=True)
        blocked=judge(s)
        for code in ("DESIGN_MUST_NOT_CARRY_OLD_BUILD",
                     "DESIGN_MUST_NOT_CARRY_OLD_QA",
                     "DESIGN_MUST_NOT_CARRY_OLD_QA_RUN",
                     "DESIGN_MUST_NOT_CLAIM_QA_WITNESS",
                     "DESIGN_MUST_NOT_CLAIM_REAL_LAUNCH"):
            self.assertIn(code,blocked.blockers)

    def test_pass_cannot_claim_current_failure_evidence(self):
        s=built("QA_PASSED",factory_tested_sha256=HASH1,
                factory_run_id="QA_RUN_1",factory_verdict="PASS",
                defect_evidence_ref="OLD_BUG",
                qa_witness_verified=True,rollback_verified=True)
        self.assertIn("CURRENT_PASS_CARRIES_FAILURE_EVIDENCE",judge(s).blockers)

    def test_single_first_qa_pass_needs_no_previous_failure(self):
        s=built("QA_PASSED",iteration=1,
                factory_tested_sha256=HASH1,factory_run_id="QA_FIRST",
                factory_verdict="PASS",qa_witness_verified=True,
                rollback_verified=True)
        a=judge(s)
        self.assertEqual(a.disposition,"NATIVE_PREFLIGHT_REQUIRED")
        self.assertFalse(a.factory_pass_attested)
        self.assertFalse(a.may_release)

    def test_wrong_project_and_stale_task_block(self):
        for s,code in (
            (replace(base(),project_id="ANOTHER_PROJECT"),"PROJECT_SCOPE_MISMATCH"),
            (replace(base(),native_task_id="OTHER_TASK"),"TASK_SCOPE_MISMATCH"),
            (replace(base(),native_task_revision=16),
             "STALE_NATIVE_TASK_REVISION"),
        ):
            with self.subTest(code=code):
                with self.assertRaises(StudioFactoryDenied) as e:
                    judge(s)
                self.assertEqual(e.exception.code,code)

    def test_stale_and_future_observations_rejected(self):
        for observed_at in (NOW-timedelta(seconds=61),
                            NOW+timedelta(seconds=6)):
            with self.subTest(observed_at=observed_at):
                with self.assertRaises(StudioFactoryDenied) as e:
                    judge(replace(base(),observed_at=observed_at))
                self.assertEqual(e.exception.code,"STALE_OR_FUTURE_SNAPSHOT")

    def test_fifth_failure_blocks_unbounded_auto_repair(self):
        s=built("QA_FAILED",iteration=5,factory_tested_sha256=HASH1,
                factory_run_id="QA_RUN_5",factory_verdict="FAIL",
                defect_evidence_ref="BUG_5",qa_witness_verified=True)
        self.assertIn("REPAIR_ITERATION_BUDGET_EXHAUSTED",judge(s).blockers)

    def test_boolean_and_hash_forgery_rejected(self):
        with self.assertRaises(StudioFactoryDenied):
            judge(built(real_preview_verified="yes"))
        with self.assertRaises(StudioFactoryDenied):
            judge(built(build_sha256="BAD_HASH"))

    def test_signed_approval_not_inferred_from_factory_report(self):
        s=built("QA_PASSED",factory_tested_sha256=HASH1,
                factory_run_id="QA_RUN_1",factory_verdict="PASS",
                qa_witness_verified=True,rollback_verified=False)
        a=judge(s)
        self.assertIn("ROLLBACK_NOT_VERIFIED",a.blockers)
        self.assertFalse(a.may_release)

    def test_unknown_phase_never_runs(self):
        with self.assertRaises(StudioFactoryDenied) as e:
            judge(phase="AUTO_INSTALL")
        self.assertEqual(e.exception.code,"INVALID_PHASE")


if __name__ == "__main__":
    unittest.main()
