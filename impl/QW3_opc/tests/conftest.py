from __future__ import annotations

import sys
from pathlib import Path

import pytest

from opc.fixtures_gen import generate

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


@pytest.fixture(scope="session")
def fixtures_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return generate(tmp_path_factory.mktemp("fixtures"))


@pytest.fixture()
def spec_dir(fixtures_root: Path) -> Path:
    return fixtures_root / "spec_repo"


@pytest.fixture()
def holdout_dir(fixtures_root: Path) -> Path:
    return fixtures_root / "holdout"


@pytest.fixture()
def instances_dir(fixtures_root: Path) -> Path:
    return fixtures_root / "instances"


@pytest.fixture()
def corpus_file(fixtures_root: Path) -> Path:
    return fixtures_root / "corpus" / "diff_corpus.json"
