import unittest
from dataclasses import replace

from shared_organizer.conflict_prevention import (
    FileVersion, ReconciliationReview, classify_reconciliation,
)

BASE = "1" * 40
PR = "2" * 40
A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64


class ConflictPreventionTests(unittest.TestCase):
    def item(self, path="windows/core/TaskEngine.cs", base=A,
             local=A, pr=B, now=A):
        return FileVersion(path, base, local, pr, now)

    def review(self, items=None, **changes):
        versions = (self.item(),) if items is None else tuple(items)
        kwargs = dict(project_id="INVENTHOR_MAIN", task_id="OP_FIX",
                      expected_base_commit=BASE, expected_pr_commit=PR,
                      observed_pr_commit=PR,
                      expected_file_count=len(versions),
                      file_versions=versions)
        kwargs.update(changes)
        return ReconciliationReview(**kwargs)

    def test_pr_only_candidate_is_not_install_permission(self):
        r = classify_reconciliation(self.review())
        self.assertEqual(r.status, "SOURCE_REVIEW_READY")
        self.assertEqual(r.files[0].classification, "PR_ONLY_CHANGE")
        self.assertEqual(r.files[0].next_action, "REVIEW_PR_CANDIDATE")
        self.assertFalse(r.may_change_files)
        self.assertFalse(r.may_merge_pr)
        self.assertFalse(r.may_install)
        self.assertFalse(r.may_take_ownership)
        self.assertTrue(r.requires_host_authenticated_lease)

    def test_three_way_all_distinct_refuses_auto_merge(self):
        r = classify_reconciliation(self.review([self.item(
            base=A, local=B, pr=C, now=B)]))
        self.assertEqual(r.status, "HOLD_DUAL_CHANGE")
        self.assertEqual(r.files[0].classification, "DUAL_CHANGE_REVIEW")
        self.assertEqual(r.files[0].next_action, "ISOLATED_SEMANTIC_REVIEW")

    def test_local_only_change_is_preserved(self):
        r = classify_reconciliation(self.review([self.item(
            base=A, local=B, pr=A, now=B)]))
        self.assertEqual(r.files[0].next_action, "PRESERVE_LOCAL")

    def test_already_integrated_files_not_rewritten(self):
        r = classify_reconciliation(self.review([self.item(
            base=A, local=B, pr=B, now=B)]))
        self.assertEqual(r.files[0].next_action, "SKIP")

    def test_absent_and_added_file_handling(self):
        versions = [
            self.item("path/absent.cs", None, None, None, None),
            self.item("path/pr_added.cs", None, None, B, None),
            self.item("path/local_added.cs", None, B, None, B),
            self.item("path/both_added.cs", None, B, C, B),
        ]
        r = classify_reconciliation(self.review(versions))
        self.assertEqual(r.status, "HOLD_DUAL_CHANGE")
        self.assertEqual([f.classification for f in r.files], [
            "ABSENT_ALL", "PR_ONLY_CHANGE", "LOCAL_ONLY_CHANGE",
            "DUAL_CHANGE_REVIEW"])

    def test_changed_pr_head_requires_new_snapshot(self):
        r = classify_reconciliation(self.review(observed_pr_commit="3" * 40))
        self.assertEqual(r.reason, "PR_HEAD_DRIFT_RESTART_READ_ONLY_INVENTORY")
        self.assertEqual(r.reviewed_count, 0)

    def test_short_commit_not_pinned(self):
        r = classify_reconciliation(self.review(expected_base_commit="123abcd"))
        self.assertEqual(r.reason, "COMMIT_SHA_NOT_PINNED")

    def test_rehash_before_edit_catches_changed_local_file(self):
        r = classify_reconciliation(self.review([self.item(
            base=A, local=A, pr=B, now=C)]))
        self.assertEqual(r.reason, "LOCAL_FILE_CHANGED_AFTER_INVENTORY")
        self.assertEqual(r.status, "HOLD_LOCAL_DRIFT")

    def test_exact_same_failed_attempt_stops_retry_loop(self):
        r = classify_reconciliation(self.review(
            prior_failure_fingerprint=A, current_failure_fingerprint=A))
        self.assertEqual(r.status, "HOLD_REPEATED_FAILURE")
        self.assertFalse(r.may_take_ownership)
        r = classify_reconciliation(self.review(
            prior_failure_fingerprint=A, current_failure_fingerprint=B))
        self.assertEqual(r.status, "SOURCE_REVIEW_READY")

    def test_missing_one_of_sixteen_is_not_partial_success(self):
        r = classify_reconciliation(self.review(expected_file_count=16))
        self.assertEqual(r.reason, "INCOMPLETE_OR_OVERLARGE_INVENTORY")
        self.assertEqual(r.reviewed_count, 0)

    def test_task_identity_and_duplicate_paths_blocked(self):
        r = classify_reconciliation(self.review(project_id=""))
        self.assertEqual(r.reason, "INVALID_TASK_IDENTITY")
        r = classify_reconciliation(self.review([
            self.item("WINDOWS/CORE/a.cs"),
            self.item("windows/core/A.cs"),
        ]))
        self.assertEqual(r.reason, "DUPLICATE_WINDOWS_PATH")

    def test_traversal_rejected_no_scope_bypass(self):
        for path in ("../password.txt", "/absolute/path", "windows/../key",
                     "C:/other-path", "foo\\bar", "windows/core/file."):
            with self.subTest(path=path):
                r = classify_reconciliation(self.review([self.item(path)]))
                self.assertEqual(r.reason, "INVALID_SCOPE_PATH")

    def test_invalid_digest_cannot_be_treated_as_missing(self):
        r = classify_reconciliation(self.review([self.item(
            base="not-a-hash")]))
        self.assertEqual(r.reason, "INVALID_FILE_DIGEST")

    def test_invalid_counts_or_types_blocked(self):
        for count in (0, True, 257, 3):
            with self.subTest(count=count):
                r = classify_reconciliation(self.review(expected_file_count=count))
                self.assertEqual(r.reason, "INCOMPLETE_OR_OVERLARGE_INVENTORY")

    def test_all_returns_are_advisory_and_nonexecuting(self):
        rows = [
            self.item("x/a.cs", A, A, B, A),
            self.item("x/b.cs", A, B, C, B),
        ]
        r = classify_reconciliation(self.review(rows))
        self.assertTrue(r.source_only)
        self.assertFalse(r.may_change_files)
        self.assertFalse(r.may_install)
        self.assertFalse(r.may_merge_pr)
