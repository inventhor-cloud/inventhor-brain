"""Evidence-based lessons from other agents for the canonical INVENTHOR Brain.

This is a deterministic source-only reducer, not a model fine-tuner or memory
database. Its results must be persisted by authenticated Main after validation.
No remote provider calls, automatic patch reuse, task creation or private logs.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
import hashlib
import re

_IDENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
_HEX64 = re.compile(r"[0-9a-fA-F]{64}\Z")
_STEPS = frozenset(("BUILD", "TEST", "INTEGRATION", "REVIEW", "DEPLOY", "QUALITY"))
_OUTCOMES = frozenset(("FAILED", "UNVERIFIED_PASS", "VERIFIED_PASS"))
_MAX_EVENTS = 512


def _id(value: object) -> bool:
    return isinstance(value, str) and _IDENT.fullmatch(value) is not None


def _hash(value: object) -> bool:
    return isinstance(value, str) and _HEX64.fullmatch(value) is not None


def _time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except (ValueError, OverflowError):
        return None


def review_agent_lessons(report: object, *, host_snapshot_revision: str,
                         host_time_iso: str, project_id: str | None = None,
                         max_lessons: int = 8) -> dict:
    """Find repeated failure signatures and *verified* recoveries across agents.

    A reference labeled verified is still only host-supplied evidence here.
    Results cannot be used as permissions, learning weights, or live truth.
    """
    def answer(status: str, reason: str = "", lessons: list[dict] | None = None,
               event_count: int = 0) -> dict:
        return {
            "status": status, "reason": reason, "lessons": lessons or [],
            "inspected_event_count": event_count,
            "source_only": True, "may_replay_failure": False,
            "may_auto_apply_fix": False, "may_train_model": False,
            "may_create_task": False, "may_access_other_project": False,
            "may_claim_live_verified": False,
            "requires_main_evidence_attestation": True,
            "requires_host_persistence": True,
        }

    if (not isinstance(report, Mapping) or not _id(host_snapshot_revision)
        or (project_id is not None and not _id(project_id))
        or type(max_lessons) is not int or max_lessons < 1 or max_lessons > 32):
        return answer("BLOCKED", "INVALID_LEARNING_INPUT")
    now, captured = _time(host_time_iso), _time(report.get("captured_at"))
    if (type(report.get("schema_version")) is not int
        or report.get("schema_version") != 1
        or report.get("source") != "INVENTHOR_MAIN"
        or report.get("snapshot_revision") != host_snapshot_revision
        or not now or not captured or not -5 <= (now - captured).total_seconds() <= 120):
        return answer("BLOCKED", "UNTRUSTED_OR_STALE_EVIDENCE")
    events = report.get("events")
    if not isinstance(events, list) or len(events) > _MAX_EVENTS:
        return answer("BLOCKED", "INVALID_EVIDENCE_EVENT_LIST")

    seen: set[str] = set()
    failures: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    recoveries: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    filtered = 0
    for item in events:
        if not isinstance(item, Mapping):
            return answer("BLOCKED", "INVALID_AGENT_EVENT")
        eid, pid, tid, agent = (item.get("event_id"), item.get("project_id"),
                                item.get("task_id"), item.get("agent_id"))
        step, outcome = item.get("step"), item.get("outcome")
        when = _time(item.get("timestamp"))
        evidence = item.get("evidence_ref")
        fingerprint = item.get("failure_fingerprint")
        resolved = item.get("resolved_failure_fingerprint")
        quality = item.get("quality_verified")
        if (not all(_id(v) for v in (eid, pid, tid, agent, evidence))
            or not isinstance(step, str) or step not in _STEPS
            or not isinstance(outcome, str) or outcome not in _OUTCOMES
            or when is None or when > now or when < captured - timedelta(days=30)
            or (fingerprint is not None and not _hash(fingerprint))
            or (resolved is not None and not _hash(resolved))
            or type(quality) is not bool):
            return answer("BLOCKED", "INVALID_AGENT_EVENT")
        if eid in seen:
            return answer("BLOCKED", "DUPLICATE_AGENT_EVENT")
        seen.add(eid)
        if project_id is not None and pid != project_id:
            continue
        filtered += 1
        record = {"event_id": eid, "agent_id": agent, "task_id": tid,
                  "evidence_ref": evidence, "when": when,
                  "quality_verified": quality}
        if outcome == "FAILED" and fingerprint is not None:
            failures[(pid, step, fingerprint.lower())].append(record)
        elif outcome == "VERIFIED_PASS" and resolved is not None and quality:
            recoveries[(pid, step, resolved.lower())].append(record)

    lessons: list[dict] = []
    for (pid, step, fingerprint), failed in sorted(failures.items()):
        fixed = sorted(
            (r for r in recoveries.get((pid, step, fingerprint), ())
             if any(r["when"] > f["when"] for f in failed)),
            key=lambda r: (r["when"], r["event_id"]),
        )
        if len(failed) < 2 and not fixed:
            continue  # One failure without verified repair is not yet a reusable rule.
        remedy = fixed[0] if fixed else None
        key = hashlib.sha256((pid + "\0" + step + "\0" + fingerprint)
                             .encode("utf-8")).hexdigest()
        lessons.append({
            "lesson_fingerprint": key,
            "project_id": pid, "step": step,
            "failure_fingerprint": fingerprint,
            "failed_attempts": len(failed),
            "agents_observed": sorted({r["agent_id"] for r in failed + fixed}),
            "verified_recovery_evidence_ref": remedy["evidence_ref"] if remedy else None,
            "verified_recovery_task_id": remedy["task_id"] if remedy else None,
            "next_action": ("REVIEW_VERIFIED_RECOVERY_FOR_REUSE"
                            if remedy else "HOLD_IDENTICAL_RETRY_AND_DIAGNOSE"),
            "needs_quality_factory_recheck": True,
        })
    lessons.sort(key=lambda item: (
        0 if item["verified_recovery_evidence_ref"] else 1,
        -item["failed_attempts"], item["project_id"], item["step"],
        item["failure_fingerprint"],
    ))
    return answer("LESSONS_REVIEW_READY", lessons=lessons[:max_lessons],
                  event_count=filtered)



def advise_fix_memory_promotion(lesson_report: object, memory_snapshot: object, *,
                                host_snapshot_revision: str,
                                max_candidates: int = 4) -> dict:
    """Suggest bounded idempotent updates to EXISTING canonical Fix Memory.

    The host must attach a current, attested revision to the canonical
    fix_memory index; old GitHub template JSON is not a live snapshot.
    No mutation, history deletion, secret copying or second memory database.
    """
    def result(status: str, reason: str = "", proposals: list[dict] | None = None) -> dict:
        return {
            "status": status, "reason": reason,
            "proposals": proposals or [],
            "memory_target": "INVENTHOR_MAIN_FIX_MEMORY",
            "source_only": True,
            "may_write_memory": False, "may_delete_history": False,
            "may_auto_apply_fix": False, "may_create_task": False,
            "requires_main_snapshot_attestation": True,
            "requires_quality_factory_review": True,
        }

    if (not isinstance(lesson_report, Mapping)
        or lesson_report.get("status") != "LESSONS_REVIEW_READY"
        or not isinstance(lesson_report.get("lessons"), list)
        or len(lesson_report["lessons"]) > 32
        or not isinstance(memory_snapshot, Mapping)
        or not _id(host_snapshot_revision)
        or type(max_candidates) is not int or not 1 <= max_candidates <= 32):
        return result("BLOCKED", "INVALID_MEMORY_PROMOTION_INPUT")
    if (type(memory_snapshot.get("schema_version")) is not int
        or memory_snapshot.get("schema_version") != 1
        or memory_snapshot.get("source") != "INVENTHOR_MAIN_FIX_MEMORY"
        or memory_snapshot.get("snapshot_revision") != host_snapshot_revision
        or not isinstance(memory_snapshot.get("fixes"), list)
        or len(memory_snapshot["fixes"]) > 4096):
        return result("BLOCKED", "UNPINNED_OR_INVALID_FIX_MEMORY")

    stored: dict[tuple[str, str], str | None] = {}
    for entry in memory_snapshot["fixes"]:
        if not isinstance(entry, Mapping):
            return result("BLOCKED", "INVALID_KNOWN_FIX_ENTRY")
        project, fingerprint, evidence = (
            entry.get("project_id"), entry.get("lesson_fingerprint"),
            entry.get("verified_recovery_evidence_ref"))
        if (not _id(project) or not _hash(fingerprint)
            or (evidence is not None and not _id(evidence))):
            return result("BLOCKED", "INVALID_KNOWN_FIX_ENTRY")
        key = (project, fingerprint.lower())
        if key in stored:
            return result("BLOCKED", "DUPLICATE_KNOWN_FIX")
        stored[key] = evidence

    candidates = []
    seen = set()
    for lesson in lesson_report["lessons"]:
        if not isinstance(lesson, Mapping):
            return result("BLOCKED", "INVALID_LESSON_CANDIDATE")
        project, fingerprint, evidence = (
            lesson.get("project_id"), lesson.get("lesson_fingerprint"),
            lesson.get("verified_recovery_evidence_ref"))
        if (not _id(project) or not _hash(fingerprint)
            or (evidence is not None and not _id(evidence))):
            return result("BLOCKED", "INVALID_LESSON_CANDIDATE")
        key = (project, fingerprint.lower())
        if key in seen:
            return result("BLOCKED", "DUPLICATE_LESSON_CANDIDATE")
        seen.add(key)
        if key not in stored:
            action = "PROPOSE_NEW_CANONICAL_FIX_MEMORY_RECORD"
        elif stored[key] == evidence:
            action = "REUSE_EXISTING_CANONICAL_MEMORY"
        elif stored[key] is None and evidence is not None:
            action = "REVIEW_VERIFIED_RECOVERY_ENRICHMENT"
        else:
            action = "REVIEW_CONFLICTING_FIX_EVIDENCE"
        candidates.append({
            "project_id": project,
            "lesson_fingerprint": fingerprint.lower(),
            "next_action": action,
            "existing_evidence_ref": stored.get(key),
            "candidate_evidence_ref": evidence,
        })
    candidates.sort(key=lambda x: (x["project_id"], x["lesson_fingerprint"]))
    return result("FIX_MEMORY_INTAKE_ADVISORY",
                  proposals=candidates[:max_candidates])
