# 灵文 · 工业化小说生产系统

> **版本**: v15.3 (Phase 118 World LLM Agent + cleanup 闭环)
  → v15.2 (Phase 117 World Visualization v1)
  → v15.1 (Phase 116 follow-up 闭环)
  → v15.0 (Phase 115 创作端 UX 子项目 #1 闭环)
  → v14.2 (Phase 114 prod Web Vitals 终结)
  → v14.0 (Phase 99-105b knip-follow-up 闭环完成)
  → v13.0 (Phase 60-67 dashboard 基础设施重构完成)

> **更新 (2026-08-26)**：Phase 118 v15.3 闭环——3 commits (`8269e081` / `1366aedc` / `37343188`)：
  - **Task #14 + #15** DRY helpers + RevisionConflict 基类：`infra/world_db/queries/_helpers.py` 提供 `now_iso()` + `row_to_dict(row, json_fields)` + `RevisionConflict` 基类。6 个 query 文件 import, 净 -49 行。`CHARACTER_REVISION_CONFLICT` alias 保留。
  - **Task #16** `create_relationship` deterministic id：用 follow-up SELECT 替换 implementation-dependent `cur.lastrowid`。新增 idempotency test。
  - **Task #17** LLM-backed agent extraction：替换 Phase 117 stub。`infra/world_db/agent_schemas.py` (Pydantic v2) + `agent_extractors.py` 真 LLM 调用 (`extract_proposals_from_chapters` + `extract_proposals_from_prompt`) + 2 new POST routes (`/api/world/agent/extract-from-chapters|prompt`) + `_AgentRateLimiter` (5 calls/session) + `useWorldAgent.js` 真 fetch。Cost guards: max_chapters=10, max_tokens=4000, rate limit。
  Tests 19 → 35 backend (+16) / world frontend +5 useWorldAgent。vue-tsc: 0 errors。ESLint: 0 warnings。ruff: Phase 118 files clean。
  副产物：发现并文档化 vis-network install regression（fresh clone 必须 `pnpm install` in apps/dashboard/）。

> **上一里程碑 (v15.2, Phase 117)**：World Visualization v1：/world 顶级页面 + 4 tabs（人物 / 势力 / 时间线 / 世界书）+ vis-network 势力关系图（lazy-loaded）+ Human + agent 双轨 Proposal inbox + Markdown round-trip import/export。
  新增 6 张 SQLite 表 + 6 queries 模块 + 4 serializers + 19 backend tests。Frontend: WorldPage + 9 components + 4 composables + 1 Pinia store。
  E2E tests 在 place 但因 Phase 114 prod preview regression 暂时 blocking 运行时（dev baseline 仍 authoritative）。

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

# 后端
pytest tests/ -v

# knip（root）
pnpm knip                  # 委托 apps/dashboard 跑 knip
```

## 关键路径

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
| `apps/dashboard/src/pages/WorldPage.vue` | 世界可视化入口 (Phase 117 /world) |
| `apps/dashboard/src/components/world/` | 人物 / 势力 / 时间线 / 世界书 组件 |
| `apps/dashboard/src/composables/world/` | 4 个 world composables (Db / Review / ImportExport / Agent 真实 LLM 调用) |
| `apps/dashboard/src/stores/useWorldStore.js` | Pinia world store |
| `apps/studio_api/routes/world.py` | FastAPI /api/world/* routes (含 2 个 agent extraction routes + rate limiter) |
| `infra/world_db/` | World DB SQLite + markdown round-trip + LLM agent |
| `infra/world_db/queries/_helpers.py` | Phase 118 DRY helpers (now_iso / row_to_dict / RevisionConflict) |
| `infra/world_db/agent_schemas.py` | Phase 118 Pydantic schemas for LLM 输出 |
| `infra/world_db/agent_extractors.py` | Phase 118 真实 LLM 调用 (取代 Phase 117 stub) |
| `docs/superpowers/specs/2026-08-26-phase-118-handoff.md` | Phase 118 v15.3 handoff |
| `docs/superpowers/specs/2026-08-26-immersive-write-workspace-design.md` | v1 设计稿 |
| `docs/superpowers/plans/2026-08-26-immersive-write-workspace.md` | v1 实施计划 |
| `.lingwen/architecture.yml` | AI 协作结构化配置（最高优先级参考） |

## 已知遗留

- **Prod preview regression** (Phase 114 accepted)：cytoscape-fcose CJS 与 rollup commonjs 插件不兼容，5 个 phase 投入失败。dev baseline 仍是 authoritative measurement。E2E Playwright runtime 暂时阻塞。
- **LoreEditor / TimelineEditor 接入** (Phase 117 任务 #18/19 输出)：Editor 组件 standalone, 未接入 LoreDetail / TimelineEventDetail 页面。需在详情页加 "编辑" toggle, 仿 CharacterDetail → CharacterEditor 模式。
- **chapterRange → chapterTexts 接线** (Phase 118 follow-up)：前端 `extractFromChapters(slug, chapterRange)` 的 chapterRange 未在 UI 里 resolve 成实际章节文本。`WorldProposalInbox` 需加 wiring。
- **Rate limiter per-IP scoping** (Phase 118 follow-up)：现行 `_AgentRateLimiter` 是 process-global, 5 calls/session 限制过宽。生产化需按 `request.client.host` 分桶。
- **vis-network install on fresh clone** (Phase 118 发现)：fresh checkout 下 `apps/dashboard/node_modules/` 缺 vis-network, 跑 frontend test 全失败。必须 `cd apps/dashboard && pnpm install`。
- **Phase 117 ruff I001 in `test_markdown_roundtrip.py`**：1 行遗留 (import order), 本 phase 不修, 留独立 commit。

---

> **版本记录**：
> - v15.3 (2026-08-26)：Phase 118 World LLM Agent + cleanup 闭环 — DRY helpers (#14/15) + create_relationship deterministic id (#16) + LLM-backed agent extraction (#17)。3 commits。Tests 19→35 backend, +5 useWorldAgent frontend。详见 `docs/superpowers/specs/2026-08-26-phase-118-handoff.md`。
> - v15.2 (2026-08-26)：Phase 117 World Visualization v1 闭环 — /world 4-tab 页面 + 势力图 (vis-network lazy) + Proposal inbox (human + agent) + Markdown round-trip。Tests backend +19 / frontend world +26。
> - v15.0 (2026-08-26)：Phase 115 Immersive Write Workspace v1 闭环 — /write/:chapterId + TipTap 编辑器 + Scrivener 3-pane + AI 抽屉 + 5-agent 兼容契约。Tests 1545 → 1614 (+69)。
> - v14.2 (2026-08-26)：Phase 114 prod Web Vitals 终结。dev baseline (Phase 106) 正式 authoritative。
> - v14.0 (2026-08-25)：Phase 99-105b knip-follow-up 闭环。knip gate 全 7 categories = 0。
> - v13.0 (2026-08-20)：Phase 60-67 dashboard 基础设施重构完成。