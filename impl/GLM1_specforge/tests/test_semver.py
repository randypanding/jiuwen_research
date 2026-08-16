"""WP1 tests: semver bump matrix (D4)."""
import pytest

from specforge.spec import SemVer, check_bump, classify_deprecation, required_bump


def test_required_bump():
    assert required_bump(True, False) == "major"
    assert required_bump(False, True) == "minor"
    assert required_bump(False, False) == "patch"


@pytest.mark.parametrize("old,new,breaking,feature,ok", [
    ("1.2.3", "1.3.0", False, True, True),    # additive -> minor ok
    ("1.2.3", "1.2.4", False, True, False),   # additive needs minor
    ("1.2.3", "2.0.0", True, False, True),    # breaking -> major ok
    ("1.2.3", "1.3.0", True, False, False),   # breaking needs major
    ("1.2.3", "1.2.2", False, False, False),  # must increase
    ("1.2.3", "1.2.4", False, False, True),   # patch ok for internal fixes
])
def test_bump_matrix(old, new, breaking, feature, ok):
    res = check_bump(old, new, has_breaking=breaking, has_feature=feature)
    assert res.ok is ok, res.reason


def test_parse_invalid():
    with pytest.raises(ValueError):
        SemVer.parse("1.2")
    with pytest.raises(ValueError):
        SemVer.parse("v1.2.3")


def test_deprecation_buffer():
    old = {"a", "b", "c"}
    new = {"a", "b"}
    # no deprecation state recorded -> violation
    v = classify_deprecation(old, new)
    assert len(v) == 1 and "c" in v[0]
    # with deprecated state -> allowed
    v2 = classify_deprecation(old, new, {"c": "deprecated"})
    assert v2 == []
