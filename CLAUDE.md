# 灵文 · 工业化小说生产系统

> **版本**: v16.2.4 (Phase 126 content subdomain 拆分 + onboarding T4 闭环)
  → v16.2.3 (Phase 126 onboarding 闭环)
  → v16.2.2 (Phase 126 settings 闭环)
  → v16.2.1 (Phase 126 creator 6-subdomain 拆分 Phase 1/8: volume subdomain 闭环)
  → v16.2.0 (Phase 124 uv workspaces + turbo 启用 闭环)
  → v16.1 (Phase 124 lingwen-shared contracts 包 闭环)
  → v16.0 (Phase 124 uv workspaces + turbo 启用 闭环)
  → v15.7.1 (Phase 125 baseline cleanup 闭环)
  → v15.7 (Phase 123 llm_service latent bug fix 闭环)
  → v15.6 (Phase 121 minimax parse_rate 修复 闭环)
  → v15.5 (Phase 120 LLM provider benchmark 闭环)
  → v15.4 (Phase 119 World follow-up 闭环)
  → v15.3 (Phase 118 World LLM Agent + cleanup 闭环)
  → v15.2 (Phase 117 World Visualization v1)
  → v15.1 (Phase 116 follow-up 闭环)
  → v15.0 (Phase 115 创作端 UX 子项目 #1 闭环)
  → v14.2 (Phase 114 prod Web Vitals 终结)
  → v14.0 (Phase 99-105b knip-follow-up 闭环完成)
  → v13.0 (Phase 60-67 dashboard 基础设施重构完成)

> **更新 (2026-08-28)**: Phase 126 v16.2.4 闭环 — creator Content subdomain 拆分 + onboarding T4 闭环——15 commits (`3f21513a` ... `55f9a84f`):
- **T1**: `shared/mode.py` extraction (cross-subdomain utility: CREATION_MODE_* + CreatorSettings + settings_from_project_config) + `infra/creator_mode` 变 shim + `shared/check.py` spec violation fix + onboarding forward-ref close。— `19e1ca03`
- **T2a-d**: 8 content files verbatim copy + 8 shims + `__init__.py` star-imports (T2 split 4 commits per DP-06: agent 598L / dashboard+logic_check / mode+models / preferences+ui_profile)。— `2ebb10ad` + `307afa97` + `ee710d6d` + `3afe3c09`
- **T3**: 16 Content DTOs (10 spec + 2 CreatorDashboard* + 4 settings/Mode utilities) → `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` + TS codegen (9068→22541 bytes, +13473) + 13 backend tests。— `b63367a1`
- **T4**: `apps/dashboard/src/api/content.ts` typed wrapper (11 funcs, NO zod, NO /api/) + `packages/dashboard-contracts/src/shared/content.ts` re-export + knip allowlist + 15 URL contract tests。— `e9facc1e`
- **T5**: 13 routes imports in `creator_core.py` migration + `infra/project_init.py` + `infra/project_config.py` 2 creator_mode imports → `shared.mode` migration。— `aec1dbff`
- **T6**: onboarding T4 composables refactor (5 files: useCreatorOnboarding + useWizardSteps + useOnboardingProgress + useOnboardingNotifications + useTodayHub cross-cutting) + delete `api/onboarding.js` shim (was 23 Creator-prefixed aliases) + bonus fix 2 T3 typed wrapper defects (applyWizardShareDone + dispatchDigestNow silently dropped body/query params) + update 4 test mocks。— `06a91169`
- **T7**: 4 cross-subdomain settings.{docs,history,merge_preferences}.py stale `infra.creator_*` imports → `lingwen_creator.content.*` migration。— `392fd809`
- **T8 fixups (3 commits)**: verification gates 发现 3 classes 修复 — (A) `content/dashboard.py` + `content/logic_check.py` intra-package imports (verbatim copy preserved `from infra.creator_ui_profile` → cycle via shim) + `infra/creator_dashboard.py` shim `_excerpt` re-export; (B) 6 onboarding test files patch path `infra.creator_onboarding_{webhook,email}` → `lingwen_creator.onboarding.{webhook,email}` (v16.2.3 T1a regression discovered: shim mock 不通过 `from X import Y` lazy import 传播) + delete orphan `apps/dashboard/tests/unit/api-creator-onboarding.spec.ts`; (C) ruff `--fix` 22 I001 violations across 10 files (shim star-import + explicit import block sort)。— `9fff074a` + `8a6e0f25` + `55f9a84f`
- **Handoff**: `docs/superpowers/handoffs/2026-08-28-phase-126-v16-2-4-content-handoff.md` (15 commits, 8 deviations, 5 lessons, 8 carryover)。

Lessons:intra-package imports after verbatim copy (extends v16.2.2 §5.1 lesson 7: now also applies to sibling-subdomain imports) / shim mocks 不 propagate through `from X import Y` lazy imports (PEP 562 `__getattr__` proxy no work for modules — Python modules don't honor `__setattr__`; test patches MUST target real module path) / composable refactor scope expansion (T6 plan estimated 5 files, actual 11: 5 composables + creator.js + index.js + useTodayHub + 4 test mocks + 2 typed wrapper defects) / typed wrapper params forwarding is fragile (use `requestWithParams(method, path, params)` helper to avoid silent arg drops) / orphan test files linger after shim deletion (`grep -r "<shim-path>" tests/` must precede deletion)。

Tests:63 (creator pkg) + 66 (shared pkg) + 241 (infra) = 370 backend passing。1778 vitest passing (22 pre-existing v16.2.1 `useCreatorVolumePlan*` debt unchanged)。vue-tsc 0 / ruff 0 / knip 0 (5 advisory hints) / codegen OK / zod 0 drift。Backend routes imports 全部迁移 (13 routes imports in `creator_core.py` + 2 project_X imports, no `from infra.creator_{agent,batch_history,dashboard,logic_check,models,preferences,ui_profile}` left in `creator_core.py`)。Shim count: 36 (unchanged, conversion of full impls to shims doesn't add count per v16.2.3 §5.1 lesson 2)。

Carryover to v16.2.5..7:v16.2.5 export (5 files Round 2 leaf)/ v16.2.6 memory (3 files Round 2 leaf)/ v16.2.7 cleanup (36 shim deletions + 4 typed wrapper `/api/` prefix fix for world/workspace/quality + onboarding `/creator/onboarding/diff-collab-notes` 404 fix + 22 vitest debt + import-linter DP-01..06)/ Content composables (19 per spec §3.7) refactor deferred to v16.2.7 / 4 unwired Content DTOs (CreatorDashboard* + CreatorUiProfile*) — wrap when endpoints land。

> **更新 (2026-08-27)**: Phase 126 v16.2.3 闭环 — onboarding subdomain 拆分——10 commits (`c7c3913a` ... `6cfdf5c2`):
- **T1a-d**: 9 onboarding files (autodetect/digest_background/digest_schedule/email/notifications/progress/webhook/onboarding.py + diff_collab) → `packages/lingwen-creator/src/lingwen_creator/onboarding/` + shims + 24 tests。T1 split 4 commits per DP-06。— `c7c3913a` + `949fb0ec` + `aa867b6b` + `8a800d68`
- **T2**: 30 Onboarding DTOs (20 top-level + 10 nested helpers) → `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` + TS codegen (14462→19805 bytes) + 13 backend tests。— `4fe2512c`
- **T3+T4-partial**: `apps/dashboard/src/api/onboarding.ts` typed wrapper (23 funcs) + `packages/dashboard-contracts/src/shared/onboarding.ts` re-export + `apps/dashboard/src/api/onboarding.js` shim with 21 Creator-prefixed legacy aliases (full composable refactor deferred to v16.2.4 T6 carryover)。— `d2a440d9`
- **T5**: 21 routes imports in `creator_onboarding.py` migration (single commit)。— `36a26fc2`
- **T6**: 3 cross-subdomain `volume/template_approvals.py` stale `infra.creator_onboarding_*` imports → `lingwen_creator.onboarding.*` (carryover from v16.2.2 §6 closed)。— `6cfdf5c2`
- **Handoff**: `docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-3-onboarding-handoff.md` (10 commits, 9 deviations, 5 lessons)。

Lessons:legacy `api/onboarding.js` shim with backward-compat aliases pattern (cleanest migration path: thin shim with both `export * from './new.ts'` AND legacy aliases) / shim count 不 increase when migrating existing files to shim form / `@lingwen/dashboard-contracts` re-export chain fragility (new DTOs need manual addition to explicit re-export list) / top-level `await import()` in shims is unsafe (use synchronous `import { ... } from './X'; export const legacy = newName`) / spec §2 import list + grep verification = complete adjustment guarantee。

Tests:24 (onboarding pkg) + 50 (shared DTO) + 16 (onboarding infra) + 25 (frontend URL contract) = 115 onboarding passing。vue-tsc 0 / ruff 0 / knip 0 / codegen OK / zod 0 drift。Shim count: 36 (unchanged per §5.1 lesson 2)。Carryover:5 composable files (useCreatorOnboarding + 3 submodules + index.ts) refactor to v16.2.4 T6 / content migration 抽 shared/mode.py 修 spec violation / dashboard-contracts/src/shared/creator.ts explicit re-export list needs update per new DTO。

> **更新 (2026-08-27)**: Phase 126 v16.2.2 闭环 — creator Settings subdomain 拆分——20 commits (`5b7c1d7f` ... `1fb9baed`):
- **T1a-d**: 3 settings Python files (docs 351 + history 136 + merge_preferences 1355 lines) verbatim copy + 1-line shim with underscore re-exports。4 commits + carve-out fix + T1c BLOCKED follow-up + H1 function-body lazy import fix。— `5b7c1d7f` + `78621a0f` + `f5844680` + `4df3fb1e` + `19e1ca03` (no, that's v16.2.4)
- **T2**: 28 Settings DTOs → `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` + tooling/contracts/generate.py + TS codegen (87 interfaces total) + 7 new DTO tests。
- **T3**: `apps/dashboard/src/api/settings.ts` typed wrapper (32 funcs, NO zod, NO /api/) + URL contract regression lock (34 tests) + knip allowlist。
- **T4a-b**: useCreatorSettings composable + 3 submodules (useSettingsDocs/History/MergePresets) refactored to typed wrapper。
- **T5a-b**: All 32 routes lazy imports in `creator_settings.py` migrated (5 docs T4b + 2 history T5a + 25 merge_preferences T5a/T5b)。
- **T6-T8**: Cross-subdomain cleanup + formal shim audit + handoff + 3 fixups (H1 function-body lazy import + D4 doc mismatch + test regex gap)。

Lessons:spec §2 import list completeness check before verbatim copy / T1a carve-out pattern for cross-task imports / T3 DP-06 budget includes index.ts re-export / shim underscore re-exports added continuously via T1c follow-up pattern / DTO count budgets ~30% extra for nested types / plan gate descriptions explicit about creation vs deletion / ALWAYS check function-body lazy imports after verbatim copy — module-level check missed H1。

Tests:50+ (settings pkg) + 37 (settings DTO) + 34 (frontend URL contract) = 121 settings passing。vue-tsc 0 / ruff 0 / knip 0 / codegen OK / zod 0 drift。Shim count: 36 - 1 (creator_mode already shim) = 35, but added 3 settings shims = 38 net (eventually settled to 36 after v16.2.3 T6 cleanup)。

> **更新 (2026-08-27)**: Phase 126 v16.2.1 闭环 — creator Volume subdomain 拆分——15 commits (`5bc35f1b` ... `5733505b`):
- **Plan reorder**: 原 plan memory-first 假设错(v16.2.0 review 跑 cross-subdomain analysis 发现 memory 依赖 content + settings)。Volume 是 root,被 4 个其他 sub-domain 依赖。先迁 volume 让后续 sub-phase 可用新 package path。— `5bc35f1b`
- **T1**: 3 小 volume files (plan + plan_share + pulse) → `packages/lingwen-creator/src/lingwen_creator/volume/` + shim + tests (7 tests)。intra-package import 规则明确(plan §12.2)。— `0ec3da6c`
- **T2**: 58 Volume DTOs → `packages/lingwen-shared/src/lingwen_shared/contracts/python/creator.py` + 跑 tooling/contracts/generate.py (修 v16.1 missing "creator" entry in MODULES list) → TS 自动生成 (59 interfaces, 9068 bytes) + zod reverse 0 drift + 23 tests。— `69195d23`
- **T3**: `apps/dashboard/src/api/volume.ts` typed wrapper + `packages/dashboard-contracts/src/shared/creator.ts` re-export shim + knip allowlist (37 wrapper functions, 匹配 v16.1 T4 world.ts/workspace.ts/quality.ts style)。— `95245044`
- **T4**: 3 composables refactor (useCreatorVolumePlan + Diff + MergeSplit) + 4 routes imports (creator_volume_plan) + 第一次 /api/ prefix fix (26/37 paths)。plan §12.2 intra-package example 更新。— `fbaee62d` + `515c399f` + `f12763cc` + `b63253e5`
- **T4 bug fix**: spec reviewer 实证 11 个 template-literal paths 仍带 `/api/` prefix (会 404)。修 commit `db0d6c12` + 18 URL-contract tests (regression lock)。
- **T5a-c**: catch-up missing 3 volume files (summary 144 + templates 1022 + template_approvals 692 lines) + shim (含 27 + 13 个 underscore re-exports for test compat) + intra-package import per §12.2。— `f5844680` + `87876ee2` + `626f60c4`
- **T5d**: `volume/__init__.py` 加 3 star-imports + `test_volume.py` 扩展 7 → 14 tests。— `ee1cb5a3`
- **T5e-f**: 2 composables refactor (useCreatorPulse + useCreatorVolumePlanTemplates, exportTemplateApprovalAudit stub 替换为真实现) + 32 routes imports migration (templates + template_approvals endpoints) + `generateVolumeSummary` typed wrapper 新增。— `0870f7c2` + `5733505b`
- **Handoff**: `docs/superpowers/handoffs/2026-08-27-phase-126-v16-2-1-volume-handoff.md` (15 commits, 11 deviations, 5 lessons, 6 carryover)。

Lessons:dependency analysis MUST precede Strangler Fig sub-phase ordering (cross-subdomain grep + graph before sequencing)/ shim private name re-exports required for test compat (any shim must audit existing tests for private symbol imports)/ typed wrapper 不 use zod runtime validation (zod is T5/CI drift, not wrapper layer; verify against v16.1 T4 reference)/ `/api/` prefix 必须 NOT be in code (core.js BASE_URL 已是 `/api`,all 4 typed wrappers 错,v16.2.1 修 volume.ts only, 其他 3 carryover 到 v16.2.7)/ spec violation carryover (shared/check.py 当前依赖 infra.creator_mode.CreatorSettings,carryover 到 v16.2.3 content migration 抽到 shared/mode.py)。

Tests:14 (packages) + 44 (infra consumer) + 40 (frontend composable + api) = 98 total passing. vue-tsc 0 errors / ruff 0 / eslint 0 / knip 0 (2 advisory hints)。Backend routes imports 全部迁移 (36 routes imports migrated, no `from infra.creator_volume` left in `creator_volume.py`)。Shim count: 6 created (3 T1 + 3 T5), 28 remaining。

Carryover to v16.2.2..7:settings (3 files)/ content (10 files, must fix shared/check.py spec violation)/ onboarding (9 files)/ memory (3 files, Round 2 leaf)/ export (5 files, Round 2 leaf)/ v16.2.7 cleanup (36 shims + /api/ fix for world/workspace/quality wrappers + import-linter forbidden pattern check)/ import-linter enforcement DP-01..06 (v16.4 / v16.5)。

> **更新 (2026-08-27)**: Phase 124 v16.1 闭环——9 commits (T1-T8 + 2 review fixups):
- **T1** `packages/lingwen-shared/` uv workspace member 新建 (hyphen name + underscore module,5/5 layout tests pass) — `121b7855`
- **T2** 12 DTO 迁入 (6 world / 4 workspace / 3 quality) + 2 Hexagonal ports 声明 (`LLMServicePort` / `StoragePort`,enforcement 在 v16.4 / v16.5)。7/7 contract tests pass。`ChapterDTO.id` 改为 `int | None = None` (TDD-driven,匹配 `ProposalDTO.id` 模式)— `b4fb3fe3`
- **T3** `tooling/contracts/generate.py` Pydantic → TS codegen (hand-rolled JSON Schema → TS converter)。5/5 codegen tests pass。Known caveat: 单值 `Literal["agent"]` 在 TS 中变成 `string` 而非 `"agent"`(`const` keyword 未处理)— `209ee5bb`
- **T4** `apps/dashboard/src/api/{world,workspace,quality}.ts` typed wrapper 新增(不替换 `composables/world/useWorldDb.js`,creator 拆分才动)。vue-tsc 0 / ESLint 0 / vitest 1731。knip allowlist 加 3 wrapper + 1 dep(`packages/dashboard-contracts/package.json` 占位 `@moling/dashboard-contracts` rename → `@lingwen/dashboard-contracts`)— `64f80f6c` + knip fix `b8b6bd5a`
- **T5** `tooling/contracts/zod_revalidate.py` + `dump_openapi.py`(Q5=B 独立 CI job)。4/4 zod tests pass(含 drift detection)。同时装 `zod` + `openapi-typescript` Node dev deps(future-use)— `7be49d38`
- **T6** `.github/workflows/test.yml` 加 `zod-revalidate` job。`needs: [hygiene]`(plan 说 `setup` 但实际 workflow 用 `hygiene`)+ `uvicorn --factory create_app` 修正(`app.py` 只有 factory,无 module-level `app`)。code review 后续修:`enable-cache: true` uv cache + readiness poll 替代 `sleep 5`— `8e542d6f` + fix `66f72f45`
- **T7** 全套 CI smoke PASS — 10/10 验证门全过。Net improvement vs v15.7.1 baseline:+4 passing / -4 failing(in pre-existing pytest debt)。新测试 +21 (T1+T2+T3+T5)全部通过。
- **T8** 文档同步(本节)。
Lessons:hyphen name + underscore module 严格分离 (v16.0 教训沿用)/ `ChapterDTO.id optional` TDD-driven 修正 vs 计划 spec 冲突 / hand-rolled JSON Schema → TS converter 比 `pydantic-to-typescript` 库更稳(version drift avoidance)/ `knip` 在加 typed wrapper 时要把 unused file/dep 加 allowlist / CI `setup-uv` cache 必加 / `sleep N` → readiness poll 在 cold CI 上更稳 / pre-existing pytest debt(agent_system/dashboard)与 v16.1 无关,不阻塞闭环。

> **更新 (2026-08-26)**：Phase 119 v15.4 闭环——14 commits (`8fcae6eb` ... `ae374afb` + `fbc99da2` ruff 清理)：
  - **Task A** LoreEditor/TimelineEditor 接入 Detail 页面 — `LoreDetail.vue` + `TimelineEventDetail.vue` 加 `editing` ref + toggle button + inline `<XxxEditor v-if="editing" />`。按钮文案 "新增条目" / "新增事件" (semantic 清晰,Editor 仍 create-only)。4 component tests per detail page (stub Editor via `vi.mock('@/.../XxxEditor.vue')`)。
  - **Task B** chapterRange → chapterTexts UI 接线 — 新 backend endpoint `GET /api/world/chapters?project=X&start=N&end=M` 读 `projects/<slug>/golden-set/chapters/ch{NNN}.md` (canonical,无 frontmatter)。`useWorldAgent.fetchChapterTexts` helper。`WorldProposalInbox.vue` 加 extract section (character dropdown + start/end inputs + 提取按钮 + result 行)。5 component tests + 2 helper tests。
  - **Task C** Rate limiter per-IP scoping — `_AgentRateLimiter` 从 process-global counter 改 dict-per-key + lazy TTL eviction。Routes inject FastAPI `Request` 取 `request.client.host`。2 unit tests (per-IP 隔离 + TTL eviction)。
  Tests 35→38 backend (+3) / world frontend 1724→1731 (+7)。vue-tsc: 0 errors。ESLint: 0 warnings。ruff: 全部 clean (含 Phase 117 遗留 I001)。
  Lessons: `@/` alias 即可 (不要 `../../../../` 数相对路径) / `v-if` panel 内 element 测试需先 click toggle (`mountAndOpen` helper) / testid-class-sync 要求 kebab + BEM 双 class / TestClient 默认 `request.client.host="testclient"`。

> **上一里程碑 (v15.3, Phase 118)**：World LLM Agent + cleanup 闭环——3 commits (`8269e081` / `1366aedc` / `37343188`)：
  - **Task #14 + #15** DRY helpers + RevisionConflict 基类：`infra/world_db/queries/_helpers.py` 提供 `now_iso()` + `row_to_dict(row, json_fields)` + `RevisionConflict` 基类。6 个 query 文件 import, 净 -49 行。
  - **Task #16** `create_relationship` deterministic id：follow-up SELECT 替换 implementation-dependent `cur.lastrowid`。
  - **Task #17** LLM-backed agent extraction：`infra/world_db/agent_schemas.py` (Pydantic v2) + `agent_extractors.py` 真 LLM 调用 + 2 new POST routes + `_AgentRateLimiter` (5 calls/session, Phase 119 Task C 升级为 per-IP) + `useWorldAgent.js` 真 fetch。
  Tests 19→35 backend (+16) / world frontend +5 useWorldAgent。副产物：vis-network install regression 文档化（fresh clone 必须 `pnpm install`）。

> **更新 (2026-08-26)**：Phase 120 v15.5 闭环——13 commits (`649fb62a` ... `8e1027e3`)：
  - **设计 → plan → 实施 (Tasks 1-9)** `infra/llm_benchmarks/` module: 7 source files (metrics/providers/fixtures/results/render/run/__init__) + 6 test files (33 tests PASS)。Mock-only pytest + CLI 真跑 (env var gated)。Hybrid execution: Tasks 1-8 inline TDD (机械 transcription), Task 9 multi-file orchestration 走 inline TDD per project pattern。
  - **Task 10 (manual real run)**: minimax 真跑 10 calls (`api.minimaxi.com/anthropic/v1/messages`)。**Real finding**: parse_rate=0.20 (8/10 calls 返回 invalid JSON — `target_id` 是字符串 '林栀' 而非整数)。quality_composite=0.73, 低于 0.90 threshold。cost=$0.0004/call, p50=4.98s p95=9.52s, consistency=1.00 (successful calls 全部一致)。
  - **Task 11 (report)**: `docs/benchmarks/2026-08-26-llm-provider-benchmark.md`。render.py 加 below-threshold section (Enhancement during Task 10)。
  - **Task 12 (decision)**: **保持 `plugin_manager.py:150` hardcode `["minimax", "anthropic", "openai"]` 不变**。minimax 是 primary (位置 1 confirmed); anthropic/openai 是 failover candidates (Phase 120 cost-controlled mock-only, 缺实测数据)。parse_rate 0.20 是 fixable issue (SYSTEM_PROMPT 或 model calibration), 不构成 "停用 minimax" 的依据。
  - **Task 13 (docs sync)**: CLAUDE.md v15.5 + `.lingwen/architecture.yml` 加 `llm_benchmarks` module boundary。
  副产物 — 修复了 `infra/llm_service.py` 的 latent bug: `_init_providers` 走 `plugin_manager.get_priority()` 但 `plugin_manager._discover_internal_providers` 用错的 module path (`infra.ai_service.<name>` 而非 `lingwen_llm.providers.<name>`)。Phase 120 绕过: 直接 instantiate `MiniMaxProvider` via `get_provider_class("minimax")`。原 bug 保留待 v15.6+ 修。
  Lessons: pytest mock-only 必须 monkeypatch LLMService.get() 避免 CI 烧钱 / Path.parents[N] 是 N levels up (off-by-one 容易错) / subprocess.run 来源 (`source .env` + `set -a`) / Pydantic validation failure 反映真 LLM output quality — benchmark surface 真实问题 / 缺数据时不要 edit hardcode (Phase 119 §5 invariants)。

> **更新 (2026-08-26)**：Phase 121 v15.6 闭环——1 commit (`e1b0539a`)：
  - **SYSTEM_PROMPT 加 rule #7** `target_id 必须是整数,不是字符串。如果不知道角色的整数数据库 ID,使用 0。绝对不要把角色 slug 或角色名字符串作为 target_id。`
  - **`infra/llm_benchmarks/run.py._call_provider` 修 canon_level_ok 指标** — 之前把 Optional=None 也算 fail,实际 schema 允许 canon_level omit (LLM 选 omit 时不应 fail)。改: only mark non-compliant if value IS provided AND not in enum。
  - **Benchmark 重跑结果**:
    - parse_rate: 0.20 → 0.70 (3.5x)
    - schema_compliance: 1.00 → 1.00
    - canon_level_compliance: 0.25 → 1.00
    - **quality_composite: 0.73 → 0.90 (AT 0.90 threshold!)**
    - consistency: 0.33 → 0.58
    - cost/call: \$0.0004, p50=3.96s, p95=8.62s
  - 73 tests pass (33 llm_bench + 40 world_db).
  Lessons: LLM 输出 schema 验证要严格区分 "字段缺失 vs 字段非法" / `parse_proposals_json` 容忍 markdown fences 但不容忍 truncated JSON / SYSTEM_PROMPT 改一个数字规则 ≠ 改 schema,小改动仍然要 verify benchmark。
  已知 carryover (Phase 122 候选):
  - 2 calls 仍 fail (JSON truncation at char 499/1017 — model-specific, 需 follow-up)
  - consistency=0.58 偏低 (temperature=0.2 + 长 chapter 输出,follow-up: 改 temperature=0.0 或更短 prompt)
  - `infra/llm_service.py._init_providers` latent bug (Phase 120 发现,未修)
  - (可选) Anthropic/OpenAI real re-test

> **更新 (2026-08-26)**：Phase 123 v15.7 闭环——1 commit (`171a757b`)：
  - **修复 `infra/llm_service.py._init_providers` + `_create_provider`** 两个 latent bug：
    - `_init_providers` 走 `self._plugin_manager.get_priority()`,但 `PluginManager._discover_internal_providers` 用错 module path (`infra.ai_service.<name>` 而非 `lingwen_llm.providers.<name>`),priority list 永远是空 → `RuntimeError("无可用的LLM Provider")`。改: 走 `_PROVIDER_REGISTRY` (`list_registered_providers()`,decorator-driven) + local priority order `[minimax, anthropic, openai]`。
    - `_create_provider` 用 `get_provider_class` 但没 import → `NameError`。改: import `get_provider_class` + `list_registered_providers`。
  - **3 new tests** (`tests/infra/test_llm_service.py`): load-minimax-with-key / uses-decorator-registry / singleton-reset。
  - 73 existing tests 仍 pass (无 regression)。
  - Phase 120 benchmark 的 bypass (直接 `get_provider_class("minimax")`) 现在变成可选 — `LLMService.get()` 也 work,但保留 bypass 避免 real-run 路径产生意外 side-effect。
  Lessons: latent bug 藏了多久 — 至少从 Phase 118 (real LLM agent integration) 起就在,只是 agent_extractors 测试都注入 mock 没触发。Production code path 上 `LLMService.get()` 一直没真跑过 (除 health.py 的 `LLMService.get_instance` 走 lingwen_llm.llm_service 路径)。Type-level fix 重要: 不光 `_init_providers`, `_create_provider` 也漏 import。

> **品牌**：本仓库的产品名是 **墨灵 Studio**（"墨灵"），内部框架名是 **灵文引擎**（"灵文"）。工程命名空间沿用历史 `lingwen`（包名 / import path / Python module 全部使用 `lingwen`，不要改成 `moling`）。品牌字符串真源在 `apps/dashboard/src/config/brand.js`。

> **v15.7.1 闭环 (2026-08-27)**: Phase 125 baseline cleanup — **v16.0 (uv workspace + turbo) 解锁前提**:
> - **15 broken pytest tests** (从 16 → 14;test_llm_service 是 false alarm) 修复为 0 collection errors
>     - `master_controller` (Phase 15.0 P3-SPLIT): `packages/lingwen-core/src/lingwen_core/agents/master_controller.py` 新建 re-export shim
>     - `infra.consistency.{checkers.*,creative_whitelist}`: 6 个新 shim,re-export from `lingwen_quality.consistency.*`
>     - `infra.agent_system.reviewer`: shim + try/except fallback
>     - `SnapshotError`: 5 行加回 `infra/errors.py`
>     - 删 `tests/test_character_agency.py` + `tests/test_core_props_checker.py` 顶层孤儿
>     - `tests/__init__.py` + `tests/{consistency,infra}/__init__.py` 解决 module-namespace 冲突
> - **519 ruff violations → 0**: `ruff --fix` 修 369, `--unsafe-fixes` 修 95, `--add-noqa F403` 加 55 条 re-export 注释
> - **knip 1 unused file + 1 unused type**: 删 `QualityAnnotation` 的 `export`(truly internal),knip.json 配置 hint 仅剩 2 个 advisory
> - **file-size 2 个 oversized test files**: `tooling/hygiene/check_file_size.py` ALLOWLIST 加 2 条 (Phase 125 注释)
> - Phase 122-124 carryover list 同步:`docs/superpowers/specs/2026-08-27-phase-124-target-architecture-design.md` 已落地,v16.0 plan 在 `docs/superpowers/plans/`
> - Tests:3739 collected (从 3481 + 16 errors → 3739 + 0 errors)+ 1731 vitest + ruff 0 + vue-tsc 0 + eslint 0 + knip 0(只 advisory hints)
> - Lessons:`# PHASE-COMPAT:` shim 注释 + ALLOWLIST Phase 编号 是 v16.x cleanup 时的 `grep` 锚点 / `tests/__init__.py` 是 pytest module-namespace 冲突的根治 / ruff `--add-noqa` 是处理 `__init__.py` star-import 的标准做法

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.12+ / FastAPI / SQLite |
| 前端 | Vue 3 + Pinia / TypeScript strict / Naive UI |
| 包管理 | pnpm workspace（前端）/ + pip（后端） |
| 测试 | pytest（后端）/ Vitest + Playwright（前端） |
| 质量 | ruff / ESLint / vue-tsc --noEmit / knip |

## 核心命令

```bash
# 前端（apps/dashboard/）
pnpm vitest run            # 单元 + 组件测试
pnpm tsc --noEmit          # TypeScript 类型检查
pnpm exec knip             # 死代码检测
pnpm build                 # 构建
pnpm dev                   # 启动开发服务器（HMR）

# 后端（必须用 miniconda3 python 3.13 + fastapi）
/home/ailearn/miniconda3/bin/python -m pytest tests/ -v

# knip（root）
pnpm knip                  # 委托 apps/dashboard 跑 knip

# Phase 119 验收 (world subtree)
pnpm vitest run tests/unit/components/world/ tests/unit/composables/use-world-agent.spec.js tests/unit/pages/world-page.spec.ts tests/unit/stores/useWorldStore.spec.js
/home/ailearn/miniconda3/bin/python -m pytest tests/infra/world_db/ apps/studio_api/tests/test_world_route.py -v
```

## 关键路径

### Write Workspace (Phase 115)

| 路径 | 用途 |
|------|------|
| `apps/dashboard/src/pages/WriteWorkspacePage.vue` | 沉浸写作工作台入口（v1 主交付） |
| `apps/dashboard/src/components/writeWorkspace/` | Write Workspace 9 个组件 |
| `apps/dashboard/src/stores/useWriteWorkspaceStore.js` | Pinia store |
| `apps/dashboard/src/composables/` | 7 个 write-workspace composables |
| `apps/dashboard/src/utils/writeWorkspace/` | serializer / sceneParser / wordCounter / schema |
| `apps/studio_api/` | FastAPI app 入口（write-workspace router 已注册） |
| `infra/persistence/write_chapter.py` | 章节原子写 Python 端点 |
| `infra/persistence/write_workspace_api.py` | FastAPI router (`/api/write/:id`) |

### World (Phase 117 + 118 + 119)

| 路径 | 用途 |
|------|------|
| `apps/dashboard/src/pages/WorldPage.vue` | 世界可视化入口 (`/world`, 4 tabs) |
| `apps/dashboard/src/components/world/` | 9 组件 (WorldTabs / WorldProposalInbox / WorldImportExport / FactionGraph + 4 detail × 2-3 each + Lore/Timeline Editor) |
| `apps/dashboard/src/composables/world/` | 4 composables (useWorldDb / useWorldReview / useWorldImportExport / useWorldAgent 真实 fetch + fetchChapterTexts) |
| `apps/dashboard/src/stores/useWorldStore.js` | Pinia world store |
| `apps/studio_api/routes/world.py` | FastAPI `/api/world/*` (9 GET/POST + 2 agent extraction + chapter texts bulk + per-IP rate limiter) |
| `infra/world_db/` | World DB SQLite + markdown round-trip + LLM agent |
| `infra/world_db/queries/_helpers.py` | Phase 118 DRY helpers (now_iso / row_to_dict / RevisionConflict) |
| `infra/world_db/agent_schemas.py` | Phase 118 Pydantic schemas for LLM 输出 |
| `infra/world_db/agent_extractors.py` | Phase 118 真实 LLM 调用 (chapters / prompt 两条路) |

### Spec + Handoff

| 路径 | 用途 |
|------|------|
| `docs/superpowers/specs/2026-08-26-phase-119-task-a-design.md` | Phase 119 Task A (LoreEditor/TimelineEditor wiring) design |
| `docs/superpowers/specs/2026-08-26-phase-119-task-b-design.md` | Phase 119 Task B (chapterRange → chapterTexts) design |
| `docs/superpowers/specs/2026-08-26-phase-119-task-c-design.md` | Phase 119 Task C (rate limiter per-IP) design |
| `docs/superpowers/specs/2026-08-26-phase-118-handoff.md` | Phase 118 v15.3 handoff (历史) |
| `docs/superpowers/specs/2026-08-26-immersive-write-workspace-design.md` | v1 设计稿 |
| `docs/superpowers/plans/2026-08-26-immersive-write-workspace.md` | v1 实施计划 |
| `.lingwen/architecture.yml` | AI 协作结构化配置（最高优先级参考） |

## 已知遗留

- **Prod preview regression** (Phase 114 accepted)：cytoscape-fcose CJS 与 rollup commonjs 插件不兼容，5 个 phase 投入失败。dev baseline 仍是 authoritative measurement。E2E Playwright runtime 暂时阻塞。
- **vis-network install on fresh clone** (Phase 118 发现)：fresh checkout 下 `apps/dashboard/node_modules/` 缺 vis-network, 跑 frontend test 全失败。必须 `cd apps/dashboard && pnpm install`。

---

> **版本记录**：
> - v15.4 (2026-08-26)：Phase 119 World follow-up 闭环 — LoreEditor/TimelineEditor 接入 Detail 页面 (Task A) + chapterRange → chapterTexts UI 接线 (Task B) + Rate limiter per-IP scoping (Task C) + Phase 117 ruff I001 清理。14 commits。Tests backend 35→38 / frontend 1724+1→1731+1。详见各 task spec。
> - v15.3 (2026-08-26)：Phase 118 World LLM Agent + cleanup 闭环 — DRY helpers (#14/15) + create_relationship deterministic id (#16) + LLM-backed agent extraction (#17)。3 commits。Tests 19→35 backend, +5 useWorldAgent frontend。详见 `docs/superpowers/specs/2026-08-26-phase-118-handoff.md`。
> - v15.2 (2026-08-26)：Phase 117 World Visualization v1 闭环 — /world 4-tab 页面 + 势力图 (vis-network lazy) + Proposal inbox (human + agent) + Markdown round-trip。Tests backend +19 / frontend world +26。
> - v15.0 (2026-08-26)：Phase 115 Immersive Write Workspace v1 闭环 — /write/:chapterId + TipTap 编辑器 + Scrivener 3-pane + AI 抽屉 + 5-agent 兼容契约。Tests 1545 → 1614 (+69)。
> - v14.2 (2026-08-26)：Phase 114 prod Web Vitals 终结。dev baseline (Phase 106) 正式 authoritative。
> - v14.0 (2026-08-25)：Phase 99-105b knip-follow-up 闭环。knip gate 全 7 categories = 0。
> - v13.0 (2026-08-20)：Phase 60-67 dashboard 基础设施重构完成。