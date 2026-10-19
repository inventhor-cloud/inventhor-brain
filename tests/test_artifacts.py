import unittest
from shared_organizer.artifacts import review_artifact_catalog


class ArtifactCatalogContractTests(unittest.TestCase):
    def item(self, **changes):
        data = dict(
            artifact_id="pkg-1",
            project_id="INVENTHOR_MAIN",
            module_id="language_brain",
            version="1.2.0",
            kind="module_package",
            store="local_artifact_store",
            relative_path="packages/language_brain/1.2.0/pkg-1.zip",
            sha256="a" * 64,
            channel="release_candidate",
            contains_secrets=False,
        )
        data.update(changes)
        return data

    def check(self, items):
        return review_artifact_catalog(
            dict(schema_version=1, system_of_record="INVENTHOR_MAIN",
                 artifacts=items),
            known_project_ids={"INVENTHOR_MAIN"},
            known_module_ids={"language_brain"})

    def test_empty_registry_is_valid_but_no_binary_verified(self):
        r = self.check([])
        self.assertEqual(r["status"], "CATALOG_VALID_SOURCE_ONLY")
        self.assertFalse(r["may_claim_bytes_verified"])
        self.assertFalse(r["may_install"])

    def test_one_package(self):
        self.assertEqual(self.check([self.item()])["issues"], [])

    def test_relative_windows_safe_paths_only(self):
        for bad in ("D:/INVENTHOR/a.zip", "C:\\Users\\file.zip", "/root/file",
                    "../secret", "packages/../../secret.zip", "packages//a",
                    "packages/./a", "\\\\server\\share", "src/.git/config",
                    "~/private"):
            with self.subTest(bad=bad):
                r = self.check([self.item(relative_path=bad)])
                self.assertEqual(r["issues"][0]["reason"], "UNSAFE_LOCATION")

    def test_unknown_project_and_module(self):
        for bad in (self.item(project_id="OTHER"), self.item(module_id="unknown")):
            self.assertEqual(self.check([bad])["issues"][0]["reason"],
                             "UNREGISTERED_OWNER")

    def test_bad_hash_and_version(self):
        self.assertEqual(self.check([self.item(sha256="unknown")])["issues"][0]["reason"],
                         "MISSING_CONTENT_DIGEST")
        self.assertEqual(self.check([self.item(version="../x")])["issues"][0]["reason"],
                         "INVALID_VERSION")

    def test_no_secrets_verified_flag(self):
        for status in (True, None, "false"):
            self.assertEqual(
                self.check([self.item(contains_secrets=status)])["issues"][0]["reason"],
                "SECRET_STATUS_UNVERIFIED")

    def test_duplicate_package_identity_is_blocked(self):
        package = self.item()
        r = self.check([package, self.item(artifact_id="pkg-2", sha256="b" * 64)])
        self.assertEqual(r["issues"][0]["reason"], "CONFLICTING_ARTIFACT_REVISION")

    def test_exact_duplicate_is_rejected(self):
        package = self.item()
        r = self.check([package, dict(package)])
        self.assertEqual(r["issues"][0]["reason"], "DUPLICATE_ARTIFACT_ENTRY")

    def test_same_id_different_version_is_rejected(self):
        r = self.check([self.item(),
                        self.item(version="1.3.0", relative_path="packages/language_brain/1.3.0/pkg-1.zip")])
        self.assertEqual(r["issues"][0]["reason"], "ARTIFACT_ID_REUSED")

    def test_source_snapshot_never_treated_as_installable(self):
        item = self.item(kind="source_snapshot", store="github_source",
                         relative_path="inventhor-brain-language/commits/sha256.tar",
                         channel="tested_source")
        r = self.check([item])
        self.assertEqual(r["status"], "CATALOG_VALID_SOURCE_ONLY")
        self.assertFalse(r["may_install"])

    def test_github_not_binary_backups(self):
        item = self.item(kind="backup", store="github_source")
        self.assertEqual(self.check([item])["issues"][0]["reason"],
                         "INVALID_GITHUB_ARTIFACT_KIND")

    def test_accepted_release_only_with_metadata_review_and_installable_kind(self):
        rejected = self.check([self.item(channel="accepted_release")])
        self.assertEqual(rejected["issues"][0]["reason"], "RELEASE_REVIEW_REFERENCE_MISSING")
        approved_label = self.check([self.item(channel="accepted_release",
                                               release_review_ref="review-101")])
        self.assertEqual(approved_label["status"], "CATALOG_VALID_SOURCE_ONLY")
        self.assertFalse(approved_label["may_install"])
        self.assertFalse(approved_label["may_claim_bytes_verified"])

    def test_release_review_label_does_not_promote_backup(self):
        b = self.item(kind="backup", channel="accepted_release",
                      release_review_ref="review-101", store="offline_backup")
        self.assertEqual(self.check([b])["issues"][0]["reason"],
                         "NONINSTALLABLE_KIND_MARKED_RELEASE")

    def test_malformed_collection(self):
        r = review_artifact_catalog({"schema_version": 1,
                                     "system_of_record": "INVENTHOR_MAIN",
                                     "artifacts": "not-a-list"},
                                    known_project_ids=set(), known_module_ids=set())
        self.assertEqual(r["status"], "INVALID_CATALOG")
