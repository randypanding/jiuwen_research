from pathlib import Path

from swarmfoundry.contracts.extract import extract_surface
from swarmfoundry.contracts.compat import diff_surfaces
from swarmfoundry.schema.surface import SEVERITY_BREAKING, SEVERITY_NON_BREAKING

OLD = '''
API_VERSION = "1.0"


def transfer(amount, account):
    """Transfer money."""
    return True


class Ledger:
    def append(self, entry):
        return None
'''

NEW_BREAKING = '''
API_VERSION = "1.0"


def transfer(amount, account, currency):
    return True


class Ledger:
    def append(self, entry):
        return None
'''

NEW_COMPAT = '''
API_VERSION = "1.0"


def transfer(amount, account, currency="CNY"):
    return True


def audit():
    return []


class Ledger:
    def append(self, entry):
        return None
'''

NEW_REMOVED = '''
API_VERSION = "1.0"


class Ledger:
    def append(self, entry):
        return None
'''


def _instance(tmp_path: Path, code: str, name: str) -> Path:
    d = tmp_path / name
    d.mkdir()
    (d / "api.py").write_text(code, encoding="utf-8")
    return d


def test_surface_extraction(tmp_path):
    inst = _instance(tmp_path, OLD, "old")
    surface = extract_surface(inst, module="svc")
    names = {(s.kind, s.name) for s in surface.symbols}
    assert ("function", "api.transfer") in names
    assert ("class", "api.Ledger") in names
    assert ("method", "api.Ledger.append") in names
    assert ("constant", "api.API_VERSION") in names


def test_new_required_param_is_breaking(tmp_path):
    old = extract_surface(_instance(tmp_path, OLD, "old"), "svc")
    new = extract_surface(_instance(tmp_path, NEW_BREAKING, "new"), "svc")
    diff = diff_surfaces(old, new)
    breaking = diff.breaking()
    assert len(breaking) == 1
    assert "currency" in breaking[0].detail


def test_optional_param_and_additions_are_compatible(tmp_path):
    old = extract_surface(_instance(tmp_path, OLD, "old"), "svc")
    new = extract_surface(_instance(tmp_path, NEW_COMPAT, "new"), "svc")
    diff = diff_surfaces(old, new)
    assert not diff.breaking()
    kinds = {c.name: c.severity for c in diff.changes}
    assert kinds["api.audit"] == SEVERITY_NON_BREAKING


def test_removed_symbol_is_breaking(tmp_path):
    old = extract_surface(_instance(tmp_path, OLD, "old"), "svc")
    new = extract_surface(_instance(tmp_path, NEW_REMOVED, "new"), "svc")
    diff = diff_surfaces(old, new)
    removed = [c for c in diff.breaking() if c.change == "removed"]
    assert any(c.name == "api.transfer" for c in removed)


def test_schema_file_hash_change_is_breaking(tmp_path):
    old_dir = _instance(tmp_path, OLD, "old")
    new_dir = _instance(tmp_path, OLD, "new")
    (old_dir / "msg.schema.json").write_text('{"v": 1}')
    (new_dir / "msg.schema.json").write_text('{"v": 2}')
    diff = diff_surfaces(extract_surface(old_dir, "svc"), extract_surface(new_dir, "svc"))
    assert diff.breaking() and diff.breaking()[0].name == "msg.schema.json"
