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
