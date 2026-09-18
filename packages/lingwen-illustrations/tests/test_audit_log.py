"""Audit log tests (Phase 98 A1-A4)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest


def test_append_and_read_back(tmp_path):
    """A1: write 3 events, read file, verify 3 lines + JSON parseable."""
    from lingwen_illustrations.audit_log import record_event
    from lingwen_illustrations.metadata import IllustrationMetadata

    meta = IllustrationMetadata(
        id="test-id",
        type="cover",
        chapter_num=None,
        created_at="2026-09-18T00:00:00+00:00",
        provider="minimax",
    )

    record_event(tmp_path, event="generation", asset_meta=meta, confirmed=True)
    record_event(tmp_path, event="regeneration", asset_meta=meta, bypassed=True)
    record_event(tmp_path, event="cleanup", asset_meta=meta)

    audit_path = tmp_path / ".lingwen" / "illustration_audit.jsonl"
    assert audit_path.exists()
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 3
    parsed = [json.loads(line) for line in lines]
    assert parsed[0]["event"] == "generation"
    assert parsed[0]["asset_id"] == "test-id"
    assert parsed[0]["confirmed"] is True
    assert parsed[1]["event"] == "regeneration"
    assert parsed[1]["bypassed"] is True
    assert parsed[2]["event"] == "cleanup"


def test_oserror_swallowed(tmp_path):
    """A2: OSError on file write is silently swallowed, no exception raised."""
    from lingwen_illustrations.audit_log import record_event

    # Patch open to raise OSError
    with patch("builtins.open", side_effect=OSError("readonly")):
        # Should NOT raise
        record_event(tmp_path, event="generation")


def test_parent_dir_created(tmp_path):
    """A3: parent .lingwen/ directory is auto-created."""
    from lingwen_illustrations.audit_log import record_event

    assert not (tmp_path / ".lingwen").exists()
    record_event(tmp_path, event="generation")
    assert (tmp_path / ".lingwen").exists()


def test_unicode_safe(tmp_path):
    """A4: Chinese characters in extra are JSON-safe (no escape issues)."""
    from lingwen_illustrations.audit_log import record_event

    record_event(tmp_path, event="generation", extra={"note": "中文测试 🌟"})

    audit_path = tmp_path / ".lingwen" / "illustration_audit.jsonl"
    raw = audit_path.read_text(encoding="utf-8")
    assert "中文测试 🌟" in raw
    parsed = json.loads(raw.strip())
    assert parsed["note"] == "中文测试 🌟"
