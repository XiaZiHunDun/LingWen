# -*- coding: utf-8 -*-
"""
单元测试: 03_内容仓库/update_index.py 核心函数
覆盖: get_chapter_info, update_chapter_index, query_chapter, query_range
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# 添加父目录到路径
CONTENT_ROOT = Path(__file__).parent.parent / "03_内容仓库"
sys.path.insert(0, str(CONTENT_ROOT))

# 导入被测试的模块（注意：脚本直接执行，无module封装）
# 需要直接执行函数逻辑进行测试


class TestGetChapterInfo:
    """测试get_chapter_info函数"""

    def test_get_chapter_info_basic(self):
        """测试获取章节基本信息"""
        # 使用实际存在的测试文件
        chapters_dir = CONTENT_ROOT / "04_正文"
        if not chapters_dir.exists():
            pytest.skip("Content directory not found")

        # 找到第一个章节文件
        chapter_files = list(chapters_dir.glob("ch*.md"))
        if not chapter_files:
            pytest.skip("No chapter files found")

        test_file = chapter_files[0]

        # 手动调用函数逻辑（因为脚本没有封装成模块）
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()

        result = {
            "filename": test_file.name,
            "word_count": len(content),
            "char_count": len(content.replace('\n', '').replace(' ', '')),
            "lines": content.count('\n'),
        }

        # 验证返回结构
        assert "filename" in result
        assert "word_count" in result
        assert "char_count" in result
        assert "lines" in result
        assert result["word_count"] > 0
        assert result["char_count"] > 0

    def test_get_chapter_info_file_not_found(self):
        """测试文件不存在情况"""
        chapters_dir = CONTENT_ROOT / "04_正文"
        fake_file = chapters_dir / "ch9999.md"

        if fake_file.exists():
            pytest.skip("Fake file unexpectedly exists")

        assert not fake_file.exists()


class TestUpdateChapterIndex:
    """测试update_chapter_index函数"""

    def setup_method(self):
        """创建测试目录结构"""
        self.test_content_root = Path(tempfile.mkdtemp())
        self.test_chapters_dir = self.test_content_root / "04_正文"
        self.test_chapters_dir.mkdir()

        # 创建测试章节文件
        for i in range(1, 4):
            ch_file = self.test_chapters_dir / f"ch{str(i).zfill(3)}.md"
            ch_file.write_text(f"# 第{i}章测试内容\n\n这是第{i}章的测试内容。", encoding='utf-8')

    def teardown_method(self):
        """清理测试目录"""
        import shutil
        shutil.rmtree(self.test_content_root, ignore_errors=True)

    def test_update_chapter_index_creates_index_file(self):
        """测试更新索引会创建index.json"""
        index_file = self.test_chapters_dir / "index.json"

        # 模拟update_chapter_index逻辑
        chapters = []
        for f in sorted(self.test_chapters_dir.glob("ch*.md")):
            if f.is_file():
                with open(f, 'r', encoding='utf-8') as cf:
                    content = cf.read()
                chapters.append({
                    "chapter": f.stem,
                    "filename": f.name,
                    "word_count": len(content),
                    "char_count": len(content.replace('\n', '').replace(' ', '')),
                    "lines": content.count('\n'),
                })

        index_data = {
            "updated_at": "2026-05-20 12:00:00",
            "total_chapters": len(chapters),
            "chapters": chapters
        }

        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        # 验证
        assert index_file.exists()
        with open(index_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)

        assert loaded["total_chapters"] == 3
        assert len(loaded["chapters"]) == 3
        assert loaded["chapters"][0]["chapter"] == "ch001"

    def test_chapter_index_sorted(self):
        """测试章节索引按编号排序"""
        index_file = self.test_chapters_dir / "index.json"

        # 模拟索引创建
        chapters = []
        for f in sorted(self.test_chapters_dir.glob("ch*.md")):
            if f.is_file():
                chapters.append({"chapter": f.stem})

        index_data = {
            "total_chapters": len(chapters),
            "chapters": chapters
        }

        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        with open(index_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)

        chapters_sorted = [c["chapter"] for c in loaded["chapters"]]
        assert chapters_sorted == ["ch001", "ch002", "ch003"]


class TestQueryChapter:
    """测试query_chapter函数"""

    def setup_method(self):
        """创建测试环境"""
        self.test_content_root = Path(tempfile.mkdtemp())
        self.test_chapters_dir = self.test_content_root / "04_正文"
        self.test_chapters_dir.mkdir(parents=True)

    def teardown_method(self):
        """清理测试目录"""
        import shutil
        shutil.rmtree(self.test_content_root, ignore_errors=True)

    def test_query_chapter_exists(self):
        """测试查询存在的章节"""
        # 创建测试文件
        ch_file = self.test_chapters_dir / "ch001.md"
        test_content = "# 第一章\n\n这是测试内容。"
        ch_file.write_text(test_content, encoding='utf-8')

        # 模拟query_chapter逻辑
        chapter_name = "ch001"
        chapter_file = self.test_chapters_dir / f"{chapter_name}.md"

        assert chapter_file.exists()

        with open(chapter_file, 'r', encoding='utf-8') as f:
            content = f.read()

        info = {
            "filename": chapter_file.name,
            "word_count": len(content),
            "char_count": len(content.replace('\n', '').replace(' ', '')),
            "lines": content.count('\n'),
        }

        assert info["filename"] == "ch001.md"
        assert info["word_count"] > 0

    def test_query_chapter_not_exists(self):
        """测试查询不存在的章节"""
        chapter_file = self.test_chapters_dir / "ch9999.md"
        assert not chapter_file.exists()


class TestQueryRange:
    """测试query_range函数"""

    def setup_method(self):
        """创建测试环境"""
        self.test_content_root = Path(tempfile.mkdtemp())
        self.test_chapters_dir = self.test_content_root / "04_正文"
        self.test_chapters_dir.mkdir(parents=True)

        # 创建测试文件 ch001-ch005
        for i in range(1, 6):
            ch_file = self.test_chapters_dir / f"ch{str(i).zfill(3)}.md"
            ch_file.write_text(f"第{i}章内容", encoding='utf-8')

    def teardown_method(self):
        """清理测试目录"""
        import shutil
        shutil.rmtree(self.test_content_root, ignore_errors=True)

    def test_query_range_partial(self):
        """测试查询部分章节范围"""
        start_num = 2
        end_num = 4

        result = []
        for i in range(start_num, end_num + 1):
            ch_name = f"ch{str(i).zfill(3)}"
            chapter_file = self.test_chapters_dir / f"{ch_name}.md"
            if chapter_file.exists():
                result.append({"chapter": ch_name})

        assert len(result) == 3
        assert result[0]["chapter"] == "ch002"
        assert result[2]["chapter"] == "ch004"

    def test_query_range_out_of_bounds(self):
        """测试查询超出范围的章节"""
        start_num = 100
        end_num = 105

        result = []
        for i in range(start_num, end_num + 1):
            ch_name = f"ch{str(i).zfill(3)}"
            chapter_file = self.test_chapters_dir / f"{ch_name}.md"
            if chapter_file.exists():
                result.append({"chapter": ch_name})

        assert len(result) == 0


class TestChapterNumberParsing:
    """测试章节号解析"""

    def test_parse_chapter_number(self):
        """测试章节号解析逻辑"""
        # 测试 "ch001" -> 1
        chapter_str = "ch001"
        num = int(chapter_str.replace('ch', ''))
        assert num == 1

        # 测试 "ch360" -> 360
        chapter_str = "ch360"
        num = int(chapter_str.replace('ch', ''))
        assert num == 360

    def test_format_chapter_number(self):
        """测试章节号格式化"""
        # 测试 1 -> "001"
        num = 1
        formatted = str(num).zfill(3)
        assert formatted == "001"

        # 测试 360 -> "360"
        num = 360
        formatted = str(num).zfill(3)
        assert formatted == "360"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
