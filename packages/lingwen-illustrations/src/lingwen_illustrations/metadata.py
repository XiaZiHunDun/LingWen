"""IllustrationMetadata dataclass for per-asset .meta.json sidecar.

Stored alongside every .jpg file at:
  <project>/assets/covers/<id>.jpg.meta.json
  <project>/assets/illustrations/chapter-NNN/<id>.jpg.meta.json
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class IllustrationMetadata:
    """Immutable metadata for one generated illustration asset."""

    id: str
    type: str  # "chapter" | "cover"
    project_slug: str
    chapter_num: int | None  # None for cover
    style_preset: str  # "ink" | "realistic" | "anime"
    custom_prompt: str | None
    scene_json: dict[str, Any]  # Stage 1 output
    final_prompt: str
    prompt_hash: str
    model: str
    created_at: str  # ISO 8601

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "IllustrationMetadata":
        return cls(**d)

    @classmethod
    def from_json(cls, raw: str) -> "IllustrationMetadata":
        return cls.from_dict(json.loads(raw))


__all__ = ["IllustrationMetadata"]
