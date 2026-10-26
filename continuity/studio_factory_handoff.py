"""Source-only Studio Design -> existing QA Factory cycle verifier.

Exactly five architectural systems: INVENTHOR, Operator, the existing
canonical Organizer, Studio Design and the existing Quality Factory (QA). This validates
reported handoff identity and evidence consistency. It does not create a
Studio, Factory, queue, job, application or installed workflow; native host
must authenticate every fact and acquire existing Organizer lease itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re


ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
SHA = re.compile(r"^[0-9a-f]{64}$")
MAX_AGE = timedelta(seconds=60)
PHASES = frozenset({
    "DESIGN_EDITED", "BUILD_RUNNING", "QA_FAILED",
    "REPAIRED_RUNNING", "QA_PASSED",
})


class StudioFactoryDenied(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class StudioFactorySnapshot:
    native_task_id: str
    project_id: str
    design_document_id: str
    native_task_revision: int
    design_revision: int
    phase: str
    observed_at: datetime
    build_sha256: str = ""
    factory_tested_sha256: str = ""
    previous_failed_build_sha256: str = ""
    previous_failed_factory_run_id: str = ""
    previous_failure_evidence_ref: str = ""
    prior_design_revision: int = 0
    iteration: int = 1
    real_preview_verified: bool = False
    real_program_launch_verified: bool = False
    factory_run_id: str = ""
    factory_verdict: str = "NONE"
    defect_evidence_ref: str = ""
    qa_witness_verified: bool = False
    rollback_verified: bool = False


@dataclass(frozen=True)
class StudioFactoryAdvice:
    task_id: str
    project_id: str
    phase: str
    disposition: str
    next_action: str
    blockers: tuple[str, ...]
    reference_type: str = "SOURCE_ONLY_STUDIO_FACTORY_ADVICE_NOT_NATIVE_QA"
    native_evidence_authenticated: bool = False
    factory_pass_attested: bool = False
    may_create_task: bool = False
    may_execute: bool = False
    may_install: bool = False
    may_release: bool = False


def _id(value: object, label: str) -> str:
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise StudioFactoryDenied("INVALID_" + label)
    return value


def _revision(value: object, label: str, *, allow_zero: bool = False) -> int:
    if type(value) is not int or value < (0 if allow_zero else 1):
        raise StudioFactoryDenied("INVALID_" + label)
    return value


def _flag(value: object, label: str) -> bool:
    if type(value) is not bool:
        raise StudioFactoryDenied("INVALID_" + label)
    return value


def advise_studio_factory_handoff(
    snapshot: StudioFactorySnapshot, *, now: datetime,
    expected_task_id: str, expected_project_id: str,
    expected_native_revision: int,
) -> StudioFactoryAdvice:
    """Validate a *claimed* one-project design/build/QA/fix/retest chain.

    The packet is never a QA certificate. Factory proof, native leases,
    signing and rollback must all be independently verified by the installed
    owner-authorized services. No real operation or queue write occurs here.
    """
    if not isinstance(snapshot, StudioFactorySnapshot):
        raise StudioFactoryDenied("SNAPSHOT_REQUIRED")
    for label, value in (
        ("TASK_ID", snapshot.native_task_id),
        ("PROJECT_ID", snapshot.project_id),
        ("DOCUMENT_ID", snapshot.design_document_id),
        ("EXPECTED_TASK_ID", expected_task_id),
        ("EXPECTED_PROJECT_ID", expected_project_id),
    ):
        _id(value, label)
    for label, value in (
        ("NATIVE_TASK_REVISION", snapshot.native_task_revision),
        ("EXPECTED_NATIVE_REVISION", expected_native_revision),
        ("DESIGN_REVISION", snapshot.design_revision),
    ):
        _revision(value, label)
    _revision(snapshot.prior_design_revision, "PRIOR_DESIGN_REVISION",
              allow_zero=True)
    if (type(snapshot.iteration) is not int
        or not 1 <= snapshot.iteration <= 5):
        raise StudioFactoryDenied("UNBOUNDED_QA_ITERATIONS")
    if snapshot.native_task_id != expected_task_id:
        raise StudioFactoryDenied("TASK_SCOPE_MISMATCH")
    if snapshot.project_id != expected_project_id:
        raise StudioFactoryDenied("PROJECT_SCOPE_MISMATCH")
    if snapshot.native_task_revision != expected_native_revision:
        raise StudioFactoryDenied("STALE_NATIVE_TASK_REVISION")
    if snapshot.phase not in PHASES:
        raise StudioFactoryDenied("INVALID_PHASE")
    if (not isinstance(now, datetime) or now.tzinfo is None
        or now.utcoffset() is None
        or not isinstance(snapshot.observed_at, datetime)
        or snapshot.observed_at.tzinfo is None
        or snapshot.observed_at.utcoffset() is None):
        raise StudioFactoryDenied("AWARE_TIMESTAMPS_REQUIRED")
    now_utc = now.astimezone(timezone.utc)
    stamp = snapshot.observed_at.astimezone(timezone.utc)
    if stamp > now_utc + timedelta(seconds=5) or now_utc - stamp > MAX_AGE:
        raise StudioFactoryDenied("STALE_OR_FUTURE_SNAPSHOT")
    for field in (
        "real_preview_verified", "real_program_launch_verified",
        "qa_witness_verified", "rollback_verified",
    ):
        _flag(getattr(snapshot, field), field.upper())
    for field in (
        "build_sha256", "factory_tested_sha256",
        "previous_failed_build_sha256",
    ):
        value = getattr(snapshot, field)
        if not isinstance(value, str) or (value and not SHA.fullmatch(value)):
            raise StudioFactoryDenied("INVALID_" + field.upper())
    for field in (
        "factory_run_id", "defect_evidence_ref",
        "previous_failed_factory_run_id", "previous_failure_evidence_ref",
    ):
        value = getattr(snapshot, field)
        if not isinstance(value, str) or len(value) > 128 or (
            value and not ID.fullmatch(value)
        ):
            raise StudioFactoryDenied("INVALID_" + field.upper())
    if snapshot.factory_verdict not in ("NONE", "FAIL", "PASS", "BLOCKED"):
        raise StudioFactoryDenied("INVALID_FACTORY_VERDICT")

    errors: list[str] = []
    def need(condition: bool, code: str) -> None:
        if not condition:
            errors.append(code)

    actions = {
        "DESIGN_EDITED": "OPERATOR_BUILD_LAUNCH_AND_VERIFY_REAL_STUDIO_PROGRAM",
        "BUILD_RUNNING": "SUBMIT_EXACT_BUILD_TO_EXISTING_FACTORY",
        "QA_FAILED": "REPAIR_DOCUMENT_IN_STUDIO_THEN_REBUILD",
        "REPAIRED_RUNNING": "RESUBMIT_CHANGED_BUILD_TO_EXISTING_FACTORY",
        "QA_PASSED": "REQUEST_SEPARATE_NATIVE_OWNER_RELEASE_PREFLIGHT",
    }
    phase = snapshot.phase
    if phase == "DESIGN_EDITED":
        # An edited design cannot inherit an old build/QA certificate.
        need(snapshot.factory_verdict == "NONE", "PREMATURE_FACTORY_VERDICT")
        need(not snapshot.build_sha256, "DESIGN_MUST_NOT_CARRY_OLD_BUILD")
        need(not snapshot.factory_tested_sha256, "DESIGN_MUST_NOT_CARRY_OLD_QA")
        need(not snapshot.factory_run_id, "DESIGN_MUST_NOT_CARRY_OLD_QA_RUN")
        need(not snapshot.qa_witness_verified, "DESIGN_MUST_NOT_CLAIM_QA_WITNESS")
        need(not snapshot.real_program_launch_verified,
             "DESIGN_MUST_NOT_CLAIM_REAL_LAUNCH")
    else:
        need(bool(snapshot.build_sha256), "BUILD_HASH_MISSING")
        need(snapshot.real_preview_verified, "REAL_PREVIEW_NOT_VERIFIED")
        need(snapshot.real_program_launch_verified, "REAL_PROGRAM_NOT_VERIFIED")

    if phase in ("BUILD_RUNNING", "REPAIRED_RUNNING"):
        need(snapshot.factory_verdict == "NONE", "STALE_FACTORY_VERDICT")
        need(not snapshot.factory_tested_sha256, "OLD_QA_RESULT_REUSED")
        need(not snapshot.factory_run_id, "OLD_FACTORY_RUN_REUSED")
    if phase in ("QA_FAILED", "QA_PASSED"):
        need(snapshot.factory_tested_sha256 == snapshot.build_sha256
             and bool(snapshot.factory_tested_sha256),
             "FACTORY_TESTED_DIFFERENT_BUILD")
        need(bool(snapshot.factory_run_id), "FACTORY_RUN_MISSING")
        need(snapshot.qa_witness_verified, "FACTORY_WITNESS_MISSING")
    if phase == "QA_FAILED":
        need(snapshot.factory_verdict == "FAIL", "REAL_FAILURE_NOT_RECORDED")
        need(bool(snapshot.defect_evidence_ref), "DEFECT_EVIDENCE_MISSING")
        need(snapshot.iteration < 5, "REPAIR_ITERATION_BUDGET_EXHAUSTED")
    if phase == "REPAIRED_RUNNING":
        need(snapshot.iteration > 1, "REPAIR_REQUIRES_FAILED_PRIOR_ITERATION")
    if phase == "QA_PASSED" and snapshot.iteration == 1:
        # First-pass success is valid; it must not inherit failed-run metadata
        # belonging to an unrelated prior build or project.
        need(not snapshot.previous_failed_build_sha256,
             "FIRST_PASS_CARRIES_OLD_FAILED_BUILD")
        need(not snapshot.previous_failed_factory_run_id,
             "FIRST_PASS_CARRIES_OLD_FAILED_QA_RUN")
        need(not snapshot.previous_failure_evidence_ref,
             "FIRST_PASS_CARRIES_OLD_FAILURE_EVIDENCE")
    if phase in ("REPAIRED_RUNNING", "QA_PASSED") and snapshot.iteration > 1:
        need(bool(snapshot.previous_failed_build_sha256),
             "FAILED_BUILD_REFERENCE_MISSING")
        need(snapshot.previous_failed_build_sha256 != snapshot.build_sha256,
             "REPAIR_DID_NOT_CHANGE_BUILD")
        need(snapshot.prior_design_revision < snapshot.design_revision
             and snapshot.prior_design_revision >= 1,
             "STUDIO_REVISION_DID_NOT_ADVANCE")
        # A new build hash alone is not a proven fix/retest: the previous
        # exact failed Factory run and its defect must be carried forward.
        need(bool(snapshot.previous_failed_factory_run_id),
             "PRIOR_FAILED_FACTORY_RUN_MISSING")
        need(bool(snapshot.previous_failure_evidence_ref),
             "PRIOR_FAILURE_EVIDENCE_MISSING")
        if phase == "QA_PASSED":
            need(snapshot.factory_run_id != snapshot.previous_failed_factory_run_id,
                 "SAME_FACTORY_RUN_REUSED_FOR_RETEST")
    if phase == "QA_PASSED":
        need(not snapshot.defect_evidence_ref,
             "CURRENT_PASS_CARRIES_FAILURE_EVIDENCE")
    if phase == "QA_PASSED":
        need(snapshot.factory_verdict == "PASS", "FACTORY_PASS_NOT_RECORDED")
        need(snapshot.rollback_verified, "ROLLBACK_NOT_VERIFIED")

    return StudioFactoryAdvice(
        task_id=snapshot.native_task_id, project_id=snapshot.project_id,
        phase=phase, disposition=(
            "BLOCKED" if errors else "NATIVE_PREFLIGHT_REQUIRED"
        ),
        next_action=("RECONCILE_REAL_STUDIO_FACTORY_EVIDENCE"
                     if errors else actions[phase]),
        blockers=tuple(errors),
    )
