# 灵文 · 工业化小说生产系统

> **版本**: v31.0 (Phase 31 ARCHDEBT-MINI 收尾) · 更新: 2026-09-07
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

- ✅ **v31.0 ARCHDEBT-MINI**（2026-09-07 ff-merge `4dbe8939`，6 commit `8f8c3e1a..4dbe8939`）：P2-ARCHDEBT 子集 2/4 清理。**Sub-task A**：chapter_golden_path 反向 import 修复（create_golden_dashboard_client + run_human_review_smoke + HumanReviewSmokeResult 从 lingwen-core 迁 apps/studio_api/tests/golden_path_smoke.py；-87 行 / +106 行；fixes I001 spirit violation）。**Sub-task B**：4 薄代理 (advance_step/dispatch_task/verify_task/get_workflow_status) 从 WorkflowMixin 抽到 mc_orchestrator_proxy.py；MasterController MRO 加 OrchestratorProxyMixin；+5 refactor-guard tests（test_workflow_state.py）；mc_workflow.py 119→99 行。**12 文件 doc 同步**："5 薄代理" → "4 薄代理"（实际 4 不是 5，Phase 27 拆 WorkflowRunner 后 stale）。详见 `docs/superpowers/handoffs/2026-09-07-phase-31-archdebt-mini-handoff.md`。
- ✅ **v30.0 TACKLE-14-FAILURES**（2026-09-07 ff-merge `38b854e7`，9 commit `2de95a80..38b854e7`）：Phase 29 剩余 14 failed 按 5 类根因一次性清零（ 0 failed / 480 passed / 20 skipped）。**2 真 prod 改动**：`mc_writing.py:155` 加 try/except 韧性契约（broad except + logger.warning + 空 audit report 兜底）+ `cost_persistence.py` 加 `record_at()` public helper（历史数据 seeding / migration / test fixture 用）。**3 test-only 清理**：stub factory `WorkflowState.empty()` 注入（-7）、`make_master_with_router` 替代 bare `MasterController()`（-2）、`WorkflowRunner._harvest_decision_specs` 迁移（-1）+ 2 处 stale assertion 修正。详见 `docs/superpowers/handoffs/2026-09-07-phase-30-tackle-14-handoff.md`。
- ✅ **v29.0 P2-MC-WRITING**（2026-09-07 ff-merge `b1b748ad`，17 commit `106dd21d..b1b748ad`）：恢复 `tests/agent_system` 路径发现 / memory gateway import / dashboard test entry point / stale test patches。84 → 14 failed (-70)，tests/got 156 / lingwen-core 68 / ruff clean 不变；11 测试文件 + **1 真 prod 改动** `packages/lingwen-core/src/lingwen_core/agents/mc_editing.py:202`（Phase 15.0 P3-SPLIT 迁移遗留 `from mc_utils import ...` 旧路径）。详见 `docs/superpowers/handoffs/2026-09-04-phase-29-mc-writing-handoff.md`。
- ✅ **v28.0 P2-RESUME-VERIFY**（2026-09-04 ff-merge）：5 E2E tests 用真实 GoTScheduler + ThoughtGraph 验证 scheduler 幂等 + start_nodes=None derivation + state.start_nodes 持久化 + WorkflowRunner.run→resume 完整 cycle；0 改范围 9 类文件不动。
- ✅ **v27.0 P2-WFRUNNER**（2026-09-04）：`WorkflowRunner` service 从 WorkflowMixin 抽出（workflow_runner.py 307 行 new + mc_workflow.py 404→119 行 -70%）；TDD 21 tests + 2 refactor guards；0 new failure。
- ✅ **v26.0 P2-WFSTATE**（2026-09-04）：`_last_*` 散点 → `WorkflowState` dataclass（with_updates + empty classmethod + 7 字段整合）；0 行为变更；3 refactor guards 防回潮。
- ✅ **v25.9 human_review 流水线修复**（2026-09-03 ff-merge `0a6f4346`）：mc_workflow.py 自仓库迁移后是 hallucinated stub；从 git history `5c4259e5:novel-factory/infra/agent_system/master_controller.py` 还原真实实现，对齐新 GoTScheduler API，解 4 个 dashboard smoke skip + 顺带 +15 cascade fixed。0 改范围（got_bridge.py / chapter_golden_path.py / apps.studio_api/* / infra/got/* / architecture.yml / HANDOFF*.md）。
- **Prod preview regression** (Phase 114 accepted)：cytoscape-fcose CJS 与 rollup commonjs 插件不兼容，5 个 phase 投入失败。dev baseline 仍是 authoritative measurement。E2E Playwright runtime 暂时阻塞。
- **vis-network install on fresh clone** (Phase 118 发现)：fresh checkout 下 `apps/dashboard/node_modules/` 缺 vis-network, 跑 frontend test 全失败。必须 `cd apps/dashboard && pnpm install`。
- **架构债（v25.9/v27/v31 推后，Phase 32+ 候选）**：`infra.got.*` 迁至 `packages/lingwen-got/`；HANDOFF 文档 `latest_decision_queue` 措辞修订；PHASE-COMPAT shim 删除。v31.0 ARCHDEBT-MINI 已清 chapter_golden_path 反向 import + OrchestratorProxyMixin (4 薄代理) 提取。

---

> 版本史已整体归档至 `docs/superpowers/archive/PHASE_HISTORY.md`；本文件不再维护版本记录表。