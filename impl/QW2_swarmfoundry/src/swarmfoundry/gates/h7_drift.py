from __future__ import annotations

from swarmfoundry.schema.gates import GATE_H7, GateResult, STATUS_FAIL, STATUS_PASS
from swarmfoundry.gates.base import Gate
from swarmfoundry.gates.context import GateContext
from swarmfoundry.specrepo.seal import seal_domain

TRACE_TAG = "spec-clause:"


class H7DriftGate(Gate):
    """H7: spec<->code drift detection (mechanical part of the reconciler).
    Two checks:
      1. seal drift: recomputed clause seals differ from the recorded seals —
         the spec changed without going through the sanctioned re-seal channel.
      2. trace drift: every normative clause with a mechanical witness must be
         anchored in the instance by a `spec-clause:<ID>` trace tag; a missing
         anchor means code no longer testifies for the clause."""

    gate_id = GATE_H7

    def run(self, ctx: GateContext) -> GateResult:
        if ctx.spec_repo is None:
            return GateResult(self.gate_id, STATUS_FAIL, evidence=["no spec repo bound to gate context"])
        evidence: list[str] = []
        failed = False

        recorded = ctx.spec_repo.load_seals()
        for dom in ctx.spec_repo.list_domains():
            spec = ctx.spec_repo.load_domain(dom)
            current = seal_domain(spec)
            baseline = recorded.get(dom, {})
            for cid, h in current.items():
                if baseline.get(cid) not in (None, h):
                    failed = True
                    evidence.append(f"seal drift: clause {cid} changed without sanctioned re-seal")
            for cid in set(baseline) - set(current):
                failed = True
                evidence.append(f"seal drift: clause {cid} removed without sanctioned re-seal")

        cfg = ctx.gate_config(self.gate_id)
        if cfg.get("require_trace_tags", True):
            corpus = self._read_corpus(ctx)
            for dom in ctx.spec_repo.list_domains():
                spec = ctx.spec_repo.load_domain(dom)
                for c in spec.clauses:
                    if c.level == "L3" or not c.has_mechanical_witness():
                        continue
                    tag = f"{TRACE_TAG}{c.id}"
                    if tag not in corpus:
                        failed = True
                        evidence.append(f"trace drift: clause {c.id} has no '{tag}' anchor in instance")
        if not failed:
            evidence.append("no drift detected")
        return GateResult(
            gate_id=self.gate_id,
            status=STATUS_FAIL if failed else STATUS_PASS,
            evidence=tuple(evidence[:80]),
        )

    @staticmethod
    def _read_corpus(ctx: GateContext) -> str:
        parts: list[str] = []
        for p in ctx.instance_dir.rglob("*"):
            if p.is_file() and p.suffix in (".py", ".md", ".json", ".yaml", ".yml", ".toml", ".txt"):
                try:
                    parts.append(p.read_text(encoding="utf-8", errors="replace"))
                except OSError:
                    continue
        return "\n".join(parts)
