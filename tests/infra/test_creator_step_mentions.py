"""Tests for wizard step @mentions."""
from __future__ import annotations

from infra.creator_onboarding_progress import (
    build_step_mentions,
    extract_step_mentions,
)


def test_extract_step_mentions() -> None:
    assert extract_step_mentions("请 @volume 先锁卷纲，@Reviewer 看一下") == [
        "volume",
        "reviewer",
    ]


def test_build_step_mentions() -> None:
    notes = {"volume": "找 @batch 协助"}
    assert build_step_mentions(notes) == {"volume": ["batch"]}
