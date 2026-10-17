"""Pure Mode 01 OBD-II response decoder; NO vehicle I/O or live diagnosis.

Takes an already-captured, single-ECU positive diagnostic payload, for
example bytes [0x41, 0x0C, 0x1A, 0xF8]. Vehicle transport, source attribution,
authorization and PID support MUST be validated by the real Main host.
Never sends AT commands, queries, CAN frames, clears faults or changes a vehicle.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ObdMetric:
    status: str
    pid: str | None = None
    label: str | None = None
    value: float | None = None
    unit: str | None = None
    reason: str = ""
    source_only: bool = True
    vehicle_identity_verified: bool = False
    sensor_calibration_verified: bool = False
    diagnosis_confirmed: bool = False
    may_send_vehicle_commands: bool = False
    may_write_vehicle: bool = False


# A small strictly-known subset; expand only with individually verified
# formulas and documented tests. Unknown PIDs MUST NOT be guessed.
_SUPPORTED: dict[int, tuple[str, str, int]] = {
    0x05: ("engine_coolant_temperature", "degC", 1),
    0x0C: ("engine_speed", "rpm", 2),
    0x0D: ("vehicle_speed", "km/h", 1),
    0x11: ("throttle_position", "percent", 1),
}


def decode_obd_mode01(payload: object) -> ObdMetric:
    """Decode positive Mode 01 data bytes, never an ELM/CAN transport stream.

    Payload MUST contain the response mode 0x41, PID and only its data.
    Reject negatives, missing/extra bytes, unsupported PIDs, protocol headers,
    booleans, raw strings and type ambiguity instead of inventing telemetry.
    """
    def fail(reason: str) -> ObdMetric:
        return ObdMetric(status="REJECTED", reason=reason)
    if not isinstance(payload, (bytes, bytearray)):
        return fail("BYTE_PAYLOAD_REQUIRED")
    if len(payload) < 3 or len(payload) > 4:
        return fail("INVALID_RESPONSE_LENGTH")
    if payload[0] != 0x41:
        return fail("NOT_POSITIVE_MODE01_RESPONSE")
    pid = payload[1]
    if pid not in _SUPPORTED:
        return fail("UNSUPPORTED_PID")
    label, unit, expected_length = _SUPPORTED[pid]
    if len(payload) != expected_length + 2:
        return fail("INVALID_PID_DATA_LENGTH")
    a = payload[2]
    if pid == 0x05:
        value = a - 40
    elif pid == 0x0C:
        value = ((a * 256) + payload[3]) / 4
    elif pid == 0x0D:
        value = a
    else:  # 0x11
        value = (a * 100) / 255
    return ObdMetric(
        status="SOURCE_DECODE_ONLY",
        pid=f"{pid:02X}",
        label=label,
        value=round(value, 3),
        unit=unit,
        reason="HOST_MUST_VERIFY_VEHICLE_ADAPTER_PROVENANCE",
    )
