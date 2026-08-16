import sys

from swarmdev.contracts import HoldoutScenario
from swarmdev.contracts.oracle import Expectation
from swarmdev.oracle import ScenarioRunner


def test_exit_code_and_stdout_regex(tmp_path):
    (tmp_path / "say.py").write_text("print('ok-42')\n")
    scenario = HoldoutScenario(
        scenario_id="SCN-1",
        spec_clause_ids=["CL-A1"],
        title="say",
        run_command=f"{sys.executable} say.py",
        expectation=Expectation(exit_code=0, stdout_regex=r"ok-\d+"),
    )
    result = ScenarioRunner().run(scenario, tmp_path)
    assert result.passed
    assert result.exit_code == 0
    assert "ok-42" in result.stdout
    assert result.duration_s >= 0


def test_exit_code_mismatch_fails(tmp_path):
    (tmp_path / "say.py").write_text("print('hi')\n")
    scenario = HoldoutScenario(
        scenario_id="SCN-2",
        spec_clause_ids=["CL-A1"],
        title="say",
        run_command=f"{sys.executable} say.py",
        expectation=Expectation(exit_code=1),
    )
    result = ScenarioRunner().run(scenario, tmp_path)
    assert not result.passed
    assert "exit_code" in result.details


def test_stdout_regex_mismatch_fails(tmp_path):
    (tmp_path / "say.py").write_text("print('hello')\n")
    scenario = HoldoutScenario(
        scenario_id="SCN-3",
        spec_clause_ids=[],
        title="say",
        run_command=f"{sys.executable} say.py",
        expectation=Expectation(exit_code=0, stdout_regex=r"^goodbye$"),
    )
    result = ScenarioRunner().run(scenario, tmp_path)
    assert not result.passed
    assert "stdout" in result.details


def test_stderr_regex_checked(tmp_path):
    (tmp_path / "warn.py").write_text("import sys\nsys.stderr.write('warning: disk low\\n')\n")
    scenario = HoldoutScenario(
        scenario_id="SCN-ERR",
        spec_clause_ids=[],
        title="warn",
        run_command=f"{sys.executable} warn.py",
        expectation=Expectation(exit_code=0, stderr_regex=r"warning: \w+ \w+"),
    )
    assert ScenarioRunner().run(scenario, tmp_path).passed


def test_files_exist_and_files_contain(tmp_path):
    (tmp_path / "writer.py").write_text(
        "from pathlib import Path\nPath('out.txt').write_text('result=7')\n"
    )
    scenario = HoldoutScenario(
        scenario_id="SCN-4",
        spec_clause_ids=[],
        title="write",
        run_command=f"{sys.executable} writer.py",
        expectation=Expectation(
            exit_code=0,
            files_exist=["out.txt"],
            files_contain={"out.txt": r"result=\d+"},
        ),
    )
    assert ScenarioRunner().run(scenario, tmp_path).passed

    (tmp_path / "writer_bad.py").write_text(
        "from pathlib import Path\nPath('out.txt').write_text('nope')\n"
    )
    bad = scenario.model_copy(
        update={"scenario_id": "SCN-4b", "run_command": f"{sys.executable} writer_bad.py"}
    )
    result = ScenarioRunner().run(bad, tmp_path)
    assert not result.passed
    assert "out.txt" in result.details


def test_timeout_counts_as_fail(tmp_path):
    (tmp_path / "slow.py").write_text("import time\ntime.sleep(3)\n")
    scenario = HoldoutScenario(
        scenario_id="SCN-5",
        spec_clause_ids=[],
        title="slow",
        run_command=f"{sys.executable} slow.py",
        timeout_s=0.5,
    )
    result = ScenarioRunner().run(scenario, tmp_path)
    assert not result.passed
    assert "timeout" in result.details
    assert result.exit_code is None


def test_setup_commands_and_env_merge(tmp_path):
    (tmp_path / "show_env.py").write_text("import os\nprint(os.environ['GREETING'])\n")
    scenario = HoldoutScenario(
        scenario_id="SCN-6",
        spec_clause_ids=[],
        title="env",
        setup_commands=[
            f"{sys.executable} -c \"from pathlib import Path; Path('data.txt').write_text('seed-1')\""
        ],
        run_command=f"{sys.executable} show_env.py",
        env={"GREETING": "hello-holdout"},
        expectation=Expectation(
            exit_code=0,
            stdout_regex="hello-holdout",
            files_contain={"data.txt": r"seed-\d+"},
        ),
    )
    result = ScenarioRunner().run(scenario, tmp_path)
    assert result.passed, result.details


def test_setup_failure_fails_scenario(tmp_path):
    scenario = HoldoutScenario(
        scenario_id="SCN-7",
        spec_clause_ids=[],
        title="bad setup",
        setup_commands=[f"{sys.executable} -c \"import sys; sys.exit(2)\""],
        run_command="echo never",
    )
    result = ScenarioRunner().run(scenario, tmp_path)
    assert not result.passed
    assert "setup" in result.details
