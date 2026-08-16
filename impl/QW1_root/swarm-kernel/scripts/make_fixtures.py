from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from swarm_kernel.contracts.spec import (
    DontCareDeclaration,
    DontCareKind,
    MachineContract,
    SpecClause,
    SpecDoc,
    SpecLevel,
    RLevel,
    WitnessKind,
)

ROOT = Path(__file__).resolve().parents[1] / "fixtures"


def build_spec() -> SpecDoc:
    dc = DontCareDeclaration(
        dont_care_id="dc-clamp-order",
        kind=DontCareKind.OUTPUT_FREEDOM,
        scope="clamp(x, lo, hi) when lo > hi",
        description="result is free when bounds are inverted; any deterministic value within implementation choice is allowed",
    )
    c1 = SpecClause(
        clause_id="REQ-TOY-001",
        level=SpecLevel.L1,
        r_level=RLevel.R1,
        title="clamp keeps values inside the requested range",
        text="For downstream callers, clamp(x, lo, hi) must never return a value outside [lo, hi] when lo <= hi.",
        witness_kind=WitnessKind.HOLDOUT,
        witness_refs=["S-CLAMP-001", "S-CLAMP-002", "S-CLAMP-003"],
    )
    c2 = SpecClause(
        clause_id="REQ-TOY-002",
        level=SpecLevel.L2,
        r_level=RLevel.R1,
        title="clamp contract surface",
        text="Export a single function clamp(x, lo, hi). post: lo <= result <= hi when lo <= hi; result == x when lo <= x <= hi.",
        contract_body=MachineContract(
            pre=["lo <= hi"],
            post=["lo <= result <= hi", "lo <= x <= hi implies result == x"],
            invariants=["pure function, no side effects"],
        ),
        dont_care=[dc],
        witness_kind=WitnessKind.MECHANICAL,
        witness_refs=["H3", "H4"],
    )
    c3 = SpecClause(
        clause_id="REQ-TOY-003",
        level=SpecLevel.L3,
        r_level=RLevel.R0,
        title="implementation notes",
        text="Any pure implementation is acceptable; min/max composition or branch form both allowed.",
        witness_kind=WitnessKind.MECHANICAL,
        witness_refs=["H2"],
    )
    return SpecDoc(spec_id="toy-clamp", spec_version="1.0.0", clauses=[c1, c2, c3])


SCENARIOS_YAML = """scenarios:
  - scenario_id: S-CLAMP-001
    title: value inside range unchanged
    inputs: {x: 5, lo: 0, hi: 10}
    expectation: {equals: 5}
    grading: FAIL_TO_PASS
    tags: [core]
  - scenario_id: S-CLAMP-002
    title: below range clamps to lo
    inputs: {x: -3, lo: 0, hi: 10}
    expectation: {equals: 0}
    grading: FAIL_TO_PASS
    tags: [boundary]
  - scenario_id: S-CLAMP-003
    title: above range clamps to hi
    inputs: {x: 17, lo: 0, hi: 10}
    expectation: {equals: 10}
    grading: FAIL_TO_PASS
    tags: [boundary]
  - scenario_id: S-CLAMP-004
    title: boundary value hi preserved
    inputs: {x: 10, lo: 0, hi: 10}
    expectation: {equals: 10}
    grading: PASS_TO_PASS
    tags: [regression]
"""

CORPUS_PY = """from __future__ import annotations

import random


def gen_corpus(seed: int, n: int) -> list[dict]:
    rng = random.Random(seed)
    corpus = []
    for i in range(n):
        lo = rng.randint(-5, 5)
        hi = lo + rng.randint(0, 6)
        if i % 7 == 0:
            lo, hi = hi, lo
        x = rng.randint(-12, 12)
        corpus.append({"x": x, "lo": lo, "hi": hi})
    return corpus
"""

BASELINE_CONTRACT = {"exports": ["clamp"], "signatures": {"clamp": "(x, lo, hi)"}, "dependencies": []}

BUILDER_TESTS = """from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from clamp_impl import clamp


def test_inside_range():
    assert clamp(5, 0, 10) == 5


def test_result_within_bounds():
    for x in (-100, -3, 0, 7, 10, 17):
        assert 0 <= clamp(x, 0, 10) <= 10
"""

ENTRY_TEMPLATE = """from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from clamp_impl import clamp


def run(inputs: dict):
    return clamp(inputs["x"], inputs["lo"], inputs["hi"])
"""

IMPL_GOOD = """from __future__ import annotations


{anchors}
def clamp(x, lo, hi):
    if lo > hi:
        return lo
    return max(lo, min(x, hi))
"""

IMPL_GOOD2 = """from __future__ import annotations


{anchors}
def clamp(x, lo, hi):
    if lo > hi:
        return lo
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x
"""

IMPL_BAD = """from __future__ import annotations


{anchors}
def clamp(x, lo, hi):
    if lo > hi:
        return lo
    if x > hi:
        return hi - 1
    return max(lo, min(x, hi))
"""

IMPL_DIVERGENT_LO = """from __future__ import annotations


{anchors}
def clamp(x, lo, hi):
    if lo > hi:
        return lo
    return max(lo, min(x, hi))
"""

IMPL_DIVERGENT_HI = """from __future__ import annotations


{anchors}
def clamp(x, lo, hi):
    if lo > hi:
        return hi
    return max(lo, min(x, hi))
"""

IMPL_SECRET = """from __future__ import annotations

API_KEY = "sk-abcdefghijklmnopqrstuvwxyz1234567890"


{anchors}
def clamp(x, lo, hi):
    if lo > hi:
        return lo
    return max(lo, min(x, hi))
"""


def write_instance(root: Path, impl: str, anchors: str, contract: dict | None = None, report: dict | None = None, extra: dict[str, str] | None = None) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "swarm_entry.py").write_text(ENTRY_TEMPLATE, encoding="utf-8")
    (root / "clamp_impl.py").write_text(impl.format(anchors=anchors), encoding="utf-8")
    surface = dict(BASELINE_CONTRACT) if contract is None else contract
    (root / "contract.json").write_text(json.dumps(surface, indent=2), encoding="utf-8")
    (root / "report.json").write_text(json.dumps(report or {"tokens": 1200, "seconds": 12, "bytes": 2048}, indent=2), encoding="utf-8")
    tests_dir = root / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "test_clamp.py").write_text(BUILDER_TESTS, encoding="utf-8")
    for name, content in (extra or {}).items():
        (root / name).write_text(content, encoding="utf-8")


def main() -> None:
    spec = build_spec()
    spec_dir = ROOT / "spec"
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "spec.json").write_text(spec.model_dump_json(indent=2), encoding="utf-8")

    oracle = ROOT / "oracle"
    (oracle / "scenarios").mkdir(parents=True, exist_ok=True)
    (oracle / "scenarios" / "toy.yaml").write_text(SCENARIOS_YAML, encoding="utf-8")
    (oracle / "corpus.py").write_text(CORPUS_PY, encoding="utf-8")
    (oracle / "baseline_contract.json").write_text(json.dumps(BASELINE_CONTRACT, indent=2), encoding="utf-8")

    c1, c2 = spec.clauses[0], spec.clauses[1]
    anchors_full = f"# @spec {c1.clause_id} #{c1.digest()[:16]}\n# @spec {c2.clause_id} #{c2.digest()[:16]}\n"
    anchors_stale = f"# @spec {c1.clause_id} #{'0' * 16}\n# @spec {c2.clause_id} #{c2.digest()[:16]}\n"

    inst = ROOT / "instances"
    write_instance(inst / "good", IMPL_GOOD, anchors_full)
    write_instance(inst / "good2", IMPL_GOOD2, anchors_full)
    write_instance(inst / "bad", IMPL_BAD, anchors_full)
    write_instance(inst / "divergent_a", IMPL_DIVERGENT_LO, anchors_full)
    write_instance(inst / "divergent_b", IMPL_DIVERGENT_HI, anchors_full)
    write_instance(inst / "drift_bad", IMPL_GOOD, anchors_stale)
    write_instance(inst / "secret_bad", IMPL_SECRET, anchors_full)
    write_instance(inst / "budget_bad", IMPL_GOOD, anchors_full, report={"tokens": 9_000_000, "seconds": 12, "bytes": 2048})
    write_instance(
        inst / "surface_bad",
        IMPL_GOOD,
        anchors_full,
        contract={"exports": [], "signatures": {}, "dependencies": []},
    )
    print(f"fixtures written to {ROOT}")


if __name__ == "__main__":
    main()
