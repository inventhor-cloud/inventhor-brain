"""Read-only wrapper for an existing, owner-pinned INVENTHOR Organizer Tool.

This file never starts work, edits a task, claims leases, installs modules or
creates a second brain/queue. An installed Main/Organizer adapter must still
verify provenance, canonical epoch and native preflight before any WRITE.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Mapping
import json
import re
import subprocess

SOURCE = "CANONICAL_WORK_ITEMS_AND_EVENTS_READ_ONLY"
TASK_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
HEX_SHA = re.compile(r"^[a-fA-F0-9]{64}$")
MAX_OUTPUT = 256 * 1024


class NativeHandoffUnavailable(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class NativeHandoffRead:
    task_id: str
    source: str
    task: Mapping[str, Any]


class OrganizerCliReader:
    """Owner-supplied executable and root, with a pinned executable hash.

    Even a valid read is not sufficient to construct a trusted write-capable
    ResumePacket: revision, capture time, dependency status and ownership
    must be freshly corroborated by the native Main/Organizer host.
    """

    def __init__(self, *, tool_path: Path, organizer_root: Path,
                 expected_tool_sha256: str,
                 runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run):
        if not isinstance(expected_tool_sha256, str) or not HEX_SHA.fullmatch(expected_tool_sha256):
            raise NativeHandoffUnavailable("PINNED_TOOL_SHA256_REQUIRED")
        self.tool_path = Path(tool_path)
        self.organizer_root = Path(organizer_root)
        self.expected_tool_sha256 = expected_tool_sha256.lower()
        self.runner = runner

    def _verify_pinned_tool(self) -> None:
        if not self.tool_path.is_file() or self.tool_path.is_symlink():
            raise NativeHandoffUnavailable("PINNED_NATIVE_TOOL_MISSING")
        if not self.organizer_root.is_dir() or self.organizer_root.is_symlink():
            raise NativeHandoffUnavailable("CANONICAL_ROOT_UNAVAILABLE")
        try:
            with self.tool_path.open("rb") as f:
                digest = sha256(f.read()).hexdigest()
        except OSError as e:
            raise NativeHandoffUnavailable("PINNED_NATIVE_TOOL_UNREADABLE") from e
        if digest != self.expected_tool_sha256:
            raise NativeHandoffUnavailable("PINNED_NATIVE_TOOL_CHANGED")

    def read_task(self, task_id: str) -> NativeHandoffRead:
        if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
            raise NativeHandoffUnavailable("TASK_ID_INVALID")
        self._verify_pinned_tool()
        args = [str(self.tool_path.resolve()), "handoff",
                "--root=" + str(self.organizer_root.resolve()),
                "--task=" + task_id]
        try:
            result = self.runner(args, shell=False, capture_output=True,
                                 text=True, timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise NativeHandoffUnavailable("NATIVE_HANDOFF_UNAVAILABLE") from e
        # Detect at least substitutions during invocation. This is a second
        # integrity observation, NOT an Authenticode/ACL/TOCTOU guarantee:
        # installed native host must separately enforce those properties.
        self._verify_pinned_tool()
        if result.returncode != 0:
            raise NativeHandoffUnavailable("NATIVE_HANDOFF_REFUSED")
        if not isinstance(result.stdout, str) or len(result.stdout) > MAX_OUTPUT:
            raise NativeHandoffUnavailable("NATIVE_HANDOFF_OVERSIZED")
        try:
            document = json.loads(result.stdout)
        except (json.JSONDecodeError, TypeError) as e:
            raise NativeHandoffUnavailable("NATIVE_HANDOFF_MALFORMED") from e
        if not isinstance(document, dict) or document.get("source") != SOURCE:
            raise NativeHandoffUnavailable("NON_CANONICAL_HANDOFF")
        tasks = document.get("tasks")
        if not isinstance(tasks, list) or len(tasks) != 1:
            raise NativeHandoffUnavailable("HANDOFF_NOT_EXACT_TASK")
        if "task_count" in document and document["task_count"] != 1:
            raise NativeHandoffUnavailable("HANDOFF_COUNT_MISMATCH")
        item = tasks[0]
        if not isinstance(item, dict):
            raise NativeHandoffUnavailable("HANDOFF_TASK_INVALID")
        ids = [item[key] for key in ("id", "task_id") if key in item]
        if not ids or any(value != task_id for value in ids):
            raise NativeHandoffUnavailable("HANDOFF_TASK_ID_MISMATCH")
        if not isinstance(item.get("state"), str):
            raise NativeHandoffUnavailable("HANDOFF_STATE_MISSING")
        return NativeHandoffRead(task_id=task_id, source=SOURCE, task=item)
