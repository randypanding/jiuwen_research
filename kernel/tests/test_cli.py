"""The CLI adapter: three-state exit contract for CI (D7)."""

from __future__ import annotations

from swarmkernel.cli import main
from swarmkernel.contracts.gate import GateId, GateStatus
from swarmkernel.contracts.oracle import JudgeProtocol
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
    path.write_text(
        decision_payload(
            judge_protocol=JudgeProtocol(required_for_admission=True)
        ),
        encoding="utf-8",
    )
    assert main([str(path)]) == 2


def test_a_forged_decision_exits_one(tmp_path):
    """A record that fails contract validation needs a human, not a retry:
    exit 1, so CI pages instead of re-queueing a fabricated document."""

    path = tmp_path / "d.json"
    path.write_text('{"admitted": "yes, trust me"}', encoding="utf-8")
    assert main([str(path)]) == 1


def test_malformed_json_exits_two(tmp_path):
    """No decision ever existed: inconclusive (re-run), not rejected."""

    path = tmp_path / "d.json"
    path.write_text("not json at all", encoding="utf-8")
    assert main([str(path)]) == 2


def test_missing_file_exits_two(tmp_path):
    assert main([str(tmp_path / "nope.json")]) == 2
