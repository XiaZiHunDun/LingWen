# Phase 92 — P2-EXTRACT-ENUM plan

> **Date**: 2026-09-16
> **Phase**: 92
> **Spec**: `docs/superpowers/specs/2026-09-16-phase-92-extract-enum-design.md`
> **Workflow**: 2026-09-15 simplified (solo, direct master commits)

## 1. Atomic commit sequence

Per solo workflow, this phase uses 4 atomic direct-master commits (per 2026-09-15 simplified
workflow — no worktree, no branch, no ff-merge):

| # | Commit | Subject | Files |
|---|--------|---------|-------|
| 1 | spec | `docs(phase-92): spec P2-EXTRACT-ENUM closure` | `docs/superpowers/specs/2026-09-16-phase-92-extract-enum-design.md` |
| 2 | plan | `docs(phase-92): plan P2-EXTRACT-ENUM closure` | `docs/superpowers/plans/2026-09-16-phase-92-extract-enum.md` |
| 3 | feat | `feat(phase-92): add STRUCTURED_EXTRACTION TaskType enum` | `packages/lingwen-shared/src/lingwen_shared/contracts/python/llm.py` |
| 4 | test | `test(phase-92): G10a enum exists + round-trip test` | `packages/lingwen-shared/tests/test_llm_dto.py`, `tests/test_phase90_illustrations.py` (G10a) |
| 5 | refactor | `refactor(phase-92): switch extract_scene to STRUCTURED_EXTRACTION + TASK_CONFIGS` | `packages/lingwen-llm-service/src/lingwen_llm_service/service.py`, `packages/lingwen-illustrations/src/lingwen_illustrations/prompt_builder.py`, `tests/test_phase90_illustrations.py` (G10b + G10c) |
| 6 | test | `test(phase-92): G10b/G10c regression guards` | (merged into refactor commit for atomicity) |
| 7 | docs | `docs(phase-92): BACKLOG + CURRENT_STATUS + CLAUDE.md v55.2 + handoff` | `collaboration/BACKLOG.md`, `collaboration/CURRENT_STATUS.md`, `CLAUDE.md`, `docs/superpowers/handoffs/2026-09-16-phase-92-extract-enum-handoff.md` |

Atomic commit #3 + #4 + #5 + #6 can be combined into a tighter 4-commit sequence (spec + plan
+ **feat+refactor combined** + test+docs combined) since this phase is small enough that
"atomic" granularity is per-concern (enum added + call-site switched + guards) not per-file.

**Final commit sequence (4 commits)**:

1. spec
3. plan
2. feat+test+refactor combined (the actual code change with G10 a/b/c + lingwen-shared test)
3. docs (BACKLOG + CURRENT_STATUS + CLAUDE.md + handoff)

## 2. Per-step code changes

### Commit 1 (spec): no code

Create `docs/superpowers/specs/2026-09-16-phase-92-extract-enum-design.md` (this file
already exists in `/docs`).

### Commit 2 (plan): no code

Create `docs/superpowers/plans/2026-09-16-phase-92-extract-enum.md` (this file).

### Commit 3 (feat+test+refactor): code change

`packages/lingwen-shared/src/lingwen_shared/contracts/python/llm.py`:

```diff
@@ class TaskType(Enum):
     WORLDVIEW_CHECK = "worldview_check"  # 世界观检测
     CHARACTER_CHECK = "character_check"  # 角色一致性检测
     LOGIC_CHECK = "logic_check"  # 逻辑矛盾检测
     AI_TRACE_CHECK = "ai_trace_check"  # AI痕迹检测
     QUALITY_ANALYSIS = "quality_analysis"  # 质量综合分析
     REPAIR = "repair"  # 修复任务
+    # v55.2 Phase 92 P2-EXTRACT-ENUM closure
+    STRUCTURED_EXTRACTION = "structured_extraction"  # 结构化抽取
```

`packages/lingwen-llm-service/src/lingwen_llm_service/service.py`:

```diff
@@ class LLMService:
         TaskType.REPAIR: {
             "max_tokens": 3000,
             "temperature": 0.3,
         },
+        TaskType.STRUCTURED_EXTRACTION: {
+            "max_tokens": 1500,
+            "temperature": 0.3,
+        },
     }
```

`packages/lingwen-illustrations/src/lingwen_illustrations/prompt_builder.py`:

```diff
@@ def extract_scene(...):
     try:
         service = get_llm_service()
-        # TaskType.STRUCTURED_EXTRACTION doesn't exist in lingwen-shared;
-        # QUALITY_ANALYSIS is the closest semantic fit (analytical JSON
-        # output, not text repair). v2 follow-up: add STRUCTURED_EXTRACTION
-        # to TaskType enum in lingwen-shared. See BACKLOG "P2-EXTRACT-ENUM".
-        task = LLMTask(task_type=TaskType.QUALITY_ANALYSIS, prompt=prompt)
+        # v55.2 Phase 92 P2-EXTRACT-ENUM closure
+        task = LLMTask(task_type=TaskType.STRUCTURED_EXTRACTION, prompt=prompt)
```

`packages/lingwen-shared/tests/test_llm_dto.py`:

```diff
@@ def test_task_type_values_match_infra_baseline() -> None:
     assert TaskType.REPAIR.value == "repair"
+    assert TaskType.STRUCTURED_EXTRACTION.value == "structured_extraction"
+
+
+def test_task_type_structured_extraction_round_trip() -> None:
+    task = LLMTask(task_type=TaskType.STRUCTURED_EXTRACTION, prompt='{"subject": "x"}')
+    assert task.task_type is TaskType.STRUCTURED_EXTRACTION
+    assert task.task_type.value == "structured_extraction"
```

`tests/test_phase90_illustrations.py` — append G10 a/b/c:

```python
def test_structured_extraction_enum_exists() -> None:
    """G10a: TaskType.STRUCTURED_EXTRACTION must exist (Phase 92 closure)."""
    from lingwen_shared.contracts.python.llm import TaskType
    assert hasattr(TaskType, "STRUCTURED_EXTRACTION")
    assert TaskType.STRUCTURED_EXTRACTION.value == "structured_extraction"


def test_extract_scene_uses_structured_extraction() -> None:
    """G10b: extract_scene switched from QUALITY_ANALYSIS fallback."""
    import inspect
    from lingwen_illustrations import prompt_builder
    source = inspect.getsource(prompt_builder.extract_scene)
    assert "TaskType.STRUCTURED_EXTRACTION" in source
    assert "TaskType.QUALITY_ANALYSIS" not in source


def test_llm_service_task_configs_includes_structured_extraction() -> None:
    """G10c: LLMService.TASK_CONFIGS has STRUCTURED_EXTRACTION entry."""
    from lingwen_shared.contracts.python.llm import TaskType
    from lingwen_llm_service.service import LLMService
    assert TaskType.STRUCTURED_EXTRACTION in LLMService.TASK_CONFIGS
    cfg = LLMService.TASK_CONFIGS[TaskType.STRUCTURED_EXTRACTION]
    assert "max_tokens" in cfg and "temperature" in cfg
```

After edit, run `ruff check --fix` on G10c imports to auto-fix import order.

### Commit 4 (docs): no code

- `collaboration/BACKLOG.md` — strike-through P2-EXTRACT-ENUM row + add recent change entry
- `collaboration/CURRENT_STATUS.md` — append Phase 92 row
- `CLAUDE.md` — bump version line v55.1 → v55.2
- `docs/superpowers/handoffs/2026-09-16-phase-92-extract-enum-handoff.md` — write handoff

## 3. Validation gates

Run in this order (per Phase 89 lesson — separate rootdir per package):

```bash
# Package-specific (uv-managed .venv has editable installs for all packages)
.venv/bin/python -m pytest packages/lingwen-shared/tests/test_llm_dto.py -v
.venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_prompt_builder.py -v
.venv/bin/python -m pytest packages/lingwen-llm-service/tests/ -v
.venv/bin/python -m pytest tests/test_phase90_illustrations.py -v
.venv/bin/python -m pytest apps/studio_api/tests/ -v

# Lint (only changed files — pre-existing errors untouched)
.venv/bin/python -m ruff check \
  packages/lingwen-shared/src/lingwen_shared/contracts/python/llm.py \
  packages/lingwen-shared/tests/test_llm_dto.py \
  packages/lingwen-llm-service/src/lingwen_llm_service/service.py \
  packages/lingwen-illustrations/src/lingwen_illustrations/prompt_builder.py \
  tests/test_phase90_illustrations.py
```

Acceptance: all GREEN; ruff clean on introduced lines (5 errors fixed by `--fix`; 2
pre-existing untouched).

## 4. Risk mitigation in commit sequence

- **Risk**: `extract_scene` regression — accidentally keep `QUALITY_ANALYSIS` fallback.
  - **Mitigation**: G10b explicitly asserts `QUALITY_ANALYSIS` not in source.
- **Risk**: `TASK_CONFIGS` dict update breaks other TaskType lookups.
  - **Mitigation**: `TaskType.STRUCTURED_EXTRACTION` is a new key; existing
    `dict[TaskType, dict]` lookups are unaffected.
- **Risk**: ruff auto-fix touches unrelated imports.
  - **Mitigation**: `ruff check --fix` only on changed lines; verify diff before commit.
- **Risk**: `uv.lock` drift surprises reviewer.
  - **Mitigation**: handoff §6 Lesson 2 documents the auto-sync behavior.

## 5. Rollback plan

If a regression is found post-merge:

1. Revert the single combined commit `refactor(phase-92): switch extract_scene ...`
2. Verify pre-commit pytest still 17/17 PASS on phase90 guards.
3. Push revert as `revert(phase-92): backout STRUCTURED_EXTRACTION switch`.

Cheap enough that the rollback is a one-liner. Phase 91 followup precedent: no rollback
needed in 7 commits since Phase 91.

## 6. Time estimate

| Step | Est. |
|------|------|
| spec + plan docs | 10 min |
| enum + TASK_CONFIGS + call-site edit | 10 min |
| tests + G10 a/b/c | 10 min |
| pytest + ruff validation | 5 min |
| docs sync + handoff | 15 min |
| 4 atomic commits + push | 5 min |
| **Total** | **~55 min** |

(The user-estimated "30 min" was optimistic — actual was closer to 45-55 min including
doc sync.)