"""Phase 17.16 守卫:角色池 registry.yaml 自动生成 + SKILL.md 存在。"""

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]


def test_writer_registry_exists():
    p = REPO / "content" / "roles" / "writer" / "registry.yaml"
    assert p.exists(), "writer registry.yaml should exist"
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    skills = {s["slug"] for s in data.get("skills", [])}
    expected = {f"writer-{c}" for c in "abcdefghij"}
    assert skills >= expected, f"Expected at least {expected}, got {skills}"


def test_reviewer_registry_exists():
    p = REPO / "content" / "roles" / "reviewer" / "registry.yaml"
    assert p.exists(), "reviewer registry.yaml should exist"
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    skills = {s["slug"] for s in data.get("skills", [])}
    expected = {f"reviewer-{c}" for c in "abcdefghijk"}
    assert skills >= expected, f"Expected at least {expected}, got {skills}"


def test_reader_registry_exists():
    p = REPO / "content" / "roles" / "reader" / "registry.yaml"
    assert p.exists(), "reader registry.yaml should exist"
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    skills = {s["slug"] for s in data.get("skills", [])}
    expected = {f"reader-{c}" for c in "abcdefghijklmnopqrst"}
    assert skills >= expected, f"Expected at least {expected}, got {skills}"


def test_writer_skill_md_present():
    """Each writer entry should have a SKILL.md in its skill dir."""
    p = REPO / "content" / "roles" / "writer" / "skills"
    for letter in "abcdefghij":
        assert (p / f"writer-{letter}" / "SKILL.md").exists(), f"Missing writer-{letter}/SKILL.md"
