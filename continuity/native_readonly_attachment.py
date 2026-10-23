"""One source-level attachment point for the EXISTING native Organizer.

Cross-checks the installed read-only Organizer CLI's exact task against an
independently authenticated native Main/Organizer LiveTaskPort observation.
No writable adapter, provider caller or native .NET service ships here.
This function cannot acquire a lease or dispatch any work.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
import json
from typing import Protocol

from continuity.live_handoff_gate import (
    HandoffDenied, LiveTaskPort, ResumePacket, resume,
)
from continuity.organizer_cli_reader import NativeHandoffRead
from continuity.provider_resume_view import (
    TaskResumeView, ResumeViewInvalid, project_native_handoff,
)


class ExactHandoffReader(Protocol):
    def read_task(self, task_id: str) -> NativeHandoffRead: ...


class IntegrationDenied(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class BrainReadOnlyAttachment:
    """Validated source-only cross-check, never a native security ticket."""
    task_id: str
    project_id: str
    target_id: str
    canonical_revision: int
    observed_at: str
    state: str
    completed: tuple[str, ...]
    remaining: tuple[str, ...]
    checkpoint_stage: str
    next_action: str
    display: TaskResumeView
    integration_class: str = "NATIVE_CLI_HOST_CROSSCHECK_REFERENCE_ONLY"
    source_runtime_installed: bool = False
    may_claim: bool = False
    may_dispatch: bool = False
    may_send_chat_message: bool = False
    qa_installed_verified: bool = False

    def as_json(self) -> str:
        # Display and host fields are deliberately *not* free-form action
        # instructions. Consumer must regard all content as untrusted text.
        value = asdict(self)
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False)


def _check_consistent(
    read: NativeHandoffRead, view: TaskResumeView, trusted: ResumePacket,
) -> None:
    if read.task_id != trusted.task_id or view.task_id != trusted.task_id:
        raise IntegrationDenied("TASK_ID_CROSSCHECK_FAILED")
    if view.state != trusted.state:
        raise IntegrationDenied("STATE_CHANGED_DURING_CROSSCHECK")
    # The installed handoff CLI exposes task progress; a disappearing field
    # must not be converted to a fabricated empty list on a real handoff.
    for key, from_host in (
        ("completed", trusted.completed),
        ("remaining", trusted.remaining),
    ):
        value = read.task.get(key)
        if not isinstance(value, list):
            raise IntegrationDenied("CLI_PROGRESS_FIELD_MISSING")
        # Compare raw exact data *before* redaction; masking could hide
        # diverging secrets or different checkpoints.
        if tuple(value) != from_host:
            raise IntegrationDenied("PROGRESS_CHANGED_DURING_CROSSCHECK")
    # CLI output varies by installed build: compare optional fields if present.
    for key, expected in (
        ("target_id", trusted.target_id),
        ("project_id", trusted.project_id),
        ("checkpoint_stage", trusted.stage),
        ("stage", trusted.stage),
        ("next_action", trusted.next_action),
    ):
        if key in read.task and read.task[key] is not None:
            if read.task[key] != expected:
                raise IntegrationDenied("CONTRADICTORY_CLI_" + key.upper())


def prepare_read_only_attachment(
    cli: ExactHandoffReader,
    native: LiveTaskPort,
    task_id: str,
    *,
    expected_target: str,
    worker: str,
    now: datetime,
) -> BrainReadOnlyAttachment:
    """Read installed CLI + trusted host; fail closed on conflicting facts.

    Native port verifies its OWN source/revision/capture time independently.
    The CLI reports no independent revision, therefore this is NOT proof that
    the two reads share one atomic epoch. It is never a write admission.
    """
    read = cli.read_task(task_id)
    try:
        view = project_native_handoff(read)
    except ResumeViewInvalid as error:
        raise IntegrationDenied("CLI_VIEW_INVALID") from error
    try:
        trusted = resume(
            native, task_id, now=now, worker=worker,
            expected_target=expected_target, write=False,
        )
    except HandoffDenied as error:
        raise IntegrationDenied("NATIVE_" + error.code) from error
    if trusted.mode != "READ_ONLY":
        raise IntegrationDenied("UNEXPECTED_NATIVE_WRITE_MODE")
    _check_consistent(read, view, trusted)
    # Only sanitized/allowlisted fields enter the human/provider-facing
    # packet. A user's secret-bearing source record is NEVER returned.
    return BrainReadOnlyAttachment(
        task_id=trusted.task_id,
        project_id=trusted.project_id,
        target_id=trusted.target_id,
        canonical_revision=trusted.revision,
        observed_at=trusted.observed_at.isoformat(),
        state=trusted.state,
        completed=view.completed,
        remaining=view.remaining,
        checkpoint_stage=view.checkpoint_stage or trusted.stage,
        next_action=view.next_action,
        display=view,
    )
