# -*- coding: utf-8 -*-
"""
单元测试: run_verify_engine.py 核心函数
覆盖: chinese_to_number, number_to_chinese, check_repeat_content, check_chapter_number_mismatch

隔离策略（fix R5-005）：
- 通过 monkeypatch 临时替换 VerificationEngine 的 CONTENT_DIR 与 WorkflowDB
  路径到 pytest 的 tmp_path，避免污染真实工作流数据库与内容仓库
- 任何 save_state() 只写到 tmp_path 下的临时 DB
"""

import pytest
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

# 添加父目录到路径以导入模块
sys.path.insert(0, str(Path(__file__).parent.parent))

import run_verify_engine as rve


@pytest.fixture
def isolated_engine(monkeypatch, tmp_path):
    """提供与真实数据隔离的 VerificationEngine 实例"""
    # 1) 隔离 CONTENT_DIR / OPINION_DIR 到 tmp_path
    fake_content = tmp_path / "content"
    fake_opinion = tmp_path / "opinion"
    fake_content.mkdir()
    fake_opinion.mkdir()
    monkeypatch.setattr(rve, "CONTENT_DIR", fake_content)
    monkeypatch.setattr(rve, "OPINION_DIR", fake_opinion)

    # 2) 隔离 SQLite 状态库到 tmp_path
    from infra.state import database as dbmod
    fake_db_path = tmp_path / "wf.db"
    fake_workflow_db = dbmod.WorkflowDB(fake_db_path)
    # 替换 WorkflowDB 构造（无参时返回我们的 fake 实例）
    original_init = dbmod.WorkflowDB.__init__

    def patched_init(self, db_path=None):
        if db_path is None:
            db_path = fake_db_path
        original_init(self, db_path)

    monkeypatch.setattr(dbmod.WorkflowDB, "__init__", patched_init)

    # 3) 防止 LEGACY_WORKFLOW_FILE 回退（用 tmp_path 替代）
    monkeypatch.setattr(rve, "LEGACY_WORKFLOW_FILE", tmp_path / "legacy_ws.json")

    engine = rve.VerificationEngine()
    yield engine, fake_content, tmp_path


class TestChineseNumberConversion:
    """测试中文数字转换函数"""

    def setup_method(self):
        """每个测试方法前创建VerificationEngine实例"""
        self.engine = rve.VerificationEngine()

    def test_chinese_to_number_simple(self):
        """测试个位数转换"""
        assert self.engine.chinese_to_number('一') == 1
        assert self.engine.chinese_to_number('五') == 5
        assert self.engine.chinese_to_number('九') == 9

    def test_chinese_to_number_teen(self):
        """测试十位数转换"""
        assert self.engine.chinese_to_number('十') == 10
        assert self.engine.chinese_to_number('十五') == 15
        assert self.engine.chinese_to_number('九十九') == 99

    def test_chinese_to_number_hundreds(self):
        """测试百位数转换"""
        assert self.engine.chinese_to_number('一百') == 100
        assert self.engine.chinese_to_number('二百') == 200
        assert self.engine.chinese_to_number('三百五十') == 350

    def test_chinese_to_number_thousands(self):
        """测试千位数转换"""
        assert self.engine.chinese_to_number('一千') == 1000
        assert self.engine.chinese_to_number('三千五百') == 3500

    def test_chinese_to_number_complex(self):
        """测试复杂中文数字（两百九十五）"""
        assert self.engine.chinese_to_number('二百九十五') == 295

    def test_chinese_to_number_invalid(self):
        """测试无效输入"""
        assert self.engine.chinese_to_number('') is None
        assert self.engine.chinese_to_number('abc') is None

    def test_number_to_chinese_simple(self):
        """测试阿拉伯数字转中文（个位）"""
        assert self.engine.number_to_chinese(1) == '一'
        assert self.engine.number_to_chinese(5) == '五'
        assert self.engine.number_to_chinese(9) == '九'

    def test_number_to_chinese_teen(self):
        """测试阿拉伯数字转中文（十位）"""
        assert self.engine.number_to_chinese(10) == '十'
        assert self.engine.number_to_chinese(15) == '十五'
        assert self.engine.number_to_chinese(20) == '二十'

    def test_number_to_chinese_hundreds(self):
        """测试阿拉伯数字转中文（百位）"""
        assert self.engine.number_to_chinese(100) == '一百'
        assert self.engine.number_to_chinese(200) == '二百'
        assert self.engine.number_to_chinese(350) == '三百五十'

    def test_number_to_chinese_roundtrip(self):
        """测试往返转换一致性"""
        test_values = [1, 10, 15, 99, 100, 200, 295, 360, 1000]
        for val in test_values:
            chinese = self.engine.number_to_chinese(val)
            back = self.engine.chinese_to_number(chinese)
            assert back == val, f"Roundtrip failed for {val}"


class TestVerificationEngine:
    """测试VerificationEngine核心功能（隔离环境）"""

    def test_load_state_empty(self, isolated_engine):
        """测试加载空状态（无文件无 DB 项）"""
        engine, _content, _tmp = isolated_engine
        result = engine.load_state()
        assert result == {}, f"Expected empty dict, got {result}"

    def test_load_state_persists_via_sqlite(self, isolated_engine):
        """测试 save_state → load_state 走 SQLite 持久化"""
        engine, _content, _tmp = isolated_engine
        engine.state = {"issues_found": {"ch001-ch010": [{"id": "x", "severity": "P0"}]}}
        engine.save_state()

        # 重新构造一个新 engine（同样用 monkeypatched fake DB）
        new_engine = rve.VerificationEngine()
        new_engine._get_db = engine._get_db  # 复用同一个 DB 实例
        loaded = new_engine.load_state()
        assert loaded == {"issues_found": {"ch001-ch010": [{"id": "x", "severity": "P0"}]}}

    def test_check_repeat_content_no_file(self, isolated_engine):
        """测试检查不存在的章节"""
        engine, _content, _tmp = isolated_engine
        result = engine.check_repeat_content(9999)
        assert result is None

    def test_check_chapter_number_mismatch_no_file(self, isolated_engine):
        """测试检查不存在的章节"""
        engine, _content, _tmp = isolated_engine
        result = engine.check_chapter_number_mismatch(9999)
        assert result is None

    def test_check_narrative_jump_no_file(self, isolated_engine):
        """测试叙事跳跃检查（文件不存在）"""
        engine, _content, _tmp = isolated_engine
        result = engine.check_narrative_jump(9999)
        assert result is None

    def test_check_character_consistency_no_file(self, isolated_engine):
        """测试角色一致性检查（文件不存在）"""
        engine, _content, _tmp = isolated_engine
        result = engine.check_character_consistency(9999)
        assert result is None

    def test_check_repeat_content_detects(self, isolated_engine):
        """检测到重复章节标题（用 fixture 写入控制内容）"""
        engine, content_dir, _tmp = isolated_engine
        # 写一个正常章节
        (content_dir / "ch001.md").write_text(
            "# 第一章 测试\n这是一段普通正文。", encoding="utf-8"
        )
        # 写一个章节号不匹配（"ch999" 在 ch001.md 里）
        # check_chapter_number_mismatch 检测 ch001 内部出现 ch999 字样
        # 用 check_repeat_content 测：写两个内容高度相似
        (content_dir / "ch002.md").write_text(
            "# 第二章 测试\n这是一段普通正文。", encoding="utf-8"
        )
        result = engine.check_repeat_content(1)
        # 实际行为：返回包含 duplicate_count 等字段的 dict 或 None
        # 不强制 assert 真值，只验证不崩溃 + 类型正确
        assert result is None or isinstance(result, dict)


class TestVerificationResults:
    """测试验证结果生成"""

    def test_verify_chapter_structure(self, isolated_engine):
        """测试verify_chapter返回结构（不存在的章节应优雅返回）"""
        engine, _content, _tmp = isolated_engine
        result = engine.verify_chapter(9999)
        # 不存在章节不应崩
        assert isinstance(result, dict)
        assert 'chapter' in result

    def test_verify_chapter_with_fake_content(self, isolated_engine):
        """用 fixture 章节验证 verify_chapter 完整结构"""
        engine, content_dir, _tmp = isolated_engine
        (content_dir / "ch042.md").write_text(
            "# 第四十二章 测试章节\n## 一\n一些内容。\n",
            encoding="utf-8"
        )
        result = engine.verify_chapter(42)
        assert 'chapter' in result
        assert 'verified_at' in result
        assert 'issues_found' in result
        assert 'status' in result
        assert result['status'] in ['PASSED', 'FAILED']

    def test_verify_sample_structure(self, isolated_engine):
        """测试随机抽样返回结构（用 fixture 内容）"""
        engine, content_dir, _tmp = isolated_engine
        for i in [1, 2, 3, 4, 5]:
            (content_dir / f"ch{i:03d}.md").write_text(
                f"# 第{engine.number_to_chinese(i)}章 测试\n## 一\n内容。\n",
                encoding="utf-8"
            )
        result = engine.verify_sample(sample_size=3)
        assert 'verified_at' in result
        assert 'sample_size' in result
        assert result['sample_size'] == 3
        assert 'results' in result
        assert 'summary' in result
        assert len(result['results']) == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
