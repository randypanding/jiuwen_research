from __future__ import annotations

import json
import tempfile
from pathlib import Path

CALC_MAIN = '''"""Calculator instance.

spec-clause:CALC-CORE-001
spec-clause:CALC-CORE-002
"""
import json
import sys


def compute(op, a, b):
    if op == "add":
        return a + b
    if op == "sub":
        return a - b
    if op == "div":
        return {round_expr}
    raise ValueError("bad op")


def main():
    req = json.load(sys.stdin)
    print(json.dumps({{"result": compute(req["op"], req["a"], req["b"])}}))


if __name__ == "__main__":
    main()
'''

GOLDEN_PROBE = '''# spec-clause:CALC-ABI-003
import hashlib

ABI = "CALC-ABI-v1"


def abi_digest():
    return hashlib.sha256(ABI.encode()).hexdigest()[:16]


print(f"{ABI}:{abi_digest()}")
'''

SUITE_MANIFEST = {
    "schema_version": "1.0.0",
    "suite_id": "calc-holdout-suite",
    "entrypoint": "python3 {instance}/main.py",
    "holdout": True,
    "rotation_id": "rot-0001",
    "env_manifest": {"PYTHONHASHSEED": "0", "TZ": "UTC", "SEED": "42"},
    "scenarios": [
        {"id": "ho-add-basic", "kind": "json_assert", "input_file": "inputs/add.json", "expected": "{\"result\": 5}"},
        {"id": "ho-sub-basic", "kind": "json_assert", "input_file": "inputs/sub.json", "expected": "{\"result\": 1}"},
        {"id": "ho-div-exact", "kind": "stdout_regex", "input_file": "inputs/div_exact.json", "expected": "\"result\": 2(\\.0)?"},
        {"id": "ho-badop-exit", "kind": "exit_code", "input_file": "inputs/badop.json", "expected": "1"},
    ],
}


def _write_spec_repo(root: Path) -> None:
    (root / "constitution.md").write_text(
        "# Constitution (immutable invariants, natural language)\nspec is the only truth.\n", encoding="utf-8"
    )
    dom = root / "domains" / "calc"
    dom.mkdir(parents=True)
    spec = {
        "schema_version": "1.0.0",
        "domain": "calc",
        "version": 1,
        "intent": "A deterministic arithmetic service for the demo domain.",
        "clauses": [
            {
                "id": "CALC-CORE-001",
                "level": "L2",
                "statement": "compute(op,a,b) returns exact arithmetic results for add/sub.",
                "r_level": "R1",
                "witnesses": [
                    {"kind": "hard_gate", "ref": "H2"},
                    {"kind": "holdout_scenario", "ref": "ho-add-basic"},
                    {"kind": "holdout_scenario", "ref": "ho-sub-basic"},
                ],
            },
            {
                "id": "CALC-CORE-002",
                "level": "L2",
                "statement": "Division rounding mode is part of the contract.",
                "r_level": "R0",
                "witnesses": [{"kind": "holdout_scenario", "ref": "ho-div-exact"}],
            },
            {
                "id": "CALC-ABI-003",
                "level": "L2",
                "statement": "The ABI banner string is frozen (R3 golden).",
                "r_level": "R3",
                "witnesses": [{"kind": "hard_gate", "ref": "H5"}],
            },
        ],
        "dontcares": [],
    }
    (dom / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    registry = {
        "schema_version": "1.0.0",
        "artifacts": [
            {"path": "calc/", "r_level": "R1", "clauses": ["CALC-CORE-001", "CALC-CORE-002"]},
            {"path": "calc/golden_probe.py", "r_level": "R3", "clauses": ["CALC-ABI-003"], "golden_ref": "goldens/abi.golden"},
        ],
    }
    (root / "registry").mkdir(exist_ok=True)
    (root / "registry" / "artifacts.json").write_text(json.dumps(registry, indent=2), encoding="utf-8")


def _write_suite(root: Path) -> None:
    inputs = root / "inputs"
    inputs.mkdir(parents=True)
    (root / "suite.json").write_text(json.dumps(SUITE_MANIFEST, indent=2), encoding="utf-8")
    (inputs / "add.json").write_text(json.dumps({"op": "add", "a": 2, "b": 3}), encoding="utf-8")
    (inputs / "sub.json").write_text(json.dumps({"op": "sub", "a": 3, "b": 2}), encoding="utf-8")
    (inputs / "div_exact.json").write_text(json.dumps({"op": "div", "a": 4, "b": 2}), encoding="utf-8")
    (inputs / "badop.json").write_text(json.dumps({"op": "mul", "a": 1, "b": 1}), encoding="utf-8")


def _write_instance(root: Path, *, round_expr: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "main.py").write_text(CALC_MAIN.format(round_expr=round_expr), encoding="utf-8")
    (root / "golden_probe.py").write_text(GOLDEN_PROBE, encoding="utf-8")


def run_selftest(verbose: bool = False) -> int:
    from swarmfoundry.gates.context import GateContext
    from swarmfoundry.gates.runner import GateRunner, build_receipt, register_receipt
    from swarmfoundry.schema.envelope import METHOD_ADMISSION_DECISION, SwarmEnvelope
    from swarmfoundry.schema.judge import JudgeVerdict
    from swarmfoundry.schema.receipt import EvidenceReceipt
    from swarmfoundry.specrepo.loader import SpecRepo
    from swarmfoundry.specrepo.seal import reseal

    def log(msg: str) -> None:
        if verbose:
            print(msg)

    checks = 0
    failures: list[str] = []

    def check(name: str, cond: bool) -> None:
        nonlocal checks
        checks += 1
        log(f"[{'OK' if cond else 'FAIL'}] {name}")
        if not cond:
            failures.append(name)

    with tempfile.TemporaryDirectory(prefix="swarmfoundry-selftest-") as td:
        td = Path(td)
        spec_root = td / "specrepo"
        spec_root.mkdir()
        _write_spec_repo(spec_root)
        repo = SpecRepo(spec_root)
        check("spec repo validates", repo.validate_all() == [])
        reseal(repo)
        check("seals recorded", bool(repo.load_seals()))

        holdout_dir = td / "holdout" / "calc"
        _write_suite(holdout_dir)

        inst_a = td / "instances" / "inst-a"
        inst_b = td / "instances" / "inst-b"
        _write_instance(inst_a, round_expr="round(a / b, 6)")
        _write_instance(inst_b, round_expr="round(a / b, 6)")

        goldens = td / "goldens"
        goldens.mkdir()
        import subprocess as _sp

        probe_out = _sp.run(["python3", str(inst_a / "golden_probe.py")], capture_output=True, text=True).stdout
        (goldens / "abi.golden").write_text(probe_out, encoding="utf-8")
        (goldens / "abi.r3info").write_text(
            json.dumps({"clause_ids": ["CALC-ABI-003"], "redactions": [], "approval_history": []}), encoding="utf-8"
        )

        judges = [
            JudgeVerdict(judge_id="judge-1", model_family="familyX", verdict="no_veto", reasons="clean", evidence_refs=("h1",)),
            JudgeVerdict(judge_id="judge-2", model_family="familyY", verdict="no_veto", reasons="clean", evidence_refs=("h2",)),
        ]

        from swarmfoundry.contracts.extract import dump_surface, extract_surface

        baseline_path = td / "baseline" / "calc.surface.json"
        dump_surface(extract_surface(inst_a, module="calc"), baseline_path)

        base_config = {
            "gates": {
                "H2": {"commands": [["python3", "-c", "print('unit tests ok')"]]},
                "H8": {"max_total_tokens": 1000000},
            }
        }
        ctx = GateContext(
            instance_dir=inst_a,
            instance_id="inst-a",
            spec_repo=repo,
            config=base_config,
            r_level="R1",
            baseline_surface_path=baseline_path,
            holdout_dirs=(holdout_dir,),
            sibling_instances=(inst_b,),
            diff_suite_dir=holdout_dir,
            judge_verdicts=tuple(judges),
            builder_model_family="familyZ",
            golden_checks=({"name": "abi-banner", "golden": str(goldens / "abi.golden"), "argv": ["python3", "golden_probe.py"]},),
        )
        decision = GateRunner().decide(ctx)
        check("identical twins admitted (all H + S pass)", decision.admitted)
        check("eight hard gates ran", len(decision.hard_results) == 8)

        receipt = build_receipt(
            wave_id="wave-selftest", spec_delta_id="delta-selftest", ctx=ctx, decision=decision, diff_conclusion="equivalent"
        )
        rpath = register_receipt(receipt, td / "receipts")
        reparsed = EvidenceReceipt.from_dict(json.loads(rpath.read_text(encoding="utf-8")))
        check("receipt roundtrip", reparsed.instance_id == "inst-a" and reparsed.admission.admitted)

        inst_c = td / "instances" / "inst-c"
        _write_instance(inst_c, round_expr="int(a / b)")
        ctx2 = GateContext(
            instance_dir=inst_c,
            instance_id="inst-c",
            spec_repo=repo,
            config=base_config,
            r_level="R0",
            holdout_dirs=(holdout_dir,),
            sibling_instances=(inst_a,),
            diff_suite_dir=holdout_dir,
            judge_verdicts=tuple(judges),
            builder_model_family="familyZ",
        )
        decision2 = GateRunner().decide(ctx2)
        h5 = next(g for g in decision2.hard_results if g.gate_id == "H5")
        check("divergent twin blocked by H5 (spec silence)", not decision2.admitted and h5.status == "fail")

        ctx3 = GateContext(
            instance_dir=inst_c,
            instance_id="inst-c",
            spec_repo=repo,
            config={
                "gates": {
                    "H2": {"commands": [["python3", "-c", "print('unit tests ok')"]]},
                    "H5": {"dontcare_paths": ["result"]},
                }
            },
            r_level="R0",
            holdout_dirs=(holdout_dir,),
            sibling_instances=(inst_a,),
            diff_suite_dir=holdout_dir,
            judge_verdicts=tuple(judges),
            builder_model_family="familyZ",
        )
        decision3 = GateRunner().decide(ctx3)
        check("registered dontcare restores admission", decision3.admitted)

        ctx4 = GateContext(
            instance_dir=inst_a,
            instance_id="inst-a-norepo",
            spec_repo=None,
            config=base_config,
            r_level="R0",
            holdout_dirs=(holdout_dir,),
            judge_verdicts=tuple(judges),
            builder_model_family="familyZ",
        )
        decision4 = GateRunner().decide(ctx4)
        check("missing spec repo fails closed (H7)", not decision4.admitted)

        ctx5 = GateContext(
            instance_dir=inst_a,
            instance_id="inst-a-noholdout",
            spec_repo=repo,
            config=base_config,
            r_level="R0",
            holdout_dirs=(),
            judge_verdicts=tuple(judges),
            builder_model_family="familyZ",
        )
        decision5 = GateRunner().decide(ctx5)
        check("missing holdout fails closed (H3)", not decision5.admitted)

        self_review = judges + [
            JudgeVerdict(judge_id="judge-3", model_family="familyZ", verdict="no_veto", reasons="self", evidence_refs=())
        ]
        ctx6 = GateContext(
            instance_dir=inst_a,
            instance_id="inst-a-selfreview",
            spec_repo=repo,
            config={"gates": {"S": {"min_valid_verdicts": 3}}},
            r_level="R0",
            holdout_dirs=(holdout_dir,),
            judge_verdicts=tuple(self_review),
            builder_model_family="familyZ",
        )
        decision6 = GateRunner().decide(ctx6)
        check("self-review invalidated and fails closed (S)", not decision6.admitted)

        veto = [
            JudgeVerdict(judge_id="judge-1", model_family="familyX", verdict="veto", reasons="design smell", evidence_refs=()),
            JudgeVerdict(judge_id="judge-2", model_family="familyY", verdict="no_veto", reasons="ok", evidence_refs=()),
        ]
        ctx7 = GateContext(
            instance_dir=inst_a,
            instance_id="inst-a-veto",
            spec_repo=repo,
            config=base_config,
            r_level="R0",
            holdout_dirs=(holdout_dir,),
            judge_verdicts=tuple(veto),
            builder_model_family="familyZ",
        )
        decision7 = GateRunner().decide(ctx7)
        check("single judge veto blocks admission", not decision7.admitted)

        env = SwarmEnvelope(
            envelope_id="env-selftest",
            sender_role="verifier",
            recipient_role="leader",
            method=METHOD_ADMISSION_DECISION,
            payload=decision.to_dict(),
        )
        check("admission envelope roundtrip", SwarmEnvelope.from_dict(env.to_dict()).method == METHOD_ADMISSION_DECISION)

        from swarmfoundry.schema.envelope import ProtocolViolation, assert_information_asymmetry

        try:
            assert_information_asymmetry(
                SwarmEnvelope(
                    envelope_id="env-bad",
                    sender_role="verifier",
                    recipient_role="builder",
                    method=METHOD_ADMISSION_DECISION,
                    payload={},
                )
            )
            leak_blocked = False
        except ProtocolViolation:
            leak_blocked = True
        check("information asymmetry blocks verdict leak to builder", leak_blocked)

    log(f"selftest: {checks - len(failures)}/{checks} checks passed")
    if failures:
        for f in failures:
            print(f"SELFTTEST FAILURE: {f}")
        return 1
    return 0
