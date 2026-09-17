"""Phase 90 Task 10 + Phase 96 Task 14: background tasks for chapter completion hooks.

`illustrations_auto_generate_task`: fire-and-forget illustration generation
triggered by chapter_marked_complete event (PUT /api/write/{chapter_id}).

`_get_illustration_settings`: Phase 96 — reads default_provider from
<project>/.lingwen/illustration_settings.yaml (populated by
PUT /api/projects/{slug}/settings). Falls back to 'minimax' default when
yaml is missing or corrupt.
"""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)


async def illustrations_auto_generate_task(
    project_slug: str,
    chapter_num: int,
    settings: dict[str, Any],
) -> None:
    """Fire-and-forget illustration generation after chapter complete.

    Triggered by chapter_marked_complete event when user has auto-generate
    enabled in project settings. Failures logged but never raised.

    Phase 96: dispatches API credentials via per-project `default_provider`
    (read by `_get_illustration_settings` from the project settings yaml).
    """
    # Lazy imports: avoid loading pipeline deps + avoid potential circular
    # import with apps.studio_api.routes.illustrations at module load time.
    from lingwen_illustrations.exceptions import IllustrationError
    from lingwen_illustrations.pipeline import generate_illustration

    from apps.studio_api.routes._project_helpers import project_root_for
    from apps.studio_api.routes.illustrations import _api_credentials_for

    try:
        project_root = project_root_for(project_slug)
        provider = settings.get("default_provider", "minimax")
        api_key, api_host = _api_credentials_for(provider)
        await generate_illustration(
            project_root=project_root,
            project_slug=project_slug,
            type="chapter",
            chapter_num=chapter_num,
            style_preset=settings.get("style_preset", "ink"),
            custom_prompt=None,
            api_key=api_key,
            api_host=api_host,
            provider=provider,
        )
        log.info(
            f"auto-generated illustration for {project_slug} ch.{chapter_num} "
            f"(provider={provider})"
        )
    except IllustrationError as e:
        log.warning(
            f"auto-generate failed [{e.stage.value}] "
            f"provider={getattr(e, 'provider', 'unknown')}: {e.message}"
        )
    except Exception as e:
        log.error(f"auto-generate unexpected error: {e}")


def _get_illustration_settings(project_slug: str) -> dict[str, Any]:
    """Read illustration settings for the project.

    Phase 96: reads from <project>/.lingwen/illustration_settings.yaml
    (populated by PUT /api/projects/{slug}/settings). Falls back to
    defaults (auto_generate OFF, style_preset 'ink', default_provider
    'minimax') when yaml is missing or corrupt.

    Future fields (max_assets, confirm_before_generate) will be added
    here when ProjectSettings schema extends.
    """
    from lingwen_illustrations.exceptions import LoadError

    from apps.studio_api.routes._project_helpers import project_root_for
    from apps.studio_api.routes.project_settings import _load_settings

    try:
        root = project_root_for(project_slug)
        settings = _load_settings(root)
    except LoadError:
        # Project not found — silent no-op (matches existing Phase 90 behavior).
        return {
            "style_preset": "ink",
            "auto_generate": False,
            "default_provider": "minimax",
        }

    return {
        "style_preset": "ink",  # TODO v2: add style_preset to ProjectSettings
        "auto_generate": False,  # TODO v2: add auto_generate to ProjectSettings
        "default_provider": settings.default_provider,
    }


__all__ = ["illustrations_auto_generate_task", "_get_illustration_settings"]
