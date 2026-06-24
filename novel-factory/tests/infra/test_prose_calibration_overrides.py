"""Tests for prose calibration human overrides."""
from __future__ import annotations

from pathlib import Path

from infra.prose_calibration_overrides import (
    apply_calibration_overrides,
    load_yaml_overrides,
    override_key,
    parse_markdown_log_overrides,
    save_yaml_override,
)


def test_parse_markdown_log_overrides() -> None:
    text = """
### demo-book

| 章 | issue_type | 留/删/疑 | 备注 |
|----|------------|----------|------|
| ch001 | `sentence_diversity_low` | 删 | 人工覆写 |
"""
    path = Path("/tmp/prose-calibration-log-sample.md")
    path.write_text(text, encoding="utf-8")
    overrides = parse_markdown_log_overrides(path)
    key = override_key("demo-book", 1, "sentence_diversity_low")
    assert overrides[key]["verdict"] == "删"
    path.unlink(missing_ok=True)


def test_yaml_override_roundtrip(tmp_path: Path) -> None:
    yaml_path = tmp_path / "overrides.yaml"
    save_yaml_override(
        "demo-book",
        3,
        "sentence_diversity_low",
        verdict="疑",
        note="边界",
        path=yaml_path,
    )
    loaded = load_yaml_overrides(yaml_path)
    key = override_key("demo-book", 3, "sentence_diversity_low")
    assert loaded[key]["verdict"] == "疑"
    samples = apply_calibration_overrides(
        [{"chapter": 3, "issue_type": "sentence_diversity_low", "verdict": "留", "note": ""}],
        slug="demo-book",
        overrides=loaded,
    )
    assert samples[0]["verdict"] == "疑"
    assert samples[0]["note"] == "边界"
