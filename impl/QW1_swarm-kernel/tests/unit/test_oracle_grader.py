from __future__ import annotations

import pytest

from swarm_kernel.oracle.grader import ScenarioGrader, load_scenarios


def test_load_scenarios(oracle_dir) -> None:
    scenarios = load_scenarios(oracle_dir)
    ids = [s.scenario_id for s in scenarios]
    assert ids == ["S-CLAMP-001", "S-CLAMP-002", "S-CLAMP-003", "S-CLAMP-004"]
    assert all(s.confidentiality.value == "holdout" for s in scenarios)


def test_good_instance_passes_suite(oracle_dir, instance) -> None:
    grader = ScenarioGrader(load_scenarios(oracle_dir))
    outcomes, ok = grader.grade(instance("good"))
    assert ok
    assert all(o.first_attempt for o in outcomes)


def test_bad_instance_fails_boundary_scenario(oracle_dir, instance) -> None:
    grader = ScenarioGrader(load_scenarios(oracle_dir))
    outcomes, ok = grader.grade(instance("bad"))
    assert not ok
    failed = [o.scenario_id for o in outcomes if not o.passed]
    assert "S-CLAMP-003" in failed


def test_missing_entry_is_error(oracle_dir, tmp_path) -> None:
    grader = ScenarioGrader(load_scenarios(oracle_dir))
    with pytest.raises(Exception):
        grader.grade(tmp_path)
