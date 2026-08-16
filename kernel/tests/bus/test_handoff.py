"""Inter-contract communication: the full wave handoff, end to end.

This is the test that answers "do the contracts actually fit together?". It
drives one unit through the complete chain

    architect -> builder -> verifier -> judge -> leader

using only the bus, and asserts at every hop that (a) the payload arrived
intact, (b) the receiving role was allowed to see it, and (c) the artefacts that
must *not* have crossed the boundary did not.

The chain is deliberately built from the real contracts, not from stand-ins: a
handoff test that uses simplified messages proves nothing about the messages the
system will actually send.
"""

from __future__ import annotations

import pytest

from swarmkernel.bus import ContractBus, DeliveryError, seal
from swarmkernel.contracts.base import ArtifactClass, Role
from swarmkernel.contracts.gate import (
    GateId,
    GateResult,
    GateStatus,
    HardGateReport,
    JudgeSample,
    SoftGateResult,
    SoftVerdict,
)
from swarmkernel.contracts.instance import DivergenceVerdict
from swarmkernel.contracts.wave import EvidenceReceipt


class Mailbox:
    """Records what a participant actually received."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, object]] = []

    def __call__(self, envelope, contract) -> None:
        self.messages.append((envelope.header.contract_type, contract))

    def types(self) -> list[str]:
        return [t for t, _ in self.messages]

    def last(self):
        return self.messages[-1][1]


@pytest.fixture
def wired():
    """A bus with the five canonical participants subscribed."""

    bus = ContractBus()
    boxes = {name: Mailbox() for name in ("architect", "builder", "verifier", "judge", "leader")}
    bus.subscribe(
        "builder",
        Role.BUILDER,
        [
            ArtifactClass.SPEC_L2,
            ArtifactClass.SPEC_DELTA,
            ArtifactClass.ORACLE_PUBLIC,
            ArtifactClass.INTERFACE_SURFACE,
        ],
        boxes["builder"],
    )
    bus.subscribe(
        "verifier",
        Role.VERIFIER,
        [
            ArtifactClass.SPEC_L2,
            ArtifactClass.SPEC_DELTA,
            ArtifactClass.ORACLE_HOLDOUT,
            ArtifactClass.INSTANCE,
            ArtifactClass.INSTANCE_REPORT,
        ],
        boxes["verifier"],
    )
    bus.subscribe(
        "judge",
        Role.JUDGE,
        [ArtifactClass.INSTANCE_REPORT, ArtifactClass.GATE_REPORT, ArtifactClass.ORACLE_HOLDOUT],
        boxes["judge"],
    )
    bus.subscribe(
        "leader",
        Role.LEADER,
        [
            ArtifactClass.GATE_REPORT,
            ArtifactClass.EVIDENCE_RECEIPT,
            ArtifactClass.DIFFERENTIAL_REPORT,
        ],
        boxes["leader"],
    )
    bus.subscribe(
        "architect",
        Role.ARCHITECT,
        [ArtifactClass.GATE_REPORT, ArtifactClass.DIFFERENTIAL_REPORT],
        boxes["architect"],
    )
    return bus, boxes


# ------------------------------------------------------------ the full chain


def test_full_wave_handoff(
    wired, spec, additive_delta, public_oracle, holdout_oracle, three_agreeing_reports
):
    bus, boxes = wired

    # 1. architect publishes the L2 contract and the delta --------------------
    bus.publish(
        seal(
            message_id="m1",
            contract=spec,
            sender_role=Role.ARCHITECT,
            sender_identity="architect",
            wave_id="W1",
        )
    )
    bus.publish(
        seal(
            message_id="m2",
            contract=additive_delta,
            sender_role=Role.ARCHITECT,
            sender_identity="architect",
            wave_id="W1",
            causation_id="m1",
        )
    )
    assert "SpecDocument" in boxes["builder"].types()
    assert "SpecDelta" in boxes["builder"].types()

    # 2. verifier publishes the public oracle (builder may self-check) --------
    bus.publish(
        seal(
            message_id="m3",
            contract=public_oracle,
            sender_role=Role.VERIFIER,
            sender_identity="verifier",
            wave_id="W1",
        )
    )
    assert "PublicOracle" in boxes["builder"].types()

    # 3. the holdout reaches the judge but never the builder ------------------
    bus.publish(
        seal(
            message_id="m4",
            contract=holdout_oracle,
            sender_role=Role.VERIFIER,
            sender_identity="verifier",
            wave_id="W1",
        )
    )
    assert "HoldoutOracle" in boxes["judge"].types()
    assert "HoldoutOracle" not in boxes["builder"].types()

    # 4. the builder hands over the *artefact*, not the evidence ---------------
    #    A builder that could author its own InstanceReport would be grading its
    #    own exam, so the capability matrix gives it INSTANCE and nothing more.
    report = three_agreeing_reports[0]
    bus.send(
        seal(
            message_id="m5",
            contract=report.manifest,
            sender_role=Role.BUILDER,
            sender_identity="builder",
            recipient_role=Role.VERIFIER,
            recipient_identity="verifier",
            wave_id="W1",
            causation_id="m1",
        )
    )
    assert boxes["verifier"].types()[-1] == "InstanceManifest"
    assert boxes["verifier"].last().instance_id == report.manifest.instance_id

    # 4b. the verifier runs the probes and authors the evidence ---------------
    bus.publish(
        seal(
            message_id="m5b",
            contract=report,
            sender_role=Role.VERIFIER,
            sender_identity="verifier",
            wave_id="W1",
            causation_id="m5",
        )
    )
    assert "InstanceReport" in boxes["judge"].types()
    assert "InstanceReport" not in boxes["builder"].types()

    # 5. verifier publishes the hard gate report ------------------------------
    hard = HardGateReport(
        unit_id=report.manifest.unit_id,
        instance_id=report.manifest.instance_id,
        results=[GateResult(gate=g, status=GateStatus.PASS) for g in GateId if g.is_hard],
    )
    bus.publish(
        seal(
            message_id="m6",
            contract=hard,
            sender_role=Role.VERIFIER,
            sender_identity="verifier",
            wave_id="W1",
            causation_id="m5",
        )
    )
    assert "HardGateReport" in boxes["judge"].types()
    assert "HardGateReport" in boxes["leader"].types()
    assert "HardGateReport" not in boxes["builder"].types()

    # 6. judge returns a soft verdict -----------------------------------------
    soft = SoftGateResult(
        verdict=SoftVerdict.NO_VETO,
        samples=[JudgeSample(criterion_id="RC-READABILITY", verdict=SoftVerdict.NO_VETO)],
        judge_model_tier=3,
        builder_model_tier=2,
    )
    bus.publish(
        seal(
            message_id="m7",
            contract=soft,
            sender_role=Role.JUDGE,
            sender_identity="judge",
            wave_id="W1",
            causation_id="m6",
        )
    )
    # Nobody in this wiring subscribes to JUDGE_VERDICT, and that is correct:
    # the verdict goes to the admission transaction, not back to the workers.
    assert "SoftGateResult" not in boxes["builder"].types()

    # 7. verifier issues the evidence receipt ---------------------------------
    receipt = EvidenceReceipt(
        receipt_id="R1",
        wave_id="W1",
        unit_id=report.manifest.unit_id,
        r_level="R1",
        spec_id=spec.spec_id,
        spec_version=spec.version,
        delta_ids=[additive_delta.delta_id],
        selected_instance_id=report.manifest.instance_id,
        differential_report_id="DR-1",
        differential_verdict=DivergenceVerdict.CLOSED,
        hard_gate_digest=hard.digest(),
        soft_gate_digest=soft.digest(),
        drift_clean=True,
        admitted=True,
        produced_by=Role.VERIFIER,
    )
    bus.publish(
        seal(
            message_id="m8",
            contract=receipt,
            sender_role=Role.VERIFIER,
            sender_identity="verifier",
            wave_id="W1",
            causation_id="m7",
        )
    )
    assert boxes["leader"].types()[-1] == "EvidenceReceipt"
    assert boxes["leader"].last().admitted

    # the whole wave is reconstructible from the audit log
    wave_msgs = {r.message_id for r in bus.audit_log}
    assert wave_msgs == {f"m{i}" for i in range(1, 9)} | {"m5b"}


def test_payload_survives_the_wire_exactly(wired, spec):
    bus, boxes = wired
    env = seal(
        message_id="m1", contract=spec, sender_role=Role.ARCHITECT, sender_identity="architect"
    )
    bus.publish(env)
    received = boxes["builder"].last()
    assert received.digest() == spec.digest()
    assert received is not spec


def test_tampered_payload_is_rejected(wired, spec):
    bus, _ = wired
    env = seal(
        message_id="m1", contract=spec, sender_role=Role.ARCHITECT, sender_identity="architect"
    )
    env.payload["domain"] = "not-checkout"
    with pytest.raises(DeliveryError, match="tampered"):
        bus.publish(env)


def test_major_version_mismatch_is_refused(wired, spec):
    bus, _ = wired
    env = seal(
        message_id="m1", contract=spec, sender_role=Role.ARCHITECT, sender_identity="architect"
    )
    bumped = env.model_copy(
        update={"header": env.header.model_copy(update={"contract_version": "2.0.0"})}
    )
    with pytest.raises(DeliveryError, match="contract-major mismatch"):
        bus.publish(bumped)


def test_minor_version_difference_is_accepted(wired, spec):
    """Additive changes must not break existing consumers, or the versioning
    discipline buys nothing."""

    bus, boxes = wired
    env = seal(
        message_id="m1", contract=spec, sender_role=Role.ARCHITECT, sender_identity="architect"
    )
    bumped = env.model_copy(
        update={"header": env.header.model_copy(update={"contract_version": "1.9.3"})}
    )
    bus.publish(bumped)
    assert "SpecDocument" in boxes["builder"].types()


def test_unknown_contract_type_is_refused(wired, spec):
    bus, _ = wired
    env = seal(
        message_id="m1", contract=spec, sender_role=Role.ARCHITECT, sender_identity="architect"
    )
    forged = env.model_copy(
        update={"header": env.header.model_copy(update={"contract_type": "NotARealContract"})}
    )
    with pytest.raises(DeliveryError, match="unknown contract type"):
        bus.publish(forged)


def test_relabelling_an_artifact_class_is_refused(wired, holdout_oracle):
    """The attack: publish the holdout while calling it a public oracle."""

    bus, boxes = wired
    env = seal(
        message_id="m1",
        contract=holdout_oracle,
        sender_role=Role.VERIFIER,
        sender_identity="verifier",
    )
    forged = env.model_copy(
        update={
            "header": env.header.model_copy(update={"payload_class": ArtifactClass.ORACLE_PUBLIC})
        }
    )
    with pytest.raises(DeliveryError, match="does not match the declared class"):
        bus.publish(forged)
    assert "HoldoutOracle" not in boxes["builder"].types()


def test_send_fails_loudly_when_recipient_is_absent(wired, spec):
    bus, _ = wired
    with pytest.raises(DeliveryError, match="did not receive"):
        bus.send(
            seal(
                message_id="m1",
                contract=spec,
                sender_role=Role.ARCHITECT,
                sender_identity="architect",
                recipient_role=Role.BUILDER,
                recipient_identity="nobody",
            )
        )


def test_send_requires_an_explicit_recipient(wired, spec):
    bus, _ = wired
    with pytest.raises(DeliveryError, match="explicit recipient"):
        bus.send(
            seal(
                message_id="m1",
                contract=spec,
                sender_role=Role.ARCHITECT,
                sender_identity="architect",
            )
        )
