# -*- coding: utf-8 -*-
"""
单元测试: run_verify_engine.py 核心函数
覆盖: chinese_to_number, number_to_chinese, check_repeat_content, check_chapter_number_mismatch
"""

import pytest
import sys
import json
import tempfile
import os
from pathlib import Path

# 添加父目录到路径以导入模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from run_verify_engine import VerificationEngine


class TestChineseNumberConversion:
    """测试中文数字转换函数"""

    def setup_method(self):
        """每个测试方法前创建VerificationEngine实例"""
        self.engine = VerificationEngine()

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
    """测试VerificationEngine核心功能"""

    def setup_method(self):
        """创建临时测试目录结构"""
        self.test_dir = tempfile.mkdtemp()
        self.original_content_dir = Path(__file__).parent.parent / "03_内容仓库" / "04_正文"
        self.original_workflow_file = Path(__file__).parent.parent / "workflow_state.json"

    def teardown_method(self):
        """清理临时目录"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_load_state_nonexistent_file(self):
        """测试加载不存在的状态文件"""
        # 临时修改路径
        engine = VerificationEngine()
        # 如果文件不存在应该返回空字典
        result = engine.load_state()
        assert isinstance(result, dict)

    def test_check_repeat_content_no_file(self):
        """测试检查不存在的章节"""
        engine = VerificationEngine()
        result = engine.check_repeat_content(9999)
        assert result is None

    def test_check_chapter_number_mismatch_no_file(self):
        """测试检查不存在的章节"""
        engine = VerificationEngine()
        result = engine.check_chapter_number_mismatch(9999)
        assert result is None

    def test_check_narrative_jump_no_file(self):
        """测试叙事跳跃检查（文件不存在）"""
        engine = VerificationEngine()
        result = engine.check_narrative_jump(9999)
        assert result is None

    def test_check_character_consistency_no_file(self):
        """测试角色一致性检查（文件不存在）"""
        engine = VerificationEngine()
        result = engine.check_character_consistency(9999)
        assert result is None


class TestVerificationResults:
    """测试验证结果生成"""

    def setup_method(self):
        """每个测试前创建引擎"""
        self.engine = VerificationEngine()

    def test_verify_chapter_structure(self):
        """测试verify_chapter返回结构"""
        result = self.engine.verify_chapter(1)
        assert 'chapter' in result
        assert 'verified_at' in result
        assert 'issues_found' in result
        assert 'status' in result
        assert result['status'] in ['PASSED', 'FAILED']

    def test_verify_chapter_format(self):
        """测试verify_chapter章节格式"""
        result = self.engine.verify_chapter(42)
        assert result['chapter'] == 'ch042'

    def test_verify_sample_structure(self):
        """测试随机抽样返回结构"""
        result = self.engine.verify_sample(sample_size=5)
        assert 'verified_at' in result
        assert 'sample_size' in result
        assert result['sample_size'] == 5
        assert 'results' in result
        assert 'summary' in result
        assert len(result['results']) == 5


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
