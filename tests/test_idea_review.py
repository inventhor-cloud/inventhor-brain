"""Project-scoped source advisor: no duplicate IDEA, no unauthorized capture."""
import unittest

from shared_organizer.idea_review import advise_idea_intake

NOW = "2026-10-19T01:45:00+02:00"
PROJECTS = [{"project_id": "MAIN"}, {"project_id": "VIKTORIJA"}]
TITLE = "Akıllı proje hafızası fikir yakalama"


def work(title=TITLE, state="TODO", project_id="MAIN", task_id="TASK1"):
    return {"project_id": project_id, "task_id": task_id,
            "title": title, "state": state}


def idea(title=TITLE, project_id="MAIN", idea_id="IDEA1"):
    return {"project_id": project_id, "idea_id": idea_id,
            "title": title, "state": "IDEA"}


def queue(items=(), revision="rev2", when=NOW):
    return {"schema_version": 1, "system_of_record": "INVENTHOR_MAIN",
            "snapshot_revision": revision, "captured_at": when,
            "work_items": list(items)}


def review(items=(), ideas=(), title=TITLE, project_id="MAIN", **kwargs):
    return advise_idea_intake(
        kwargs.pop("projects", PROJECTS),
        kwargs.pop("queue_data", queue(items)),
        kwargs.pop("idea_index", list(ideas)),
        kwargs.pop("proposal", {"project_id": project_id, "title": title}),
        host_snapshot_revision=kwargs.pop("revision", "rev2"),
        host_time_iso=kwargs.pop("time", NOW),
    )


class IdeaIntakeTests(unittest.TestCase):
    def test_no_duplicate_creates_only_advisory_host_request(self):
        result = review()
        self.assertEqual(result["status"], "HOST_IDEA_CAPTURE_REVIEW_REQUIRED")
        for key in ("may_create_idea", "may_update_idea", "may_promote_todo",
                    "may_take_ownership", "may_execute"):
            self.assertFalse(result[key])
        self.assertTrue(result["requires_host_atomic_review"])

    def test_existing_idea_case_and_whitespace_deduped(self):
        r = review(ideas=[idea()], title="  AKILLI   PROJE hafızası FİKİR YAKALAMA ")
        self.assertEqual(r["status"], "EXISTING_IDEA_REVIEW")
        self.assertEqual(r["matches"][0]["id"], "IDEA1")

    def test_existing_todo_is_not_second_idea(self):
        r = review(items=[work()])
        self.assertEqual(r["status"], "EXISTING_WORK_REVIEW")
        self.assertEqual(r["matches"][0]["id"], "TASK1")

    def test_existing_done_never_replayed(self):
        self.assertEqual(review(items=[work(state="DONE")])["status"],
                         "HISTORY_REVIEW_NO_REPLAY")

    def test_existing_archived_idea_requires_history_review(self):
        prior = {**idea(), "state": "ARCHIVED"}
        self.assertEqual(review(ideas=[prior])["status"],
                         "HISTORY_REVIEW_NO_REPLAY")

    def test_similar_title_requests_review_not_auto_merge(self):
        r = review(items=[work(title="Akıllı proje hafızası otomatik fikir yakalama")])
        self.assertEqual(r["status"], "SIMILAR_PURPOSE_REVIEW")
        self.assertFalse(r["may_update_idea"])

    def test_unrelated_title_does_not_fabricate_semantic_match(self):
        r = review(items=[work(title="Takvim günlük plan görüntüsü")])
        self.assertEqual(r["status"], "HOST_IDEA_CAPTURE_REVIEW_REQUIRED")

    def test_other_projects_do_not_expose_identifiers_or_merge(self):
        r = review(items=[work(project_id="VIKTORIJA", task_id="PRIVATE_TASK")],
                   ideas=[idea(project_id="VIKTORIJA", idea_id="PRIVATE_IDEA")])
        self.assertEqual(r["status"], "HOST_IDEA_CAPTURE_REVIEW_REQUIRED")
        self.assertNotIn("PRIVATE_TASK", str(r))
        self.assertNotIn("PRIVATE_IDEA", str(r))

    def test_explicit_project_required_and_unknown_denied(self):
        self.assertEqual(review(project_id=None)["status"],
                         "EXPLICIT_PROJECT_ROUTING_REQUIRED")
        self.assertEqual(review(project_id="FANTASY")["status"],
                         "PROJECT_NOT_REGISTERED")

    def test_stale_and_future_host_views_denied(self):
        self.assertEqual(review(time="2026-10-19T01:48:00+02:00")["status"],
                         "STALE_SNAPSHOT_REQUIRES_MAIN_REFRESH")
        self.assertEqual(review(time="2026-10-19T01:44:00+02:00")["status"],
                         "STALE_SNAPSHOT_REQUIRES_MAIN_REFRESH")

    def test_revision_mismatch_and_no_timestamp_denied(self):
        self.assertEqual(review(revision="wrong")["status"],
                         "UNVERSIONED_OR_MISMATCHED_SNAPSHOT")
        self.assertEqual(review(queue_data=queue(when=""))["status"],
                         "UNVERSIONED_OR_MISMATCHED_SNAPSHOT")

    def test_untrusted_queue_never_authenticates_by_title(self):
        q = queue([work()])
        q["system_of_record"] = "OTHER_LEDGER"
        self.assertEqual(review(queue_data=q)["status"],
                         "UNTRUSTED_CANONICAL_QUEUE")

    def test_no_idea_index_or_invalid_idea_index_denied(self):
        self.assertEqual(review(idea_index=None)["status"], "INVALID_INPUT")
        self.assertEqual(review(idea_index=[{"project_id": "MAIN", "idea_id": "I1"}])["status"],
                         "INCOMPLETE_CANONICAL_INDEX")

    def test_duplicate_canonical_idea_ids_blocked(self):
        self.assertEqual(review(ideas=[idea(), idea()])["status"],
                         "AMBIGUOUS_CANONICAL_ID")

    def test_duplicate_titles_block_automatic_capture(self):
        r = review(ideas=[idea(idea_id="I1"), idea(idea_id="I2")])
        self.assertEqual(r["status"], "AMBIGUOUS_DUPLICATE_REVIEW")
        self.assertEqual(len(r["matches"]), 2)

    def test_invalid_project_registry_denied(self):
        self.assertEqual(review(projects=PROJECTS + [PROJECTS[0]])["status"],
                         "DUPLICATE_PROJECT_REGISTRY")

    def test_overlong_and_control_character_titles_denied(self):
        self.assertEqual(review(title="x" * 201)["status"], "INVALID_IDEA_TITLE")
        self.assertEqual(review(title="Fikir\nKopya")["status"], "INVALID_IDEA_TITLE")

    def test_untrusted_permission_flags_do_not_grant_capture(self):
        p = {"project_id": "MAIN", "title": TITLE,
             "may_execute": True, "owner_approved": True,
             "auto_promote": True}
        r = review(proposal=p)
        self.assertFalse(r["may_execute"])
        self.assertFalse(r["may_create_idea"])
        self.assertFalse(r["may_promote_todo"])

    def test_bounded_index_denies_overlarge_idea_pool(self):
        records = [idea(title="Yeni fikir " + str(i), idea_id="I" + str(i))
                   for i in range(513)]
        self.assertEqual(review(ideas=records)["status"], "BOUNDED_INDEX_REQUIRED")


if __name__ == "__main__":
    unittest.main()
