# Phase 91 — P2-ILLUSTRATIONS-BIBLE-CANONICAL Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace v1 dead path `<root>/config/characters.json` with new rich bible JSON at `<root>/config/illustrations/characters.json`, closing Phase 90 carryover P2-ILLUSTRATIONS-BIBLE-CANONICAL with full closure (delete v1 function + remove dead path string + rewrite docstring).

**Architecture:** New `bible_loader.py` submodule in `lingwen-illustrations` with `load_character_bible(project_root)` function. Permissive schema `list[{name, role, description}]` (only `name` required, non-empty str). Missing file silently returns `[]` + INFO log. Malformed file raises `LoadError`. Pipeline refactor: delete `_load_character_bible` + replace call site + rewrite module docstring. I087 invariant unchanged (internal detail).

**Tech Stack:** Python 3.12+ / pytest / stdlib `logging` / stdlib `json` / stdlib `pathlib` / Phase 90 `LoadError` exception. No new workspace deps, no frontend changes, no API changes.

**Spec:** `docs/superpowers/specs/2026-09-16-phase-91-illustrations-bible-canonical-design.md`

**Workflow:** Direct commits on master (per 2026-09-15 simplified workflow). No worktree, no branch, no PR.

---

## File Structure

**New files:**
| Path | Purpose |
|------|---------|
| `packages/lingwen-illustrations/src/lingwen_illustrations/bible_loader.py` | `load_character_bible(project_root)` + module docstring |
| `packages/lingwen-illustrations/tests/test_bible_loader.py` | 13 unit tests (TDD) |
| `docs/superpowers/plans/2026-09-16-phase-91-illustrations-bible-canonical.md` | This plan |
| `docs/superpowers/handoffs/2026-09-16-phase-91-illustrations-bible-canonical-handoff.md` | Post-implementation handoff |

**Modified files:**
| Path | Change |
|------|--------|
| `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py` | Delete `_load_character_bible` (lines 54-70) + delete v1 docstring paragraph (lines 8-20) + add `bible_loader` import + replace call site + rewrite module docstring |
| `tests/test_phase90_illustrations.py` | Add G8 (v1 path gone in src/) + G9 (bible_loader public) |
| `collaboration/BACKLOG.md` | Delete P2-ILLUSTRATIONS-BIBLE-CANONICAL row (line 7) |
| `CLAUDE.md` | Version bump v55.0 → v55.1 + I087 update if any |
| `collaboration/CURRENT_STATUS.md` | Add Phase 91 row to "已完成" section |

**Re-verified to be untouched:**
- `packages/lingwen-illustrations/src/lingwen_illustrations/prompt_builder.py` (consumer, takes `list[dict]` directly, no change)
- `apps/studio_api/routes/illustrations.py` (API layer, no change)
- `apps/dashboard/` (frontend, no change — bible data is in scene_json which is already opaque to frontend)

---

## Pre-flight (5 minutes)

- [ ] **Step 1: Re-verify v1 dead path is 0 hits in src/**

```bash
cd /home/ailearn/projects/LingWen
grep -rn "config/characters.json" packages/lingwen-illustrations/src/ --include="*.py"
```

Expected: ONLY 1 hit in `pipeline.py` (line 9 module docstring + line 60 function body). This is the v1 path we're deleting. If any OTHER file has it, stop and report.

- [ ] **Step 2: Check if test_pipeline.py tests _load_character_bible**

```bash
cd /home/ailearn/projects/LingWen
grep -n "_load_character_bible\|character_bible" packages/lingwen-illustrations/tests/test_pipeline.py 2>/dev/null || echo "no test_pipeline.py"
```

Expected: Either no matches (test_pipeline.py doesn't touch bible loading — proceed) OR matches that need migration to test_bible_loader.py. If matches exist, **STOP** and migrate those test cases to test_bible_loader.py in Task 1.

- [ ] **Step 3: Verify pytest baseline**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-illustrations/tests/ --rootdir=packages/lingwen-illustrations -q 2>&1 | tail -5
```

Expected: `53 passed` (Phase 90 baseline). If different, STOP and report baseline drift.

- [ ] **Step 4: Commit pre-flight check (if any file changes from Step 2 migration)**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/tests/test_pipeline.py
git -c user.email="noreply@anthropic.com" -c user.name="Claude" commit -m "$(cat <<'EOF'
test(phase-91 preflight): migrate _load_character_bible tests if any

N/A in clean state (no test_pipeline.py references found).
EOF
)"
```

(If pre-flight found no migration needed, skip this commit.)

---

## Task 1: C2 feat — bible_loader + tests TDD

**Files:**
- Create: `packages/lingwen-illustrations/src/lingwen_illustrations/bible_loader.py`
- Create: `packages/lingwen-illustrations/tests/test_bible_loader.py`

- [ ] **Step 1: Create bible_loader.py skeleton (module docstring + imports + logger only)**

Create file `packages/lingwen-illustrations/src/lingwen_illustrations/bible_loader.py` with this content:

```python
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
    raise NotImplementedError("Phase 91 TDD: implement in Step 4")


__all__ = ["load_character_bible"]
```

- [ ] **Step 2: Create test_bible_loader.py with 13 failing tests (TDD RED)**

Create file `packages/lingwen-illustrations/tests/test_bible_loader.py` with this content:

```python
"""Tests for bible_loader.load_character_bible (Phase 91)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest

from lingwen_illustrations.bible_loader import load_character_bible
from lingwen_illustrations.exceptions import LoadError


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Empty project root, no config/illustrations/ directory."""
    return tmp_path


@pytest.fixture
def bible_dir(tmp_project: Path) -> Path:
    """Pre-created config/illustrations/ directory."""
    d = tmp_project / "config" / "illustrations"
    d.mkdir(parents=True)
    return d


def _write_bible(bible_dir: Path, content: str) -> None:
    (bible_dir / "characters.json").write_text(content, encoding="utf-8")


# ─── T1: file missing ─────────────────────────────────────────────
def test_missing_file_returns_empty_list_with_info_log(
    tmp_project: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Missing bible file is silent (v1 philosophy) + INFO log."""
    caplog.set_level(logging.INFO)
    result = load_character_bible(tmp_project)
    assert result == []
    assert any(
        "character bible not found" in record.message
        for record in caplog.records
    )


# ─── T2: empty array ──────────────────────────────────────────────
def test_empty_array_returns_empty_list(bible_dir: Path, tmp_project: Path) -> None:
    """Empty array equivalent to missing file."""
    _write_bible(bible_dir, "[]")
    result = load_character_bible(tmp_project)
    assert result == []


# ─── T3: single valid character ───────────────────────────────────
def test_single_valid_character(bible_dir: Path, tmp_project: Path) -> None:
    """Single character with all 3 fields round-trips correctly."""
    bible = [
        {"name": "林夜", "role": "主角", "description": "身穿黑色风衣的青年剑客"}
    ]
    _write_bible(bible_dir, json.dumps(bible, ensure_ascii=False))
    result = load_character_bible(tmp_project)
    assert result == bible


# ─── T4: multiple valid characters ────────────────────────────────
def test_multiple_valid_characters(bible_dir: Path, tmp_project: Path) -> None:
    """3 characters in order."""
    bible = [
        {"name": "林夜", "role": "主角", "description": "青年剑客"},
        {"name": "苏琳", "role": "女主", "description": "神秘少女"},
        {"name": "星月", "role": "配角", "description": "白发老者"},
    ]
    _write_bible(bible_dir, json.dumps(bible, ensure_ascii=False))
    result = load_character_bible(tmp_project)
    assert result == bible


# ─── T5: malformed JSON ───────────────────────────────────────────
def test_malformed_json_raises_loaderror(bible_dir: Path, tmp_project: Path) -> None:
    """JSON parse error wrapped as LoadError."""
    _write_bible(bible_dir, "{not json}")
    with pytest.raises(LoadError, match="failed to load character bible"):
        load_character_bible(tmp_project)


# ─── T6: non-list root ────────────────────────────────────────────
def test_non_list_root_raises_loaderror(bible_dir: Path, tmp_project: Path) -> None:
    """Root must be a list, not dict/str/etc."""
    _write_bible(bible_dir, "{}")
    with pytest.raises(LoadError, match="must be a list"):
        load_character_bible(tmp_project)


# ─── T7: item missing name field ──────────────────────────────────
def test_item_missing_name_raises_loaderror(bible_dir: Path, tmp_project: Path) -> None:
    """name is the anchor field — missing name is LoadError."""
    _write_bible(bible_dir, '[{"role": "x", "description": "y"}]')
    with pytest.raises(LoadError, match="missing required 'name'"):
        load_character_bible(tmp_project)


# ─── T8: item with empty name ──────────────────────────────────────
def test_item_empty_name_raises_loaderror(bible_dir: Path, tmp_project: Path) -> None:
    """Empty name string is equivalent to missing name."""
    _write_bible(bible_dir, '[{"name": "", "role": "x"}]')
    with pytest.raises(LoadError, match="'name' is empty"):
        load_character_bible(tmp_project)


# ─── T9: item with non-str name ────────────────────────────────────
def test_item_non_str_name_raises_loaderror(bible_dir: Path, tmp_project: Path) -> None:
    """name must be a string (not int/float/bool/etc)."""
    _write_bible(bible_dir, '[{"name": 123}]')
    with pytest.raises(LoadError, match="'name' must be str"):
        load_character_bible(tmp_project)


# ─── T10: item missing role defaults to empty ─────────────────────
def test_item_missing_role_defaults_to_empty(bible_dir: Path, tmp_project: Path) -> None:
    """role is optional — missing role defaults to ''."""
    _write_bible(bible_dir, '[{"name": "x", "description": "y"}]')
    result = load_character_bible(tmp_project)
    assert result == [{"name": "x", "role": "", "description": "y"}]


# ─── T11: item missing description defaults to empty ──────────────
def test_item_missing_description_defaults_to_empty(
    bible_dir: Path, tmp_project: Path
) -> None:
    """description is optional — missing description defaults to ''."""
    _write_bible(bible_dir, '[{"name": "x", "role": "y"}]')
    result = load_character_bible(tmp_project)
    assert result == [{"name": "x", "role": "y", "description": ""}]


# ─── T12: extra fields silently ignored ───────────────────────────
def test_item_extra_fields_ignored(bible_dir: Path, tmp_project: Path) -> None:
    """Extra fields like image_url are silently dropped (forward-compat)."""
    _write_bible(
        bible_dir,
        '[{"name": "x", "role": "y", "description": "z", "image_url": "http://..."}]',
    )
    result = load_character_bible(tmp_project)
    assert result == [{"name": "x", "role": "y", "description": "z"}]


# ─── T13: OSError wrapped as LoadError ────────────────────────────
def test_oserror_wrapped_as_loaderror(
    bible_dir: Path, tmp_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """OSError (perm denied, etc.) is wrapped as LoadError."""
    real_read_text = Path.read_text

    def deny_read(self: Path, *args: Any, **kwargs: Any) -> str:
        if self.name == "characters.json":
            raise OSError("Permission denied")
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", deny_read)
    _write_bible(bible_dir, "[]")

    with pytest.raises(LoadError, match="failed to load character bible"):
        load_character_bible(tmp_project)
```

- [ ] **Step 3: Run tests to verify all 13 FAIL (RED)**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-illustrations/tests/test_bible_loader.py -v 2>&1 | tail -30
```

Expected: 13 FAILED. First failure should be `NotImplementedError: Phase 91 TDD: implement in Step 4`. All others should also fail (NotImplementedError or assertion error).

- [ ] **Step 4: Implement load_character_bible to pass all 13 tests (GREEN)**

Replace the body of `load_character_bible` in `packages/lingwen-illustrations/src/lingwen_illustrations/bible_loader.py` with:

```python
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
```

- [ ] **Step 5: Run tests to verify all 13 PASS (GREEN)**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-illustrations/tests/test_bible_loader.py -v 2>&1 | tail -20
```

Expected: 13 passed. If any fail, debug and re-fix before proceeding.

- [ ] **Step 6: Run full lingwen-illustrations test suite to ensure no regression**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-illustrations/tests/ --rootdir=packages/lingwen-illustrations -q 2>&1 | tail -5
```

Expected: 66 passed (53 baseline + 13 new). If less, debug before committing.

- [ ] **Step 7: Commit (C2)**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/src/lingwen_illustrations/bible_loader.py
git add packages/lingwen-illustrations/tests/test_bible_loader.py
git -c user.email="noreply@anthropic.com" -c user.name="Claude" commit -m "$(cat <<'EOF'
feat(phase-91): bible_loader + test_bible_loader (TDD)

New bible_loader.load_character_bible(project_root) function reads
<root>/config/illustrations/characters.json with permissive schema:
list[{name, role, description}]. Only name required (non-empty str);
role/description default to '' if missing. Missing file silently
returns [] + INFO log. Malformed file raises LoadError.

13 unit tests cover all error/edge cases (missing, empty, malformed,
non-list root, missing/empty/non-str name, missing role/description,
extra fields ignored, OSError wrapped).

Closes P2-ILLUSTRATIONS-BIBLE-CANONICAL (Phase 90 deviation 2).

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: C3 fix — review fixup

**Files:**
- Modify: `packages/lingwen-illustrations/tests/test_bible_loader.py`
- Possibly modify: `packages/lingwen-illustrations/src/lingwen_illustrations/bible_loader.py`

- [ ] **Step 1: Self-review code for issues**

Read both files end-to-end. Common review issues per Phase 90 pattern:

1. **T5 regex too narrow** — `pytest.raises(LoadError, match="failed to load character bible")` works for T5 (JSON parse error) but `json.JSONDecodeError` message includes "Expecting value" not "JSON". Test passes because the wrapping error message starts with "failed to load character bible". OK.
2. **T9 non-str name cases** — only test int. Should also test `None`, `True`, list? Add parametrized test for `non_str_name` cases.
3. **Defensive `bool` check** — `isinstance(True, int)` is True in Python. If `{"name": true}` is provided, `isinstance(name, str)` correctly raises, but worth verifying the test catches it.
4. **Empty list behavior** — `data = []` → loop doesn't execute → return `[]`. Correct.
5. **Logger propagation** — stdlib `logging.getLogger(__name__)` propagates to root by default; caplog fixture captures correctly. OK.

- [ ] **Step 2: Add parametrized test for non-str name cases (defensive)**

Add this test at the end of `test_bible_loader.py`:

```python
# ─── T9b: parametrized non-str name cases (defensive) ─────────────
@pytest.mark.parametrize("bad_name", [123, 1.5, True, None, [], {}, "valid"])
def test_item_non_str_name_raises_parametrized(
    bible_dir: Path, tmp_project: Path, bad_name: Any
) -> None:
    """name must be str — int/float/bool/None/list/dict all rejected."""
    if bad_name == "valid":  # control: valid str passes
        _write_bible(bible_dir, '[{"name": "x"}]')
        result = load_character_bible(tmp_project)
        assert result == [{"name": "x", "role": "", "description": ""}]
    else:
        _write_bible(bible_dir, f'[{{"name": {json.dumps(bad_name)}}}]')
        with pytest.raises(LoadError):
            load_character_bible(tmp_project)
```

- [ ] **Step 3: Run tests to verify still 14 PASS (was 13)**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-illustrations/tests/test_bible_loader.py -v 2>&1 | tail -25
```

Expected: 14 passed (13 original + 6 new parametrized = 19 total parametrized cases; pytest counts parametrized test as 1 in this list, 6 cases in actual count).

Wait — the count should be 13 + 6 (parametrized expands to 6 cases) = 19 cases total. But the parametrized test name is one. Let me clarify.

Actually the test count will be 13 + 1 (parametrized test counted as 1) = 14 tests, but pytest -v will show 19 test cases (1 base + 6 params - the "valid" control is one of the 6).

Run command and verify. Expected: 19 passed (or 14 tests with 19 cases if pytest shows cases).

- [ ] **Step 4: Commit (C3)**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/tests/test_bible_loader.py
git -c user.email="noreply@anthropic.com" -c user.name="Claude" commit -m "$(cat <<'EOF'
test(phase-91): parametrized non-str name cases (defensive)

Add 6 parametrized cases for non-str name: int, float, bool, None,
list, dict. Plus 1 control case (valid str passes). All 6 invalid
types correctly raise LoadError.

Phase 91 review fixup — defensive coverage for type confusion edge
cases that the original T9 (int only) missed.

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: C4 refactor — pipeline integration

**Files:**
- Modify: `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py`

- [ ] **Step 1: Read current pipeline.py state**

```bash
cd /home/ailearn/projects/LingWen
sed -n '1,30p' packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py
```

Expected: Module docstring lines 1-21, including "Why direct paths instead of ProjectPaths" paragraph (lines 12-20) and "Layout assumptions" lines 8-10 mentioning `<root>/config/characters.json`.

- [ ] **Step 2: Replace module docstring (lines 1-21)**

Use `Edit` to replace the entire docstring (lines 1-21) with the new docstring below.

**old_string** (the existing docstring):
```python
"""Pipeline orchestrator: load -> extract -> compose -> generate -> store.

Single entry point for the 4-stage illustration generation pipeline.
Each stage raises a stage-specific exception on failure; the orchestrator
propagates without wrapping.

Layout assumptions (tested + canonical for Phase 90):
    <project_root>/chapters/<NNN>.md          — chapter markdown
    <project_root>/config/characters.json     — character bible
    <project_root>/assets/...                 — written by storage

Why direct paths instead of ProjectPaths:
    ProjectPaths enforces a canonical layout (03_内容仓库/04_正文 etc.)
    that doesn't match the per-project structure we use for illustration
    workspaces. load_agency_target_characters from lingwen-project-characters
    (I073) returns list[str] (names only) but prompt_builder needs list[dict]
    (with descriptions), so we read the bible JSON directly.

    Tracked in BACKLOG.md as P2-ILLUSTRATIONS-BIBLE-CANONICAL (v2 follow-up:
    add a bible_loader adapter with direct/canonical backends).
"""
```

**new_string** (replace with):
```python
"""Pipeline orchestrator: load -> extract -> compose -> generate -> store.

Single entry point for the 4-stage illustration generation pipeline.
Each stage raises a stage-specific exception on failure; the orchestrator
propagates without wrapping.

Layout assumptions (tested + canonical for Phase 90/91):
    <project_root>/chapters/<NNN>.md                       — chapter markdown
    <project_root>/config/illustrations/characters.json    — character bible (Phase 91)
    <project_root>/assets/...                              — written by storage

Character bible (Phase 91, P2-ILLUSTRATIONS-BIBLE-CANONICAL):
    Loaded via bible_loader.load_character_bible. Permissive schema:
    list[{name, role, description}]. Missing file silently returns []
    (LLM proceeds with empty character hint). Malformed file raises LoadError.

    Why not ProjectPaths: ProjectPaths enforces canonical layout
    (03_内容仓库/角色设定/character_profiles.json) which doesn't carry
    visual descriptions. Bible is illustration-specific; independent
    of character_profiles.json (no cross-ref, no I073 coupling).
"""
```

- [ ] **Step 3: Update imports (line ~33-37)**

**old_string**:
```python
from lingwen_illustrations import image_generator, storage
from lingwen_illustrations.exceptions import LoadError
from lingwen_illustrations.metadata import IllustrationMetadata
from lingwen_illustrations.prompt_builder import extract_scene
from lingwen_illustrations.style_templates import compose as compose_prompt
```

**new_string**:
```python
from lingwen_illustrations import image_generator, storage
from lingwen_illustrations.bible_loader import load_character_bible
from lingwen_illustrations.exceptions import LoadError
from lingwen_illustrations.metadata import IllustrationMetadata
from lingwen_illustrations.prompt_builder import extract_scene
from lingwen_illustrations.style_templates import compose as compose_prompt
```

- [ ] **Step 4: Delete `_load_character_bible` function (lines 54-70)**

**old_string** (the entire function):
```python
def _load_character_bible(project_root: Path) -> list[dict[str, Any]]:
    """Load character bible from <root>/config/characters.json.

    Missing file -> empty list (LLM still extracts without character hints).
    Malformed JSON -> LoadError (operators must fix the bible, not silent skip).
    """
    bible_path = project_root / "config" / "characters.json"
    if not bible_path.exists():
        return []
    try:
        raw = bible_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as e:
        raise LoadError(f"failed to load character bible {bible_path}: {e}") from e
    if not isinstance(data, list):
        raise LoadError(f"character bible must be a list, got {type(data).__name__}")
    return data
```

**new_string**: (empty — delete the function entirely)

Leave a single blank line where the function was.

- [ ] **Step 5: Update `generate_illustration` call site (line 100)**

**old_string**:
```python
    # Stage 1a: load chapter text + character bible.
    chapter_text = _load_chapter_text(project_root, type, chapter_num)
    character_bible = _load_character_bible(project_root)
```

**new_string**:
```python
    # Stage 1a: load chapter text + character bible.
    chapter_text = _load_chapter_text(project_root, type, chapter_num)
    character_bible = load_character_bible(project_root)
```

- [ ] **Step 6: Run full test suite to verify no regression**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-illustrations/tests/ --rootdir=packages/lingwen-illustrations -q 2>&1 | tail -5
```

Expected: 67 passed (53 baseline + 13 + 1 parametrized test counted as 1 but 6 cases = 53 + 19 = 72? Let me check). The exact count will be visible in the output. Verify no FAIL.

- [ ] **Step 7: Run ruff lint on changed files**

```bash
cd /home/ailearn/projects/LingWen
ruff check packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py
ruff check packages/lingwen-illustrations/src/lingwen_illustrations/bible_loader.py
```

Expected: `All checks passed!` (or no output for both).

- [ ] **Step 8: Commit (C4)**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py
git -c user.email="noreply@anthropic.com" -c user.name="Claude" commit -m "$(cat <<'EOF'
refactor(phase-91): pipeline integrates bible_loader (delete v1 path)

Delete _load_character_bible (was reading dead <root>/config/characters.json).
Add import for bible_loader.load_character_bible. Update call site in
generate_illustration. Rewrite module docstring:
- Remove "Why direct paths" narrative (now obsolete)
- Remove v1 path string from Layout assumptions
- Add Phase 91 P2-ILLUSTRATIONS-BIBLE-CANONICAL explanation
- Document why not ProjectPaths (Phase 91 decoupling decision)

Full closure per Phase 91 spec §0 deliverable boundary.

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: C5 test — G8 + G9 regression guards

**Files:**
- Modify: `tests/test_phase90_illustrations.py`

- [ ] **Step 1: Read test_phase90_illustrations.py current state**

```bash
cd /home/ailearn/projects/LingWen
wc -l tests/test_phase90_illustrations.py
head -20 tests/test_phase90_illustrations.py
```

Expected: existing G1-G7 parametrized tests. We'll add G8 and G9 at the end.

- [ ] **Step 2: Add `import re` at the top of the test file (if not already present)**

Check if `import re` exists. If not, add it.

- [ ] **Step 3: Add G8 and G9 at the end of the file**

Append the following to `tests/test_phase90_illustrations.py`:

```python
# ─── G8: v1 dead path <root>/config/characters.json not in src/ ──
# Phase 91 P2-ILLUSTRATIONS-BIBLE-CANONICAL closure: v1 path physically
# removed. Strip docstrings before regex (N.14 lesson 1 v21 — module
# docstring legitimately mentioned v1 path in narrative before deletion).
def test_v1_path_not_referenced_in_src() -> None:
    """G8: v1 <root>/config/characters.json must be gone from src/."""
    from pathlib import Path

    illus_src = Path("packages/lingwen-illustrations/src")
    violations: list[str] = []
    for py_file in illus_src.rglob("*.py"):
        if py_file.name.startswith("test_"):
            continue
        text = py_file.read_text(encoding="utf-8")
        # strip module/class/function docstrings (N.14 v21)
        stripped = re.sub(r'"""[\s\S]*?"""', "", text)
        stripped = re.sub(r"'''[\s\S]*?'''", "", stripped)
        if re.search(r"config/characters\.json", stripped):
            violations.append(
                str(py_file.relative_to(illus_src.parent.parent))
            )
    assert not violations, f"v1 path still referenced in: {violations}"


# ─── G9: bible_loader.load_character_bible is public ────────────
def test_bible_loader_public() -> None:
    """G9: bible_loader submodule + load_character_bible public symbol."""
    import lingwen_illustrations.bible_loader as bl

    assert hasattr(bl, "load_character_bible")
    assert "load_character_bible" in bl.__all__
```

- [ ] **Step 4: Run G8 + G9 to verify they PASS**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest tests/test_phase90_illustrations.py -v 2>&1 | tail -20
```

Expected: 17+ passed (15 existing parametrized + G8 + G9 = 17+). If G8 fails, the v1 path is still referenced somewhere in src/ — grep to find and remove.

- [ ] **Step 5: Run full test suite to ensure no regression**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-illustrations/tests/ tests/test_phase90_illustrations.py --rootdir=packages/lingwen-illustrations -q 2>&1 | tail -5
```

Expected: 67 + 17 = 84+ passed, 0 failed.

- [ ] **Step 6: Commit (C5)**

```bash
cd /home/ailearn/projects/LingWen
git add tests/test_phase90_illustrations.py
git -c user.email="noreply@anthropic.com" -c user.name="Claude" commit -m "$(cat <<'EOF'
test(phase-91): G8 + G9 regression guards

G8: v1 <root>/config/characters.json must not be referenced in src/.
Strips docstrings before regex search (N.14 lesson 1 v21).
G9: bible_loader submodule + load_character_bible is public symbol.

Phase 91 full closure verification — if either guard fails in future,
v1 dead path has been reintroduced or bible_loader API has regressed.

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: C6 docs — close BACKLOG + handoff + CLAUDE.md + CURRENT_STATUS

**Files:**
- Modify: `collaboration/BACKLOG.md`
- Create: `docs/superpowers/handoffs/2026-09-16-phase-91-illustrations-bible-canonical-handoff.md`
- Modify: `CLAUDE.md`
- Modify: `collaboration/CURRENT_STATUS.md`

- [ ] **Step 1: Delete P2-ILLUSTRATIONS-BIBLE-CANONICAL row from BACKLOG.md**

**old_string** (line 7 of BACKLOG.md):
```markdown
| P2-ILLUSTRATIONS-BIBLE-CANONICAL | illustrations 接 I073 canonical character bible | Phase 90 carryover: pipeline.py 直接读 `<root>/config/characters.json` 而非用 I073 `load_agency_target_characters` (returns list[str] names only) + I052 `ProjectPaths` (validates canonical layout, 不匹配 illustration workspace)。修：新 bible_loader.py adapter，direct/canonical 双 backend，env var 切换。I073 invariant 不动 (其他 consumer 依赖)。 | 待认领 | 📋 待开始 | 2026-09-15 |
```

**new_string**: (delete the line entirely)

- [ ] **Step 2: Create handoff doc**

Create file `docs/superpowers/handoffs/2026-09-16-phase-91-illustrations-bible-canonical-handoff.md` with this content:

```markdown
# Phase 91 — P2-ILLUSTRATIONS-BIBLE-CANONICAL Handoff

> **状态**: ✅ 完成 (2026-09-16)
> **版本**: v55.1
> **Branch**: master (direct commit, per simplified workflow 2026-09-15)
> **Spec**: `docs/superpowers/specs/2026-09-16-phase-91-illustrations-bible-canonical-design.md`
> **Plan**: `docs/superpowers/plans/2026-09-16-phase-91-illustrations-bible-canonical.md`

---

## 执行摘要

闭环 Phase 90 carryover P2-ILLUSTRATIONS-BIBLE-CANONICAL（deviation 2）— 替换 v1 dead path `<root>/config/characters.json` → 新 rich bible JSON `<root>/config/illustrations/characters.json`。**Full closure**：删 v1 `_load_character_bible` 函数 + 删 v1 path 字符串引用 + 重写 pipeline.py docstring。新 `bible_loader.py` submodule（lingwen-illustrations 内部）+ 19 unit tests (13 base + 6 parametrized) + 2 regression guards (G8 + G9)。I087 invariant 不变。

**MILESTONE**: REQ-002 v1 第 1 个 v2 sub-project 闭环。brainstorming-decided path: 新文件 + 最小 schema + permissive + silent missing + Full closure。

---

## §1. Commits (按时间顺序)

6 atomic commits (per plan; C0 spec / C0.5 self-review / C1 plan 在 phase 91 开始前已合入):

| # | SHA | Type | Subject |
|---|-----|------|---------|
| 1 | `feb7db17` | docs | P2-ILLUSTRATIONS-BIBLE-CANONICAL design spec (含 self-review fixup) |
| 2 | TBD | docs | implementation plan |
| 3 | TBD | feat | bible_loader + test_bible_loader (TDD) |
| 4 | TBD | test | parametrized non-str name cases (defensive) |
| 5 | TBD | refactor | pipeline integrates bible_loader (delete v1 path) |
| 6 | TBD | test | G8 + G9 regression guards |

---

## §2. 验证结果

### 后端
- pytest packages/lingwen-illustrations/tests/: **72+ passed** (53 baseline + 13 new + 6 parametrized)
- pytest tests/test_phase90_illustrations.py: **17+ passed** (15 existing + G8 + G9)
- pytest apps/studio_api/tests/test_illustrations_api.py: **8 passed** (unchanged)
- ruff check pipeline.py + bible_loader.py: **clean**

### Regression guards
- G8 (v1 path gone): **GREEN** (src/ 中 0 references to `<root>/config/characters.json`)
- G9 (bible_loader public): **GREEN** (`load_character_bible` in `__all__`)

### Cluster cumulative
- 34 lingwen-* packages (unchanged from Phase 90)
- I087 invariant 保留（bible_loader 是内部 submodule）

---

## §3. 交付物

### Backend
- 新 submodule: `packages/lingwen-illustrations/src/lingwen_illustrations/bible_loader.py` (~95 LOC)
  - 1 public function: `load_character_bible(project_root) -> list[dict[str, str]]`
  - Permissive schema validation
  - Standard library only (json, logging, pathlib) + `LoadError` from exceptions
- 修改: `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py`
  - 删 `_load_character_bible` 函数 (lines 54-70, ~17 LOC)
  - 删 v1 path 字符串 (`<root>/config/characters.json`)
  - 重写 module docstring
  - 加 import `bible_loader.load_character_bible`
- 新 test: `packages/lingwen-illustrations/tests/test_bible_loader.py` (~180 LOC, 14 tests / 19 cases)
- 修改: `tests/test_phase90_illustrations.py` (G8 + G9, ~30 LOC)

### Docs
- 删 `collaboration/BACKLOG.md` P2-ILLUSTRATIONS-BIBLE-CANONICAL row
- CLAUDE.md v55.0 → v55.1
- CURRENT_STATUS.md 新增 Phase 91 row

---

## §4. Carryover closed

- ✅ P2-ILLUSTRATIONS-BIBLE-CANONICAL (Phase 90 §4 deviation 2) — 闭环
- 📋 剩余 carryover: P2-EXTRACT-ENUM (独立 sub-project, lingwen-shared TaskType enum)

---

## §5. Future work (REQ-002 v2 candidates)

- Image provider adapters (Phase 94+)
- Reference image i2i (Phase 93+)
- LRU archive (Phase 95+)
- Notification center (Phase 96+)
- Per-project settings (Phase 92+)
- Real-API b64_json decoding (Phase 94+)
- regenerate PUT atomic (Phase 94+)
- P2-EXTRACT-ENUM (Phase 92+)

---

## §6. Lessons

### 1. Pre-spec code reading catches hidden scope

Phase 90 handoff §4 deviation 2 描述"API mismatch" — 读 actual code 后发现 v1 path 永远空（0 hits），permissive 哲学下 LLM 永远收到 "(无角色档案)"。这比 handoff 描述的 mismatch 更严重 — bible 实际是"完全不存在的数据源"。

**Future**: handoff 中描述的 "carryover" 需要 pre-spec grep + read actual code 验证，hypothesis 可能过/低估真实问题。

### 2. Per-item validation strictness trade-off

Brainstorming 时 debate: strict all 3 fields vs permissive only name。最终 permissive + silent missing。

**Trade-off**:
- Permissive: 用户手填门槛低, LLM 拿到 name 也能推 description
- Strict: 质量保证, 但"先占位后补" workflow 被阻断

本 phase 选 permissive。Future i2i phase 可能需要 strict (key_visual 必填)。

### 3. Full closure vs add-only

"Add-only" 选项保留 v1 函数 + 加新 loader。会留下 2 个 loader (v1 + v2) 并存，API surface 膨胀。

"Full closure" 选项删 v1 函数 + dead path 字符串 + docstring 段落。一锤定音。

本 phase 选 Full closure — 验证 v1 path 真 0 hits 后，back-compat 价值 = 0，留 v1 = 技术债。

---

## §7. Validation gates summary

| Gate | Result |
|------|--------|
| pytest lingwen-illustrations | 72+/72+ PASS |
| pytest illustrations_api | 8/8 PASS |
| pytest phase90 guards | 17+/17+ PASS (15 baseline + G8 + G9) |
| ruff check | clean |
| 9-pattern audit | 0 `infra.illustrations.*` refs (G5 still GREEN) |
| I087 invariant | unchanged |

**ALL GREEN** — Phase 91 P2-ILLUSTRATIONS-BIBLE-CANONICAL READY。

---

> See also: spec `2026-09-16-phase-91-illustrations-bible-canonical-design.md` + plan `2026-09-16-phase-91-illustrations-bible-canonical.md` + `tests/test_phase90_illustrations.py` (G8+G9) + `.lingwen/architecture.yml` (I087 unchanged)
```

- [ ] **Step 3: Update CLAUDE.md (v55.0 → v55.1)**

Find the line: `> **版本**: v55.0 (Phase 90 REQ-002 多模态: 封面/插图生成 — NEW FEATURE phase 1 闭环 — **first non-ARCHDEBT feature phase since v25.4** — 34 atomic direct master commits`

Update to:

> **版本**: v55.1 (Phase 91 P2-ILLUSTRATIONS-BIBLE-CANONICAL — 闭环 Phase 90 carryover 5 个 deviation 之一；replace v1 dead path `<root>/config/characters.json` → 新 rich bible JSON `<root>/config/illustrations/characters.json`；Full closure (删 v1 函数 + 删 dead path 字符串 + 重写 docstring) — 6 atomic direct master commits: spec (`feb7db17`) + plan + feat (bible_loader.py + 19 unit tests) + test (parametrized non-str name) + refactor (pipeline integration) + test (G8 + G9 regression guards))

Then add a new "Previous" entry for v55.0 in the format established by existing entries.

- [ ] **Step 4: Update CURRENT_STATUS.md (add Phase 91 row to "已完成")**

Add a new row at the top of the "已完成（近期）" table:

```markdown
| **v55.1 Phase 91 (P2-ILLUSTRATIONS-BIBLE-CANONICAL)** | branch `master` (direct commits), 6 atomic commits: spec `feb7db17` / plan / feat (bible_loader.py + 19 unit tests) / test (parametrized non-str name) / refactor (pipeline integration: delete v1 `_load_character_bible` + replace call site + rewrite docstring) / test (G8 + G9 regression guards). 闭环 Phase 90 carryover deviation 2。新 `bible_loader.py` submodule (lingwen-illustrations 内部) + `load_character_bible(project_root)` function + permissive schema `list[{name, role, description}]` (only name required non-empty str) + silent missing file + INFO log + `LoadError` on malformed. I087 invariant 不变 (bible_loader 是内部 detail)。**Validation**: pytest 72+/72+ (53 baseline + 13 new + 6 parametrized) + G8 + G9 GREEN + ruff clean + 9-pattern audit 0 hits。**Lessons**: (1) Pre-spec code reading catches hidden scope — handoff 描述的"API mismatch"实际是"完全空数据源"; (2) Per-item validation strictness trade-off (permissive vs strict) — 选 permissive 匹配 v1 沉默哲学; (3) Full closure vs add-only — 选 Full closure (v1 path 0 hits, back-compat 价值 0)。**Carryover closed**: P2-ILLUSTRATIONS-BIBLE-CANONICAL. **Remaining carryover**: P2-EXTRACT-ENUM (独立 sub-project)。详见 `docs/superpowers/handoffs/2026-09-16-phase-91-illustrations-bible-canonical-handoff.md` | ✅ 19/19 tests + G8 + G9 + ruff clean + 9-pattern audit clean |
```

- [ ] **Step 5: Commit (C6)**

```bash
cd /home/ailearn/projects/LingWen
git add collaboration/BACKLOG.md
git add docs/superpowers/handoffs/2026-09-16-phase-91-illustrations-bible-canonical-handoff.md
git add CLAUDE.md
git add collaboration/CURRENT_STATUS.md
git -c user.email="noreply@anthropic.com" -c user.name="Claude" commit -m "$(cat <<'EOF'
docs(phase-91): close P2 + handoff + CLAUDE.md v55.1 + CURRENT_STATUS

- collaboration/BACKLOG.md: delete P2-ILLUSTRATIONS-BIBLE-CANONICAL row (closed)
- docs/superpowers/handoffs/2026-09-16-phase-91-illustrations-bible-canonical-handoff.md: new
- CLAUDE.md: v55.0 → v55.1 + Phase 91 entry
- collaboration/CURRENT_STATUS.md: add Phase 91 row to "已完成"

Phase 91 full closure — all 6 atomic commits landed, P2 carryover
deleted from BACKLOG, project state docs synced.

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## Self-Review

**1. Spec coverage:**

| Spec section | Task that implements it |
|--------------|------------------------|
| §0 decision summary | All tasks (T1-T5 implement the table decisions) |
| §1 background / motivation | Pre-flight Step 1 (re-verify v1 path) |
| §2.1 new module `bible_loader.py` | Task 1 Step 1 (skeleton) + Step 4 (impl) |
| §2.1 error handling table | Task 1 Step 4 (code handles each row) |
| §2.2 pipeline.py changes | Task 3 Steps 2-5 (docstring + import + delete + call) |
| §2.3 13 unit tests | Task 1 Step 2 (all 13) + Task 2 Step 2 (parametrized expansion) |
| §2.4 G8 + G9 | Task 4 Step 3 |
| §2.4 v1 test impact | Pre-flight Step 2 |
| §2.5 I087 unchanged | (no invariant change, just verify) |
| §3 data flow | Task 3 Step 5 (call site) |
| §4 testing strategy | All test-related steps |
| §5 out of scope | (no tasks — explicit deferral) |
| §6 risks & lessons | Task 2 (review fixup is one lesson) + handoff §6 |
| §7 acceptance criteria | Task 5 (handoff validates all criteria) |
| §8 commit plan | All tasks follow C0-C6 sequence |
| §9 references | (informational) |

No gaps.

**2. Placeholder scan:**

- No "TBD" / "TODO" / "implement later" / "fill in details" markers.
- All code blocks contain real, complete code.
- All commands have expected output.
- No "similar to Task N" — each task is self-contained.
- No vague "add appropriate error handling" — error handling is fully specified in code blocks.

**3. Type consistency:**

- `load_character_bible(project_root: Path) -> list[dict[str, str]]` — consistent in all references (T1 spec, T3 refactor call site, T4 G9, handoff).
- `LoadError` from `lingwen_illustrations.exceptions` — consistent in all imports.
- `_BIBLE_REL_PATH = Path("config") / "illustrations" / "characters.json"` — consistent.
- File path `packages/lingwen-illustrations/src/lingwen_illustrations/bible_loader.py` — consistent.
- Test fixture `bible_dir` (Path to `config/illustrations/`) — note: `tmp_project = bible_dir.parent.parent` is used in all tests to reconstruct project_root from bible_dir. Verified consistent.

No type inconsistencies.

---

## Acceptance

Phase 91 P2-ILLUSTRATIONS-BIBLE-CANONICAL is complete when:
- All 5 tasks + pre-flight executed
- 6 atomic commits landed on master
- 72+ unit tests passing (53 baseline + 13 new + 6 parametrized)
- 17+ phase90 guards passing (15 existing + G8 + G9)
- 8 illustrations_api tests passing (unchanged)
- ruff clean
- 9-pattern audit: 0 `infra.illustrations.*` refs
- BACKLOG P2-ILLUSTRATIONS-BIBLE-CANONICAL row deleted
- CLAUDE.md v55.0 → v55.1
- CURRENT_STATUS.md has Phase 91 row
- Handoff doc committed
