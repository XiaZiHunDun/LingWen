"""Creator UI preferences (model, temperature, memory RAG) per project."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_STATE_VERSION = "1"
_DEFAULT: dict[str, Any] = {
    "default_model": "minimax-abab6.5",
    "temperature": 0.7,
    "max_tokens": 8000,
    "memory_rag_enabled": True,
    "memory_rag_top_k": 8,
    "task_models": {
        "outline": "inherit",
        "body": "inherit",
        "review": "inherit",
        "memory": "inherit",
    },
    "companion_lightweight": True,
    "intervention_rules": {
        "deviation_alerts": True,
        "batch_progress": True,
        "logic_p0": True,
        "settings_unsaved": True,
        "preferences_unsaved": True,
        "memory_offline": True,
        "empty_write_hint": True,
    },
}
_TASK_KEYS = frozenset({"outline", "body", "review", "memory"})
_INTERVENTION_RULE_KEYS = frozenset(_DEFAULT["intervention_rules"].keys())


def _prefs_path(project_root: Path | str) -> Path:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    return root / ".state" / "creator_preferences.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _clamp_float(value: Any, *, low: float, high: float, default: float) -> float:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, num))


def _clamp_int(value: Any, *, low: int, high: int, default: int) -> int:
    try:
        num = int(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, num))


def normalize_creator_preferences(data: dict[str, Any] | None) -> dict[str, Any]:
    src = data or {}
    task_models = dict(_DEFAULT["task_models"])
    raw_tasks = src.get("task_models") or {}
    if isinstance(raw_tasks, dict):
        for key in _TASK_KEYS:
            val = str(raw_tasks.get(key, "inherit"))
            task_models[key] = val if val else "inherit"
    intervention_rules = dict(_DEFAULT["intervention_rules"])
    raw_rules = src.get("intervention_rules") or {}
    if isinstance(raw_rules, dict):
        for key in _INTERVENTION_RULE_KEYS:
            if key in raw_rules:
                intervention_rules[key] = bool(raw_rules[key])
    return {
        "default_model": str(src.get("default_model") or _DEFAULT["default_model"]),
        "temperature": _clamp_float(src.get("temperature"), low=0.0, high=1.5, default=0.7),
        "max_tokens": _clamp_int(src.get("max_tokens"), low=1000, high=32000, default=8000),
        "memory_rag_enabled": bool(src.get("memory_rag_enabled", True)),
        "memory_rag_top_k": _clamp_int(src.get("memory_rag_top_k"), low=1, high=20, default=8),
        "task_models": task_models,
        "companion_lightweight": bool(src.get("companion_lightweight", True)),
        "intervention_rules": intervention_rules,
    }


def load_creator_preferences(project_root: Path | str) -> dict[str, Any]:
    path = _prefs_path(project_root)
    if not path.is_file():
        return normalize_creator_preferences(None)
    data = json.loads(path.read_text(encoding="utf-8"))
    prefs = normalize_creator_preferences(data)
    prefs["updated_at"] = data.get("updated_at")
    return prefs


def save_creator_preferences(project_root: Path | str, payload: dict[str, Any]) -> dict[str, Any]:
    path = _prefs_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    prefs = normalize_creator_preferences(payload)
    out = {
        "schema_version": _STATE_VERSION,
        **prefs,
        "updated_at": _now_iso(),
    }
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def creator_preferences_payload(project) -> dict[str, Any]:
    prefs = load_creator_preferences(project.root)
    return {
        "slug": project.slug,
        **prefs,
    }
