"""Tests for infra.llm_benchmarks.fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from infra.llm_benchmarks.fixtures import (
    CHAPTER_IDS,
    CHARACTER_SLUG,
    load_golden_chapters,
)


def test_constants_are_set():
    assert CHARACTER_SLUG == "林栀"
    assert CHAPTER_IDS == [1, 3, 10]


def test_load_golden_chapters_returns_three_strings(monkeypatch):
    fake_root = Path("/tmp/lingwen-test-projects-root")
    proj = fake_root / "huiyu-dangan" / "golden-set" / "chapters"
    proj.mkdir(parents=True, exist_ok=True)
    # Overwrite chapter content in case dir persists from previous run
    (proj / "ch001.md").write_text("林栀 chapter 1", encoding="utf-8")
    (proj / "ch003.md").write_text("林栀 chapter 3", encoding="utf-8")
    (proj / "ch010.md").write_text("林栀 chapter 10", encoding="utf-8")
    monkeypatch.setenv("LINGWEN_PROJECTS_ROOT", str(fake_root))

    chapters = load_golden_chapters("huiyu-dangan", [1, 3, 10])
    assert len(chapters) == 3
    assert chapters[0] == "林栀 chapter 1"
    assert chapters[1] == "林栀 chapter 3"
    assert chapters[2] == "林栀 chapter 10"


def test_load_golden_chapters_raises_on_missing_file(monkeypatch):
    fake_root = Path("/tmp/lingwen-empty-projects-root")
    fake_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("LINGWEN_PROJECTS_ROOT", str(fake_root))

    with pytest.raises(FileNotFoundError, match="ch001.md"):
        load_golden_chapters("huiyu-dangan", [1])
