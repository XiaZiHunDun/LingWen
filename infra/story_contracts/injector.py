"""Story Contract Context Injector for hooks.yaml integration."""

from pathlib import Path
from typing import Any, Dict, Optional

from .engine import StoryContractEngine
from .persister import ContractPayload


class StoryContractInjector:
    """Injects story contract data into the writing context.

    This class provides the interface used by hooks.yaml BEFORE_WRITE triggers
    to inject genre routing and anti-pattern constraints into the context.
    """

    def __init__(self, project_root: str | Path | None = None) -> None:
        """Initialize the injector.

        Args:
            project_root: Root directory of the novel project.
                Defaults to current working directory.
        """
        if project_root is None:
            project_root = Path.cwd()
        self.project_root = Path(project_root).expanduser().resolve()
        self._engine: Optional[StoryContractEngine] = None

    @property
    def engine(self) -> StoryContractEngine:
        """Lazy-load engine on first access."""
        if self._engine is None:
            self._engine = StoryContractEngine(project_root=self.project_root)
        return self._engine

    def inject_story_contract(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Inject story contract data into the writing context.

        This method is called by the hooks.yaml BEFORE_WRITE trigger.
        It loads the persisted contract (if any) and injects it into the
        context dict under the 'story_contract' key.

        Args:
            context: The existing context dict (may be modified in place).

        Returns:
            The modified context dict with story_contract injected.
        """
        payload = self.engine.load()

        if payload is None:
            context["story_contract"] = {
                "available": False,
                "message": "No story contract found. Run 'lingwen.py story-contract' first.",
            }
            return context

        context["story_contract"] = self._payload_to_context(payload)
        context["story_contract"]["available"] = True
        return context

    def _payload_to_context(self, payload: ContractPayload) -> Dict[str, Any]:
        """Convert ContractPayload to context dict format.

        Args:
            payload: The contract payload to convert.

        Returns:
            Context-ready dict with story_contract section.
        """
        result = {
            "route": {
                "primary_genre": payload.master_setting.get("route", {}).get("primary_genre", "unknown"),
                "genre_aliases": payload.master_setting.get("route", {}).get("genre_aliases", []),
                "route_source": payload.master_setting.get("route", {}).get("route_source", "unknown"),
            },
            "master_constraints": {
                "core_tone": payload.master_setting.get("master_constraints", {}).get("core_tone", ""),
                "pacing_strategy": payload.master_setting.get("master_constraints", {}).get("pacing_strategy", ""),
                "forbidden_patterns": payload.master_setting.get("master_constraints", {}).get("forbidden_patterns", []),
            },
            "anti_patterns": [
                {"text": ap.get("text", ""), "source": ap.get("source_table", "unknown")}
                for ap in payload.anti_patterns
            ],
        }

        if payload.chapter_brief is not None:
            result["chapter_brief"] = {
                "chapter_number": payload.chapter_brief.get("chapter_number"),
                "tone": payload.chapter_brief.get("chapter_constraints", {}).get("tone", ""),
                "pacing_strategy": payload.chapter_brief.get("chapter_constraints", {}).get("pacing_strategy", ""),
                "forbidden_patterns": payload.chapter_brief.get("chapter_constraints", {}).get("forbidden_patterns", []),
            }

        return result


def inject_story_contract(context: Dict[str, Any], project_root: str | Path | None = None) -> Dict[str, Any]:
    """Standalone function for hooks.yaml integration.

    This is the function called by the hooks.yaml trigger:
        module: "infra.story_contracts.injector"
        method: "inject_story_contract"

    Args:
        context: The context dict from the hook system.
        project_root: Optional project root override.

    Returns:
        Context with story_contract injected.
    """
    injector = StoryContractInjector(project_root=project_root)
    return injector.inject_story_contract(context)
