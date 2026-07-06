"""Tests for creator writing agent plan API."""
from __future__ import annotations

from pathlib import Path

import pytest

from infra.creator_agent import iter_creator_agent_plan_stream, run_creator_agent_plan


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    root = tmp_path / "novel"
    chapters = root / "chapters"
    chapters.mkdir(parents=True)
    (chapters / "ch001.md").write_text("第一段\n\n第二段正文", encoding="utf-8")
    return root


class TestCreatorAgent:
    def test_chapter_scope_returns_candidates(self, project_root: Path) -> None:
        result = run_creator_agent_plan(
            project_root,
            action="path:faster",
            action_label="加快节奏",
            scope={"type": "chapter", "chapter": 1},
            body_draft="第一段\n\n第二段正文",
            style_strength=2,
            provider_mode="mock",
        )
        assert result["advice_only"] is False
        assert len(result["candidates"]) == 3
        assert result["provider"] == "mock"
        assert "第一段" in result["candidates"][0]["text"]

    def test_advice_only_when_style_strength_zero(self, project_root: Path) -> None:
        result = run_creator_agent_plan(
            project_root,
            action="rewrite:restrained",
            action_label="更克制",
            scope={"type": "selection", "selection_text": "选区文字"},
            style_strength=0,
            provider_mode="mock",
        )
        assert result["advice_only"] is True
        assert result["candidates"] == []
        assert len(result["advice"]) >= 3

    def test_selection_requires_text(self, project_root: Path) -> None:
        with pytest.raises(ValueError, match="selection_text"):
            run_creator_agent_plan(
                project_root,
                action="prompt",
                action_label="test",
                scope={"type": "selection"},
            )

    def test_goal_tag_adjusts_advice(self, project_root: Path) -> None:
        result = run_creator_agent_plan(
            project_root,
            action="path:faster",
            action_label="加快节奏",
            scope={"type": "selection", "selection_text": "x"},
            style_strength=0,
            goal_tag="suspense",
            provider_mode="mock",
        )
        texts = " ".join(a["text"] for a in result["advice"])
        assert "悬疑" in texts

    def test_editor_lens_returns_annotations(self, project_root: Path) -> None:
        result = run_creator_agent_plan(
            project_root,
            action="path:faster",
            action_label="加快节奏",
            scope={"type": "chapter", "chapter": 1},
            body_draft="第一段\n\n第二段正文",
            style_strength=2,
            lens="editor",
            provider_mode="mock",
        )
        assert result["lens"] == "editor"
        assert len(result["annotations"]) >= 2
        assert result["annotations"][0]["level"] in {"warn", "info", "error"}

    def test_reviewer_lens_advice_focus(self, project_root: Path) -> None:
        result = run_creator_agent_plan(
            project_root,
            action="path:conflict",
            action_label="加深冲突",
            scope={"type": "selection", "selection_text": "对白"},
            style_strength=0,
            lens="reviewer",
            provider_mode="mock",
        )
        assert result["lens"] == "reviewer"
        texts = " ".join(a["text"] for a in result["advice"])
        assert "读者" in texts or "信息" in texts

    def test_stream_yields_chunks_and_done(self, project_root: Path) -> None:
        events = list(
            iter_creator_agent_plan_stream(
                project_root,
                action="path:faster",
                action_label="加快节奏",
                scope={"type": "chapter", "chapter": 1},
                body_draft="第一段\n\n第二段正文",
                style_strength=2,
                provider_mode="mock",
            ),
        )
        types = [e["type"] for e in events]
        assert types[0] == "status"
        assert "chunk" in types
        assert types[-1] == "done"
        assert events[-1]["plan"]["candidates"]

    def test_stream_llm_tokens_when_provider_streams(self, project_root: Path, monkeypatch) -> None:
        payload = (
            '{"advice_only": false, "candidates": ['
            '{"id": "steady", "label": "稳健", "text": "流式正文"}, '
            '{"id": "balanced", "label": "平衡", "text": "二"}, '
            '{"id": "bold", "label": "大胆", "text": "三"}], '
            '"advice": [], "annotations": []}'
        )

        def fake_stream(_self, _task):
            yield payload[:20]
            yield payload[20:]

        monkeypatch.setattr("infra.creator_agent._has_llm_api_key", lambda: True)
        monkeypatch.setattr("infra.llm_service.LLMService.execute_stream", fake_stream)

        events = list(
            iter_creator_agent_plan_stream(
                project_root,
                action="path:faster",
                action_label="加快节奏",
                scope={"type": "chapter", "chapter": 1},
                body_draft="第一段\n\n第二段正文",
                style_strength=2,
                provider_mode="llm",
            ),
        )
        llm_chunks = [e for e in events if e.get("type") == "chunk" and e.get("source") == "llm"]
        assert len(llm_chunks) >= 2
        assert events[-1]["type"] == "done"
        assert events[-1]["plan"]["stream_mode"] == "llm_token"
        assert events[-1]["plan"]["candidates"][0]["text"] == "流式正文"
