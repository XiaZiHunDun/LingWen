"""Tests for post-v7.0 product features: share collab v2, diff collab notes."""
from __future__ import annotations

from infra.creator_diff_collab import (
    load_diff_collab_notes,
    merge_diff_collab_notes,
    save_diff_collab_notes,
)
from infra.creator_ui_profile import resolve_creator_ui_profile
from infra.creator_volume_plan_share import decode_share_token, encode_share_token


def test_advance_post_v7_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_share_collab_v2"] is True


def test_companion_post_v7_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="companion")
    assert profile.get("volume_plan_diff_share_collab_v2") is not True


def test_share_token_v3_roundtrip() -> None:
    token = encode_share_token(
        changes=[{"type": "changed", "label": "一", "message": "冲突更新"}],
        draft_volumes=[
            {
                "label": "一",
                "start_chapter": 1,
                "end_chapter": 5,
                "core_conflict": "主线",
                "locked": False,
            }
        ],
        collab_notes={"一": "请 @reviewer 确认卷纲"},
    )
    parsed = decode_share_token(token)
    assert parsed["valid"] is True
    assert parsed["version"] == 3
    assert parsed["has_collab_notes"] is True
    assert parsed["collab_notes"]["一"] == "请 @reviewer 确认卷纲"
    assert parsed["can_apply"] is True


def test_diff_collab_notes_persist(tmp_path) -> None:
    root = tmp_path
    saved = save_diff_collab_notes(root, {"一": "先锁卷纲"})
    assert saved["一"] == "先锁卷纲"
    merged = merge_diff_collab_notes(load_diff_collab_notes(root), {"二": "待审"})
    save_diff_collab_notes(root, merged)
    loaded = load_diff_collab_notes(root)
    assert loaded["一"] == "先锁卷纲"
    assert loaded["二"] == "待审"
