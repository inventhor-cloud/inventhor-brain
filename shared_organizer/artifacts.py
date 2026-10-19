"""Read-only artifact catalog preflight for the existing Main/Organizer.

This is NOT an artifact store, installer, downloader, vault or second registry.
Main owns canonical metadata; Windows Operator must independently verify bytes,
signature/trust, target path, permission and a rollback snapshot before deploy.
"""
from __future__ import annotations

import re
from collections.abc import Mapping

HEX64 = re.compile(r"^[0-9a-f]{64}$")
IDENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
VERSION = re.compile(r"^[0-9]+[.][0-9]+[.][0-9]+(?:[-+][A-Za-z0-9.-]+)?$")
KINDS = frozenset(("source_snapshot", "module_package", "app_release", "backup", "test_evidence"))
STORES = frozenset(("github_source", "local_artifact_store", "offline_backup"))
CHANNELS = frozenset(("draft", "tested_source", "release_candidate", "accepted_release", "archived"))


def _id(value: object) -> bool:
    return isinstance(value, str) and IDENT.fullmatch(value) is not None


def _relative(path: object) -> bool:
    """Canonical forward-slash path only: never trust absolute or traversal paths."""
    if not isinstance(path, str) or not path or len(path) > 512:
        return False
    if path.startswith(("/", "~")) or "\\" in path or ":" in path or "\0" in path:
        return False
    pieces = path.split("/")
    return all(_id(part) and part not in (".", "..") and not part.startswith(".")
               for part in pieces)


def review_artifact_catalog(catalog: object, *, known_project_ids: set[str],
                            known_module_ids: set[str]) -> dict:
    """Audit references only; success is never release/deployment permission."""
    def response(status: str, issues: list[dict]) -> dict:
        return {"status": status, "issues": issues,
                "may_install": False, "may_delete": False,
                "may_claim_bytes_verified": False,
                "requires_host_file_hash": True,
                "requires_main_approval": True,
                "source_only": True}

    if (not isinstance(catalog, Mapping) or type(catalog.get("schema_version")) is not int
        or catalog["schema_version"] != 1
        or catalog.get("system_of_record") != "INVENTHOR_MAIN"
        or not isinstance(catalog.get("artifacts"), list)
        or len(catalog["artifacts"]) > 4096
        or not isinstance(known_project_ids, set)
        or not isinstance(known_module_ids, set)):
        return response("INVALID_CATALOG", [{"reason": "CATALOG_SCHEMA_REJECTED"}])

    # Every version+kind+module+project is one canonical artifact identity.
    identities: dict[tuple[str, str, str, str], tuple[str, str]] = {}
    hashes: dict[tuple[str, str], tuple[str, str]] = {}
    issues: list[dict] = []
    for index, item in enumerate(catalog["artifacts"]):
        if not isinstance(item, Mapping):
            issues.append({"index": index, "reason": "INVALID_ENTRY"})
            continue
        aid = item.get("artifact_id")
        project = item.get("project_id")
        module = item.get("module_id")
        version = item.get("version")
        kind = item.get("kind")
        store = item.get("store")
        path = item.get("relative_path")
        digest = item.get("sha256")
        channel = item.get("channel")
        if not all(_id(v) for v in (aid, project, module)):
            issues.append({"index": index, "reason": "INVALID_IDENTITY"})
            continue
        if project not in known_project_ids or module not in known_module_ids:
            issues.append({"index": index, "reason": "UNREGISTERED_OWNER"})
            continue
        if not isinstance(version, str) or VERSION.fullmatch(version) is None:
            issues.append({"index": index, "reason": "INVALID_VERSION"})
            continue
        if (not isinstance(kind, str) or not isinstance(store, str) or
            not isinstance(channel, str) or kind not in KINDS or
            store not in STORES or channel not in CHANNELS):
            issues.append({"index": index, "reason": "INVALID_KIND_STORE_OR_CHANNEL"})
            continue
        if not _relative(path):
            issues.append({"index": index, "reason": "UNSAFE_LOCATION"})
            continue
        if not isinstance(digest, str) or HEX64.fullmatch(digest) is None:
            issues.append({"index": index, "reason": "MISSING_CONTENT_DIGEST"})
            continue
        if item.get("contains_secrets") is not False:
            issues.append({"index": index, "reason": "SECRET_STATUS_UNVERIFIED"})
            continue
        if store == "github_source" and kind != "source_snapshot":
            issues.append({"index": index, "reason": "INVALID_GITHUB_ARTIFACT_KIND"})
            continue
        if kind == "backup" and store == "github_source":
            issues.append({"index": index, "reason": "PRIVATE_BACKUP_NOT_FOR_SOURCE_REPO"})
            continue

        key = (project, module, kind, version)
        value = (aid, digest)
        if key in identities and identities[key] != value:
            issues.append({"index": index, "reason": "CONFLICTING_ARTIFACT_REVISION"})
            continue
        if key in identities:
            issues.append({"index": index, "reason": "DUPLICATE_ARTIFACT_ENTRY"})
            continue
        identities[key] = value
        if (project, aid) in hashes:
            issues.append({"index": index, "reason": "ARTIFACT_ID_REUSED"})
            continue
        hashes[(project, aid)] = (version, digest)

        if channel == "accepted_release":
            # Presence of a review reference is only source metadata.
            # Never trust it as evidence of a real signed/verified release.
            if not _id(item.get("release_review_ref")):
                issues.append({"index": index, "reason": "RELEASE_REVIEW_REFERENCE_MISSING"})
                continue
            if kind not in ("module_package", "app_release"):
                issues.append({"index": index, "reason": "NONINSTALLABLE_KIND_MARKED_RELEASE"})
                continue

    return response("CATALOG_VALID_SOURCE_ONLY" if not issues else "CATALOG_REVIEW_REQUIRED",
                    issues)
