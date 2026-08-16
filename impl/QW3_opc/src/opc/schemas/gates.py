from __future__ import annotations

from datetime import datetime, timezone

from pydantic import Field, field_validator

from opc.schemas.common import BaseSchema, Verdict

GATE_IDS = ("H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "S")


class CheckResult(BaseSchema):
    id: str
    status: Verdict
    detail: str = ""
    evidence_ref: str = ""


class GateReport(BaseSchema):
    """Uniform output of every hard gate (H1-H8) and the soft gate (S).

    Gates are veto-only devices: they answer 'may this instance enter the
    shared world', never 'what is true'. A gate with verdict != PASS blocks
    admission; INCONCLUSIVE never admits either.
    """

    gate: str
    verdict: Verdict
    checks: list[CheckResult] = Field(default_factory=list)
    instance_id: str = ""
    wave_id: str = ""
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_s: float = 0.0
    environment_fingerprint: str = ""
    artifacts: dict[str, str] = Field(default_factory=dict)

    @field_validator("gate")
    @classmethod
    def _gate(cls, v: str) -> str:
        if v not in GATE_IDS:
            raise ValueError(f"gate must be one of {GATE_IDS}, got {v!r}")
        return v

    @property
    def ok(self) -> bool:
        return self.verdict is Verdict.PASS


class AdmissionVerdict(BaseSchema):
    """Admit(instance) = H(instance) ^ S(instance). Both are veto devices."""

    admitted: bool
    hard_verdicts: dict[str, Verdict]
    soft_verdict: Verdict
    blocking_gates: list[str] = Field(default_factory=list)
    instance_id: str = ""
    wave_id: str = ""

    @classmethod
    def decide(
        cls,
        hard: dict[str, GateReport],
        soft: GateReport | None,
        required_hard: tuple[str, ...] = ("H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8"),
    ) -> "AdmissionVerdict":
        hard_verdicts: dict[str, Verdict] = {}
        blocking: list[str] = []
        for gate_id in required_hard:
            report = hard.get(gate_id)
            if report is None:
                hard_verdicts[gate_id] = Verdict.INCONCLUSIVE
                blocking.append(gate_id)
                continue
            hard_verdicts[gate_id] = report.verdict
            if not report.ok:
                blocking.append(gate_id)
        soft_verdict = soft.verdict if soft is not None else Verdict.INCONCLUSIVE
        if soft is None or not soft.ok:
            blocking.append("S")
        admitted = not blocking
        return cls(
            admitted=admitted,
            hard_verdicts=hard_verdicts,
            soft_verdict=soft_verdict,
            blocking_gates=sorted(set(blocking)),
            instance_id=next(iter(hard.values())).instance_id if hard else "",
            wave_id=next(iter(hard.values())).wave_id if hard else "",
        )
