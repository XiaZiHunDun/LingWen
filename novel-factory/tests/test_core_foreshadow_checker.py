#!/usr/bin/env python3
"""Tests for CoreForeshadowChecker"""
from pathlib import Path

import pytest


def test_core_foreshadow_checker_init():
    """Test checker initialization"""
    from infra.consistency.checkers.core_foreshadow_checker import CoreForeshadowChecker
    checker = CoreForeshadowChecker()
    assert checker.chapters_dir.exists()

def test_foreshadow_issue_dataclass():
    """Test ForeshadowIssue dataclass"""
    from infra.consistency.checkers.core_foreshadow_checker import ForeshadowIssue
    issue = ForeshadowIssue(
        chapter='ch001',
        foreshadow_text='万剑宗',
        level='core',
        severity='HIGH',
        description='Test issue'
    )
    assert issue.chapter == 'ch001'
    assert issue.level == 'core'


# -----------------------------------------------------------------------------
# R2-009: _get_chapter_content 缓存 — 防止 N 个伏笔 × M 章节 = N×M 次磁盘读
# -----------------------------------------------------------------------------

class TestChapterContentCache:
    """R2-009: 章节内容缓存,避免 _is_recycled 在 expect_range 循环内重复 read_text"""

    def _make_checker(self, tmp_path):
        """创建一个指向 tmp_path/chapters 的 checker"""
        from infra.consistency.checkers.core_foreshadow_checker import CoreForeshadowChecker
        chapters_dir = tmp_path / "chapters"
        chapters_dir.mkdir()
        return CoreForeshadowChecker(chapters_dir=str(chapters_dir))

    def test_cache_initially_empty(self, tmp_path):
        """新 checker 缓存应为空 dict"""
        from infra.consistency.checkers.core_foreshadow_checker import CoreForeshadowChecker
        checker = CoreForeshadowChecker(chapters_dir=str(tmp_path))
        assert checker._chapter_content_cache == {}

    def test_get_chapter_content_caches_existing_file(self, tmp_path):
        """文件存在 → 第二次调用命中缓存 (通过修改文件可验证)"""
        ch_file = tmp_path / "ch001.md"
        ch_file.write_text("初始内容 万剑宗", encoding="utf-8")
        from infra.consistency.checkers.core_foreshadow_checker import CoreForeshadowChecker
        checker = CoreForeshadowChecker(chapters_dir=str(tmp_path))

        # 第一次:写入缓存
        c1 = checker._get_chapter_content(1)
        assert c1 == "初始内容 万剑宗"
        # 第二次:即使外部改了文件,缓存也命中(防止外部 race)
        ch_file.write_text("被改写", encoding="utf-8")
        c2 = checker._get_chapter_content(1)
        assert c2 == "初始内容 万剑宗", "缓存应优先,不应再读磁盘"
        assert checker._chapter_content_cache[1] == "初始内容 万剑宗"

    def test_get_chapter_content_caches_missing_as_none(self, tmp_path):
        """文件不存在 → 缓存 None,不会反复 stat"""
        from infra.consistency.checkers.core_foreshadow_checker import CoreForeshadowChecker
        checker = CoreForeshadowChecker(chapters_dir=str(tmp_path))

        # 文件不存在
        assert checker._get_chapter_content(999) is None
        assert checker._chapter_content_cache[999] is None
        # 第二次仍返回 None(不重 stat)
        assert checker._get_chapter_content(999) is None

    def test_clear_chapter_cache_empties_dict(self, tmp_path):
        """clear_chapter_cache() 应清空缓存"""
        ch_file = tmp_path / "ch001.md"
        ch_file.write_text("test", encoding="utf-8")
        from infra.consistency.checkers.core_foreshadow_checker import CoreForeshadowChecker
        checker = CoreForeshadowChecker(chapters_dir=str(tmp_path))

        checker._get_chapter_content(1)
        assert 1 in checker._chapter_content_cache
        checker.clear_chapter_cache()
        assert checker._chapter_content_cache == {}

    def test_is_recycled_uses_cache_not_disk_loop(self, tmp_path, monkeypatch):
        """核心场景:_is_recycled 内部对 expect_range 的每个 chapter 只读一次

        通过 monkeypatch 替换 Path.read_text 为计数器,验证调用次数。
        """
        from infra.consistency.checkers.core_foreshadow_checker import CoreForeshadowChecker

        # 准备: ch027-ch029 三个章节,每个含一个关键词
        for i in [27, 28, 29]:
            (tmp_path / f"ch{i:03d}.md").write_text(
                f"这是第{i}章 包含 token{i}", encoding="utf-8"
            )

        checker = CoreForeshadowChecker(chapters_dir=str(tmp_path))

        # Monkey-patch Path.read_text:每章只应被读一次
        from pathlib import Path
        original_read = Path.read_text
        read_count = {}

        def counting_read_text(self, *args, **kwargs):
            read_count[self.name] = read_count.get(self.name, 0) + 1
            return original_read(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", counting_read_text)

        # 触发 _is_recycled,expect_range = ch027-ch029 (3 章)
        result = checker._is_recycled("token28", start_chapter=1, expect_range="ch027-ch029")
        assert result is True

        # ch027 应被读 1 次(命中 → break)
        # ch028 应被读 1 次(命中 → break)
        # ch029 不应被读(已 break)
        assert read_count.get("ch027.md", 0) == 1
        assert read_count.get("ch028.md", 0) == 1
        assert read_count.get("ch029.md", 0) == 0

    def test_check_chapter_dedupes_file_reads_across_foreshadows(self, tmp_path, monkeypatch):
        """核心场景:同一章有 5 个伏笔都引用 ch027 → ch027 只读 1 次

        修复前:5 个伏笔 × 3 章 = 15 次 read_text
        修复后:1 次预缓存 + 5 次 dict 查找 = 1 次 read_text
        """
        from infra.consistency.checkers.core_foreshadow_checker import CoreForeshadowChecker

        # 准备 5 个目标章节
        for i in [27, 28, 29, 30, 31]:
            (tmp_path / f"ch{i:03d}.md").write_text(
                f"ch{i} content 目标词{i}", encoding="utf-8"
            )

        # ch001 有 5 个伏笔,都期望在 ch027-ch031 回收
        ch001_content = (
            "本章 5 个伏笔:\n"
            "【伏笔:core:目标词27:ch027-ch031】\n"
            "【伏笔:core:目标词28:ch027-ch031】\n"
            "【伏笔:core:目标词29:ch027-ch031】\n"
            "【伏笔:core:目标词30:ch027-ch031】\n"
            "【伏笔:core:目标词31:ch027-ch031】\n"
        )
        (tmp_path / "ch001.md").write_text(ch001_content, encoding="utf-8")

        checker = CoreForeshadowChecker(chapters_dir=str(tmp_path))

        # 计数 read_text
        from pathlib import Path
        original_read = Path.read_text
        read_count = {}

        def counting_read_text(self, *args, **kwargs):
            read_count[self.name] = read_count.get(self.name, 0) + 1
            return original_read(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", counting_read_text)

        # 触发 check_chapter
        issues = checker.check_chapter(1)
        # 5 个伏笔都已被回收(每章都有对应目标词)
        assert len(issues) == 0

        # 关键断言:ch027 只读 1 次 (缓存命中),不再被 5 次伏笔循环重读
        # 修复前:ch027 会被读 5 次
        for ch_num in [27, 28, 29, 30, 31]:
            count = read_count.get(f"ch{ch_num:03d}.md", 0)
            assert count == 1, (
                f"ch{ch_num:03d}.md 被读 {count} 次,期望 1 次 — "
                f"缓存未生效,可能 _is_recycled 没走 _get_chapter_content"
            )
