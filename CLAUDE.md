# 灵文 · 工业化小说生产系统

> **版本**: v15.2 (Phase 117 World Visualization v1)
  → v15.1 (Phase 116 follow-up 闭环)
  → v15.0 (Phase 115 创作端 UX 子项目 #1 闭环)
  → v14.2 (Phase 114 prod Web Vitals 终结)
  → v14.0 (Phase 99-105b knip-follow-up 闭环完成)
  → v13.0 (Phase 60-67 dashboard 基础设施重构完成)

> **更新 (2026-08-26)**：Phase 117 v15.2 World Visualization v1 闭环——
  - /world 顶级页面 + 4 tabs（人物 / 势力 / 时间线 / 世界书）。
  - vis-network 势力关系图（lazy-loaded，避免 cytoscape 体积问题）。
  - Human + agent 双轨 Proposal inbox：人工编辑走 CharacterEditor；agent 走 `extract_proposals_from_chapters()` stub（Phase 118 接 LLM）。
  - Markdown round-trip import/export：character-bible / faction-design / lore-registry 三源 idempotent 导入。
  新增 6 张 SQLite 表（characters / factions / relationships / lore / timeline / proposals）+ 6 queries 模块 + 4 serializers + 19 backend tests。
  Frontend: WorldPage + 9 components + 4 composables + 1 Pinia store + 11 routing tests。Phase 117 全 19 backend + 26 frontend world tests PASS。
  Vue-tsc: 0 errors。ESLint: 0 warnings。ruff: Phase 117 文件 clean。knip: existing items only (无 new dead code)。

> **上一里程碑 (v15.0, Phase 115)**：Immersive Write Workspace v1：/write/:chapterId 路由 + TipTap 长文编辑器 + 章节-场景两级 + Markdown 落地 + Author/Editor 双模式 + Scrivener 3-pane + AI 侧栏抽屉 + 5-agent 兼容契约。
  新增 4 composables + 1 store + 8 components + 1 共享 front-matter schema + 1 Python atomic write backend。
  详见 `docs/superpowers/specs/2026-08-26-immersive-write-workspace-design.md` 与 `docs/superpowers/plans/2026-08-26-immersive-write-workspace.md`。
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
| `apps/dashboard/src/composables/world/` | 4 个 world composables (Db / Review / ImportExport / Agent stub) |
| `apps/dashboard/src/stores/useWorldStore.js` | Pinia world store |
| `apps/studio_api/routes/world.py` | FastAPI /api/world/* routes |
| `infra/world_db/` | World DB SQLite + markdown round-trip + agent stub |
| `docs/superpowers/specs/2026-08-26-immersive-write-workspace-design.md` | v1 设计稿 |
| `docs/superpowers/plans/2026-08-26-immersive-write-workspace.md` | v1 实施计划 |
| `.lingwen/architecture.yml` | AI 协作结构化配置（最高优先级参考） |

## 已知遗留

- **Prod preview regression** (Phase 114 accepted)：cytoscape-fcose CJS 与 rollup commonjs 插件不兼容，5 个 phase 投入失败。dev baseline 仍是 authoritative measurement。E2E Playwright runtime 暂时阻塞。

---

> **版本记录**：
> - v15.2 (2026-08-26)：Phase 117 World Visualization v1 闭环 — /world 4-tab 页面 + 势力图 (vis-network lazy) + Proposal inbox (human + agent) + Markdown round-trip。Tests backend +19 / frontend world +26。
> - v15.1 (2026-08-26)：Phase 116 follow-up 闭环 — GET `/api/write/:id` 端点 (Task B) + 4 个 page-level tests 72 条 (Task C + W-1) + ESLint warnings 13→0 (Task D)。Tests 1614 → 1685 (+71)。
> - v15.0 (2026-08-26)：Phase 115 Immersive Write Workspace v1 闭环 — /write/:chapterId + TipTap 编辑器 + Scrivener 3-pane + AI 抽屉 + 5-agent 兼容契约。Tests 1545 → 1614 (+69)。
> - v14.2 (2026-08-26)：Phase 114 prod Web Vitals 终结。dev baseline (Phase 106) 正式 authoritative。
> - v14.0 (2026-08-25)：Phase 99-105b knip-follow-up 闭环。knip gate 全 7 categories = 0。
> - v13.0 (2026-08-20)：Phase 60-67 dashboard 基础设施重构完成。