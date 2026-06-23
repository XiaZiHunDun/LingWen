"""Tests for infra.project_init minimal-short scaffold."""
from __future__ import annotations

import os

import pytest
import yaml

from infra.agent_system.chapter_production_outline import build_canon_initial_inputs
from infra.agent_system.chapter_production_pilot import preflight_checklist
from infra.paths import ProjectPaths
from infra.project_config import ProjectConfig
from infra.project_init import init_minimal_short_project, validate_slug


@pytest.fixture
def factory_tmp(tmp_path, monkeypatch):
    ProjectPaths.reset()
    monkeypatch.chdir(tmp_path)
    factory = tmp_path / "factory"
    factory.mkdir()
    (factory / "infra").mkdir()
    yield factory
    ProjectPaths.reset()


def test_validate_slug():
    assert validate_slug("anye-xinbiao") == "anye-xinbiao"
    with pytest.raises(ValueError):
        validate_slug("Bad Slug!")


def test_init_minimal_short_project(factory_tmp):
    result = init_minimal_short_project(
        slug="demo-short",
        title="暗夜信标",
        protagonist="沈柯",
        factory_root=factory_tmp,
        creation_mode="studio",
    )
    assert result.root.is_dir()
    assert (result.root / "config/project.yaml").is_file()
    assert (result.root / "03_内容仓库/04_正文/ch001_大纲.md").is_file()
    assert (result.root / "03_内容仓库/04_正文/ch010_大纲.md").is_file()
    assert result.chapter_count == 10
    assert result.creation_mode == "studio"


def test_init_companion_15_chapters(factory_tmp):
    result = init_minimal_short_project(
        slug="companion-15",
        title="陪伴长篇",
        factory_root=factory_tmp,
        creation_mode="companion",
        chapter_count=15,
    )
    assert (result.root / "03_内容仓库/04_正文/ch015_大纲.md").is_file()
    data = yaml.safe_load((result.root / "config/project.yaml").read_text(encoding="utf-8"))
    assert data["project"]["creation_mode"] == "companion"
    assert data["project"]["quality_profile"] == "creator_relaxed"


def test_init_project_preflight_passes_ch1(factory_tmp, monkeypatch):
    result = init_minimal_short_project(
        slug="demo-short",
        title="暗夜信标",
        factory_root=factory_tmp,
        creation_mode="studio",
    )
    ProjectPaths.reset()
    monkeypatch.setenv("LINGWEN_PROJECT_ROOT", str(result.root))
    monkeypatch.setenv("LINGWEN_PRODUCTION_MODE", "canon")
    monkeypatch.setenv("LINGWEN_REAL_LLM", "1")
    monkeypatch.setenv("MINIMAX_API_KEY", "test-key")

    cfg = ProjectConfig.load()
    assert cfg.role == "production"
    assert cfg.max_chapter == 10

    ok, msg = cfg.validate_production(1, mode="canon")
    assert ok, msg

    checks = preflight_checklist(chapter_num=1)
    gate = next(c for c in checks if c.name == "project_production_gate")
    assert gate.passed

    inputs = build_canon_initial_inputs(1)
    assert inputs["outline"]["title"] == "暗夜信标"
    assert inputs["outline"]["chapters"][0]["title"].startswith("第1章")


def test_init_project_cli_smoke(factory_tmp, monkeypatch):
    result = init_minimal_short_project(
        slug="cli-demo",
        title="测试短篇",
        factory_root=factory_tmp,
        creation_mode="studio",
    )
    data = yaml.safe_load((result.root / "config/project.yaml").read_text(encoding="utf-8"))
    assert data["project"]["slug"] == "cli-demo"
