import pytest

from swarmdev.oracle import ApprovalRequired, GoldenManifest, GoldenStore


def _manifest(approved_by="human:alice") -> GoldenManifest:
    return GoldenManifest(spec_hash="h", seed="seed", lock_hash="lock", approved_by=approved_by)


def test_save_requires_approval(tmp_path):
    store = GoldenStore(tmp_path / "golden")
    with pytest.raises(ApprovalRequired):
        store.save("ART-1", "content", _manifest(approved_by=None))
    with pytest.raises(ApprovalRequired):
        store.save("ART-1", "content", _manifest(approved_by=""))


def test_save_rejects_slash_in_artifact_id(tmp_path):
    store = GoldenStore(tmp_path / "golden")
    with pytest.raises(ValueError):
        store.save("nested/ART-1", "content", _manifest())


def test_compare_missing_snapshot(tmp_path):
    store = GoldenStore(tmp_path / "golden")
    verdict = store.compare("ART-1", "anything")
    assert verdict.match is False
    assert verdict.reason == "missing_snapshot"


def test_load_missing_raises_keyerror(tmp_path):
    store = GoldenStore(tmp_path / "golden")
    with pytest.raises(KeyError):
        store.load("ART-1")


def test_compare_content_mismatch_and_match(tmp_path):
    store = GoldenStore(tmp_path / "golden")
    store.save("ART-1", "golden-content", _manifest())
    verdict = store.compare("ART-1", "different-content")
    assert not verdict.match
    assert verdict.reason == "content_mismatch"
    verdict2 = store.compare("ART-1", "golden-content")
    assert verdict2.match


def test_load_roundtrip(tmp_path):
    store = GoldenStore(tmp_path / "golden")
    store.save("ART-1", "golden-content", _manifest())
    content, manifest = store.load("ART-1")
    assert content == "golden-content"
    assert manifest.approved_by == "human:alice"
    assert manifest.spec_hash == "h"
    assert manifest.created_at
