"""Tests for infra.creator_check."""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from infra.cli.options import CheckOptions
from infra.creator_check import apply_creator_check_defaults
from infra.creator_mode import CREATION_MODE_COMPANION, CREATION_MODE_STUDIO
from infra.paths import ProjectPaths


@dataclass
class _Opts:
    quick: bool = False
    full: bool = True
    llm: bool = False
    limit: int = 20
    fail_severity: str | None = None


@pytest.fixture
def companion_project(tmp_path):
    ProjectPaths._instance = None
    (tmp_path / "03_内容仓库" / "04_正文").mkdir(parents=True)
    (tmp_path / "03_内容仓库" / "角色设定").mkdir(parents=True)
    (tmp_path / "03_内容仓库" / "角色设定" / "character_profiles.json").write_text(
        "{}", encoding="utf-8",
    )
    (tmp_path / "config").mkdir(parents=True)
    (tmp_path / "config" / "project.yaml").write_text(
        """
project:
  name: Companion Book
  slug: companion-book
  creation_mode: companion
  max_chapter: 10
  pillars_path: docs/novel-pillars.md
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "docs" / "novel-pillars.md").write_text("# pillars", encoding="utf-8")
    paths = ProjectPaths.get(tmp_path)
    yield paths
    ProjectPaths._instance = None


def test_apply_companion_defaults_fail_p0(companion_project):
    opts = CheckOptions(full=True, llm=True)
    updated, config, settings = apply_creator_check_defaults(
        opts,
        paths=companion_project,
        fail_severity_explicit=False,
    )
    assert config.creation_mode == CREATION_MODE_COMPANION
    assert updated.fail_severity == "P0"
    assert updated.llm is False
    assert not settings.run_llm_judge


def test_explicit_fail_severity_not_overridden(companion_project):
    opts = CheckOptions(full=True, fail_severity="P2")
    updated, _, _ = apply_creator_check_defaults(
        opts,
        paths=companion_project,
        fail_severity_explicit=True,
    )
    assert updated.fail_severity == "P2"


def test_studio_project_keeps_llm_when_requested(tmp_path):
    ProjectPaths._instance = None
    (tmp_path / "03_内容仓库" / "04_正文").mkdir(parents=True)
    (tmp_path / "03_内容仓库" / "角色设定").mkdir(parents=True)
    (tmp_path / "03_内容仓库" / "角色设定" / "character_profiles.json").write_text(
        "{}", encoding="utf-8",
    )
    (tmp_path / "config").mkdir(parents=True)
    (tmp_path / "config" / "project.yaml").write_text(
        """
project:
  name: Studio Book
  slug: studio-book
  creation_mode: studio
  max_chapter: 10
  pillars_path: docs/novel-pillars.md
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "docs" / "novel-pillars.md").write_text("# pillars", encoding="utf-8")
    paths = ProjectPaths.get(tmp_path)

    opts = CheckOptions(full=True, llm=True)
    updated, config, settings = apply_creator_check_defaults(
        opts,
        paths=paths,
        fail_severity_explicit=False,
    )
    assert config.creation_mode == CREATION_MODE_STUDIO
    assert updated.llm is True
    assert settings.run_llm_judge
    ProjectPaths._instance = None
