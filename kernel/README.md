# swarmkernel

Spec-as-Source Agent Swarm kernel: frozen data contracts, hard gates (H1–H8),
deterministic oracle engines and the information-asymmetry bus. No LLM calls,
no framework imports — everything here is deterministic, offline-runnable and
unit-testable.

## Layering and dependency policy (D21)

The package is deliberately layered, and so are its dependencies:

| Layer | Modules | Third-party deps |
|---|---|---|
| Contracts (data layer) | `swarmkernel.contracts` | `pydantic` (construction-time invariants), `PyYAML` (spec Markdown frontmatter only) |
| Oracle engines | `swarmkernel.oracle` | **none** (pure stdlib) |
| Gates + admission algebra | `swarmkernel.gates` | **none** (pure stdlib) |
| Bus | `swarmkernel.bus` | `pydantic`, via the `Contract` base class the envelopes carry |

The judgment core — oracle engines, gates, the admission algebra — imports no
third-party library directly. Everything a CI run decides is decidable from
the standard library alone; pydantic only guards contract construction (and,
through the shared `Contract` base, the bus envelopes that carry contracts).

## Kernel vs harness responsibilities

The kernel ships **pure functions and contracts only**. It never schedules,
never calls a model, never owns a process. Consumed by the harness layer:

- gate execution order — `GateRegistry.run_for_stage(ctx, stage)` provides the
  D17 policy (M0/M1 run-and-record, M2+ fail-fast by ascending cost); *when*
  and *with which stage* to call it is the harness's decision;
- fan-out orchestration — `FanoutPlan.decide()` is the closed decision
  function for N; dispatching the N builds and collecting their reports is
  harness work;
- the full wave pipeline — `WaveStatus`/`wave_transition` define and guard the
  six-state lifecycle; driving a wave through it is harness work.

## Naming aliases (D28)

The cross-plan consensus vocabulary for judge verdicts is PASS/VETO/ABSTAIN.
This kernel spells the affirmative `NO_VETO` — `SoftVerdict` deliberately has
no `PASS` member, so "the soft gate can admit something" is unrepresentable.
Integration mapping: consensus PASS ≡ `NO_VETO`, VETO ≡ `VETO`,
ABSTAIN ≡ `ABSTAIN`.

## Workspace layout (D26)

A swarm workspace uses four directories; the kernel maps onto them as:

```
spec/      human specs (Markdown + frontmatter, see contracts.spec_md)
           + machine contracts (canonical JSON + sha256)
oracle/    public/holdout oracle bundles, golden outputs, drift baselines
           (baseline and goldens stay external to the code they measure, D24;
            holdout lives in-repo with a routing deny until a second team
            consumes it, then moves to its own repository, D25)
harness/   adapters that drive builds, probes and model calls; owns
           .swarm/ state
.swarm/    wave manifests, evidence receipts, admission ledger (append-only)
```

## Admission exit codes (D7)

`swarmkernel decision.json` validates one `AdmissionDecision` and exits:

- `0` ADMITTED
- `1` REJECTED — a definite failure was measured; also the exit for a record
  that fails contract validation (a forged decision needs a human)
- `2` INCONCLUSIVE — the instruments could not decide (retry or escalate);
  also the exit for input that never produced a decision

## Development

Python `>=3.11,<3.14`; CI (`.github/workflows/kernel-ci.yml`) runs the matrix
3.11 / 3.12 / 3.13. Tests:

```bash
python -m pytest tests
```

Every test breaks exactly one thing and asserts exactly one gate fires. The
`meta`-marked tests are the oracle anti-vacuity proof: each hard gate must go
red on a mutation of exactly the defect class it claims to catch.
