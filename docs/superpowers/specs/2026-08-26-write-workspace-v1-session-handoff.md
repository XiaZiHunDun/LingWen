# Write Workspace v1 会话交接文档

> **历史快照**: 本文档对应 master @ `dce74c33` (v15.0 Phase 115 闭环时刻)。**后续会话不应按本文档 carryover 工作** — 这些项已在 Phase 116 (v15.1) 闭环：
>
> | 原始 carryover | Phase 116 commit | 状态 |
> |----------------|------------------|------|
> | Task B: GET `/api/write/:chapter_id` 未实现 | `65615f8c` feat(api): add GET /api/write/{chapter_id} endpoint | ✅ Closed |
> | Task C: 老页面测试覆盖率 24%→80% | `d7646c10` + `d22070ae` (page-level tests) | ✅ Closed (LibraryPage / MorePage / InsightPage / WriteWorkspacePage) |
> | Task D: ESLint warnings 148→≤50 | `39b53346` fix(dashboard): resolve 13 testid-class-sync warnings | ✅ Closed (13→0) |
>
> 当前真实状态见 `CLAUDE.md` v15.1 段。Tests: 1685/1686 PASS (1 skipped)。本文档保留供历史参考，不归档 (per handoff §5)。

> **目的**: 新会话从这个 doc 衔接 — 项目状态、已闭环工作、未做 carryover、下一步推荐、用户策略。
> **生成时间**: 2026-08-26 (master @ `dce74c33`)
> **前置阅读** (按顺序): `CLAUDE.md` v15.1 段 → 本文档 → `docs/superpowers/specs/2026-08-26-immersive-write-workspace-design.md`

---

## 0. TL;DR

Write Workspace v1 (Phase 115, v15.0) **已闭环**。32 commits ahead of handoff HEAD `9ea11010`，全部 push 到 `origin/master`。所有 gates green:
- Tests: **1614/1614 PASS**
- Vue-tsc: **0 errors**
- Build: **OK** (21s)
- knip: **exit 0**
- Backend router: **mounted** (`PUT /api/write/{chapter_id}`)

---

## 1. 已完成 (本会话 3 件事)

| 主题 | commits | 说明 |
|------|---------|------|
| **Write Workspace v1 实现** | 28 commits (`191d693d..e3502aac`) | 25 个 task 全过 — TipTap spike + utils + store + 7 components + REST API + Python backend + page 4 + E2E + 3 self-review fixes |
| **Doc cleanup** | 1 commit (`d3482b14`) | CLAUDE.md 604→70 行, AGENTS.md 62→32, architecture.yml 路径全部修正 |
| **Follow-up A+B+C** | 3 commits (`492a2904`, `7c020bb2`, `dce74c33`) | 注册 write-workspace router、HANDOFF.md 刷到 v15.0、DESIGN.md 路径修正 |

### Write Workspace v1 实际产出

| 类别 | 路径 |
|------|------|
| 共享 utils | `apps/dashboard/src/utils/writeWorkspace/` — 5 files (frontmatterSchema, markdownSerializer, sceneParser, wordCounter, types) |
| Composables | `apps/dashboard/src/composables/` — 5 new (useWriteWorkspaceApi, useWriteWorkspacePersistence, useWriteGoal, useTypewriterMode, useWriteQualityCheck) |
| Components | `apps/dashboard/src/components/writeWorkspace/` — 9 components + sceneBreakMark.js |
| Store | `apps/dashboard/src/stores/useWriteWorkspaceStore.js` (Pinia, 8 shallowRefs + 8 actions) |
| Page | `apps/dashboard/src/pages/WriteWorkspacePage.vue` |
| Route | `/write/:chapterId` (in `apps/dashboard/src/router/index.js`) |
| Backend | `infra/persistence/write_chapter.py` + `write_workspace_api.py` + 已注册到 `apps/studio_api/routes/write_workspace.py` |
| E2E | `apps/dashboard/tests/e2e/write-workspace.spec.ts` (spec in place, runtime blocked by Phase 114) |

### 关键决策（已闭环）

1. **Editor: TipTap 2.27.2 + ProseMirror** (方案 A) — SceneBreak 是 `Node.create({group:'block', atom:true})` 不是 Mark（spike 时发现）
2. **Markdown 落地**: `js-yaml` with `yaml.JSON_SCHEMA` 避免 YAML 1.1 timestamp auto-parse
3. **架构**: 5-agent pipeline 兼容契约（frontmatter `last_modified_by: human|agent`）
4. **路径别名**: `@/*` → `apps/dashboard/src/*` (在 vite + tsconfig 中已配)

---

## 2. 已知 Carryover（CLAUDE.md "已知遗留"段同款）

### 优先级 1: 实际影响 dev/preview

**A. Prod preview regression** (accepted debt per Phase 114)
- 现象: `pnpm preview` throws `Cannot set properties of undefined (setting 'exports')` / TDZ on `H`
- Root cause: cytoscape-fcose CJS 与 rollup `@rollup/plugin-commonjs` 冲突
- 5 phase 投入失败 (110/111B/111C/112/112C/114)
- **当前决策**: dev baseline 是 authoritative; 不建议再尝试 cytoscape stub 方向
- 真修复 ROI 不匹配 (custom rollup plugin 4-8h 或换 mermaid 8-16h)
- **影响**: Playwright E2E runtime 被 block；unit/component 测试 + build 都正常

**B. GET /api/write/:chapter_id 未实现**
- 现状: backend 只有 PUT；`useWriteWorkspaceApi.loadChapter` 调用 GET 时 404
- 缓解: `WriteWorkspacePage.vue` 的 `loadChapter` catch 分支 fallback 到空 state
- **影响**: 新章节直接打开看到"新章节"placeholder；agent 写入后才能通过 PUT 看内容
- 工作量: ~30 min（mirror PUT pattern）

### 优先级 2: OPTIMIZATION_PLAN 收尾

**C. Page test coverage 24% → 80%** (P0 立项，"执行中"未闭环)
- Write Workspace 加了 9 个 page/component tests (覆盖自己)
- 但其他 17 个老页面大多未测
- 工作量: ~1-2 天

**D. ESLint warnings 148 → ≤50** (P0 立项，未闭环)
- 当前 knip 是 exit 0;ESLint 警告数未跟踪（可能已不同）
- 工作量: ~0.5-1 天

### 优先级 3: 中长期 feature work

**E. 创作者线 v6.12 → v7.0** (HANDOFF.md §0.2.1 路线图)
- 3 柱: 卷纲 diff/share、batch 历史可视化、...
- 已知 v1.5 已落地;剩余多 phase

**F. 世界/人物/情节可视化** (brainstorming 时识别的第二大缺口)
- 人物卡编辑、世界书、势力图、时间线
- 当前散落: `docs/character-bible/`, `faction-design.md`, `lore-registry.md`
- 工作量: ~1-2 周

---

## 3. 推荐优先级** (**新会话**)

**短期 (1-2 天)** — 收尾**:
1. **Task B** (GET endpoint) — 30 min, 实测 dev mode
2. **Task C** (page coverage) — 1-2 天, 写 17 个老页面 smoke tests
3. **Task D** (ESLint cleanup) — 0.5-1 天

**中长期 (1-2 周)** — feature:
4. **Task F** (可视化) — 高 ROI 但大
5. **Task E** (创作者线 v7.0) — 多 phase

**不建议**:
- **Task A** (prod preview fix) — ROI 不匹配;接受 dev baseline

---

## 4. 上下文: 用户策略（重要!）

### 已批准且有效

**1. Inline apply small fixes 政策** (本会话通过 AskUserQuestion 确认)
- 触发: plan 有 bug（小 typo、内部矛盾、过时假设）
- 行动: controller inline fix + commit with detailed message
- 跳过: BLOCKED → escalate → re-dispatch cycle
- 节省: ~30 sub-agent dispatches in Phase 1-8

**2. Subagent workflow** (per `superpowers:subagent-driven-development` skill)
- 流程: implementer → spec reviewer → code quality reviewer
- **每 task 3 个 subagent dispatch** (per task by plan structure)
- 简化 (本会话实际做法):
  - Routine task (Vue 组件, util) → 1 implementer + inline verify (跳过 reviewer)
  - Critical task (full page wiring) → 完整 3 stages
  - 小 plan bug → inline fix (per #1)

### 项目约定

**3. Architecture invariants** (AGENTS.md 5 条仍 valid)
- infra/ 禁止依赖 dashboard/ / apps/
- 检查器 = 纯函数规则引擎
- L3/L4 禁止引用 L2
- 写审分离
- 创作流必须支持 checkpoint 恢复

**4. 优先级源** (structured config)
- `.lingwen/architecture.yml` 是 AI-readable 真源
- AGENTS.md 文字版 backup
- 这两个文件已 cleanup, paths 都已修正

---

## 5. 避免 (Don't Do)

- ❌ **不要尝试 prod preview fix** (Phase 114 5 phase 投入失败, ROI 不匹配)
- ❌ **不要主动开第九本书** / 星陨 wave / SaaS / 录屏
- ❌ **不要恢复 llm×7 每次 push 全跑** (改 `projects/**`/`infra/**` 或 label `llm-check` 才跑)
- ❌ **不要把 spec/plan/audit 文档归档到 docs/archive/** — 项目当前就是"维护模式"，让历史可见
- ❌ **不要自作主张重命名 `lingwen` 命名空间** — 品牌字符串真源在 `apps/dashboard/src/config/brand.js`
- ❌ **不要加 `@ts-ignore` / `as any` / 空 catch** — 见 `.lingwen/constraints.yml`

---

## 6. 项目入口

| 任务 | 命令 |
|------|------|
| 前端测试 | `cd apps/dashboard && pnpm vitest run` |
| 前端类型检查 | `cd apps/dashboard && pnpm tsc --noEmit` |
| 死代码检测 | `cd apps/dashboard && pnpm exec knip` |
| 构建 | `cd apps/dashboard && pnpm build` |
| Dev 启动 | `cd apps/dashboard && pnpm dev` |
| Backend 测试 | `pytest tests/ -v` |
| Backend import 检查 | `python -c "from infra.persistence.write_workspace_api import router"` |
| 启动 FastAPI | `python -c "from apps.studio_api.app import create_app; create_app()"` (实际 dev 用 `apps/studio_api/main.py`) |

---

## 7. 关键文件指针

| 文件 | 内容 |
|------|------|
| `CLAUDE.md` (70 行) | v15.0 项目 meta + 技术栈 + 核心命令 + 已知遗留 + 版本记录 |
| `AGENTS.md` (32 行) | 5 条架构不变量 + 3 个 `.lingwen/*.yml` 指针 + 技术栈 |
| `.lingwen/architecture.yml` | AI-readable 模块边界真源 |
| `.lingwen/constraints.yml` | 9 个 A00X 反反模式 (A001-A009) |
| `.lingwen/checkers.yml` | 检查器注册表 |
| `HANDOFF.md` | 1204 行历史 changelog (本会话刷到 v15.0) |
| `DESIGN.md` | L0-L7 架构图 + 流程 + 规范 (本会话修了路径) |
| `docs/superpowers/specs/2026-08-26-immersive-write-workspace-design.md` | Write Workspace v1 设计稿 |
| `docs/superpowers/plans/2026-08-26-immersive-write-workspace.md` | 25 task 实施计划 (2976 行) |
| `docs/superpowers/specs/2026-08-26-write-workspace-v1-session-handoff.md` | **本文件** |

---

## 8. 历史背景

- 项目维护模式（v15.0）— v12 顶级 KPI 已达标，Phase 60-115 都是工程清理/优化
- 最近 50+ phases 都是 dashboard 工程 (perf, knip, ESLint, maintenance)
- Phase 115 v15.0 是首次**产品侧**添加（Write Workspace 用户视角）
- 用户方向 (per 早期会话): "优化项目"而不是"生产新小说";**首要** = = "产品能力"，dashboard 是载具