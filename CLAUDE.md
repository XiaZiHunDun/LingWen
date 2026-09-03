# 灵文 · 工业化小说生产系统

> **版本**: v25.4 (Phase 25.4 收尾) · 更新: 2026-09-03
> 当前状态: `collaboration/CURRENT_STATUS.md` · 待办: `collaboration/BACKLOG.md` · 版本史: `docs/superpowers/archive/PHASE_HISTORY.md`
> 最高优先级参考: `.lingwen/architecture.yml`

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.12+ / FastAPI / SQLite / uv workspace (packages/lingwen-* + apps/studio_api) |
| 前端 | Vue 3 + Pinia / TypeScript strict / Naive UI |
| 包管理 | pnpm workspace（前端）/ uv workspace（后端） |
| 测试 | pytest（后端）/ Vitest（前端） |
| 质量 | ruff / ESLint / vue-tsc --noEmit / knip |

> Python 基线：架构声称 3.12+（`.lingwen/architecture.yml` core 层 `tech: [Python3.12, SQLite]`）；`pyproject.toml` 的 `requires-python >= 3.11` 为下界。本机 local 实际可为 3.13，统一用 `uv run` 执行，勿硬编码 conda / miniconda 绝对路径。

## 核心命令

```bash
# 前端（apps/dashboard/）
pnpm vitest run            # 单元 + 组件测试
pnpm tsc --noEmit          # TypeScript 类型检查
pnpm exec knip             # 死代码检测
pnpm build                 # 构建
pnpm dev                   # 启动开发服务器（HMR）

# 后端（uv workspace，勿用 miniconda 绝对路径）
uv run pytest tests/ -v                                      # 全量后端测试
uv run pytest apps/studio_api/tests/ -v                      # 网关层测试

# knip（root）
pnpm knip                  # 委托 apps/dashboard 跑 knip

# CLI 健康检查
python lingwen.py doctor
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

## 架构不变量

| ID | 约束 |
|----|------|
| I001 | `infra/` 禁止 import `apps/`（单向依赖） |
| I002 | 检查器 = 纯函数规则引擎，禁止调用 LLM / AI 服务 |
| I003 | L3/L4 免疫侧禁止引用 L2 创作侧 |
| I004 | 写审分离（独立 AI 会话，无作者 CLAIM 访问） |
| I005 | 创作流必须支持 checkpoint 恢复 |
| I048 | PilotPage 独占 batch 生命周期 |

> 完整不变量与设计原则 DP-01..06 见 `.lingwen/architecture.yml`；提交纪律与反模式见 `.lingwen/constraints.yml`。

## 品牌与命名

- **产品名**：灵文工作室（用户可见 UI 标题、侧栏副标题、对外文档统一使用）。
- **工程命名空间**：沿用历史 `lingwen`（包名 / import path / Python module 全部使用 `lingwen`，**不要改成 moling**）。
- 显示串真源 `apps/dashboard/src/config/brand.js` 目前仍为「墨灵 Studio」——为范围外遗留，待后续统一。

## 文档入口

| 文档 | 作用 |
|------|------|
| `collaboration/CURRENT_STATUS.md` | 当前状态 / 已完成 |
| `collaboration/BACKLOG.md` | 待办 backlog |
| `docs/superpowers/handoffs/` | 各 phase 详细 handoff（52 个） |
| `docs/superpowers/archive/PHASE_HISTORY.md` | 版本史 / phase 归档（本文件不再承载版本史） |
| `.lingwen/architecture.yml` | 架构分层 / 边界 / 约束（最高优先级） |
| `HANDOFF.md` | 切换工具 TL;DR + 交接 |

## 已知遗留

- **Prod preview regression** (Phase 114 accepted)：cytoscape-fcose CJS 与 rollup commonjs 插件不兼容，5 个 phase 投入失败。dev baseline 仍是 authoritative measurement。E2E Playwright runtime 暂时阻塞。
- **vis-network install on fresh clone** (Phase 118 发现)：fresh checkout 下 `apps/dashboard/node_modules/` 缺 vis-network, 跑 frontend test 全失败。必须 `cd apps/dashboard && pnpm install`。

---

> 版本史已整体归档至 `docs/superpowers/archive/PHASE_HISTORY.md`；本文件不再维护版本记录表。