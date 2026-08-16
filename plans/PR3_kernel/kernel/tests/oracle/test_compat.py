"""H4: contract surface extraction and breaking-change classification.

Research finding that shaped this gate: SemVer compliance in the wild is around
a quarter, because humans classify their own changes. So the classification is
mechanical, the severity is derived from the classification, and the version
bump is checked against the severity rather than announced by the author.

Each test below is one rule of the classifier. They are written as
"this edit is/is not breaking" rather than "the function returns code X", so
that they stay meaningful if the codes are renamed.
"""

from __future__ import annotations

import pytest

from swarmkernel.contracts.base import ChangeSeverity
from swarmkernel.oracle.compat import SemanticResult, classify, classify_json_schema
from swarmkernel.oracle.surface import attach_schema_surface, extract_module_surface, extract_surface


def surface_of(source: str, module: str = "m") -> dict:
    return {"modules": {module: extract_module_surface(source, module).to_dict()}, "schemas": {}}


def codes(changes) -> set[str]:
    return {c.code for c in changes}


def diff(old_src: str, new_src: str):
    return classify(surface_of(old_src), surface_of(new_src))


# ------------------------------------------------------------- no change


def test_identical_surface_is_not_a_change():
    src = "def f(a, b=1):\n    return a + b\n"
    changes, severity, _ = diff(src, src)
    assert changes == []
    assert severity is ChangeSeverity.NONE


def test_body_edits_do_not_touch_the_surface():
    """The whole point of a surface: internals are free to change."""

    changes, severity, _ = diff(
        "def f(a, b=1):\n    return a + b\n",
        "def f(a, b=1):\n    total = a + b\n    return total\n",
    )
    assert severity is ChangeSeverity.NONE


def test_private_helpers_are_not_surface():
    changes, severity, _ = diff(
        "def f(a):\n    return a\n",
        "def _helper():\n    return 1\ndef f(a):\n    return a\n",
    )
    assert severity is ChangeSeverity.NONE


def test_docstring_changes_are_not_breaking():
    changes, severity, _ = diff(
        'def f(a):\n    """old"""\n    return a\n',
        'def f(a):\n    """new"""\n    return a\n',
    )
    assert severity is not ChangeSeverity.BREAKING


# ------------------------------------------------------------- breaking


def test_removing_a_function_is_breaking():
    changes, severity, _ = diff("def f():\n    pass\ndef g():\n    pass\n", "def f():\n    pass\n")
    assert severity is ChangeSeverity.BREAKING
    assert "H4.SYMBOL_REMOVED" in codes(changes)


def test_removing_a_module_is_breaking():
    changes, severity, _ = classify(surface_of("def f(): pass"), {"modules": {}, "schemas": {}})
    assert severity is ChangeSeverity.BREAKING
    assert "H4.MODULE_REMOVED" in codes(changes)


def test_removing_a_parameter_is_breaking():
    changes, severity, _ = diff("def f(a, b):\n    pass\n", "def f(a):\n    pass\n")
    assert severity is ChangeSeverity.BREAKING
    assert "H4.PARAM_REMOVED" in codes(changes)


def test_adding_a_required_parameter_is_breaking():
    changes, severity, _ = diff("def f(a):\n    pass\n", "def f(a, b):\n    pass\n")
    assert severity is ChangeSeverity.BREAKING
    assert "H4.PARAM_ADDED_REQUIRED" in codes(changes)


def test_reordering_positional_parameters_is_breaking():
    """Callers who passed positionally are broken even though every name
    survives -- the case a name-set comparison would miss."""

    changes, severity, _ = diff("def f(a, b):\n    pass\n", "def f(b, a):\n    pass\n")
    assert severity is ChangeSeverity.BREAKING
    assert "H4.POSITIONAL_ORDER_CHANGED" in codes(changes)


def test_removing_a_default_is_breaking():
    changes, severity, _ = diff("def f(a=1):\n    pass\n", "def f(a):\n    pass\n")
    assert severity is ChangeSeverity.BREAKING
    assert "H4.PARAM_DEFAULT_REMOVED" in codes(changes)


def test_making_a_function_async_is_breaking():
    changes, severity, _ = diff("def f():\n    pass\n", "async def f():\n    pass\n")
    assert severity is ChangeSeverity.BREAKING
    assert "H4.ASYNCNESS_CHANGED" in codes(changes)


def test_removing_a_method_is_breaking():
    changes, severity, _ = diff(
        "class C:\n    def m(self):\n        pass\n",
        "class C:\n    pass\n",
    )
    assert severity is ChangeSeverity.BREAKING
    assert "H4.METHOD_REMOVED" in codes(changes)


def test_removing_a_base_class_is_breaking():
    changes, severity, _ = diff(
        "class B: pass\nclass C(B):\n    pass\n",
        "class B: pass\nclass C:\n    pass\n",
    )
    assert severity is ChangeSeverity.BREAKING
    assert "H4.BASE_REMOVED" in codes(changes)


def test_removing_a_public_constant_is_breaking():
    changes, severity, _ = diff("LIMIT = 10\n", "")
    assert severity is ChangeSeverity.BREAKING
    assert "H4.CONSTANT_REMOVED" in codes(changes)


def test_changing_a_parameter_kind_is_breaking():
    changes, severity, _ = diff("def f(a):\n    pass\n", "def f(*, a):\n    pass\n")
    assert severity is ChangeSeverity.BREAKING
    assert "H4.PARAM_KIND_CHANGED" in codes(changes)


# ------------------------------------------------------------- additive


def test_adding_a_function_is_additive():
    changes, severity, _ = diff("def f():\n    pass\n", "def f():\n    pass\ndef g():\n    pass\n")
    assert severity is ChangeSeverity.ADDITIVE
    assert "H4.SYMBOL_ADDED" in codes(changes)


def test_adding_an_optional_parameter_is_additive():
    changes, severity, _ = diff("def f(a):\n    pass\n", "def f(a, b=None):\n    pass\n")
    assert severity is ChangeSeverity.ADDITIVE
    assert "H4.PARAM_ADDED_OPTIONAL" in codes(changes)


def test_adding_a_default_is_additive():
    changes, severity, _ = diff("def f(a):\n    pass\n", "def f(a=1):\n    pass\n")
    assert severity is ChangeSeverity.ADDITIVE


def test_adding_a_method_is_additive():
    changes, severity, _ = diff(
        "class C:\n    pass\n", "class C:\n    def m(self):\n        pass\n"
    )
    assert severity is ChangeSeverity.ADDITIVE


def test_adding_kwargs_absorbs_removed_parameters():
    """``**kwargs`` keeps old callers working, so the removal is not breaking.

    This is the case a naive name-set diff gets wrong in the *unsafe*
    direction's opposite: it would over-report, and a gate that cries wolf gets
    switched off.
    """

    changes, severity, _ = diff(
        "def f(a, b):\n    pass\n", "def f(a, **kwargs):\n    pass\n"
    )
    assert severity is not ChangeSeverity.BREAKING
    assert "H4.PARAM_ABSORBED_BY_KWARGS" in codes(changes)


# ---------------------------------------------------------------- patch


def test_changing_a_default_value_is_breaking():
    """A deliberate departure from "the signature still type-checks".

    Every caller that relied on the default silently changes behaviour, with no
    compile error and usually no test failure. Classifying this as PATCH is the
    single most common way a real breaking change ships under a patch bump, so
    the classifier treats it as BREAKING and forces the author to argue.
    """

    changes, severity, _ = diff("def f(a=1):\n    pass\n", "def f(a=2):\n    pass\n")
    assert severity is ChangeSeverity.BREAKING
    assert "H4.PARAM_DEFAULT_CHANGED" in codes(changes)


def test_changing_a_type_annotation_is_reported():
    changes, severity, _ = diff("def f(a: int):\n    pass\n", "def f(a: str):\n    pass\n")
    assert "H4.PARAM_TYPE_CHANGED" in codes(changes)


def test_changing_a_return_annotation_is_reported():
    changes, _, _ = diff("def f() -> int:\n    pass\n", "def f() -> str:\n    pass\n")
    assert "H4.RETURN_TYPE_CHANGED" in codes(changes)


# ---------------------------------------------------------------- schemas


def test_adding_a_required_schema_property_is_breaking():
    old = {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]}
    new = {
        "type": "object",
        "properties": {"a": {"type": "string"}, "b": {"type": "string"}},
        "required": ["a", "b"],
    }
    changes = classify_json_schema(old, new)
    assert "H4.SCHEMA_REQUIRED_ADDED" in codes(changes)
    assert any(c.severity is ChangeSeverity.BREAKING for c in changes)


def test_removing_a_schema_property_is_breaking():
    old = {"type": "object", "properties": {"a": {}, "b": {}}}
    new = {"type": "object", "properties": {"a": {}}}
    changes = classify_json_schema(old, new)
    assert "H4.SCHEMA_PROPERTY_REMOVED" in codes(changes)


def test_adding_an_optional_schema_property_is_additive():
    old = {"type": "object", "properties": {"a": {}}}
    new = {"type": "object", "properties": {"a": {}, "b": {}}}
    changes = classify_json_schema(old, new)
    assert all(c.severity is not ChangeSeverity.BREAKING for c in changes)


def test_shrinking_an_enum_is_breaking_and_growing_it_is_not():
    """Asymmetry that a symmetric differ gets wrong: for a *request* enum,
    removing a value rejects inputs that used to be accepted."""

    old = {"enum": ["a", "b", "c"]}
    shrunk = classify_json_schema(old, {"enum": ["a", "b"]})
    grown = classify_json_schema(old, {"enum": ["a", "b", "c", "d"]})
    assert any(c.severity is ChangeSeverity.BREAKING for c in shrunk)
    assert all(c.severity is not ChangeSeverity.BREAKING for c in grown)


def test_tightening_a_constraint_is_breaking():
    old = {"type": "string", "maxLength": 100}
    new = {"type": "string", "maxLength": 10}
    changes = classify_json_schema(old, new)
    assert "H4.SCHEMA_CONSTRAINT_TIGHTENED" in codes(changes)
    assert any(c.severity is ChangeSeverity.BREAKING for c in changes)


def test_changing_a_schema_type_is_breaking():
    changes = classify_json_schema({"type": "string"}, {"type": "integer"})
    assert "H4.SCHEMA_TYPE_CHANGED" in codes(changes)


def test_schema_surface_is_attachable_and_diffable():
    a = attach_schema_surface({"modules": {}, "schemas": {}}, "Cart", {"type": "object"})
    b = attach_schema_surface({"modules": {}, "schemas": {}}, "Cart", {"type": "array"})
    changes, severity, _ = classify(a, b)
    assert severity is ChangeSeverity.BREAKING


# ------------------------------------------------------ severity is a max


def test_severity_is_the_worst_change_not_the_last_one():
    changes, severity, _ = diff(
        "def f(a):\n    pass\n",
        "def f(a, b=1):\n    pass\ndef g(x):\n    pass\n",
    )
    assert severity is ChangeSeverity.ADDITIVE

    changes, severity, _ = diff(
        "def f(a):\n    pass\ndef g():\n    pass\n",
        "def f(a, b=1):\n    pass\n",
    )
    assert severity is ChangeSeverity.BREAKING


def test_semantic_refinement_is_unknown_unless_a_checker_is_supplied():
    """No checker means "unknown", never "refined". A missing prover must not
    read as a passed proof."""

    _, _, semantic = diff("def f(a):\n    pass\n", "def f(a):\n    pass\n")
    assert semantic == SemanticResult.UNKNOWN


def test_a_semantic_checker_cannot_rescue_a_structural_break():
    """The hook may only strengthen a verdict. A checker that claims
    "semantically compatible" must not unbreak a removed function."""

    changes, severity, _ = classify(
        surface_of("def f(a):\n    pass\n"),
        surface_of(""),
        semantic_check=lambda old, new: SemanticResult.COMPATIBLE,
    )
    assert severity is ChangeSeverity.BREAKING


def test_a_failed_semantic_refinement_is_breaking():
    changes, severity, semantic = classify(
        surface_of("def f(a):\n    pass\n"),
        surface_of("def f(a):\n    pass\n"),
        semantic_check=lambda old, new: SemanticResult.INCOMPATIBLE,
    )
    assert semantic == SemanticResult.INCOMPATIBLE
    assert "H4.SEMANTIC_REFINEMENT_FAILED" in codes(changes)
    assert severity is ChangeSeverity.BREAKING


# ------------------------------------------------- unparseable is not clean


def test_unparseable_source_is_an_explicit_failure_not_an_empty_surface(tmp_path):
    """The dangerous default: a syntax error yields "no symbols", which diffs as
    "everything removed" or, worse, as "no change" against another broken file.
    """

    (tmp_path / "broken.py").write_text("def f(:\n")
    broken = extract_surface(["broken.py"], root=tmp_path)
    assert "error" in broken["modules"]["broken"]
    changes, severity, _ = classify(broken, broken)
    assert "H4.SURFACE_UNPARSEABLE" in codes(changes)
    assert severity is ChangeSeverity.BREAKING


# ------------------------------------------------------------- extraction


def test_extract_surface_reads_real_files(tmp_path):
    pkg = tmp_path / "cart"
    pkg.mkdir()
    (pkg / "total.py").write_text("def total(lines):\n    return 0\n")
    surface = extract_surface(["cart/total.py"], root=tmp_path)
    assert "cart.total" in surface["modules"]
    names = {f["qualname"] for f in surface["modules"]["cart.total"]["functions"]}
    assert names == {"total"}


def test_extract_surface_is_stable_across_runs(tmp_path):
    pkg = tmp_path / "cart"
    pkg.mkdir()
    (pkg / "total.py").write_text("def total(lines):\n    return 0\n")
    first = extract_surface(["cart/total.py"], root=tmp_path)
    second = extract_surface(["cart/total.py"], root=tmp_path)
    assert first == second


def test_missing_file_is_reported_not_silently_empty(tmp_path):
    """A declared surface path that vanished must fail H4 loudly. Crashing the
    extractor or returning an empty surface are both worse than an error node.
    """

    surface = extract_surface(["cart/nope.py"], root=tmp_path)
    assert "error" in surface["modules"]["cart.nope"]
    changes, severity, _ = classify(surface, surface)
    assert "H4.SURFACE_UNPARSEABLE" in codes(changes)
    assert severity is ChangeSeverity.BREAKING


@pytest.mark.parametrize(
    "source",
    [
        "def f(a, /, b, *, c):\n    pass\n",
        "class C:\n    x: int = 1\n    def m(self) -> None: ...\n",
        "async def g(**kw):\n    pass\n",
    ],
)
def test_surface_extraction_survives_modern_syntax(source):
    surface = extract_module_surface(source, "m").to_dict()
    assert surface["functions"] or surface["classes"]
