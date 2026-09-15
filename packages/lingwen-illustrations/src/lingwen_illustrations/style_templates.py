"""Style preset templates + custom prompt override.

3 fixed presets (ink / realistic / anime). Custom prompt appended
verbatim if provided. Validation raises ComposeError on invalid preset.
"""

from __future__ import annotations

from typing import Any

from lingwen_illustrations.exceptions import ComposeError

# Style template fragments. Each is a base instruction appended before
# scene content. Custom prompts are appended after the scene.
_STYLE_TEMPLATES: dict[str, str] = {
    "ink": (
        "古风水墨画风格，宣纸质感，淡墨晕染，"
        "留白构图，"
    ),
    "realistic": (
        "Photorealistic digital painting, high detail, "
        "cinematic lighting, 8k resolution, "
    ),
    "anime": (
        "Anime illustration style, vibrant colors, "
        "clean linework, expressive characters, "
    ),
}


def list_presets() -> list[str]:
    """Return available style preset names."""
    return list(_STYLE_TEMPLATES.keys())


def compose(
    preset: str,
    *,
    scene_json: dict[str, Any],
    custom_prompt: str | None,
) -> str:
    """Compose final image generation prompt from preset + scene + override.

    Args:
        preset: One of "ink" | "realistic" | "anime".
        scene_json: Stage 1 extraction output with subject/scene/mood/
            characters_in_scene fields.
        custom_prompt: Optional user override, appended verbatim.

    Returns:
        Final prompt string for image API.

    Raises:
        ComposeError: If preset is unknown or scene_json is malformed.
    """
    if preset not in _STYLE_TEMPLATES:
        raise ComposeError(f"unknown preset '{preset}'; choose from {list_presets()}")

    for required in ("subject", "scene", "mood", "characters_in_scene"):
        if required not in scene_json:
            raise ComposeError(f"scene_json missing required field '{required}'")

    parts: list[str] = [_STYLE_TEMPLATES[preset]]

    parts.append(f"主体: {scene_json['subject']}")
    parts.append(f"场景: {scene_json['scene']}")
    parts.append(f"氛围: {scene_json['mood']}")

    for char in scene_json["characters_in_scene"]:
        name = char.get("name", "未命名")
        visual = char.get("key_visual", "")
        parts.append(f"角色 {name}: {visual}")

    if custom_prompt:
        parts.append(f"附加: {custom_prompt}")

    return "。".join(parts)


PRESETS = list_presets

__all__ = ["PRESETS", "compose", "list_presets"]
