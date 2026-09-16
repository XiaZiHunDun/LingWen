# Phase 92 — P2-EXTRACT-ENUM closure handoff

> **Date**: 2026-09-16
> **Branch**: master (direct commits per 2026-09-15 simplified workflow)
> **Version**: v55.1 → v55.2
> **Carryover source**: Phase 90 REQ-002 multimodal handoff §6 (deviation 1 of 5)

## 1. Goal

Close the cheapest Phase 90 carryover deviation: add `TaskType.STRUCTURED_EXTRACTION` to
the lingwen-shared enum so `lingwen-illustrations.prompt_builder.extract_scene` can declare
its true intent instead of using `QUALITY_ANALYSIS` as a semantic stand-in.

**Scope** (3 packages, 4 files):
- `packages/lingwen-shared/src/lingwen_shared/contracts/python/llm.py` — add enum member
- `packages/lingwen-llm-service/src/lingwen_llm_service/service.py` — add `TASK_CONFIGS` entry
- `packages/lingwen-illustrations/src/lingwen_illustrations/prompt_builder.py` — switch call-site
- `packages/lingwen-shared/tests/test_llm_dto.py` — add round-trip test

## 2. Deliverables

### Enum extension

`TaskType` (was 6 members) gains a 7th:

```python
# v55.2 Phase 92 P2-EXTRACT-ENUM closure
STRUCTURED_EXTRACTION = "structured_extraction"  # 结构化抽取
```

The new member is **semantically exact** for `extract_scene` (chapter scene schema-bounded
JSON output) — distinct from `QUALITY_ANALYSIS` (analytical prose review) and `REPAIR`
(text rewriting).

### TASK_CONFIGS entry

`LLMService.TASK_CONFIGS` (was 5 entries) gains:

```python
TaskType.STRUCTURED_EXTRACTION: {
    "max_tokens": 1500,
    "temperature": 0.3,
}
```

Choices:
- `max_tokens=1500` — a typical chapter scene JSON (`subject + scene + mood + characters_in_scene[]`)
  fits comfortably; lower than `QUALITY_ANALYSIS` (2000) because the schema is bounded.
- `temperature=0.3` — deterministic JSON; matches `WORLDVIEW_CHECK`/`CHARACTER_CHECK`/`REPAIR`
  pattern (analytical tasks need low variance, unlike `QUALITY_ANALYSIS` 0.5 which trades
  creativity in judgment-style prompts).

### Call-site switch

`extract_scene` in `prompt_builder.py:108`:

```diff
-        # TaskType.STRUCTURED_EXTRACTION doesn't exist in lingwen-shared;
-        # QUALITY_ANALYSIS is the closest semantic fit (analytical JSON
-        # output, not text repair). v2 follow-up: add STRUCTURED_EXTRACTION
-        # to TaskType enum in lingwen-shared. See BACKLOG "P2-EXTRACT-ENUM".
-        task = LLMTask(task_type=TaskType.QUALITY_ANALYSIS, prompt=prompt)
+        # v55.2 Phase 92 P2-EXTRACT-ENUM closure: STRUCTURED_EXTRACTION
+        # added to TaskType in lingwen-shared. Semantic fit is exact.
+        task = LLMTask(task_type=TaskType.STRUCTURED_EXTRACTION, prompt=prompt)
```

The 4-line "v2 follow-up" comment is replaced with a 2-line "what changed" comment.

## 3. Test additions

### Unit (lingwen-shared)

`test_llm_dto.py`:

- `test_task_type_values_match_infra_baseline` — extended assertion: STRUCTURED_EXTRACTION value.
- **NEW** `test_task_type_structured_extraction_round_trip` — constructs `LLMTask` with the new
  enum, asserts identity + value round-trip.

### Regression guards (test_phase90_illustrations.py)

- **G10a** `test_structured_extraction_enum_exists` — `TaskType.STRUCTURED_EXTRACTION` exists
  in lingwen-shared with correct value `"structured_extraction"`.
- **G10b** `test_extract_scene_uses_structured_extraction` — `inspect.getsource(extract_scene)`
  contains the new enum name and **does not** contain `QUALITY_ANALYSIS` anymore.
- **G10c** `test_llm_service_task_configs_includes_structured_extraction` — `TASK_CONFIGS`
  contains the new key, with both `max_tokens` and `temperature` present.

## 4. Validation

| Gate | Result |
|------|--------|
| pytest `packages/lingwen-shared/tests/` | 141/141 (incl. 7 in test_llm_dto) |
| pytest `packages/lingwen-illustrations/tests/` | 72/72 (incl. 9 prompt_builder) |
| pytest `packages/lingwen-llm-service/tests/` | 3/3 |
| pytest `tests/test_phase90_illustrations.py` | **20/20** (15 baseline + G8 + G9 + G10 a/b/c) |
| pytest `apps/studio_api/tests/` | 90/90 (unchanged) |
| ruff check on changed files | All introduced errors fixed (`--fix`); 1 pre-existing W292 in service.py + 1 pre-existing E741 in test_phase90:102 untouched |

`uv.lock` auto-synced `httpx` dep for `lingwen-illustrations` (was already declared in
`packages/lingwen-illustrations/pyproject.toml:10`, just never locked from the workspace
resolution cache). No code change required.

## 5. Files changed

```
packages/lingwen-shared/src/lingwen_shared/contracts/python/llm.py   | +6 -1
packages/lingwen-shared/tests/test_llm_dto.py                       | +14 -1
packages/lingwen-llm-service/src/lingwen_llm_service/service.py     | +8 -0
packages/lingwen-illustrations/src/lingwen_illustrations/prompt_builder.py | +6 -6
tests/test_phase90_illustrations.py                                 | +63 -0
collaboration/BACKLOG.md                                            | +3 -1 (P2-EXTRACT-ENUM row + recent change entry)
collaboration/CURRENT_STATUS.md                                     | +1 -0 (new row)
docs/superpowers/handoffs/2026-09-16-phase-92-extract-enum-handoff.md | NEW (this file)
uv.lock                                                            | +2 (auto httpx sync)
```

Total: ~100 LOC net (production +6 lines for STRUCTURED_EXTRACTION + 6 in TASK_CONFIGS + 4 in
call-site rewrite; tests +77; docs +4).

## 6. Lessons

### Lesson 1: Pre-existing ruff errors should NOT be touched

Ruff on changed files surfaced 6 errors:

```
W292  packages/lingwen-llm-service/src/lingwen_llm_service/service.py:282  (pre-existing — verified via `git stash`)
E741  tests/test_phase90_illustrations.py:102                              (pre-existing — loop var `l`)
F541  tests/test_phase90_illustrations.py:120                              (pre-existing — f-string without placeholders)
I001  tests/test_phase90_illustrations.py:136                              (pre-existing — import order)
W292  tests/test_phase90_illustrations.py:236                              (introduced by G10c — fixed)
I001  tests/test_phase90_illustrations.py:228                              (introduced by G10c — fixed)
```

`git stash` + re-run ruff confirmed the first 4 (including W292 in service.py — same
trailing-newline issue existed before Phase 92 touched service.py line ~64). Only the 2
ruff errors I introduced in `G10c` were fixed via `--fix`.

**Rule for future phases**: ruff is a sanity check, not a cleanup tool. Touching
pre-existing errors muddies blame history and risks regression in unrelated areas.

### Lesson 2: `uv.lock` auto-syncs on `.venv/bin/python` runs

Running `.venv/bin/python -m pytest ...` after the Phase 91 commit triggered `uv sync`
which re-resolved workspace deps. The lockfile gained `httpx` for `lingwen-illustrations`
because `packages/lingwen-illustrations/pyproject.toml:10` already declared it but the
lockfile was stale from a prior install.

**Heuristic**: after any phase that touches `pyproject.toml` (workspace member deps) on a
fresh worktree / new commit, expect `uv.lock` to drift. The drift is benign — commit
the diff to keep reproducible installs.

### Lesson 3: Multi-package pytest combined run fails on rootdir conflict (3rd recurrence)

Combined command:
```bash
.venv/bin/python -m pytest packages/lingwen-shared/tests/ tests/test_phase90_illustrations.py packages/lingwen-illustrations/tests/ packages/lingwen-llm-service/tests/ -v
```
fails with:
```
ERROR packages/lingwen-illustrations/tests/test_bible_loader.py
ERROR packages/lingwen-illustrations/tests/test_exceptions.py
...
9 errors during collection
```

Root cause: pytest sees `tests/` (root) + `packages/lingwen-illustrations/tests/` and
namespace-collision on `tests/__init__.py` imports + missing rootdir config.

**Fix**: run each package's tests separately (Phase 89 lesson 5 was the 2nd recurrence).
Combined commands work only when all test paths share the same rootdir (e.g., only
`packages/X/tests/` or only `tests/`).

## 7. Carryover status

| Item | Status |
|------|--------|
| P2-EXTRACT-ENUM | ✅ **CLOSED** (this phase) |
| image_generator b64_json real-API decoding | OPEN — deferred to REQ-002 v2 |
| regenerate non-atomic (DELETE+POST → PUT atomic swap) | OPEN — deferred to REQ-002 v2 |
| ProjectSettingsPage doesn't exist (use global SettingsPage) | OPEN — deferred to REQ-002 v2 |

**Phase 90 carryover**: was 5 → now **3 remaining** (all REQ-002 v2 candidates).

## 8. Next-step candidates (per BACKLOG + v55.2 handoff)

1. **REQ-002 v2 sub-projects** — image provider adapters / reference image i2i / LRU archive
   / notification center. Each is a separate multi-week phase. Recommend starting with
   **image provider adapters** (most isolates, highest decoupling).
2. **REQ-004 团队协作 (P4 brainstorm)** — requires design exploration first; no immediate
   implementation hook.

Neither is blocking. Phase 92 is the cleanest "low-cost carryover" closure in the
Phase 90-92 series (Phase 90: 34 commits; Phase 91: 7 commits; Phase 92: 4 commits).