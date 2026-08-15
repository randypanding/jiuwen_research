"""WP2 tests: AST contract surface extraction."""
from specforge.contracts import extract, extract_module

SRC = '''
VERSION = "1.0"

def add(a: int, b: int = 1) -> int:
    return a + b

def _private(x):
    return x

class Calculator:
    precision = 2

    def __init__(self, scale: int = 1):
        self.scale = scale

    def compute(self, x: int) -> int:
        return x * self.scale
'''


def test_extracts_public_surface():
    snap = extract_module(SRC, "m")
    assert "add" in snap.functions
    assert "_private" not in snap.functions
    fn = snap.functions["add"]
    assert [p.name for p in fn.params] == ["a", "b"]
    assert fn.params[0].annotation == "int"
    assert fn.params[1].default == "1"
    assert fn.returns == "int"
    assert snap.constants["VERSION"] == "'1.0'"
    cls = snap.classes["Calculator"]
    assert cls.public_attrs == ["precision"]
    methods = {m.name for m in cls.public_methods}
    assert methods == {"__init__", "compute"}


def test_dunder_all_restriction():
    src = SRC + '\n__all__ = ["add"]\n'
    snap = extract_module(src, "m")
    assert list(snap.functions) == ["add"]
    assert snap.classes == {}


def test_snapshot_hash_stability_and_roundtrip():
    a = extract_module(SRC, "m")
    b = extract_module(SRC, "m")
    assert a.hash() == b.hash()
    c = extract_module(SRC.replace("b: int = 1", "b: int = 2"), "m")
    assert a.hash() != c.hash()
    from specforge.contracts import SurfaceSnapshot
    rt = SurfaceSnapshot.from_json(a.to_json())
    assert rt.hash() == a.hash()


def test_extract_file_and_tree(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "core.py").write_text("def f(x):\n    return x\n", encoding="utf-8")
    (pkg / "extra.py").write_text("def g(y):\n    return y\n", encoding="utf-8")
    snap = extract(pkg, "pkg")
    assert set(snap.functions) == {"core.f", "extra.g"}
