#!/usr/bin/env python3
"""Read-only sanity check for INVENTHOR's public continuity reference.

This repository is not a live task runner. This check refuses to bless old
cloud queue/project snapshots as current canonical runtime state.
Python standard library only; no network, credentials, or local Operator.
"""
import json
import sys
from pathlib import Path


def validate(root: Path) -> list[str]:
    errors: list[str] = []

    def read_json(relative: str) -> dict:
        path = root / relative
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("expected a JSON object")
            return payload
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{relative}: unreadable or invalid JSON: {exc}")
            return {}

    def require_reference_only(relative: str, payload: dict) -> None:
        if payload.get("runtime_authoritative") is not False:
            errors.append(f"{relative}: runtime_authoritative must be false")
        if payload.get("reference_snapshot_only") is not True:
            errors.append(f"{relative}: must be explicitly snapshot-only")
        if payload.get("state_freshness") != "UNVERIFIED":
            errors.append(f"{relative}: cannot claim live state without runtime proof")
        if payload.get("freshness_policy_path") != (
            "continuity/LIVE_SOURCE_FRESHNESS_GATE.md"
        ):
            errors.append(f"{relative}: missing shared freshness policy link")

    policy = root / "continuity/LIVE_SOURCE_FRESHNESS_GATE.md"
    if not policy.is_file():
        errors.append("missing live-source freshness policy")

    entry_path = root / "CONTINUE_HERE.md"
    try:
        entry = entry_path.read_text(encoding="utf-8")
        if "STATUS=REFERENCE_ONLY_LIVE_TASK_RECHECK_REQUIRED" not in entry:
            errors.append("CONTINUE_HERE.md: legacy active status is unsafe")
        if "HISTORICAL_NEXT_TASK_20260922=" not in entry:
            errors.append("CONTINUE_HERE.md: old next task must be historical")
        if "LIVE_SOURCE_FRESHNESS_GATE.md" not in entry:
            errors.append("CONTINUE_HERE.md: freshness gate not discoverable")
    except OSError:
        errors.append("missing CONTINUE_HERE.md")

    manifest_path = "continuity/continuity_manifest.json"
    manifest = read_json(manifest_path)
    require_reference_only(manifest_path, manifest)
    if manifest.get("live_task_handoff_required") is not True:
        errors.append("manifest: live task-specific handoff must be required")

    queue_path = "continuity/work_queue.json"
    queue = read_json(queue_path)
    require_reference_only(queue_path, queue)
    if queue.get("owner_runtime_task_id_required") is not True:
        errors.append("queue: must require a canonical runtime task ID")

    ideas_path = "continuity/idea_pool.json"
    ideas = read_json(ideas_path)
    require_reference_only(ideas_path, ideas)
    if ideas.get("ideas_do_not_preempt_active_work") is not True:
        errors.append("ideas: backlog intake must not preempt active work")

    declared = [
        manifest.get("idea_pool_path"),
        manifest.get("resume_protocol_path"),
        manifest.get("terminology_path"),
        manifest.get("replication_policy_path"),
        manifest.get("owner_work_intake_policy_path"),
    ]
    declared.extend(
        x.get("state_path") for x in manifest.get("active_projects", [])
        if isinstance(x, dict)
    )
    for relative in declared:
        if not isinstance(relative, str):
            errors.append("manifest: invalid path declaration")
            continue
        resolved = (root / relative).resolve()
        if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
            errors.append(f"manifest: missing/unsafe declared file {relative}")
        elif relative.startswith("continuity/active_projects/"):
            require_reference_only(relative, read_json(relative))

    for relative in (
        "continuity/agent_resume_protocol.md",
        "continuity/OWNER_WORK_INTAKE_POLICY.md",
    ):
        try:
            text = (root / relative).read_text(encoding="utf-8")
            if "LIVE_SOURCE_FRESHNESS_GATE.md" not in text:
                errors.append(f"{relative}: missing live-source guard")
        except OSError:
            errors.append(f"{relative}: missing")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    errors = validate(root)
    for error in errors:
        print("BRAIN_REFERENCE_FAIL:", error)
    if errors:
        return 1
    print("BRAIN_REFERENCE_FRESHNESS_GUARD_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
