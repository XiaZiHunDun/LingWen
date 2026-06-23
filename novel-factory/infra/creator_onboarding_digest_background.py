"""Background polling loop for scheduled creator onboarding digest dispatch."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_POLL_SEC = 900


def digest_poll_interval_sec() -> int:
    import os

    raw = os.environ.get("LINGWEN_CREATOR_DIGEST_POLL_SEC", "").strip()
    if not raw:
        return _DEFAULT_POLL_SEC
    try:
        return max(60, int(raw))
    except ValueError:
        return _DEFAULT_POLL_SEC


def tick_digest_for_active_project() -> dict[str, Any]:
    """Run one digest dispatch tick for the active studio project."""
    from infra.creator_onboarding_digest_schedule import (
        dispatch_scheduled_digest,
        load_digest_schedule,
    )
    from infra.studio_registry import active_project

    project = active_project()
    if project is None:
        return {"skipped": True, "reason": "no active project"}
    schedule = load_digest_schedule(project.root)
    if not schedule.get("enabled"):
        return {"skipped": True, "reason": "schedule disabled"}
    return dispatch_scheduled_digest(project.root, force=False)


async def run_digest_background_loop() -> None:
    """Poll digest schedule and dispatch when due."""
    while True:
        await asyncio.sleep(digest_poll_interval_sec())
        try:
            result = await asyncio.to_thread(tick_digest_for_active_project)
            if result.get("sent"):
                logger.info("creator digest background dispatch sent")
        except Exception:
            logger.exception("creator digest background tick failed")


def start_digest_background_task() -> asyncio.Task:
    """Start background digest polling (dashboard lifespan)."""
    return asyncio.create_task(run_digest_background_loop())
