"""Creator writing agent plan API (director paths / rewrite / prompt)."""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from infra.paths import ProjectPaths

logger = logging.getLogger(__name__)

VALID_LENSES = frozenset({"author", "editor", "reviewer", "polish", "roleplay"})
VALID_PROVIDER_MODES = frozenset({"auto", "mock", "llm"})

_PATH_CONSEQUENCES = {
    "faster": "信息披露前移，悬念减弱但推进加快",
    "restrained": "情绪降温、留白增加，适合铺垫后段",
    "conflict": "对立加深，后续需安排收束与代价",
}

_LENS_STATUS_SUFFIX = {
    "author": "",
    "editor": "（编辑透镜：标注弱/虚/散）",
    "reviewer": "（审稿透镜：逻辑与信息清晰度）",
    "polish": "（打磨透镜：句级节奏）",
    "roleplay": "（角色透镜：台词草案）",
}

_AGENT_SYSTEM = """你是网文写作导演助手。根据用户任务与透镜模式，输出严格 JSON（不要 markdown 包裹以外的说明）。
JSON 结构：
{
  "advice_only": boolean,
  "candidates": [{"id":"steady|balanced|bold","label":"稳健|平衡|大胆","direction":"简短方向","text":"完整改写文本"}],
  "advice": [{"id":"a1","text":"建议"}],
  "annotations": [{"id":"e1","level":"warn|info|error","text":"标注说明","paragraph": 1}]
}
规则：
- advice_only 为 true 时 candidates 必须为空数组，advice 2-4 条
- 未允许补全世界观时不要添加用户未交代的设定
- editor 透镜：annotations 至少 2 条，candidates 可为空
- reviewer 透镜：advice 聚焦逻辑漏洞与信息不清
- polish 透镜：candidates 为句级改写，每条 text 不超过 200 字
- roleplay 透镜：candidates 为角色台词草案
- 使用中文
"""


def _excerpt(text: str, limit: int = 120) -> str:
    compact = re.sub(r"\s+", " ", (text or "").strip())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


def _has_llm_api_key() -> bool:
    return bool(
        os.environ.get("MINIMAX_API_KEY", "").strip()
        or os.environ.get("ANTHROPIC_API_KEY", "").strip()
        or os.environ.get("OPENAI_API_KEY", "").strip()
    )


def _memory_character_hints(project_root: Path) -> list[str]:
    hints: list[str] = []
    try:
        from infra.memory_service import get_memory_gateway

        gateway = get_memory_gateway()
        if getattr(gateway, "is_noop", False):
            return hints
        characters = gateway.get_all_characters() if hasattr(gateway, "get_all_characters") else {}
        for name, state in (characters or {}).items():
            loc = state.get("current_location") or ""
            alive = state.get("alive")
            status = "存活" if alive is not False else "已故"
            detail = " · ".join(p for p in [loc, status] if p)
            hints.append(f"{name}：{detail}" if detail else name)
            if len(hints) >= 3:
                break
    except Exception:
        return hints
    return hints


def _resolve_base_text(
    project_root: Path,
    *,
    scope: dict[str, Any],
    body_draft: str | None,
) -> str:
    scope_type = scope.get("type") or "none"
    if scope_type == "selection":
        text = (scope.get("selection_text") or "").strip()
        if text:
            return text
    if scope_type == "chapter":
        if body_draft and body_draft.strip():
            return body_draft.strip()
        chapter = scope.get("chapter")
        if chapter:
            try:
                paths = ProjectPaths.get(project_root)
                content = paths.read_chapter(int(chapter))
                if content:
                    return content.strip()
            except Exception:
                pass
    return (body_draft or "").strip()


def _path_id_from_action(action: str) -> str | None:
    if action.startswith("path:"):
        return action.split(":", 1)[1]
    return None


def _normalize_lens(lens: str | None) -> str:
    val = (lens or "author").strip().lower()
    return val if val in VALID_LENSES else "author"


def _normalize_provider_mode(mode: str | None) -> str:
    val = (mode or "auto").strip().lower()
    return val if val in VALID_PROVIDER_MODES else "auto"


def _mock_candidates(base_text: str, action_label: str, *, allow_fill: bool, lens: str) -> list[dict[str, Any]]:
    seed = base_text.strip() or "（待生成内容）"
    fill_note = "" if allow_fill else "（不补全世界观）"
    if lens == "roleplay":
        return [
            {"id": "steady", "label": "内敛", "direction": "克制台词", "text": f"「……」\n（{action_label} · 内敛{fill_note}）"},
            {"id": "balanced", "label": "平衡", "direction": "自然对话", "text": f"「你说什么？」\n（{action_label} · 平衡{fill_note}）"},
            {"id": "bold", "label": "外放", "direction": "强情绪", "text": f"「别逼我！」\n（{action_label} · 外放{fill_note}）"},
        ]
    if lens == "polish":
        snippet = seed.split("\n")[0][:80] if seed else seed
        return [
            {"id": "steady", "label": "稳健", "direction": "句级微调", "text": f"{snippet}（{action_label} · 稳健{fill_note}）"},
            {"id": "balanced", "label": "平衡", "direction": "节奏优化", "text": f"{snippet}——{action_label}（平衡{fill_note}）"},
            {"id": "bold", "label": "大胆", "direction": "意象加密", "text": f"{snippet}！（{action_label} · 大胆{fill_note}）"},
        ]
    return [
        {"id": "steady", "label": "稳健", "direction": "更稳健", "text": f"{seed}\n\n[{action_label} · 稳健候选{fill_note}]"},
        {"id": "balanced", "label": "平衡", "direction": "更平衡", "text": f"{seed}\n\n[{action_label} · 平衡候选{fill_note}]"},
        {"id": "bold", "label": "大胆", "direction": "更戏剧", "text": f"{seed}\n\n[{action_label} · 大胆候选{fill_note}]"},
    ]


def _mock_annotations(lens: str, action_label: str) -> list[dict[str, Any]]:
    if lens == "editor":
        return [
            {"id": "e1", "level": "warn", "text": f"铺垫略长，进入「{action_label}」前可删 1 句环境描写", "paragraph": 1},
            {"id": "e2", "level": "info", "text": "对话信息量可再集中，避免解释性旁白", "paragraph": 2},
        ]
    if lens == "reviewer":
        return [
            {"id": "r1", "level": "warn", "text": "读者可能尚不清楚角色当下目标", "paragraph": 1},
            {"id": "r2", "level": "info", "text": "因果承接尚可加强（上一段结果 → 本段反应）", "paragraph": 2},
        ]
    return []


def _mock_advice(
    action_label: str,
    *,
    path_id: str | None,
    goal_tag: str | None,
    memory_hints: list[str],
    lens: str,
) -> list[dict[str, str]]:
    consequence = _PATH_CONSEQUENCES.get(path_id or "", "注意本章与上一章的情绪承接")
    if goal_tag == "suspense" and path_id == "faster":
        consequence = "悬疑感可能减弱，建议保留 1 处未解信息"
    if lens == "reviewer":
        items = [
            {"id": "a1", "text": "检查读者此刻是否知道「谁想要什么」"},
            {"id": "a2", "text": f"针对「{action_label}」：信息是否给得太早或太晚"},
            {"id": "a3", "text": "标出可能让读者出戏的因果跳跃"},
        ]
    elif lens == "editor":
        items = [
            {"id": "a1", "text": "先标出最弱的一段，再决定删还是改"},
            {"id": "a2", "text": f"「{action_label}」处是否缺少具体动作支撑"},
            {"id": "a3", "text": "检查是否有重复意象或空泛形容词"},
        ]
    else:
        items = [
            {"id": "a1", "text": f"可先缩短铺垫句，再进入「{action_label}」的核心动作"},
            {"id": "a2", "text": consequence},
            {"id": "a3", "text": "保留一句你满意的原句作为锚点，其余再改"},
        ]
    if memory_hints:
        items.append({"id": "a4", "text": f"记忆约束：{'；'.join(memory_hints[:2])}"})
    return items[:4]


def _build_llm_prompt(
    *,
    action: str,
    action_label: str,
    base: str,
    lens: str,
    style_strength: int,
    allow_fill: bool,
    goal_tag: str | None,
    memory_hints: list[str],
    execution_mode: str,
) -> str:
    hints = "\n".join(f"- {h}" for h in memory_hints) or "(无)"
    goal = goal_tag or "(未指定)"
    return (
        f"透镜: {lens}\n"
        f"任务 action: {action}\n"
        f"任务说明: {action_label}\n"
        f"风格强度(0-3): {style_strength}\n"
        f"允许补全世界观: {'是' if allow_fill else '否'}\n"
        f"写作目标标签: {goal}\n"
        f"执行模式: {execution_mode}\n"
        f"记忆约束:\n{hints}\n\n"
        f"待处理文本:\n{base[:5000]}\n"
    )


def _llm_agent_plan(prompt: str, *, advice_only: bool) -> dict[str, Any]:
    from infra.llm_service import LLMService, LLMTask, TaskType

    service = LLMService.get()
    raw = service.execute(
        LLMTask(
            task_type=TaskType.REPAIR if not advice_only else TaskType.QUALITY_ANALYSIS,
            system=_AGENT_SYSTEM,
            prompt=prompt,
            max_tokens=2800,
            temperature=0.45,
        ),
    )
    parsed = service.parse_json_response(raw)
    if not isinstance(parsed, dict):
        raise ValueError("LLM response is not a JSON object")
    return parsed


def _coerce_plan_payload(
    payload: dict[str, Any],
    *,
    fallback_advice_only: bool,
) -> dict[str, Any]:
    advice_only = bool(payload.get("advice_only", fallback_advice_only))
    candidates = payload.get("candidates") if isinstance(payload.get("candidates"), list) else []
    advice = payload.get("advice") if isinstance(payload.get("advice"), list) else []
    annotations = payload.get("annotations") if isinstance(payload.get("annotations"), list) else []
    out_candidates = []
    for row in candidates[:3]:
        if not isinstance(row, dict) or not row.get("text"):
            continue
        out_candidates.append({
            "id": str(row.get("id") or "steady"),
            "label": str(row.get("label") or "候选"),
            "direction": str(row.get("direction") or ""),
            "text": str(row.get("text")),
        })
    out_advice = []
    for i, row in enumerate(advice[:4]):
        if not isinstance(row, dict):
            continue
        text = str(row.get("text") or "").strip()
        if text:
            out_advice.append({"id": str(row.get("id") or f"a{i + 1}"), "text": text})
    out_annotations = []
    for i, row in enumerate(annotations[:6]):
        if not isinstance(row, dict):
            continue
        text = str(row.get("text") or "").strip()
        if not text:
            continue
        level = str(row.get("level") or "info")
        if level not in {"warn", "info", "error"}:
            level = "info"
        item = {"id": str(row.get("id") or f"e{i + 1}"), "level": level, "text": text}
        if row.get("paragraph") is not None:
            item["paragraph"] = int(row["paragraph"])
        out_annotations.append(item)
    return {
        "advice_only": advice_only,
        "candidates": out_candidates,
        "advice": out_advice,
        "annotations": out_annotations,
    }


def _mock_plan(
    *,
    base: str,
    action_label: str,
    path_id: str | None,
    goal_tag: str | None,
    memory_hints: list[str],
    style_strength: int,
    allow_fill: bool,
    execution_mode: str,
    lens: str,
) -> dict[str, Any]:
    annotations = _mock_annotations(lens, action_label)
    if style_strength <= 0:
        return {
            "advice_only": True,
            "candidates": [],
            "advice": _mock_advice(
                action_label,
                path_id=path_id,
                goal_tag=goal_tag,
                memory_hints=memory_hints,
                lens=lens,
            ),
            "annotations": annotations,
            "status_line": "导演建议已就绪（只建议模式，不改正文）" + _LENS_STATUS_SUFFIX.get(lens, ""),
            "provider": "mock",
            "base_excerpt": _excerpt(base),
            "memory_hints": memory_hints,
            "lens": lens,
        }

    candidates = _mock_candidates(base, action_label, allow_fill=allow_fill, lens=lens)
    if lens in {"editor", "reviewer"} and annotations:
        candidates = candidates[:1]

    preview = execution_mode == "preview"
    status = (
        "候选已就绪（预览模式，不覆盖正文）"
        if preview
        else "请确认后应用（将创建回滚点）"
    )
    return {
        "advice_only": False,
        "candidates": candidates,
        "advice": [],
        "annotations": annotations,
        "status_line": status + _LENS_STATUS_SUFFIX.get(lens, ""),
        "provider": "mock",
        "base_excerpt": _excerpt(base),
        "memory_hints": memory_hints,
        "lens": lens,
    }


def run_creator_agent_plan(
    project_root: Path | str,
    *,
    action: str,
    action_label: str,
    scope: dict[str, Any],
    body_draft: str | None = None,
    style_strength: int = 1,
    allow_worldbuilding_fill: bool = False,
    goal_tag: str | None = None,
    execution_mode: str = "preview",
    lens: str | None = "author",
    provider_mode: str | None = "auto",
) -> dict[str, Any]:
    """Build agent plan via LLM when configured, else mock."""
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    lens_norm = _normalize_lens(lens)
    mode = _normalize_provider_mode(provider_mode)
    scope_type = scope.get("type") or "none"
    if scope_type not in {"selection", "chapter"}:
        raise ValueError("scope.type must be selection or chapter")

    if scope_type == "chapter" and not scope.get("chapter"):
        raise ValueError("scope.chapter required for chapter scope")

    if scope_type == "selection" and not (scope.get("selection_text") or "").strip():
        raise ValueError("scope.selection_text required for selection scope")

    base = _resolve_base_text(root, scope=scope, body_draft=body_draft)
    memory_hints = _memory_character_hints(root)
    path_id = _path_id_from_action(action)
    advice_only = int(style_strength) <= 0

    use_llm = mode == "llm" or (mode == "auto" and _has_llm_api_key())
    if use_llm and mode != "mock":
        try:
            prompt = _build_llm_prompt(
                action=action,
                action_label=action_label,
                base=base,
                lens=lens_norm,
                style_strength=style_strength,
                allow_fill=allow_worldbuilding_fill,
                goal_tag=goal_tag,
                memory_hints=memory_hints,
                execution_mode=execution_mode,
            )
            parsed = _llm_agent_plan(prompt, advice_only=advice_only)
            coerced = _coerce_plan_payload(parsed, fallback_advice_only=advice_only)
            if not coerced["advice_only"] and not coerced["candidates"] and not coerced["annotations"]:
                raise ValueError("LLM returned empty plan")
            preview = execution_mode == "preview"
            status = coerced.get("status_line") or (
                "导演建议已就绪（只建议模式）" if coerced["advice_only"]
                else ("候选已就绪（预览模式）" if preview else "请确认后应用")
            )
            from infra.llm_service import LLMService

            return {
                **coerced,
                "status_line": str(status) + _LENS_STATUS_SUFFIX.get(lens_norm, ""),
                "provider": LLMService.get().provider_name,
                "base_excerpt": _excerpt(base),
                "memory_hints": memory_hints,
                "lens": lens_norm,
            }
        except Exception as exc:
            logger.warning("creator agent LLM failed, fallback to mock: %s", exc)
            if mode == "llm":
                raise

    result = _mock_plan(
        base=base,
        action_label=action_label,
        path_id=path_id,
        goal_tag=goal_tag,
        memory_hints=memory_hints,
        style_strength=style_strength,
        allow_fill=allow_worldbuilding_fill,
        execution_mode=execution_mode,
        lens=lens_norm,
    )
    return result


def _chunk_text(text: str, size: int = 24) -> list[str]:
    compact = text or ""
    if not compact:
        return []
    return [compact[i : i + size] for i in range(0, len(compact), size)]


def iter_creator_agent_plan_stream(
    project_root: Path | str,
    *,
    action: str,
    action_label: str,
    scope: dict[str, Any],
    body_draft: str | None = None,
    style_strength: int = 1,
    allow_worldbuilding_fill: bool = False,
    goal_tag: str | None = None,
    execution_mode: str = "preview",
    lens: str | None = "author",
    provider_mode: str | None = "auto",
) -> Any:
    """Yield SSE-friendly event dicts: status | preview_label | chunk | advice | done."""
    yield {"type": "status", "message": "正在分析写作范围…"}
    yield {"type": "status", "message": "正在生成候选…"}
    plan = run_creator_agent_plan(
        project_root,
        action=action,
        action_label=action_label,
        scope=scope,
        body_draft=body_draft,
        style_strength=style_strength,
        allow_worldbuilding_fill=allow_worldbuilding_fill,
        goal_tag=goal_tag,
        execution_mode=execution_mode,
        lens=lens,
        provider_mode=provider_mode,
    )
    if plan.get("advice_only"):
        for row in plan.get("advice") or []:
            text = str(row.get("text") or "").strip()
            if text:
                yield {"type": "advice", "text": text}
    else:
        candidates = plan.get("candidates") or []
        primary = candidates[0] if candidates else None
        if primary:
            label = str(primary.get("label") or "候选")
            yield {"type": "preview_label", "label": label}
            for piece in _chunk_text(str(primary.get("text") or "")):
                yield {"type": "chunk", "text": piece}
    yield {"type": "done", "plan": plan}
