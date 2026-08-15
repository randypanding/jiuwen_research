from __future__ import annotations

from swarm_kernel.contracts.drift import AnchorState
from swarm_kernel.contracts.spec import SpecDoc
from swarm_kernel.spec_repo.registry import ClauseRegistry, check_drift, scan_anchors


def test_scan_anchors(instance) -> None:
    anchors = scan_anchors(instance("good"))
    ids = {a[0] for a in anchors}
    assert ids == {"REQ-TOY-001", "REQ-TOY-002"}


def test_good_instance_no_drift(instance, spec_path) -> None:
    registry = ClauseRegistry(SpecDoc.model_validate_json(spec_path.read_text(encoding="utf-8")))
    records = check_drift(registry, instance("good"))
    assert all(r.state == AnchorState.OK for r in records)
    assert len(records) == 2


def test_stale_anchor_detected(instance, spec_path) -> None:
    registry = ClauseRegistry(SpecDoc.model_validate_json(spec_path.read_text(encoding="utf-8")))
    records = check_drift(registry, instance("drift_bad"))
    states = {r.clause_id: r.state for r in records}
    assert states["REQ-TOY-001"] == AnchorState.STALE
    assert states["REQ-TOY-002"] == AnchorState.OK


def test_orphan_anchor_detected(instance, spec_path, tmp_path) -> None:
    registry = ClauseRegistry(SpecDoc.model_validate_json(spec_path.read_text(encoding="utf-8")))
    rogue = tmp_path / "rogue.py"
    rogue.write_text("# @spec REQ-UNKNOWN-999 #abcdef0123456789\n", encoding="utf-8")
    records = check_drift(registry, tmp_path)
    states = {r.clause_id: r.state for r in records}
    assert states["REQ-UNKNOWN-999"] == AnchorState.ORPHAN
    assert states["REQ-TOY-001"] == AnchorState.UNIMPLEMENTED
    assert states["REQ-TOY-002"] == AnchorState.UNIMPLEMENTED


def test_l3_clause_needs_no_anchor(instance, spec_path) -> None:
    registry = ClauseRegistry(SpecDoc.model_validate_json(spec_path.read_text(encoding="utf-8")))
    assert not registry.requires_anchor("REQ-TOY-003")
    assert registry.requires_anchor("REQ-TOY-001")
