from __future__ import annotations

from pathlib import Path

from swarmfoundry.schema.gates import GATE_H3, GateResult, STATUS_FAIL, STATUS_PASS
from swarmfoundry.gates.base import Gate
from swarmfoundry.gates.context import GateContext
from swarmfoundry.oracle.runner import load_suite, run_suite


class H3HoldoutGate(Gate):
    """H3: holdout scenario suites (oracle body, L1 intent). Runs every suite in
    ctx.holdout_dirs against the instance. Also performs the mechanical part of
    information asymmetry: if the instance text contains holdout suite/scenario
    ids, the builder saw material it must not see -> fail."""

    gate_id = GATE_H3

    def run(self, ctx: GateContext) -> GateResult:
        if not ctx.holdout_dirs:
            return GateResult(
                gate_id=self.gate_id,
                status=STATUS_FAIL,
                evidence=["no holdout suites provided; a gate without oracle cannot admit"],
            )
        evidence: list[str] = []
        failed = False
        holdout_ids: set[str] = set()
        for suite_dir in ctx.holdout_dirs:
            suite_dir = Path(suite_dir)
            suite = load_suite(suite_dir)
            holdout_ids.add(suite.suite_id)
            holdout_ids.update(sc.id for sc in suite.scenarios)
            results = run_suite(suite, ctx.instance_dir, suite_dir)
            passed = sum(1 for r in results if r.passed)
            evidence.append(f"suite {suite.suite_id}: {passed}/{len(results)} scenarios passed")
            for r in results:
                if not r.passed:
                    failed = True
                    evidence.append(f"  FAIL {r.scenario_id}: {r.detail[:200]}")
        leak_hits = self._scan_leaks(ctx.instance_dir, holdout_ids)
        if leak_hits:
            failed = True
            evidence.append(f"holdout leak: instance references holdout identifiers {leak_hits[:5]}")
        return GateResult(
            gate_id=self.gate_id,
            status=STATUS_FAIL if failed else STATUS_PASS,
            evidence=tuple(evidence),
            details={"suites": len(ctx.holdout_dirs), "leak_hits": len(leak_hits)},
        )

    @staticmethod
    def _scan_leaks(instance_dir: Path, holdout_ids: set[str]) -> list[str]:
        hits: set[str] = set()
        for p in Path(instance_dir).rglob("*"):
            if not p.is_file() or p.suffix not in (".py", ".json", ".md", ".txt", ".toml", ".yaml", ".yml"):
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for hid in holdout_ids:
                if hid and hid in text:
                    hits.add(hid)
        return sorted(hits)
