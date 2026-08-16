"""WP4 tests: differential engine (real subprocess instances) + measurement table."""

from specforge.difftest import (
    DivergenceCorpus,
    InstanceRecords,
    NormalizeRules,
    fingerprint,
    moderation_route,
    run_instance,
    run_measurement,
)

GOOD = (
    "import sys, json\n"
    "for line in sys.stdin:\n"
    "    o = json.loads(line)\n"
    "    print(json.dumps({'sum': o['a'] + o['b'], 'log': 'x'}))\n"
)
BROKEN_SIGN = (
    "import sys, json\n"
    "for line in sys.stdin:\n"
    "    o = json.loads(line)\n"
    "    print(json.dumps({'sum': abs(o['a']) + abs(o['b']), 'log': 'x'}))\n"
)
LOG_ONLY = (
    "import sys, json\n"
    "for line in sys.stdin:\n"
    "    o = json.loads(line)\n"
    "    print(json.dumps({'sum': o['a'] + o['b'], 'log': 'y-%d' % o['a']}))\n"
)
CRASH = (
    "import sys, json\n"
    "for line in sys.stdin:\n"
    "    o = json.loads(line)\n"
    "    raise RuntimeError('boom')\n"
)


def _mk(tmp_path, name, src):
    p = tmp_path / f"{name}.py"
    p.write_text(src, encoding="utf-8")
    return ["python", str(p)]


INPUTS = [{"a": a, "b": 3} for a in (2, -4, 10, -7, 0)]


def _records(tmp_path, name, src, oracle=True, inputs=None):
    recs = run_instance(_mk(tmp_path, name, src), inputs or INPUTS, cwd=str(tmp_path),
                        timeout_per_input=5)
    return InstanceRecords(instance_id=name, records=recs, oracle_passed=oracle)


def test_identical_instances_closed(tmp_path):
    m = run_measurement([
        _records(tmp_path, "g1", GOOD),
        _records(tmp_path, "g2", GOOD.replace("'x'", "'x'")),
    ])
    assert m.verdict == "CLOSED"
    assert len(set(m.fingerprints.values())) == 1


def test_silence_on_unregistered_divergence(tmp_path):
    m = run_measurement([
        _records(tmp_path, "g", GOOD),
        _records(tmp_path, "b", BROKEN_SIGN),
    ])
    assert m.verdict == "SILENCE"
    assert m.divergences, "divergences must be recorded for the moderator"
    assert moderation_route(m).startswith("spec-moderator")


def test_silence_dc_when_region_registered(tmp_path):
    m = run_measurement([
        _records(tmp_path, "g", GOOD),
        _records(tmp_path, "l", LOG_ONLY),
    ], dc_regions={"log*": "unspecified"})
    assert m.verdict == "SILENCE_DC"
    assert moderation_route(m) == "register-freedom"


def test_diff_in_undefined_is_defect(tmp_path):
    m = run_measurement([
        _records(tmp_path, "g", GOOD),
        _records(tmp_path, "b", BROKEN_SIGN),
    ], dc_regions={"sum*": "undefined"})
    assert m.verdict == "DIFF_IN_UNDEFINED"
    assert moderation_route(m) == "defect: reject and fix"


def test_ambiguous_partial_failure(tmp_path):
    m = run_measurement([
        _records(tmp_path, "g", GOOD, oracle=True),
        _records(tmp_path, "c", CRASH, oracle=False),
        _records(tmp_path, "g2", GOOD, oracle=True),
    ])
    assert m.verdict == "AMBIGUOUS"


def test_conflict_all_fail(tmp_path):
    m = run_measurement([
        _records(tmp_path, "c1", CRASH, oracle=False),
        _records(tmp_path, "c2", CRASH, oracle=False),
        _records(tmp_path, "c3", CRASH, oracle=False),
    ])
    assert m.verdict == "CONFLICT"
    assert "steward" in moderation_route(m)


def test_insufficient_n_lt_3_with_failures(tmp_path):
    m = run_measurement([
        _records(tmp_path, "g", GOOD, oracle=True),
        _records(tmp_path, "c", CRASH, oracle=False),
    ])
    assert m.verdict == "INSUFFICIENT"
    assert moderation_route(m) == "fan-out more instances (>=3)"


def test_timeout_marks_all_records(tmp_path):
    hang = "import time\ntime.sleep(30)\n"
    recs = _records(tmp_path, "h", hang, inputs=[{"a": 1}])
    assert all(r.timed_out for r in recs.records)


def test_fingerprint_clustering(tmp_path):
    r1 = _records(tmp_path, "g", GOOD)
    r2 = _records(tmp_path, "g2", GOOD)
    r3 = _records(tmp_path, "b", BROKEN_SIGN)
    f1 = fingerprint(r1.records, NormalizeRules())
    assert f1 == fingerprint(r2.records, NormalizeRules())
    assert f1 != fingerprint(r3.records, NormalizeRules())


def test_corpus_roundtrip(tmp_path):
    corpus = DivergenceCorpus(tmp_path / "corpus")
    corpus.add("u.x", {"a": -4, "b": 3}, ["sum"], "SILENCE")
    corpus.add("u.x", {"a": -4, "b": 3}, ["sum"], "SILENCE")  # dedupe
    corpus.add("u.x", {"a": -7, "b": 3}, ["sum"], "SILENCE")
    assert len(corpus.inputs("u.x")) == 2
