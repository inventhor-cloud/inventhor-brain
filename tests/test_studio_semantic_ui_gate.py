"""Source-only Brain→existing Studio semantic UI review regression tests."""
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from continuity.studio_semantic_ui_gate import (
    SemanticUiEditSnapshot, StudioUiReviewInvalid,
    StudioOperationClaim, StudioResourceSnapshot,
    review_studio_semantic_ui_edit, review_studio_operation_safety,
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


def check(*, approved_operation="UI_SET_CONSTRAINT",
          approved_target="panel.right.inspector",
          approved_ids=("panel.right.inspector",), **changes):
    return review_studio_semantic_ui_edit(
        replace(base(), **changes),
        now=NOW,
        expected_task_id="CANONICAL_TASK",
        expected_project_id="APP_DESIGN",
        expected_document_id="STUDIO_DOCUMENT",
        expected_native_revision=20,
        approved_operation=approved_operation,
        approved_semantic_target_id=approved_target,
        approved_touched_ids=approved_ids,
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

    def test_untrusted_operation_cannot_override_approved_ui_intent(self):
        with self.assertRaises(StudioUiReviewInvalid) as cm:
            check(operation="UI_HIDE")
        self.assertEqual(cm.exception.code, "UI_OPERATION_SCOPE_MISMATCH")

    def test_untrusted_semantic_target_cannot_swap_approved_panel(self):
        with self.assertRaises(StudioUiReviewInvalid) as cm:
            check(target_semantic_id="toolbar.global.send",
                  intended_touched_ids=("toolbar.global.send",),
                  observed_touched_ids=("toolbar.global.send",))
        self.assertEqual(cm.exception.code, "SEMANTIC_TARGET_SCOPE_MISMATCH")

    def test_self_consistent_but_unapproved_additional_change_is_blocked(self):
        result = check(intended_touched_ids=(
            "panel.right.inspector", "toolbar.global.send"),
            observed_touched_ids=(
                "panel.right.inspector", "toolbar.global.send"))
        self.assertEqual(result.disposition, "BLOCKED")
        self.assertIn("UNAPPROVED_INTENDED_COMPONENT", result.blockers)
        self.assertIn("UNAPPROVED_OBSERVED_COMPONENT", result.blockers)
        self.assertFalse(result.may_execute)

    def test_approved_subset_with_extra_component_is_permitted_for_review(self):
        result = check(approved_ids=(
            "panel.right.inspector", "toolbar.global.send"))
        self.assertEqual(result.disposition, "NATIVE_STUDIO_REVIEW_REQUIRED")
        self.assertFalse(result.native_evidence_authenticated)

    def test_missing_or_invalid_approved_scope_fails_closed(self):
        for kwargs, code in (
            ({"approved_operation": "EXECUTE_POWERSHELL"},
             "INVALID_APPROVED_OPERATION"),
            ({"approved_target": "panel.unknown"},
             "APPROVED_TARGET_NOT_IN_SCOPE"),
            ({"approved_ids": ("panel.right.inspector",
                                "panel.right.inspector")},
             "DUPLICATE_APPROVED_TARGETS"),
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(StudioUiReviewInvalid) as cm:
                    check(**kwargs)
                self.assertEqual(cm.exception.code, code)

    def test_owner_approved_mobile_only_task_is_not_forced_to_windows(self):
        result = check(expected_platforms=("ANDROID_PHONE",),
                       tested_platforms=("ANDROID_PHONE",))
        self.assertEqual(result.disposition, "NATIVE_STUDIO_REVIEW_REQUIRED")
        self.assertFalse(result.may_execute)

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



def operation_claim(**overrides):
    fields = dict(
        task_id="TASK_A", project_id="PROJECT_A",
        design_document_id="DOC_A", base_design_revision=7,
        actor_session_id="GPT_SESSION_A", lease_epoch=3,
        lease_expires_at=NOW + timedelta(minutes=5),
        component_ids=("panel.right.inspector",),
        resource_keys=("workspace:A",),
    )
    fields.update(overrides)
    return StudioOperationClaim(**fields)


def capacity(**overrides):
    fields = dict(
        measured_at=NOW,
        available_memory_mb=8192,
        reserve_memory_mb=1024,
        expected_extra_memory_mb=512,
        occupied_build_slots=0,
        safe_build_slots=2,
        needs_build_slot=False,
    )
    fields.update(overrides)
    return StudioResourceSnapshot(**fields)


def safety(active=(), request=None, load=None):
    return review_studio_operation_safety(
        request if request is not None else operation_claim(),
        native_active_claims=active,
        native_load=load if load is not None else capacity(),
        now=NOW,
    )


class StudioOperationConflictTests(unittest.TestCase):
    def test_independent_task_and_document_do_not_block_each_other(self):
        x = safety(active=(operation_claim(
            task_id="TASK_B", design_document_id="DOC_B",
            component_ids=("panel.left.navigation",),
            resource_keys=("workspace:B",)),))
        self.assertEqual(x.disposition, "NATIVE_PREFLIGHT_REQUIRED")
        self.assertEqual(x.reasons, ())
        self.assertFalse(x.can_dispatch)
        self.assertFalse(x.lease_authenticated)

    def test_same_document_disjoint_panels_still_rebase_atomically(self):
        x = safety(active=(operation_claim(
            task_id="TASK_B", actor_session_id="CODEX_SESSION_B",
            component_ids=("panel.left.navigation",),
            resource_keys=("workspace:B",)),))
        self.assertEqual(x.disposition, "SERIALIZE_AND_REBASE")
        self.assertIn("SAME_DOCUMENT_REBASE_REQUIRED", x.reasons)
        self.assertNotIn("OVERLAPPING_COMPONENT_EDIT", x.reasons)

    def test_same_component_and_resource_conflicts(self):
        x = safety(active=(operation_claim(
            task_id="TASK_B", actor_session_id="CODEX_SESSION_B"),))
        self.assertIn("OVERLAPPING_COMPONENT_EDIT", x.reasons)
        self.assertIn("RESOURCE_LOCK_COLLISION", x.reasons)
        self.assertEqual(x.disposition, "SERIALIZE_AND_REBASE")

    def test_shared_resource_across_different_documents_serialized(self):
        x = safety(active=(operation_claim(
            task_id="TASK_B", project_id="PROJECT_B",
            design_document_id="DOC_B"),))
        self.assertIn("RESOURCE_LOCK_COLLISION", x.reasons)
        self.assertNotIn("SAME_DOCUMENT_REBASE_REQUIRED", x.reasons)

    def test_same_task_epoch_cannot_be_replayed(self):
        x = safety(active=(operation_claim(),))
        self.assertEqual(x.disposition, "RECONCILE_BEFORE_RETRY")
        self.assertIn("DUPLICATE_TASK_EPOCH", x.reasons)
        self.assertFalse(x.can_dispatch)

    def test_expired_foreign_lease_requires_event_reconciliation(self):
        x = safety(active=(operation_claim(
            task_id="TASK_B", lease_expires_at=NOW - timedelta(seconds=1)),))
        self.assertEqual(x.disposition, "RECONCILE_BEFORE_RETRY")
        self.assertIn("EXPIRED_ACTIVE_LEASE_RECONCILIATION_REQUIRED", x.reasons)

    def test_expired_intent_is_not_valid_new_execution(self):
        x = safety(request=operation_claim(
            lease_expires_at=NOW - timedelta(seconds=1)))
        self.assertEqual(x.disposition, "RECONCILE_BEFORE_RETRY")

    def test_low_memory_defers_task_but_does_not_reject_goal(self):
        x = safety(load=capacity(available_memory_mb=1400,
                                 expected_extra_memory_mb=512))
        self.assertEqual(x.disposition, "DEFER_FOR_CAPACITY")
        self.assertIn("INSUFFICIENT_MEMORY_HEADROOM", x.reasons)
        self.assertFalse(x.can_dispatch)

    def test_busy_build_limit_defers_without_launching_parallel_build(self):
        x = safety(load=capacity(needs_build_slot=True,
                                 occupied_build_slots=2))
        self.assertEqual(x.disposition, "DEFER_FOR_CAPACITY")
        self.assertIn("BUILD_CAPACITY_BUSY", x.reasons)

    def test_fresh_memory_headroom_and_build_slot_does_not_block(self):
        x = safety(load=capacity(needs_build_slot=True,
                                 occupied_build_slots=1))
        self.assertEqual(x.disposition, "NATIVE_PREFLIGHT_REQUIRED")

    def test_stale_metrics_are_never_accepted_as_free_capacity(self):
        x = safety(load=capacity(measured_at=NOW - timedelta(seconds=31)))
        self.assertEqual(x.disposition, "DEFER_FOR_CAPACITY")
        self.assertIn("RESOURCE_MEASUREMENT_STALE", x.reasons)

    def test_incomplete_claim_window_needs_native_reconciliation(self):
        claims = tuple(operation_claim(
            task_id="TASK_B" + str(i),
            design_document_id="DOC_B" + str(i),
            resource_keys=("workspace:B" + str(i),))
            for i in range(257))
        x = safety(active=claims)
        self.assertEqual(x.disposition, "RECONCILE_BEFORE_RETRY")
        self.assertIn("ACTIVE_CLAIM_WINDOW_INCOMPLETE", x.reasons)

    def test_non_sense_load_and_claim_are_rejected_without_dispatch(self):
        for request, load, active in (
            (operation_claim(lease_epoch=True), capacity(), ()),
            (operation_claim(), capacity(available_memory_mb=-1), ()),
            (operation_claim(), capacity(needs_build_slot=1), ()),
            (operation_claim(), capacity(), ["not-native-claim"]),
            (operation_claim(resource_keys=("workspace:A", "workspace:A")),
             capacity(), ()),
        ):
            with self.subTest(request=request, load=load):
                with self.assertRaises(StudioUiReviewInvalid):
                    safety(request=request, load=load, active=active)


if __name__ == "__main__":
    unittest.main()
