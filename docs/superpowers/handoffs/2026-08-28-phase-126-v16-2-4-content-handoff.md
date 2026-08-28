# Phase 126 v16.2.4 — Content Subdomain 拆分 + Onboarding T4 闭环 Handoff

> **状态**: ✅ 闭环
> **承接**:
> - `docs/superpowers/specs/2026-08-28-phase-126-v16-2-4-content-design.md` (§2 目标架构 + §3 迁移计划 + §7 lessons applied)
> - `docs/superpowers/specs/2026-08-27-phase-126-v16-2-creator-subdomain-split-design.md` (§2.1 content + §3.4 迁移计划 + §2.4 依赖矩阵)
> - `docs/superpowers/plans/2026-08-28-phase-126-v16-2-4-content-plan.md` (本 sub-phase 计划)
> - `docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-3-onboarding-handoff.md` (前置 sub-phase + 8 lessons)
> - `docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-2-settings-handoff.md` (前置 sub-phase 闭环 + 5 lessons)
> - `docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-1-volume-handoff.md` (root + 5 lessons)
> - `.lingwen/architecture.yml` (`creator` module_boundaries — Content + Mode exports added)
> **前置**: v16.2.3 (`6cfdf5c2`) onboarding + v16.2.2 (`1fb9baed`) settings + v16.2.1 (`5733505b`) volume + v16.2.0 (`5bc35f1b`) shared
> **下一步**: v16.2.5 export (5 files Round 2 leaf) + v16.2.6 memory (3 files Round 2 leaf) + v16.2.7 cleanup (36 shims + import-linter DP-01..06)

---

## 0. TL;DR

**v16.2.4 = 8 content files + 1 shared/mode.py extraction + 16 DTOs + 11 wrapper functions + 23 onboarding aliases refactored + 4 carryover closures** 迁到 `packages/lingwen-creator/src/lingwen_creator/content/` + `shared/mode.py`。

Content 是 creator 主循环的核心但**依赖模式最复杂**:
- **shared/mode.py 抽离** (T1) — 修 shared/check.py spec violation (5.1 lesson 6 from v16.2.1 闭环)
- **infra.creator_mode forward-reference 闭环** — onboarding.py 现在依赖 `lingwen_creator.content.mode` (shim)
- **跨 subdomain 依赖** — settings.docs + settings.history + settings.merge_preferences 引用 content (T7 清理)
- **infra/project_init + project_config** — creator_mode imports 迁移到 `shared.mode` (T5)

**关键事实** (实测):
- 8 content files: agent (598L) + dashboard (228L) + preferences (116L) + ui_profile (327L) + logic_check (114L) + models (61L) + batch_history (28L) + mode (shim)
- 1 shared/mode.py: CREATION_MODE_* + CreatorSettings + settings_from_project_config (cross-subdomain utility)
- 16 Content DTOs (10 spec §3.7 + 2 CreatorDashboard* + 1 ExportResponse rename + 3 settings/Mode utilities)
- 11 typed wrapper functions in `apps/dashboard/src/api/content.ts`
- 23 onboarding aliases replaced + `api/onboarding.js` shim DELETED (T6)
- 13 routes imports in `creator_core.py` migrated + 2 infra/project_X imports migrated
- 4 cross-subdomain cleanup in settings.{docs,history,merge_preferences}

**15 commits** (vs plan §3 估算 11):
```
55f9a84f style: ruff import sort auto-fix (Phase 126 v16.2.4 T8 cleanup)
8a6e0f25 fix(tests): onboarding shim mock path + delete orphan (Phase 126 v16.2.4 T8 fixup)
9fff074a fix(content): intra-package imports + shim _excerpt re-export (Phase 126 v16.2.4 T8 fixup)
392fd809 refactor(creator): Phase 126 v16.2.4 T7 — cross-subdomain cleanup (settings → docs/history/merge_preferences)
06a91169 feat(dashboard): Phase 126 v16.2.4 T6 — onboarding T4 composables refactor + delete shim
aec1dbff feat(routes): Phase 126 v16.2.4 T5 — content routes + project_X migration
e9facc1e feat(dashboard): Phase 126 v16.2.4 T4 — content typed wrapper + re-export + URL contract
b63367a1 feat(shared): Phase 126 v16.2.4 T3 — Content DTOs (16 Pydantic models) + TS codegen
3afe3c09 feat(creator): Phase 126 v16.2.4 T2d — content/ completion + tests + __init__
ee710d6d feat(creator): Phase 126 v16.2.4 T2c — content/mode.py shim + models.py migration
307afa97 feat(creator): Phase 126 v16.2.4 T2b — content/dashboard.py + logic_check.py migration
2ebb10ad feat(creator): Phase 126 v16.2.4 T2a — content/agent.py + batch_history.py migration
19e1ca03 feat(creator): Phase 126 v16.2.4 T1 — shared/mode.py extraction + spec violation fix
93ed184e docs(phase-126): v16.2.4 plan — content subdomain split + onboarding T4 closure
3f21513a docs(phase-126): v16.2.4 spec — content subdomain split + onboarding T4 closure
```

---

## 1. v16.2.4 完成的 N 件事

| Task | 完成度 | 文件 | Commit(s) |
|---|---|---|---|
| **T1**: shared/mode.py extraction + creator_mode shim + check.py fix + onboarding forward-ref close | ✅ | `packages/lingwen-creator/src/lingwen_creator/shared/{mode.py,check.py}` + `infra/creator_mode.py` (shim) + `packages/lingwen-creator/src/lingwen_creator/onboarding/onboarding.py` (forward-ref closed) | `19e1ca03` |
| **T2a**: content/agent.py (598L) + batch_history.py (28L) verbatim copy + shims | ✅ | `packages/lingwen-creator/src/lingwen_creator/content/{agent.py,batch_history.py}` + 2 shims | `2ebb10ad` |
| **T2b**: content/dashboard.py (228L) + logic_check.py (114L) verbatim copy + shims | ✅ | `packages/lingwen-creator/src/lingwen_creator/content/{dashboard.py,logic_check.py}` + 2 shims | `307afa97` |
| **T2c**: content/mode.py (shim) + content/models.py (61L) verbatim copy + shim | ✅ | `packages/lingwen-creator/src/lingwen_creator/content/{mode.py,models.py}` + 2 shims | `ee710d6d` |
| **T2d**: content/preferences.py (116L) + ui_profile.py (327L) + __init__.py 8 star-imports + test_content.py | ✅ | `packages/lingwen-creator/src/lingwen_creator/content/{preferences.py,ui_profile.py,__init__.py}` + 2 shims + 6 tests | `3afe3c09` |
| **T3**: 16 Content DTOs + TS codegen | ✅ | `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` (+16 DTOs) + `creator.ts` (auto-generated, 9068→22541 bytes) + `test_content_dto.py` | `b63367a1` |
| **T4**: content.ts typed wrapper (11 funcs) + re-export + URL contract | ✅ | `apps/dashboard/src/api/content.ts` + `packages/dashboard-contracts/src/shared/{content.ts,creator.ts}` + `use-content-typed-wrapper.spec.ts` (15 tests) | `e9facc1e` |
| **T5**: routes imports migration + project_init/project_config cleanup | ✅ | `apps/studio_api/routes/creator_core.py` (13 imports migrated) + `infra/project_init.py` + `infra/project_config.py` (2 imports migrated) | `aec1dbff` |
| **T6**: onboarding T4 composables refactor (23 aliases replaced) + delete api/onboarding.js shim + fixed 2 T3 typed wrapper defects | ✅ | `apps/dashboard/src/composables/useCreatorOnboarding*` (5 files refactored) + `apps/dashboard/src/api/{creator.js,index.js,onboarding.ts}` + `useTodayHub.js` + 4 test mocks updated + shim DELETED | `06a91169` |
| **T7**: cross-subdomain cleanup (4 settings stale imports migrated) | ✅ | `packages/lingwen-creator/src/lingwen_creator/settings/{docs.py,history.py,merge_preferences.py}` (4 lazy imports migrated to content) | `392fd809` |
| **T8 fixup A**: content intra-package imports + shim _excerpt re-export | ✅ | `packages/lingwen-creator/src/lingwen_creator/content/{dashboard.py,logic_check.py}` (intra-package) + `infra/creator_dashboard.py` shim (_excerpt) | `9fff074a` |
| **T8 fixup B**: onboarding shim mock path (6 tests) + orphan test delete | ✅ | 6 test files (patch path infra → lingwen_creator) + deleted `apps/dashboard/tests/unit/api-creator-onboarding.spec.ts` (orphan) | `8a6e0f25` |
| **T8 fixup C**: ruff import sort auto-fix (22 violations across 10 files) | ✅ | 8 infra shim files + 2 test files (ruff --fix I001) | `55f9a84f` |

**总计**: 12 implementation commits (T1-T7 + 3 fixups) + 2 doc commits (spec + plan) = **15 commits**.

---

## 2. 决策实现

| Q | 决策 | 实际落地 |
|---|---|---|
| **Q1** mode placement | shared/mode.py (per plan §5) | ✅ shared/mode.py is cross-subdomain utility (settings + onboarding + content all use), content/mode.py is shim re-export |
| **Q2** agent.py 单文件 | 单文件 verbatim (precedent digest_schedule.py 526L) | ✅ agent.py 598L verbatim copy (largest single-file migration in v16.2.x) |
| **Q3** infra/creator_mode.py | 变 shim (precedent v16.2.1..3) | ✅ T1 + T2c both NO-OP for creator_mode (already shim from v16.2.2; v16.2.4 closes it as content/mode.py shim) |
| **Q4** task granularity | 8 commits (T1-T8) | ✅ Actual 12 implementation commits (T1 + T2a-d + T3-T7 + 3 fixups) — T2 split into 4 sub-commits per DP-06 (agent.py 598L needs separate commit for review hygiene) |
| **Q5** onboarding T4 composables | 绑到 v16.2.4 做 | ✅ T6 refactor + shim delete + bonus 2 T3 typed wrapper defects fix (applyWizardShareDone + dispatchDigestNow ignored args) |

---

## 3. Plan deviations (审计)

| # | Plan | 实际 | 原因 |
|---|---|---|---|
| **D1** | T2 1 commit | 4 commits (T2a-d) | DP-06 compliance — agent.py 598L + 7 other files in T2 = 8 files > DP-06 4-file budget. T2 split per file-group semantic boundaries (agent+batch_history / dashboard+logic_check / mode+models / preferences+ui_profile) |
| **D2** | infra.creator_mode.py 变 shim (precedent v16.2.1..3) | ✅ Exactly per plan | No deviation |
| **D3** | T6 onboarding T4 composables | ✅ Refactored 5 files + bonus: deleted 23-aliases shim + fixed 2 latent T3 typed wrapper bugs | Spec scope expansion during T6 — discovered typed wrapper params forwarding bugs while refactoring composables. Per v16.2.2 §5.1 lesson 7 (ALWAYS check function-body lazy imports after verbatim copy) analogue: refactoring composables requires checking typed wrapper body/param forwarding |
| **D4** | T8 = handoff doc only | 3 commits (intra-package fixup + test fixup + ruff fixup) | Verification gates discovered 3 classes of fixup needs: (a) my v16.2.4 actual regression in content/dashboard.py + logic_check.py (verbatim copy preserved `from infra.creator_ui_profile`); (b) v16.2.3 onboarding regression in 6 test patches (mocks targeted shim, production reads from real module); (c) 22 ruff I001 violations from accumulated import drift. Each commit scoped to single concern |
| **D5** | shim count 36 → 28 | **36 → 36** | Plan §5 Q3 was misleading: converting existing `infra.creator_X.py` (full impl) → shim doesn't add count. v16.2.4 added 9 new shims (creator_mode was already shim from v16.2.2; 8 new content shims created from full impls = net 0). Same lesson as v16.2.3 §5.1 lesson 2 |
| **D6** | v16.2.3 carryover (4 closures) | ✅ ALL 4 closed | (a) onboarding forward-ref → closed in T1; (b) shared/check.py spec violation → closed in T1; (c) infra/project_X imports of creator_mode → closed in T5; (d) onboarding T4 composables + shim → closed in T6 |
| **D7** | T7 cross-subdomain | **4 stale imports** (vs plan estimated 2) | T7 found more stale imports than plan estimated: volume/templates.py:144 + volume/template_approvals.py:667 (carryover from v16.2.2 §6 closed in v16.2.3 T6) + 2 NEW in settings/{docs,history,merge_preferences}.py that v16.2.2 didn't catch because content wasn't migrated then |
| **D8** | pre-existing pytest/vitest debt | Same — 22 vitest + Phase 125 module-namespace | acceptable per Phase 125 + v16.2.1 baselines |

---

## 4. v16.2.4 副作用

| 影响 | 描述 |
|---|---|
| Content Python package | `import lingwen_creator.content` works; star-imports re-export all 8 submodules + 9 content functions |
| shared/mode.py extraction | `from lingwen_creator.shared.mode import CreatorSettings, CREATION_MODE_*, settings_from_project_config, resolve_creator_settings` works cross-subdomain (settings + onboarding + content all use) |
| Content DTO source-of-truth | `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` (Content section, 16 DTOs, 9068→22541 bytes) |
| TS types | `packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts` (140 interfaces total, +16 content) |
| Typed wrapper (new) | `import { fetchCreatorOverview, saveCreatorChapterOutline, ... } from '@/api/content'` (11 functions) |
| Routes migration | `apps/studio_api/routes/creator_core.py` 13 imports migrated (0 infra.creator_content_* imports remaining) |
| Project init migration | `infra/project_init.py` + `infra/project_config.py` 2 creator_mode imports migrated to `shared.mode` (resolves circular init) |
| Onboarding T4 closure | 23 onboarding aliases replaced + `apps/dashboard/src/api/onboarding.js` shim DELETED (was 73 lines, replaced by direct typed wrapper imports in 5 composable files) |
| Cross-subdomain | settings/{docs,history,merge_preferences}.py 4 stale `infra.creator_*` imports migrated to `lingwen_creator.content.*` |
| Spec violation fix | `shared/check.py` no longer imports `infra.creator_mode` (was 5.1 lesson 6 from v16.2.1 carryover) |
| Forward-reference close | `onboarding/onboarding.py` no longer forward-references `infra.creator_mode` (v16.2.3 T1c carryover closed) |
| Typed wrapper defects fixed | `applyWizardShareDone` + `dispatchDigestNow` now correctly forward body/query params (were silently dropped in v16.2.3 T3) |
| Orphan test delete | `apps/dashboard/tests/unit/api-creator-onboarding.spec.ts` deleted (was testing deleted shim, causing vue-tsc errors) |
| Ruff cleanup | 22 I001 violations across 10 files auto-fixed (shim star-import + explicit import block sort) |
| Shim count | 36 (no change — converting existing full impls to shims doesn't add count, per D5) |

---

## 5. Lessons

### 5.1 v16.2.4 新增 lessons

1. **Intra-package imports after verbatim copy (extends v16.2.2 lesson 7)**: When migrating files that import from sibling subdomain files (now also being migrated), the verbatim copy preserves `from infra.creator_X` paths. These must be rewritten to `from lingwen_creator.<subdomain>.X` (spec §12.2). Failure mode: import cycle via shim (shim loads from new module → new module imports from old infra shim → still loading → partial init). Future T2 tasks must grep for `from infra.creator_` in source files being migrated, not just in target migration list.

2. **Shim mocks don't propagate through `from X import Y` lazy imports** (v16.2.3 T1a regression discovered in v16.2.4 verification): When production code does `from lingwen_creator.X import func` (lazy) and tests do `patch("infra.creator_X.func", mock)`, the mock does NOT propagate because shim and real module have separate `__dict__`. PEP 562 `__getattr__` proxy doesn't work because Python modules don't honor `__setattr__` for direct `setattr()` calls. Test patches MUST target the real module path that production reads from. This bug class lurks in 6 tests from v16.2.3 T1a; future `from infra.X import` migrations must grep test patches and update them.

3. **Composable refactor scope expansion when shim is deleted**: T6 plan estimated "5 composable files + delete shim". Actual scope: 5 composables + creator.js re-export + index.js 19 legacy aliases + useTodayHub.js cross-cutting + 4 test mocks + 2 typed wrapper bug fixes. Plan underestimated by ~6 files. Future T-shim-delete tasks should budget for cross-cutting fixes.

4. **Typed wrapper params forwarding is fragile**: v16.2.3 T3 introduced `applyWizardShareDone` and `dispatchDigestNow` typed wrappers that silently dropped their body/query params (called endpoint with empty payload). Bug surfaced only when T6 refactored composables to use them directly. Recommendation: typed wrappers should use a single helper `requestWithParams(method, path, params)` that explicitly constructs URL/body, avoiding silent arg drops.

5. **Orphan test files linger after shim deletion**: T6 deleted `api/onboarding.js` but `tests/unit/api-creator-onboarding.spec.ts` (testing that shim) remained — causing vue-tsc errors until manual deletion. Future shim-deletion tasks must `grep -r "<shim-path>" tests/` to find orphan tests before deletion.

### 5.2 v16.2.1..3 lessons 沿用 (确认有效)

- T1 verbatim copy + intra-package import adjustments (5.1 lesson 1 from v16.2.1) — D1 deviation traced back to needing this for 8-file T2
- shim private name re-exports for test compat (5.1 lesson 3 from v16.2.1) — `_excerpt` re-export added in T8 fixup A
- typed wrapper 无 zod (5.1 lesson 4 from v16.2.1) — T4 严格遵循 (11 wrappers, no zod)
- `/api/` prefix 不 in code (5.1 lesson 5 from v16.2.1) — T4 URL contract test 验证 11 wrappers (0 violations)
- spec-violation carryover discipline (5.1 lesson 6 from v16.2.1) — `shared/check.py` + `onboarding/onboarding.py` both closed
- forward-reference pattern for not-yet-migrated subdomains (5.3 from v16.2.3) — used in T2c content/mode.py shim
- hyphen name + underscore module, ruff `# noqa: F401` inline, knip allowlist, `uv sync --all-packages` + `uv run python`, verbatim copy integrity
- DP-06 ≤4 files/commit — D1 deviation justified (T2 = 8 files > 4)

### 5.3 Spec §12.2 — Intra-package import pattern (final form)

```python
# WRONG (verbatim copy):
from infra.creator_ui_profile import filter_deviations_by_min_severity

# CORRECT (intra-package):
from lingwen_creator.content.ui_profile import filter_deviations_by_min_severity
```

Pattern: never cross subdomain via `infra.X` from inside `lingwen_creator.*`. Always use the new package path for sibling submodule imports. `infra.X` is reserved for cross-boundary consumers (routes, scripts, etc.).

---

## 6. Carryover to v16.2.5+

| 任务 | 阶段 | 来源 |
|---|---|---|
| **v16.2.5 export** | 5 files (common + docx + epub + publish + publish_adapters) — Round 2 leaf | per plan §7 |
| **v16.2.6 memory** | 3 files (annotations + assets + query) — Round 2 leaf | per plan §7 |
| **v16.2.7 cleanup** | 36 shim deletions + 4 typed wrapper `/api/` prefix fix (world/workspace/quality + onboarding from v16.2.3) + 22 vitest debt + import-linter DP-01..06 | per plan §9 |
| **Content composables (19)** | useCreatorAgent + useCreatorDashboard + useCreatorLogicCheck + useCreatorPreferences + useCreatorUiProfile (per spec §3.7) — refactor deferred to v16.2.7 | T6 partial (only onboarding T4 in scope) |
| **4 unwired Content DTOs** | CreatorDashboardOverview + CreatorDashboardChapterPreview + CreatorUiProfileState (embedded as field) + CreatorUiProfileSaveRequest — wrap when endpoints land | T3 spec §3.7 listed 10 but 4 not wired |
| **typed wrapper path bug** | `fetchDiffCollabNotes`/`saveDiffCollabNotes` hit `/creator/onboarding/diff-collab-notes` (doesn't exist) — should be `/creator/diff-collab-notes` | T4 URL contract tests didn't catch this because endpoints aren't implemented yet (404 expected) — Phase 127+ fix |
| **`api/onboarding.js` shim** | ✅ DELETED in T6 — no carryover | resolved |
| **`apps/dashboard/src/api/onboarding.ts` typed wrapper defects** | ✅ FIXED in T6 (applyWizardShareDone + dispatchDigestNow) | resolved |
| **Pre-existing vitest debt** | 22 v16.2.1 `useCreatorVolumePlan*.spec.ts` failures — unchanged | v16.2.7 cleanup |

---

## 7. 验证证据

```bash
# Backend tests (separate invocations due to Phase 125 module-namespace collision)
$ /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/ -q
============================== 63 passed in 0.26s ==============================

$ /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ -q
============================== 66 passed in 0.45s ==============================

$ /home/ailearn/miniconda3/bin/python -m pytest tests/infra/test_creator_*.py -q
============================= 241 passed in 12.75s =============================

# Frontend (full dashboard)
$ cd apps/dashboard && pnpm vitest run --reporter=dot
 Test Files  4 failed | 217 passed (221)
      Tests  22 failed | 1778 passed | 1 skipped (1801)
# 22 failures all in useCreatorVolumePlan* (pre-existing v16.2.1 debt, unchanged)

# Type / Lint / Code
$ pnpm exec vue-tsc --noEmit
0 errors

$ pnpm exec knip
0 errors (5 unrelated hints — settings.ts + content.ts + dashboard-contracts + router/routes.js + main.js)

$ ruff check .
All checks passed!

$ /home/ailearn/miniconda3/bin/python tooling/contracts/generate.py
WROTE .../ts/creator.ts (22541 bytes) — was 9068 (v16.2.1), +13473 from 16 content DTOs

$ /home/ailearn/miniconda3/bin/python tooling/contracts/zod_revalidate.py --openapi /tmp/openapi.json
zod reverse validation OK (no drift detected)

# Carryover closure verification
$ grep -cE "infra\.creator_mode" packages/lingwen-creator/src/lingwen_creator/onboarding/onboarding.py
0  # forward-reference closed (T1)

$ grep -cE "infra\.creator_mode" packages/lingwen-creator/src/lingwen_creator/shared/check.py
0  # spec violation fixed (T1)

$ grep -cE "infra\.creator_mode" infra/project_init.py infra/project_config.py
infra/project_init.py:0
infra/project_config.py:0
# project_X migrated (T5)

$ ls apps/dashboard/src/api/onboarding.js
ls: cannot access ...: No such file or directory
# shim deleted (T6)

$ grep -cE "infra\.creator_(agent|dashboard|logic_check|batch_history|models|preferences|ui_profile)" apps/studio_api/routes/creator_core.py
0  # routes migrated (T5)

$ ls packages/lingwen-creator/src/lingwen_creator/content/*.py | wc -l
9  # 8 modules + __init__.py

# Shim back-compat (sample)
$ /home/ailearn/miniconda3/bin/python -c "from infra.creator_dashboard import creator_overview, creator_chapter_preview"
OK

$ /home/ailearn/miniconda3/bin/python -c "from infra.creator_agent import run_creator_agent_plan, iter_creator_agent_plan_stream"
OK

$ /home/ailearn/miniconda3/bin/python -c "from infra.creator_mode import CreatorSettings, CREATION_MODE_ADVANCE, settings_from_project_config"
OK
```

**Test totals**: 63 creator pkg + 66 shared pkg + 241 infra = **370 backend passing**, 1778 frontend passing. 0 regressions (excluding pre-existing 22 vitest debt).

---

## 8. 新工具总结

| 工具 | 旧 | 新 |
|---|---|---|
| Content Python | `infra/creator_{agent,batch_history,dashboard,logic_check,mode,models,preferences,ui_profile}.py` (8 files, 1502 lines) | `packages/lingwen-creator/src/lingwen_creator/content/` (8 files, 1502 lines verbatim copy) + 8 1-line shims in `infra/` |
| shared/mode.py extraction | inline in `infra/creator_mode.py` (creator-specific) | `packages/lingwen-creator/src/lingwen_creator/shared/mode.py` (cross-subdomain utility — settings + onboarding + content all use) |
| Content DTOs | inline in `apps/studio_api/models/creator_core.py` (local) | `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` (Content section, 16 DTOs) |
| TS types | inline in frontend code | `packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts` (auto-generated, 140 interfaces total, +16 content) |
| Typed wrapper (new) | n/a | `apps/dashboard/src/api/content.ts` (11 wrapper functions) + `packages/dashboard-contracts/src/shared/content.ts` re-export shim |
| Onboarding typed wrapper | via `api/onboarding.js` shim with 21 Creator-prefixed aliases | direct import from `@/api/onboarding` (23 aliases removed, 2 T3 defects fixed) |
| Routes | 13 lazy imports from `infra.creator_*` + 2 from `infra.creator_mode` in project_init/config | all 15 migrated to `lingwen_creator.content.*` + `lingwen_creator.shared.mode` (0 infra imports remaining) |
| Cross-subdomain | settings.{docs,history,merge_preferences}.py 4 stale `infra.creator_*` imports | all 4 migrated to `lingwen_creator.content.*` |
| Spec violation | `shared/check.py` depends on `infra.creator_mode.CreatorSettings` (5.1 lesson 6 violation) | depends on `lingwen_creator.shared.mode.CreatorSettings` (intra-package, no boundary cross) |

---

## 9. v16.2.4 完整 commit 时间线

```
master: 6cfdf5c2 (v16.2.3 onboarding closed)
  ↓
  3f21513a (spec: content subdomain split + onboarding T4 closure)
  93ed184e (plan: content subdomain split + onboarding T4 closure)
  ↓
  19e1ca03 (T1: shared/mode.py extraction + spec violation fix + forward-ref close)
  2ebb10ad (T2a: content/agent.py + batch_history.py verbatim copy)
  307afa97 (T2b: content/dashboard.py + logic_check.py verbatim copy)
  ee710d6d (T2c: content/mode.py shim + models.py verbatim copy)
  3afe3c09 (T2d: content/preferences.py + ui_profile.py + __init__.py + tests)
  b63367a1 (T3: 16 Content DTOs + TS codegen)
  e9facc1e (T4: content.ts typed wrapper + re-export + URL contract tests)
  aec1dbff (T5: 13 routes imports + 2 project_X imports migration)
  06a91169 (T6: onboarding T4 composables refactor + delete shim + fix 2 T3 defects)
  392fd809 (T7: 4 settings stale imports cross-subdomain cleanup)
  ↓
  9fff074a (T8 fixup A: content intra-package imports + shim _excerpt re-export)
  8a6e0f25 (T8 fixup B: 6 onboarding test mock paths + delete orphan test)
  55f9a84f (T8 fixup C: ruff import sort auto-fix 22 violations)
  ↓
HEAD: 55f9a84f
```

Total: 15 commits (2 doc + 10 T1-T7 + 3 T8 fixups) vs plan §3 estimate of 11.

---

## 10. Closing Notes

v16.2.4 content 是 Phase 126 v16.2 creator 6-subdomain split 的第四个 sub-phase. Content 是 creator 主循环的核心但**依赖模式最复杂**:
- shared/mode.py 抽离 (cross-subdomain utility, 修了 5.1 lesson 6 carryover)
- infra.creator_mode forward-reference 闭环 (v16.2.3 T1c carryover closed)
- infra/project_X 迁移 (修了 init circular)
- 4 cross-subdomain cleanup in settings (T7)

12 implementation commits 估算 (vs plan §3 估算 11), deviation 主因:
- T2a-d split (4 vs 1 planned) — DP-06 compliance for 8-file T2
- 3 T8 fixup commits — verification discovered 3 classes of fixup needs (intra-package import cycle, v16.2.3 test mock regression, ruff import drift)
- T6 scope expansion — onboarding T4 refactor + 2 typed wrapper defects fix + 4 test mock updates

**4 carryover closures** (vs plan §6):
1. onboarding forward-reference to infra.creator_mode (T1)
2. shared/check.py spec violation (T1)
3. infra/project_init + infra/project_config imports of infra.creator_mode (T5)
4. onboarding T4-partial composables + api/onboarding.js shim (T6)

0 test regressions (excluding pre-existing 22 vitest debt from v16.2.1 + Phase 125 module-namespace issue).

Next session entry: v16.2.5 export (5 files Round 2 leaf) + v16.2.6 memory (3 files Round 2 leaf) + v16.2.7 cleanup (final shim deletion + import-linter enforcement).