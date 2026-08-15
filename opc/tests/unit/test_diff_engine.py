from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from opc.diff.engine import DiffEngine, flatten_json
from opc.schemas.common import Verdict


def test_flatten_nested_structure():
    data = {"a": {"b": [1, 2]}, "c": 3}
    flat = flatten_json(data)
    assert flat == {"a.b[0]": 1, "a.b[1]": 2, "c": 3}


def test_dont_care_scope_matching():
    engine = DiffEngine()
    assert engine._in_dont_care("elapsed_ms", ["elapsed_ms"])
    assert engine._in_dont_care("meta.trace_id", ["meta"])
    assert engine._in_dont_care("items[0]", ["items"])
    assert not engine._in_dont_care("fee", ["elapsed_ms"])
    assert not engine._in_dont_care("meta_x", ["meta"])


@given(st.dictionaries(st.text(min_size=1, max_size=8, alphabet="abcdef"), st.integers(), min_size=1, max_size=6))
@settings(max_examples=30)
def test_flatten_roundtrip_keys(data):
    flat = flatten_json(data)
    assert set(flat) == set(data)


def test_information_insufficient_rule(tmp_path):
    instance = tmp_path / "solo"
    instance.mkdir()
    (instance / "main.py").write_text("def run(x=0):\n    return {'v': x}\n", encoding="utf-8")
    report = DiffEngine().run(
        instances={"solo": instance},
        entrypoint="main:run",
        corpus={"I1": {"x": 1}},
        min_instances=3,
    )
    assert report.verdict is Verdict.INCONCLUSIVE
    assert "information insufficient" in report.note


def test_crash_is_inconclusive_not_pass(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "main.py").write_text("def run(x=0):\n    return {'v': x}\n", encoding="utf-8")
    (b / "main.py").write_text("def run(x=0):\n    raise RuntimeError('boom')\n", encoding="utf-8")
    report = DiffEngine().run(
        instances={"a": a, "b": b},
        entrypoint="main:run",
        corpus={"I1": {"x": 1}},
        min_instances=2,
    )
    assert report.verdict is Verdict.INCONCLUSIVE
