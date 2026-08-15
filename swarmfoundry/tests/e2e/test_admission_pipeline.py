import json
import subprocess
import sys

from swarmfoundry.selftest import run_selftest


def test_selftest_end_to_end():
    assert run_selftest(verbose=False) == 0


def test_cli_gates_run_on_fixture(tmp_path):
    from swarmfoundry.selftest import _write_instance, _write_spec_repo, _write_suite
    from swarmfoundry.specrepo.loader import SpecRepo
    from swarmfoundry.specrepo.seal import reseal

    spec_root = tmp_path / "repo"
    spec_root.mkdir()
    _write_spec_repo(spec_root)
    reseal(SpecRepo(spec_root))
    holdout = tmp_path / "holdout"
    _write_suite(holdout)
    inst = tmp_path / "inst"
    _write_instance(inst, round_expr="round(a / b, 6)")

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "swarmfoundry.cli",
            "gates-run",
            "--instance",
            str(inst),
            "--instance-id",
            "cli-inst",
            "--spec-repo",
            str(spec_root),
            "--holdout",
            str(holdout),
            "--r-level",
            "R0",
            "--receipt-dir",
            str(tmp_path / "receipts"),
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "H3" in proc.stdout

    # with a passing judge panel the same instance must be admitted
    from swarmfoundry.gates.context import GateContext
    from swarmfoundry.gates.runner import GateRunner
    from swarmfoundry.schema.judge import JudgeVerdict

    ctx = GateContext(
        instance_dir=inst,
        instance_id="cli-inst",
        spec_repo=SpecRepo(spec_root),
        config={"gates": {"H2": {"commands": [["python3", "-c", "print('ok')"]]}}},
        r_level="R0",
        holdout_dirs=(holdout,),
        judge_verdicts=(
            JudgeVerdict("j1", "famX", "no_veto", "ok", ()),
            JudgeVerdict("j2", "famY", "no_veto", "ok", ()),
        ),
        builder_model_family="famZ",
    )
    assert GateRunner().decide(ctx).admitted


def test_cli_spec_validate_and_seal(tmp_path):
    from swarmfoundry.selftest import _write_spec_repo
    from swarmfoundry.cli import main

    spec_root = tmp_path / "repo"
    spec_root.mkdir()
    _write_spec_repo(spec_root)
    assert main(["spec-validate", "--repo", str(spec_root)]) == 0
    assert main(["spec-seal", "--repo", str(spec_root)]) == 0
    assert (spec_root / "registry" / "seals.json").is_file()


def test_cli_surface_extract_and_diff(tmp_path):
    from swarmfoundry.cli import main
    from swarmfoundry.selftest import _write_instance

    a = tmp_path / "a"
    _write_instance(a, round_expr="round(a / b, 6)")
    old = tmp_path / "old.json"
    assert main(["surface-extract", "--dir", str(a), "--module", "calc", "--out", str(old)]) == 0
    new = tmp_path / "new.json"
    assert main(["surface-extract", "--dir", str(a), "--module", "calc", "--out", str(new)]) == 0
    assert main(["surface-diff", "--old", str(old), "--new", str(new)]) == 0
