"""Tests for character markdown round-trip parser/serializer."""
from pathlib import Path

from infra.world_db.markdown_roundtrip import (
    parse_character_markdown,
    serialize_character_markdown,
)

SAMPLE_DIR = Path("docs/character-bible")


def test_parse_lin_ye():
    src = (SAMPLE_DIR / "林夜.md").read_text(encoding="utf-8")
    parsed = parse_character_markdown(src)
    assert parsed["slug"] == "lin-ye"
    assert "林夜" in parsed["name"]
    assert parsed["canon_level"] in ("Provisional", "Established", "Draft")
    assert "quick_ref" in parsed["attributes"]
    assert "appearance" in parsed["attributes"]


def test_round_trip_preserves_sections():
    src = (SAMPLE_DIR / "林夜.md").read_text(encoding="utf-8")
    parsed = parse_character_markdown(src)
    out = serialize_character_markdown(parsed)
    parsed2 = parse_character_markdown(out)
    # key data preserved (modulo formatting whitespace)
    assert parsed2["slug"] == parsed["slug"]
    assert parsed2["name"] == parsed["name"]
    assert parsed2["canon_level"] == parsed["canon_level"]
    assert parsed2["attributes"].get("appearance") == \
           parsed["attributes"].get("appearance")
