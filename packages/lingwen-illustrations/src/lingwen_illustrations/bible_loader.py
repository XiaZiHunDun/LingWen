"""Bible loader: read <root>/config/illustrations/characters.json.

Phase 91 P2-ILLUSTRATIONS-BIBLE-CANONICAL: replaces v1 dead path
<root>/config/characters.json (which had 0 hits in real projects at
Phase 90 grep audit, so v1 always returned [] silently — LLM prompt
was perpetually "(无角色档案)").

Schema (permissive):
    list of {name: str, role: str, description: str}
    - name: required (non-empty str) — anchor field, used as key
    - role: optional (defaults to '') — cross-ref hint for LLM
    - description: optional (defaults to '') — primary visual cue
    - extra fields: silently ignored (forward-compat for v2+ schema)

Why NOT character_profiles.json (lingwen-project-characters / I073):
    I073 returns list[str] (names only) — does not carry visual descriptions.
    character_profiles.json schema lacks description field. Coupling would
    force schema migration of canonical file + I073 invariant expansion
    (8 other consumers depend on current list[str] shape).

Why NOT ProjectPaths (lingwen-paths / I052):
    ProjectPaths enforces canonical layout (03_内容仓库/角色设定/...) which
    is content-focused, not illustration-focused. Bible lives in
    config/illustrations/ (project-local, independent of canonical hierarchy).

Error contract (v1-compatible):
    - File missing → return [] + INFO log (silent, like v1)
    - Malformed JSON / non-list root → raise LoadError (operators must fix)
    - Item with missing/empty/non-str name → raise LoadError (anchor field)
    - Item with non-str role/description → raise LoadError (type defense)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from lingwen_illustrations.exceptions import LoadError

logger = logging.getLogger(__name__)

_BIBLE_REL_PATH = Path("config") / "illustrations" / "characters.json"


def load_character_bible(project_root: Path) -> list[dict[str, str]]:
    """Load character bible from <project_root>/config/illustrations/characters.json.

    Returns:
        Validated list of {name, role, description} dicts.
        Empty list if file is missing.

    Raises:
        LoadError: JSON parse error, non-list root, item type error,
            or item with missing/empty/non-str required name field,
            or non-str role/description.
    """
    bible_path = project_root / _BIBLE_REL_PATH
    if not bible_path.exists():
        logger.info("character bible not found at %s", bible_path)
        return []

    try:
        raw = bible_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as e:
        raise LoadError(
            f"failed to load character bible {bible_path}: {e}"
        ) from e

    if not isinstance(data, list):
        raise LoadError(
            f"character bible must be a list, got {type(data).__name__}"
        )

    result: list[dict[str, str]] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise LoadError(
                f"item {i} must be a dict, got {type(item).__name__}"
            )
        if "name" not in item:
            raise LoadError(f"item {i} missing required 'name' field")
        name = item["name"]
        if not isinstance(name, str):
            raise LoadError(
                f"item {i} 'name' must be str, got {type(name).__name__}"
            )
        if not name:
            raise LoadError(f"item {i} 'name' is empty")
        role = item.get("role", "")
        if not isinstance(role, str):
            raise LoadError(
                f"item {i} 'role' must be str, got {type(role).__name__}"
            )
        description = item.get("description", "")
        if not isinstance(description, str):
            raise LoadError(
                f"item {i} 'description' must be str, got {type(description).__name__}"
            )
        result.append({
            "name": name,
            "role": role,
            "description": description,
        })

    return result


__all__ = ["load_character_bible"]
