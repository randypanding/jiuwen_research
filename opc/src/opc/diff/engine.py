from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any

from opc.oracle.scenarios import invoke_entrypoint, redact
from opc.schemas.common import Verdict, sha256_hex
from opc.schemas.diff import DiffReport, Divergence, InstanceRun


def flatten_json(obj: Any, prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            flat.update(flatten_json(value, path))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            flat.update(flatten_json(value, f"{prefix}[{index}]"))
    else:
        flat[prefix or "$"] = obj
    return flat


def _hash_of(value: Any) -> str:
    return sha256_hex(json.dumps(value, sort_keys=True, default=str, ensure_ascii=False).encode("utf-8"))


class DiffEngine:
    """H5: behavioural differential over same-source instances.

    Measurement semantics (PDR-001 section 6):
      * all pass + empty diff            -> spec closed w.r.t. the oracle
      * all pass + divergence            -> spec silence (don't-care ruling needed)
      * partial pass/fail                -> spec ambiguity (moderator converges spec)
      * fewer than min_instances run well-> information insufficient, INCONCLUSIVE
    """

    def __init__(self, timeout_s: float = 30.0, python_executable: str | None = None):
        self.timeout_s = timeout_s
        self.python = python_executable

    def run(
        self,
        instances: dict[str, str | Path],
        entrypoint: str,
        corpus: dict[str, dict[str, Any]],
        redactions: list[str] | None = None,
        dont_care_scopes: list[str] | None = None,
        min_instances: int = 3,
    ) -> DiffReport:
        redactions = redactions or []
        dont_care_scopes = dont_care_scopes or []
        runs: list[InstanceRun] = []
        outputs: dict[str, dict[str, Any]] = {}

        for instance_id, instance_dir in instances.items():
            instance_dir = str(Path(instance_dir).resolve())
            outputs[instance_id] = {}
            for input_id, inputs in corpus.items():
                result, err = invoke_entrypoint(
                    instance_dir, entrypoint, inputs, self.timeout_s, self.python
                )
                if err:
                    runs.append(
                        InstanceRun(
                            instance_id=instance_id,
                            input_id=input_id,
                            status=Verdict.FAIL,
                            timed_out=err == "timeout",
                            exit_code=None,
                        )
                    )
                    continue
                norm = redact(result, redactions)
                outputs[instance_id][input_id] = norm
                runs.append(
                    InstanceRun(
                        instance_id=instance_id,
                        input_id=input_id,
                        status=Verdict.PASS,
                        output_hash=_hash_of(norm),
                        normalized_output=norm if isinstance(norm, dict) else {"$": norm},
                    )
                )

        divergences: list[Divergence] = []
        for input_id in corpus:
            eligible = [i for i in instances if input_id in outputs.get(i, {})]
            for a, b in itertools.combinations(sorted(eligible), 2):
                flat_a = flatten_json(outputs[a][input_id])
                flat_b = flatten_json(outputs[b][input_id])
                for path in sorted(set(flat_a) | set(flat_b)):
                    value_a = flat_a.get(path)
                    value_b = flat_b.get(path)
                    if value_a == value_b:
                        continue
                    divergences.append(
                        Divergence(
                            input_id=input_id,
                            instance_a=a,
                            instance_b=b,
                            field_path=path,
                            value_a=repr(value_a)[:200],
                            value_b=repr(value_b)[:200],
                            in_dont_care_scope=self._in_dont_care(path, dont_care_scopes),
                        )
                    )

        healthy_instances = {
            r.instance_id
            for r in runs
            if r.status is Verdict.PASS
        }
        all_runs_ok = len(runs) == len(instances) * len(corpus) and all(
            r.status is Verdict.PASS for r in runs
        )
        constrained_divergences = [d for d in divergences if not d.in_dont_care_scope]
        dont_care_count = len(divergences) - len(constrained_divergences)

        if len(healthy_instances) < min_instances:
            verdict, note = Verdict.INCONCLUSIVE, (
                f"information insufficient: only {len(healthy_instances)} healthy instances "
                f"(< {min_instances}); regenerate before judging"
            )
        elif not all_runs_ok:
            verdict, note = Verdict.INCONCLUSIVE, "some runs crashed or timed out; measurement incomplete"
        elif constrained_divergences:
            verdict, note = Verdict.FAIL, (
                f"{len(constrained_divergences)} divergence(s) in constrained region: "
                "spec silence or ambiguity candidate, route to spec moderator"
            )
        else:
            verdict, note = Verdict.PASS, "no divergence outside registered don't-care scopes"

        return DiffReport(
            instance_ids=sorted(instances),
            corpus_id="",
            runs=runs,
            divergences=divergences,
            verdict=verdict,
            all_pass_and_empty_diff=all_runs_ok and not divergences,
            dont_care_divergences=dont_care_count,
            note=note,
        )

    @staticmethod
    def _in_dont_care(path: str, scopes: list[str]) -> bool:
        for scope in scopes:
            if path == scope or path.startswith(scope + ".") or path.startswith(scope + "["):
                return True
        return False
