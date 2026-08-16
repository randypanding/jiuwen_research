"""CI adapter for admission decisions — the three-state exit contract (D7).

The console script declared in ``pyproject.toml`` reads one
``AdmissionDecision`` JSON document (file argument or stdin), validates it
through the contract — so a forged or algebra-violating record dies here —
and exits with:

* ``0`` ADMITTED
* ``1`` REJECTED — a definite failure was measured; fix it. A record that
  fails contract validation (a forged decision) also exits 1: that needs a
  human, not a retry.
* ``2`` INCONCLUSIVE — the instruments could not decide; retry or escalate.
  Input that never produced a decision (unreadable file, malformed JSON,
  wrong usage) exits 2 as well: there is nothing to fix, only to re-run.

CI treats 2 differently from 1: an inconclusive run re-queues instead of
paging a human to "fix" a defect nobody measured.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from pydantic import ValidationError

from .contracts.gate import AdmissionDecision, AdmissionOutcome

__all__ = ["main", "decide_exit_code"]


def decide_exit_code(decision: AdmissionDecision) -> int:
    """Pure mapping so the exit contract itself is unit-testable."""

    return decision.exit_code


def _load(payload: dict[str, Any]) -> AdmissionDecision:
    return AdmissionDecision.model_validate(payload)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) > 1:
        print("usage: swarmkernel [decision.json]", file=sys.stderr)
        return 2
    try:
        raw = open(argv[0], encoding="utf-8").read() if argv else sys.stdin.read()
    except OSError as exc:
        # No decision ever existed: inconclusive (retry), not rejected.
        print(f"swarmkernel: cannot read decision: {exc}", file=sys.stderr)
        return 2
    try:
        decision = _load(json.loads(raw))
    except ValidationError as exc:
        # A record that fails contract validation — including a forged or
        # algebra-violating one — needs a human, not a retry: exit 1.
        print(f"swarmkernel: decision failed contract validation: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:  # malformed JSON
        print(f"swarmkernel: cannot parse decision: {exc}", file=sys.stderr)
        return 2
    code = decide_exit_code(decision)
    outcome = decision.outcome or AdmissionOutcome.REJECTED
    reasons = "; ".join(f.code for f in decision.reasons) or "-"
    print(
        f"{decision.unit_id}/{decision.instance_id}: "
        f"{outcome.value} (exit {code}) — {reasons}"
    )
    return code


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
