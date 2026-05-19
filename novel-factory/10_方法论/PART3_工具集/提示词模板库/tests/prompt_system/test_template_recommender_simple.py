#!/usr/bin/env python3
"""
模板推荐引擎测试 (简化版)

Tests for TemplateRecommender
"""

import pytest
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from prompt_assembler import PromptAssembler, TemplateCategory
from template_recommender import TemplateRecommender, TemplateScore, RecommendationCriteria


class TestTemplateRecommenderBasic:
    """基础功能测试 - 使用最小化的fixture"""

    @pytest.fixture
    def simple_recommender(self, tmp_path):
        """创建最小化配置"""
        # 创建目录结构
        config_dir = tmp_path / "config" / "prompts"
        config_dir.mkdir(parents=True)

        # 创建索引文件 (在根目录)
        index_content = """
templates:
  - id: outline_v1
    name: 全文大纲
    category: outline
    version: v1.0.0
    status: active
    file: 01_大纲生成/全文大纲.md
    description: 生成大纲
    temperature:
      recommended: 0.6
      range: [0.5, 0.7]
    care_elements:
      result_metrics: [S1, S2]
    use_count: 5
    success_rate: 0.8
    avg_score: 8.5

  - id: continuation_v1
    name: 标准续写
    category: continuation
    version: v1.0.0
    status: active
    file: 02_正文续写/标准续写.md
    description: 续写正文
    temperature:
      recommended: 0.7
      range: [0.6, 0.8]
    care_elements:
      result_metrics: [S1, S3]
    use_count: 10
    success_rate: 0.9
    avg_score: 9.0
"""
        (tmp_path / "00_模板索引.yaml").write_text(index_content, encoding='utf-8')

        # 创建温度映射
        temp_content = """
scene_types:
  outline_generation:
    temperature:
      recommended: 0.6
      range: [0.5, 0.7]
  content_continuation:
    temperature:
      recommended: 0.7
      range: [0.6, 0.8]
"""
        (config_dir / "场景温度映射.yaml").write_text(temp_content, encoding='utf-8')

        # 创建模板文件
        outline_dir = tmp_path / "01_大纲生成"
        outline_dir.mkdir(parents=True)
        (outline_dir / "全文大纲.md").write_text("# 全文大纲", encoding='utf-8')

        continuation_dir = tmp_path / "02_正文续写"
        continuation_dir.mkdir(parents=True)
        (continuation_dir / "标准续写.md").write_text("# 标准续写", encoding='utf-8')

        # 创建 assembler 和 recommender
        assembler = PromptAssembler(str(config_dir))
        recommender = TemplateRecommender(
            assembler,
            index_file=str(tmp_path / "00_模板索引.yaml")
        )

        return recommender

    def test_recommender_loads_stats(self, simple_recommender):
        """测试加载模板统计"""
        assert len(simple_recommender.template_stats) >= 2

    def test_recommend_outline_scene(self, simple_recommender):
        """测试大纲场景推荐"""
        results = simple_recommender.recommend(scene_type="outline_generation")
        assert len(results) > 0
        assert results[0].template.category == TemplateCategory.OUTLINE

    def test_recommend_continuation_scene(self, simple_recommender):
        """测试续写场景推荐"""
        results = simple_recommender.recommend(scene_type="content_continuation")
        assert len(results) > 0

    def test_recommend_single(self, simple_recommender):
        """测试单个推荐"""
        result = simple_recommender.recommend_single(scene_type="outline_generation")
        assert result is not None
        assert isinstance(result, TemplateScore)

    def test_history_bonus(self, simple_recommender):
        """测试历史评分"""
        bonus = simple_recommender._calculate_history_bonus("outline_v1")
        assert bonus > 0

    def test_explain_recommendation(self, simple_recommender):
        """测试推荐说明生成"""
        result = simple_recommender.recommend_single(scene_type="outline_generation")
        explanation = simple_recommender.explain_recommendation(result)
        assert "全文大纲" in explanation
        assert "v1.0.0" in explanation


class TestVersionManagerBasic:
    """版本管理器基础测试"""

    @pytest.fixture
    def simple_version_manager(self, tmp_path):
        """创建最小化版本管理器"""
        # 创建版本管理器
        config_dir = tmp_path / "config" / "prompts"
        config_dir.mkdir(parents=True)

        from version_manager import VersionManager
        return VersionManager(str(config_dir))

    def test_version_manager_init(self, simple_version_manager):
        """测试版本管理器初始化"""
        assert simple_version_manager is not None
        assert simple_version_manager.versions_dir.exists()

    def test_get_empty_history(self, simple_version_manager):
        """测试获取空历史"""
        history = simple_version_manager.get_history("nonexistent")
        assert history == []

    def test_get_latest_version_empty(self, simple_version_manager):
        """测试获取不存在的版本"""
        latest = simple_version_manager.get_latest_version("nonexistent")
        assert latest is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])