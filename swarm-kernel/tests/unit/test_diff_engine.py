from __future__ import annotations

from swarm_kernel.diff.engine import canonicalize, run_differential


def test_divergent_pair_detected(oracle_dir, instance) -> None:
    report = run_differential([instance("divergent_a"), instance("divergent_b")], oracle_dir, seed=42, corpus_size=60)
    assert report.divergent
    assert report.divergent_inputs
    assert all("lo" in i and "hi" in i for i in report.divergent_inputs)
    for key, diffs in report.pairwise.items():
        assert diffs


def test_behaviorally_equal_instances_not_divergent(oracle_dir, instance) -> None:
    report = run_differential([instance("good"), instance("good2")], oracle_dir, seed=42, corpus_size=60)
    assert not report.divergent
    assert report.pairwise


def test_diff_is_deterministic(oracle_dir, instance) -> None:
    r1 = run_differential([instance("divergent_a"), instance("divergent_b")], oracle_dir, seed=7, corpus_size=30)
    r2 = run_differential([instance("divergent_a"), instance("divergent_b")], oracle_dir, seed=7, corpus_size=30)
    assert r1.pairwise == r2.pairwise
    assert r1.divergent_inputs == r2.divergent_inputs


def test_canonicalize_redaction() -> None:
    a = canonicalize({"v": 1, "ts": 123}, redactions=("ts",))
    b = canonicalize({"v": 1, "ts": 999}, redactions=("ts",))
    assert a == b
    assert canonicalize(1.0000000001) == canonicalize(1.0)
