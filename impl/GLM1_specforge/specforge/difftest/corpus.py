"""Divergence corpus: delta-diversity regression inputs (research: NEZHA).

Inputs that revealed divergence are persisted and replayed on future waves,
so discovered spec-silence is never lost.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class DivergenceCorpus:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def add(self, spec_id: str, input_obj: dict[str, Any], paths: list[str], verdict: str) -> None:
        entry = {"input": input_obj, "paths": paths, "verdict": verdict}
        p = self.root / f"{spec_id}.jsonl"
        existing = self.load(spec_id)
        for e in existing:
            if e["input"] == input_obj:
                return  # dedupe
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def load(self, spec_id: str) -> list[dict[str, Any]]:
        p = self.root / f"{spec_id}.jsonl"
        if not p.exists():
            return []
        out = []
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
        return out

    def inputs(self, spec_id: str) -> list[dict[str, Any]]:
        return [e["input"] for e in self.load(spec_id)]
