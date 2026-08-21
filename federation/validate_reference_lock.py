#!/usr/bin/env python3
"""Validate the central federation catalog against pinned domain references.

This validator is deliberately dependency-free. It checks the local catalog and
the immutable reference record; fetching private domain repositories is kept out
of the central brain and must be performed by the reviewed release workflow.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


SHA40 = re.compile(r"^[0-9a-f]{40}$")
DOMAIN_ENTRY = re.compile(
    r"(?ms)^  ([a-z0-9_-]+):\s*\n"
    r"    repository:\s*([^\n]+)\s*\n"
    r"    manifest:\s*([^\n]+)\s*$"
)


def fail(errors: list[str]) -> int:
    print("STATUS=BF_FEDERATION_REFERENCE_LOCK")
    for error in errors:
        print(f"ERROR={error}")
    return 1


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    catalog_path = root / "federation" / "BRAIN_REPOSITORY_CATALOG.yaml"
    lock_path = root / "federation" / "CROSS_DOMAIN_REFERENCE_LOCK.json"
    errors: list[str] = []

    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - protocol failure path
        return fail([f"LOCK_READ={exc}"])

    catalog_text = catalog_path.read_text(encoding="utf-8")
    catalog_domains = {
        domain: (repository, manifest)
        for domain, repository, manifest in DOMAIN_ENTRY.findall(catalog_text)
    }
    domains = lock.get("domains")
    if not isinstance(domains, list) or not domains:
        errors.append("DOMAINS_MISSING")
        return fail(errors)

    lock_domains: dict[str, dict] = {}
    repositories: set[str] = set()
    commits: set[str] = set()
    for item in domains:
        if not isinstance(item, dict):
            errors.append("DOMAIN_ENTRY_NOT_OBJECT")
            continue
        domain = item.get("domain")
        repository = item.get("repository")
        manifest = item.get("manifest")
        commit_sha = item.get("commit_sha")
        blob_sha = item.get("manifest_blob_sha")
        if not all(isinstance(value, str) for value in (domain, repository, manifest)):
            errors.append(f"DOMAIN_ENTRY_INVALID={domain!r}")
            continue
        if domain in lock_domains:
            errors.append(f"DUPLICATE_DOMAIN={domain}")
        if repository in repositories:
            errors.append(f"DUPLICATE_REPOSITORY={repository}")
        if commit_sha in commits:
            errors.append(f"DUPLICATE_COMMIT={commit_sha}")
        repositories.add(repository)
        commits.add(commit_sha)
        lock_domains[domain] = item
        if not isinstance(commit_sha, str) or not SHA40.fullmatch(commit_sha):
            errors.append(f"INVALID_COMMIT_SHA={domain}")
        if not isinstance(blob_sha, str) or not SHA40.fullmatch(blob_sha):
            errors.append(f"INVALID_MANIFEST_BLOB_SHA={domain}")
        if item.get("reference_mode") != "PINNED_READ_ONLY":
            errors.append(f"REFERENCE_NOT_READ_ONLY={domain}")
        expected = catalog_domains.get(domain)
        if expected is None:
            errors.append(f"DOMAIN_NOT_IN_CATALOG={domain}")
        elif (repository, manifest) != expected:
            errors.append(f"CATALOG_MISMATCH={domain}")

    if set(lock_domains) != set(catalog_domains):
        errors.append("DOMAIN_SET_MISMATCH")
    policy = lock.get("reference_policy", {})
    if policy.get("cross_domain_copy") is not False:
        errors.append("CROSS_DOMAIN_COPY_MUST_BE_FALSE")
    if policy.get("secrets_allowed") is not False:
        errors.append("SECRETS_MUST_BE_FORBIDDEN")
    if policy.get("owner_approval_required_for_promotion") is not True:
        errors.append("OWNER_APPROVAL_REQUIRED")
    if policy.get("rollback_required") is not True:
        errors.append("ROLLBACK_REQUIRED")

    if errors:
        return fail(errors)
    print("STATUS=BS_FEDERATION_REFERENCE_LOCK_VALID")
    print(f"DOMAINS={len(lock_domains)}")
    print("CATALOG_MATCH=YES")
    print("PINNED_READ_ONLY=YES")
    print("CROSS_DOMAIN_COPY=FORBIDDEN")
    print("SECRETS=FORBIDDEN")
    print("ROLLBACK=REQUIRED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
