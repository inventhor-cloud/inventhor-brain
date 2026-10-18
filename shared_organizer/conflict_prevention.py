"""Deterministic, no-I/O conflict prevention advisory for Main Organizer.

No Git fetch, local file read, lease acquisition, write, retry or install.
The trusted Main host must supply hashes from independently verified snapshots.
This cannot authenticate that those hashes correspond to the owner's PC.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from .board import _valid_scope

_SHA = re.compile(r"[0-9a-fA-F]{64}\Z")
_COMMIT = re.compile(r"[0-9a-fA-F]{40}\Z")
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")


@dataclass(frozen=True)
class FileVersion:
    path: str
    base_sha256: str | None
    local_sha256: str | None
    pr_sha256: str | None
    local_sha256_rechecked: str | None


@dataclass(frozen=True)
class ReconciliationReview:
    project_id: str
    task_id: str
    expected_base_commit: str
    expected_pr_commit: str
    observed_pr_commit: str
    expected_file_count: int
    file_versions: tuple[FileVersion, ...]
    prior_failure_fingerprint: str | None = None
    current_failure_fingerprint: str | None = None


@dataclass(frozen=True)
class FileAdvice:
    path: str
    classification: str
    next_action: str


@dataclass(frozen=True)
class ReviewAdvice:
    status: str
    reason: str
    files: tuple[FileAdvice, ...] = ()
    reviewed_count: int = 0
    may_change_files: bool = False
    may_take_ownership: bool = False
    may_merge_pr: bool = False
    may_install: bool = False
    requires_host_authenticated_lease: bool = True
    source_only: bool = True


def classify_reconciliation(review: ReconciliationReview) -> ReviewAdvice:
    """Fail closed on branch drift, unrecognized files and repeated failures.

    Returned advice is a human/host review plan; NEVER approval to write.
    """
    def stop(status: str, reason: str, files: tuple[FileAdvice, ...] = ()) -> ReviewAdvice:
        return ReviewAdvice(status=status, reason=reason, files=files, reviewed_count=len(files))

    if not isinstance(review, ReconciliationReview):
        return stop("BLOCKED", "INVALID_REVIEW")
    if any(not isinstance(v, str) or not _ID.fullmatch(v)
           for v in (review.project_id, review.task_id)):
        return stop("BLOCKED", "INVALID_TASK_IDENTITY")
    commits = (
        review.expected_base_commit, review.expected_pr_commit,
        review.observed_pr_commit
    )
    if any(not isinstance(c, str) or not _COMMIT.fullmatch(c) for c in commits):
        return stop("BLOCKED", "COMMIT_SHA_NOT_PINNED")
    if review.expected_pr_commit.casefold() != review.observed_pr_commit.casefold():
        return stop("BLOCKED", "PR_HEAD_DRIFT_RESTART_READ_ONLY_INVENTORY")
    if review.expected_base_commit.casefold() == review.expected_pr_commit.casefold():
        return stop("BLOCKED", "BASE_EQUALS_PR_CHECK_REVISION")
    if (type(review.expected_file_count) is not int
        or not 0 < review.expected_file_count <= 256
        or not isinstance(review.file_versions, (tuple, list))
        or len(review.file_versions) != review.expected_file_count):
        return stop("BLOCKED", "INCOMPLETE_OR_OVERLARGE_INVENTORY")
    failures = (review.prior_failure_fingerprint, review.current_failure_fingerprint)
    if any(f is not None and (not isinstance(f, str) or not _SHA.fullmatch(f))
           for f in failures):
        return stop("BLOCKED", "INVALID_FAILURE_FINGERPRINT")
    if failures[0] is not None and failures[0].casefold() == str(failures[1]).casefold():
        return stop("HOLD_REPEATED_FAILURE", "REQUIRES_DIFFERENT_SAFE_PATH")

    paths: set[str] = set()
    output: list[FileAdvice] = []
    for item in review.file_versions:
        if not isinstance(item, FileVersion) or not isinstance(item.path, str):
            return stop("BLOCKED", "INVALID_FILE_ROW")
        if not _valid_scope("path:" + item.path):
            return stop("BLOCKED", "INVALID_SCOPE_PATH")
        key = item.path.casefold()
        if key in paths:
            return stop("BLOCKED", "DUPLICATE_WINDOWS_PATH")
        paths.add(key)
        hashes = (
            item.base_sha256, item.local_sha256,
            item.pr_sha256, item.local_sha256_rechecked
        )
        if any(h is not None and (not isinstance(h, str) or not _SHA.fullmatch(h))
               for h in hashes):
            return stop("BLOCKED", "INVALID_FILE_DIGEST")
        base, local, pr, now = (h.lower() if h is not None else None for h in hashes)
        if local != now:
            return stop("HOLD_LOCAL_DRIFT", "LOCAL_FILE_CHANGED_AFTER_INVENTORY")
        if local == base and base == pr:
            classification = "ABSENT_ALL" if local is None else "IDENTICAL_ALL"
            action = "SKIP"
        elif local == pr:
            classification, action = "ALREADY_MATCHES_PR", "SKIP"
        elif local == base:
            classification, action = "PR_ONLY_CHANGE", "REVIEW_PR_CANDIDATE"
        elif pr == base:
            classification, action = "LOCAL_ONLY_CHANGE", "PRESERVE_LOCAL"
        else:
            classification, action = "DUAL_CHANGE_REVIEW", "ISOLATED_SEMANTIC_REVIEW"
        output.append(FileAdvice(item.path, classification, action))
    rows = tuple(output)
    if any(c.classification == "DUAL_CHANGE_REVIEW" for c in rows):
        return stop("HOLD_DUAL_CHANGE", "MANUAL_THREE_WAY_REVIEW_REQUIRED", rows)
    return stop("SOURCE_REVIEW_READY", "NO_AUTO_WRITE_OR_MERGE_AUTHORITY", rows)
