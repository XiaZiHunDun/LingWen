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
    """Immutable metadata for one generated illustration asset.

    Phase 96: added `provider` field for per-provider attribution.
    Default 'minimax' for backwards compat with old .meta.json files
    (no provider field). New code always passes provider explicitly.
    """

    id: str
    type: Literal["chapter", "cover"]
    project_slug: str
    chapter_num: int | None  # None for cover
    style_preset: str  # "ink" | "realistic" | "anime"
    custom_prompt: str | None
    scene_json: dict[str, Any]  # Stage 1 output
    final_prompt: str
    prompt_hash: str
    model: str  # "minimax-multimodal" | "dall-e-3" | "sd3-medium" etc.
    created_at: str  # ISO 8601 with trailing Z (UTC)
    # NEW (Phase 96). Default 'minimax' for backwards compat with old
    # .meta.json files (Phase 90-95 era, no provider field). New code
    # always passes provider explicitly. Values: "minimax" | "openai" | "stability".
    provider: str = "minimax"
    # NEW (Phase 97). Default False for backwards compat with Phase 90-96 metadata.json
    # (no used_reference_image field). New code always passes this explicitly.
    used_reference_image: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "IllustrationMetadata":
        # Phase 96 backwards compat: inject "minimax" if old .meta.json
        # lacks provider field (Phase 90-95 era).
        if "provider" not in d:
            d = {**d, "provider": "minimax"}
        # Phase 97 backwards compat: inject False if old .meta.json
        # lacks used_reference_image field (Phase 90-96 era).
        if "used_reference_image" not in d:
            d = {**d, "used_reference_image": False}
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
