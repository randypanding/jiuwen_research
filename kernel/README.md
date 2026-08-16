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
| Bus | `swarmkernel.bus` | **none** (pure stdlib) |

The judgment core — oracle engines, gates, the admission algebra — imports no
third-party library directly. Everything a CI run decides is decidable from
the standard library alone; pydantic only guards contract construction.

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
- `1` REJECTED — a definite failure was measured
- `2` INCONCLUSIVE — the instruments could not decide (retry or escalate)

## Development

Python `>=3.11,<3.14` (CI pins 3.12). Tests:

```bash
python -m pytest tests
```

Every test breaks exactly one thing and asserts exactly one gate fires.
