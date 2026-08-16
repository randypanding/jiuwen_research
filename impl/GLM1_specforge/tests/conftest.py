"""Shared fixtures for specforge tests."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = REPO_ROOT / "examples"

GATE_IDS = ["h1", "h2", "h3", "h4", "h5", "h6", "h7", "h8"]
HOLDOUT_IDS = ["adder-basic", "adder-edge"]


@pytest.fixture
def demo_spec_path() -> str:
    return str(EXAMPLES / "demo_adder" / "spec.md")


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """A mini project tree: package + strong tests, ready for H1/H2 gates."""
    pkg = tmp_path / "demo_adder"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "good.py").write_text(
        (EXAMPLES / "demo_adder" / "good.py").read_text(encoding="utf-8"), encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_adder.py").write_text(
        (EXAMPLES / "demo_adder" / "tests" / "test_adder.py").read_text(encoding="utf-8"),
        encoding="utf-8")
    return tmp_path


@pytest.fixture
def tmp_project_weak_tests(tmp_path: Path) -> Path:
    """Same package but with assertion-free tests (weak oracle)."""
    root = tmp_path
    pkg = root / "demo_adder"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "good.py").write_text(
        (EXAMPLES / "demo_adder" / "good.py").read_text(encoding="utf-8"), encoding="utf-8")
    tests = root / "tests"
    tests.mkdir()
    (tests / "test_weak.py").write_text(
        "import sys\nfrom pathlib import Path\n"
        "sys.path.insert(0, str(Path(__file__).resolve().parents[1]))\n"
        "from demo_adder.good import add\n\n"
        "def test_runs():\n"
        "    add(1, 2)\n"
        "def test_runs_more():\n"
        "    add(-3, 4)\n",
        encoding="utf-8")
    return root


def git_available() -> bool:
    return shutil.which("git") is not None
