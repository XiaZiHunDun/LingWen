"""Tests for emit_chapter disk persistence."""
from __future__ import annotations

import json
import os

import pytest

from infra.agent_system.chapter_emit import (
    emit_chapter_enabled,
    emit_chapter_to_repo,
)
from infra.agent_system.got_bridge import AgentComputeFn
from infra.got.data_structures import NodeType, ThoughtNode
from infra.paths import ProjectPaths


@pytest.fixture
def isolated_paths(tmp_path, monkeypatch):
    ProjectPaths._instance = None
    (tmp_path / "03_内容仓库" / "04_正文").mkdir(parents=True)
    (tmp_path / "03_内容仓库" / "角色设定").mkdir(parents=True)
    (tmp_path / "03_内容仓库" / "角色设定" / "character_profiles.json").write_text(
        "{}", encoding="utf-8",
    )
    index_script = tmp_path / "03_内容仓库" / "update_index.py"
    index_script.write_text(
        "def update_chapter_index():\n"
        "    from pathlib import Path\n"
        "    import json\n"
        "    chapters_dir = Path(__file__).parent / '04_正文'\n"
        "    (chapters_dir / 'index.json').write_text(json.dumps({'ok': True}), encoding='utf-8')\n",
        encoding="utf-8",
    )
    paths = ProjectPaths.get(tmp_path)
    monkeypatch.chdir(tmp_path)
    yield paths
    ProjectPaths._instance = None


class TestEmitChapterEnabled:
    def test_off_by_default(self, monkeypatch):
        monkeypatch.delenv("LINGWEN_EMIT_CHAPTER", raising=False)
        monkeypatch.delenv("LINGWEN_REAL_LLM", raising=False)
        assert emit_chapter_enabled() is False

    def test_on_when_real_llm(self, monkeypatch):
        monkeypatch.setenv("LINGWEN_REAL_LLM", "1")
        monkeypatch.delenv("LINGWEN_EMIT_CHAPTER", raising=False)
        assert emit_chapter_enabled() is True

    def test_explicit_off_overrides_real_llm(self, monkeypatch):
        monkeypatch.setenv("LINGWEN_REAL_LLM", "1")
        monkeypatch.setenv("LINGWEN_EMIT_CHAPTER", "0")
        assert emit_chapter_enabled() is False


class TestEmitChapterToRepo:
    def test_writes_markdown_and_index(self, isolated_paths):
        result = emit_chapter_to_repo(
            chapter_num=367,
            content="# 第367章 测试\n\n正文。",
            paths=isolated_paths,
        )
        chapter_path = isolated_paths.get_chapter_path(367)
        assert chapter_path.is_file()
        assert chapter_path.read_text(encoding="utf-8").startswith("# 第367章")
        assert result["written"] is True
        assert result["index_updated"] is True
        index_path = isolated_paths.chapters / "index.json"
        assert index_path.is_file()
        assert json.loads(index_path.read_text(encoding="utf-8")) == {"ok": True}


class TestAgentComputeFnEmitChapter:
    def test_emit_writes_when_enabled(self, isolated_paths, monkeypatch):
        monkeypatch.setenv("LINGWEN_EMIT_CHAPTER", "1")

        class _Master:
            _last_initial_inputs = {"chapter_num": 368}

        compute = AgentComputeFn(_Master())
        node = ThoughtNode(
            node_id="emit_chapter",
            type=NodeType.OUTPUT,
            name="Emit Chapter",
            description="emit",
            prompt_scenario=None,
        )
        result = compute(
            node,
            {"polish_merge": {"content": "# 第368章\n\n落盘测试。"}},
        )

        assert result.fail is False
        assert result.output["written"] is True
        assert isolated_paths.get_chapter_path(368).is_file()

    def test_emit_skipped_when_disabled(self, isolated_paths, monkeypatch):
        monkeypatch.delenv("LINGWEN_EMIT_CHAPTER", raising=False)
        monkeypatch.delenv("LINGWEN_REAL_LLM", raising=False)

        class _Master:
            _last_initial_inputs = {"chapter_num": 369}

        compute = AgentComputeFn(_Master())
        node = ThoughtNode(
            node_id="emit_chapter",
            type=NodeType.OUTPUT,
            name="Emit Chapter",
            description="emit",
            prompt_scenario=None,
        )
        result = compute(node, {"polish_merge": {"content": "stub content"}})

        assert result.fail is False
        assert result.output["written"] is False
        assert not isolated_paths.get_chapter_path(369).exists()

    def test_emit_fails_without_content(self, monkeypatch):
        monkeypatch.setenv("LINGWEN_EMIT_CHAPTER", "1")
        compute = AgentComputeFn(type("_M", (), {"_last_initial_inputs": {"chapter_num": 1}})())
        node = ThoughtNode(
            node_id="emit_chapter",
            type=NodeType.OUTPUT,
            name="Emit Chapter",
            description="emit",
            prompt_scenario=None,
        )
        result = compute(node, {"polish_merge": {}})
        assert result.fail is True
        assert "content is required" in (result.error or "")
