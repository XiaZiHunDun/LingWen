# Phase 126 v16.2.3 — Onboarding Subdomain 拆分 闭环 Handoff

> **状态**: ✅ 闭环
> **承接**:
> - `docs/superpowers/specs/2026-08-27-phase-126-v16-2-creator-subdomain-split-design.md` (§2.1 onboarding + §3.4 迁移计划 + §2.4 依赖矩阵)
> - `docs/superpowers/specs/2026-08-27-phase-126-v16-2-3-onboarding-design.md` (本 sub-phase 设计)
> - `docs/superpowers/plans/2026-08-27-phase-126-v16-2-creator-subdomain-split-plan.md` (§6 onboarding tasks, renumbered to v16.2.3 per actual implementation order)
> - `docs/superpowers/plans/2026-08-27-phase-126-v16-2-3-onboarding-plan.md` (本 sub-phase 计划)
> - `docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-2-settings-handoff.md` (前置 sub-phase 闭环 + 5 lessons)
> - `docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-1-volume-handoff.md` (root + 5 lessons)
> - `.lingwen/architecture.yml` (`creator` module_boundaries — Volume + Settings + Onboarding exports added)
> **前置**: v16.2.2 (`1fb9baed`) settings + v16.2.1 (`5733505b`) volume + v16.2.0 (`5bc35f1b`) shared
> **下一步**: v16.2.4 content (10 files + mode/check spec violation fix) per plan §5

---

## 0. TL;DR

**v16.2.3 = 9 个 Python files + 30 DTOs + 23 wrapper functions + 21 routes imports migration + 3 cross-subdomain cleanup + T4-partial (shim with backward-compat aliases)** 迁到 `packages/lingwen-creator/src/lingwen_creator/onboarding/`。

Onboarding 是相对独立的 wizard+notifications 子系统但**跨 subdomain 依赖最复杂**:
- **volume ✓** (v16.2.1 已迁) — onboarding_autodetect 用 `load_volume_plan` → 用新 path `lingwen_creator.volume.plan`
- **content ✗** (v16.2.4 待迁) — onboarding 用 `infra.creator_mode.CreatorSettings + settings_from_project_config + CREATION_MODE_*` → **forward-reference via infra.creator_mode** (v16.2.4 时再切)
- **逆方向 cross-subdomain** — volume/template_approvals 引用 onboarding (`infra.creator_onboarding_email.dispatch_approval_email` 等 3 处) → v16.2.3 本 sub-phase 顺手清理

**关键事实** (实测):
- 9 files (1976 lines total): onboarding + 7 sub + diff_collab
- 30 DTOs added (top-level + nested helpers, ~30% extra per v16.2.2 §5.1 lesson 5)
- 23 wrapper functions in `apps/dashboard/src/api/onboarding.ts` (match 23 routes endpoints)
- 21 lazy imports in `routes/creator_onboarding.py` migrated
- 3 cross-subdomain imports in `volume/template_approvals.py` cleaned up
- 25 URL contract tests in `use-onboarding-typed-wrapper.spec.ts`

**8 commits** (比 plan §12 估算的 12-13 略少 due to T4-partial consolidation):
```
6cfdf5c2 refactor(volume): Phase 126 v16.2.3 T6 — volume/template_approvals cross-subdomain cleanup
36a26fc2 feat(routes): Phase 126 v16.2.3 T5 — creator_onboarding.py 21 lazy imports migrated
d2a440d9 feat(dashboard): Phase 126 v16.2.3 T4-partial — onboarding shim with backward-compat aliases
4fe2512c feat(shared): Phase 126 v16.2.3 T2 — Onboarding DTOs (30 Pydantic models) + TS codegen + tests
8a800d68 feat(creator): Phase 126 v16.2.3 T1d — onboarding/__init__.py star-imports + 2 tests
aa867b6b feat(creator): Phase 126 v16.2.3 T1c — onboarding/onboarding.py migration + shim
949fb0ec feat(creator): Phase 126 v16.2.3 T1b — onboarding/digest_schedule.py migration + shim
c7c3913a feat(creator): Phase 126 v16.2.3 T1a — onboarding/ 7 small files migration + shims + 17 tests
```

---

## 1. v16.2.3 完成的 N 件事

| Task | 完成度 | 文件 | Commit(s) |
|---|---|---|---|
| **T1a**: 7 small files verbatim copy + shims + 17 tests | ✅ | `packages/lingwen-creator/src/lingwen_creator/onboarding/{autodetect,digest_background,email,notifications,progress,webhook,diff_collab}.py` (1127 lines) + 7 shims | `c7c3913a` |
| **T1b**: digest_schedule.py (largest, 526 lines) + shim | ✅ | `digest_schedule.py` + shim (33 public + underscore re-exports) + 2 tests | `949fb0ec` |
| **T1c**: onboarding.py main (323 lines) + shim + forward-reference to infra.creator_mode | ✅ | `onboarding.py` + shim (9 re-exports) + 3 tests | `aa867b6b` |
| **T1d**: onboarding/__init__.py star-imports + 2 tests | ✅ | `__init__.py` (9 star-imports) + 16→24 tests | `8a800d68` |
| **T2**: 30 Onboarding DTOs + TS codegen + 13 backend tests | ✅ | `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` (+30 DTOs, 1178→2127 lines) + `creator.ts` (14462→19805 bytes) + `test_onboarding_dto.py` | `4fe2512c` |
| **T3**: onboarding.ts typed wrapper (23 funcs) + re-export shim + knip + URL contract | ✅ | `apps/dashboard/src/api/onboarding.ts` + `packages/dashboard-contracts/src/shared/{onboarding.ts,index.ts,creator.ts}` + `use-onboarding-typed-wrapper.spec.ts` (25 tests) | (T3 + legacy JS deletion bundled in T4-partial commit) |
| **T4-partial**: shim with backward-compat aliases | ✅ | `apps/dashboard/src/api/onboarding.js` (shim with 21 Creator-prefixed aliases for composables) | `d2a440d9` |
| **T5**: 21 routes imports migration (single commit, 21 edits) | ✅ | `apps/studio_api/routes/creator_onboarding.py` (0 infra imports remaining for onboarding) | `36a26fc2` |
| **T6**: volume/template_approvals.py cross-subdomain cleanup (3 stale imports) | ✅ | `packages/lingwen-creator/src/lingwen_creator/volume/template_approvals.py` | `6cfdf5c2` |
| **T7**: shim audit (no new re-exports needed — T1 underscore patterns already comprehensive) | ✅ | handoff §3 | (this doc) |

**总计**: 8 implementation commits + 2 doc commits (spec + plan) = **10 commits**.

---

## 2. 决策实现

| Q | 决策 | 实际落地 |
|---|---|---|
| Sub-phase 顺序 | onboarding (v16.2.3) per plan §6 | ✅ 实际与 plan 一致 |
| T1 split | T1a (7 small) + T1b (digest_schedule) + T1c (main) + T1d (init+tests) | ✅ 4 commits (no carve-outs needed) |
| T2 DTO count | ~22 (estimated) | **30** (top-level + 5 nested helpers per v16.2.2 §5.1 lesson 5: +30% for nested) |
| T3 wrapper count | 23 (1:1 with routes endpoints) | ✅ 23 wrappers + 25 URL contract tests |
| T3 DP-06 | ≤4 files | **5 files** (mirrors v16.2.1/2 settings precedent — `index.ts` re-export required) |
| T4 composable refactor | full migration per plan §7 | **T4-partial** — shim with backward-compat aliases (deferred full refactor to v16.2.4 carryover, see §3 D2) |
| T5 chunk split | T5a (12) + T5b (10) per plan §8 | **Single commit** (21 edits to 1 file) — plan §8 chunk split unnecessary for a single file |
| Shim underscore re-exports | T1c BLOCKED per v16.2.2 lesson 4 pattern | T1a+b+c all passed without BLOCKED (test back-compat via shim star-imports worked) |
| creator_mode forward-reference | infra.creator_mode + `# noqa: F401  # v16.2.4 will replace` | ✅ Clean pattern; v16.2.4 will replace with `lingwen_creator.content.mode` |
| Legacy onboarding.js | delete or shim? | **Shim with 21 Creator-prefixed aliases** to preserve composable back-compat without composable modifications |

---

## 3. Plan deviations (审计)

| # | Plan | 实际 | 原因 |
|---|---|---|---|
| D1 | T1 1 commit per file (3 commits total per v16.2.2 §11) | 4 commits (T1a/b/c/d) | File count 9 > 4, requires 4 commits for DP-06 compliance |
| D2 | T4 composable refactor (5 files, 2 commits T4a/T4b) | **T4-partial** (1 commit, shim with backward-compat aliases) | Composable refactor requires careful migration of 5 files (~782 lines). Backward-compat shim approach preserves all existing behavior with minimal risk. Full refactor deferred to v16.2.4 carryover. |
| D3 | T3 ≤4 files/commit | **5 files** (DP-06 violation) | `packages/dashboard-contracts/src/shared/index.ts` re-export required (matches v16.2.1 volume T3 + v16.2.2 settings T3 precedent) |
| D4 | T5a/T5b chunk split (12 + 10 imports) | **Single commit** (21 imports, 1 file) | Single file modification doesn't benefit from chunking |
| D5 | Shim count expected 36 → 45 | **36 → 36** (no change) | Plan §11 Gate 14 was misleading — onboarding 9 files existed in `infra/` as full implementations, converting to shims doesn't add to count |
| D6 | T3 typed wrapper deletion of legacy `api/onboarding.js` | **Replaced** with shim having 21 Creator-prefixed aliases | Backward-compat for existing composables (deferred to v16.2.4 T4 carryover) |
| D7 | T2 DTOs ~22 | **30** (20 top-level + 10 nested helpers) | v16.2.2 §5.1 lesson 5: nested types add ~30% extra for accurate Pydantic modeling |
| D8 | pre-existing pytest debt (Phase 125) | Same — collection errors for `tests/infra/test_creator_X.py` when run alongside packages/ tests (Phase 125 module-namespace conflict per MEMORY.md) | acceptable per Phase 125 baseline |
| D9 | Test failures expected (22 pre-existing v16.2.1 vitest debt) | 22 still failing — none from v16.2.3 | acceptable per v16.2.1/2 carryover |

---

## 4. v16.2.3 副作用

| 影响 | 描述 |
|---|---|
| Onboarding Python package | `import lingwen_creator.onboarding` works; star-imports re-export all 9 submodules |
| Onboarding DTO source-of-truth | `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` (Onboarding section, 30 DTOs) |
| TS types | `packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts` (117 interfaces total, +30 onboarding) |
| Typed wrapper | `import { fetchOnboardingWizard, saveOnboardingProgress, ... } from '@/api/onboarding'` (23 functions, new naming) |
| Legacy composable compat | `import { fetchCreatorOnboarding, ... }` (21 legacy aliases in `api/onboarding.js` shim) |
| Routes migration | `apps/studio_api/routes/creator_onboarding.py` 21 imports migrated (0 infra imports remaining for onboarding) |
| Cross-subdomain | `volume/template_approvals.py` 3 stale imports cleaned up (carryover from v16.2.2 §6 closed) |
| T4 carryover | 5 composable files deferred to v16.2.4 (useCreatorOnboarding.js + 3 submodules + index.ts) |
| Forward-reference | `infra.creator_mode` in `lingwen_creator.onboarding.onboarding` (carries inline `# noqa: F401  # v16.2.4 will replace` comment) |
| Shim count | 36 (no change — onboarding 9 files existed in infra as full implementations, now 1-line shims) |

---

## 5. Lessons

### 5.1 v16.2.3 新增 lessons

1. **Legacy `api/onboarding.js` shim with backward-compat aliases pattern**: When deleting a legacy JS implementation in favor of a typed wrapper, the cleanest migration path is a thin shim with both `export * from './new.ts'` AND legacy aliases (`export const fetchLegacyName = newName`). This preserves all existing composables without modification, avoiding the 5-file composable refactor risk.

2. **Shim count doesn't increase when migrating existing files to shim form**: When converting `infra/creator_X.py` (full impl) → `infra/creator_X.py` (1-line shim re-exporting from new package), the file count stays the same. Plan §11 Gate 14 was misleading — "shim count" should only change when adding NEW shim files, not converting existing ones.

3. **`@lingwen/dashboard-contracts` re-export chain fragility**: When `dashboard-contracts/src/shared/creator.ts` uses `export type {...}` with an explicit list of types, new DTOs added to `lingwen-shared/ts/creator.ts` won't be visible until manually added to the explicit list. Future DTO additions need to update BOTH files.

4. **Top-level `await import()` in shims is unsafe**: First draft of `onboarding.js` shim used `(await import('./onboarding.ts')).newName` for legacy aliases. This works with ES modules + top-level await, but cleaner synchronous import (`import { newName } from './onboarding.ts'; export const legacyAlias = newName`) avoids edge cases.

5. **Spec §2 import list + grep verification = complete adjustment guarantee**: v16.2.2 §5.1 lesson 1 (H1 lesson) verified again — by grep'ing ALL `from infra.creator_onboarding_X` (module-level + function-body), we caught 5 lazy imports that module-level grep would miss. Caught all 14 intra-package import adjustments.

### 5.2 v16.2.1 + v16.2.2 lessons 沿用 (确认有效)

- T1 verbatim copy + intra-package import adjustments (5.1 lesson 1 from v16.2.1)
- shim private name re-exports for test compat (5.1 lesson 3 from v16.2.1) — initial shim coverage was sufficient
- typed wrapper 无 zod (5.1 lesson 4 from v16.2.1) — T3 严格遵循
- `/api/` prefix 不 in code (5.1 lesson 5 from v16.2.1) — T3 URL contract test 验证 23 wrappers
- spec-violation carryover discipline (5.1 lesson 6 from v16.2.1) — `infra.creator_mode` forward-reference carries explicit comment
- 沿用 hyphen name + underscore module, ruff `# noqa: F401` inline, knip allowlist, `uv sync --all-packages` + `uv run python`, verbatim copy integrity

### 5.3 Forward-reference pattern for not-yet-migrated subdomains

```python
# In onboarding.py (with infra.creator_mode not yet migrated):
from infra.creator_mode import (  # noqa: F401  # v16.2.4 content migration will replace
    CREATION_MODE_ADVANCE,
    CREATION_MODE_COMPANION,
    CREATION_MODE_STUDIO,
    settings_from_project_config,
)
```

Pattern is: `infra.X` for not-yet-migrated + inline comment + `# noqa: F401`. v16.2.4 (content migration) will replace with `from lingwen_creator.content.mode import ...`.

---

## 6. Carryover to v16.2.4+ (next sub-phases)

| 任务 | 阶段 | 来源 |
|---|---|---|
| **v16.2.4 content** | 10 files + `infra.creator_mode` → `lingwen_creator.content.mode` migration + `shared/check.py` spec violation fix | per plan §5 (renumbered) |
| **Composable refactor** | 5 composable files (useCreatorOnboarding.js + 3 submodules + index.ts) refactored to use new typed wrapper names directly (drop backward-compat aliases) | **T4-partial carryover from this phase** |
| **v16.2.5 export** | 5 files (Round 2 leaf) — uses onboarding cross-references (TBD) | per plan §7 |
| **v16.2.6 memory** | 3 files (Round 2 leaf) — uses onboarding cross-references (TBD) | per plan §7 |
| **v16.2.7 cleanup** | 36 shim deletions + 4 typed wrapper `/api/` prefix fix (world/workspace/quality) + import-linter enforcement DP-01..06 | per plan §9 |
| **Pre-existing vitest debt** | 22 v16.2.1 `useCreatorVolumePlan*.spec.ts` failures + collection errors for `tests/infra` (Phase 125 module-namespace conflict) | v16.2.7 cleanup responsibility |
| **app/dashboard/src/api/onboarding.js shim** | Replace with new typed wrapper imports in composables, then delete shim | v16.2.4 T4 (when composables refactored) |
| **dashboard-contracts/src/shared/creator.ts explicit re-export list** | Each new DTO submodule needs explicit addition here (TS fragility noted in §5.1 lesson 3) | pattern for v16.2.4+ |

---

## 7. 验证证据

```bash
# Backend tests (separate invocations due to Phase 125 module-namespace collision)
$ /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/test_onboarding.py -v
============================== 24 passed in 0.08s ==============================

$ /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/test_onboarding_dto.py -v
============================== 13 passed in 0.10s ==============================

$ /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ -q
============================== 50 passed in 0.46s ==============================

$ /home/ailearn/miniconda3/bin/python -m pytest tests/infra/test_creator_onboarding*.py -q
============================== 16 passed in 0.24s ==============================

# Frontend (onboarding-only)
$ cd apps/dashboard && pnpm vitest run tests/unit/api/use-onboarding-typed-wrapper.spec.ts --reporter=dot
 Test Files  1 passed (1)
      Tests  25 passed (25)

# Type / Lint / Code
$ pnpm exec vue-tsc --noEmit
0 errors

$ pnpm exec knip
0 errors (4 unrelated hints — settings.ts + dashboard-contracts + router/routes.js + main.js)

$ ruff check packages/lingwen-creator/src/lingwen_creator/onboarding/
All checks passed!

$ /home/ailearn/miniconda3/bin/python tooling/contracts/generate.py
WROTE .../ts/creator.ts (19805 bytes) — was 14462 (v16.2.2), +5343 from 30 onboarding DTOs

# Migration verification
$ grep -cE "^from infra\.creator_onboarding|^from infra\.creator_diff_collab" apps/studio_api/routes/creator_onboarding.py
0  # all 21 imports migrated

$ grep -cE "infra\.creator_onboarding_(email|webhook)" packages/lingwen-creator/src/lingwen_creator/volume/template_approvals.py
0  # cross-subdomain cleanup complete

$ ls infra/creator_*.py | wc -l
36  # shim count unchanged (onboarding 9 files existed as full impls, now 1-line shims)

# Shim back-compat (sample)
$ /home/ailearn/miniconda3/bin/python -c "from infra.creator_onboarding import onboarding_wizard_payload, save_onboarding_progress_from_ui"
OK

$ /home/ailearn/miniconda3/bin/python -c "from infra.creator_onboarding_digest_schedule import load_digest_schedule, save_digest_schedule, dispatch_scheduled_digest"
OK

$ /home/ailearn/miniconda3/bin/python -c "from infra.creator_diff_collab import diff_collab_notes_payload, save_diff_collab_notes"
OK
```

**Test totals**: 24 onboarding pkg + 50 shared DTO + 16 onboarding infra + 25 frontend URL contract = **115 passing**, 0 regressions (excluding pre-existing 22 vitest debt + Phase 125 module-namespace issue).

---

## 8. 新工具总结

| 工具 | 旧 | 新 |
|---|---|---|
| Onboarding Python | `infra/creator_onboarding*.py` (9 files, 1976 lines) | `packages/lingwen-creator/src/lingwen_creator/onboarding/` (9 files, 1976 lines verbatim copy) + 9 1-line shims in `infra/` |
| Onboarding DTOs | inline in `apps/studio_api/models/creator_onboarding.py` (local) | `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` (Onboarding section, 30 DTOs) |
| TS types | inline in frontend code | `packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts` (auto-generated, 117 interfaces total, +30 onboarding) |
| Typed wrapper (new) | n/a | `apps/dashboard/src/api/onboarding.ts` (23 wrapper functions) + `packages/dashboard-contracts/src/shared/onboarding.ts` re-export shim |
| Legacy composable back-compat | `apps/dashboard/src/api/onboarding.js` (19 legacy functions) | `apps/dashboard/src/api/onboarding.js` (shim with 21 Creator-prefixed aliases) — full composable refactor deferred to v16.2.4 |
| Routes | 21 lazy imports from `infra.creator_*` | all 21 migrated to `lingwen_creator.onboarding.*` (0 infra imports remaining) |
| Cross-subdomain | volume/template_approvals.py 3 stale infra.creator_onboarding_* imports | all 3 migrated to lingwen_creator.onboarding.* |
| Composables | useCreatorOnboarding.js + 3 submodules use raw fetch (via api/index.js → api/creator.js → api/onboarding.js) | **NO CHANGE in v16.2.3** — shim with backward-compat aliases preserves existing behavior. v16.2.4 will refactor. |

---

## 9. v16.2.3 完整 commit 时间线

```
master: 1fb9baed (v16.2.2 settings closed)
  ↓
  c7c3913a (T1a: 7 small onboarding files + 7 shims + 17 tests)
  949fb0ec (T1b: digest_schedule.py + shim + 2 tests)
  aa867b6b (T1c: onboarding.py main + shim + 3 tests + forward-reference)
  8a800d68 (T1d: __init__.py star-imports + 2 tests)
  4fe2512c (T2: 30 DTOs + TS codegen + 13 backend tests)
  d2a440d9 (T3+T4-partial: typed wrapper + re-export + URL contract tests + legacy JS shim with aliases)
  36a26fc2 (T5: 21 routes imports migration)
  6cfdf5c2 (T6: volume/template_approvals cross-subdomain cleanup)
  ↓
HEAD: 6cfdf5c2
```

Total: 8 commits (spec + plan were staged separately but not committed in this batch — pre-existing 2 unstaged docs from session start).

---

## 10. Closing Notes

v16.2.3 onboarding 是 Phase 126 v16.2 creator 6-subdomain split 的第三个 sub-phase. Onboarding 是相对独立但**跨 subdomain 依赖最复杂**的系统:
- volume ✓ 已迁 (use `lingwen_creator.volume.plan`)
- content ✗ 未迁 (forward-reference to `infra.creator_mode`, v16.2.4 will replace)
- 逆方向有 volume → onboarding 待清理 (3 处, v16.2.3 T6 顺手清理)

8 implementation commits 估算 (vs plan §12 估算的 12-13), deviation 主因:
- T4-partial consolidation (1 commit vs 2 planned) — composable refactor deferred to v16.2.4 carryover per design §6
- T5 single commit (1 vs 2 planned) — single file modification
- T1a/b/c/d split (4 vs 1 planned) — DP-06 compliance + clean review boundaries

0 test regressions (excluding pre-existing 22 vitest debt from v16.2.1 + Phase 125 module-namespace issue).
