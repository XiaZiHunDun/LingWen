#!/usr/bin/env python3
"""
质量检查器测试
"""
import pytest
from pathlib import Path
import tempfile
import os

# 添加父目录到 path 以便导入
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "consistency"))

from check_naming import check_naming, extract_chapter_num, chinese_to_arabic
from check_content_integrity import check_integrity


class TestChineseToArabic:
    """中文数字转换测试"""

    def test_simple_digits(self):
        """测试简单中文数字"""
        assert chinese_to_arabic('一') == 1
        assert chinese_to_arabic('二') == 2
        assert chinese_to_arabic('三') == 3
        assert chinese_to_arabic('十') == 10

    def test_compound_digits(self):
        """测试复合中文数字"""
        assert chinese_to_arabic('十一') == 11
        assert chinese_to_arabic('二十') == 20
        assert chinese_to_arabic('三十五') == 35


class TestExtractChapterNum:
    """章节号提取测试"""

    def test_extract_chinese_chapter(self):
        """测试提取中文章节号"""
        assert extract_chapter_num('# 第十二章 测试') == 12
        assert extract_chapter_num('# 第三十五章 测试') == 35

    def test_extract_arabic_returns_none(self):
        """测试阿拉伯数字章节号返回None（当前实现仅支持中文）"""
        # 当前实现仅支持中文数字，阿拉伯数字返回None
        assert extract_chapter_num('# 第1章 测试') is None
        assert extract_chapter_num('# 第12章 测试') is None


class TestNamingChecker:
    """命名检查器测试"""

    def test_check_naming_with_valid_file(self, tmp_path):
        """测试检查正常命名的章节"""
        # 创建临时章节文件
        chapter_file = tmp_path / "ch001.md"
        chapter_file.write_text("# 第1章 测试标题\n\n内容\n\n**本章完**", encoding='utf-8')

        issues = check_naming(str(tmp_path), (1, 1))

        # 应该没有严重问题
        assert len(issues) == 0 or all(issue[0] != "MISMATCH" for issue in issues)

    def test_check_naming_mismatch(self, tmp_path):
        """测试检查文件名与内容不匹配"""
        # 创建文件名为 ch001 但内容是第2章
        # 注意：需要使用中文数字，检查器不支持阿拉伯数字
        chapter_file = tmp_path / "ch001.md"
        chapter_file.write_text("# 第十二章 错误标题\n\n内容\n\n**本章完**", encoding='utf-8')

        issues = check_naming(str(tmp_path), (1, 1))

        # 应该发现问题 - 文件名ch001但内容是第12章
        assert len(issues) > 0
        assert any(issue[0] == "MISMATCH" for issue in issues)


class TestContentIntegrityChecker:
    """内容完整性检查器测试"""

    def test_finds_missing_end_marker(self, tmp_path):
        """测试检测缺少本章完标记"""
        chapter_file = tmp_path / "ch002.md"
        # 需要足够多的内容（>100字符）才能通过 EMPTY_CHAPTER 检查
        # 然后才检测到 MISSING_END_MARK 问题
        content = "# 第2章 无标记\n\n" + "这是测试内容。" * 50  # 约300字符
        chapter_file.write_text(content, encoding='utf-8')

        issues = check_integrity(str(tmp_path), (2, 2))

        # 应该发现问题 - 缺少本章完标记
        assert len(issues) > 0
        assert any("本章完" in issue[3] for issue in issues)

    def test_detects_short_content(self, tmp_path):
        """测试检测字数不足"""
        chapter_file = tmp_path / "ch003.md"
        chapter_file.write_text("# 第3章\n\n短", encoding='utf-8')

        issues = check_integrity(str(tmp_path), (3, 3))

        # 应该发现问题（字数不足或内容过少）
        assert len(issues) > 0
        assert any("字数" in issue[3] or "内容过少" in issue[3] for issue in issues)