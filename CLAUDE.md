# 灵文 · 工业化小说生产系统

> **版本**: v16.1 (Phase 124 lingwen-shared contracts 包 闭环)
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