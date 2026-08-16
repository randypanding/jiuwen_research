from __future__ import annotations

import pytest

from swarm_kernel.golden.store import GoldenPolicyError, GoldenStore


def test_golden_write_requires_non_ci(tmp_path, monkeypatch) -> None:
    store = GoldenStore(tmp_path / "golden")
    monkeypatch.delenv("CI", raising=False)
    manifest = store.write("clamp-vector", "1\n2\n", seed=42, generator_config_sha256="cfg", created_by="architect", approved_by="human:alice")
    assert manifest.approved
    content, loaded = store.load("clamp-vector")
    assert content == "1\n2\n"
    assert loaded.content_sha256 == manifest.content_sha256


def test_ci_must_never_auto_write_golden(tmp_path, monkeypatch) -> None:
    store = GoldenStore(tmp_path / "golden")
    monkeypatch.setenv("CI", "true")
    with pytest.raises(GoldenPolicyError):
        store.write("clamp-vector", "1\n", seed=1, generator_config_sha256="cfg", created_by="ci")


def test_missing_golden_fails_closed(tmp_path) -> None:
    store = GoldenStore(tmp_path / "golden")
    ok, mismatches, manifest = store.compare("never-written", "anything")
    assert not ok
    assert manifest is None
    assert any("fail-closed" in m for m in mismatches)


def test_compare_detects_mismatch(tmp_path, monkeypatch) -> None:
    store = GoldenStore(tmp_path / "golden")
    monkeypatch.delenv("CI", raising=False)
    store.write("vec", "line1\nline2\n", seed=1, generator_config_sha256="cfg", created_by="a", approved_by="h:b")
    ok, mismatches, manifest = store.compare("vec", "line1\nDIFFERENT\n")
    assert not ok
    assert any("line 2" in m for m in mismatches)
    ok2, _, _ = store.compare("vec", "line1\nline2\n")
    assert ok2


def test_unapproved_manifest_blocks(tmp_path, monkeypatch) -> None:
    store = GoldenStore(tmp_path / "golden")
    monkeypatch.delenv("CI", raising=False)
    manifest = store.write("vec", "x\n", seed=1, generator_config_sha256="cfg", created_by="a", approved_by="")
    assert not manifest.approved
