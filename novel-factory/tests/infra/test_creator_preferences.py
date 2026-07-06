"""Tests for creator_preferences."""
from __future__ import annotations

from pathlib import Path

from infra.creator_preferences import (
    load_creator_preferences,
    normalize_creator_preferences,
    save_creator_preferences,
)


def test_normalize_defaults() -> None:
    prefs = normalize_creator_preferences(None)
    assert prefs["default_model"] == "minimax-abab6.5"
    assert prefs["task_models"]["body"] == "inherit"
    assert prefs["intervention_rules"]["logic_p0"] is True


def test_intervention_rules_roundtrip(tmp_path) -> None:
    save_creator_preferences(
        tmp_path,
        {"intervention_rules": {"batch_progress": False, "empty_write_hint": False}},
    )
    loaded = load_creator_preferences(tmp_path)
    assert loaded["intervention_rules"]["batch_progress"] is False
    assert loaded["intervention_rules"]["empty_write_hint"] is False
    assert loaded["intervention_rules"]["logic_p0"] is True


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    save_creator_preferences(
        tmp_path,
        {
            "temperature": 0.2,
            "memory_rag_enabled": False,
            "task_models": {"body": "gpt-4o"},
        },
    )
    loaded = load_creator_preferences(tmp_path)
    assert loaded["temperature"] == 0.2
    assert loaded["memory_rag_enabled"] is False
    assert loaded["task_models"]["body"] == "gpt-4o"
