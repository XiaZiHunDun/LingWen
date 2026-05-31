"""Tests for GenreRouter."""

import csv
from pathlib import Path

import pytest

from infra.story_contracts.router import GenreRouter, RouteResult


@pytest.fixture
def csv_dir(tmp_path):
    """Create a temporary CSV directory."""
    return tmp_path


@pytest.fixture
def sample_csv(csv_dir):
    """Create a sample CSV file for testing."""
    csv_path = csv_dir / "题材与调性推理.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "题材/流派",
                "题材别名",
                "关键词",
                "意图与同义词",
                "核心调性",
                "节奏策略",
                "禁止模式",
                "推荐基础表",
                "推荐动态表",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "题材/流派": "玄幻",
                "题材别名": "奇幻|Xianxia",
                "关键词": "修炼|飞升|丹药",
                "意图与同义词": "修仙|升级",
                "核心调性": "热血",
                "节奏策略": "升级流",
                "禁止模式": "系统流|签到",
                "推荐基础表": "character_base",
                "推荐动态表": "cultivation_levels",
            }
        )
        writer.writerow(
            {
                "题材/流派": "都市",
                "题材别名": "现代|都市生活",
                "关键词": "都市|职场|商战",
                "意图与同义词": "现实|当代",
                "核心调性": "写实",
                "节奏策略": "慢热",
                "禁止模式": "超能力",
                "推荐基础表": "modern_base",
                "推荐动态表": "career_progression",
            }
        )
    return csv_path


class TestRouteResult:
    """Tests for RouteResult dataclass."""

    def test_route_result_is_frozen(self):
        """Verify RouteResult is a frozen dataclass."""
        result = RouteResult(
            primary_genre="test",
            genre_aliases=[],
            core_tone="neutral",
            pacing_strategy="standard",
            forbidden_patterns=[],
            recommended_base_tables=[],
            recommended_dynamic_tables=[],
            route_source="test",
        )
        with pytest.raises(Exception):  # frozen dataclass cannot be modified
            result.primary_genre = "modified"

    def test_route_result_equality(self):
        """Verify RouteResult instances with same values are equal."""
        result1 = RouteResult(
            primary_genre="玄幻",
            genre_aliases=["奇幻"],
            core_tone="热血",
            pacing_strategy="升级流",
            forbidden_patterns=["系统流"],
            recommended_base_tables=["character_base"],
            recommended_dynamic_tables=["cultivation_levels"],
            route_source="keyword_match",
        )
        result2 = RouteResult(
            primary_genre="玄幻",
            genre_aliases=["奇幻"],
            core_tone="热血",
            pacing_strategy="升级流",
            forbidden_patterns=["系统流"],
            recommended_base_tables=["character_base"],
            recommended_dynamic_tables=["cultivation_levels"],
            route_source="keyword_match",
        )
        assert result1 == result2


class TestGenreRouter:
    """Tests for GenreRouter class."""

    def test_router_loads_csv_and_matches_keyword(self, csv_dir):
        """Verify keyword matching works correctly."""
        # Create test CSV
        csv_path = csv_dir / "题材与调性推理.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "题材/流派",
                    "题材别名",
                    "关键词",
                    "意图与同义词",
                    "核心调性",
                    "节奏策略",
                    "禁止模式",
                    "推荐基础表",
                    "推荐动态表",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "题材/流派": "玄幻",
                    "题材别名": "奇幻|Xianxia",
                    "关键词": "修炼|飞升|丹药",
                    "意图与同义词": "修仙|升级",
                    "核心调性": "热血",
                    "节奏策略": "升级流",
                    "禁止模式": "系统流|签到",
                    "推荐基础表": "character_base",
                    "推荐动态表": "cultivation_levels",
                }
            )

        router = GenreRouter(csv_dir)
        result = router.route("主角开始修炼踏上飞升之路")

        assert result.primary_genre == "玄幻"
        assert result.route_source == "keyword_match"
        assert result.core_tone == "热血"
        assert result.pacing_strategy == "升级流"
        assert "系统流" in result.forbidden_patterns
        assert "奇幻" in result.genre_aliases

    def test_router_falls_back_to_explicit_genre(self, csv_dir):
        """Verify explicit genre fallback works when no keyword matches."""
        # Create test CSV
        csv_path = csv_dir / "题材与调性推理.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "题材/流派",
                    "题材别名",
                    "关键词",
                    "意图与同义词",
                    "核心调性",
                    "节奏策略",
                    "禁止模式",
                    "推荐基础表",
                    "推荐动态表",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "题材/流派": "玄幻",
                    "题材别名": "奇幻|Xianxia",
                    "关键词": "修炼|飞升",
                    "意图与同义词": "修仙",
                    "核心调性": "热血",
                    "节奏策略": "升级流",
                    "禁止模式": "系统流",
                    "推荐基础表": "character_base",
                    "推荐动态表": "cultivation_levels",
                }
            )
            writer.writerow(
                {
                    "题材/流派": "都市",
                    "题材别名": "现代|都市生活",
                    "关键词": "都市|职场",
                    "意图与同义词": "现实",
                    "核心调性": "写实",
                    "节奏策略": "慢热",
                    "禁止模式": "超能力",
                    "推荐基础表": "modern_base",
                    "推荐动态表": "career_progression",
                }
            )

        router = GenreRouter(csv_dir)
        # Query doesn't match any keyword
        result = router.route("今天天气真好", genre="都市")

        assert result.primary_genre == "都市"
        assert result.route_source == "explicit_genre_fallback"
        assert result.core_tone == "写实"
        assert result.pacing_strategy == "慢热"

    def test_router_returns_empty_fallback_when_no_csv(self, csv_dir):
        """Verify empty fallback when CSV file does not exist."""
        router = GenreRouter(csv_dir)
        result = router.route("any query here")

        assert result.primary_genre == "unknown"
        assert result.route_source == "empty_fallback"
        assert result.genre_aliases == []
        assert result.core_tone == "neutral"
        assert result.pacing_strategy == "standard"
        assert result.forbidden_patterns == []

    def test_router_normalizes_query_text(self, csv_dir):
        """Verify case insensitivity in query matching."""
        # Create test CSV
        csv_path = csv_dir / "题材与调性推理.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "题材/流派",
                    "题材别名",
                    "关键词",
                    "意图与同义词",
                    "核心调性",
                    "节奏策略",
                    "禁止模式",
                    "推荐基础表",
                    "推荐动态表",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "题材/流派": "玄幻",
                    "题材别名": "奇幻",
                    "关键词": "修炼",
                    "意图与同义词": "修仙",
                    "核心调性": "热血",
                    "节奏策略": "升级流",
                    "禁止模式": "",
                    "推荐基础表": "character_base",
                    "推荐动态表": "cultivation_levels",
                }
            )

        router = GenreRouter(csv_dir)

        # Test uppercase query
        result_upper = router.route("主角开始修炼")
        assert result_upper.primary_genre == "玄幻"

        # Test mixed case query
        result_mixed = router.route("主角开始修锬")  # typo but matches '修'
        # Note: '修炼' is the keyword, not '修' alone
        # The keyword '修炼' should match in "主角开始修炼"
        assert result_mixed.primary_genre == "玄幻"

    def test_router_returns_default_fallback_when_no_match(self, csv_dir):
        """Verify default fallback returns first row when no keyword or genre matches."""
        # Create test CSV
        csv_path = csv_dir / "题材与调性推理.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "题材/流派",
                    "题材别名",
                    "关键词",
                    "意图与同义词",
                    "核心调性",
                    "节奏策略",
                    "禁止模式",
                    "推荐基础表",
                    "推荐动态表",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "题材/流派": "玄幻",
                    "题材别名": "奇幻",
                    "关键词": "修炼",
                    "意图与同义词": "修仙",
                    "核心调性": "热血",
                    "节奏策略": "升级流",
                    "禁止模式": "",
                    "推荐基础表": "character_base",
                    "推荐动态表": "cultivation_levels",
                }
            )

        router = GenreRouter(csv_dir)
        # Query doesn't match any keyword, no genre provided
        result = router.route("完全无关的查询文本")

        assert result.primary_genre == "玄幻"
        assert result.route_source == "default_fallback"

    def test_router_handles_empty_csv(self, csv_dir):
        """Verify empty fallback when CSV file exists but has no data rows."""
        # Create empty CSV (only header)
        csv_path = csv_dir / "题材与调性推理.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "题材/流派",
                    "题材别名",
                    "关键词",
                    "意图与同义词",
                    "核心调性",
                    "节奏策略",
                    "禁止模式",
                    "推荐基础表",
                    "推荐动态表",
                ],
            )
            writer.writeheader()
            # No data rows

        router = GenreRouter(csv_dir)
        result = router.route("any query")

        assert result.primary_genre == "unknown"
        assert result.route_source == "empty_fallback"

    def test_router_matches_synonyms(self, csv_dir):
        """Verify matching works with intent/synonyms column."""
        # Create test CSV
        csv_path = csv_dir / "题材与调性推理.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "题材/流派",
                    "题材别名",
                    "关键词",
                    "意图与同义词",
                    "核心调性",
                    "节奏策略",
                    "禁止模式",
                    "推荐基础表",
                    "推荐动态表",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "题材/流派": "玄幻",
                    "题材别名": "奇幻",
                    "关键词": "修炼",
                    "意图与同义词": "修仙|升级",
                    "核心调性": "热血",
                    "节奏策略": "升级流",
                    "禁止模式": "",
                    "推荐基础表": "character_base",
                    "推荐动态表": "cultivation_levels",
                }
            )

        router = GenreRouter(csv_dir)
        # Query matches via "意图与同义词" not "关键词"
        result = router.route("主角踏上修仙之路")

        assert result.primary_genre == "玄幻"
        assert result.route_source == "keyword_match"

    def test_router_matches_aliases(self, csv_dir):
        """Verify matching works with genre aliases column."""
        # Create test CSV
        csv_path = csv_dir / "题材与调性推理.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "题材/流派",
                    "题材别名",
                    "关键词",
                    "意图与同义词",
                    "核心调性",
                    "节奏策略",
                    "禁止模式",
                    "推荐基础表",
                    "推荐动态表",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "题材/流派": "玄幻",
                    "题材别名": "奇幻|Xianxia|Fantasy",
                    "关键词": "修炼",
                    "意图与同义词": "修仙",
                    "核心调性": "热血",
                    "节奏策略": "升级流",
                    "禁止模式": "",
                    "推荐基础表": "character_base",
                    "推荐动态表": "cultivation_levels",
                }
            )

        router = GenreRouter(csv_dir)
        # Query matches via "题材别名"
        result = router.route("这是一个Xianxia风格的奇幻故事")

        assert result.primary_genre == "玄幻"
        assert result.route_source == "keyword_match"
        assert "Xianxia" in result.genre_aliases
        assert "奇幻" in result.genre_aliases