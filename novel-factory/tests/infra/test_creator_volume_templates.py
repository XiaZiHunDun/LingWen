"""Tests for infra.creator_volume_templates."""
from __future__ import annotations

import pytest

from infra.creator_volume_templates import build_volume_template, list_volume_templates


def test_list_volume_templates():
    rows = list_volume_templates()
    ids = {row["id"] for row in rows}
    assert "three_act" in ids
    assert "five_volume" in ids


def test_build_three_act_template():
    volumes = build_volume_template("three_act", 40)
    assert len(volumes) == 3
    assert volumes[0]["start_chapter"] == 1
    assert volumes[-1]["end_chapter"] == 40


def test_build_companion_short():
    volumes = build_volume_template("companion_short", 12)
    assert len(volumes) == 1
    assert volumes[0]["end_chapter"] == 12


def test_unknown_template():
    with pytest.raises(ValueError):
        build_volume_template("nope", 10)
