from __future__ import annotations

import shutil
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture()
def fixtures_root() -> Path:
    return FIXTURES


@pytest.fixture()
def spec_path(fixtures_root: Path) -> Path:
    return fixtures_root / "spec" / "spec.json"


@pytest.fixture()
def oracle_dir(fixtures_root: Path) -> Path:
    return fixtures_root / "oracle"


@pytest.fixture()
def instance(fixtures_root: Path):
    def _get(name: str) -> Path:
        return fixtures_root / "instances" / name

    return _get


@pytest.fixture()
def work_root(tmp_path: Path) -> Path:
    return tmp_path / "world-root"
