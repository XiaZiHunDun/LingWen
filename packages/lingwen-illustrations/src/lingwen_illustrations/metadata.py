"""IllustrationMetadata dataclass for per-asset .meta.json sidecar.

Stored alongside every .jpg file at:
  <project>/assets/covers/<id>.jpg.meta.json
  <project>/assets/illustrations/chapter-NNN/<id>.jpg.meta.json

Invariant: `created_at` is always an ISO 8601 string with trailing `Z`
(UTC). This lets `storage.list_assets` sort by string comparison without
timezone arithmetic. Callers that emit timestamps MUST format with `Z`.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class IllustrationMetadata:
    """Immutable metadata for one generated illustration asset."""

    id: str
    type: Literal["chapter", "cover"]
    project_slug: str
    chapter_num: int | None  # None for cover
    style_preset: str  # "ink" | "realistic" | "anime"
    custom_prompt: str | None
    scene_json: dict[str, Any]  # Stage 1 output
    final_prompt: str
    prompt_hash: str
    model: str
    created_at: str  # ISO 8601 with trailing Z (UTC)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "IllustrationMetadata":
        try:
            return cls(**d)
        except (KeyError, TypeError) as e:
            from lingwen_illustrations.exceptions import LoadError
            raise LoadError(f"invalid metadata dict: {e}") from e

    @classmethod
    def from_json(cls, raw: str) -> "IllustrationMetadata":
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            from lingwen_illustrations.exceptions import LoadError
            raise LoadError(f"invalid metadata JSON: {e}") from e
        return cls.from_dict(data)


__all__ = ["IllustrationMetadata"]
