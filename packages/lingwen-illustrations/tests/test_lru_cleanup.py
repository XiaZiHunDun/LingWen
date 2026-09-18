"""lru_cleanup tests (Phase 98 L1-L12)."""
from __future__ import annotations

from pathlib import Path

import pytest

from lingwen_illustrations.metadata import IllustrationMetadata


def _make_meta(
    asset_id: str,
    created_at: str,
    type: str = "cover",
    chapter_num: int | None = None,
) -> IllustrationMetadata:
    return IllustrationMetadata(
        id=asset_id,
        type=type,
        project_slug="test-slug",
        chapter_num=chapter_num,
        style_preset="ink",
        custom_prompt=None,
        scene_json={"scene": asset_id},
        final_prompt=f"a {asset_id} illustration",
        prompt_hash=f"hash-{asset_id}",
        model="minimax-multimodal",
        created_at=created_at,
        provider="minimax",
    )


def _save_one(root: Path, meta: IllustrationMetadata) -> None:
    """Helper: persist an asset by writing .jpg + .meta.json sidecar."""
    from lingwen_illustrations.storage import save_asset

    save_asset(root, b"jpg-bytes-" + meta.id.encode(), meta)


def test_max_count_3_keep_all(tmp_path):
    """L1: 2 assets, max=3, no deletion."""
    from lingwen_illustrations.storage import lru_cleanup

    _save_one(tmp_path, _make_meta("a", "2026-09-01T00:00:00+00:00"))
    _save_one(tmp_path, _make_meta("b", "2026-09-02T00:00:00+00:00"))
    deleted = lru_cleanup(tmp_path, type="cover", max_count=3)
    assert deleted == []


def test_max_count_3_delete_1(tmp_path):
    """L2: 4 assets, max=3, oldest 1 deleted."""
    from lingwen_illustrations.storage import lru_cleanup

    _save_one(tmp_path, _make_meta("a", "2026-09-01T00:00:00+00:00"))
    _save_one(tmp_path, _make_meta("b", "2026-09-02T00:00:00+00:00"))
    _save_one(tmp_path, _make_meta("c", "2026-09-03T00:00:00+00:00"))
    _save_one(tmp_path, _make_meta("d", "2026-09-04T00:00:00+00:00"))
    deleted = lru_cleanup(tmp_path, type="cover", max_count=3)
    assert len(deleted) == 1
    assert deleted[0].id == "a"


def test_max_count_3_delete_2(tmp_path):
    """L3: 5 assets, max=3, oldest 2 deleted."""
    from lingwen_illustrations.storage import lru_cleanup

    for i, dt in enumerate([
        "2026-09-01T00:00:00+00:00",
        "2026-09-02T00:00:00+00:00",
        "2026-09-03T00:00:00+00:00",
        "2026-09-04T00:00:00+00:00",
        "2026-09-05T00:00:00+00:00",
    ]):
        _save_one(tmp_path, _make_meta(f"id{i}", dt))
    deleted = lru_cleanup(tmp_path, type="cover", max_count=3)
    assert len(deleted) == 2
    assert deleted[0].id == "id0"
    assert deleted[1].id == "id1"


def test_cover_scope_isolated(tmp_path):
    """L4: cover cleanup doesn't touch chapter assets."""
    from lingwen_illustrations.storage import lru_cleanup

    _save_one(tmp_path, _make_meta("cover-a", "2026-09-01T00:00:00+00:00", type="cover"))
    _save_one(tmp_path, _make_meta("cover-b", "2026-09-02T00:00:00+00:00", type="cover"))
    _save_one(
        tmp_path,
        _make_meta("ch1-a", "2026-09-01T00:00:00+00:00", type="chapter", chapter_num=1),
    )
    _save_one(
        tmp_path,
        _make_meta("ch1-b", "2026-09-02T00:00:00+00:00", type="chapter", chapter_num=1),
    )
    _save_one(
        tmp_path,
        _make_meta("ch1-c", "2026-09-03T00:00:00+00:00", type="chapter", chapter_num=1),
    )

    deleted = lru_cleanup(tmp_path, type="cover", max_count=1)
    assert len(deleted) == 1
    assert deleted[0].id == "cover-a"

    # Chapter assets untouched
    from lingwen_illustrations.storage import list_assets

    chapter_assets = [m for m in list_assets(tmp_path) if m.type == "chapter"]
    assert len(chapter_assets) == 3


def test_chapter_scope_isolated(tmp_path):
    """L5: chapter cleanup only affects the specified chapter_num."""
    from lingwen_illustrations.storage import lru_cleanup

    _save_one(
        tmp_path,
        _make_meta("ch1-a", "2026-09-01T00:00:00+00:00", type="chapter", chapter_num=1),
    )
    _save_one(
        tmp_path,
        _make_meta("ch1-b", "2026-09-02T00:00:00+00:00", type="chapter", chapter_num=1),
    )
    _save_one(
        tmp_path,
        _make_meta("ch2-a", "2026-09-01T00:00:00+00:00", type="chapter", chapter_num=2),
    )
    _save_one(
        tmp_path,
        _make_meta("ch2-b", "2026-09-02T00:00:00+00:00", type="chapter", chapter_num=2),
    )
    _save_one(
        tmp_path,
        _make_meta("ch2-c", "2026-09-03T00:00:00+00:00", type="chapter", chapter_num=2),
    )

    deleted = lru_cleanup(tmp_path, type="chapter", chapter_num=1, max_count=1)
    assert len(deleted) == 1
    assert deleted[0].id == "ch1-a"

    # Chapter 2 untouched
    from lingwen_illustrations.storage import list_assets

    ch2 = [m for m in list_assets(tmp_path) if m.chapter_num == 2]
    assert len(ch2) == 3


def test_max_count_zero_raises(tmp_path):
    """L6: max_count=0 raises StoreError."""
    from lingwen_illustrations.exceptions import StoreError
    from lingwen_illustrations.storage import lru_cleanup

    with pytest.raises(StoreError):
        lru_cleanup(tmp_path, type="cover", max_count=0)


def test_max_count_negative_raises(tmp_path):
    """L7: max_count<0 raises StoreError."""
    from lingwen_illustrations.exceptions import StoreError
    from lingwen_illustrations.storage import lru_cleanup

    with pytest.raises(StoreError):
        lru_cleanup(tmp_path, type="cover", max_count=-1)


def test_idempotent_on_missing_files(tmp_path):
    """L8: deletion is idempotent if files already missing."""
    from lingwen_illustrations.storage import asset_path, lru_cleanup

    _save_one(tmp_path, _make_meta("a", "2026-09-01T00:00:00+00:00"))
    _save_one(tmp_path, _make_meta("b", "2026-09-02T00:00:00+00:00"))
    _save_one(tmp_path, _make_meta("c", "2026-09-03T00:00:00+00:00"))
    # Manually delete oldest
    asset_path(tmp_path, type="cover", id="a").unlink()
    (asset_path(tmp_path, type="cover", id="a").with_suffix(".jpg.meta.json")).unlink()

    deleted = lru_cleanup(tmp_path, type="cover", max_count=2)
    # 'a' is gone (file missing), but list_assets already skips it; 'b' and 'c' remain.
    # lru_cleanup only operates on what list_assets returns.
    assert len(deleted) == 0  # 2 assets <= max_count=2


def test_chapter_num_none_for_cover_ok(tmp_path):
    """L9: type=cover doesn't require chapter_num."""
    from lingwen_illustrations.storage import lru_cleanup

    _save_one(tmp_path, _make_meta("a", "2026-09-01T00:00:00+00:00", type="cover"))
    # Should not raise even without chapter_num
    deleted = lru_cleanup(tmp_path, type="cover", max_count=10)
    assert deleted == []


def test_chapter_num_none_for_chapter_raises(tmp_path):
    """L10: type=chapter without chapter_num raises StoreError."""
    from lingwen_illustrations.exceptions import StoreError
    from lingwen_illustrations.storage import lru_cleanup

    with pytest.raises(StoreError):
        lru_cleanup(tmp_path, type="chapter", max_count=10)


def test_sort_tie_break_stable(tmp_path):
    """L11: same created_at uses id asc as deterministic tie-break."""
    from lingwen_illustrations.storage import lru_cleanup

    same_ts = "2026-09-01T00:00:00+00:00"
    _save_one(tmp_path, _make_meta("c", same_ts))
    _save_one(tmp_path, _make_meta("a", same_ts))
    _save_one(tmp_path, _make_meta("b", same_ts))
    deleted = lru_cleanup(tmp_path, type="cover", max_count=1)
    # Tie-break by id asc: a deleted first
    assert len(deleted) == 2
    assert deleted[0].id == "a"
    assert deleted[1].id == "b"


def test_no_assets_dir(tmp_path):
    """L12: fresh project with no assets/ returns empty list."""
    from lingwen_illustrations.storage import lru_cleanup

    deleted = lru_cleanup(tmp_path, type="cover", max_count=5)
    assert deleted == []
