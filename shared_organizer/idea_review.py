"""Advisory IDEA intake for the EXISTING Main/WorkOrganizer ledger.

Compares one owner-supplied thought with a fresh, project-scoped canonical
work/idea snapshot. No second registry, automatic semantic inference, provider
call, file access, task creation, promotion, lease or background process.
Main alone can authenticate the snapshot and approve a canonical IDEA capture.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import timezone
import re
import unicodedata

from .board import _queue_rows, _time

_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
_MAX_WORK = 2048
_MAX_IDEAS = 512
_MAX_TITLE = 200


def _id(value: object) -> bool:
    return isinstance(value, str) and _ID.fullmatch(value) is not None


def _title(value: object) -> str | None:
    if not isinstance(value, str) or not 5 <= len(value.strip()) <= _MAX_TITLE:
        return None
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        return None
    folded = unicodedata.normalize("NFKC", value).casefold()
    # Locale-neutral casefold splits Turkish I/İ/ı; folding these to i is
    # review-only and never merges records without the trusted Main host.
    folded = folded.replace("\u0307", "").replace("\u0131", "i")
    words = re.findall(r"[^\W_]+", folded)
    return " ".join(words) if words else None


def _similar(left: str, right: str) -> bool:
    a, b = set(left.split()), set(right.split())
    # Token overlap merely asks for review; it never authorizes a merge.
    return (len(a) >= 3 and len(b) >= 3
            and len(a & b) >= 3
            and len(a & b) / len(a | b) >= 0.65)


def advise_idea_intake(
    projects: object,
    queue: object,
    existing_ideas: object,
    proposal: object,
    *,
    host_snapshot_revision: str,
    host_time_iso: str,
) -> dict:
    """Return a project-scoped advisory intake verdict, never an IDEA write.

    Source claims are not proof of a host-signed snapshot. The host must
    independently authenticate the project membership, revision, permission,
    canonical idea index and identity before doing a revision-locked capture.
    """
    def answer(status: str, matches: list[dict] | None = None) -> dict:
        return {
            "status": status,
            "matches": matches or [],
            "state": "SOURCE_REFERENCE_ONLY",
            "may_create_idea": False,
            "may_update_idea": False,
            "may_promote_todo": False,
            "may_take_ownership": False,
            "may_execute": False,
            "requires_authenticated_main_snapshot": True,
            "requires_host_atomic_review": True,
        }

    if (not isinstance(projects, list) or not isinstance(queue, Mapping)
        or not isinstance(proposal, Mapping)
        or not _id(host_snapshot_revision)
        or not isinstance(existing_ideas, list)):
        return answer("INVALID_INPUT")
    if len(projects) > 256 or len(existing_ideas) > _MAX_IDEAS:
        return answer("BOUNDED_INDEX_REQUIRED")

    now, captured = _time(host_time_iso), _time(queue.get("captured_at"))
    if (not _id(queue.get("snapshot_revision"))
        or queue["snapshot_revision"] != host_snapshot_revision
        or now is None or captured is None):
        return answer("UNVERSIONED_OR_MISMATCHED_SNAPSHOT")
    age = (now - captured).total_seconds()
    if not -5 <= age <= 120:
        return answer("STALE_SNAPSHOT_REQUIRES_MAIN_REFRESH")

    try:
        work = _queue_rows(queue)
    except ValueError:
        return answer("UNTRUSTED_CANONICAL_QUEUE")
    if len(work) > _MAX_WORK:
        return answer("BOUNDED_INDEX_REQUIRED")

    project_ids = set()
    for project in projects:
        if not isinstance(project, Mapping) or not _id(project.get("project_id")):
            return answer("INVALID_PROJECT_REGISTRY")
        pid = project["project_id"]
        if pid in project_ids:
            return answer("DUPLICATE_PROJECT_REGISTRY")
        project_ids.add(pid)

    pid = proposal.get("project_id")
    if not _id(pid):
        return answer("EXPLICIT_PROJECT_ROUTING_REQUIRED")
    if pid not in project_ids:
        return answer("PROJECT_NOT_REGISTERED")
    normalized = _title(proposal.get("title"))
    if normalized is None:
        return answer("INVALID_IDEA_TITLE")

    # Separate from the same canonical Work Items: the caller supplies the
    # canonical Idea Pool index, not a search result or another task database.
    indexed: list[dict] = []
    seen_ids: set[tuple[str, str]] = set()
    for kind, items in (("WORK_ITEM", work), ("IDEA", existing_ideas)):
        for item in items:
            if not isinstance(item, Mapping):
                return answer("INVALID_CANONICAL_INDEX")
            item_pid = item.get("project_id")
            if not _id(item_pid):
                return answer("INVALID_CANONICAL_INDEX")
            if item_pid != pid:
                continue  # Never disclose or match another project's work.
            item_id = (item.get("task_id", item.get("id"))
                       if kind == "WORK_ITEM"
                       else item.get("idea_id", item.get("id")))
            title = _title(item.get("title"))
            if not _id(item_id) or title is None:
                return answer("INCOMPLETE_CANONICAL_INDEX")
            key = (pid, item_id)
            if key in seen_ids:
                return answer("AMBIGUOUS_CANONICAL_ID")
            seen_ids.add(key)
            indexed.append({
                "id": item_id,
                "kind": kind,
                "state": str(item.get("state", "UNKNOWN"))[:32],
                "normalized_title": title,
            })

    exact = [i for i in indexed if i["normalized_title"] == normalized]
    if len(exact) > 1:
        return answer("AMBIGUOUS_DUPLICATE_REVIEW", [
            {k: v for k, v in i.items() if k != "normalized_title"}
            for i in exact[:12]
        ])
    if exact:
        item = exact[0]
        status = ("HISTORY_REVIEW_NO_REPLAY"
                  if item["state"] in ("DONE", "BS", "ARCHIVED")
                  else "EXISTING_IDEA_REVIEW" if item["kind"] == "IDEA"
                  else "EXISTING_WORK_REVIEW")
        return answer(status, [
            {k: v for k, v in item.items() if k != "normalized_title"}
        ])

    similar = [i for i in indexed if _similar(normalized, i["normalized_title"])]
    if similar:
        return answer("SIMILAR_PURPOSE_REVIEW", [
            {k: v for k, v in i.items() if k != "normalized_title"}
            for i in sorted(similar, key=lambda x: (x["kind"], x["id"]))[:12]
        ])

    # Never mark a proposal IDEA or TODO here. Authenticated Main must recheck
    # uniqueness, project routing, quotas, approval and an atomic ledger write.
    return answer("HOST_IDEA_CAPTURE_REVIEW_REQUIRED")
