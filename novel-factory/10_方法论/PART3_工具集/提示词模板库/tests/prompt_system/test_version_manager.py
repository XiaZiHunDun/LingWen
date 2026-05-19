#!/usr/bin/env python3
"""
版本管理器测试

Tests for VersionManager
"""

import pytest
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from version_manager import VersionManager, TemplateVersion, VersionDiff


# ==================== Fixtures ====================

@pytest.fixture
def temp_config_dir(tmp_path):
    """创建临时配置目录结构：
    tmp_path/prompt_config/config/prompts/
        01_大纲生成/
            全文大纲_CARE.md
        00_模板索引.yaml
    """
    prompts_dir = tmp_path / "prompt_config" / "config" / "prompts"
    prompts_dir.mkdir(parents=True)

    # 创建模板分类目录
    (prompts_dir / "01_大纲生成").mkdir(parents=True)
    (prompts_dir / "02_正文续写").mkdir(parents=True)

    # 创建测试模板文件
    template_file = prompts_dir / "01_大纲生成" / "全文大纲_CARE.md"
    template_file.write_text("# 全文大纲 v1.0\n模板内容", encoding='utf-8')

    # 创建模板索引
    index_content = """
templates:
  - id: outline_full_novel_v1
    name: 全文大纲
    category: outline
    version: v1.0.0
    status: active
    file: 01_大纲生成/全文大纲_CARE.md
    description: 生成整本小说的完整大纲
    temperature:
      recommended: 0.6
      range: [0.5, 0.7]
    care_elements:
      result_metrics: [S1, S2, S6, S7]
"""
    (prompts_dir / "00_模板索引.yaml").write_text(index_content, encoding='utf-8')

    return prompts_dir


@pytest.fixture
def version_manager(temp_config_dir):
    """创建VersionManager实例 - 传入prompts目录"""
    return VersionManager(str(temp_config_dir))


# ==================== 测试版本管理器初始化 ====================

class TestVersionManagerInit:
    def test_creates_versions_directory(self, version_manager, temp_config_dir):
        """测试创建版本目录"""
        assert version_manager.versions_dir.exists()
        assert version_manager.versions_dir.is_dir()

    def test_history_file_created_after_first_version(self, version_manager, temp_config_dir):
        """测试历史文件在创建第一个版本后创建"""
        template_file = temp_config_dir / "01_大纲生成" / "全文大纲_CARE.md"

        # Create first version - this triggers _save_history which creates the history file
        version_manager.create_version(
            template_id="outline_full_novel",
            changelog="初始版本",
            template_dir=template_file
        )

        assert version_manager.history_file.exists()


# ==================== 测试版本创建 ====================

class TestVersionCreation:
    def test_create_first_version(self, version_manager, temp_config_dir):
        """测试创建第一个版本"""
        template_file = temp_config_dir / "01_大纲生成" / "全文大纲_CARE.md"

        version = version_manager.create_version(
            template_id="outline_full_novel",
            changelog="初始版本",
            template_dir=template_file
        )

        assert version is not None
        assert isinstance(version, TemplateVersion)
        assert version.version == "v1.0.0"
        assert version.template_id == "outline_full_novel"
        assert version.changelog == "初始版本"
        assert version.status == "active"

    def test_create_multiple_versions(self, version_manager, temp_config_dir):
        """测试创建多个版本"""
        template_file = temp_config_dir / "01_大纲生成" / "全文大纲_CARE.md"

        # 创建第一个版本
        v1 = version_manager.create_version(
            template_id="outline_full_novel",
            changelog="初始版本",
            template_dir=template_file
        )
        assert v1.version == "v1.0.0"

        # 修改文件
        template_file.write_text("# 全文大纲 v1.1\n新模板内容", encoding='utf-8')

        # 创建第二个版本
        v2 = version_manager.create_version(
            template_id="outline_full_novel",
            changelog="添加新功能",
            template_dir=template_file
        )
        assert v2.version == "v1.0.1"

    def test_backup_file_created(self, version_manager, temp_config_dir):
        """测试备份文件创建"""
        template_file = temp_config_dir / "01_大纲生成" / "全文大纲_CARE.md"

        version_manager.create_version(
            template_id="outline_full_novel",
            changelog="初始版本",
            template_dir=template_file
        )

        backup_dir = version_manager.versions_dir / "outline_full_novel"
        assert backup_dir.exists()

        backups = list(backup_dir.glob("v*.md"))
        assert len(backups) >= 1


# ==================== 测试版本历史 ====================

class TestVersionHistory:
    def test_get_history_empty(self, version_manager):
        """测试获取空历史"""
        history = version_manager.get_history("nonexistent_template")
        assert history == []

    def test_get_history_after_creation(self, version_manager, temp_config_dir):
        """测试创建后的历史记录"""
        template_file = temp_config_dir / "01_大纲生成" / "全文大纲_CARE.md"

        version_manager.create_version(
            template_id="outline_full_novel",
            changelog="初始版本",
            template_dir=template_file
        )

        history = version_manager.get_history("outline_full_novel")

        assert len(history) == 1
        assert history[0].version == "v1.0.0"

    def test_get_history_sorted_by_date(self, version_manager, temp_config_dir):
        """测试历史按日期排序"""
        import time
        template_file = temp_config_dir / "01_大纲生成" / "全文大纲_CARE.md"

        # 创建多个版本，每个间隔确保不同的时间戳
        for i in range(3):
            template_file.write_text(f"# 版本 {i+1}\n内容", encoding='utf-8')
            version_manager.create_version(
                template_id="outline_full_novel",
                changelog=f"版本 {i+1}",
                template_dir=template_file
            )
            time.sleep(0.1)  # 确保不同的时间戳

        history = version_manager.get_history("outline_full_novel")

        # 最新版本在前（按 created_at 倒序）
        assert history[0].version == "v1.0.2"
        assert history[1].version == "v1.0.1"
        assert history[2].version == "v1.0.0"

    def test_get_history_with_limit(self, version_manager, temp_config_dir):
        """测试历史记录限制"""
        template_file = temp_config_dir / "01_大纲生成" / "全文大纲_CARE.md"

        # 创建多个版本
        for i in range(5):
            template_file.write_text(f"# 版本 {i+1}\n内容", encoding='utf-8')
            version_manager.create_version(
                template_id="outline_full_novel",
                changelog=f"版本 {i+1}",
                template_dir=template_file
            )

        history = version_manager.get_history("outline_full_novel", limit=3)

        assert len(history) == 3

    def test_get_latest_version(self, version_manager, temp_config_dir):
        """测试获取最新版本"""
        template_file = temp_config_dir / "01_大纲生成" / "全文大纲_CARE.md"

        # 创建多个版本
        for i in range(3):
            template_file.write_text(f"# 版本 {i+1}\n内容", encoding='utf-8')
            version_manager.create_version(
                template_id="outline_full_novel",
                changelog=f"版本 {i+1}",
                template_dir=template_file
            )

        latest = version_manager.get_latest_version("outline_full_novel")

        assert latest is not None
        assert latest.version == "v1.0.2"


# ==================== 测试版本比较 ====================

class TestVersionComparison:
    def test_compare_versions(self, version_manager, temp_config_dir):
        """测试版本比较"""
        template_file = temp_config_dir / "01_大纲生成" / "全文大纲_CARE.md"

        # 创建两个版本
        template_file.write_text("# v1.0\n内容1", encoding='utf-8')
        version_manager.create_version(
            template_id="outline_full_novel",
            changelog="版本1",
            template_dir=template_file
        )

        template_file.write_text("# v1.1\n内容2", encoding='utf-8')
        version_manager.create_version(
            template_id="outline_full_novel",
            changelog="版本2",
            template_dir=template_file
        )

        diff = version_manager.compare_versions(
            "outline_full_novel",
            "v1.0.0",
            "v1.0.1"
        )

        assert isinstance(diff, VersionDiff)
        assert diff.version_from == "v1.0.0"
        assert diff.version_to == "v1.0.1"
        assert "content" in diff.changed_fields


# ==================== 测试版本回滚 ====================

class TestVersionRollback:
    def test_rollback(self, version_manager, temp_config_dir):
        """测试版本回滚"""
        template_file = temp_config_dir / "01_大纲生成" / "全文大纲_CARE.md"

        # 创建两个版本
        template_file.write_text("# v1.0\n原始内容", encoding='utf-8')
        version_manager.create_version(
            template_id="outline_full_novel",
            changelog="原始版本",
            template_dir=template_file
        )

        template_file.write_text("# v1.1\n修改内容", encoding='utf-8')
        version_manager.create_version(
            template_id="outline_full_novel",
            changelog="修改版本",
            template_dir=template_file
        )

        # 回滚到v1.0
        success = version_manager.rollback("outline_full_novel", "v1.0.0")

        assert success is True
        content = template_file.read_text(encoding='utf-8')
        assert "原始内容" in content

    def test_rollback_nonexistent_version(self, version_manager):
        """测试回滚不存在的版本"""
        success = version_manager.rollback("outline_full_novel", "v99.99.99")
        assert success is False


# ==================== 测试版本导出 ====================

class TestVersionExport:
    def test_export_version(self, version_manager, temp_config_dir):
        """测试导出版本"""
        template_file = temp_config_dir / "01_大纲生成" / "全文大纲_CARE.md"

        version_manager.create_version(
            template_id="outline_full_novel",
            changelog="初始版本",
            template_dir=template_file
        )

        export_dir = temp_config_dir / "export"
        export_dir.mkdir()

        output = version_manager.export_version(
            "outline_full_novel",
            "v1.0.0",
            export_dir
        )

        assert output is not None
        assert output.exists()


# ==================== 测试所有模板历史 ====================

class TestAllTemplatesHistory:
    def test_get_all_templates_with_history(self, version_manager, temp_config_dir):
        """测试获取所有模板历史"""
        template_file = temp_config_dir / "01_大纲生成" / "全文大纲_CARE.md"

        version_manager.create_version(
            template_id="outline_full_novel",
            changelog="初始版本",
            template_dir=template_file
        )

        all_histories = version_manager.get_all_templates_with_history()

        assert "outline_full_novel" in all_histories
        assert len(all_histories["outline_full_novel"]) == 1


# ==================== 测试清理旧版本 ====================

class TestCleanupOldVersions:
    def test_cleanup_keeps_recent_versions(self, version_manager, temp_config_dir):
        """测试清理保留最近版本"""
        template_file = temp_config_dir / "01_大纲生成" / "全文大纲_CARE.md"

        # 创建5个版本
        for i in range(5):
            template_file.write_text(f"# 版本 {i+1}\n内容", encoding='utf-8')
            version_manager.create_version(
                template_id="outline_full_novel",
                changelog=f"版本 {i+1}",
                template_dir=template_file
            )

        deleted = version_manager.cleanup_old_versions("outline_full_novel", keep_count=3)

        assert deleted == 2

        history = version_manager.get_history("outline_full_novel")
        assert len(history) == 3

    def test_cleanup_no_action_when_enough_versions(self, version_manager, temp_config_dir):
        """测试版本足够时不删除"""
        template_file = temp_config_dir / "01_大纲生成" / "全文大纲_CARE.md"

        # 创建2个版本
        for i in range(2):
            template_file.write_text(f"# 版本 {i+1}\n内容", encoding='utf-8')
            version_manager.create_version(
                template_id="outline_full_novel",
                changelog=f"版本 {i+1}",
                template_dir=template_file
            )

        deleted = version_manager.cleanup_old_versions("outline_full_novel", keep_count=5)

        assert deleted == 0
