"""Story Contract Engine - Main orchestrator for story contracts."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .anti_patterns import AntiPattern, AntiPatternAggregator
from .paths import StoryContractPaths
from .persister import ContractPayload, ContractPersister
from .router import GenreRouter, RouteResult


class StoryContractEngine:
    """Main orchestrator for Story Contracts.

    Coordinates genre routing, anti-pattern aggregation, and contract persistence
    to provide a unified interface for story contract operations.
    """

    SCHEMA_VERSION = "story-contracts/v1"

    def __init__(
        self,
        project_root: str | Path,
        rules_dir: str | Path | None = None,
    ) -> None:
        """Initialize the StoryContractEngine.

        Args:
            project_root: Root directory of the novel project.
            rules_dir: Directory containing rule CSV files.
                Defaults to project_root/rules/story_contracts.
        """
        self.project_root = Path(project_root).expanduser().resolve()
        self.paths = StoryContractPaths.from_project_root(self.project_root)

        if rules_dir is None:
            rules_dir = self.project_root / "rules" / "story_contracts"
        self.rules_dir = Path(rules_dir)

        self.router = GenreRouter(self.rules_dir)
        self.aggregator = AntiPatternAggregator()
        self.persister = ContractPersister(self.paths)

    def build(
        self,
        query: str,
        genre: Optional[str] = None,
        chapter: Optional[int] = None,
    ) -> ContractPayload:
        """Build a story contract from query and genre.

        Args:
            query: The story query or description.
            genre: Optional explicit genre for routing.
            chapter: Optional chapter number for chapter-specific contracts.

        Returns:
            ContractPayload containing the built contract data.
        """
        # Route to get genre info
        route_result = self.router.route(query, genre)

        # Build master_setting
        master_setting = self._build_master_setting(route_result)

        # Build anti-patterns from route result
        anti_patterns = self._build_anti_patterns(route_result)

        # Build chapter_brief if chapter specified
        chapter_brief: Optional[Dict[str, Any]] = None
        if chapter is not None:
            chapter_brief = self._build_chapter_brief(chapter, route_result)

        return ContractPayload(
            master_setting=master_setting,
            anti_patterns=anti_patterns,
            chapter_brief=chapter_brief,
        )

    def persist(self, payload: ContractPayload) -> None:
        """Persist a contract payload to storage.

        Args:
            payload: The ContractPayload to persist.
        """
        self.persister.persist(payload)

    def load(self) -> Optional[ContractPayload]:
        """Load a contract payload from storage.

        Returns:
            ContractPayload if one exists, None otherwise.
        """
        return self.persister.load()

    def _build_master_setting(self, route: RouteResult) -> Dict[str, Any]:
        """Build master_setting dict from RouteResult.

        Args:
            route: The RouteResult from genre routing.

        Returns:
            Master setting dictionary ready for persistence.
        """
        return {
            "meta": {
                "schema_version": self.SCHEMA_VERSION,
                "contract_type": "MASTER_SETTING",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
            "route": {
                "primary_genre": route.primary_genre,
                "genre_aliases": route.genre_aliases,
                "route_source": route.route_source,
            },
            "master_constraints": {
                "core_tone": route.core_tone,
                "pacing_strategy": route.pacing_strategy,
                "forbidden_patterns": route.forbidden_patterns,
            },
            "source_trace": [
                {
                    "table": "题材与调性推理",
                    "id": "GR-001",
                    "reason": route.route_source,
                }
            ],
        }

    def _build_anti_patterns(self, route: RouteResult) -> List[Dict[str, Any]]:
        """Build anti-patterns list from RouteResult.

        Args:
            route: The RouteResult from genre routing.

        Returns:
            List of anti-pattern dictionaries.
        """
        # Convert AntiPattern objects to dicts for persistence
        aggregated = self.aggregator.merge(
            [
                {
                    "text": fp,
                    "source_table": "题材与调性推理",
                    "source_id": "GR-001",
                }
                for fp in route.forbidden_patterns
            ]
        )

        return [
            {
                "text": ap.text,
                "source_table": ap.source_table,
                "source_id": ap.source_id,
            }
            for ap in aggregated
        ]

    def _build_chapter_brief(
        self, chapter: int, route: RouteResult
    ) -> Dict[str, Any]:
        """Build chapter_brief dict for chapter-specific contracts.

        Args:
            chapter: Chapter number.
            route: The RouteResult from genre routing.

        Returns:
            Chapter brief dictionary ready for persistence.
        """
        return {
            "chapter_number": chapter,
            "chapter_constraints": {
                "tone": route.core_tone,
                "pacing_strategy": route.pacing_strategy,
                "forbidden_patterns": route.forbidden_patterns,
            },
        }
