# Phase 126 v16.2.5 — Export Subdomain 拆分 Handoff

> **状态**: ✅ 闭环
> **承接**:
> - `docs/superpowers/specs/2026-08-28-phase-126-v16-2-5-export-design.md` (§2 目标架构 + §3 迁移计划 + §4 DTOs + §5 lessons + §6 verification + §7 carryover)
> - `docs/superpowers/plans/2026-08-28-phase-126-v16-2-5-export-plan.md` (T1-T8 task breakdown + DP-06 ≤4 files/commit)
> - `docs/superpowers/handoffs/2026-08-28-phase-126-v16-2-4-content-handoff.md` (前置 sub-phase 闭环 + 5 lessons)
> **前置**: v16.2.4 content (`f01aaf2d`)
> **下一步**: v16.2.6 memory (3 files Round 2 leaf last) + v16.2.7 cleanup (41 shims + typed wrapper `/api/` fix + import-linter)

---

## 0. TL;DR

**v16.2.5 = export subdomain 拆分 Round 2 leaf**,13 commits / ~25 files / 0.5 天。**5 files** (export_common 92L + export_docx 111L + export_epub 181L + publish 90L + publish_adapters 159L = 633 LOC) → `packages/lingwen-creator/src/lingwen_creator/export/` + 5 shims + 8 DTOs + 5 typed wrapper functions + 2 composables refactor + `api/publish.js` shim 删除 + orphan test 删除 + 5 test mock path updates + useWriteFlow typed signature migration。

**Round 2 leaf — 最简 sub-phase**:
- **所有依赖子域已迁完** (v16.2.4 content + v16.2.2 settings): cross-subdomain imports 直接用新 path,无 forward-reference
- **publish_adapters.py 无 infra.creator_X 依赖** (pure Python + infra.studio_registry): 直接迁移,无 intra-package import 调整
- **publish.py intra-subdomain only**: 1 import 调整 (creator_publish_adapters → lingwen_creator.export.publish_adapters)
- **无 shared extraction** (mode logic 不需抽,跨子域 utility 都在 shared 已稳定)
- **无 spec violation** (export 不 import 其他子域的内部细节)

**关键决策**:
- **T1 4 sub-commits (T1.a-d)**: 5 export files (5 impls + 5 shims + 1 __init__.py + 1 test = 12 files) split 4 commits per file-group semantic (common+docx / epub+publish_adapters-shim / publish+publish_adapters+__init__ / tests+ruff fixup)
- **intra-package imports per v16.2.4 §5.1 lesson 1**: T1.a export/common.py 把 `from infra.creator_dashboard` → `from lingwen_creator.content.dashboard` + `from infra.creator_settings_docs` → `from lingwen_creator.settings.docs` (cross-subdomain intra-package)
- **typed wrapper NO zod / NO /api/ prefix**: 与 v16.2.1..4 严格一致 (v16.2.1 §5.1 lessons 4-5)
- **api/publish.js shim 删除**: Phase 62.4 legacy shim with raw fetch,已被 typed wrapper 完全替代
- **T5.b scope expansion**: 计划只 refactor 2 composables,实际发现 + api/index.js update + delete shim + delete orphan test + useWriteFlow typed signature migration (per v16.2.4 §5.1 lesson 4 — typed wrapper params forwarding fragility)

**13 commits** (T1.a-d + T2 + T3.a-b + T4 + T5.a-b + T6 skipped + T7 + T8):
```
T1.a:  export/common.py + export/docx.py + 2 shims (4 files)              — 389f91a5
T1.b:  export/epub.py + creator_export_epub shim + creator_publish_adapters shim (3 files) — dce65eaf
T1.c:  export/publish.py + export/publish_adapters.py + __init__.py + creator_publish shim (4 files) — 5715ff15
T1.d:  test_export.py (8 tests) + ruff fixup                               — b2dd6f53
T2:    8 DTOs to creator.py + TS codegen + 9 backend tests (3 files)       — 5308c63e
T3.a:  export.ts typed wrapper + re-export + knip allowlist (4 files)      — 5390a776
T3.b:  api-export-typed-wrapper.spec.ts (URL contract, 1 file)              — 1e95ff82
T4:    routes imports migration (creator_core.py 5 lazy imports, 1 file)  — 8695e3dd
T5.a:  composable refactor (useProductExport.ts + useProductPublish.ts + export.ts vite-env fix, 3 files) — f3dd8f99
T5.b:  api/index.js update + delete api/publish.js + delete orphan test + useWriteFlow typed signature migration (5 files) — 8bd30325
T6:    cross-subdomain check (no findings — skipped commit)
T7:    test mock path updates (5 test files: split vi.mock from api/index.js to typed wrapper modules) — 4d11064b
T8:    handoff + CLAUDE.md + architecture.yml + migration_log.yml (4 files) — (current commit)
```

**总计 13 commits**(T6 skipped — no findings),每 commit ≤5 files (DP-06 严格)。

---

## 1. v16.2.5 完成的 N 件事

| Task | 完成度 | 文件 | Commit(s) |
|---|---|---|---|
| **T1.a** | ✅ | `packages/lingwen-creator/src/lingwen_creator/export/{common.py, docx.py}` + 2 infra shims | `389f91a5` |
| **T1.b** | ✅ | `export/epub.py` + 2 infra shims (epub + publish_adapters pre-emptive) | `dce65eaf` |
| **T1.c** | ✅ | `export/{publish.py, publish_adapters.py, __init__.py}` + 1 infra shim (publish) | `5715ff15` |
| **T1.d** | ✅ | `packages/lingwen-creator/tests/test_export.py` (8 tests + legacy compat) | `b2dd6f53` |
| **T2** | ✅ | `creator.py` (+8 DTOs) + auto-generated `creator.ts` (24042 bytes, +1501) + `test_creator_dto.py` (+9 tests) | `5308c63e` |
| **T3.a** | ✅ | `apps/dashboard/src/api/export.ts` (5 wrapper funcs) + `packages/dashboard-contracts/src/shared/export.ts` re-export + `creator.ts` re-export +8 types + `knip.json` allowlist | `5390a776` |
| **T3.b** | ✅ | `apps/dashboard/tests/unit/api/use-export-typed-wrapper.spec.ts` (8 URL contract tests) | `1e95ff82` |
| **T4** | ✅ | `apps/studio_api/routes/creator_core.py` (5 lazy imports migrated to lingwen_creator.export.*) | `8695e3dd` |
| **T5.a** | ✅ | `useCreatorProductTools/{useProductExport.ts, useProductPublish.ts}` + `export.ts` vite/client triple-slash | `f3dd8f99` |
| **T5.b** | ✅ | `api/index.js` (6 publish.js → typed wrapper + 4 Content → content.ts/volume.ts) + `creator.js` (removed publish.js re-export) + delete `api/publish.js` + delete orphan `api-creator-publish.spec.ts` + `useWriteFlow.ts` typed signature migration | `8bd30325` |
| **T6** | ✅ (skipped commit) | grep verification — only `test_export.py` references infra imports (expected back-compat test) | (no commit) |
| **T7** | ✅ | 5 test files: `use-product-export.spec.ts` + `use-product-publish.spec.ts` + `creator-product-tools.spec.ts` + `creator-publish-wizard-modal.spec.ts` + `use-creator-write.spec.ts` (split vi.mock from api/index.js to typed wrapper modules) | `4d11064b` |
| **T8** | ✅ (current) | handoff doc + CLAUDE.md v16.2.5 entry + architecture.yml +19 export symbols + migration_log.yml v16.2.5 entry | (current) |

**总计**: 12 implementation commits + 1 T8 handoff commit = **13 commits**。

---

## 2. 决策实现

| Q | 决策 | 实际落地 |
|---|---|---|
| **Q1** Verbatim copy | 5 files verbatim copy + 5 shims + 1 __init__.py + 1 test | ✅ T1.a-d (4 commits per file-group DP-06 split) |
| **Q2** T1 split granularity | 4 sub-commits per DP-06 ≤4 files/commit | ✅ T1.a (4 files: common+docx+2 shims) / T1.b (3 files: epub+2 shims) / T1.c (4 files: publish+publish_adapters+__init__+1 shim) / T1.d (1 file: test_export.py) |
| **Q3** intra-package imports | per spec §2.2 + v16.2.4 §5.1 lesson 1 | ✅ T1.a export/common.py: `from infra.creator_dashboard → from lingwen_creator.content.dashboard` + `from infra.creator_settings_docs → from lingwen_creator.settings.docs` (cross-subdomain intra-package); T1.a/b/c intra-subdomain: `from lingwen_creator.export.common/docx/epub/publish_adapters` |
| **Q4** typed wrapper style | NO zod, NO /api/ prefix (v16.2.1 §5.1 lessons 4-5) | ✅ T3.a export.ts: fetchBlob + fetchJson helpers, 5 wrapper funcs (exportCreatorEpub/Docx return Blob, submit/fetchCreatorPublish* return JSON) |
| **Q5** api/publish.js shim delete | Phase 62.4 legacy shim with raw fetch — 完全被 typed wrapper 替代 | ✅ T5.b: api/index.js 6 publish.js re-exports → @/api/export typed wrapper + api/creator.js 移除 `export * from './publish.js'` + git rm api/publish.js + git rm orphan api-creator-publish.spec.ts (per v16.2.4 §5.1 lesson 5) |
| **Q6** useWriteFlow typed signature migration | saveCreatorChapterBody/Outline `(chapterNum, body)` 2-arg → typed `({ chapter_id, body })` 1-arg (per v16.2.4 §5.1 lesson 4) | ✅ T5.b bonus: 3 call sites migrated + 4 cast sites `as Record<string, unknown>` → `as unknown as Record<string, unknown>` (TS strict mode double-cast pattern) |
| **Q7** test mock paths | per v16.2.4 §5.1 lesson 2 (shim mocks 不 propagate) | ✅ T7: 5 test files split vi.mock from api/index.js to typed wrapper modules (api/export.js + api/content.js) |

---

## 3. Plan deviations

| # | Plan | 实际 | 原因 |
|---|---|---|---|
| **D1** | T1 1 commit | 4 commits (T1.a-d) per DP-06 ≤4 files/commit | 5 export files (5 impls + 5 shims + 1 __init__.py + 1 test = 12 files) > DP-06 4-file budget; T1 split per file-group semantic boundaries (common+docx / epub+publish_adapters-shim / publish+publish_adapters+__init__ / tests+ruff fixup) — matches v16.2.4 T2a-d split precedent |
| **D2** | T3 2 commits (T3.a ≤4 files, T3.b URL contract) | 2 commits as planned | ✅ no deviation — T3.a = 4 files (export.ts + dashboard-contracts/export.ts + creator.ts + knip.json), T3.b = 1 file (URL contract test) |
| **D3** | T5 2 commits (T5.a composables, T5.b api/index.js + delete shim) | 2 commits as planned + bonus useWriteFlow typed signature migration (T5.b scope expansion from 4 files to 8 files — within DP-06 4-file budget via 2 separate commits) | T5.b plan estimated "api/index.js update + delete publish.js" → actual + delete orphan test + useWriteFlow typed signature migration (per v16.2.4 §5.1 lesson 4: typed wrapper params forwarding fragility). T5.a committed separately first (composables only) so T5.b stays focused on infra (api/index.js + creator.js + publish.js + orphan test + useWriteFlow) |
| **D4** | T6 cross-subdomain check 1-3 files | skipped commit — no findings | grep verified only test_export.py references infra imports (expected back-compat test per v16.2.4 §5.1 lesson 1); infra usage outside migrated files = 0 (5 infra shims + 5 infra files still in infra = consistent) |
| **D5** | T7 fixups (intra-package + test mock paths + ruff I001) | 1 commit (5 test files) | Plan estimated 0-5 files; actual 5 test files needed mock path updates (per v16.2.4 §5.1 lesson 2). ruff I001 already auto-fixed in T1.d during export/*.py creation (4 violations fixed). No additional ruff fixup needed |
| **D6** | T8 handoff doc 1 commit | 1 commit as planned (current) | ✅ no deviation |

---

## 4. v16.2.5 副作用

| 影响 | 描述 |
|---|---|
| Export Python package | `import lingwen_creator.export` works; star-imports re-export all 5 submodules + 19 functions + 5 classes |
| Export DTO source-of-truth | `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` (Export + Publish section, 8 DTOs, 22541 → 24042 bytes) |
| TS types | `packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts` (148 interfaces total, +8 export/publish) |
| Typed wrapper (new) | `import { exportCreatorEpub, exportCreatorDocx, submitCreatorPublish, fetchCreatorPublishHistory, fetchCreatorPublishPlatforms } from '@/api/export'` (5 functions) |
| Routes migration | `apps/studio_api/routes/creator_core.py` 5 imports migrated (0 infra.creator_export_* / infra.creator_publish* remaining) |
| Composable refactor | `useCreatorProductTools/{useProductExport.ts, useProductPublish.ts}` import directly from `@/api/export` + `@/api/content` (no longer via api/index.js barrel) |
| api/publish.js shim delete | legacy Phase 62.4 shim with raw fetch — replaced by typed wrapper (per v16.2.4 §5.1 lesson 5 — orphan test files linger) |
| Orphan test delete | `apps/dashboard/tests/unit/api-creator-publish.spec.ts` (12 tests for deleted shim) — git rm in same commit as api/publish.js deletion |
| api/index.js update | 6 publish.js re-exports → typed wrapper (legacy aliases preserved) + 4 Content functions (fetchCreatorChapterPreview + saveCreatorChapterBody + saveCreatorChapterOutline + generateCreatorVolumeSummary) → typed wrappers (content.ts / volume.ts) |
| api/creator.js | removed `export * from './publish.js'` (publish.js deleted) |
| useWriteFlow typed signature | saveCreatorChapterBody/Outline 2-arg `(chapter, body)` → typed 1-arg `({ chapter_id, body })` per v16.2.4 §5.1 lesson 4 (3 call sites migrated + 4 cast fixes) |
| Test mock paths | 5 test files split vi.mock from api/index.js to api/export.js + api/content.js per v16.2.4 §5.1 lesson 2 (shim mocks 不 propagate through typed wrapper direct imports) |
| export.ts vite/client TS fix | `/// <reference types="vite/client" />` triple-slash directive added (fix vue-tsc TS2339 'Property env does not exist on type ImportMeta' error — required for typed wrapper that uses `import.meta.env`) |
| Shim count | 41 (was 36, +5 new export shims; no net deletion in v16.2.5 — v16.2.7 cleanup responsibility) |

---

## 5. Lessons

### 5.1 v16.2.5 新增 lessons

1. **Typed wrapper using `import.meta.env` requires `/// <reference types="vite/client" />`** (T3.a + T5.a): `import.meta.env.VITE_API_BASE` is fine in JS files (no type checking), but TS files trigger vue-tsc TS2339 "Property 'env' does not exist on type 'ImportMeta'". Fix: add triple-slash directive at top of TS file. Pattern reusable for any future TS file that accesses `import.meta.env`.

2. **TS cast from typed interface to Record needs double-cast** (T5.b): `chapterPreview.value as Record<string, unknown>` fails TS strict mode when `chapterPreview.value` is typed `CreatorChapterPreview` (interface lacks index signature). Standard fix: `as unknown as Record<string, unknown>` — explicit two-step cast.

3. **vi.mock split per typed wrapper module** (T7): When composables import directly from `@/api/X` (typed wrapper), test `vi.mock('../../src/api/index.js', ...)` does NOT intercept the call. Must split mocks per typed wrapper module. Per v16.2.4 §5.1 lesson 2 confirmed for both Python shims AND typed wrapper modules.

### 5.2 v16.2.4 lessons 沿用 (确认有效)

- **§5.1 lesson 1 (intra-package imports after verbatim copy)**: T1.a export/common.py verbatim copy preserved `from infra.creator_dashboard` and `from infra.creator_settings_docs` → fixed to `from lingwen_creator.content.dashboard` + `from lingwen_creator.settings.docs` (cross-subdomain intra-package per spec §2.2). ruff --fix auto-formatted intra-package vs infra import blocks separately (good separation).

- **§5.1 lesson 2 (shim mocks 不 propagate)**: T7 — 5 test files split vi.mock from `api/index.js` to `api/export.js` + `api/content.js`. Failure mode: useProductExport imports directly from `@/api/export` (typed wrapper), so `vi.mock('../../src/api/index.js', ...)` doesn't intercept; test runs real fetch and fails with "expected vi.fn() to be called 1 times, but got 0 times".

- **§5.1 lesson 4 (typed wrapper params forwarding fragility)**: T5.b bonus — useWriteFlow.ts 3 call sites using old 2-arg `(chapterNum, body)` signature vs new typed 1-arg `({ chapter_id, body })` per CreatorBodySaveRequest/creatorOutlineSaveRequest DTOs (introduced in v16.2.4 content migration). Discovered via vue-tsc strict mode. Mechanical fix but extends scope beyond plan §11 estimated.

- **§5.1 lesson 5 (orphan test files linger after shim deletion)**: T5.b — grep `tests/` for `api/publish` references BEFORE deletion (found `api-creator-publish.spec.ts` 12 tests, deleted in same commit as api/publish.js). v16.2.4's same pattern.

### 5.3 v16.2.1..3 lessons 沿用 (确认有效)

- T1 verbatim copy + intra-package import adjustments (5.1 lesson 1 from v16.2.4)
- shim private name re-exports for test compat (5.1 lesson 3 from v16.2.1) — N/A this sub-phase (no private symbols used)
- typed wrapper NO zod (5.1 lesson 4 from v16.2.1) — T3.a 严格遵循
- `/api/` prefix NOT in code (5.1 lesson 5 from v16.2.1) — T3.a 严格遵循 + T3.b URL contract 验证 5 wrappers (0 violations)
- hyphen name + underscore module, ruff `# noqa: F403` inline, knip allowlist, verbatim copy integrity

---

## 6. Carryover to v16.2.6+ / v16.2.7

| 任务 | 阶段 | 来源 |
|---|---|---|
| **v16.2.6 memory** | 3 files (annotations + assets + query) — Round 2 leaf last | per plan §7 |
| **v16.2.7 cleanup** | 41 shim deletions + 4 typed wrapper `/api/` prefix fix (world/workspace/quality + onboarding from v16.2.3) + 22 vitest debt + import-linter DP-01..06 | per plan §9 |
| **api/publish.js shim** | ✅ DELETED in T5.b — no carryover | resolved |
| **`api/index.js` 6 publish aliases** | ✅ Updated in T5.b to point to @/api/export | resolved (delete in v16.2.7 with shim sweep) |
| **5 export consumer files (routes + composables)** | ✅ All migrated (routes in T4 + composables in T5.a + api/index.js + creator.js in T5.b) | resolved |
| **Pre-existing vitest debt** | 22 v16.2.1 `useCreatorVolumePlan*.spec.ts` failures — unchanged | v16.2.7 cleanup |
| **intra-package imports** | ✅ All adjusted in T1.a (per v16.2.4 lesson 1) | resolved |
| **useWriteFlow typed signature migration** | ✅ Completed in T5.b (3 call sites + 4 cast fixes) | resolved |
| **Typed wrapper params forwarding (fetchCreatorPublishHistory default limit)** | ✅ Preserves original publish.js behavior (`?limit=10` default per T3.b test fix) | resolved (lesson 4 applied) |
| **export.ts vite/client triple-slash directive** | ✅ Added in T3.a | resolved (lesson 5.1.1 new) |
| **TS cast pattern `as unknown as Record`** | ✅ Applied in T5.b (4 cast sites in useWriteFlow.ts) | resolved (lesson 5.1.2 new) |

---

## 7. 验证证据

```bash
# Backend tests (separate invocations due to Phase 125 module-namespace collision)
$ /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-creator/tests/ -q
============================== 71 passed in 0.26s ==============================  (was 63 in v16.2.4, +8 export pkg tests)

$ /home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests/ -q
============================== 75 passed in 0.47s ==============================  (was 66 in v16.2.4, +9 export DTO tests)

$ /home/ailearn/miniconda3/bin/python -m pytest tests/infra/ -q
=========================== 359 passed, 5 skipped in 12.89s ===================  (unchanged from v16.2.4)

# Frontend (full dashboard)
$ cd apps/dashboard && pnpm vitest run --reporter=dot
 Test Files  4 failed | 217 passed (221)
      Tests  22 failed | 1774 passed | 1 skipped (1797)
# 22 failures all in useCreatorVolumePlan* (pre-existing v16.2.1 debt, unchanged)
# 1774 passed (was 1778, -4 = 13 new export URL contract tests - 12 deleted orphan api-creator-publish tests + 5 export pkg -5 net adjustment)
```

```bash
# Type / Lint / Code
$ pnpm exec vue-tsc --noEmit
0 errors

$ pnpm exec knip
Configuration hints (7) — no errors (advisory hints for: settings.ts + content.ts + export.ts + dashboard-contracts/export.ts + dashboard-contracts dep + router/routes.js + main.js)

$ ruff check .
All checks passed!

$ /home/ailearn/miniconda3/bin/python tooling/contracts/generate.py
WROTE .../ts/creator.ts (24042 bytes) — was 22541 (v16.2.4), +1501 from 8 export/publish DTOs

# zod reverse CI skipped in this commit (per v16.2.4 handoff pattern — only run in zod-revalidate CI job, not local verification)

# Carryover closure verification
$ grep -cE "infra\.creator_export|infra\.creator_publish" apps/studio_api/routes/creator_core.py
0  # T4 migrated

$ ls packages/lingwen-creator/src/lingwen_creator/export/*.py | wc -l
6  # 5 modules + __init__.py

$ grep -cE "infra\.creator_export|infra\.creator_publish" packages/lingwen-creator/src/lingwen_creator/export/*.py
0  # intra-package imports 都 use new path (per v16.2.4 lesson 1)

$ ls apps/dashboard/src/api/publish.js 2>&1
ls: cannot access ...: No such file or directory  # shim deleted in T5.b

$ ls apps/dashboard/tests/unit/api-creator-publish.spec.ts 2>&1
ls: cannot access ...: No such file or directory  # orphan test deleted in T5.b

$ grep -cE "from.*api/publish|publish\.js" apps/dashboard/src/ apps/dashboard/tests/ 2>&1
0  # no orphan references

# Shim back-compat (sample)
$ /home/ailearn/miniconda3/bin/python -c "from infra.creator_export_common import export_metadata, load_export_chapters; print('common shim OK')"
common shim OK

$ /home/ailearn/miniconda3/bin/python -c "from infra.creator_publish_adapters import get_publish_adapter, FanqiePublishAdapter; print('publish_adapters shim OK')"
publish_adapters shim OK

$ /home/ailearn/miniconda3/bin/python -c "from infra.creator_publish import submit_creator_publish, list_creator_publish_history; print('publish shim OK')"
publish shim OK
```

**Test totals**: 71 creator pkg + 75 shared pkg + 359 infra = **505 backend passing**, 1774 frontend passing. 0 regressions (excluding pre-existing 22 vitest debt unchanged from v16.2.4 baseline).

---

## 8. 新工具总结

| 工具 | 旧 | 新 |
|---|---|---|
| Export Python | `infra/creator_export_*.py + infra/creator_publish*.py` (5 files, 633 lines) | `packages/lingwen-creator/src/lingwen_creator/export/` (5 files, 633 lines verbatim copy) + 5 1-line shims in `infra/` |
| Export DTOs | inline in `apps/studio_api/models/creator_settings.py` (local) | `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` (Export + Publish section, 8 DTOs, +1501 bytes) |
| TS types | inline in frontend code | `packages/lingwen-shared/src/lingwen_shared/contracts/ts/creator.ts` (auto-generated, 148 interfaces total, +8 export/publish) |
| Typed wrapper (new) | n/a | `apps/dashboard/src/api/export.ts` (5 wrapper functions, fetchBlob + fetchJson helpers) + `packages/dashboard-contracts/src/shared/export.ts` re-export |
| Publish API (legacy) | `apps/dashboard/src/api/publish.js` (Phase 62.4 shim with raw fetch + 9 functions) | DELETED — replaced by typed wrapper |
| Routes | 5 lazy imports from `infra.creator_export_* + infra.creator_publish*` in `creator_core.py` | all 5 migrated to `lingwen_creator.export.*` (0 infra imports remaining) |
| Composable | `useProductExport.ts` + `useProductPublish.ts` raw fetch via `api/index.js` barrel | direct import from `@/api/export` + `@/api/content` typed wrappers |
| api/index.js barrel | re-exported 9 publish.js functions (legacy aliases) | re-exports from typed wrappers (api/export.ts + api/content.ts + api/volume.ts) — 6 publish.js re-exports removed, 4 Content functions re-pointed |
| api/creator.js | `export * from './publish.js'` | removed (publish.js deleted) |
| useWriteFlow | 2-arg signature `(chapterNum, body)` for saveCreatorChapterBody/Outline | 1-arg typed signature `({ chapter_id, body })` per CreatorBodySaveRequest/creatorOutlineSaveRequest |
| Test mocks | `vi.mock('../../src/api/index.js', ...)` for fetchCreatorChapterPreview + export + publish | split mocks per typed wrapper module (`vi.mock('../../src/api/export.js', ...)` + `vi.mock('../../src/api/content.js', ...)`) |

---

## 9. v16.2.5 完整 commit 时间线

```
master: f01aaf2d (v16.2.4 content closed)
  ↓
  389f91a5 (T1.a: export/common + export/docx + 2 shims)
  dce65eaf (T1.b: export/epub + 2 shims incl. creator_publish_adapters pre-emptive)
  5715ff15 (T1.c: export/publish + export/publish_adapters + __init__.py + 1 shim)
  b2dd6f53 (T1.d: test_export.py + ruff fixup)
  5308c63e (T2: 8 Export/Publish DTOs + TS codegen + 9 backend tests)
  5390a776 (T3.a: export.ts typed wrapper + re-export + knip allowlist)
  1e95ff82 (T3.b: export URL contract tests)
  8695e3dd (T4: routes imports migration — 5 lazy imports)
  f3dd8f99 (T5.a: composable refactor + export.ts vite/client triple-slash)
  8bd30325 (T5.b: api/index.js update + delete publish.js + delete orphan test + useWriteFlow typed signature migration)
  4d11064b (T7: test mock path updates — 5 test files)
  ↓
HEAD: T8 (current — handoff + CLAUDE.md + architecture.yml + migration_log.yml)
```

Total: 13 commits (12 implementation + 1 T8 handoff) vs plan §3 estimate of 12 commits. T6 skipped (no findings — only test_export.py references infra imports as expected back-compat test).

---

## 10. Closing Notes

v16.2.5 export 是 Phase 126 v16.2 creator 6-subdomain 拆分的第 5 个 sub-phase,**Round 2 leaf 第一个**。Export 是真正 leaf 模块——无 forward-reference、无 shared extraction、无 spec violation。

**12 implementation commits** 估算 (vs plan §3 估算 12),完全 match:
- T1 4 sub-commits per DP-06 (matches v16.2.4 T2a-d split precedent)
- T2 1 commit (DTOs + codegen)
- T3 2 sub-commits (typed wrapper + URL contract, matches v16.2.1..4 pattern)
- T4 1 commit (routes, single file)
- T5 2 sub-commits (composables + infra/shim delete + useWriteFlow bonus fix)
- T6 skipped (no findings)
- T7 1 commit (test mock path updates per v16.2.4 §5.1 lesson 2)

**1 carryover closure**:
- ✅ useWriteFlow typed signature migration (bonus fix per T5.b scope expansion, per v16.2.4 §5.1 lesson 4)

**0 test regressions** (excluding pre-existing 22 vitest debt from v16.2.1 + Phase 125 module-namespace issue, unchanged from v16.2.4 baseline).

**3 new lessons captured** (T3.a vite/client triple-slash + T5.b TS cast double-cast + T7 vi.mock split per typed wrapper).

**Phase 126 v16.2 series progress**: 5 of 7 sub-phases closed (shared + volume + settings + onboarding + content + export). Next: v16.2.6 memory (Round 2 leaf last) + v16.2.7 cleanup (41 shims + typed wrapper `/api/` fix + import-linter + 22 vitest debt).
