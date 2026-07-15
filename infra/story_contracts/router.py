"""CSV-based genre routing for Story Contracts."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class RouteResult:
    """Result of routing a query to a genre."""

    primary_genre: str
    genre_aliases: List[str]
    core_tone: str
    pacing_strategy: str
    forbidden_patterns: List[str]
    recommended_base_tables: List[str]
    recommended_dynamic_tables: List[str]
    route_source: str  # keyword_match | explicit_genre_fallback | default_fallback | empty_fallback


class GenreRouter:
    """Routes story contract queries to appropriate genres using CSV data."""

    CSV_FILENAME = "题材与调性推理.csv"

    def __init__(self, csv_dir: str | Path) -> None:
        """Initialize router with CSV directory path.

        Args:
            csv_dir: Directory containing the genre CSV files.
        """
        self.csv_dir = Path(csv_dir)

    def route(self, query: str, genre: Optional[str] = None) -> RouteResult:
        """Route a query to the appropriate genre.

        Args:
            query: The story query text to route.
            genre: Optional explicit genre for fallback matching.

        Returns:
            RouteResult with genre information and routing source.
        """
        csv_path = self.csv_dir / self.CSV_FILENAME

        if not csv_path.exists():
            return self._build_empty_result("empty_fallback")

        rows = self._load_csv_rows(self.CSV_FILENAME)
        if not rows:
            return self._build_empty_result("empty_fallback")

        query_normalized = self._normalize_text(query)

        # Step 1: Keyword match
        for row in rows:
            keywords = self._split_multi_value(row.get("关键词", ""))
            synonyms = self._split_multi_value(row.get("意图与同义词", ""))
            aliases = self._split_multi_value(row.get("题材别名", ""))

            all_terms = keywords + synonyms + aliases
            for term in all_terms:
                if term and term in query_normalized:
                    return self._build_result(row, "keyword_match")

        # Step 2: Explicit genre fallback
        if genre:
            genre_normalized = self._normalize_text(genre)
            for row in rows:
                row_genre = self._normalize_text(row.get("题材/流派", ""))
                if row_genre and row_genre == genre_normalized:
                    return self._build_result(row, "explicit_genre_fallback")

        # Step 3: Default fallback (first row)
        return self._build_result(rows[0], "default_fallback")

    def _load_csv_rows(self, filename: str) -> List[dict]:
        """Load CSV file as list of dictionaries.

        Args:
            filename: Name of CSV file to load.

        Returns:
            List of row dictionaries.
        """
        import csv

        csv_path = self.csv_dir / filename
        if not csv_path.exists():
            return []

        rows = []
        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        return rows

    def _normalize_text(self, text: str) -> str:
        """Normalize text for matching (lowercase and strip).

        Args:
            text: Text to normalize.

        Returns:
            Lowercased and stripped text.
        """
        return text.lower().strip()

    def _split_multi_value(self, raw: str) -> List[str]:
        """Split pipe-separated values into list.

        Args:
            raw: Pipe-separated string value.

        Returns:
            List of non-empty stripped values.
        """
        if not raw:
            return []
        return [v.strip() for v in raw.split("|") if v.strip()]

    def _build_result(self, row: dict, route_source: str) -> RouteResult:
        """Build RouteResult from CSV row.

        Args:
            row: CSV row dictionary.
            route_source: Source of the routing decision.

        Returns:
            RouteResult constructed from row data.
        """
        return RouteResult(
            primary_genre=row.get("题材/流派", "unknown"),
            genre_aliases=self._split_multi_value(row.get("题材别名", "")),
            core_tone=row.get("核心调性", "neutral"),
            pacing_strategy=row.get("节奏策略", "standard"),
            forbidden_patterns=self._split_multi_value(row.get("强制禁忌/毒点", "")),
            recommended_base_tables=self._split_multi_value(row.get("推荐基础检索表", "")),
            recommended_dynamic_tables=self._split_multi_value(row.get("推荐动态检索表", "")),
            route_source=route_source,
        )

    def _build_empty_result(self, route_source: str) -> RouteResult:
        """Build empty RouteResult for fallback cases.

        Args:
            route_source: Source indicating why result is empty.

        Returns:
            RouteResult with empty/default values.
        """
        return RouteResult(
            primary_genre="unknown",
            genre_aliases=[],
            core_tone="neutral",
            pacing_strategy="standard",
            forbidden_patterns=[],
            recommended_base_tables=[],
            recommended_dynamic_tables=[],
            route_source=route_source,
        )
