"""WP1 contract tests: spec parser."""
import pytest

from specforge.spec import SpecParseError, parse_spec

VALID = """---
spec_id: units.demo.adder
version: 1.0.0
r_level: R0
depends: []
artifacts: ["demo_adder/good.py"]
---

## L1 intent

free prose here

```clause
id: REQ-A-L1-1
level: L1
text: add returns the mathematical sum.
witness: holdout:adder-basic
```

## L2 contract

```clause
text: commutative law holds
witness: gate:h2
```

```contract
{"exports": {"add": {}}}
```

```invariant
expr: add(a,b) == add(b,a)
scope: h2
```

## DONT-CARE

```dontcare
- id: DC-1
  kind: unspecified
  region: debug_log
```
"""


def test_parse_valid_spec():
    unit = parse_spec(VALID)
    assert unit.spec_id == "units.demo.adder"
    assert unit.version == "1.0.0"
    assert unit.r_level == "R0"
    assert unit.artifacts == ["demo_adder/good.py"]
    assert len(unit.clauses) == 2
    assert unit.clauses[0].clause_id == "REQ-A-L1-1"
    assert unit.clauses[0].witness.kind == "holdout"
    assert unit.clauses[0].witness.ref == "adder-basic"
    # auto-id assigned to second clause
    assert unit.clauses[1].level == "L2"
    assert unit.clauses[1].witness.as_ref() == "gate:h2"
    assert unit.contract == {"exports": {"add": {}}}
    assert unit.invariants[0].expr == "add(a,b) == add(b,a)"
    assert unit.dont_cares[0].kind == "unspecified"


def test_parse_demo_spec(demo_spec_path):
    unit = parse_spec(path=demo_spec_path)
    assert unit.r_level == "R0"
    ids = {c.clause_id for c in unit.clauses}
    assert {"REQ-ADDER-L1-1", "REQ-ADDER-L2-1", "REQ-ADDER-L2-2"} <= ids
    assert unit.dont_cares[0].dc_id == "DC-ADDER-1"


@pytest.mark.parametrize("bad,match", [
    ("no frontmatter here", "frontmatter"),
    ("---\nspec_id: x\nversion: 1.0.0\n---\n", "r_level"),
    ("---\nspec_id: x\nversion: 1.0.0\nr_level: R9\n---\n", "r_level"),
])
def test_parse_errors(bad, match):
    with pytest.raises(SpecParseError, match=match):
        parse_spec(bad)


def test_bad_witness_kind():
    src = VALID.replace("witness: gate:h2", "witness: oracle:h2")
    with pytest.raises(SpecParseError, match="witness kind"):
        parse_spec(src)


def test_bad_dontcare_kind():
    src = VALID.replace("kind: unspecified", "kind: whatever")
    with pytest.raises(SpecParseError, match="dontcare kind"):
        parse_spec(src)


def test_contract_must_be_json_object():
    src = VALID.replace('{"exports": {"add": {}}}', "[1,2,3]")
    with pytest.raises(SpecParseError, match="JSON object"):
        parse_spec(src)


def test_roundtrip_dict_stable(demo_spec_path):
    unit = parse_spec(path=demo_spec_path)
    d1 = unit.to_dict()
    d2 = parse_spec(  # reparse from serialized clauses is stable on ids
        open(demo_spec_path, encoding="utf-8").read()).to_dict()
    assert d1 == d2
