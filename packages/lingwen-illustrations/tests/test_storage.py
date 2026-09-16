"""Test asset file IO + .meta.json sidecar writing."""

from __future__ import annotations

from pathlib import Path

import pytest
from lingwen_illustrations.exceptions import StoreError
from lingwen_illustrations.metadata import IllustrationMetadata
from lingwen_illustrations.storage import (
    asset_path,
    delete_asset,
    list_assets,
    replace_asset,
    save_asset,
)


def _sample_meta(id: str = "test-id", chapter_num: int | None = 17) -> IllustrationMetadata:
    return IllustrationMetadata(
        id=id,
        type="chapter" if chapter_num else "cover",
        project_slug="test-project",
        chapter_num=chapter_num,
        style_preset="ink",
        custom_prompt=None,
        scene_json={"subject": "x", "scene": "y", "mood": "z", "characters_in_scene": [], "extraction_confidence": 0.8},
        final_prompt="test prompt",
        prompt_hash="sha256:abc",
        model="minimax-multimodal",
        created_at="2026-09-15T10:00:00Z",
    )


def test_asset_path_cover(tmp_path: Path):
    p = asset_path(tmp_path, type="cover", id="abc")
    assert p == tmp_path / "assets" / "covers" / "abc.jpg"


def test_asset_path_chapter(tmp_path: Path):
    p = asset_path(tmp_path, type="chapter", id="abc", chapter_num=17)
    assert p == tmp_path / "assets" / "illustrations" / "chapter-017" / "abc.jpg"


def test_save_asset_writes_jpg_and_meta(tmp_path: Path):
    meta = _sample_meta(id="abc123")
    image_bytes = b"\xff\xd8\xff\xe0fake-jpeg-bytes"

    result_path = save_asset(tmp_path, image_bytes, meta)

    assert result_path == tmp_path / "assets" / "illustrations" / "chapter-017" / "abc123.jpg"
    assert result_path.exists()
    assert result_path.read_bytes() == image_bytes

    sidecar = result_path.with_suffix(result_path.suffix + ".meta.json")
    assert sidecar.exists()
    assert "abc123" in sidecar.read_text()


def test_save_asset_creates_parents(tmp_path: Path):
    meta = _sample_meta(id="x", chapter_num=5)
    save_asset(tmp_path, b"data", meta)
    assert (tmp_path / "assets" / "illustrations" / "chapter-005").exists()


def test_delete_asset_removes_jpg_and_meta(tmp_path: Path):
    meta = _sample_meta(id="del")
    save_asset(tmp_path, b"data", meta)
    delete_asset(tmp_path, meta)
    assert not (tmp_path / "assets" / "illustrations" / "chapter-017" / "del.jpg").exists()
    assert not (tmp_path / "assets" / "illustrations" / "chapter-017" / "del.jpg.meta.json").exists()


def test_list_assets_returns_all(tmp_path: Path):
    save_asset(tmp_path, b"a", _sample_meta(id="a", chapter_num=1))
    save_asset(tmp_path, b"b", _sample_meta(id="b", chapter_num=2))
    save_asset(tmp_path, b"c", IllustrationMetadata(
        id="c", type="cover", project_slug="test", chapter_num=None,
        style_preset="ink", custom_prompt=None, scene_json={},
        final_prompt="", prompt_hash="sha256:c", model="m", created_at="2026-09-15T00:00:00Z",
    ))
    assets = list_assets(tmp_path)
    assert len(assets) == 3
    types = {a.type for a in assets}
    assert types == {"chapter", "cover"}


def test_list_assets_empty_dir(tmp_path: Path):
    assert list_assets(tmp_path) == []


def test_asset_path_invalid_type_raises():
    with pytest.raises(StoreError):
        asset_path(Path("/tmp"), type="bogus", id="x")  # type: ignore[arg-type]


def test_list_assets_sorts_by_created_at_desc(tmp_path: Path):
    """MINOR fix: sort order not previously tested."""
    import dataclasses

    def meta_with_ts(id: str, ts: str) -> IllustrationMetadata:
        return dataclasses.replace(_sample_meta(id=id), created_at=ts)

    save_asset(tmp_path, b"a", meta_with_ts("oldest", "2026-09-15T08:00:00Z"))
    save_asset(tmp_path, b"b", meta_with_ts("newest", "2026-09-15T10:00:00Z"))
    save_asset(tmp_path, b"c", meta_with_ts("middle", "2026-09-15T09:00:00Z"))

    assets = list_assets(tmp_path)
    assert [a.id for a in assets] == ["newest", "middle", "oldest"]


def test_list_assets_skips_corrupt_sidecars(tmp_path: Path):
    """MINOR fix: behavior added in amend (LoadError catch) needs regression test."""
    # Write one valid + one corrupt sidecar
    save_asset(tmp_path, b"good", _sample_meta(id="good"))
    corrupt = tmp_path / "assets" / "illustrations" / "chapter-017" / "corrupt.jpg.meta.json"
    corrupt.parent.mkdir(parents=True, exist_ok=True)
    corrupt.write_text("not valid json{", encoding="utf-8")

    # And one with missing required field (would raise LoadError per Task 3 fixup)
    missing = tmp_path / "assets" / "illustrations" / "chapter-017" / "missing.jpg.meta.json"
    missing.write_text('{"id": "x"}', encoding="utf-8")  # only id, no other required fields

    assets = list_assets(tmp_path)
    # Only the valid one should be returned
    assert len(assets) == 1
    assert assets[0].id == "good"


def test_delete_asset_idempotent(tmp_path: Path):
    """MINOR fix: delete twice should not raise."""
    meta = _sample_meta(id="twice")
    save_asset(tmp_path, b"data", meta)
    delete_asset(tmp_path, meta)  # first delete
    delete_asset(tmp_path, meta)  # second delete on already-gone — no error
    # Verify the files really are gone
    assert not (tmp_path / "assets" / "illustrations" / "chapter-017" / "twice.jpg").exists()


# ─── replace_asset tests (Phase 94 atomic regenerate) ──────────────


def test_replace_asset_preserves_id_and_swaps_bytes(tmp_path: Path):
    """replace_asset overwrites bytes in place; asset_id stays the same."""
    meta = _sample_meta(id="regen-1")
    save_asset(tmp_path, b"OLD-BYTES", meta)
    jpg_path = asset_path(tmp_path, type="chapter", id="regen-1", chapter_num=17)
    sidecar = jpg_path.with_suffix(jpg_path.suffix + ".meta.json")
    assert jpg_path.read_bytes() == b"OLD-BYTES"

    # Replace with new content + updated metadata.
    new_meta = _sample_meta(id="regen-1")
    new_meta_dict = dict(new_meta.to_dict())
    new_meta_dict["created_at"] = "2026-09-16T12:00:00Z"  # timestamp changed
    new_meta = IllustrationMetadata.from_dict(new_meta_dict)
    new_meta_dict["final_prompt"] = "updated prompt v2"
    new_meta = IllustrationMetadata.from_dict(new_meta_dict)

    returned = replace_asset(tmp_path, b"NEW-BYTES", new_meta)
    assert returned == jpg_path
    assert jpg_path.read_bytes() == b"NEW-BYTES"

    # Sidecar updated with new metadata (final_prompt, created_at).
    import json
    sidecar_data = json.loads(sidecar.read_text(encoding="utf-8"))
    assert sidecar_data["id"] == "regen-1"
    assert sidecar_data["final_prompt"] == "updated prompt v2"
    assert sidecar_data["created_at"] == "2026-09-16T12:00:00Z"


def test_replace_asset_no_temp_leftover_on_success(tmp_path: Path):
    """Atomic rename must clean up the temp file (no .tmp leftovers)."""
    meta = _sample_meta(id="clean-tmp")
    save_asset(tmp_path, b"v1", meta)
    replace_asset(tmp_path, b"v2", meta)
    jpg_path = asset_path(tmp_path, type="chapter", id="clean-tmp", chapter_num=17)
    # No .tmp siblings should remain.
    siblings = list(jpg_path.parent.glob("*.tmp"))
    assert siblings == [], f"leftover temp files: {siblings}"


def test_replace_asset_falls_back_to_save_when_missing(tmp_path: Path):
    """If no existing asset, replace_asset bootstraps via save_asset (no atomic target)."""
    meta = _sample_meta(id="bootstrap")
    # No prior save_asset call.
    returned = replace_asset(tmp_path, b"NEW", meta)
    jpg_path = asset_path(tmp_path, type="chapter", id="bootstrap", chapter_num=17)
    assert returned == jpg_path
    assert jpg_path.read_bytes() == b"NEW"


def test_replace_asset_invalidates_listing_via_created_at(tmp_path: Path):
    """After replace, list_assets returns updated metadata (created_at + final_prompt)."""
    meta = _sample_meta(id="listable")
    save_asset(tmp_path, b"OLD", meta)

    # Replace with new metadata.
    new_meta_dict = dict(meta.to_dict())
    new_meta_dict["created_at"] = "2026-09-16T12:00:00Z"
    new_meta_dict["final_prompt"] = "new prompt v2"
    new_meta = IllustrationMetadata.from_dict(new_meta_dict)
    replace_asset(tmp_path, b"NEW", new_meta)

    listed = list_assets(tmp_path)
    found = next((a for a in listed if a.id == "listable"), None)
    assert found is not None
    assert found.final_prompt == "new prompt v2"
    assert found.created_at == "2026-09-16T12:00:00Z"


def test_replace_asset_preserves_existing_on_failure(tmp_path: Path, monkeypatch):
    """If atomic rename fails (disk full / permissions), original is preserved."""
    meta = _sample_meta(id="preserve-on-fail")
    save_asset(tmp_path, b"ORIGINAL", meta)
    jpg_path = asset_path(tmp_path, type="chapter", id="preserve-on-fail", chapter_num=17)
    assert jpg_path.read_bytes() == b"ORIGINAL"

    # Force Path.replace to raise — simulates disk-full during atomic rename.
    def _raise_replace(self, other):
        raise OSError("simulated disk full during rename")

    monkeypatch.setattr(Path, "replace", _raise_replace)

    with pytest.raises(StoreError) as exc:
        replace_asset(tmp_path, b"NEW-BYTES", meta)
    assert "rename" in str(exc.value).lower() or "failed" in str(exc.value).lower()

    # Original asset must still be readable.
    assert jpg_path.read_bytes() == b"ORIGINAL"
    # No .tmp leftover after rollback.
    siblings = list(jpg_path.parent.glob("*.tmp"))
    assert siblings == []
