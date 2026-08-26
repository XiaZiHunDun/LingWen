# 灵文 · 工业化小说生产系统

> **版本**: v15.1 (Phase 116 follow-up 闭环)
  → v15.0 (Phase 115 创作端 UX 子项目 #1 闭环)
  → v14.2 (Phase 114 prod Web Vitals 终结)
  → v14.0 (Phase 99-105b knip-follow-up 闭环完成)
  → v13.0 (Phase 60-67 dashboard 基础设施重构完成)

> **更新 (2026-08-26)**：Phase 116 v15.1 follow-up 闭环——
  - Task B: GET `/api/write/{chapter_id}` 端点（mirror PUT 模式）+ `read_chapter()` 函数 + 7 路由测试；frontend `loadChapter()` 404 fallback 移除。
  - Task C: LibraryPage / MorePage / InsightPage page-level 测试 47 条；WriteWorkspacePage 测试 25 条 (Task W-1)。
  - Task D: writeWorkspace 组件 testid-class-sync warnings 13 → 0。
  新增 5 commits ahead of v15.0。Tests: 1685/1686 PASS (+71 over v15.0, 1 skipped — Pinia watcher mock limit)。Vue-tsc: 0 errors。Build: OK。knip: clean。ESLint: 0 warnings。
  覆盖提升 (单页): LibraryPage 9%→95%, MorePage 25%→93%, InsightPage 68%→96%, WriteWorkspacePage 0%→85%。

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
| `docs/superpowers/specs/2026-08-26-immersive-write-workspace-design.md` | v1 设计稿 |
| `docs/superpowers/plans/2026-08-26-immersive-write-workspace.md` | v1 实施计划 |
| `.lingwen/architecture.yml` | AI 协作结构化配置（最高优先级参考） |

## 已知遗留

- **Prod preview regression** (Phase 114 accepted)：cytoscape-fcose CJS 与 rollup commonjs 插件不兼容，5 个 phase 投入失败。dev baseline 仍是 authoritative measurement。E2E Playwright runtime 暂时阻塞。

---

> **版本记录**：
> - v15.1 (2026-08-26)：Phase 116 follow-up 闭环 — GET `/api/write/:id` 端点 (Task B) + 4 个 page-level tests 72 条 (Task C + W-1) + ESLint warnings 13→0 (Task D)。Tests 1614 → 1685 (+71)。
> - v15.0 (2026-08-26)：Phase 115 Immersive Write Workspace v1 闭环 — /write/:chapterId + TipTap 编辑器 + Scrivener 3-pane + AI 抽屉 + 5-agent 兼容契约。Tests 1545 → 1614 (+69)。
> - v14.2 (2026-08-26)：Phase 114 prod Web Vitals 终结。dev baseline (Phase 106) 正式 authoritative。
> - v14.0 (2026-08-25)：Phase 99-105b knip-follow-up 闭环。knip gate 全 7 categories = 0。
> - v13.0 (2026-08-20)：Phase 60-67 dashboard 基础设施重构完成。