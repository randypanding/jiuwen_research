"""SpecForge: Spec-as-Source development swarm harness (PDR-001 implementation).

Layered per PLAN.md:
  spec/      L1/L2/L3 spec units, don't-care regions, R-levels, semver
  contracts/ public surface extraction + BC/NBC diff (H4 basis)
  gates/     admission algebra + H1..H8 mechanical oracles + statistics
  difftest/  N-instance differential measurement engine (H5)
  golden/    golden output store with manifest gate
  holdout/   private scenario store with information asymmetry
  judge/     LLM-as-judge workflow skeleton (soft gates S)
  wave/      wave transactions, admission, rollback
  receipt/   evidence receipts with hash chain
  metrics/   health metrics + human-facing report
  swarm/     orchestration state machine + openJiuwen wiring map
"""

__version__ = "0.1.0"
