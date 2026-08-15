"""WP8 tests: wave transactions (atomicity, rollback, frontier lock) + receipts."""
import pytest

from specforge.gates import GateResult
from specforge.wave import FakeInstancePort, FrontierLock, WaveError, WaveManager


def _passing():
    return [GateResult("h1", "PASS"), GateResult("h6", "PASS")]


def _failing():
    return [GateResult("h1", "FAIL", reason="compile error")]


@pytest.fixture
def wm(tmp_path):
    return WaveManager(str(tmp_path / "waves"), FakeInstancePort(str(tmp_path / "inst")))


def _delta():
    return {"spec_id": "u.x", "r_level": "R0", "risk": 0.2, "novelty": 0.1,
            "old_version": "1.0.0", "new_version": "1.1.0"}


def test_begin_register_admit(wm):
    wave = wm.begin(_delta())
    inst = wm.register_instance(wave.wave_id, source=str(wm.root))
    decision, receipt = wm.admit(wave.wave_id, inst.instance_id, _passing(),
                                 measurement={"verdict": "CLOSED"}, cost_usd=1.2)
    assert decision.admitted
    assert receipt is not None and receipt.receipt_hash
    rec = wm.load(wave.wave_id)
    assert rec.state == "COMMITTED"
    assert rec.admitted_instance == inst.instance_id
    assert wm.ledger.verify_chain() == []


def test_reject_leaves_world_untouched(wm):
    wave = wm.begin(_delta())
    inst = wm.register_instance(wave.wave_id, source=str(wm.root))
    decision, receipt = wm.admit(wave.wave_id, inst.instance_id, _failing())
    assert decision.decision == "REJECT"
    assert receipt is None
    rec = wm.load(wave.wave_id)
    assert rec.state == "OPEN"  # wave can still admit a different instance
    assert all(i.status != "ADMITTED" for i in rec.instances)
    assert wm.ledger.all() == []


def test_siblings_discarded_on_admit(wm):
    wave = wm.begin(_delta())
    wm.register_instance(wave.wave_id, source=str(wm.root), instance_id="a")
    wm.register_instance(wave.wave_id, source=str(wm.root), instance_id="b")
    wm.admit(wave.wave_id, "a", _passing())
    rec = wm.load(wave.wave_id)
    statuses = {i.instance_id: i.status for i in rec.instances}
    assert statuses == {"a": "ADMITTED", "b": "DISCARDED"}


def test_admit_closed_wave_raises(wm):
    wave = wm.begin(_delta())
    inst = wm.register_instance(wave.wave_id, source=str(wm.root))
    wm.admit(wave.wave_id, inst.instance_id, _passing())
    with pytest.raises(WaveError):
        wm.admit(wave.wave_id, inst.instance_id, _passing())


def test_rollback_reverts_and_marks_receipt(wm):
    wave = wm.begin(_delta())
    inst = wm.register_instance(wave.wave_id, source=str(wm.root))
    _, receipt = wm.admit(wave.wave_id, inst.instance_id, _passing())
    new_head = wm.rollback(wave.wave_id, reason="post-admission escape defect")
    assert new_head
    assert wm.load(wave.wave_id).state == "ROLLED_BACK"
    tail = wm.ledger.tail()
    assert tail.reverted and "escape" in tail.revert_reason
    assert wm.ledger.verify_chain() == []


def test_commit_failure_aborts_atomically(wm):
    wm.port.fail_commit = True
    wave = wm.begin(_delta())
    inst = wm.register_instance(wave.wave_id, source=str(wm.root))
    with pytest.raises(Exception):
        wm.admit(wave.wave_id, inst.instance_id, _passing())
    assert wm.load(wave.wave_id).state == "ABORTED"
    assert wm.ledger.all() == []  # no receipt for a failed commit


def test_frontier_lock_ttl_and_expiry(tmp_path):
    import time

    lock = FrontierLock(str(tmp_path / "frontier.lock"), ttl_s=0.2)
    lock.acquire()
    with pytest.raises(WaveError):
        FrontierLock(str(tmp_path / "frontier.lock"), ttl_s=60).acquire()
    time.sleep(0.25)  # expired
    FrontierLock(str(tmp_path / "frontier.lock"), ttl_s=60).acquire()
    # corrupt lock file expires immediately
    p = tmp_path / "frontier2.lock"
    p.write_text("garbage{", encoding="utf-8")
    FrontierLock(str(p), ttl_s=60).acquire()


def test_frontier_status(wm):
    s = wm.frontier_status()
    assert s["locked"] is False
    assert s["chain_errors"] == []
