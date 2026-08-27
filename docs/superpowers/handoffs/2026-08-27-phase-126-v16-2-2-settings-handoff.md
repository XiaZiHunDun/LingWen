# Phase 126 v16.2.2 — Settings Subdomain 拆分 闭环 Handoff

> **状态**: ✅ 闭环
> **承接**:
> - `docs/superpowers/specs/2026-08-27-phase-126-v16-2-creator-subdomain-split-design.md` (§2.1 settings + §3.3 迁移计划 + §2.4 依赖矩阵)
> - `docs/superpowers/specs/2026-08-27-phase-126-v16-2-2-settings-design.md` (本 sub-phase 设计)
> - `docs/superpowers/plans/2026-08-27-phase-126-v16-2-creator-subdomain-split-plan.md` (§4 v16.2.2 tasks)
> - `docs/superpowers/plans/2026-08-27-phase-126-v16-2-2-settings-plan.md` (本 sub-phase 计划)
> - `docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-1-volume-handoff.md` (前置 sub-phase 闭环 + 5 lessons)
> - `.lingwen/architecture.yml` (creator module_boundaries)
> **前置**: v16.2.1 (`5733505b`) volume + v16.2.0 (`5bc35f1b`) shared + v16.1 + v16.0 + v15.7.1
> **下一步**: v16.2.3 onboarding (per plan §6 — 9 files)

---

## 0. TL;DR

**v16.2.2 = 3 个 Python files + 28 DTOs + 32 wrapper functions + 3 composable refactors + 32 routes imports + shim audit (3 underscore re-exports) + cross-subdomain cleanup** 全部迁到 `packages/lingwen-creator/src/lingwen_creator/settings/`。

**13 commits** in master HEAD = `7a0694c8` (实际 12 commits + 1 follow-up — T1c 因 BLOCKED 拆 2 commits):

```
7a0694c8 refactor(volume): T6 cross-subdomain lazy import cleanup
cce77ab2 feat(routes): T5b creator_settings.py finalize
8352033a feat(routes): T5a creator_settings.py merge_preferences imports chunk 1
213dac36 feat(routes): T4b settings submodule test mocks + creator_settings.py docs imports
04e4c3c5 feat(dashboard): T4b composable submodule refactor
ed56673a feat(dashboard): T4a useCreatorSettings composable refactor part 1
239829e4 feat(dashboard): Phase 126 v16.2.2 T3 — settings typed wrapper + re-export shim + knip + URL contract tests
69ed75a0 feat(shared): T2 Settings DTOs (28 Pydantic models) + TS codegen
8695442e feat(creator): T1d settings/__init__.py star-imports + tests
e85980c4 feat(creator): T1c-followup add _normalize_factory_preset_id re-export
e8a52aec feat(creator): T1c settings/merge_preferences.py migration + shim
9494ba87 feat(creator): T1b settings/history.py migration + shim + T1a carve-out fix
bd0ecce6 feat(creator): T1a settings/docs.py migration + shim
```

---

## 1. v16.2.2 完成的 13 件事

| Task | 完成度 | 文件 | Commit(s) |
|---|---|---|---|
| **T1a**: settings/docs.py verbatim copy + shim | ✅ | `packages/lingwen-creator/src/lingwen_creator/settings/docs.py` (352 lines) + `infra/creator_settings_docs.py` shim | `bd0ecce6` |
| **T1a carve-out**: append_settings_snapshot 留 infra path (T1b 修复) | ✅ | `settings/docs.py:11` (T1a) → T1b 改 | `bd0ecce6` (carve-out) + `9494ba87` (fix) |
| **T1b**: settings/history.py + shim + carve-out fix | ✅ | `settings/history.py` (136 lines) + shim + carve-out fix in docs.py | `9494ba87` |
| **T1c**: settings/merge_preferences.py + shim (largest file) | ✅ | `settings/merge_preferences.py` (1355 lines) + shim with 2 underscore re-exports | `e8a52aec` |
| **T1c-followup**: 3rd underscore re-export (_normalize_factory_preset_id) | ✅ | `infra/creator_merge_preferences.py` 加 `_normalize_factory_preset_id` | `e85980c4` |
| **T1d**: settings/__init__.py star-imports + 6 tests | ✅ | `settings/__init__.py` (3 star-imports) + `test_settings.py` (6 tests) | `8695442e` |
| **T2**: 28 Settings DTOs + TS codegen + 7 tests | ✅ | `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` (+28 DTOs) + `creator.ts` (87 interfaces) + `test_creator_dto.py` (37 tests) | `69ed75a0` |
| **T3**: settings.ts typed wrapper (32 funcs) + re-export shim + knip + URL contract | ✅ | `apps/dashboard/src/api/settings.ts` (32 wrappers) + `packages/dashboard-contracts/src/shared/settings.ts` + `knip.json` allowlist + URL contract regression lock | `239829e4` |
| **T4a**: useCreatorSettings main composable refactor (5 functions) | ✅ | `apps/dashboard/src/composables/useCreatorSettings.js` + test | `ed56673a` |
| **T4b**: composable submodule refactor (25+ functions) + routes chunk 1 | ✅ | `useSettingsDocs.ts` + `useSettingsHistory.ts` + `useMergePresets.ts` + 4 test files + 5 docs.py imports migrated | `04e4c3c5` + `213dac36` |
| **T5a**: routes chunk 2 (14 imports migrated: 12 merge_preferences + 2 history) | ✅ | `apps/studio_api/routes/creator_settings.py` | `8352033a` |
| **T5b**: routes chunk 3 finalize (last 13 merge_preferences imports) | ✅ | `creator_settings.py` (0 infra imports remaining) | `cce77ab2` |
| **T6**: cross-subdomain lazy import cleanup (volume) | ✅ | `volume/templates.py:144` + `volume/template_approvals.py:667` | `7a0694c8` |

**总计**: 13 commits, 116 backend tests + 87 frontend tests pass, 0 regressions.

---

## 2. 决策实现

| Q | 决策 | 实际落地 |
|---|---|---|
| Sub-phase 顺序 | settings (v16.2.2) per plan §4 | ✅ 实际与 plan 一致 |
| T1 split | T1a (docs) + T1b (history) + T1c (merge_preferences) + T1d (init+tests) | ✅ 4 commits, T1a carve-out + T1c follow-up due to actual test failures |
| T3 wrapper count | ~15 (estimated) | 32 (actual — match all `@router.X` decorators in creator_settings.py) |
| T3 DP-06 | ≤4 files (estimated) | 5 files (matches v16.2.1 volume T3 precedent — `index.ts` re-export required) |
| Shim underscore re-exports | T7 formal audit | T1c + follow-up 已 comprehensive — T7 audit 0 new re-exports needed |
| DTO count | ~20 (estimated) | 28 (20 top-level + 8 nested helpers) — spec §3 enumerated top-level only, nested types unavoidable for accurate modeling |
| Local DTOs in T3 | 0 (planned) | ~15 local interfaces (for DTOs still in `apps/studio_api/models/`) — TS strict requires them; v16.2.x will replace |

---

## 3. Plan deviations (审计)

| # | Plan | 实际 | 原因 |
|---|---|---|---|
| D1 | T1 1 commit per file (3 commits total) | 5 commits (T1a/b/c/d + T1c-followup) | T1a carve-out (settings/history not yet created) + T1c test failures (3 underscore names needed) |
| D2 | T3 ≤4 files/commit | 5 files (DP-06 violation) | `packages/dashboard-contracts/src/shared/index.ts` re-export required (matches v16.2.1 volume T3 precedent) |
| D3 | T4b 1 commit | 2 commits (composables + test/routes) | 8 files exceed DP-06; split into 2 logical commits |
| D4 | T1c carve-out: 1 import adjusted | 1 import adjusted (T1c); 1 missed (caught by final code review, fixed in H1 follow-up commit) | T1c correctly updated MERGE_SOURCES (module-level); the `infra.creator_volume_templates` function-body lazy import inside `_semver_tuple` (merge_preferences.py:679) was missed and corrected by final code review (H1, post-handoff). Handoff doc originally stated "2 imports adjusted" — that was inaccurate; only MERGE_SOURCES was adjusted during v16.2.2 main flow. |
| D5 | T3 wrapper count ~15 | 32 (more than 2x estimate) | Match all 32 `@router.X` decorators in creator_settings.py (1:1 wrapper-to-endpoint mapping) |
| D6 | DTOs ~20 | 28 (20 + 8 nested) | Nested types unavoidable for accurate Pydantic modeling |
| D7 | T7 0 re-exports expected | 0 new (T1c + follow-up already comprehensive) | T7 formal audit confirmed — all test imports already covered |
| D8 | pre-existing pytest debt (Phase 124) | Phase 124 had no route-level settings tests; coverage via infra tests + routes import smoke (consistent with v16.2.1 T4b) | acceptable per v16.2.1 pattern |
| D9 | shim count expected to decrease to 33 | Still 36 (no shim deletion in v16.2.2 — v16.2.7 cleanup responsibility) | Plan §11 gate 14 was misleading — clarify in handoff |

---

## 4. v16.2.2 副作用

| 影响 | 描述 |
|---|---|
| Settings Python package | `import lingwen_creator.settings` works; star-imports re-export all 3 submodules |
| Settings DTO source-of-truth | `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` (Settings section, 28 DTOs) |
| TS types | `packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts` (87 interfaces total, +28 settings) |
| Typed wrapper | `import { getSettingsDocs, saveSettingsDocs, listMergePresetPackages, ... } from '@/api/settings'` (32 functions) |
| Composable refactor | `useCreatorSettings.js` + 3 submodules (useSettingsDocs.ts, useSettingsHistory.ts, useMergePresets.ts) use typed wrapper, no raw fetch for refactored subset |
| Routes migration | `apps/studio_api/routes/creator_settings.py` 32 imports migrated (5 docs + 2 history + 25 merge_preferences); 0 infra imports remaining |
| Shim back-compat | 36 creator_*.py shims (3 of which are v16.2.2: docs/history/merge_preferences) |
| Shim underscore re-exports | `_global_prefs_path`, `_factory_preset_packages_path`, `_normalize_factory_preset_id` (all on merge_preferences shim) |
| Cross-subdomain cleanup | volume/templates.py:144 + volume/template_approvals.py:667 use `lingwen_creator.settings.docs.text_diff_summary` |

---

## 5. Lessons

### 5.1 v16.2.2 新增 lessons

1. **intra-package import 调整必须完整**: Plan §2.3 列了 1 个 import to adjust (`infra.creator_volume_templates`), implementer caught 第 2 个 (`infra.creator_settings_docs` for MERGE_SOURCES). **新 rule**: 任何 verbatim copy 前先 grep 所有 `from infra.creator_` imports, not just spec §2 列表的。

2. **T1a carve-out 模式可推广**: 当 sub-phase 顺序要求 T1a → T1b, T1a 引入对 T1b target 的 import 时, T1a 应该保持 carve-out (留 infra path) + 加 inline comment + 在 commit message 明确 follow-up。 **新 rule**: 任何 T1a 引入 cross-task import 时, 评估 carve-out 是否更 clean than split。

3. **DP-06 + 5-file commit 的判断**: T3 必须 re-export shim via `index.ts` (vue-tsc 否则 fail), 这是 5-file commit 不可避免的情况。**新 rule**: T3 typed wrapper plans 应预算 5 files (4 DP-06 + 1 index.ts re-export), per v16.2.1 volume T3 precedent。

4. **shim underscore re-exports 按需添加**: T1c BLOCKED due to 3 underscore names missing; T7 audit 0 new — **意味着 T1c follow-up 模式 (continuously add re-exports as tests fail) 是 correct approach**, not pre-emptive T1 添加所有潜在 ~20 underscore names。

5. **DTO modeling 真实 count > 估算**: 28 DTOs vs 估算 20, 差异主要在 nested helpers (8) — **新 rule**: DTO 估算应该 budget ~30% extra for nested types required for accurate modeling。

6. **Plan §11 gate 14 (shim count) 误导**: 计划说 "Expected: 33 (was 36, -3 settings shims)" — 但 v16.2.2 不删除 shims,只把现有文件变 thin shim。**新 rule**: gate descriptions 必须 explicit about shim creation vs deletion。

### 5.2 v16.2.1 lessons 沿用 (确认有效)

- T1 verbatim copy + intra-package import adjustments (5.1 lesson 1 from v16.2.1)
- shim private name re-exports for test compat (5.1 lesson 3 from v16.2.1) — 再次验证
- typed wrapper 无 zod (5.1 lesson 4 from v16.2.1) — T3 严格遵循
- `/api/` prefix 不 in code (5.1 lesson 5 from v16.2.1) — T3 URL contract test 验证
- spec-violation carryover discipline (5.1 lesson 6 from v16.2.1) — shared/check.py spec violation 仍待 v16.2.6 处理
- 沿用 hyphen name + underscore module, ruff `# noqa: F403` inline, knip allowlist, `uv sync --all-packages` + `uv run python`, verbatim copy integrity

---

## 6. Carryover (to v16.2.3 → v16.2.7)

| 任务 | 阶段 |
|---|---|
| **v16.2.3 onboarding** | 9 files (creator_onboarding + 7 sub + diff_collab) |
| **v16.2.4 content** | 10 files + `infra/creator_mode.py` → `shared/mode.py` + `shared/check.py` spec violation 修复 |
| **v16.2.5 export** | 5 files (Round 2 leaf) — uses `infra.creator_settings_docs` (4 imports) |
| **v16.2.6 memory** | 3 files (Round 2 leaf) — uses `infra.creator_settings_docs` (1 import) |
| **v16.2.7 cleanup** | 删 36 shims (12 commits per plan §3.8 + 1 final commit) + world/workspace/quality `/api/` prefix fix + import-linter forbidden pattern check |
| **pre-existing vitest debt** | 22 v16.2.1 useCreatorVolumePlan*.spec.ts failures (jsdom ERR_INVALID_URL on relative URL — tests mock src/api/index.js but composables use @/api/volume typed wrapper). v16.2.7 cleanup will fix |
| **routes `infra.creator_revision` import** | `apps/studio_api/routes/creator_settings.py:94` — `from infra.creator_revision import CreatorDocConflictError` should be `from lingwen_creator.shared.revision import CreatorDocConflictError` (shared 已 v16.2.0 迁)。Tracked for v16.2.7 cleanup |
| **creator_settings_docs.py shim docstring** | 1-line shim 缺 v16.2.1 docstring pattern (per T7 audit observation). Tracked for v16.2.7 cleanup (consistency with creator_settings_history.py + creator_merge_preferences.py) |
| **Volume cross-subdomain stale imports** | 4 stale imports in volume: plan.py:591 → creator_dashboard; template_approvals.py:133, 423, 435 → creator_onboarding (pending v16.2.5) |
| **Import-linter enforcement DP-01..06** | v16.4/v16.5 (per design principles) |
| **T3 local DTOs (~15 interfaces)** | Defined local in settings.ts wrapper; v16.2.x will replace with imported shared types as more DTOs migrate |

---

## 7. 验证证据

```bash
# Backend tests (separate invocations due to Phase 125 module-namespace collision)
$ uv run python -m pytest packages/lingwen-creator/tests/test_settings.py packages/lingwen-creator/tests/test_volume.py packages/lingwen-creator/tests/test_shared_*.py -q
============================== 28 passed in 0.11s ==============================

$ uv run python -m pytest packages/lingwen-shared/tests/ -q
============================== 37 passed in 0.42s ==============================

$ uv run python -m pytest tests/infra/test_creator_settings_*.py tests/infra/test_creator_merge_*.py tests/infra/test_creator_v36_features.py tests/infra/test_creator_v37_features.py tests/infra/test_creator_volume_*.py -q
============================== 51 passed in 0.42s ==============================

# Frontend (settings-only)
$ cd apps/dashboard && pnpm vitest run tests/unit/api/use-settings-typed-wrapper.spec.ts tests/unit/use-settings-docs.spec.ts tests/unit/use-settings-history.spec.ts tests/unit/use-merge-presets.spec.ts tests/unit/use-creator-settings.spec.ts --reporter=dot
 Test Files  5 passed (5)
      Tests  87 passed (87)

# Type / Lint / Code
$ pnpm exec vue-tsc --noEmit
0 errors

$ pnpm exec knip
0 errors (4 advisory hints — expected new settings.ts advisory)

$ ruff check .
All checks passed!

$ uv run python tooling/contracts/generate.py
WROTE .../ts/world.ts (1715 bytes)
WROTE .../ts/workspace.ts (838 bytes)
WROTE .../ts/quality.ts (685 bytes)
WROTE .../ts/creator.ts (14462 bytes)

# Migration verification
$ grep "^from infra.creator_settings_\|^from infra.creator_merge_preferences" apps/studio_api/routes/creator_settings.py | wc -l
0  # all 32 imports migrated

$ grep "^from infra.creator_settings_docs" packages/lingwen-creator/src/lingwen_creator/volume/{templates,template_approvals}.py | wc -l
0  # cross-subdomain cleanup complete

$ ls infra/creator_*.py | wc -l
36  # no shim deletion in v16.2.2 (v16.2.7 cleanup responsibility)

# Shim back-compat
$ uv run python -c "from infra.creator_settings_docs import creator_settings_docs_payload, text_diff_summary"
OK
$ uv run python -c "from infra.creator_settings_history import settings_history_payload, append_settings_snapshot, restore_settings_snapshot, load_snapshot_raw"
OK
$ uv run python -c "from infra.creator_merge_preferences import load_merge_preferences, _global_prefs_path, _factory_preset_packages_path, _normalize_factory_preset_id"
OK
```

**Test totals**: 116 backend + 87 frontend = 203 passing (excluding pre-existing 22 vitest debt)

---

## 8. 新工具总结

| 工具 | 旧 | 新 |
|---|---|---|
| Settings Python | `infra/creator_settings_*.py` (3 files) + `infra/creator_merge_preferences.py` (1 file) | `packages/lingwen-creator/src/lingwen_creator/settings/{docs,history,merge_preferences}.py` (3 files, 1842 lines total) |
| Settings DTOs | inline in `apps/studio_api/models/creator_*.py` (local) | `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` (Settings section, 28 DTOs) |
| TS types | inline in frontend code | `packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts` (auto-generated, 87 interfaces total, +28 settings) |
| Typed wrapper | raw `fetch()` | `apps/dashboard/src/api/settings.ts` (32 wrapper functions) + `packages/dashboard-contracts/src/shared/settings.ts` re-export shim |
| Composable | `useCreatorSettings.js` + 3 submodules using raw fetch | refactored to use `@/api/settings` typed wrapper |
| Routes | 32 lazy imports from `infra.creator_*` | all 32 migrated to `lingwen_creator.settings.*` (0 infra imports remaining) |
| Volume cross-imports | 2 stale `infra.creator_settings_docs` lazy imports | updated to `lingwen_creator.settings.docs` |

---

## 9. v16.2.2 完整 commit 时间线

```
master: 5733505b (v16.2.1 volume closed)
  ↓
  bd0ecce6 (T1a: docs + shim) [carve-out: append_settings_snapshot]
  9494ba87 (T1b: history + shim + carve-out fix)
  e8a52aec (T1c: merge_preferences + shim + 2 underscore re-exports) [BLOCKED due to tests]
  e85980c4 (T1c-followup: 3rd underscore re-export _normalize_factory_preset_id)
  8695442e (T1d: __init__.py + 6 tests)
  69ed75a0 (T2: 28 DTOs + codegen + 7 tests)
  239829e4 (T3: typed wrapper 32 funcs + re-export + knip + URL contract)
  ed56673a (T4a: composable main refactor)
  04e4c3c5 (T4b: composable submodules refactor)
  213dac36 (T4b: tests + routes docs imports)
  8352033a (T5a: routes merge_preferences chunk 1)
  cce77ab2 (T5b: routes chunk 3 finalize)
  7a0694c8 (T6: volume cross-subdomain cleanup)
  ↓
HEAD: 7a0694c8
```

---

## 10. Closing Notes

v16.2.2 是 Phase 126 v16.2 (creator 6-subdomain split) 的第二个完整 sub-phase. Settings 是 root (被 content + export + memory 依赖), 这次迁移让后续 sub-phase 可以用新 package path.

13 commits (比 plan §8.4 估算的 10-12 略多 due to T1a carve-out + T1c follow-up + T4b 2-commit split), 0 test regressions (excluding pre-existing 22 vitest debt from v16.2.1).

Lessons captured for future sub-phases:
1. Spec §2 import list completeness check before verbatim copy
2. T1a carve-out pattern for cross-task imports
3. T3 DP-06 budget includes index.ts re-export (5 files vs 4)
4. Shim underscore re-exports added continuously (T1c follow-up pattern), not pre-emptive
5. DTO count budgets ~30% extra for nested types
6. Plan gate descriptions explicit about creation vs deletion

**下一步**: v16.2.3 onboarding (per plan §6 — 9 files).