from __future__ import annotations

import hashlib
from typing import Callable, Optional

from pydantic import BaseModel

from swarmdev.admission.measurement import InstanceGateResult, Outcome, classify_fanout
from swarmdev.contracts import (
    ContractBus,
    EnvelopeKind,
    EvidenceReceipt,
    GateOutcome,
    RLevel,
    Role,
    SoftVerdict,
    SpecDoc,
    Wave,
    WaveState,
    WaveTask,
    make_token,
    new_id,
)
from swarmdev.contracts.receipt import DiscardedInstance, GateStatus


class BuiltInstance(BaseModel):
    instance_id: str
    instance_dir: str
    tier: str
    cost_tokens: int


GateRunResult = list[GateOutcome]


class WaveOutcome(BaseModel):
    wave_id: str
    final_state: WaveState
    receipts: list[EvidenceReceipt]
    outcomes: dict[str, str]
    admitted: bool


_DIFF_TEXT = {
    Outcome.CLOSED: "closed: passed instances behaviorally identical",
    Outcome.SILENCE: "silence: passed instances diverge in unspecified region",
    Outcome.DIVERGENCE: "divergence: mixed pass/fail across instances",
    Outcome.TIER_GAP: "tier_gap: base tier failed, higher tier passed",
    Outcome.SPEC_ORACLE_CONFLICT: "spec_oracle_conflict: all instances failed",
    Outcome.INSUFFICIENT: "insufficient: sample size below threshold",
}


class AdmissionOrchestrator:
    def __init__(
        self,
        builder_factory: Callable[[WaveTask, int], BuiltInstance],
        gate_executor: Callable[[BuiltInstance, WaveTask], list[GateOutcome]],
        soft_judge: Optional[Callable[[BuiltInstance, WaveTask], list[SoftVerdict]]] = None,
        drift_check: Optional[Callable[[], bool]] = None,
        bus: Optional[ContractBus] = None,
    ) -> None:
        self.builder_factory = builder_factory
        self.gate_executor = gate_executor
        self.soft_judge = soft_judge
        self.drift_check = drift_check
        self.bus = bus

    def execute_wave(self, wave: Wave, spec: SpecDoc, bundle_or_none=None) -> WaveOutcome:
        architect = make_token(Role.ARCHITECT, "architect", wave.wave_id)
        leader = make_token(Role.LEADER, "leader", wave.wave_id)
        verifier = make_token(Role.VERIFIER, "verifier", wave.wave_id)
        judge = make_token(Role.JUDGE, "judge", wave.wave_id)

        wave.transition(WaveState.COLLECTING)
        built_by_ru: dict[str, list[BuiltInstance]] = {}
        for task in wave.tasks:
            instances: list[BuiltInstance] = []
            for i in range(task.fanout.n_target):
                built = self.builder_factory(task, i)
                if self.bus is not None:
                    builder = make_token(Role.BUILDER, built.instance_id, wave.wave_id)
                    self.bus.publish(
                        architect, EnvelopeKind.SPEC_ASSIGNMENT,
                        {"spec_id": spec.spec_id, "version": spec.version,
                         "ru_id": task.ru_id, "l1_intent": spec.l1_intent},
                        [Role.BUILDER, Role.LEADER], trace_id=wave.wave_id)
                    self.bus.publish(
                        builder, EnvelopeKind.INSTANCE_SUBMISSION,
                        {"instance_id": built.instance_id, "ru_id": task.ru_id},
                        [Role.VERIFIER, Role.LEADER], trace_id=wave.wave_id)
                instances.append(built)
            built_by_ru[task.ru_id] = instances

        wave.transition(WaveState.ADJUDICATING)
        judged: list[dict] = []
        for task in wave.tasks:
            outcomes_by_instance: dict[str, list[GateOutcome]] = {}
            results: list[InstanceGateResult] = []
            ensemble_h5_fail = False
            for built in built_by_ru[task.ru_id]:
                outs = list(self.gate_executor(built, task))
                outcomes_by_instance[built.instance_id] = outs
                if task.r_level < RLevel.R3:
                    h5 = [o for o in outs if o.gate_id == "H5"]
                    if h5 and h5[0].status == GateStatus.FAIL:
                        ensemble_h5_fail = True
                    individual = [o for o in outs if o.gate_id != "H5"]
                else:
                    individual = list(outs)
                results.append(InstanceGateResult(
                    instance_id=built.instance_id,
                    gates_passed=all(o.status == GateStatus.PASS for o in individual),
                    tier=built.tier))

            passed_sigs: set[tuple] = set()
            for r in results:
                if r.gates_passed:
                    individual_outs = [
                        o for o in outcomes_by_instance[r.instance_id]
                        if not (o.gate_id == "H5" and task.r_level < RLevel.R3)
                    ]
                    passed_sigs.add(tuple(sorted(
                        (o.gate_id, o.details) for o in individual_outs
                    )))
            has_divergence = len(passed_sigs) > 1 or ensemble_h5_fail
            outcome = classify_fanout(results, has_divergence)

            built_map = {b.instance_id: b for b in built_by_ru[task.ru_id]}
            passed_ids = [r.instance_id for r in results if r.gates_passed]
            pool = passed_ids or [b.instance_id for b in built_by_ru[task.ru_id]]
            chosen_id = min(pool, key=lambda iid: (built_map[iid].cost_tokens, iid))

            task_ok = outcome == Outcome.CLOSED
            if task_ok and task.r_level >= RLevel.R3:
                # PDR-001 §5/R3：冻结制品逐行语义敏感，无 H5 差分/黄金输出见证不得准入
                task_ok = any(o.gate_id == "H5" and o.status == GateStatus.PASS
                              for o in outcomes_by_instance[chosen_id])

            if self.bus is not None:
                self.bus.publish(
                    verifier, EnvelopeKind.GATE_RESULTS,
                    {"wave_id": wave.wave_id, "ru_id": task.ru_id,
                     "gate_outcomes": {iid: [o.model_dump(mode="json") for o in outs]
                                       for iid, outs in outcomes_by_instance.items()}},
                    [Role.LEADER, Role.ARCHITECT], trace_id=wave.wave_id)
                self.bus.publish(
                    verifier, EnvelopeKind.MEASUREMENT_REPORT,
                    {"wave_id": wave.wave_id, "ru_id": task.ru_id,
                     "outcome": outcome.name, "has_divergence": has_divergence},
                    [Role.SPEC_MODERATOR, Role.ARCHITECT], trace_id=wave.wave_id)

            judged.append({
                "task": task,
                "results": results,
                "outcome": outcome,
                "outcomes_by_instance": outcomes_by_instance,
                "chosen": built_map[chosen_id],
                "task_ok": task_ok,
                "soft_verdicts": [],
            })

        admitted = bool(judged) and all(j["task_ok"] for j in judged)

        if admitted and self.soft_judge is not None:
            for j in judged:
                verdicts = list(self.soft_judge(j["chosen"], j["task"]))
                j["soft_verdicts"] = verdicts
                if self.bus is not None:
                    self.bus.publish(
                        verifier, EnvelopeKind.JUDGE_REQUEST,
                        {"wave_id": wave.wave_id, "ru_id": j["task"].ru_id,
                         "instance_id": j["chosen"].instance_id},
                        [Role.JUDGE], trace_id=wave.wave_id)
                    self.bus.publish(
                        judge, EnvelopeKind.JUDGE_VERDICT,
                        {"wave_id": wave.wave_id, "ru_id": j["task"].ru_id,
                         "verdicts": [sv.model_dump(mode="json") for sv in verdicts]},
                        [Role.VERIFIER, Role.LEADER], trace_id=wave.wave_id)
                if any(sv.judge.verdict == "veto" for sv in verdicts):
                    admitted = False

        drift_passed = True
        if admitted and self.drift_check is not None:
            drift_passed = bool(self.drift_check())
            admitted = drift_passed

        receipts: list[EvidenceReceipt] = []
        outcomes_map = {j["task"].ru_id: j["outcome"].name for j in judged}

        if admitted:
            wave.transition(WaveState.COMMITTING)
            for j in judged:
                task: WaveTask = j["task"]
                chosen: BuiltInstance = j["chosen"]
                commit_ref = "sha:" + hashlib.sha256(
                    chosen.instance_id.encode("utf-8")).hexdigest()[:12]
                receipt = EvidenceReceipt(
                    receipt_id=new_id("receipt"),
                    wave_id=wave.wave_id,
                    spec_id=spec.spec_id,
                    spec_delta_ref=task.spec_delta_ref,
                    r_level=task.r_level,
                    chosen_instance_id=chosen.instance_id,
                    discarded_instances=self._discarded(j, chosen.instance_id),
                    hard_gate_outcomes=j["outcomes_by_instance"][chosen.instance_id],
                    soft_verdicts=j["soft_verdicts"],
                    differential_conclusion=_DIFF_TEXT[j["outcome"]],
                    drift_check_passed=True,
                    admitted=True,
                    commit_ref=commit_ref,
                )
                receipts.append(receipt)
                if self.bus is not None:
                    self.bus.publish(
                        leader, EnvelopeKind.ADMISSION_RECEIPT,
                        {"wave_id": wave.wave_id, "ru_id": task.ru_id,
                         "receipt_id": receipt.receipt_id,
                         "chosen_instance_id": chosen.instance_id,
                         "commit_ref": commit_ref, "admitted": True},
                        [Role.LEADER, Role.ARCHITECT, Role.SPEC_STEWARD,
                         Role.MODERATOR, Role.HUMAN],
                        trace_id=wave.wave_id)
            wave.transition(WaveState.COMMITTED)
        else:
            wave.transition(WaveState.ROLLED_BACK)
            for j in judged:
                task = j["task"]
                chosen = j["chosen"]
                receipt = EvidenceReceipt(
                    receipt_id=new_id("receipt"),
                    wave_id=wave.wave_id,
                    spec_id=spec.spec_id,
                    spec_delta_ref=task.spec_delta_ref,
                    r_level=task.r_level,
                    chosen_instance_id=chosen.instance_id,
                    discarded_instances=self._discarded(j, chosen.instance_id),
                    hard_gate_outcomes=j["outcomes_by_instance"][chosen.instance_id],
                    soft_verdicts=j["soft_verdicts"],
                    differential_conclusion=_DIFF_TEXT[j["outcome"]],
                    drift_check_passed=drift_passed,
                    admitted=False,
                    commit_ref=None,
                    rollback_ref="rollback:" + wave.wave_id,
                )
                receipts.append(receipt)
                if self.bus is not None:
                    self.bus.publish(
                        leader, EnvelopeKind.ADMISSION_RECEIPT,
                        {"wave_id": wave.wave_id, "ru_id": task.ru_id,
                         "receipt_id": receipt.receipt_id,
                         "chosen_instance_id": chosen.instance_id,
                         "rollback_ref": receipt.rollback_ref, "admitted": False},
                        [Role.LEADER, Role.ARCHITECT, Role.SPEC_STEWARD,
                         Role.MODERATOR, Role.HUMAN],
                        trace_id=wave.wave_id)

        return WaveOutcome(
            wave_id=wave.wave_id,
            final_state=wave.state,
            receipts=receipts,
            outcomes=outcomes_map,
            admitted=admitted,
        )

    @staticmethod
    def _discarded(j: dict, chosen_id: str) -> list[DiscardedInstance]:
        outcome: Outcome = j["outcome"]
        discarded: list[DiscardedInstance] = []
        for r in j["results"]:
            if r.instance_id == chosen_id:
                continue
            # PDR-001 宪法不变量 2：被丢弃实例仍须留下其测量结论
            if r.gates_passed:
                conclusion = f"{outcome.name}: gates passed, discarded by admission selection"
            else:
                conclusion = f"{outcome.name}: gates failed, discarded"
            discarded.append(DiscardedInstance(
                instance_id=r.instance_id, measurement_conclusion=conclusion))
        return discarded
