"""Creator memory semantic query with vector + local fallback."""
from __future__ import annotations

import re
from typing import Any

from infra.creator_memory_assets import creator_memory_assets_payload
from infra.creator_preferences import load_creator_preferences
from infra.studio_registry import StudioProject

_VALID_SCOPES = frozenset({"all", "character", "chapter", "relationship"})


def _extract_matched_terms(query: str, text: str, *, max_terms: int = 6) -> list[str]:
    q = query.strip()
    if not q or not text:
        return []
    terms: list[str] = []
    lowered = text.lower()
    for token in re.findall(r"[\w\u4e00-\u9fff]{2,}", q):
        if token.lower() in lowered and token not in terms:
            terms.append(token)
    if not terms and q.lower() in lowered:
        terms.append(q[:32])
    return terms[:max_terms]


def _normalize_vector_hit(hit: dict[str, Any], query: str) -> dict[str, Any]:
    payload = hit.get("payload") if isinstance(hit.get("payload"), dict) else {}
    text = (
        payload.get("text")
        or payload.get("content")
        or payload.get("excerpt")
        or str(hit.get("id", ""))
    )
    chapter = payload.get("chapter") or payload.get("chapter_num")
    asset_name = str(payload.get("title") or payload.get("name") or "")
    snippet = str(text)[:400]
    citation = str(payload.get("citation") or payload.get("source_path") or "")
    if not citation and chapter is not None:
        citation = f"第{int(chapter)}章 · 向量片段"
    elif not citation:
        citation = "记忆向量库"
    return {
        "id": str(hit.get("id", payload.get("id", ""))),
        "snippet": snippet,
        "score": float(hit.get("score", 0)),
        "chapter": int(chapter) if chapter is not None else None,
        "kind": str(payload.get("type") or "segment"),
        "source": "vector",
        "citation": citation,
        "asset_name": asset_name or None,
        "matched_terms": _extract_matched_terms(query, snippet),
    }


def _local_search(project: StudioProject, query: str, *, top_k: int) -> list[dict[str, Any]]:
    assets = creator_memory_assets_payload(project)
    needle = query.strip().lower()
    if not needle:
        return []
    results: list[dict[str, Any]] = []
    for item in assets.get("items", []):
        name = str(item.get("name", ""))
        excerpt = str(item.get("excerpt", ""))
        hay = f"{name} {excerpt}".lower()
        chapters = item.get("chapters") or []
        if needle not in hay and not any(needle in f"第{ch}章" for ch in chapters):
            continue
        score = 0.55
        if needle in name.lower():
            score += 0.25
        chapter = chapters[0] if chapters else None
        kind = str(item.get("kind", "asset"))
        source = str(item.get("source", "local"))
        citation_parts = [kind, name]
        if chapter:
            citation_parts.append(f"第{chapter}章")
        citation = " · ".join(p for p in citation_parts if p)
        snippet = excerpt
        results.append(
            {
                "id": item.get("id", ""),
                "snippet": snippet,
                "score": min(score, 0.99),
                "chapter": chapter,
                "kind": kind,
                "source": source,
                "citation": citation,
                "asset_name": name,
                "matched_terms": _extract_matched_terms(query, f"{name} {excerpt}"),
            },
        )
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_k]


def creator_memory_query(
    project: StudioProject,
    *,
    query: str,
    scope: str = "all",
    top_k: int | None = None,
) -> dict[str, Any]:
    prefs = load_creator_preferences(project.root)
    limit = top_k if top_k is not None else int(prefs.get("memory_rag_top_k", 8))
    limit = max(1, min(limit, 20))
    scope_val = scope if scope in _VALID_SCOPES else "all"
    q = (query or "").strip()
    if not q:
        return {
            "query": "",
            "memory_available": False,
            "used_fallback": True,
            "results": [],
        }

    vector_results: list[dict[str, Any]] = []
    memory_available = False
    if prefs.get("memory_rag_enabled", True):
        try:
            from infra.memory_service import get_memory_gateway

            gateway = get_memory_gateway()
            if not getattr(gateway, "is_noop", False):
                memory_available = True
                raw = gateway.query(q, scope=scope_val, top_k=limit)
                for hit in raw or []:
                    if isinstance(hit, dict):
                        vector_results.append(_normalize_vector_hit(hit, q))
        except Exception:
            memory_available = False

    if vector_results:
        return {
            "query": q,
            "memory_available": memory_available,
            "used_fallback": False,
            "results": vector_results[:limit],
        }

    local = _local_search(project, q, top_k=limit)
    return {
        "query": q,
        "memory_available": memory_available,
        "used_fallback": True,
        "results": local,
    }
