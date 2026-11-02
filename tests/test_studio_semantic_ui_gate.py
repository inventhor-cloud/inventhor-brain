"""Source-only Brain→existing Studio semantic UI review regression tests."""
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from continuity.studio_semantic_ui_gate import (
    SemanticUiEditSnapshot, StudioUiReviewInvalid,
    review_studio_semantic_ui_edit,
)

NOW = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
BEFORE = "a" * 64
AFTER = "b" * 64
STRANGER = "c" * 64


def base():
    return SemanticUiEditSnapshot(
        existing_task_id="CANONICAL_TASK",
        project_id="APP_DESIGN",
        design_document_id="STUDIO_DOCUMENT",
        native_task_revision=20,
        previous_design_revision=5,
        design_revision=6,
        observed_at=NOW,
        operation="UI_SET_CONSTRAINT",
        target_semantic_id="panel.right.inspector",
        intended_touched_ids=("panel.right.inspector",),
        observed_touched_ids=("panel.right.inspector",),
        before_manifest_sha256=BEFORE,
        after_manifest_sha256=AFTER,
        preview_manifest_sha256=AFTER,
        preview_document_revision=6,
        expected_platforms=("WINDOWS_DESKTOP",),
        tested_platforms=("WINDOWS_DESKTOP",),
        real_preview_observed=True,
        target_action_effect_observed=True,
        no_clipping_or_overlap_observed=True,
        focus_and_hit_targets_observed=True,
        localization_expansion_observed=True,
        undo_checkpoint_observed=True,
    )


def check(**changes):
    return review_studio_semantic_ui_edit(
        replace(base(), **changes),
        now=NOW,
        expected_task_id="CANONICAL_TASK",
        expected_project_id="APP_DESIGN",
        expected_document_id="STUDIO_DOCUMENT",
        expected_native_revision=20,
    )


class SemanticUiGateTests(unittest.TestCase):
    def test_complete_source_packet_still_never_authorizes_native_change(self):
        result = check()
        self.assertEqual(result.disposition, "NATIVE_STUDIO_REVIEW_REQUIRED")
        self.assertEqual(result.blockers, ())
        self.assertEqual(result.next_action,
                         "REQUEST_EXISTING_STUDIO_NATIVE_RENDER_AND_ACTION_EFFECT_WITNESS")
        for flag in ("native_evidence_authenticated",
                     "preview_verified_by_native_host", "design_applied",
                     "organizer_updated", "may_execute", "may_release"):
            self.assertFalse(getattr(result, flag), flag)
        self.assertIn("SOURCE_ONLY", result.source_class)

    def test_stale_preview_revision_and_manifest_block(self):
        result = check(preview_document_revision=5,
                       preview_manifest_sha256=STRANGER)
        self.assertEqual(result.disposition, "BLOCKED")
        self.assertIn("STALE_PREVIEW_REVISION", result.blockers)
        self.assertIn("PREVIEW_OF_DIFFERENT_DOCUMENT", result.blockers)

    def test_unrelated_component_cannot_change(self):
        result = check(
            intended_touched_ids=("panel.right.inspector",),
            observed_touched_ids=("panel.right.inspector",
                                  "toolbar.global.send"))
        self.assertIn("UNRELATED_COMPONENT_MUTATED", result.blockers)

    def test_target_must_have_real_change(self):
        result = check(
            observed_touched_ids=("panel.left.navigation",))
        self.assertIn("SEMANTIC_TARGET_NOT_CHANGED", result.blockers)
        self.assertIn("UNRELATED_COMPONENT_MUTATED", result.blockers)

    def test_semantic_target_must_be_preapproved(self):
        result = check(intended_touched_ids=("panel.left.navigation",))
        self.assertIn("SEMANTIC_TARGET_NOT_IN_SCOPE", result.blockers)
        self.assertIn("UNRELATED_COMPONENT_MUTATED", result.blockers)

    def test_revision_and_manifest_must_advance(self):
        result = check(design_revision=5, after_manifest_sha256=BEFORE,
                       preview_manifest_sha256=BEFORE,
                       preview_document_revision=5)
        self.assertIn("DESIGN_REVISION_NOT_ADVANCED", result.blockers)
        self.assertIn("NO_DOCUMENT_MANIFEST_CHANGE", result.blockers)

    def test_platform_coverage_required(self):
        result = check(
            expected_platforms=("WINDOWS_DESKTOP", "ANDROID_PHONE"),
            tested_platforms=("WINDOWS_DESKTOP",))
        self.assertIn("RESPONSIVE_PLATFORM_NOT_TESTED", result.blockers)

    def test_mobile_and_desktop_both_tested(self):
        result = check(
            expected_platforms=("WINDOWS_DESKTOP", "ANDROID_PHONE"),
            tested_platforms=("ANDROID_PHONE", "WINDOWS_DESKTOP"))
        self.assertEqual(result.disposition, "NATIVE_STUDIO_REVIEW_REQUIRED")

    def test_visual_touch_and_localization_are_not_optional(self):
        result = check(
            real_preview_observed=False,
            target_action_effect_observed=False,
            no_clipping_or_overlap_observed=False,
            focus_and_hit_targets_observed=False,
            localization_expansion_observed=False,
            undo_checkpoint_observed=False)
        self.assertEqual(result.disposition, "BLOCKED")
        self.assertEqual(len(result.blockers), 6)
        self.assertIn("FOCUS_OR_TOUCH_NOT_CHECKED", result.blockers)
        self.assertIn("LOCALIZATION_NOT_CHECKED", result.blockers)
        self.assertIn("UNDO_CHECKPOINT_NOT_OBSERVED", result.blockers)

    def test_stale_native_organizer_context_is_denied(self):
        with self.assertRaises(StudioUiReviewInvalid) as cm:
            check(native_task_revision=21)
        self.assertEqual(cm.exception.code, "STALE_ORGANIZER_REVISION")

    def test_wrong_project_task_or_design_document_denied(self):
        for changed, expected in (
            ({"existing_task_id": "OTHER_TASK"}, "TASK_SCOPE_MISMATCH"),
            ({"project_id": "OTHER_PROJECT"}, "PROJECT_SCOPE_MISMATCH"),
            ({"design_document_id": "OTHER_DOCUMENT"}, "DOCUMENT_SCOPE_MISMATCH"),
        ):
            with self.subTest(changed=changed):
                with self.assertRaises(StudioUiReviewInvalid) as cm:
                    check(**changed)
                self.assertEqual(cm.exception.code, expected)

    def test_stale_or_future_observation_denied(self):
        for stamp in (NOW - timedelta(seconds=61),
                      NOW + timedelta(seconds=6)):
            with self.subTest(stamp=stamp):
                with self.assertRaises(StudioUiReviewInvalid) as cm:
                    check(observed_at=stamp)
                self.assertEqual(cm.exception.code, "STALE_OR_FUTURE_EDIT_OBSERVATION")

    def test_naive_timestamp_denied(self):
        with self.assertRaises(StudioUiReviewInvalid) as cm:
            check(observed_at=datetime(2026, 11, 2, 12))
        self.assertEqual(cm.exception.code, "AWARE_TIMESTAMPS_REQUIRED")

    def test_duplicate_targets_denied(self):
        with self.assertRaises(StudioUiReviewInvalid) as cm:
            check(observed_touched_ids=("panel.right.inspector",
                                        "panel.right.inspector"))
        self.assertEqual(cm.exception.code, "DUPLICATE_OBSERVED_TARGETS")

    def test_unbounded_touched_scope_rejected(self):
        with self.assertRaises(StudioUiReviewInvalid) as cm:
            check(intended_touched_ids=tuple("panel." + str(i)
                                            for i in range(17)))
        self.assertEqual(cm.exception.code, "INVALID_INTENDED_TARGETS")

    def test_unknown_operation_and_target_denied(self):
        for change, expected in (
            ({"operation": "EXECUTE_POWERSHELL"}, "UNSUPPORTED_UI_OPERATION"),
            ({"target_semantic_id": "../escape"}, "INVALID_SEMANTIC_TARGET"),
        ):
            with self.subTest(change=change):
                with self.assertRaises(StudioUiReviewInvalid) as cm:
                    check(**change)
                self.assertEqual(cm.exception.code, expected)

    def test_unknown_platform_denied(self):
        with self.assertRaises(StudioUiReviewInvalid) as cm:
            check(tested_platforms=("LINUX_UNSUPPORTED",))
        self.assertEqual(cm.exception.code, "INVALID_TESTED_PLATFORMS")

    def test_unhashable_platform_or_operation_is_rejected_not_crashed(self):
        with self.assertRaises(StudioUiReviewInvalid) as cm:
            check(tested_platforms=(["NOT_A_PLATFORM"],))
        self.assertEqual(cm.exception.code, "INVALID_TESTED_PLATFORMS")
        with self.assertRaises(StudioUiReviewInvalid) as cm:
            check(operation=["EXECUTE_SOMETHING"])
        self.assertEqual(cm.exception.code, "UNSUPPORTED_UI_OPERATION")

    def test_fake_numeric_bool_flag_denied(self):
        with self.assertRaises(StudioUiReviewInvalid) as cm:
            check(real_preview_observed=1)
        self.assertEqual(cm.exception.code, "INVALID_REAL_PREVIEW_OBSERVED")

    def test_no_new_task_or_fabricated_qa_from_result(self):
        result = check()
        self.assertFalse(hasattr(result, "factory_run_id"))
        self.assertFalse(result.may_execute)
        self.assertFalse(result.may_release)
        self.assertEqual(result.task_id, "CANONICAL_TASK")


if __name__ == "__main__":
    unittest.main()
