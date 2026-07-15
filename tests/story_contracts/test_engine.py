"""Tests for StoryContractEngine."""

import json
from pathlib import Path

import pytest

from infra.story_contracts.engine import StoryContractEngine
from infra.story_contracts.paths import StoryContractPaths


class TestStoryContractEngine:
    """Tests for StoryContractEngine."""

    def test_engine_initialization(self, tmp_path):
        """Test engine initializes with correct paths."""
        engine = StoryContractEngine(project_root=tmp_path)

        assert engine.project_root == tmp_path
        assert isinstance(engine.paths, StoryContractPaths)
        assert engine.paths.project_root == tmp_path

    def test_build_creates_payload_with_master_setting(self, tmp_path):
        """Test build creates ContractPayload with master_setting."""
        # Create minimal CSV
        csv_dir = tmp_path / "rules" / "story_contracts"
        csv_dir.mkdir(parents=True)
        self._write_csv(
            csv_dir / "题材与调性推理.csv",
            ["编号", "分类", "关键词", "意图与同义词", "题材/流派", "题材别名", "核心调性", "节奏策略", "强制禁忌/毒点", "推荐基础检索表", "推荐动态检索表"],
            [
                {
                    "编号": "GR-001",
                    "分类": "题材路由",
                    "关键词": "玄幻退婚流",
                    "意图与同义词": "退婚流",
                    "题材/流派": "玄幻退婚流",
                    "题材别名": "退婚流",
                    "核心调性": "压抑蓄势后爆裂反击",
                    "节奏策略": "前压后爆",
                    "强制禁忌/毒点": "打脸节奏不能缺最后一拍补刀",
                    "推荐基础检索表": "命名规则",
                    "推荐动态检索表": "桥段套路",
                }
            ],
        )

        engine = StoryContractEngine(project_root=tmp_path, rules_dir=csv_dir)
        payload = engine.build(query="主角被退婚", genre=None)

        assert payload.master_setting is not None
        assert payload.master_setting["meta"]["contract_type"] == "MASTER_SETTING"
        assert payload.master_setting["route"]["primary_genre"] == "玄幻退婚流"
        assert payload.master_setting["master_constraints"]["core_tone"] == "压抑蓄势后爆裂反击"

    def test_build_creates_anti_patterns_from_route(self, tmp_path):
        """Test build creates anti-patterns list from route result."""
        csv_dir = tmp_path / "rules" / "story_contracts"
        csv_dir.mkdir(parents=True)
        self._write_csv(
            csv_dir / "题材与调性推理.csv",
            ["编号", "分类", "关键词", "意图与同义词", "题材/流派", "题材别名", "核心调性", "节奏策略", "强制禁忌/毒点", "推荐基础检索表", "推荐动态检索表"],
            [
                {
                    "编号": "GR-001",
                    "分类": "题材路由",
                    "关键词": "都市",
                    "意图与同义词": "",
                    "题材/流派": "都市",
                    "题材别名": "",
                    "核心调性": "都市节奏",
                    "节奏策略": "快节奏",
                    "强制禁忌/毒点": "配角抢戏|主角光环缺失",
                    "推荐基础检索表": "",
                    "推荐动态检索表": "",
                }
            ],
        )

        engine = StoryContractEngine(project_root=tmp_path, rules_dir=csv_dir)
        payload = engine.build(query="都市生活", genre=None)

        assert payload.anti_patterns is not None
        assert len(payload.anti_patterns) == 2
        texts = [ap["text"] for ap in payload.anti_patterns]
        assert "配角抢戏" in texts
        assert "主角光环缺失" in texts

    def test_build_with_chapter_creates_chapter_brief(self, tmp_path):
        """Test build with chapter number creates chapter_brief."""
        csv_dir = tmp_path / "rules" / "story_contracts"
        csv_dir.mkdir(parents=True)
        self._write_csv(
            csv_dir / "题材与调性推理.csv",
            ["编号", "分类", "关键词", "意图与同义词", "题材/流派", "题材别名", "核心调性", "节奏策略", "强制禁忌/毒点", "推荐基础检索表", "推荐动态检索表"],
            [
                {
                    "编号": "GR-001",
                    "分类": "题材路由",
                    "关键词": "都市",
                    "意图与同义词": "",
                    "题材/流派": "都市",
                    "题材别名": "",
                    "核心调性": "都市节奏",
                    "节奏策略": "快节奏",
                    "强制禁忌/毒点": "",
                    "推荐基础检索表": "",
                    "推荐动态检索表": "",
                }
            ],
        )

        engine = StoryContractEngine(project_root=tmp_path, rules_dir=csv_dir)
        payload = engine.build(query="都市故事", genre=None, chapter=5)

        assert payload.chapter_brief is not None
        assert payload.chapter_brief["chapter_number"] == 5
        assert payload.chapter_brief["chapter_constraints"]["tone"] == "都市节奏"

    def test_persist_and_load_round_trip(self, tmp_path):
        """Test persist and load produce equivalent payloads."""
        csv_dir = tmp_path / "rules" / "story_contracts"
        csv_dir.mkdir(parents=True)
        self._write_csv(
            csv_dir / "题材与调性推理.csv",
            ["编号", "分类", "关键词", "意图与同义词", "题材/流派", "题材别名", "核心调性", "节奏策略", "强制禁忌/毒点", "推荐基础检索表", "推荐动态检索表"],
            [
                {
                    "编号": "GR-001",
                    "分类": "题材路由",
                    "关键词": "玄幻",
                    "意图与同义词": "",
                    "题材/流派": "玄幻",
                    "题材别名": "",
                    "核心调性": "玄幻基调",
                    "节奏策略": "爆发",
                    "强制禁忌/毒点": "战力崩",
                    "推荐基础检索表": "",
                    "推荐动态检索表": "",
                }
            ],
        )

        engine = StoryContractEngine(project_root=tmp_path, rules_dir=csv_dir)
        original = engine.build(query="玄幻世界", genre=None)
        engine.persist(original)

        loaded = engine.load()

        assert loaded is not None
        assert loaded.master_setting["route"]["primary_genre"] == "玄幻"
        assert len(loaded.anti_patterns) == 1

    def test_load_returns_none_when_no_contract(self, tmp_path):
        """Test load returns None when no contract exists."""
        engine = StoryContractEngine(project_root=tmp_path)
        loaded = engine.load()

        assert loaded is None

    def _write_csv(self, path: Path, headers: list[str], rows: list[dict]) -> None:
        """Write a CSV file for testing."""
        import csv

        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
