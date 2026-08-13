"""Phase 17.15 守卫:.skills/ 已迁到 content/roles/<role>/skills/。

旧布局:
    .skills/<dept>/<slug>/SKILL.md

新布局:
    content/roles/<role>/skills/<slug>/SKILL.md
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def test_no_top_level_skills_dir():
    """Top-level .skills/ 不应存在(已迁到 content/roles/<role>/skills/)。"""
    skills = REPO / ".skills"
    assert not (skills.exists() and skills.is_dir()), (
        ".skills/ should have moved to content/roles/<role>/skills/ in 17.15"
    )


def test_content_roles_have_skills_subdirs():
    """content/roles/{writer,reviewer,reader}/ 下应有 skills/ 子目录。"""
    for role in ("writer", "reviewer", "reader"):
        skills = REPO / "content" / "roles" / role / "skills"
        assert skills.is_dir(), f"Missing {skills}"
