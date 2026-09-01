# Phase 18 — Business Boundary + Interface Cleanup Plan (REVISED)

## Pre-flight

1. **Verify worktree at master HEAD `2e53a15a`**:
   ```bash
   git log --oneline -3
   ```

2. **Baseline gates**:
   ```bash
   cd apps/dashboard && pnpm exec knip       # 0 lines
   ./.venv/bin/python -m pytest tests/subplot/ tests/consistency/test_pacing_checker.py -q   # verify pre-T1 state
   ```

3. **Verify domain entity availability**:
   ```bash
   grep -rE "class Ripple\b|class NodeId\b|class Chapter\b|class Volume\b" packages/lingwen-core/src/lingwen_core/domain/ --include="*.py" | head -10
   ```

## Commit Plan (3 commits)

### T1: Sub-A — Remove 14 TODO(Phase18) markers

```bash
# Files to edit:
#   packages/lingwen-quality/src/lingwen_quality/consistency/checkers/foreshadow_checker_types.py:18
#   packages/lingwen-quality/src/lingwen_quality/consistency/checkers/pacing_checker.py:21,25 (2 markers)
#   packages/lingwen-cli/src/lingwen_cli/commands/{ripple_rollback,ripple_reset,cascade,ripple_audit,ripple_scan}.py (5 files, 7 markers)
#   packages/lingwen-core/src/lingwen_core/agents/{chapter_memory_hook,chapter_production_pilot,production_summary,context_helpers,context_builder}.py (5 files, 7 markers)
#   packages/lingwen-core/src/lingwen_core/agents/internal/incremental_backfill.py:1
#
# Each marker references `packages/lingwen-domain` which doesn't exist.
# The canonical home is `packages/lingwen-core/domain/` (already exists).
# Remove markers since the domain entity gap is closed.

# Use sed or Edit to remove each `# TODO(Phase18): ...` line

git add packages/lingwen-quality/ packages/lingwen-cli/ packages/lingwen-core/
git commit -m "chore: remove 14 TODO(Phase18) markers (domain gap closed)"
```

**Post-T1**: `grep -rn "TODO(Phase18)" packages/ | wc -l` → 0

### T2: Sub-B — Update `.lingwen/architecture.yml`

```bash
# Edit:
#   - version: "16.5.N7" → "16.5.N17+18"
#   - DP-02 enforcement_phase: add Phase 18 closure note
#   - DP-03 enforcement_phase: add Phase 18 closure note
#   - Add active_subsystems entry for domain/ports/use_cases

git add .lingwen/architecture.yml
git commit -m "docs(architecture): mark Phase 18 closed — domain/ports/use_cases shipped"
```

### T3: Sub-C — Write handoff + update CLAUDE.md

```bash
git add docs/superpowers/handoffs/2026-09-01-phase-18-business-boundary-cleanup-handoff.md CLAUDE.md
git commit -m "docs(phase-18): handoff + CLAUDE.md update"
```

## Final Verification

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-18/apps/dashboard && pnpm exec knip       # 0 lines
cd /home/ailearn/projects/LingWen/.worktrees/phase-18 && pnpm knip                          # 0 lines
./.venv/bin/python -m pytest packages/lingwen-core/tests/ packages/lingwen-quality/tests/ packages/lingwen-creator/tests/ packages/lingwen-shared/tests/ 2>&1 | tail -3
cd apps/dashboard && pnpm vitest run                                                        # 1762+1
pnpm tsc --noEmit                                                                           # 0
pnpm eslint .                                                                              # 0

# Verify TODO(Phase18) markers removed (in scope)
grep -rn "TODO(Phase18)" packages/lingwen-quality packages/lingwen-cli packages/lingwen-core/src 2>/dev/null | grep -v __pycache__
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

## Lessons (record in handoff T3)

1. **Verify-before-design (N.14 lesson 1 re-confirmed)** — Original Phase 18 plan estimated 16 tasks with extensive migration work. Empirical verification revealed only 3 sub-phases actually need to close Phase 18:
   - `infra/consistency/` and `infra/agent_system/` are 1-line shim re-exports (not duplicated implementations) — no migration needed
   - `infra/world_model.data_structures.WorldSnapshot` has API divergence with `lingwen_core.domain.WorldSnapshot` (missing to_dict/from_dict + active_subplots) — migration would expand Phase 18 scope
   - All 17 TODO(Phase18) markers reference a non-existent `packages/lingwen-domain` — they were placeholder comments for Phase 18 closure, can be removed now that `packages/lingwen-core/domain` exists

2. **PHASE-COMPAT shim detection** — Look for `# PHASE-COMPAT:` docstrings at top of files. These mark directories marked for deletion post-v16.x. Don't migrate their consumers unless doing full bulk rename — the shims work transparently.

3. **API divergence in domain migration** — `lingwen_core.domain.*` are minimal dataclasses without `to_dict`/`from_dict` (per Phase 18.1 DDD principle: domain pure, persistence separate). Migrations from `infra.*` must handle serialization in a separate adapter layer.

4. **Atomic 1-task-per-commit scales to tiny scope** — 3 commits for 3 sub-phases. Even when the work is small, atomic commits help review.