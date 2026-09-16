"""Tests for bible_loader.load_character_bible (Phase 91)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest

from lingwen_illustrations.bible_loader import load_character_bible
from lingwen_illustrations.exceptions import LoadError


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Empty project root, no config/illustrations/ directory."""
    return tmp_path


@pytest.fixture
def bible_dir(tmp_project: Path) -> Path:
    """Pre-created config/illustrations/ directory."""
    d = tmp_project / "config" / "illustrations"
    d.mkdir(parents=True)
    return d


def _write_bible(bible_dir: Path, content: str) -> None:
    (bible_dir / "characters.json").write_text(content, encoding="utf-8")


# ─── T1: file missing ─────────────────────────────────────────────
def test_missing_file_returns_empty_list_with_info_log(
    tmp_project: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Missing bible file is silent (v1 philosophy) + INFO log."""
    caplog.set_level(logging.INFO)
    result = load_character_bible(tmp_project)
    assert result == []
    assert any(
        "character bible not found" in record.message
        for record in caplog.records
    )


# ─── T2: empty array ──────────────────────────────────────────────
def test_empty_array_returns_empty_list(bible_dir: Path, tmp_project: Path) -> None:
    """Empty array equivalent to missing file."""
    _write_bible(bible_dir, "[]")
    result = load_character_bible(tmp_project)
    assert result == []


# ─── T3: single valid character ───────────────────────────────────
def test_single_valid_character(bible_dir: Path, tmp_project: Path) -> None:
    """Single character with all 3 fields round-trips correctly."""
    bible = [
        {"name": "林夜", "role": "主角", "description": "身穿黑色风衣的青年剑客"}
    ]
    _write_bible(bible_dir, json.dumps(bible, ensure_ascii=False))
    result = load_character_bible(tmp_project)
    assert result == bible


# ─── T4: multiple valid characters ────────────────────────────────
def test_multiple_valid_characters(bible_dir: Path, tmp_project: Path) -> None:
    """3 characters in order."""
    bible = [
        {"name": "林夜", "role": "主角", "description": "青年剑客"},
        {"name": "苏琳", "role": "女主", "description": "神秘少女"},
        {"name": "星月", "role": "配角", "description": "白发老者"},
    ]
    _write_bible(bible_dir, json.dumps(bible, ensure_ascii=False))
    result = load_character_bible(tmp_project)
    assert result == bible


# ─── T5: malformed JSON ───────────────────────────────────────────
def test_malformed_json_raises_loaderror(bible_dir: Path, tmp_project: Path) -> None:
    """JSON parse error wrapped as LoadError."""
    _write_bible(bible_dir, "{not json}")
    with pytest.raises(LoadError, match="failed to load character bible"):
        load_character_bible(tmp_project)


# ─── T6: non-list root ────────────────────────────────────────────
def test_non_list_root_raises_loaderror(bible_dir: Path, tmp_project: Path) -> None:
    """Root must be a list, not dict/str/etc."""
    _write_bible(bible_dir, "{}")
    with pytest.raises(LoadError, match="must be a list"):
        load_character_bible(tmp_project)


# ─── T7: item missing name field ──────────────────────────────────
def test_item_missing_name_raises_loaderror(bible_dir: Path, tmp_project: Path) -> None:
    """name is the anchor field — missing name is LoadError."""
    _write_bible(bible_dir, '[{"role": "x", "description": "y"}]')
    with pytest.raises(LoadError, match="missing required 'name'"):
        load_character_bible(tmp_project)


# ─── T8: item with empty name ──────────────────────────────────────
def test_item_empty_name_raises_loaderror(bible_dir: Path, tmp_project: Path) -> None:
    """Empty name string is equivalent to missing name."""
    _write_bible(bible_dir, '[{"name": "", "role": "x"}]')
    with pytest.raises(LoadError, match="'name' is empty"):
        load_character_bible(tmp_project)


# ─── T9: item with non-str name ────────────────────────────────────
def test_item_non_str_name_raises_loaderror(bible_dir: Path, tmp_project: Path) -> None:
    """name must be a string (not int/float/bool/etc)."""
    _write_bible(bible_dir, '[{"name": 123}]')
    with pytest.raises(LoadError, match="'name' must be str"):
        load_character_bible(tmp_project)


# ─── T10: item missing role defaults to empty ─────────────────────
def test_item_missing_role_defaults_to_empty(bible_dir: Path, tmp_project: Path) -> None:
    """role is optional — missing role defaults to ''."""
    _write_bible(bible_dir, '[{"name": "x", "description": "y"}]')
    result = load_character_bible(tmp_project)
    assert result == [{"name": "x", "role": "", "description": "y"}]


# ─── T11: item missing description defaults to empty ──────────────
def test_item_missing_description_defaults_to_empty(
    bible_dir: Path, tmp_project: Path
) -> None:
    """description is optional — missing description defaults to ''."""
    _write_bible(bible_dir, '[{"name": "x", "role": "y"}]')
    result = load_character_bible(tmp_project)
    assert result == [{"name": "x", "role": "y", "description": ""}]


# ─── T12: extra fields silently ignored ───────────────────────────
def test_item_extra_fields_ignored(bible_dir: Path, tmp_project: Path) -> None:
    """Extra fields like image_url are silently dropped (forward-compat)."""
    _write_bible(
        bible_dir,
        '[{"name": "x", "role": "y", "description": "z", "image_url": "http://..."}]',
    )
    result = load_character_bible(tmp_project)
    assert result == [{"name": "x", "role": "y", "description": "z"}]


# ─── T13: OSError wrapped as LoadError ────────────────────────────
def test_oserror_wrapped_as_loaderror(
    bible_dir: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """OSError (perm denied, etc.) is wrapped as LoadError."""
    real_read_text = Path.read_text

    def deny_read(self: Path, *args: Any, **kwargs: Any) -> str:
        if self.name == "characters.json":
            raise OSError("Permission denied")
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", deny_read)
    _write_bible(bible_dir, "[]")

    with pytest.raises(LoadError, match="failed to load character bible"):
        load_character_bible(tmp_project)


# ─── T14: parametrized non-str name cases (defensive) ─────────────
@pytest.mark.parametrize("bad_name", [123, 1.5, True, None, [], {}])
def test_item_non_str_name_raises_parametrized(
    bible_dir: Path, tmp_project: Path, bad_name: Any
) -> None:
    """name must be str — int/float/bool/None/list/dict all rejected.

    Note: `isinstance(True, int)` is True in Python, but the explicit
    str check correctly rejects bool. This test ensures type defense
    is robust across Python's loose type system.
    """
    _write_bible(bible_dir, f'[{{"name": {json.dumps(bad_name)}}}]')
    with pytest.raises(LoadError, match="'name' must be str"):
        load_character_bible(tmp_project)
