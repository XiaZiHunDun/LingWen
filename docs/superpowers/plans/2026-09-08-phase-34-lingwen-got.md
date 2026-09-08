# Phase 34 LINGWEN-GOT Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate `infra/got/*` (8 modules, 1788 lines, 32 public symbols) to `packages/lingwen-got/src/lingwen_got/` as a proper uv workspace package, updating 30 consumer files across `apps/infra/packages/tests` and relocating 12 got-specific test files to `packages/lingwen-got/tests/`.

**Architecture:** Batched mechanical sed per Phase 32 SHIM-CLEANUP precedent. Flat package mirror (no sub-packages). 8 atomic commits (C0-C7) with each gated by 1-3 validation commands. `infra/got/` hard-deleted after all consumer migration complete (no shim needed since all 30 consumers are bounded + known).

**Tech Stack:** Python 3.12+ · uv workspace · hatchling build backend · pytest · ruff

**Spec:** `docs/superpowers/specs/2026-09-08-phase-34-lingwen-got-design.md` (commit `2ec3c626`)

**Worktree:** `/home/ailearn/projects/LingWen-phase-34` (branch `phase-34-lingwen-got`)

---

## File Structure (目标态)

```
packages/lingwen-got/                                    ← NEW
├── pyproject.toml                                       ← NEW
├── README.md                                            ← NEW
├── src/lingwen_got/                                     ← NEW (mirror infra/got/)
│   ├── __init__.py          (98)    # 32 symbol re-export
│   ├── aggregator.py        (138)
│   ├── cache.py              (66)
│   ├── data_structures.py   (160)
│   ├── graph.py             (352)
│   ├── llm_compute.py       (133)
│   ├── scheduler.py         (420)
│   ├── visualizer.py        (211)
│   └── workflow_loader.py   (210)
└── tests/                                              ← NEW
    ├── __init__.py                                     ← NEW
    ├── conftest.py                                     ← NEW
    ├── test_aggregator.py                              ← MOVED (tests/got/test_aggregator.py)
    ├── test_cache.py                                   ← MOVED+RENAME (tests/got/test_got_cache.py)
    ├── test_data_structures.py                         ← MOVED+RENAME (tests/got/test_got_data_structures.py)
    ├── test_decision_pause_resume.py                   ← MOVED
    ├── test_graph.py                                   ← MOVED
    ├── test_llm_compute.py                             ← MOVED
    ├── test_llm_compute_e2e.py                         ← MOVED
    ├── test_scheduler.py                               ← MOVED+RENAME (tests/got/test_got_scheduler.py)
    ├── test_visualizer.py                              ← MOVED
    ├── test_workflow_loader.py                         ← MOVED
    ├── test_got_bridge.py                              ← MOVED (tests/agent_system/test_got_bridge.py)
    └── test_got_bridge_budget.py                       ← MOVED (tests/agent_system/test_got_bridge_budget.py)

# 30 consumer files: import path sed `infra.got.X` → `lingwen_got.X`
#   (no consumer file location changes except 12 test files above)
#   - 4 × packages/lingwen-core/src/lingwen_core/agents/ (workflow_runner, chapter_production_pilot, chapter_golden_path, got_bridge)
#   - 3 × apps/studio_api/ (protocols.py, routes/workflows.py, helpers/workflow.py)
#   - 2 × infra/ (cross_volume/incremental_backfill.py, poc/run_volume_1.py)
#   - 7 × tests/agent_system/ (test_chapter_emit, test_chapter_golden_path, test_decision_integration, test_master_controller_stub_router_e2e, test_phase7_1_production_fixes, test_production_summary, test_workflow_runner)
#   - 1 × tests/cross_volume/ (test_incremental_backfill.py)
#   - 2 × tests/dashboard/ (test_app_workflow_production_summary_f66.py, test_decision_api.py)

# 1 directory deletion:
#   - infra/got/  (8 .py files, 1788 lines total) — DELETED in C6

# 1 new test file:
#   - tests/test_phase34_lingwen_got.py  (7 regression guards)
```

---

## Commit Chain

```
phase-34-lingwen-got
├── C0  [DONE] docs(phase-34): write spec                                       (2ec3c626)
├── C1         chore(packages): scaffold lingwen-got package skeleton
├── C2         refactor(test): move 12 got-related test files to packages/lingwen-got/tests/
├── C3         refactor(infra): migrate 4 lingwen-core consumers to lingwen_got
├── C4         refactor(apps): migrate 3 apps/studio_api consumers to lingwen_got
├── C5         refactor(infra): migrate 2 infra + 10 tests/ consumers to lingwen_got
├── C6         chore(infra): delete infra/got/ directory
└── C7         test(phase-34): regression guard tests + doc sync
```

---

## Task 0: Pre-flight — Worktree env bootstrap (Phase 32 lesson)

**Files:** Worktree setup only, no production changes.

- [ ] **Step 1: Verify worktree exists**

```bash
git worktree list | grep phase-34-lingwen-got
```

Expected: shows `/home/ailearn/projects/LingWen-phase-34` on branch `phase-34-lingwen-got`.

- [ ] **Step 2: Sync uv workspace dependencies**

```bash
cd /home/ailearn/projects/LingWen-phase-34
uv sync --all-packages --offline
```

Expected: exit 0; "Resolved N packages" + "Installed N packages" output. Use `--offline` per Phase 32 lesson (sandbox-safe).

- [ ] **Step 3: Install extra test deps not in workspace deps**

```bash
cd /home/ailearn/projects/LingWen-phase-34
uv pip install pytest pytest-asyncio psutil pytest-timeout pytest-cov pytest-env pytest-metadata pytest-json-report
```

Expected: "Successfully installed ..." per MEMORY.md Phase 32 lesson (these are NOT in workspace deps but used by pytest config).

- [ ] **Step 4: Verify Python interpreter is worktree's .venv**

```bash
cd /home/ailearn/projects/LingWen-phase-34
ls .venv/bin/python && .venv/bin/python --version
```

Expected: `.venv/bin/python` exists, version 3.12+ (NOT `/home/ailearn/miniconda3/bin/python` per MEMORY.md N.14 lesson 4).

- [ ] **Step 5: Capture baseline test failure list (Phase 32 N.14 lesson 4)**

```bash
cd /home/ailearn/projects/LingWen-phase-34
.venv/bin/python -m pytest tests/ --co -q 2>&1 | grep -E "FAILED|ERROR" | head -40
```

Expected: capture list of pre-existing failures to diff against at C6 G11.

- [ ] **Step 6: Save baseline to /tmp/phase34-baseline.txt**

```bash
.venv/bin/python -m pytest tests/ --co -q 2>&1 | grep -E "FAILED|ERROR" | sort -u > /tmp/phase34-baseline.txt
wc -l /tmp/phase34-baseline.txt
```

Expected: line count saved. Compare to G11 output at end of phase.

---

## Task 1: C1 — Scaffold lingwen-got package skeleton

**Files:**
- Create: `packages/lingwen-got/pyproject.toml`
- Create: `packages/lingwen-got/README.md`
- Create: `packages/lingwen-got/src/lingwen_got/{__init__,aggregator,cache,data_structures,graph,llm_compute,scheduler,visualizer,workflow_loader}.py` (9 files)
- Create: `packages/lingwen-got/tests/__init__.py`
- Create: `packages/lingwen-got/tests/conftest.py`
- Modify: `pyproject.toml` (root) — `tool.uv.workspace.members` + `tool.uv.sources`
- Modify: `packages/lingwen-got/src/lingwen_got/__init__.py` + 4 submodules (scheduler/visualizer/workflow_loader/graph) — internal literal-path imports → relative

- [ ] **Step 1: Create packages/lingwen-got/pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "lingwen-got"
version = "0.1.0"
description = "LingWen · Graph of Thoughts engine (ThoughtGraph + GoTScheduler + aggregator + viz + workflow loader)"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.7",
    "lingwen-llm",
]

[project.optional-dependencies]
test = ["pytest>=8.0"]

[tool.hatch.build.targets.wheel]
packages = ["src/lingwen_got"]
```

Write to `/home/ailearn/projects/LingWen-phase-34/packages/lingwen-got/pyproject.toml`.

- [ ] **Step 2: Create packages/lingwen-got/README.md**

```markdown
# lingwen-got

LingWen · Graph of Thoughts engine.

This package is the GoT scheduler + graph + LLM compute + workflow loader + visualizer stack, lifted out of `infra/got/` into a proper uv workspace package in Phase 34.

Public API: 32 symbols (see `lingwen_got.__all__`).
```

- [ ] **Step 3: Copy 9 .py files from infra/got/ to packages/lingwen-got/src/lingwen_got/**

```bash
cd /home/ailearn/projects/LingWen-phase-34
mkdir -p packages/lingwen-got/src/lingwen_got
cp infra/got/__init__.py packages/lingwen-got/src/lingwen_got/__init__.py
cp infra/got/aggregator.py packages/lingwen-got/src/lingwen_got/aggregator.py
cp infra/got/cache.py packages/lingwen-got/src/lingwen_got/cache.py
cp infra/got/data_structures.py packages/lingwen-got/src/lingwen_got/data_structures.py
cp infra/got/graph.py packages/lingwen-got/src/lingwen_got/graph.py
cp infra/got/llm_compute.py packages/lingwen-got/src/lingwen_got/llm_compute.py
cp infra/got/scheduler.py packages/lingwen-got/src/lingwen_got/scheduler.py
cp infra/got/visualizer.py packages/lingwen-got/src/lingwen_got/visualizer.py
cp infra/got/workflow_loader.py packages/lingwen-got/src/lingwen_got/workflow_loader.py
```

Expected: 9 files copied, no errors.

- [ ] **Step 4: Create packages/lingwen-got/tests/__init__.py**

```python
"""lingwen-got test package."""
```

- [ ] **Step 5: Create packages/lingwen-got/tests/conftest.py**

```python
"""Shared pytest fixtures for lingwen-got tests.

Currently a placeholder — copy any project-level fixtures here as needed.
"""
```

- [ ] **Step 6: Convert internal literal-path imports to relative (within lingwen-got)**

The 4 submodules currently use literal-path imports that must become relative. Run this sed (in worktree):

```bash
cd /home/ailearn/projects/LingWen-phase-34
sed -i 's|^from infra\.got\.aggregator|from .aggregator|' packages/lingwen-got/src/lingwen_got/aggregator.py
sed -i 's|^from infra\.got\.cache|from .cache|' packages/lingwen-got/src/lingwen_got/cache.py
sed -i 's|^from infra\.got\.data_structures|from .data_structures|' packages/lingwen-got/src/lingwen_got/data_structures.py
sed -i 's|^from infra\.got\.graph|from .graph|' packages/lingwen-got/src/lingwen_got/graph.py
sed -i 's|^from infra\.got\.llm_compute|from .llm_compute|' packages/lingwen-got/src/lingwen_got/llm_compute.py
sed -i 's|^from infra\.got\.scheduler|from .scheduler|' packages/lingwen-got/src/lingwen_got/scheduler.py
sed -i 's|^from infra\.got\.visualizer|from .visualizer|' packages/lingwen-got/src/lingwen_got/visualizer.py
sed -i 's|^from infra\.got\.workflow_loader|from .workflow_loader|' packages/lingwen-got/src/lingwen_got/workflow_loader.py

# Also handle indented (function-body / multi-line) imports — use case-by-case
# for scheduler.py:252 (function-body lazy import) — manual edit:
```

- [ ] **Step 7: Manually fix the 1 function-body lazy import in scheduler.py:252**

```bash
cd /home/ailearn/projects/LingWen-phase-34
# Open in editor, find line 252 in packages/lingwen-got/src/lingwen_got/scheduler.py:
# Original (function body, lazy):
#     from infra.got.visualizer import render_mermaid_from_scheduler
# Change to:
#     from .visualizer import render_mermaid_from_scheduler
```

Expected: scheduler.py has zero literal-path infra.got imports left.

- [ ] **Step 8: Add lingwen-got to root pyproject.toml workspace**

Edit `/home/ailearn/projects/LingWen-phase-34/pyproject.toml`:

In `[tool.uv.workspace]`, add `"packages/lingwen-got",` to the `members` list (e.g. after `"packages/lingwen-creator",`):

```toml
[tool.uv.workspace]
members = [
    "packages/lingwen-core",
    "packages/lingwen-storage",
    "packages/lingwen-llm",
    "packages/lingwen-memory",
    "packages/lingwen-prompt",
    "packages/lingwen-pipeline",
    "packages/lingwen-quality",
    "packages/lingwen-cli",
    "packages/lingwen-shared",
    "packages/lingwen-creator",
    "packages/lingwen-got",   # ★ Phase 34
    "apps/studio_api",
]
```

In `[tool.uv.sources]`, add:

```toml
lingwen-got = { workspace = true }
```

- [ ] **Step 9: G1 — uv sync validates lingwen-got integration**

```bash
cd /home/ailearn/projects/LingWen-phase-34
uv sync --all-packages --offline 2>&1 | tail -5
```

Expected: "Resolved N packages" + "Installed N packages" + exit 0. No resolution errors for `lingwen-got`.

- [ ] **Step 10: G2 — import lingwen_got and verify 32 symbols**

```bash
cd /home/ailearn/projects/LingWen-phase-34
.venv/bin/python -c "import lingwen_got; symbols = lingwen_got.__all__; print(f'count={len(symbols)}'); assert len(symbols) == 32, f'expected 32, got {len(symbols)}'"
```

Expected: prints `count=32`, exit 0.

- [ ] **Step 11: Verify zero literal-path infra.got imports inside lingwen-got**

```bash
cd /home/ailearn/projects/LingWen-phase-34
grep -rn "infra\.got" packages/lingwen-got/src/ --include="*.py" || echo "OK: zero literal-path imports"
```

Expected: prints `OK: zero literal-path imports`. If hits found, fix them before committing C1.

- [ ] **Step 12: Commit C1**

```bash
cd /home/ailearn/projects/LingWen-phase-34
git add packages/lingwen-got/pyproject.toml \
        packages/lingwen-got/README.md \
        packages/lingwen-got/src/lingwen_got/ \
        packages/lingwen-got/tests/__init__.py \
        packages/lingwen-got/tests/conftest.py \
        pyproject.toml
git commit -m "chore(packages): scaffold lingwen-got package skeleton

Phase 34 C1: scaffold packages/lingwen-got as a proper uv workspace
member (hatchling build + lingwen-llm dep). Copies infra/got/* to
packages/lingwen-got/src/lingwen_got/ with internal literal-path
imports converted to relative (4 modules affected: scheduler,
visualizer, workflow_loader, graph). Adds lingwen-got to root
pyproject.toml [tool.uv.workspace] members + [tool.uv.sources].

infra/got/ directory remains — C6 deletes it.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

Expected: 1 commit. `git log --oneline -2` shows C0 + C1.

---

## Task 2: C2 — Move 12 got-related test files

**Files:**
- Move + rename: 10 from `tests/got/*` → `packages/lingwen-got/tests/*` (3 with `got_` → rename)
- Move: 2 from `tests/agent_system/test_got_bridge*.py` → `packages/lingwen-got/tests/`
- Modify: 12 test files — sed `from infra.got.X` → `from lingwen_got.X`
- Delete: `tests/got/` (empty directory)

- [ ] **Step 1: Move 10 files from tests/got/ to packages/lingwen-got/tests/**

```bash
cd /home/ailearn/projects/LingWen-phase-34
mv tests/got/test_aggregator.py                packages/lingwen-got/tests/test_aggregator.py
mv tests/got/test_got_cache.py                 packages/lingwen-got/tests/test_cache.py
mv tests/got/test_got_data_structures.py       packages/lingwen-got/tests/test_data_structures.py
mv tests/got/test_got_scheduler.py             packages/lingwen-got/tests/test_scheduler.py
mv tests/got/test_graph.py                     packages/lingwen-got/tests/test_graph.py
mv tests/got/test_llm_compute.py               packages/lingwen-got/tests/test_llm_compute.py
mv tests/got/test_llm_compute_e2e.py           packages/lingwen-got/tests/test_llm_compute_e2e.py
mv tests/got/test_visualizer.py                packages/lingwen-got/tests/test_visualizer.py
mv tests/got/test_workflow_loader.py           packages/lingwen-got/tests/test_workflow_loader.py
mv tests/got/test_decision_pause_resume.py     packages/lingwen-got/tests/test_decision_pause_resume.py
```

Expected: 10 files moved. `ls tests/got/` should show only `__pycache__` left.

- [ ] **Step 2: Move 2 files from tests/agent_system/ to packages/lingwen-got/tests/**

```bash
cd /home/ailearn/projects/LingWen-phase-34
mv tests/agent_system/test_got_bridge.py          packages/lingwen-got/tests/test_got_bridge.py
mv tests/agent_system/test_got_bridge_budget.py   packages/lingwen-got/tests/test_got_bridge_budget.py
```

Expected: 2 files moved.

- [ ] **Step 3: Sed all 12 test files: infra.got.X → lingwen_got.X**

```bash
cd /home/ailearn/projects/LingWen-phase-34
for f in packages/lingwen-got/tests/test_aggregator.py \
         packages/lingwen-got/tests/test_cache.py \
         packages/lingwen-got/tests/test_data_structures.py \
         packages/lingwen-got/tests/test_decision_pause_resume.py \
         packages/lingwen-got/tests/test_graph.py \
         packages/lingwen-got/tests/test_llm_compute.py \
         packages/lingwen-got/tests/test_llm_compute_e2e.py \
         packages/lingwen-got/tests/test_scheduler.py \
         packages/lingwen-got/tests/test_visualizer.py \
         packages/lingwen-got/tests/test_workflow_loader.py \
         packages/lingwen-got/tests/test_got_bridge.py \
         packages/lingwen-got/tests/test_got_bridge_budget.py; do
    sed -i 's|from infra\.got|from lingwen_got|g; s|infra\.got\.|lingwen_got.|g' "$f"
done
```

Expected: 12 files updated.

- [ ] **Step 4: Verify zero infra.got remaining in moved test files**

```bash
cd /home/ailearn/projects/LingWen-phase-34
grep -rn "infra\.got" packages/lingwen-got/tests/ --include="*.py" || echo "OK: zero infra.got"
```

Expected: `OK: zero infra.got`.

- [ ] **Step 5: Clean up empty tests/got/ directory + __pycache__**

```bash
cd /home/ailearn/projects/LingWen-phase-34
rm -rf tests/got/
ls tests/ | grep -E "^got" || echo "OK: tests/got/ removed"
```

Expected: prints `OK: tests/got/ removed`.

- [ ] **Step 6: G3 — Run new packages/lingwen-got/tests/ suite**

```bash
cd /home/ailearn/projects/LingWen-phase-34
cd packages/lingwen-got && ../../.venv/bin/python -m pytest tests/ -v 2>&1 | tail -30
cd /home/ailearn/projects/LingWen-phase-34
```

Expected: all moved tests PASS. Failures would indicate sed missed something — fix and re-run.

- [ ] **Step 7: G4 — Run remaining tests/agent_system/ tests (excluding moved files)**

```bash
cd /home/ailearn/projects/LingWen-phase-34
.venv/bin/python -m pytest tests/agent_system/ -v \
  --ignore=tests/agent_system/test_got_bridge.py \
  --ignore=tests/agent_system/test_got_bridge_budget.py 2>&1 | tail -20
```

Expected: remaining 7 test files all PASS.

- [ ] **Step 8: Commit C2**

```bash
cd /home/ailearn/projects/LingWen-phase-34
git add -A packages/lingwen-got/tests/ tests/agent_system/test_got_bridge.py tests/agent_system/test_got_bridge_budget.py tests/got/
git rm -r tests/got/
git commit -m "refactor(test): move 12 got-related test files to packages/lingwen-got/tests/

Phase 34 C2: relocates all got-specific tests to the new package:
- 10 files from tests/got/ (3 renamed to remove got_ prefix: test_cache,
  test_data_structures, test_scheduler)
- 2 files from tests/agent_system/: test_got_bridge.py + test_got_bridge_budget.py

All test files now use 'from lingwen_got.X import Y' instead of
'infra.got.X'. tests/got/ directory deleted.

Validation: G3 (12 lingwen-got tests pass) + G4 (remaining 7
tests/agent_system tests still pass).

Co-Authored-By: Claude <noreply@anthropic.com>"
```

Expected: 1 commit. C2 is the largest file-movement commit in Phase 34.

---

## Task 3: C3 — Migrate 4 lingwen-core consumers

**Files:**
- Modify: `packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py` — sed imports
- Modify: `packages/lingwen-core/src/lingwen_core/agents/chapter_production_pilot.py`
- Modify: `packages/lingwen-core/src/lingwen_core/agents/chapter_golden_path.py`
- Modify: `packages/lingwen-core/src/lingwen_core/agents/got_bridge.py` (含 function-body lazy imports L447-449)

- [ ] **Step 1: Sed 4 lingwen-core files**

```bash
cd /home/ailearn/projects/LingWen-phase-34
for f in packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py \
         packages/lingwen-core/src/lingwen_core/agents/chapter_production_pilot.py \
         packages/lingwen-core/src/lingwen_core/agents/chapter_golden_path.py \
         packages/lingwen-core/src/lingwen_core/agents/got_bridge.py; do
    sed -i 's|from infra\.got|from lingwen_got|g; s|infra\.got\.|lingwen_got.|g' "$f"
done
```

Expected: 4 files updated. The sed handles both `from infra.got.X import Y` AND `infra.got.X` references in code (e.g. type annotations).

- [ ] **Step 2: Verify zero infra.got in lingwen-core agents**

```bash
cd /home/ailearn/projects/LingWen-phase-34
grep -rn "infra\.got" packages/lingwen-core/src/lingwen_core/agents/ --include="*.py" || echo "OK: zero infra.got"
```

Expected: `OK: zero infra.got`.

- [ ] **Step 3: G5 — Run lingwen-core tests**

```bash
cd /home/ailearn/projects/LingWen-phase-34/packages/lingwen-core
../../.venv/bin/python -m pytest tests/ -v --rootdir=. 2>&1 | tail -30
cd /home/ailearn/projects/LingWen-phase-34
```

Expected: all lingwen-core tests PASS.

- [ ] **Step 4: Commit C3**

```bash
cd /home/ailearn/projects/LingWen-phase-34
git add packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py \
        packages/lingwen-core/src/lingwen_core/agents/chapter_production_pilot.py \
        packages/lingwen-core/src/lingwen_core/agents/chapter_golden_path.py \
        packages/lingwen-core/src/lingwen_core/agents/got_bridge.py
git commit -m "refactor(infra): migrate 4 lingwen-core consumers to lingwen_got

Phase 34 C3: updates workflow_runner / chapter_production_pilot /
chapter_golden_path / got_bridge to import from lingwen_got.* instead
of infra.got.* (including got_bridge's function-body lazy imports at
L447-449).

Validation: G5 (lingwen-core tests pass).

Co-Authored-By: Claude <noreply@anthropic.com>"
```

Expected: 1 commit.

---

## Task 4: C4 — Migrate 3 apps/studio_api consumers

**Files:**
- Modify: `apps/studio_api/protocols.py` (lazy import L259)
- Modify: `apps/studio_api/routes/workflows.py` (lazy imports L181-183)
- Modify: `apps/studio_api/helpers/workflow.py`

- [ ] **Step 1: Sed 3 apps/studio_api files**

```bash
cd /home/ailearn/projects/LingWen-phase-34
for f in apps/studio_api/protocols.py \
         apps/studio_api/routes/workflows.py \
         apps/studio_api/helpers/workflow.py; do
    sed -i 's|from infra\.got|from lingwen_got|g; s|infra\.got\.|lingwen_got.|g' "$f"
done
```

Expected: 3 files updated.

- [ ] **Step 2: Verify zero infra.got in apps/studio_api**

```bash
cd /home/ailearn/projects/LingWen-phase-34
grep -rn "infra\.got" apps/studio_api/ --include="*.py" || echo "OK: zero infra.got"
```

Expected: `OK: zero infra.got`.

- [ ] **Step 3: G6 — Import smoke (verify lazy import paths work)**

```bash
cd /home/ailearn/projects/LingWen-phase-34
.venv/bin/python -c "
from apps.studio_api.protocols import *
from apps.studio_api.routes.workflows import *
print('imports OK')
"
```

Expected: prints `imports OK`, exit 0. This validates that the lazy imports at protocols.py:259 + routes/workflows.py:181-183 also resolve correctly.

- [ ] **Step 4: G6b — Run apps/studio_api tests**

```bash
cd /home/ailearn/projects/LingWen-phase-34
.venv/bin/python -m pytest apps/studio_api/tests/ -v 2>&1 | tail -20
```

Expected: all apps/studio_api tests PASS.

- [ ] **Step 5: Commit C4**

```bash
cd /home/ailearn/projects/LingWen-phase-34
git add apps/studio_api/protocols.py \
        apps/studio_api/routes/workflows.py \
        apps/studio_api/helpers/workflow.py
git commit -m "refactor(apps): migrate 3 apps/studio_api consumers to lingwen_got

Phase 34 C4: updates protocols.py (lazy L259), routes/workflows.py
(lazy L181-183), helpers/workflow.py to import from lingwen_got.*
instead of infra.got.*.

Validation: G6 (lazy import smoke) + G6b (studio_api tests).

Co-Authored-By: Claude <noreply@anthropic.com>"
```

Expected: 1 commit.

---

## Task 5: C5 — Migrate 2 infra consumers + 10 tests/ consumers

**Files (12 total):**
- Modify: `infra/cross_volume/incremental_backfill.py`
- Modify: `infra/poc/run_volume_1.py`
- Modify: 7 × `tests/agent_system/` (test_chapter_emit, test_chapter_golden_path, test_decision_integration, test_master_controller_stub_router_e2e, test_phase7_1_production_fixes, test_production_summary, test_workflow_runner)
- Modify: `tests/cross_volume/test_incremental_backfill.py`
- Modify: 2 × `tests/dashboard/` (test_app_workflow_production_summary_f66, test_decision_api)

- [ ] **Step 1: Sed 2 infra files**

```bash
cd /home/ailearn/projects/LingWen-phase-34
for f in infra/cross_volume/incremental_backfill.py \
         infra/poc/run_volume_1.py; do
    sed -i 's|from infra\.got|from lingwen_got|g; s|infra\.got\.|lingwen_got.|g' "$f"
done
```

- [ ] **Step 2: Sed 10 tests/ files**

```bash
cd /home/ailearn/projects/LingWen-phase-34
for f in tests/agent_system/test_chapter_emit.py \
         tests/agent_system/test_chapter_golden_path.py \
         tests/agent_system/test_decision_integration.py \
         tests/agent_system/test_master_controller_stub_router_e2e.py \
         tests/agent_system/test_phase7_1_production_fixes.py \
         tests/agent_system/test_production_summary.py \
         tests/agent_system/test_workflow_runner.py \
         tests/cross_volume/test_incremental_backfill.py \
         tests/dashboard/test_app_workflow_production_summary_f66.py \
         tests/dashboard/test_decision_api.py; do
    sed -i 's|from infra\.got|from lingwen_got|g; s|infra\.got\.|lingwen_got.|g' "$f"
done
```

Expected: 12 files updated in total (2 infra + 10 tests).

- [ ] **Step 3: G7 — Run root tests (excluding moved files)**

```bash
cd /home/ailearn/projects/LingWen-phase-34
.venv/bin/python -m pytest tests/ -v \
  --ignore=tests/agent_system/test_got_bridge.py \
  --ignore=tests/agent_system/test_got_bridge_budget.py 2>&1 | tail -30
```

Expected: all root-discovered tests PASS. The `test_got_bridge*` files are now in `packages/lingwen-got/tests/` (already validated in G3). Diff against `/tmp/phase34-baseline.txt` (pre-existing failures should match).

- [ ] **Step 4: G8 — Verify zero infra.got in any file outside lingwen-got/src**

```bash
cd /home/ailearn/projects/LingWen-phase-34
grep -rln "infra\.got\b" --include="*.py" . \
  --exclude-dir=node_modules \
  --exclude-dir=.git \
  --exclude-dir=__pycache__ \
  | grep -v "^./packages/lingwen-got/src/" || echo "OK: zero infra.got outside lingwen-got"
```

Expected: `OK: zero infra.got outside lingwen-got`. If hits found, fix them (likely a literal-path or function-body import sed missed — per Phase 32 N.14 lesson 1).

- [ ] **Step 5: Commit C5**

```bash
cd /home/ailearn/projects/LingWen-phase-34
git add infra/cross_volume/incremental_backfill.py \
        infra/poc/run_volume_1.py \
        tests/agent_system/test_chapter_emit.py \
        tests/agent_system/test_chapter_golden_path.py \
        tests/agent_system/test_decision_integration.py \
        tests/agent_system/test_master_controller_stub_router_e2e.py \
        tests/agent_system/test_phase7_1_production_fixes.py \
        tests/agent_system/test_production_summary.py \
        tests/agent_system/test_workflow_runner.py \
        tests/cross_volume/test_incremental_backfill.py \
        tests/dashboard/test_app_workflow_production_summary_f66.py \
        tests/dashboard/test_decision_api.py
git commit -m "refactor(infra): migrate 2 infra + 10 tests consumers to lingwen_got

Phase 34 C5: final consumer batch — 2 infra/* + 7 tests/agent_system/*
+ 1 tests/cross_volume/* + 2 tests/dashboard/* — all switched from
infra.got.* to lingwen_got.* via mechanical sed.

After this commit, infra.got.* has zero consumers anywhere outside
packages/lingwen-got/src/lingwen_got/.

Validation: G7 (root tests pass, pre-existing failures match
/tmp/phase34-baseline.txt) + G8 (zero infra.got hits outside
lingwen-got/src/).

Co-Authored-By: Claude <noreply@anthropic.com>"
```

Expected: 1 commit.

---

## Task 6: C6 — Delete infra/got/ directory

**Files:**
- Delete: `infra/got/` (8 .py files + `__init__.py`)

- [ ] **Step 1: G9 — Final pre-deletion grep (whole repo)**

```bash
cd /home/ailearn/projects/LingWen-phase-34
grep -rln "infra\.got\b" --include="*.py" . \
  --exclude-dir=node_modules \
  --exclude-dir=.git \
  --exclude-dir=__pycache__ || echo "OK: zero infra.got in repo"
```

Expected: `OK: zero infra.got in repo`. If hits found, STOP — must be fixed before deletion (an unresolved import would cause `ModuleNotFoundError` everywhere).

- [ ] **Step 2: Delete infra/got/ directory**

```bash
cd /home/ailearn/projects/LingWen-phase-34
rm -rf infra/got/
ls infra/got/ 2>&1 || echo "OK: infra/got/ deleted"
```

Expected: `ls` fails, `OK: infra/got/ deleted`.

- [ ] **Step 3: G10 — ruff clean**

```bash
cd /home/ailearn/projects/LingWen-phase-34
ruff check . 2>&1 | tail -10
```

Expected: `All checks passed!` or zero errors. Fix any auto-fixable issues with `ruff check --fix`.

- [ ] **Step 4: G11 — Run full root test suite**

```bash
cd /home/ailearn/projects/LingWen-phase-34
.venv/bin/python -m pytest tests/ -v 2>&1 | tail -20
```

Expected: same failures as `/tmp/phase34-baseline.txt` (pre-existing) + ZERO new failures. If new failures appear, they're Phase 34 regressions — fix before commit.

- [ ] **Step 5: Verify lingwen-got tests still pass**

```bash
cd /home/ailearn/projects/LingWen-phase-34
cd packages/lingwen-got && ../../.venv/bin/python -m pytest tests/ -v 2>&1 | tail -10
cd /home/ailearn/projects/LingWen-phase-34
```

Expected: all 12 lingwen-got test files PASS.

- [ ] **Step 6: Commit C6**

```bash
cd /home/ailearn/projects/LingWen-phase-34
git add -u infra/got/
git commit -m "chore(infra): delete infra/got/ directory

Phase 34 C6: after all 30 consumer files migrated (C2-C5), infra/got/
no longer has any consumers. Hard delete the directory (8 .py files,
1788 lines).

infra/ directory itself remains — infra/{paths, project_config,
logging_config, errors, studio_registry} are still in use by
lingwen-core/pipeline/creator (out of scope for Phase 34, tracked as
P3-ARCHDEBT carryover).

Validation: G9 (zero infra.got in repo) + G10 (ruff clean) +
G11 (root tests match baseline, no regressions).

Co-Authored-By: Claude <noreply@anthropic.com>"
```

Expected: 1 commit. Note `git add -u infra/got/` adds the deletions.

---

## Task 7: C7 — Regression guard tests + doc sync

**Files:**
- Create: `tests/test_phase34_lingwen_got.py` (7 regression guards)
- Modify: `CLAUDE.md` (v33.0 entry + Phase 34 carryover + invariant #49)
- Modify: `.lingwen/architecture.yml` (version 32.0 → 33.0; invariants add #49; workspace members add lingwen-got)
- Modify: `docs/LINGWEN_ARCHITECTURE_SPEC.md` (lingwen-got section + GoT module row)
- Modify: `docs/superpowers/handoffs/2026-09-07-phase-32-shim-cleanup-handoff.md` (carryover flip)
- Modify: `docs/superpowers/archive/PHASE_HISTORY.md` (v33.0 row)
- Modify: `MEMORY.md` (master HEAD + Phase 34 lessons)
- Create: `docs/superpowers/handoffs/2026-09-08-phase-34-lingwen-got-handoff.md`

- [ ] **Step 1: Create tests/test_phase34_lingwen_got.py with 7 guards**

```python
"""Phase 34 LINGWEN-GOT regression guards.

Verify packages/lingwen-got/ is the canonical GoT engine location and
infra/got/ has been deleted. See
docs/superpowers/specs/2026-09-08-phase-34-lingwen-got-design.md
section 6.
"""
from __future__ import annotations

import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_lingwen_got_pyproject_exists():
    """packages/lingwen-got/pyproject.toml must exist (C1)."""
    assert (REPO_ROOT / "packages" / "lingwen-got" / "pyproject.toml").is_file()


def test_lingwen_got_init_exists():
    """packages/lingwen-got/src/lingwen_got/__init__.py must exist (C1)."""
    assert (REPO_ROOT / "packages" / "lingwen-got" / "src" / "lingwen_got" / "__init__.py").is_file()


def test_infra_got_directory_deleted():
    """infra/got/ directory must NOT exist (C6)."""
    assert not (REPO_ROOT / "infra" / "got").exists()


def test_lingwen_got_exports_32_symbols():
    """Public API surface must match pre-migration infra.got (32 symbols)."""
    import lingwen_got
    assert len(lingwen_got.__all__) == 32
    expected = {
        "ThoughtNode", "NodeExecution", "NodeType", "NodeStatus",
        "ThoughtGraph", "GraphError", "DuplicateNodeError", "NodeNotFoundError",
        "ExecutionNotFoundError", "GraphCycleError",
        "ThoughtCache", "JudgmentAggregator",
        "GoTScheduler", "ExecutionSummary", "ComputeResult",
        "SchedulerError", "HumanInterventionRequired", "MaxStepsExceeded",
        "load_workflow", "WorkflowError", "WorkflowNotFoundError",
        "WorkflowParseError", "WorkflowValidationError",
        "LLMComputeFn", "default_prompt_builder",
        "NODE_STATUS_CLASS", "render_mermaid", "render_mermaid_from_scheduler",
        "render_status_table", "render_status_table_from_scheduler",
        "render_summary", "render_summary_from_scheduler",
    }
    assert expected.issubset(set(lingwen_got.__all__))


def test_lingwen_got_tests_directory_complete():
    """12 test files must exist in packages/lingwen-got/tests/."""
    expected = [
        "test_aggregator.py", "test_cache.py", "test_data_structures.py",
        "test_decision_pause_resume.py", "test_graph.py", "test_llm_compute.py",
        "test_llm_compute_e2e.py", "test_scheduler.py", "test_visualizer.py",
        "test_workflow_loader.py", "test_got_bridge.py", "test_got_bridge_budget.py",
    ]
    tests_dir = REPO_ROOT / "packages" / "lingwen-got" / "tests"
    for name in expected:
        assert (tests_dir / name).is_file(), f"Missing {name}"


def test_lingwen_core_consumers_use_lingwen_got():
    """4 lingwen-core consumers must import from lingwen_got (not infra.got)."""
    files = [
        "packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py",
        "packages/lingwen-core/src/lingwen_core/agents/chapter_production_pilot.py",
        "packages/lingwen-core/src/lingwen_core/agents/chapter_golden_path.py",
        "packages/lingwen-core/src/lingwen_core/agents/got_bridge.py",
    ]
    for f in files:
        content = (REPO_ROOT / f).read_text()
        assert "infra.got" not in content, f"{f} still references infra.got"
        assert "lingwen_got" in content, f"{f} must import lingwen_got"


def test_lingwen_got_depends_on_lingwen_llm():
    """lingwen-got pyproject.toml must declare lingwen-llm dependency."""
    pyproject = REPO_ROOT / "packages" / "lingwen-got" / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    deps = data["project"]["dependencies"]
    assert any("lingwen-llm" in d for d in deps), "lingwen-got must depend on lingwen-llm"
```

Write to `/home/ailearn/projects/LingWen-phase-34/tests/test_phase34_lingwen_got.py`.

- [ ] **Step 2: Run regression guards**

```bash
cd /home/ailearn/projects/LingWen-phase-34
.venv/bin/python -m pytest tests/test_phase34_lingwen_got.py -v 2>&1 | tail -15
```

Expected: 7/7 PASS. These were already GREEN at C6 since the migration is done — C7 just locks in the assertions for future regression prevention.

- [ ] **Step 3: Update CLAUDE.md (v33.0 entry + invariant #49)**

Open `/home/ailearn/projects/LingWen-phase-34/CLAUDE.md` and apply these edits:

(a) Update version banner line: `# 灵文 · 工业化小说生产系统 ... 当前状态: v33.0 (Phase 34 LINGWEN-GOT 闭环) · 更新: 2026-09-08`

(b) Update header table:
```
| 后端 | Python 3.12+ / FastAPI / SQLite / uv workspace (packages/lingwen-* + apps/studio_api) |
```
Change to include `lingwen-got`:
```
| 后端 | Python 3.12+ / FastAPI / SQLite / uv workspace (packages/lingwen-* 含 got + apps/studio_api) |
```

(c) Add to "架构不变量" table:
```
| I049 | packages/lingwen-got/ 是 GoT 引擎唯一实包; infra.got.* 路径非法 (Phase 34+) |
```

(d) Update "已知遗留" section to add Phase 34 entry (mirror Phase 32/33 format).

- [ ] **Step 4: Update .lingwen/architecture.yml (version + invariants + workspace)**

Edit `/home/ailearn/projects/LingWen-phase-34/.lingwen/architecture.yml`:

(a) Top-level `version: "32.0"` → `version: "33.0"`

(b) In `invariants` section, add after I048:
```yaml
- id: I049
  title: lingwen-got canonical
  status: enforced
  description: |
    packages/lingwen-got/ 是 GoT 引擎的唯一实包. infra.got.* 路径非法
    (Phase 34 起). 任何新代码必须 `from lingwen_got.X import Y`.
  enforcement: |
    - tests/test_phase34_lingwen_got.py::test_infra_got_directory_deleted
    - grep -rln "infra\.got\b" --include="*.py" . → 0 行
```

(c) In `workspace.members` list, add `packages/lingwen-got`.

- [ ] **Step 5: Update docs/LINGWEN_ARCHITECTURE_SPEC.md**

Add a new section for `lingwen-got` package (mirror format of existing package sections). Update the GoT module row in any tables: `infra/got` → `packages/lingwen-got/src/lingwen_got`.

- [ ] **Step 6: Flip Phase 32 handoff carryover**

Edit `/home/ailearn/projects/LingWen-phase-34/docs/superpowers/handoffs/2026-09-07-phase-32-shim-cleanup-handoff.md`:

In the "Carryover to Phase 33+" table, change:
```
| **`infra.got.*` → `packages/lingwen-got/` migration** | 199 tests, multi-day | 1 phase / 20-30 commits |
```
to:
```
| ~~**`infra.got.*` → `packages/lingwen-got/` migration**~~ | CLOSED by Phase 34 (v33.0) | n/a |
```

- [ ] **Step 7: Add v33.0 row to docs/superpowers/archive/PHASE_HISTORY.md**

Edit `/home/ailearn/projects/LingWen-phase-34/docs/superpowers/archive/PHASE_HISTORY.md`:

Add a new row at the end (mirror v32.0 format):
```
| v33.0 | 2026-09-08 | Phase 34 LINGWEN-GOT | packages/lingwen-got/ 创建 (9 modules, 32 public symbols); 30 consumer 迁移; 12 test files 搬到 packages/lingwen-got/tests/; infra/got/ 删除; invariant #49 NEW |
```

- [ ] **Step 8: Update MEMORY.md**

Edit `/home/ailearn/projects/LingWen-phase-34/MEMORY.md`:

(a) Update Master HEAD line:
```
- **Master HEAD**: `<phase-34-merge-sha>` (Phase 34 — lingwen-got package migration)
```

(b) Update Phase list:
```
- **Phases 23-34 history gap**: ... v33.0 = Phase 34 LINGWEN-GOT (this phase)
```

(c) Add Phase 34 lessons to "## Critical" or appropriate section:
```
- **⚠️ Phase 34 lesson (mechanical sed + 3-pattern audit)**: 30 consumer files sed'd
  `infra.got.X` → `lingwen_got.X` in 4 batches (C2/C3/C4/C5). The 3-pattern audit
  (literal path + 同包 relative + 父包 relative + TYPE_CHECKING + function-body lazy)
  caught no missed sites in C5 — was clean. The function-body lazy import at
  `infra/got/scheduler.py:252` was caught and fixed in C1 (not C5).
```

(d) Update carryover section:
```
- **P2-ARCHDEBT (remaining)**: `infra/world_model/__init__.py` split (1 phase / 8-12 commits) — Phase 35
- **P3-ARCHDEBT (NEW)**: `infra.{paths,project_config,logging_config,errors,studio_registry}` → packages/ migration — Phase 36+
- **Phase 34** ✅ CLOSED — lingwen-got package migration done
```

- [ ] **Step 9: G12 — Run regression guards**

```bash
cd /home/ailearn/projects/LingWen-phase-34
.venv/bin/python -m pytest tests/test_phase34_lingwen_got.py -v 2>&1 | tail -15
```

Expected: 7/7 PASS.

- [ ] **Step 10: G13 — ruff clean**

```bash
cd /home/ailearn/projects/LingWen-phase-34
ruff check . 2>&1 | tail -5
```

Expected: `All checks passed!`.

- [ ] **Step 11: Write handoff doc**

Create `/home/ailearn/projects/LingWen-phase-34/docs/superpowers/handoffs/2026-09-08-phase-34-lingwen-got-handoff.md` mirroring the Phase 32/33 handoff format:

Required sections:
1. Final Summary table (commit count / files moved / test count / ruff / consumer count)
2. Commit chain (C0-C7 with sha + 1-line description each)
3. Validation gates log (G1-G13 + G6b with PASS/FAIL)
4. Lessons learned (Phase 34 specific)
5. Doc sync (12+ carrier flips)
6. Carryover closure (P2-ARCHDEBT got → CLOSED; P3-ARCHDEBT NEW)
7. Solo workflow closure (worktree remove + ff-merge + push)

- [ ] **Step 12: Commit C7**

```bash
cd /home/ailearn/projects/LingWen-phase-34
git add tests/test_phase34_lingwen_got.py \
        CLAUDE.md \
        .lingwen/architecture.yml \
        docs/LINGWEN_ARCHITECTURE_SPEC.md \
        docs/superpowers/handoffs/2026-09-07-phase-32-shim-cleanup-handoff.md \
        docs/superpowers/archive/PHASE_HISTORY.md \
        MEMORY.md \
        docs/superpowers/handoffs/2026-09-08-phase-34-lingwen-got-handoff.md
git commit -m "test(phase-34): regression guard tests + doc sync

Phase 34 C7: locks in the migration with 7 regression guards + syncs
all carrier documentation.

Guards (tests/test_phase34_lingwen_got.py):
1. lingwen-got pyproject.toml exists
2. lingwen-got __init__.py exists
3. infra/got/ directory deleted
4. lingwen_got.__all__ has 32 symbols (matches pre-migration API surface)
5. 12 test files exist in packages/lingwen-got/tests/
6. 4 lingwen-core consumers import lingwen_got (not infra.got)
7. lingwen-got pyproject declares lingwen-llm dep

Doc sync:
- CLAUDE.md v33.0 entry + invariant #49
- .lingwen/architecture.yml version 32.0 → 33.0 + invariant #49 + workspace lingwen-got
- docs/LINGWEN_ARCHITECTURE_SPEC.md lingwen-got section + GoT module row
- phase-32 handoff: P2-ARCHDEBT got → CLOSED
- PHASE_HISTORY.md v33.0 row
- MEMORY.md: master HEAD + Phase 34 lessons + carryover updates
- handoff doc

Validation: G12 (7/7 guards GREEN) + G13 (ruff clean).

Co-Authored-By: Claude <noreply@anthropic.com>"
```

Expected: 1 commit. C7 is final commit on `phase-34-lingwen-got` branch.

---

## Task 8: Post-execution — Handoff + ff-merge + push

- [ ] **Step 1: Verify commit chain complete**

```bash
cd /home/ailearn/projects/LingWen-phase-34
git log --oneline eecdd20c..HEAD
```

Expected: 8 commits (C0-C7) on top of master `eecdd20c`.

- [ ] **Step 2: Final full-suite test verification**

```bash
cd /home/ailearn/projects/LingWen-phase-34
.venv/bin/python -m pytest tests/ 2>&1 | tail -5
.venv/bin/python -m pytest packages/lingwen-got/tests/ 2>&1 | tail -5
.venv/bin/python -m pytest packages/lingwen-core/tests/ --rootdir=packages/lingwen-core 2>&1 | tail -5
.venv/bin/python -m pytest apps/studio_api/tests/ 2>&1 | tail -5
```

Expected: all four test invocations PASS (or match `/tmp/phase34-baseline.txt` pre-existing failures).

- [ ] **Step 3: Push branch**

```bash
cd /home/ailearn/projects/LingWen-phase-34
git push -u origin phase-34-lingwen-got
```

Expected: branch pushed to origin.

- [ ] **Step 4: ff-merge to master**

```bash
cd /home/ailearn/projects/LingWen
git checkout master
git merge --ff-only phase-34-lingwen-got
git push origin master
```

Expected: master HEAD now at Phase 34 final commit; `git log --oneline -1` shows the C7 commit.

- [ ] **Step 5: Cleanup worktree**

```bash
cd /home/ailearn/projects/LingWen
git worktree remove /home/ailearn/projects/LingWen-phase-34
git worktree list | grep phase-34 || echo "OK: worktree removed"
```

Expected: worktree removed; `git worktree list` no longer shows it.

---

## Self-Review

**1. Spec coverage:**
- §3 目标架构 (lingwen-got pyproject + 9 src files + 13 test files + workspace + invariant #49) → Task 1 ✓
- §4 30 consumers in 4 batches → Tasks 2, 3, 4, 5 ✓
- §5 8 commits (C0-C7) → Tasks 1, 2, 3, 4, 5, 6, 7 ✓ (C0 already done in Task 0)
- §6 7 regression guards → Task 7 Step 1 ✓
- §7 14 validation gates → Steps in Tasks 1-7 (G1-G13 + G6b distributed) ✓
- §10 success criteria → Tasks 7-8 verify each ✓

**2. Placeholder scan:** No TBD/TODO/FIXME/XXX/??? in plan. All sed commands shown in full. All pyproject.toml content shown. All regression guard test code shown.

**3. Type consistency:** Symbols referenced consistently (`lingwen_got`, `ThoughtGraph`, `GoTScheduler`, etc.) — all defined in C1 Step 3 + exported in `lingwen_got.__all__`. Test file names consistent between C2 (move) + C7 guard (verify). Validation gate numbers (G1-G13 + G6b) consistent with spec.

---

## Execution Choice

Plan complete and saved to `docs/superpowers/plans/2026-09-08-phase-34-lingwen-got.md`. Two execution options:

1. **Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**