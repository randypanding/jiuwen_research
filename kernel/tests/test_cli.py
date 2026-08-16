"""The CLI adapter: three-state exit contract for CI (D7)."""

from __future__ import annotations

import json

from swarmkernel.cli import main
from swarmkernel.contracts.gate import GateId, GateStatus
from swarmkernel.contracts.spec import RLevel
from swarmkernel.gates.algebra import decide

from .gates.test_algebra import HARD, all_pass, result


def decision_payload(**kwargs) -> str:
    d = decide(
        unit_id="U",
        instance_id="i",
        r_level=kwargs.pop("r_level", RLevel.R1),
        results=kwargs.pop("results", all_pass()),
        soft=None,
        **kwargs,
    )
    return d.model_dump_json()


def test_admitted_exits_zero(tmp_path, capsys):
    path = tmp_path / "d.json"
    path.write_text(decision_payload(), encoding="utf-8")
    assert main([str(path)]) == 0
    assert "admitted" in capsys.readouterr().out


def test_rejected_exits_one(tmp_path):
    results = [
        result(g, GateStatus.FAIL if g is GateId.H1_BUILD else GateStatus.PASS)
        for g in HARD
    ]
    path = tmp_path / "d.json"
    path.write_text(decision_payload(results=results), encoding="utf-8")
    assert main([str(path)]) == 1


def test_inconclusive_exits_two(tmp_path):
    path = tmp_path / "d.json"
    path.write_text(decision_payload(soft_required=True), encoding="utf-8")
    assert main([str(path)]) == 2


def test_unreadable_input_is_inconclusive_not_rejected(tmp_path):
    """A forged decision is not a rejection: nothing was measured. CI re-queues
    instead of paging a human to fix a ghost defect."""

    path = tmp_path / "d.json"
    path.write_text('{"admitted": "yes, trust me"}', encoding="utf-8")
    assert main([str(path)]) == 2
