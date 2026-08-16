"""WP12: end-to-end dogfood run over the demo_adder unit (real components).

Covers cross-WP contract communication with REAL implementations:
spec parser -> linter -> gates (H1/H6/H7 real subprocess) -> difftest (real
subprocess instances) -> measurement -> wave admission -> receipt chain ->
health report.
"""
from __future__ import annotations

from pathlib import Path

from specforge.contracts import extract_file
from specforge.difftest import (
    DivergenceCorpus,
    NormalizeRules,
    generate_inputs,
    run_instance,
    run_measurement,
)
from specforge.gates import GateContext, H1BuildGate, H6GuardrailGate, H7DriftGate
from specforge.gates.base import GateVerdict, decide_admission, run_suite
from specforge.holdout import HoldoutScenario, HoldoutStore
from specforge.metrics import HealthTracker, render_human_report
from specforge.spec import compute_delta, parse_spec
from specforge.wave import FakeInstancePort, WaveManager

REPO = Path(__file__).resolve().parents[1]
DEMO = REPO / "examples" / "demo_adder"


def run_demo(tmp_root: Path | None = None) -> dict:
    import tempfile

    tmp = Path(tmp_root or tempfile.mkdtemp(prefix="sfdemo-"))

    # 1) parse + lint spec
    unit = parse_spec(path=str(DEMO / "spec.md"))
    from specforge.spec import lint_spec
    from tests.conftest import GATE_IDS, HOLDOUT_IDS

    rep = lint_spec(unit, gate_ids=GATE_IDS, holdout_ids=HOLDOUT_IDS)
    assert rep.ok, [str(e) for e in rep.errors]

    # 2) build an "instance" = project tree containing the good implementation
    inst = tmp / "instance"
    pkg = inst / "demo_adder"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "good.py").write_text((DEMO / "good.py").read_text(encoding="utf-8"),
                                 encoding="utf-8")
    (pkg / "broken.py").write_text((DEMO / "broken.py").read_text(encoding="utf-8"),
                                   encoding="utf-8")
    tests = inst / "tests"
    tests.mkdir()
    (tests / "test_adder.py").write_text(
        (DEMO / "tests" / "test_adder.py").read_text(encoding="utf-8"), encoding="utf-8")

    # 3) hard gates on the instance (H1 real, H6 real, H7 real)
    ctx = GateContext(instance_path=str(inst), world_path=str(inst), spec_unit=unit,
                      surface_new=extract_file(pkg / "good.py", "good"))
    suite = run_suite(ctx, [H1BuildGate(), H6GuardrailGate(), H7DriftGate(min_coverage=0.99)])
    hard = {r.gate_id: r.verdict for r in suite.results}
    decision = decide_admission(suite.results, [])
    assert decision.admitted, decision.reasons

    # 4) holdout evaluation (verifier side; aggregate only)
    store = HoldoutStore(tmp / "holdout")
    for sid, a, b, expect in [("h-neg", -2, 3, 1), ("h-pos", 2, 3, 5), ("h-zero", 0, 0, 0)]:
        store.add_scenario(HoldoutScenario(sid, "adder-basic", "io", payload={
            "cmd": ["python", "-c",
                    "import sys, json; sys.path.insert(0, '.'); "
                    "from demo_adder.good import run; "
                    "print(json.dumps(run(**json.load(sys.stdin))))"],
            "input": {"a": a, "b": b}, "expect": {"sum": expect}}))

    runner = None  # use store default runner (cmd protocol via stdin/stdout)
    score = store.evaluate(str(inst), "adder-basic", runner=runner)
    assert score.aggregate == 1.0

    # 5) calibration pipeline B: differential good vs broken (all discarded)
    # NOTE: sys.path must point at the PARENT of the demo_adder package dir.
    good_cmd = ["python", "-c",
                "import sys, json; sys.path.insert(0, %r); "
                "from demo_adder.good import run; "
                "print(json.dumps(run(**json.load(sys.stdin))))" % str(inst)]
    broken_cmd = ["python", "-c",
                  "import sys, json; sys.path.insert(0, %r); "
                  "from demo_adder.broken import run; "
                  "print(json.dumps(run(**json.load(sys.stdin))))" % str(inst)]
    schema = {"a": {"type": "int", "min": -20, "max": 20},
              "b": {"type": "int", "min": -20, "max": 20}}
    inputs = generate_inputs(schema, seed=20260815, n=40)
    rules = NormalizeRules(strip_fields=["debug_log"])
    from specforge.difftest import InstanceRecords

    recs_g = InstanceRecords("good", run_instance(good_cmd, inputs, cwd=str(pkg)))
    recs_b = InstanceRecords("broken", run_instance(broken_cmd, inputs, cwd=str(pkg)))
    dc = {d.region: d.kind for d in unit.dont_cares}
    m = run_measurement([recs_g, recs_b], rules=rules, dc_regions=dc)
    corpus = DivergenceCorpus(tmp / "corpus")
    for d in m.divergences:
        corpus.add(unit.spec_id, d.input, d.paths, m.verdict)
    assert m.verdict in ("SILENCE", "SILENCE_DC", "DIFF_IN_UNDEFINED")
    assert m.divergences, "broken instance must be caught by differential"

    # 6) wave admission (delivery path, single good instance)
    wm = WaveManager(str(tmp / "waves"), FakeInstancePort(str(tmp / "wt")))
    delta = compute_delta(None, unit, risk=0.1, novelty=0.1)
    wave = wm.begin(delta)
    irec = wm.register_instance(wave.wave_id, source=str(inst))
    adm, receipt = wm.admit(wave.wave_id, irec.instance_id, suite.results,
                            measurement={"verdict": "CLOSED"}, cost_usd=0.42)
    assert adm.admitted and receipt
    assert wm.ledger.verify_chain() == []

    # 7) health snapshot + human report
    tracker = HealthTracker()
    from specforge.metrics import WaveMetrics

    tracker.record_wave(WaveMetrics(wave_id=wave.wave_id, spec_id=unit.spec_id,
                                    n_instances=2, measurement_verdict=m.verdict,
                                    divergences=len(m.divergences), admitted=True,
                                    cost_usd=0.42))
    rep2 = tracker.snapshot(clause_coverage=1.0)
    report = render_human_report(rep2, l1_l2_matters=["adder L1.1 witness coverage ok"])
    assert "health score" in report

    return {"ok": True, "hard": hard, "holdout": score.aggregate,
            "measurement": m.verdict, "divergences": len(m.divergences),
            "admission": adm.decision, "chain": wm.ledger.verify_chain() == [],
            "health": rep2.health_score}


def test_demo_e2e(tmp_path):
    result = run_demo(tmp_path)
    assert result["ok"]
    assert result["hard"]["h1"] == GateVerdict.PASS
    assert result["hard"]["h6"] == GateVerdict.PASS
    assert result["hard"]["h7"] == GateVerdict.PASS
    assert result["holdout"] == 1.0
    assert result["admission"] == "ADMIT"
    assert result["chain"] is True


def test_demo_breaks_when_instance_has_backdoor(tmp_path):
    """H6 catches a hardcoded secret planted in the instance tree."""
    unit = parse_spec(path=str(DEMO / "spec.md"))
    inst = tmp_path / "evil"
    pkg = inst / "demo_adder"
    pkg.mkdir(parents=True)
    src = (DEMO / "good.py").read_text(encoding="utf-8")
    (pkg / "good.py").write_text(src + '\nAPI_KEY = "sk-1234567890abcdef1234"\n',
                                 encoding="utf-8")
    ctx = GateContext(instance_path=str(inst), world_path=".", spec_unit=unit)
    res = H6GuardrailGate().run(ctx)
    assert res.verdict == GateVerdict.FAIL
    assert any(f["kind"] == "hardcoded_secret" for f in res.evidence["findings"])
