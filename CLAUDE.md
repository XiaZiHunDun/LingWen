# 灵文 · 工业化小说生产系统

> **版本**: v15.5 (Phase 120 LLM provider benchmark 闭环)
  → v15.4 (Phase 119 World follow-up 闭环)
  → v15.3 (Phase 118 World LLM Agent + cleanup 闭环)
  → v15.2 (Phase 117 World Visualization v1)
  → v15.1 (Phase 116 follow-up 闭环)
  → v15.0 (Phase 115 创作端 UX 子项目 #1 闭环)
  → v14.2 (Phase 114 prod Web Vitals 终结)
  → v14.0 (Phase 99-105b knip-follow-up 闭环完成)
  → v13.0 (Phase 60-67 dashboard 基础设施重构完成)

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

> **品牌**：本仓库的产品名是 **墨灵 Studio**（"墨灵"），内部框架名是 **灵文引擎**（"灵文"）。工程命名空间沿用历史 `lingwen`（包名 / import path / Python module 全部使用 `lingwen`，不要改成 `moling`）。品牌字符串真源在 `apps/dashboard/src/config/brand.js`。

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