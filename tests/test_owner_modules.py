import unittest
from shared_organizer.owner_modules import review_owner_module_request

T = "2026-10-18T13:00:00+00:00"


def catalog():
    return {
        "schema_version": 1,
        "system_of_record": "INVENTHOR_MAIN",
        "snapshot_revision": "rev8",
        "captured_at": T,
        "modules": [
            {"project_id": "MAIN", "module_id": "filesystem",
             "declared_capabilities": ["FILE_LIST"]},
            {"project_id": "VIKTORIJA", "module_id": "filesystem",
             "declared_capabilities": ["FILE_LIST"]},
        ],
    }


def request():
    return {
        "schema_version": 1,
        "intent": "OWNER_MODULE_REQUEST",
        "requester_role": "OWNER",
        "project_id": "MAIN",
        "module_id": "my_custom_robot",
        "capabilities": ["ROBOT_CONTROL", "AUTOMATE_DESKTOP"],
        "source_evidence_refs": ["github:mycustommodule"],
    }


def review(r=None, c=None):
    return review_owner_module_request(
        request() if r is None else r,
        catalog() if c is None else c,
        host_snapshot_revision="rev8",
        host_time_iso=T,
    )


class OwnerModuleRequestTests(unittest.TestCase):
    def test_any_owner_chosen_custom_module_without_product_whitelist(self):
        for name in ("self_hosted_ai", "private_hardware", "thirdparty_tool",
                     "owner_designed_game", "inventhor_custom_app"):
            with self.subTest(name=name):
                q = request()
                q["module_id"] = name
                a = review(q)
                self.assertEqual(a["status"], "OWNER_CHOICE_READY_FOR_HOST_VALIDATION")
                self.assertTrue(a["proposed"]["new_module"])
                self.assertEqual(a["supported_product_categories"],
                                 "UNRESTRICTED_BY_THIS_ADVISOR")

    def test_output_never_installs_or_authenticates_owner_from_string(self):
        a = review()
        for key in ("may_install", "may_write", "may_change_security_policy",
                    "may_claim_owner_authenticated", "may_grant_capability"):
            self.assertFalse(a[key])
        self.assertTrue(a["requires_main_authenticated_owner"])
        self.assertTrue(a["requires_package_integrity_and_rollback"])

    def test_request_of_known_module_extends_instead_of_duplicates(self):
        q = request()
        q["module_id"] = "FILESYSTEM"
        q["capabilities"] = ["FILE_LIST", "FILE_WRITE"]
        a = review(q)
        self.assertEqual(a["status"], "REVIEW_EXISTING_MODULE_EXTENSION")
        self.assertFalse(a["proposed"]["new_module"])
        self.assertEqual(a["existing_module"]["module_id"], "filesystem")
        self.assertEqual(a["missing_capability_evidence"], ["FILE_WRITE"])

    def test_owner_capability_overlap_not_hard_banned_but_routing_explicit(self):
        q = request()
        q["capabilities"] = ["FILE_LIST", "FILE_COPY"]
        a = review(q)
        self.assertEqual(a["status"], "OWNER_CHOICE_READY_FOR_HOST_VALIDATION")
        self.assertEqual(len(a["capability_overlaps"]), 1)
        self.assertEqual(a["capability_overlaps"][0]["existing_module_id"], "filesystem")
        self.assertEqual(a["capability_overlaps"][0]["next_action"],
                         "REVIEW_OWNER_PREFERRED_CAPABILITY_ROUTE")

    def test_same_capability_in_unrelated_project_not_a_conflict(self):
        q = request()
        q["project_id"] = "VIKTORIJA"
        q["capabilities"] = ["ROBOT_CONTROL"]
        a = review(q)
        self.assertEqual(a["capability_overlaps"], [])

    def test_no_evidence_yet_is_a_gap_not_a_category_prohibition(self):
        q = request()
        q["source_evidence_refs"] = []
        a = review(q)
        self.assertEqual(a["status"], "OWNER_CHOICE_READY_FOR_HOST_VALIDATION")
        self.assertEqual(a["missing_capability_evidence"],
                         ["AUTOMATE_DESKTOP", "ROBOT_CONTROL"])

    def test_guest_cannot_impersonate_owner(self):
        q = request()
        q["requester_role"] = "GUEST"
        self.assertEqual(review(q)["reason"], "OWNER_INTENT_NOT_IDENTIFIED")

    def test_unversioned_catalog_cannot_grant_decisions(self):
        c = catalog()
        c["snapshot_revision"] = "other"
        self.assertEqual(review(c=c)["reason"], "MAIN_CATALOG_SNAPSHOT_INVALID")

    def test_stale_catalog_is_rejected(self):
        c = catalog()
        c["captured_at"] = "2026-10-18T12:55:00Z"
        self.assertEqual(review(c=c)["reason"], "MAIN_CATALOG_STALE_OR_UNVERSIONED")

    def test_duplicate_canonical_module_is_not_auto_replaced(self):
        c = catalog()
        c["modules"].append({
            "project_id": "MAIN", "module_id": "FILESYSTEM",
            "declared_capabilities": ["FILE_READ"],
        })
        self.assertEqual(review(c=c)["reason"], "DUPLICATE_CANONICAL_MODULE")

    def test_malformed_capabilities_rejected_without_execution(self):
        for value in (["../LEAK"], ["A"], ["FILE_READ", "FILE_READ"], ["FILE_READ", 1], []):
            q = request()
            q["capabilities"] = value
            self.assertEqual(review(q)["reason"], "INVALID_CAPABILITY_DECLARATION")

    def test_path_leak_or_secret_in_evidence_id_not_allowed(self):
        q = request()
        q["source_evidence_refs"] = ["C:\\secret\\key"]
        self.assertEqual(review(q)["reason"], "INVALID_EVIDENCE_REFERENCES")

    def test_invalid_module_id_does_not_create_second_registry(self):
        q = request()
        q["module_id"] = "../../duplicate-registry"
        a = review(q)
        self.assertEqual(a["reason"], "INVALID_PROJECT_OR_MODULE_ID")
        self.assertFalse(a["may_write"])
