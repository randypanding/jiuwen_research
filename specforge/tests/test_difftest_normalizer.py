"""WP4 tests: normalizer + comparator + generator."""

from specforge.difftest import (
    NormalizeRules,
    compare_outputs,
    generate_inputs,
    match_dc_region,
    normalize,
)


def test_normalize_floats_and_key_order():
    a = {"z": 1.0, "y": 2.0000000001, "n": -0.0}
    b = {"y": 2.0, "z": 1.0, "n": 0.0}
    assert normalize(a, NormalizeRules()) == normalize(b, NormalizeRules())


def test_normalize_strips_fields_and_redacts():
    rules = NormalizeRules(strip_fields=["duration"],
                           redact_patterns=[r"\d{4}-\d{2}-\d{2}T[\d:]+Z"])
    a = {"v": 1, "duration": 0.31, "ts": "2026-01-02T03:04:05Z"}
    b = {"v": 1, "duration": 9.99, "ts": "2026-99-99T99:99:99Z"}
    assert normalize(a, rules) == normalize(b, rules)


def test_normalize_nan_inf():
    assert normalize(float("nan"), NormalizeRules()) == "<NaN>"
    assert normalize(float("inf"), NormalizeRules()) == "<Inf+>"


def test_compare_equal_and_diff():
    rules = NormalizeRules()
    assert compare_outputs({"s": 1}, {"s": 1}, rules).verdict == "EQUAL"
    out = compare_outputs({"s": 1}, {"s": 2}, rules)
    assert out.verdict == "DIFF"
    assert out.diffs[0].path == "s"


def test_compare_dc_regions():
    rules = NormalizeRules()
    dc = {"debug_log.*": "unspecified", "sum": "int"}
    # divergence only inside registered don't-care region
    out = compare_outputs({"sum": 3, "debug_log": "A"}, {"sum": 3, "debug_log": "B"}, rules, dc)
    assert out.verdict == "DIFF_IN_DONT_CARE"
    # divergence in constrained field: plain DIFF
    out2 = compare_outputs({"sum": 3, "debug_log": "A"}, {"sum": 4, "debug_log": "A"}, rules, dc)
    assert out2.verdict == "DIFF"
    # divergence crossing an `undefined` boundary is a defect
    dc2 = {"sum.*": "undefined"}
    out3 = compare_outputs({"sum": 3}, {"sum": 4}, rules, dc2)
    assert out3.verdict == "DIFF_IN_UNDEFINED"


def test_match_dc_glob():
    assert match_dc_region("a.b.c", {"a.*": "unspecified"}) == "unspecified"
    assert match_dc_region("x.y", {"a.*": "unspecified"}) is None


def test_generator_deterministic_and_seeded():
    schema = {"a": {"type": "int", "min": -50, "max": 50},
              "b": {"type": "int", "min": -50, "max": 50}}
    i1 = generate_inputs(schema, seed=42, n=20)
    i2 = generate_inputs(schema, seed=42, n=20)
    i3 = generate_inputs(schema, seed=43, n=20)
    assert i1 == i2
    assert i1 != i3  # different seed -> different stream
    # seed is mandatory (constitution #17)
    try:
        generate_inputs(schema, seed=None, n=1)
        raise AssertionError("seed=None must raise")
    except Exception:
        pass


def test_generator_includes_boundaries():
    schema = {"a": {"type": "int", "min": -100, "max": 100}}
    vals = {i["a"] for i in generate_inputs(schema, seed=7, n=200)}
    assert 0 in vals and 1 in vals and -1 in vals
