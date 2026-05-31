"""Anti-pattern aggregation and deduplication for Story Contracts."""

from dataclasses import dataclass
from typing import Any, Iterable, List


@dataclass(frozen=True)
class AntiPattern:
    """Represents an anti-pattern found in story content.

    Attributes:
        text: The text content of the anti-pattern.
        source_table: The table name where this anti-pattern was found.
        source_id: The unique identifier within the source table.
    """

    text: str
    source_table: str
    source_id: str


class AntiPatternAggregator:
    """Aggregates anti-patterns from multiple sources with deduplication.

    This class merges multiple groups of anti-pattern dictionaries and
    deduplicates them based on exact text match (case-sensitive).
    When duplicates are found, only the first occurrence's metadata
    (source_table, source_id) is preserved.
    """

    def merge(self, *groups: Iterable[dict[str, Any]]) -> List[AntiPattern]:
        """Merge multiple groups of anti-pattern dictionaries.

        Args:
            *groups: Variable number of iterables of dicts, where each dict
                contains 'text', 'source_table', and 'source_id' keys.

        Returns:
            List of AntiPattern objects with duplicates removed.
            The list maintains insertion order, with first occurrence
            metadata preserved for any duplicates.
        """
        seen_texts: set[str] = set()
        result: List[AntiPattern] = []

        for group in groups:
            for row in group:
                text = row["text"]
                if text not in seen_texts:
                    seen_texts.add(text)
                    result.append(
                        AntiPattern(
                            text=text,
                            source_table=row["source_table"],
                            source_id=row["source_id"],
                        )
                    )

        return result