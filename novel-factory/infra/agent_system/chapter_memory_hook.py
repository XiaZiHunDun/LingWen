"""Phase 9.70 F62: optional MemoryGateway RAG hook for chapter workflows."""
from __future__ import annotations

import logging
import os
from typing import Any, Literal, Mapping

from infra.cross_volume.incremental_backfill import extract_chapter_num

logger = logging.getLogger(__name__)

MemoryRagMode = Literal["off", "stub", "live"]
WORKFLOWS_WITH_MEMORY = frozenset({"novel_writing", "chapter_golden"})

MEMORY_RAG_HOOK_BEHAVIOR: tuple[dict[str, str], ...] = (
    {
        "trigger": "env LINGWEN_MEMORY_RAG",
        "behavior": "off (default) | stub | live (1/true/yes)",
    },
    {
        "trigger": "workflow_name",
        "behavior": "novel_writing, chapter_golden",
    },
    {
        "trigger": "chapter_num",
        "behavior": "initial_inputs (same resolver as incremental backfill)",
    },
    {
        "trigger": "stub mode",
        "behavior": "deterministic context, 0 Qdrant (golden path default)",
    },
    {
        "trigger": "live mode",
        "behavior": "MemoryGateway.auto_push_context(chapter_num)",
    },
)


def resolve_memory_rag_mode(explicit: str | None = None) -> MemoryRagMode:
    """Resolve hook mode from explicit override or LINGWEN_MEMORY_RAG env."""
    if explicit is not None:
        normalized = explicit.lower()
        if normalized in ("off", ""):
            return "off"
        if normalized in ("stub", "test"):
            return "stub"
        if normalized in ("1", "true", "yes", "live"):
            return "live"
        return "off"
    env = os.environ.get("LINGWEN_MEMORY_RAG", "").lower()
    if env in ("stub", "test"):
        return "stub"
    if env in ("1", "true", "yes", "live"):
        return "live"
    return "off"


def stub_chapter_memory_context(chapter_num: int) -> dict[str, Any]:
    """Deterministic single-chapter context for stub / CI (0 Qdrant)."""
    prev = max(1, chapter_num - 1)
    return {
        "chapter": chapter_num,
        "character_states": {
            "stub_protagonist": {"location": f"ch{chapter_num}_scene"},
        },
        "pending_foreshadows": {},
        "recent_events": [
            {"chapter": prev, "summary": f"stub event from ch{prev}"},
        ],
        "related_segments": [
            {"text": f"stub RAG segment for chapter {chapter_num}", "score": 1.0},
        ],
        "source": "stub",
    }


def fetch_live_memory_context(
    chapter_num: int,
    *,
    gateway: Any = None,
) -> dict[str, Any]:
    """Live path via MemoryGateway (NoOp-safe when Qdrant unavailable)."""
    if gateway is None:
        from infra.memory_service import get_memory_gateway

        gateway = get_memory_gateway()
    ctx = dict(gateway.auto_push_context(chapter_num))
    ctx["source"] = "live"
    return ctx


def maybe_attach_memory_context(
    workflow_name: str,
    initial_inputs: Mapping[str, Any] | None,
    *,
    mode: str | None = None,
    gateway: Any = None,
) -> dict[str, Any] | None:
    """Return memory_context dict to merge into initial_inputs, or None if skipped."""
    resolved = resolve_memory_rag_mode(mode)
    if resolved == "off":
        return None
    if workflow_name not in WORKFLOWS_WITH_MEMORY:
        return None
    if initial_inputs and initial_inputs.get("memory_context"):
        return None
    chapter_num = extract_chapter_num(initial_inputs, None)
    if chapter_num is None:
        logger.debug("memory RAG skipped: chapter_num unresolved")
        return None
    if resolved == "stub":
        return stub_chapter_memory_context(chapter_num)
    return fetch_live_memory_context(chapter_num, gateway=gateway)


def describe_memory_rag_hook() -> list[dict[str, str]]:
    """Return hook behavior rows for runbook / CLI docs."""
    return [dict(row) for row in MEMORY_RAG_HOOK_BEHAVIOR]


def memory_rag_live_gateway_check() -> tuple[bool, str]:
    """Return (ok, message) for live MemoryGateway (Qdrant + embedding provider)."""
    from infra.memory_service import (
        get_initialization_error,
        get_memory_gateway,
        is_memory_gateway_available,
    )

    get_memory_gateway()
    if is_memory_gateway_available():
        gateway = get_memory_gateway()
        embedder = getattr(gateway, "embedder", None)
        if embedder is not None:
            ok, probe = embedder.health_check()
            detail = (
                f"provider={embedder.provider_name}, model={embedder.model}, "
                f"dim={embedder.dimension}, probe={probe}"
            )
            if ok:
                return True, f"MemoryGateway live ready ({detail})"
            return False, f"MemoryGateway embedder probe failed: {detail}"
        return True, "MemoryGateway live ready (Qdrant + Embedder)"
    err = get_initialization_error() or "MemoryGateway unavailable"
    return False, f"MemoryGateway NoOp: {err}"
