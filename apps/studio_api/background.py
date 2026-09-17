"""Phase 90 Task 10: background tasks for chapter completion hooks.

`illustrations_auto_generate_task`: fire-and-forget illustration generation
triggered by chapter_marked_complete event (PUT /api/write/{chapter_id}).

`_get_illustration_settings`: v1 stub returning default illustration settings
(auto_generate OFF by default). v2 will read from project config.
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
    """
    # Lazy imports: avoid loading pipeline deps + avoid potential circular
    # import with apps.studio_api.routes.illustrations at module load time.
    from lingwen_illustrations.exceptions import IllustrationError
    from lingwen_illustrations.pipeline import generate_illustration

    from apps.studio_api.routes._project_helpers import project_root_for
    from apps.studio_api.routes.illustrations import (
        _api_credentials,
    )

    try:
        project_root = project_root_for(project_slug)
        api_key, api_host = _api_credentials()
        await generate_illustration(
            project_root=project_root,
            project_slug=project_slug,
            type="chapter",
            chapter_num=chapter_num,
            style_preset=settings.get("style_preset", "ink"),
            custom_prompt=None,
            api_key=api_key,
            api_host=api_host,
        )
        log.info(f"auto-generated illustration for {project_slug} ch.{chapter_num}")
    except IllustrationError as e:
        log.warning(f"auto-generate failed [{e.stage.value}]: {e.message}")
    except Exception as e:
        log.error(f"auto-generate unexpected error: {e}")


def _get_illustration_settings(project_slug: str) -> dict[str, Any]:
    """v1 stub: return default illustration settings.

    v2: read from <project>/.lingwen/illustration_settings.yaml or similar.
    Default OFF — auto_generate must be explicitly enabled by v2 config.
    """
    return {
        "style_preset": "ink",
        "auto_generate": False,
    }


__all__ = ["illustrations_auto_generate_task", "_get_illustration_settings"]
