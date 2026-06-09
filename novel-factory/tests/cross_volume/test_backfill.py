"""Phase 9.11: Backfiller + 4 Extractor + CLI tests.

TDD: 这些测试在 step 1 阶段会全部 FAIL (ImportError on Backfiller / 4 Extractor),
在 Task 2 (Extractor impl) + Task 3 (Backfiller + storage.append_nodes_atomic) + Task 4 (CLI) + Task 5 (fixture) 后通过.
"""
import yaml
import pytest
from pathlib import Path

from infra.cross_volume import ReferenceNode
from infra.cross_volume.storage import RippleStorage
from infra.cross_volume.backfill import Backfiller, BackfillStats
from infra.cross_volume.extractors import (
    CharacterExtractor,
    ForeshadowExtractor,
    SettingExtractor,
    PlotPointExtractor,
)
from infra.cross_volume.reference_graph import CrossVolumeReferenceGraph


# ============ 4 Extractor unit tests (8 tests) ============

class TestCharacterExtractor:
    @pytest.fixture
    def rules(self):
        return {
            "name_pattern": "[李青云林凡]{2,3}",
            "alias_map": {"凡": "林凡"},
            "blacklist": ["那个", "什么"],
            "occurrence_threshold": 1,
        }

    @pytest.fixture
    def extractor(self, rules):
        return CharacterExtractor(rules=rules, volume=1)

    def test_extracts_canonical_names(self, extractor, tmp_path):
        chapter = tmp_path / "ch001.md"
        chapter.write_text("李青云走进林凡身旁, 二人对视.", encoding="utf-8")
        nodes = extractor.extract(chapter)
        names = {n.payload["name"] for n in nodes}
        assert names == {"李青云", "林凡"}
        assert len(nodes) == 2  # alias_map 命中 "凡" → "林凡", 0 重复

    def test_blacklist_filters_common_words(self, extractor, tmp_path):
        chapter = tmp_path / "ch001.md"
        chapter.write_text("那个 什么 怎么 这里 那里 如此 这般, 李青云走过.", encoding="utf-8")
        nodes = extractor.extract(chapter)
        names = {n.payload["name"] for n in nodes}
        assert "那个" not in names
        assert "什么" not in names
        assert names == {"李青云"}


class TestForeshadowExtractor:
    @pytest.fixture
    def rules(self):
        return {
            "keywords": ["伏笔", "暗示", "铺垫"],
            "pattern": "(?P<content>[\\u4e00-\\u9fff]{6,30}?(?:伏笔|暗示|铺垫))",
            "chapter_window": 5,
        }

    @pytest.fixture
    def extractor(self, rules):
        return ForeshadowExtractor(rules=rules, volume=1)

    def test_extracts_keyword_context(self, extractor, tmp_path):
        chapter = tmp_path / "ch001_大纲.md"
        chapter.write_text("# 章节一\n\n古剑碎片是本章伏笔, 林凡将继承此剑.\n", encoding="utf-8")
        nodes = extractor.extract(chapter)
        assert len(nodes) >= 1
        assert any("伏笔" in n.payload.get("content", "") for n in nodes)

    def test_empty_chapter_returns_empty_list(self, extractor, tmp_path):
        chapter = tmp_path / "ch001_大纲.md"
        chapter.write_text("# 章节一\n\n普通叙事无伏笔信号.\n", encoding="utf-8")
        nodes = extractor.extract(chapter)
        assert nodes == []


class TestSettingExtractor:
    @pytest.fixture
    def rules(self):
        return {
            "name_pattern": "[\\u4e00-\\u9fff]{2,6}(?:学院|山门|大陆|帝国|秘境|洞府|遗迹|海域|城|宗|派|观|谷)",
            "blacklist": ["这个", "那个"],
            "occurrence_threshold": 1,
        }

    @pytest.fixture
    def extractor(self, rules):
        return SettingExtractor(rules=rules, volume=1)

    def test_extracts_noun_suffixed_settings(self, extractor, tmp_path):
        chapter = tmp_path / "ch001.md"
        chapter.write_text("李青云拜入凌霄宗, 游历青云大陆, 探访古幽秘境.", encoding="utf-8")
        nodes = extractor.extract(chapter)
        names = {n.payload["name"] for n in nodes}
        assert "凌霄宗" in names
        assert "青云大陆" in names
        assert "古幽秘境" in names

    def test_blacklist_filters_pronouns(self, extractor, tmp_path):
        chapter = tmp_path / "ch001.md"
        chapter.write_text("这个 那个 此刻, 李青云走向凌霄宗.", encoding="utf-8")
        nodes = extractor.extract(chapter)
        names = {n.payload["name"] for n in nodes}
        assert names == {"凌霄宗"}


class TestPlotPointExtractor:
    @pytest.fixture
    def rules(self):
        return {
            "pattern": "^##\\s+(.+)$",
            "min_length": 8,
            "max_length": 50,
            "blacklist": ["^## 简介$", "^## 备注$"],
        }

    @pytest.fixture
    def extractor(self, rules):
        return PlotPointExtractor(rules=rules, volume=1)

    def test_extracts_markdown_h2_titles(self, extractor, tmp_path):
        chapter = tmp_path / "ch001_大纲.md"
        chapter.write_text(
            "# 章节一\n\n## 青云觉醒获得古剑碎片\n## 林凡登场\n## 简介\n",
            encoding="utf-8",
        )
        nodes = extractor.extract(chapter)
        titles = {n.payload["title"] for n in nodes}
        assert "青云觉醒获得古剑碎片" in titles
        assert "林凡登场" in titles
        assert "简介" not in titles  # blacklist

    def test_filters_short_titles(self, extractor, tmp_path):
        chapter = tmp_path / "ch001_大纲.md"
        chapter.write_text("## 太短\n## 简介\n## 备注\n", encoding="utf-8")
        nodes = extractor.extract(chapter)
        # min_length=8 过滤 "太短" (2 字) + blacklist 过滤
        assert nodes == []


# ============ Backfiller orchestration tests (3 tests) ============

class TestBackfiller:
    @pytest.fixture
    def rules_yaml(self, tmp_path):
        yaml_content = """
character:
  name_pattern: "[李青云林凡]{2,3}"
  alias_map: {"凡": "林凡"}
  blacklist: []
  occurrence_threshold: 1
foreshadow:
  keywords: ["伏笔", "暗示"]
  pattern: "(?P<content>[\\u4e00-\\u9fff]{6,30}?(?:伏笔|暗示))"
  chapter_window: 5
setting:
  name_pattern: "[\\u4e00-\\u9fff]{2,6}(?:学院|山门|大陆|帝国|秘境|宗)"
  blacklist: []
  occurrence_threshold: 1
plot_point:
  pattern: "^##\\s+(.+)$"
  min_length: 8
  max_length: 50
  blacklist: []
"""
        rules_path = tmp_path / "rules.yaml"
        rules_path.write_text(yaml_content, encoding="utf-8")
        return rules_path

    @pytest.fixture
    def corpus(self, tmp_path):
        corpus_root = tmp_path / "corpus"
        corpus_root.mkdir()
        # ch001: character + setting
        (corpus_root / "ch001.md").write_text("李青云拜入凌霄宗, 林凡登场.", encoding="utf-8")
        (corpus_root / "ch001_大纲.md").write_text(
            "# 章节一\n## 青云觉醒获得古剑碎片\n## 林凡登场\n", encoding="utf-8"
        )
        # ch002: character (跨章聚合 ch001)
        (corpus_root / "ch002.md").write_text("李青云与林凡激战.", encoding="utf-8")
        (corpus_root / "ch002_大纲.md").write_text(
            "# 章节二\n## 凌霄宗大战林凡\n", encoding="utf-8"
        )
        return corpus_root

    def test_backfill_dry_run_does_not_write(self, rules_yaml, corpus, tmp_path):
        """Phase 9.11: --dry-run 0 写库, 仅 print 统计."""
        storage = RippleStorage(db_path=tmp_path / "ripple.db")
        graph = CrossVolumeReferenceGraph(storage=storage)
        backfiller = Backfiller(rules_path=rules_yaml, corpus_root=corpus, graph=graph)
        stats = backfiller.run(dry_run=True)
        assert stats.dry_run is True
        assert stats.total_count >= 1
        # dry-run → 0 写库
        assert storage.load_all_nodes() == []

    def test_backfill_execute_writes_via_append_nodes_atomic(self, rules_yaml, corpus, tmp_path):
        """Phase 9.11: --execute 走 storage.append_nodes_atomic 1 commit."""
        storage = RippleStorage(db_path=tmp_path / "ripple.db")
        graph = CrossVolumeReferenceGraph(storage=storage)
        backfiller = Backfiller(rules_path=rules_yaml, corpus_root=corpus, graph=graph)
        stats = backfiller.run(dry_run=False)
        assert stats.dry_run is False
        assert stats.total_count >= 1
        # execute → 写库
        loaded = storage.load_all_nodes()
        assert len(loaded) == stats.total_count
        # 跨章聚合: 李青云 ch001 + ch002 → 1 node + chapter_appearances=[1, 2]
        liqy = [n for n in loaded if n.payload.get("name") == "李青云"]
        assert len(liqy) == 1
        assert set(liqy[0].payload["chapter_appearances"]) == {1, 2}

    def test_backfill_volume_filter_restricts_scan(self, rules_yaml, corpus, tmp_path):
        """Phase 9.11: --vol 1 抽样式, 仅扫 vol 1 章."""
        storage = RippleStorage(db_path=tmp_path / "ripple.db")
        graph = CrossVolumeReferenceGraph(storage=storage)
        backfiller = Backfiller(rules_path=rules_yaml, corpus_root=corpus, graph=graph)
        stats_all = backfiller.run(dry_run=True, volume_filter=None)
        stats_v1 = backfiller.run(dry_run=True, volume_filter=1)
        # vol filter 0 写库, dry-run 0 写库, 仅统计差异 (vol filter 应 ≤ all)
        assert stats_v1.total_count <= stats_all.total_count


# ============ Integration tests (atomic_batch + dry-run gating) ============

class TestBackfillIntegration:
    def test_backfill_execute_commits_atomically(self, rules_yaml, corpus, tmp_path):
        """Phase 9.11: --execute 走 append_nodes_atomic, 0 partial write."""
        storage = RippleStorage(db_path=tmp_path / "ripple.db")
        graph = CrossVolumeReferenceGraph(storage=storage)
        backfiller = Backfiller(rules_path=rules_yaml, corpus_root=corpus, graph=graph)
        stats = backfiller.run(dry_run=False)
        # 全部 nodes 写库, 0 0 残留
        loaded = storage.load_all_nodes()
        assert len(loaded) == stats.total_count
        assert all(n.created_by.startswith("backfill:") for n in loaded)

    def test_backfill_dry_run_creates_no_db(self, rules_yaml, corpus, tmp_path):
        """Phase 9.11: dry-run 跑后, ripple.db 0 创建 / 0 创建后 0 nodes."""
        non_existent_db = tmp_path / "ripple_dry.db"
        storage = RippleStorage(db_path=non_existent_db)
        graph = CrossVolumeReferenceGraph(storage=storage)
        backfiller = Backfiller(rules_path=rules_yaml, corpus_root=corpus, graph=graph)
        backfiller.run(dry_run=True)
        # dry-run → 0 写库 (但 __init__ 已创建空 DB, load 应 0 nodes)
        assert storage.load_all_nodes() == []


# ============ E2E test (10 章 fixture) ============

class TestBackfillE2E:
    def test_backfill_runs_on_10_chapter_fixture(self, tmp_path):
        """Phase 9.11 E2E: 走 10 章真实 fixture, 验证 4 维 N nodes 范围合理 0 crash."""
        # fixture dir 在 tests/cross_volume/fixtures/
        from tests.cross_volume.fixtures.sample_corpus import SAMPLE_CORPUS_ROOT
        rules_yaml = tmp_path / "rules.yaml"
        rules_yaml.write_text(SAMPLE_RULES_YAML, encoding="utf-8")
        storage = RippleStorage(db_path=tmp_path / "ripple.db")
        graph = CrossVolumeReferenceGraph(storage=storage)
        backfiller = Backfiller(
            rules_path=rules_yaml, corpus_root=SAMPLE_CORPUS_ROOT, graph=graph
        )
        stats = backfiller.run(dry_run=False)
        # 4 维 N nodes 范围合理 (跟 fixture 内容有关, 估 ≥ 5 total, 各 dim ≥ 1)
        assert stats.total_count >= 5
        assert stats.character_count >= 1
        assert stats.plot_point_count >= 1
