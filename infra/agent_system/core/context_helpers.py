"""TODO(Phase18): replace with proper domain entity from packages/lingwen-domain.

Phase 17.0 local stub for the story contract engine that
``ContextBuilder._get_story_contract`` consumed via ``infra.story_contracts``.

This module preserves the same surface that ``context_builder`` expects
(constructor + ``load()`` returning a payload with ``master_setting`` and
``anti_patterns``) so the rest of the agent_system keeps importing cleanly
after the deferred ``infra.story_contracts`` module is removed.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional


class _StoryContractPayload:
    """Payload with the same attribute shape the upstream uses."""

    def __init__(self, master_setting: dict[str, Any], anti_patterns: list[dict[str, Any]]):
        self.master_setting = master_setting
        self.anti_patterns = anti_patterns


class StoryContractEngine:
    """Local stub: tries upstream ``infra.story_contracts`` if importable,
    else returns an empty payload (no story contract injected).

    The upstream ``load()`` reads ``.story-system/`` from project_root and
    returns a parsed payload or None. Phase 17 callers receive None and
    silently skip the injection branch — same behavior as the existing
    try/except wrapper that swallows all exceptions.
    """

    def __init__(self, project_root: Optional[str | Path] = None) -> None:
        self.project_root = Path(project_root) if project_root else Path.cwd()

    def load(self) -> Optional[_StoryContractPayload]:
        # Try the upstream first (legacy still works during transition).
        try:
            from infra.story_contracts import StoryContractEngine as _Upstream  # type: ignore[import-not-found]
            engine = _Upstream(project_root=self.project_root)
            return engine.load()
        except Exception:
            return None


__all__ = ["StoryContractEngine"]
