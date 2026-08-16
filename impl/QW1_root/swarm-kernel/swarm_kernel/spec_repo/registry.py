from __future__ import annotations

import re
from pathlib import Path

from swarm_kernel.contracts.drift import AnchorRecord, AnchorState
from swarm_kernel.contracts.spec import SpecDoc

ANCHOR_RE = re.compile(r"@spec\s+([A-Za-z0-9][A-Za-z0-9_\-]*)\s+#([0-9a-f]{8,64})")


class ClauseRegistry:
    def __init__(self, spec: SpecDoc) -> None:
        self.spec = spec
        self._clauses = spec.clause_map()

    def digest_of(self, clause_id: str) -> str | None:
        clause = self._clauses.get(clause_id)
        return clause.digest() if clause else None

    def requires_anchor(self, clause_id: str) -> bool:
        clause = self._clauses.get(clause_id)
        return clause is not None and clause.level.value in ("L1", "L2")

    def anchor_expectations(self) -> dict[str, str]:
        return {cid: c.digest() for cid, c in self._clauses.items() if c.level.value in ("L1", "L2")}


def scan_anchors(root: str | Path, suffixes: tuple[str, ...] = (".py", ".ts", ".java", ".go", ".rs")) -> list[tuple[str, str, int, str]]:
    out: list[tuple[str, str, int, str]] = []
    root_path = Path(root)
    for fp in sorted(root_path.rglob("*")):
        if not fp.is_file() or fp.suffix not in suffixes:
            continue
        try:
            text = fp.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for idx, line in enumerate(text.splitlines(), start=1):
            m = ANCHOR_RE.search(line)
            if m:
                out.append((m.group(1), m.group(2), idx, str(fp)))
    return out


def check_drift(registry: ClauseRegistry, root: str | Path) -> list[AnchorRecord]:
    expectations = registry.anchor_expectations()
    records: list[AnchorRecord] = []
    seen_clauses: set[str] = set()
    for clause_id, anchor_hash, line, fp in scan_anchors(root):
        expected = registry.digest_of(clause_id)
        if expected is None:
            records.append(AnchorRecord(clause_id=clause_id, anchor_hash=anchor_hash, file=fp, line=line, state=AnchorState.ORPHAN))
            continue
        seen_clauses.add(clause_id)
        if expected.startswith(anchor_hash) or anchor_hash == expected:
            records.append(AnchorRecord(clause_id=clause_id, anchor_hash=anchor_hash, file=fp, line=line, state=AnchorState.OK, expected_hash=expected))
        else:
            records.append(AnchorRecord(clause_id=clause_id, anchor_hash=anchor_hash, file=fp, line=line, state=AnchorState.STALE, expected_hash=expected))
    for clause_id, expected in expectations.items():
        if clause_id not in seen_clauses:
            records.append(AnchorRecord(clause_id=clause_id, anchor_hash="", file="", state=AnchorState.UNIMPLEMENTED, expected_hash=expected))
    return records
