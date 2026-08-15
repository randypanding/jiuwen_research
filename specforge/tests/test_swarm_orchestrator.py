"""WP10 contract-communication tests: full pipeline over fake ports.

Locks the Port protocols and the orchestrator state machine:
  happy path / gate rejection / differential defect / moderator routing /
  tier wiring enforcement / budget & event publication.
"""
import pytest

from specforge.metrics import HealthTracker
from specforge.swarm import (
    DeliveryOrchestrator,
    OrchestratorConfig,
    SpawnOrder,
    SwarmEvent,
    WiringError,
)
from specforge.swarm.ports import (
    GateRunOrder,
    InstanceOutput,
    ModerationDecision,
)
from specforge.wave import FakeInstancePort, WaveManager


class FakeBuilder:
    tier = "RU-M"

    def __init__(self, sources, oracle_results=None):
        self.sources = list(sources)
        self.oracle_results = oracle_results or [True] * len(sources)
        self.spawned: list[SpawnOrder] = []

    def spawn(self, order):
        self.spawned.append(order)
        idx = len(self.spawned) - 1
        return InstanceOutput(instance_id=order.instance_id,
                              source=self.sources[idx % len(self.sources)],
                              oracle_passed=self.oracle_results[idx % len(self.oracle_results)])


class FakeVerifier:
    def __init__(self, gate_results=None, differential=None):
        self.gate_results = gate_results or [{"gate_id": "h1", "verdict": "PASS"}]
        self.differential = differential
        self.calls = []

    def run_hard_gates(self, order: GateRunOrder):
        self.calls.append(("gates", order.instance_source))
        return {"results": [dict(g) for g in self.gate_results]}

    def run_differential(self, sources, spec_unit):
        self.calls.append(("diff", sources))
        return self.differential if self.differential is not None else {"verdict": "CLOSED"}


class FakeModerator:
    def __init__(self, route="admit-best-instance"):
        self.route_name = route
        self.routed = []

    def route(self, measurement):
        self.routed.append(measurement)
        return ModerationDecision(route=self.route_name, rationale="fake")


class FakeMessenger:
    def __init__(self):
        self.events: list[SwarmEvent] = []

    def publish(self, event):
        self.events.append(event)

    def history(self):
        return self.events


SPEC_UNIT = {"spec_id": "u.x", "r_level": "R0", "artifacts": ["a.py"]}
DELTA = {"spec_id": "u.x", "r_level": "R0", "risk": 0.1, "novelty": 0.1,
         "old_version": "1.0.0", "new_version": "1.1.0"}


@pytest.fixture
def world(tmp_path):
    wm = WaveManager(str(tmp_path / "waves"), FakeInstancePort(str(tmp_path / "inst")))
    return wm


def _orch(world, builder, verifier, moderator=None, messenger=None, cfg=None):
    return DeliveryOrchestrator(
        world, builder, verifier, moderator or FakeModerator(), messenger,
        config=cfg, health=HealthTracker())


def test_tier_wiring_enforced(world):
    with pytest.raises(WiringError):
        DeliveryOrchestrator(
            world, FakeBuilder([str(world.root)]), FakeVerifier(), FakeModerator(),
            config=OrchestratorConfig(judge_tier="RU-L"))


def test_happy_path_admits(world, tmp_path):
    src = tmp_path / "srcA"
    src.mkdir()
    builder = FakeBuilder([str(src)])
    orch = _orch(world, builder, FakeVerifier(),
                 messenger=FakeMessenger())
    out = orch.run_pipeline(SPEC_UNIT, DELTA)
    assert out["outcome"] == "admitted"
    assert out["receipt"]["receipt_hash"]
    assert world.ledger.verify_chain() == []
    assert orch.health.snapshot().admissions == 1


def test_seeds_platform_injected(world, tmp_path):
    src = tmp_path / "s"
    src.mkdir()
    builder = FakeBuilder([str(src), str(src), str(src)])
    from specforge.swarm import EarlyStopPolicy

    orch = _orch(world, builder, FakeVerifier(),
                 cfg=OrchestratorConfig(early_stop=EarlyStopPolicy(enabled=False)))
    orch.run_pipeline(SPEC_UNIT, {**DELTA, "risk": 0.9, "novelty": 0.9})
    seeds = [o.seed for o in builder.spawned]
    assert len(seeds) >= 3 and len(set(seeds)) == len(seeds), "seeds unique per builder"
    assert all(s is not None for s in seeds)
    assert all(o.context_id.startswith("builder::") for o in builder.spawned)


def test_gate_rejection_aborts_wave(world, tmp_path):
    src = tmp_path / "s"
    src.mkdir()
    verifier = FakeVerifier(gate_results=[{"gate_id": "h1", "verdict": "FAIL"}])
    orch = _orch(world, FakeBuilder([str(src)]), verifier)
    out = orch.run_pipeline(SPEC_UNIT, DELTA)
    assert out["outcome"] == "rejected"
    assert world.ledger.all() == []
    assert orch.health.snapshot().admissions == 0


def test_differential_defect_blocks_admission(world, tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    verifier = FakeVerifier(differential={"verdict": "DIFF_IN_UNDEFINED",
                                          "divergences": [{"input": {"x": 1}, "paths": ["sum"]}]})
    orch = _orch(world, FakeBuilder([str(a), str(b)]), verifier,
                 cfg=OrchestratorConfig())
    out = orch.run_pipeline(SPEC_UNIT, {**DELTA, "risk": 0.9, "novelty": 0.9})
    assert out["outcome"] == "differential-defect"
    assert world.ledger.all() == []


def test_silence_routes_to_moderator(world, tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    moderator = FakeModerator(route="spec-clarify")
    verifier = FakeVerifier(differential={"verdict": "SILENCE",
                                          "divergences": [{"input": {"x": 1}, "paths": ["log"]}]})
    orch = _orch(world, FakeBuilder([str(a), str(b)]), verifier, moderator)
    out = orch.run_pipeline(SPEC_UNIT, {**DELTA, "risk": 0.9, "novelty": 0.9})
    assert out["outcome"] == "moderated:spec-clarify"
    assert moderator.routed, "moderator must receive the measurement"
    assert world.ledger.all() == []


def test_events_published_in_order(world, tmp_path):
    src = tmp_path / "s"
    src.mkdir()
    msgr = FakeMessenger()
    orch = _orch(world, FakeBuilder([str(src)]), FakeVerifier(), messenger=msgr)
    orch.run_pipeline(SPEC_UNIT, DELTA)
    kinds = [e.kind for e in msgr.events]
    assert kinds[0] == "wave-begin"
    assert "spawn" in kinds and "gates" in kinds and "admit" in kinds


def test_early_stop_reduces_spawns(world, tmp_path):
    src = tmp_path / "s"
    src.mkdir()
    builder = FakeBuilder([str(src)] * 8)
    from specforge.swarm import EarlyStopPolicy

    orch = _orch(world, builder, FakeVerifier(),
                 cfg=OrchestratorConfig(early_stop=EarlyStopPolicy(k=2, enabled=True)))
    orch.run_pipeline(SPEC_UNIT, {**DELTA, "risk": 0.9, "novelty": 0.9})  # would spawn 6
    assert len(builder.spawned) == 2
