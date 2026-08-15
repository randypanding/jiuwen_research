from swarmfoundry.oracle.diff import diff_instances
from swarmfoundry.oracle.runner import load_suite
from swarmfoundry.schema.diff import DIVERGENT, EQUIVALENT
from swarmfoundry.selftest import _write_instance, _write_suite


def test_identical_instances_equivalent(tmp_path):
    suite_dir = tmp_path / "suite"
    _write_suite(suite_dir)
    a = tmp_path / "a"
    b = tmp_path / "b"
    _write_instance(a, round_expr="round(a / b, 6)")
    _write_instance(b, round_expr="round(a / b, 6)")
    report = diff_instances(load_suite(suite_dir), suite_dir, a, b)
    assert report.equivalence == EQUIVALENT
    assert report.inputs_run == 4


def test_divergence_detected(tmp_path):
    suite_dir = tmp_path / "suite"
    _write_suite(suite_dir)
    a = tmp_path / "a"
    b = tmp_path / "b"
    _write_instance(a, round_expr="round(a / b, 6)")
    _write_instance(b, round_expr="int(a / b)")
    report = diff_instances(load_suite(suite_dir), suite_dir, a, b)
    assert report.equivalence == DIVERGENT
    assert any(d.path == "result" for d in report.divergences)


def test_dontcare_path_excluded(tmp_path):
    suite_dir = tmp_path / "suite"
    _write_suite(suite_dir)
    a = tmp_path / "a"
    b = tmp_path / "b"
    _write_instance(a, round_expr="round(a / b, 6)")
    _write_instance(b, round_expr="int(a / b)")
    report = diff_instances(load_suite(suite_dir), suite_dir, a, b, dontcare_paths=("result",))
    assert report.equivalence == EQUIVALENT
