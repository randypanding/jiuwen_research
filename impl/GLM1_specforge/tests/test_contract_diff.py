"""WP2 tests: BC/NBC classification matrix (9 change kinds)."""
from specforge.contracts import diff_surfaces, explain, extract_module
from specforge.contracts.diff import delta_is_breaking

V1 = '''
def add(a: int, b: int) -> int:
    return a + b

def helper(x): return x

LIMIT = 10

class Calc:
    def __init__(self, scale=1):
        self.scale = scale
    def run(self, v): return v * self.scale
'''


def _diff(new_src):
    return diff_surfaces(extract_module(V1, "m"), extract_module(new_src, "m"))


def kinds(delta):
    return {c.kind for c in delta.changes}


def test_no_change():
    d = _diff(V1)
    assert d.changes == []
    assert not delta_is_breaking(d)


def test_added_export_is_bc():
    d = _diff(V1 + "\ndef extra(q):\n    return q\n")
    assert "added" in kinds(d) and not d.has_breaking


def test_removed_export_is_nbc():
    d = _diff(V1.replace("def helper(x): return x\n", ""))
    assert d.has_breaking
    assert any(c.kind == "removed" and c.symbol == "helper" for c in d.changes)


def test_required_param_added_is_nbc():
    d = _diff(V1.replace("def add(a: int, b: int)", "def add(a: int, b: int, c: int)"))
    assert any(c.kind == "param_added" and c.breaking for c in d.changes)


def test_default_param_added_is_bc():
    d = _diff(V1.replace("def add(a: int, b: int)", "def add(a: int, b: int, c: int = 0)"))
    assert any(c.kind == "param_added_default" and not c.breaking for c in d.changes)


def test_param_removed_is_nbc():
    d = _diff(V1.replace("def add(a: int, b: int)", "def add(a: int)"))
    assert any(c.kind == "param_removed" and c.breaking for c in d.changes)


def test_annotation_tightened_is_nbc():
    d = _diff(V1.replace("def run(self, v)", "def run(self, v: int)"))
    assert any(c.kind == "param_tightened" and c.breaking for c in d.changes)


def test_annotation_widened_is_bc():
    """Regression: int->float param widening must NOT be classified breaking
    (a repeated dict-key bug once collapsed 'int' widenings to the last entry)."""
    d = _diff(V1.replace("def add(a: int, b: int)", "def add(a: int, b: float)"))
    assert not d.has_breaking
    # widening an untyped param to bool stays recognized (bool accepts int input)
    d2 = _diff(V1.replace("def helper(x):", "def helper(x: bool):"))
    assert d2.has_breaking


def test_return_changed_is_nbc():
    d = _diff(V1.replace("def add(a: int, b: int) -> int:", "def add(a: int, b: int) -> float:"))
    assert any(c.kind == "return_changed" and c.breaking for c in d.changes)


def test_const_changed_is_nbc():
    d = _diff(V1.replace("LIMIT = 10", "LIMIT = 20"))
    assert any(c.kind == "const_changed" and c.breaking for c in d.changes)


def test_init_param_removal_is_nbc():
    d = _diff(V1.replace("def __init__(self, scale=1):", "def __init__(self):"))
    assert any(c.symbol == "Calc.__init__.scale" and c.breaking for c in d.changes)


def test_explain_human_readable():
    d = _diff(V1.replace("LIMIT = 10", "LIMIT = 20"))
    text = explain(d)
    assert "BREAKING" in text and "LIMIT" in text
