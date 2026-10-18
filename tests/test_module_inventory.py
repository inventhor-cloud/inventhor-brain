import copy
import unittest

from shared_organizer.inventory import review_module_inventory

REV = "revision-42"
TIME = "2026-10-18T12:00:00+00:00"


def claimed(name, result="PASS", evidence="QA-123"):
    return {"name": name, "result": result, "evidence_ref": evidence}


def catalog():
    return {"schema_version": 1, "system_of_record": "INVENTHOR_MAIN",
            "snapshot_revision": REV, "modules": [
                {"project_id": "MAIN", "module_id": "windows.files",
                 "declared_capabilities": ["FILE_LIST", "FILE_READ"]},
                {"project_id": "MAIN", "module_id": "windows.cleanup",
                 "declared_capabilities": ["CLEANUP_SCAN"]},
                {"project_id": "VICTORIA", "module_id": "windows.files",
                 "declared_capabilities": ["FILE_LIST"]},
            ]}


def observed():
    return {"schema_version": 1, "source": "WINDOWS_OPERATOR",
            "snapshot_revision": REV, "captured_at": TIME, "modules": [
                {"project_id": "MAIN", "module_id": "windows.files",
                 "status": "ACTIVE",
                 "capabilities": [claimed("FILE_LIST"), claimed("FILE_READ")]},
                {"project_id": "MAIN", "module_id": "windows.cleanup",
                 "status": "ACTIVE", "capabilities": [claimed("CLEANUP_SCAN")]},
                {"project_id": "VICTORIA", "module_id": "windows.files",
                 "status": "ACTIVE", "capabilities": [claimed("FILE_LIST")]},
            ]}


def audit(cat=None, obs=None, **kw):
    return review_module_inventory(
        catalog() if cat is None else cat,
        observed() if obs is None else obs,
        host_snapshot_revision=REV,
        host_time_iso=kw.pop("host_time_iso", TIME),
        **kw,
    )


def main_module(report, name="windows.files"):
    return next(m for m in report["modules"]
                if m["project_id"] == "MAIN" and m["module_id"] == name)


class ModuleInventoryReviewTests(unittest.TestCase):
    def test_full_coverage_is_only_unattested_source_report(self):
        r = audit()
        self.assertEqual(r["status"], "SOURCE_COVERAGE_REVIEW")
        self.assertEqual(r["summary"]["reported_complete"], 3)
        self.assertFalse(r["may_install"])
        self.assertFalse(r["may_execute"])
        self.assertFalse(r["may_claim_live_verified"])
        self.assertFalse(r["may_update_registry"])
        self.assertTrue(r["requires_quality_factory_evidence_verification"])
        self.assertEqual(r["evidence_trust"], "UNATTESTED_HOST_REFERENCES")

    def test_partial_coverage_exposes_exact_gap(self):
        o = observed()
        o["modules"][0]["capabilities"].pop()
        r = audit(obs=o)
        row = main_module(r)
        self.assertEqual(row["reported_pass_count"], 1)
        self.assertEqual(row["status"], "PARTIAL_OR_UNVERIFIED")
        self.assertEqual(row["missing_or_unverified"], ["FILE_READ"])

    def test_pass_without_evidence_never_counts(self):
        o = observed()
        o["modules"][0]["capabilities"][0]["evidence_ref"] = None
        row = main_module(audit(obs=o))
        self.assertEqual(row["reported_pass_count"], 1)
        self.assertIn("FILE_LIST", row["missing_or_unverified"])

    def test_false_and_unknown_results_never_count(self):
        o = observed()
        o["modules"][0]["capabilities"] = [
            claimed("FILE_LIST", "FAIL", "QA-FAILED"),
            claimed("FILE_READ", "UNKNOWN", None),
        ]
        row = main_module(audit(obs=o))
        self.assertEqual(row["reported_pass_count"], 0)

    def test_missing_module_is_not_misreported_as_installed(self):
        o = observed()
        o["modules"] = o["modules"][1:]
        r = audit(obs=o)
        row = main_module(r)
        self.assertEqual(row["status"], "NOT_REPORTED")
        self.assertIn("MODULE_OBSERVATION_MISSING",
                      [i["reason"] for i in r["issues"]])

    def test_inactive_module_reports_no_coverage(self):
        o = observed()
        o["modules"][0]["status"] = "INACTIVE"
        row = main_module(audit(obs=o))
        self.assertEqual(row["status"], "INACTIVE")
        self.assertEqual(row["reported_pass_count"], 0)

    def test_unregistered_observation_is_not_auto_onboarded(self):
        o = observed()
        o["modules"].append({"project_id": "MAIN", "module_id": "vendor.unknown",
                             "status": "ACTIVE", "capabilities": [claimed("SECRET")]})
        r = audit(obs=o)
        self.assertEqual(r["summary"]["catalog_modules"], 3)
        self.assertIn("UNREGISTERED_MODULE_OBSERVATION",
                      [i["reason"] for i in r["issues"]])

    def test_unexpected_capability_does_not_inflate_completeness(self):
        o = observed()
        o["modules"][0]["capabilities"].append(claimed("FILE_PURGE"))
        r = audit(obs=o)
        row = main_module(r)
        self.assertEqual(row["status"], "PARTIAL_OR_UNVERIFIED")
        self.assertEqual(row["reported_pass_count"], 2)
        self.assertEqual(row["undeclared_observed"], ["FILE_PURGE"])

    def test_duplicate_live_ownership_is_ambiguous_even_with_pass_evidence(self):
        c = catalog()
        c["modules"][1]["declared_capabilities"].append("FILE_READ")
        o = observed()
        o["modules"][1]["capabilities"].append(claimed("FILE_READ", evidence="QA-OTHER"))
        r = audit(c, o)
        self.assertEqual(r["summary"]["ambiguous_capabilities"], 1)
        self.assertEqual(main_module(r)["status"], "AMBIGUOUS_OWNER")
        self.assertEqual(main_module(r, "windows.cleanup")["status"], "AMBIGUOUS_OWNER")
        self.assertIn("AMBIGUOUS_CAPABILITY_OWNER",
                      [i["reason"] for i in r["issues"]])

    def test_separate_projects_do_not_have_cross_project_conflicts(self):
        r = audit()
        self.assertEqual(r["summary"]["ambiguous_capabilities"], 0)
        v = audit(project_id="VICTORIA")
        self.assertEqual(v["summary"]["catalog_modules"], 1)
        self.assertEqual(v["modules"][0]["project_id"], "VICTORIA")
        self.assertEqual(v["summary"]["reported_complete"], 1)

    def test_stale_observation_rejected(self):
        o = observed()
        o["captured_at"] = "2026-10-18T11:57:00Z"
        self.assertEqual(audit(obs=o)["reason"], "STALE_INVENTORY_OBSERVATION")

    def test_future_observation_rejected(self):
        o = observed()
        o["captured_at"] = "2026-10-18T12:00:07Z"
        self.assertEqual(audit(obs=o)["reason"], "STALE_INVENTORY_OBSERVATION")

    def test_drifted_snapshot_revision_is_blocked(self):
        o = observed()
        o["snapshot_revision"] = "newer-revision"
        self.assertEqual(audit(obs=o)["reason"], "UNPINNED_OR_UNTRUSTED_INVENTORY")

    def test_untrusted_operator_source_rejected(self):
        o = observed()
        o["source"] = "UNVERIFIED_AGENT"
        self.assertEqual(audit(obs=o)["reason"], "UNPINNED_OR_UNTRUSTED_INVENTORY")

    def test_duplicate_module_names_case_insensitive_per_project(self):
        c = catalog()
        c["modules"].append({"project_id": "MAIN", "module_id": "WINDOWS.FILES",
                             "declared_capabilities": ["EXTRA"]})
        self.assertEqual(audit(cat=c)["reason"], "DUPLICATE_CATALOG_MODULE")

    def test_duplicate_operator_rows_are_rejected(self):
        o = observed()
        duplicate = copy.deepcopy(o["modules"][0])
        duplicate["module_id"] = "WINDOWS.FILES"
        o["modules"].append(duplicate)
        self.assertEqual(audit(obs=o)["reason"], "DUPLICATE_OPERATOR_OBSERVATION")

    def test_duplicate_capability_claims_rejected(self):
        o = observed()
        o["modules"][0]["capabilities"].append(claimed("FILE_READ"))
        self.assertEqual(audit(obs=o)["reason"], "INVALID_CAPABILITY_EVIDENCE")

    def test_duplicate_declared_capability_rejected(self):
        c = catalog()
        c["modules"][0]["declared_capabilities"].append("FILE_LIST")
        self.assertEqual(audit(cat=c)["reason"], "INVALID_CATALOG_MODULE")

    def test_invalid_id_and_invalid_evidence_fail_closed(self):
        c = catalog()
        c["modules"][0]["module_id"] = "../secret"
        self.assertEqual(audit(cat=c)["reason"], "INVALID_CATALOG_MODULE")
        o = observed()
        o["modules"][0]["capabilities"][0]["evidence_ref"] = "C:\\token\\secret"
        self.assertEqual(audit(obs=o)["reason"], "INVALID_CAPABILITY_EVIDENCE")

    def test_malformed_states_fail_closed_without_uncaught_exception(self):
        for invalid in ([], {}, None, 1, True):
            with self.subTest(invalid=invalid):
                o = observed()
                o["modules"][0]["status"] = invalid
                self.assertEqual(audit(obs=o)["reason"], "INVALID_OPERATOR_OBSERVATION")
                o = observed()
                o["modules"][0]["capabilities"][0]["result"] = invalid
                self.assertEqual(audit(obs=o)["reason"], "INVALID_CAPABILITY_EVIDENCE")

    def test_no_binary_data_and_no_implicit_writes(self):
        r = audit()
        self.assertTrue(all(set(m) == {
            "project_id", "module_id", "status", "declared_count",
            "reported_pass_count", "missing_or_unverified", "undeclared_observed",
            "ambiguous_capabilities", "coverage_basis",
        } for m in r["modules"]))
        self.assertNotIn("QA-123", str(r))
