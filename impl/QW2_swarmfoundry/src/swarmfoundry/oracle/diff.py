from __future__ import annotations

import json
from pathlib import Path

from swarmfoundry.schema.diff import DIVERGENT, EQUIVALENT, INCONCLUSIVE, DiffReport, Divergence
from swarmfoundry.schema.oracle import ScenarioSuite
from swarmfoundry.oracle.runner import run_entrypoint


def _normalize(text: str):
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        return None


def _walk_diff(path: str, a, b, out: list[Divergence], input_id: str) -> None:
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            p = f"{path}.{k}" if path else k
            if k not in b:
                out.append(Divergence(input_id, p, repr(a[k]), "<absent>"))
            elif k not in a:
                out.append(Divergence(input_id, p, "<absent>", repr(b[k])))
            else:
                _walk_diff(p, a[k], b[k], out, input_id)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(Divergence(input_id, path, f"len={len(a)}", f"len={len(b)}"))
        for i, (x, y) in enumerate(zip(a, b)):
            _walk_diff(f"{path}[{i}]", x, y, out, input_id)
    elif a != b or type(a) is not type(b):
        out.append(Divergence(input_id, path, repr(a)[:200], repr(b)[:200]))


def diff_instances(
    suite: ScenarioSuite,
    suite_dir: Path,
    instance_a: Path,
    instance_b: Path,
    dontcare_paths: tuple[str, ...] = (),
) -> DiffReport:
    """H5 instrument: same inputs into two instances; behavioral divergences are
    spec silence until adjudicated. dontcare_paths (dot paths) are registered
    freedoms and excluded from divergence accounting."""
    suite_dir = Path(suite_dir)
    divergences: list[Divergence] = []
    inconclusive_reasons: list[str] = []
    run = 0
    for sc in suite.scenarios:
        input_path = suite_dir / sc.input_file
        if not input_path.is_file():
            inconclusive_reasons.append(f"missing input {sc.input_file}")
            continue
        input_text = input_path.read_text(encoding="utf-8")
        try:
            out_a = run_entrypoint(suite, instance_a, input_text, sc.timeout_s)
            out_b = run_entrypoint(suite, instance_b, input_text, sc.timeout_s)
        except Exception as e:
            inconclusive_reasons.append(f"{sc.id}: execution error {e}")
            continue
        run += 1
        if out_a.exit_code != out_b.exit_code:
            divergences.append(Divergence(sc.id, "exit_code", str(out_a.exit_code), str(out_b.exit_code)))
            continue
        na, nb = _normalize(out_a.stdout), _normalize(out_b.stdout)
        if na is None or nb is None:
            if out_a.stdout.strip() != out_b.stdout.strip():
                divergences.append(Divergence(sc.id, "stdout", out_a.stdout[:200], out_b.stdout[:200]))
        else:
            local: list[Divergence] = []
            _walk_diff("", na, nb, local, sc.id)
            for d in local:
                if any(d.path == p or d.path.startswith(p + ".") or d.path.startswith(p + "[") for p in dontcare_paths):
                    continue
                divergences.append(d)
    if inconclusive_reasons and not divergences and run == 0:
        return DiffReport(
            instance_a=str(instance_a),
            instance_b=str(instance_b),
            inputs_run=run,
            equivalence=INCONCLUSIVE,
            note="; ".join(inconclusive_reasons),
        )
    equivalence = EQUIVALENT if not divergences else DIVERGENT
    note = "; ".join(inconclusive_reasons) if inconclusive_reasons else ""
    return DiffReport(
        instance_a=str(instance_a),
        instance_b=str(instance_b),
        inputs_run=run,
        equivalence=equivalence,
        divergences=tuple(divergences),
        note=note,
    )
