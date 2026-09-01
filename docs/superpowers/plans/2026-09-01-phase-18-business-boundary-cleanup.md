# Phase 18 — Business Boundary + Interface Cleanup Plan

## Pre-flight

1. **Verify worktree at master HEAD `2e53a15a`**:
   ```bash
   git log --oneline -3
   ```

2. **Baseline gate** (must stay green throughout):
   ```bash
   cd apps/dashboard && pnpm exec knip       # 0 lines
   cd /home/ailearn/projects/LingWen/.worktrees/phase-18 && ./.venv/bin/python -m pytest packages/lingwen-core/tests/ packages/lingwen-quality/tests/ packages/lingwen-creator/tests/ packages/lingwen-shared/tests/ tests/ --rootdir=packages/lingwen-core
   pnpm knip                                   # 0 lines
   ```

3. **Verify domain entity availability**:
   ```bash
   grep -E "class Ripple\b|class RippleState\b|class NodeId\b|class NodeType\b" \
     packages/lingwen-core/src/lingwen_core/domain/ripple.py packages/lingwen-core/src/lingwen_core/domain/common.py
   ```

4. **Verify lingwen-quality importable**:
   ```bash
   ./.venv/bin/python tooling/hygiene/check_lingwen_quality_importable.py
   ```

## Commit Plan (10 commits)

### T1: Sub1.a — Migrate `infra/world_model.{NodeId,NodeType}` consumers

```bash
# Files:
#   tests/subplot/test_subplot_data_structures.py (line 29)
#   tests/subplot/test_subplot_integration.py (line 29)

# For each file: replace `from infra.world_model import NodeId, NodeType`
# with `from lingwen_core.domain.common import NodeId, NodeType`

git add tests/subplot/test_subplot_data_structures.py tests/subplot/test_subplot_integration.py
git commit -m "refactor(tests): migrate infra.world_model.NodeId/NodeType → lingwen_core.domain.common"
```

**Post-T1**: `pytest tests/subplot/ -q`

### T2: Sub1.b — Migrate `infra/world_model.data_structures.{Ripple,RippleState}` consumers

```bash
# Files:
#   tests/consistency/checkers/test_pacing_ripple_integration.py (lines 26-27)
#   tests/consistency/checkers/test_foreshadow_ripple_alignment.py (lines 26-27)
#   tests/world_model/test_snapshot_store.py (line 24)
#   tests/world_model/test_ripple_engine.py (line 20)
#   tests/world_model/test_ripple_queries.py (line 12)

# For each file: replace `from infra.world_model.data_structures import Ripple, RippleState`
# with `from lingwen_core.domain.ripple import Ripple, RippleState`

git add tests/consistency/checkers/test_pacing_ripple_integration.py \
        tests/consistency/checkers/test_foreshadow_ripple_alignment.py \
        tests/world_model/test_snapshot_store.py \
        tests/world_model/test_ripple_engine.py \
        tests/world_model/test_ripple_queries.py
git commit -m "refactor(tests): migrate infra.world_model.data_structures.Ripple/RippleState → lingwen_core.domain.ripple"
```

**Post-T2**: `pytest tests/consistency/checkers/test_pacing_ripple_integration.py tests/consistency/checkers/test_foreshadow_ripple_alignment.py tests/world_model/`

### T3: Sub1.c — Migrate `infra/subplot` + `infra/poc` consumers

```bash
# Files:
#   infra/subplot/data_structures.py (line 22)
#   infra/poc/run_volume_1.py (line 43)

# Same migration: infra.world_model.{NodeId,NodeType,KeyPoint,...} → lingwen_core.domain.common

git add infra/subplot/data_structures.py infra/poc/run_volume_1.py
git commit -m "refactor(infra): migrate subplot + poc from infra.world_model → lingwen_core.domain"
```

**Post-T3**: `pytest tests/subplot/ tests/consistency/checkers/`

### T4: Sub2.a — Migrate `infra/consistency.checkers.*` test consumers

```bash
# Files (5):
#   tests/consistency/test_pacing_checker.py → lingwen-quality.consistency.checkers.pacing_checker
#   tests/consistency/test_character_agency.py → lingwen-quality.consistency.checkers.character_agency
#   tests/consistency/test_core_props_checker.py → lingwen-quality.consistency.checkers.core_props_checker
#   tests/consistency/test_item_checker.py → lingwen-quality.consistency.checkers.item_checker

git add tests/consistency/test_pacing_checker.py \
        tests/consistency/test_character_agency.py \
        tests/consistency/test_core_props_checker.py \
        tests/consistency/test_item_checker.py
git commit -m "refactor(tests): migrate infra.consistency.checkers.* → lingwen-quality.consistency.checkers.*"
```

**Post-T4**: `pytest tests/consistency/test_pacing_checker.py tests/consistency/test_character_agency.py tests/consistency/test_core_props_checker.py tests/consistency/test_item_checker.py`

### T5: Sub2.b — Migrate `infra/consistency.creative_whitelist` + `checker_feedback`

```bash
# Files (2):
#   tests/consistency/test_creative_whitelist.py
#   scripts/ci_baseline_check.py

git add tests/consistency/test_creative_whitelist.py scripts/ci_baseline_check.py
git commit -m "refactor(tests+scripts): migrate infra.consistency.creative_whitelist + checker_feedback → lingwen-quality"
```

**Post-T5**: `pytest tests/consistency/test_creative_whitelist.py` + verify scripts still parseable

### T6: Sub3 — Migrate `infra/agent_system.reviewer` consumer

```bash
# Files (2):
#   packages/lingwen-core/src/lingwen_core/agents/agents/reviewer.py
#   tests/agent_system/test_reviewer.py

# Replace `from infra.consistency.*` + `from infra.agent_system.*` with canonical lingwen-quality imports

git add packages/lingwen-core/src/lingwen_core/agents/agents/reviewer.py tests/agent_system/test_reviewer.py
git commit -m "refactor(core): migrate reviewer agent from infra.consistency/agent_system → lingwen-quality"
```

**Post-T6**: `pytest tests/agent_system/test_reviewer.py`

### T7: Sub4 — Remove resolved TODO(Phase18) markers

```bash
# Files (8):
#   packages/lingwen-quality/src/lingwen_quality/consistency/checkers/foreshadow_checker_types.py
#   packages/lingwen-quality/src/lingwen_quality/consistency/checkers/pacing_checker.py (2 TODOs)
#   packages/lingwen-cli/src/lingwen_cli/commands/{ripple_rollback,ripple_reset,cascade,ripple_audit,ripple_scan}.py (7 TODOs)
#   packages/lingwen-core/src/lingwen_core/agents/{chapter_memory_hook,chapter_production_pilot,production_summary,context_helpers,context_builder}.py
#   packages/lingwen-core/src/lingwen_core/agents/internal/incremental_backfill.py

# Remove TODO(Phase18) comments since migrations resolved them

git add packages/lingwen-quality/... packages/lingwen-cli/... packages/lingwen-core/...
git commit -m "chore: remove resolved TODO(Phase18) markers after migration to lingwen-core.domain"
```

**Post-T7**: search for any remaining `TODO(Phase18)` (should be 0 in resolved scope; 2 remaining in `infra/exports/*` are separate concern)

### T8: Sub5.a — Update `.lingwen/architecture.yml`

```bash
# Edit:
#   - version field: "16.5.N7" → "16.5.N17+18"
#   - DP-02 enforcement_phase: add v16.5 #N.0-#N.17 markers
#   - DP-03 enforcement_phase: add v16.5 #N.0-#N.17 markers
#   - Add `domain` and `ports` module_boundaries entries (already exist, just verify they list)
#   - Add Phase 18 active_subsystems entry (domain + ports + use_cases)

git add .lingwen/architecture.yml
git commit -m "docs(architecture): mark Phase 18 closed — version 16.5.N17+18, add domain/ports/use_cases"
```

### T9: Sub5.b — Write Phase 18 handoff doc

```bash
git add docs/superpowers/handoffs/2026-09-01-phase-18-business-boundary-cleanup-handoff.md
git commit -m "docs(phase-18): handoff — domain/ports/use_cases shipped, infra/world_model consumers migrated"
```

### T10: Sub5.c — Update CLAUDE.md

```bash
git add CLAUDE.md
git commit -m "docs(phase-18): CLAUDE.md v18 entry"
```

## Final Verification

```bash
# 1. All gates green
cd /home/ailearn/projects/LingWen/.worktrees/phase-18/apps/dashboard && pnpm exec knip       # 0 lines
cd /home/ailearn/projects/LingWen/.worktrees/phase-18 && pnpm knip                          # 0 lines
./.venv/bin/python -m pytest packages/lingwen-core/tests/ packages/lingwen-quality/tests/ packages/lingwen-creator/tests/ packages/lingwen-shared/tests/ 2>&1 | tail -3
cd apps/dashboard && pnpm vitest run                                                        # 1762+1
pnpm tsc --noEmit                                                                           # 0
pnpm eslint .                                                                              # 0

# 2. Verify no remaining TODO(Phase18) in migrated scope
grep -rn "TODO(Phase18)" packages/lingwen-quality packages/lingwen-cli packages/lingwen-core/src/lingwen_core/agents/ 2>/dev/null | grep -v __pycache__
# Expected: 0 results (only infra/exports/ may remain, separate concern)

# 3. Verify no remaining infra.consistency/world_model/agent_system imports in migrated files
grep -rn "from infra.consistency\|from infra.world_model\|from infra.agent_system" packages/ tests/ scripts/ 2>/dev/null | grep -v __pycache__
# Expected: 0 results
```

## Push + Merge to Master (per new workflow)

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-18
git push -u origin phase-18
cd /home/ailearn/projects/LingWen
git checkout master
git merge --ff-only phase-18
git push origin master
```

## Cleanup

After merge:
```bash
git worktree remove .worktrees/phase-18
git branch -d phase-18
```

## Lessons (record in handoff T9)

1. **Verify-before-design (N.14 lesson 1 re-confirmed)** — Phase 18 plan from Aug 14 substantially executed by Phase 126 v16.5 #N.0-N.17. Actual remaining scope = 10 commits, not 16 tasks with all 16 needing work.
2. **knip + carryover verification** — `grep -rln "TODO(Phase18)"` revealed 17 markers but didn't show the actual domain/ports package existence; manual verification of package contents showed Phase 18 was mostly done.
3. **Atomic 1-task-per-commit** — 10 commits for 5 sub-phases of work; easy to review, easy to revert.
4. **Test files are first-class migration targets** — many of the imports live in tests/, not production code. Migrating tests first proves the new paths work before touching production.
5. **Domain entities migrate first, then ports, then consumers** — `lingwen-core.domain` (Sub1) + `lingwen-quality.consistency` (Sub2) are the canonical homes. Tests follow.