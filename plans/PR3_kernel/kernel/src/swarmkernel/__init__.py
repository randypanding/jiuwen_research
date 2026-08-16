"""swarmkernel — Spec-as-Source Agent Swarm kernel.

This package is the *mechanical* half of the paradigm fixed by PDR-001
(``structure.md``).  It deliberately contains **no LLM calls and no framework
imports**: every artefact here must be deterministic, offline-runnable and
unit-testable, because it is what the hard gates (H1-H8) are made of.

Layers
------
``swarmkernel.contracts``  Frozen data contracts exchanged between teams.
``swarmkernel.oracle``     Deterministic oracle engines (surface extraction,
                           differential comparison, don't-care normalisation,
                           golden outputs, traceability).
``swarmkernel.gates``      H1-H8 hard gates plus the admission algebra.
``swarmkernel.bus``        Contract bus + the information-asymmetry policy that
                           makes "builders never see the holdout" mechanical.
"""

__version__ = "0.1.0"

CONTRACT_MAJOR = 1
"""Current major version of the contract family. See docs/plan/02_契约总册.md."""
