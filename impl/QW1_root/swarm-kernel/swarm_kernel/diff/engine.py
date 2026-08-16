from __future__ import annotations

import importlib.util
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from swarm_kernel.oracle.grader import load_instance_adapter


@dataclass
class DiffReport:
    corpus_size: int
    seed: int
    divergent: bool
    divergent_inputs: list[dict[str, Any]] = field(default_factory=list)
    pairwise: dict[str, list[int]] = field(default_factory=dict)


def canonicalize(value: Any, redactions: tuple[str, ...] = ()) -> str:
    def scrub(v: Any) -> Any:
        if isinstance(v, dict):
            return {k: scrub(x) for k, x in v.items() if k not in redactions}
        if isinstance(v, list):
            return [scrub(x) for x in v]
        if isinstance(v, float):
            return round(v, 9)
        return v

    return json.dumps(scrub(value), sort_keys=True, ensure_ascii=False, default=str, separators=(",", ":"))


def load_corpus_generator(oracle_dir: str | Path) -> Callable[[int, int], list[dict[str, Any]]]:
    fp = Path(oracle_dir) / "corpus.py"
    if not fp.exists():
        raise FileNotFoundError(f"oracle dir {oracle_dir} lacks corpus.py")
    spec = importlib.util.spec_from_file_location(f"oracle_corpus_{Path(oracle_dir).name}", fp)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load corpus.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if not hasattr(module, "gen_corpus"):
        raise AttributeError("corpus.py must define gen_corpus(seed, n)")
    return module.gen_corpus


def run_differential(
    instance_dirs: list[str | Path],
    oracle_dir: str | Path,
    seed: int = 42,
    corpus_size: int = 50,
    redactions: tuple[str, ...] = (),
) -> DiffReport:
    gen = load_corpus_generator(oracle_dir)
    corpus = gen(seed, corpus_size)
    runners = [(str(d), load_instance_adapter(d)) for d in instance_dirs]
    traces: dict[str, list[str]] = {}
    raw_inputs: list[dict[str, Any]] = []
    for inputs in corpus:
        raw_inputs.append(inputs)
    for name, run in runners:
        outputs = []
        for inputs in corpus:
            try:
                outputs.append(canonicalize(run(dict(inputs)), redactions))
            except Exception as e:
                outputs.append(f"<error:{type(e).__name__}>")
        traces[name] = outputs
    names = [n for n, _ in runners]
    pairwise: dict[str, list[int]] = {}
    divergent_idx: set[int] = set()
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            key = f"{Path(names[i]).name}|{Path(names[j]).name}"
            diffs = [idx for idx in range(corpus_size) if traces[names[i]][idx] != traces[names[j]][idx]]
            pairwise[key] = diffs
            divergent_idx.update(diffs)
    return DiffReport(
        corpus_size=corpus_size,
        seed=seed,
        divergent=bool(divergent_idx),
        divergent_inputs=[raw_inputs[i] for i in sorted(divergent_idx)][:20],
        pairwise=pairwise,
    )
