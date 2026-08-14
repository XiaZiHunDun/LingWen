"""创意豁免白名单测试"""

import pytest
from infra.consistency.creative_whitelist import (
    CreativeWhitelist,
    WhitelistChapter,
    WhitelistError,
    ChapterAlreadyWhitelistedError,
    ChapterNotWhitelistedError,
    DIAMOND,
    GOLD,
    SILVER,
    DOWNGRADED_LEVELS,
    add_whitelist,
    is_whitelisted,
    remove_whitelist,
    get_whitelisted_chapters,
)


class TestWhitelistChapter:
    """WhitelistChapter 数据类测试"""

    def test_create_entry(self):
        entry = WhitelistChapter(chapter_num=5, reason="创意实验")
        assert entry.chapter_num == 5
        assert entry.reason == "创意实验"
        assert entry.created_at
        assert entry.expires_at is None

    def test_not_expired_without_expiry(self):
        entry = WhitelistChapter(chapter_num=5, reason="测试")
        assert not entry.is_expired()

    def test_not_expired_future_date(self):
        entry = WhitelistChapter(chapter_num=5, reason="测试", expires_at="2099-12-31")
        assert not entry.is_expired()

    def test_expired_past_date(self):
        entry = WhitelistChapter(chapter_num=5, reason="测试", expires_at="2020-01-01")
        assert entry.is_expired()

    def test_invalid_expiry_format(self):
        entry = WhitelistChapter(chapter_num=5, reason="测试", expires_at="invalid")
        assert not entry.is_expired()  # 无效格式不视为过期


class TestCreativeWhitelist:
    """CreativeWhitelist 管理器测试"""

    def setup_method(self):
        CreativeWhitelist().clear()

    def test_singleton(self):
        a = CreativeWhitelist()
        b = CreativeWhitelist()
        assert a is b

    def test_add_chapter(self):
        wl = CreativeWhitelist()
        entry = wl.add(3, "关键转折章节")
        assert entry.chapter_num == 3
        assert wl.is_whitelisted(3)

    def test_add_duplicate_raises(self):
        wl = CreativeWhitelist()
        wl.add(3, "原因1")
        with pytest.raises(ChapterAlreadyWhitelistedError):
            wl.add(3, "原因2")

    def test_add_invalid_chapter_num(self):
        wl = CreativeWhitelist()
        with pytest.raises(WhitelistError):
            wl.add(0, "无效")
        with pytest.raises(WhitelistError):
            wl.add(-1, "无效")

    def test_add_empty_reason(self):
        wl = CreativeWhitelist()
        with pytest.raises(WhitelistError):
            wl.add(5, "")

    def test_add_with_expiry(self):
        wl = CreativeWhitelist()
        wl.add(5, "测试", expires_at="2099-12-31")
        assert wl.is_whitelisted(5)

    def test_add_invalid_expiry_format(self):
        wl = CreativeWhitelist()
        with pytest.raises(WhitelistError):
            wl.add(5, "测试", expires_at="bad-date")

    def test_is_whitelisted_returns_false_unknown(self):
        wl = CreativeWhitelist()
        assert not wl.is_whitelisted(999)

    def test_is_whitelisted_auto_cleanup_expired(self):
        wl = CreativeWhitelist()
        wl.add(5, "测试", expires_at="2020-01-01")
        assert not wl.is_whitelisted(5)  # 过期自动清理

    def test_remove_chapter(self):
        wl = CreativeWhitelist()
        wl.add(3, "测试")
        removed = wl.remove(3)
        assert removed.chapter_num == 3
        assert not wl.is_whitelisted(3)

    def test_remove_not_found_raises(self):
        wl = CreativeWhitelist()
        with pytest.raises(ChapterNotWhitelistedError):
            wl.remove(999)

    def test_get_whitelisted_chapters(self):
        wl = CreativeWhitelist()
        wl.add(3, "原因A")
        wl.add(1, "原因B")
        chapters = wl.get_whitelisted_chapters()
        assert len(chapters) == 2
        assert chapters[0]["chapter_num"] == 1
        assert chapters[1]["chapter_num"] == 3

    def test_get_whitelisted_chapters_cleans_expired(self):
        wl = CreativeWhitelist()
        wl.add(1, "有效")
        wl.add(2, "过期", expires_at="2020-01-01")
        chapters = wl.get_whitelisted_chapters()
        assert len(chapters) == 1
        assert chapters[0]["chapter_num"] == 1

    def test_downgraded_levels(self):
        wl = CreativeWhitelist()
        levels = wl.get_downgraded_levels()
        assert GOLD in levels
        assert SILVER in levels
        assert DIAMOND not in levels

    def test_should_downgrade(self):
        wl = CreativeWhitelist()
        assert wl.should_downgrade(GOLD)
        assert wl.should_downgrade(SILVER)
        assert not wl.should_downgrade(DIAMOND)

    def test_clear(self):
        wl = CreativeWhitelist()
        wl.add(1, "测试")
        wl.add(2, "测试")
        wl.clear()
        assert len(wl.get_whitelisted_chapters()) == 0

    def test_overwrite_expired(self):
        wl = CreativeWhitelist()
        wl.add(5, "旧原因", expires_at="2020-01-01")
        # 过期后可覆盖
        wl.add(5, "新原因")
        assert wl.is_whitelisted(5)
        chapters = wl.get_whitelisted_chapters()
        assert chapters[0]["reason"] == "新原因"


class TestModuleLevelFunctions:
    """模块级便捷函数测试"""

    def setup_method(self):
        CreativeWhitelist().clear()

    def test_add_whitelist(self):
        add_whitelist(7, "模块级测试")
        assert is_whitelisted(7)

    def test_is_whitelisted(self):
        assert not is_whitelisted(999)
        add_whitelist(3, "测试")
        assert is_whitelisted(3)

    def test_remove_whitelist(self):
        add_whitelist(3, "测试")
        remove_whitelist(3)
        assert not is_whitelisted(3)

    def test_get_whitelisted_chapters(self):
        add_whitelist(5, "A")
        add_whitelist(3, "B")
        chapters = get_whitelisted_chapters()
        assert len(chapters) == 2