# Phase 117 v15.2 — World Visualization v1 会话交接文档

> **目的**: 新会话从这个 doc 衔接 — 当前 master 状态、Phase 117 闭环内容、未做 carryover、下一步推荐。
> **生成时间**: 2026-08-26 (master @ `f890706e`)
> **前置阅读** (按顺序): `CLAUDE.md` v15.2 段 → 本文档 → `docs/superpowers/specs/2026-08-26-world-visualization-design.md` → `docs/superpowers/plans/2026-08-26-world-visualization.md`

---

## 0. TL;DR

Phase 117 v15.2 (World Visualization v1) **已闭环并合入 master**。merge commit `f890706e`，26 commits ahead。所有 gates green:

- 后端 tests: **42/42 PASS** (world_db 19 + studio_api 23)
- 前端 tests: **1711/1712 PASS** (+1 历史跳过 = Pinia watcher mock limit, 与 Phase 117 无关)
- vue-tsc: **0 errors**
- ESLint: **0 errors / 0 warnings**
- ruff: Phase 117 文件 clean
- knip: 无新增死代码

---

## 1. 已完成 (本扩展会话)

### 1.1 Phase 116 Tasks B/C/D + W-1 (合入 master)

| Commit | 内容 |
|--------|------|
| `65615f8c` | feat(api): add GET /api/write/{chapter_id} endpoint |
| `dad3f84b` | docs(cleanup): remove stale "Backend FastAPI router 未注册" from CLAUDE.md |
| `d7646c10` | test(dashboard): page-level tests for LibraryPage / MorePage / InsightPage |
| `d22070ae` | test(dashboard): page-level test for WriteWorkspacePage |
| `39b53346` | fix(dashboard): resolve 13 testid-class-sync warnings in writeWorkspace |
| `d2b93b26` | docs(CLAUDE.md): refresh to v15.1 + supersede v1 handoff doc |

### 1.2 Task F (Phase 117 World Visualization) — 完整执行

| Phase | Tasks | 内容 |
|-------|-------|------|
| 设计 + 规划 | brainstorm + spec + plan | `docs/superpowers/{specs,plans}/2026-08-26-world-visualization-{design,plan}.md` (3248 行计划) |
| Phase 1 | 1-3 | `infra/world_db/{schema, queries/{characters,factions,relationships,lore,timeline,proposals}}.py` + 19 backend tests |
| Phase 2 | 4-6 | `infra/world_db/markdown_roundtrip.py` (character parser + faction/lore/timeline serializers + import orchestrator) |
| Phase 3 | 7-10 | `apps/studio_api/routes/world.py` (9 endpoints under /api/world/*) |
| Phase 4-5 | 11-12 | `apps/dashboard/src/{stores/useWorldStore.js, composables/world/*, pages/WorldPage.vue}` + 4 child stubs + router entry |
| Phase 6 | 13-15 | Character tab: list + detail + relationships + editor |
| Phase 7 | 16-17 | Faction tab: list/graph toggle + **vis-network** graph (lazy-loaded) |
| Phase 8 | 18 | Timeline tab: horizontal track + detail + editor |
| Phase 9 | 19 | Lore tab: categorized list + detail + editor |
| Phase 10 | 20-22 | WorldProposalInbox UI + WorldImportExport UI + backend agent extractor stub |
| Phase 11 | 23 | Acceptance gates + CLAUDE.md (v15.2) + architecture.yml + push |

### 1.3 已合并到 master

- merge commit `f890706e` (从 `phase-117/world-v1` 合入)
- 50 个新文件，3308 行新增
- 无合并冲突（3 个潜在冲突文件实际只被 phase-117 新增内容触碰）

---

## 2. 已知遗留 (Phase 118 候选)

### 优先级 1: 代码 review follow-ups (已记录在 tasks #14, #15, #16)

**A. DRY 助手提取** (Task #14)
- `_now()` 在 6 个 query 文件重复 (`characters.py`, `factions.py`, `lore.py`, `timeline.py`, `proposals.py`, `relationships.py`)
- `_row_to_dict` 在 3 个文件重复 (`lore.py`, `timeline.py`, `proposals.py`)
- 建议提取到 `infra/world_db/queries/_helpers.py` (或 `_time.py` / `_rows.py`)

**B. 共享 `RevisionConflict` 异常基类** (Task #15)
- 3 个独立 exception classes: `CharacterRevisionConflict`, `LoreRevisionConflict`, `TimelineRevisionConflict`
- `characters.py:11` 已有 `CHARACTER_REVISION_CONFLICT = CharacterRevisionConflict` alias — 证明作者已意识到冗余
- 建议: 共享基类 `RevisionConflict(Exception)`, 子类只提供更具体的语义

**C. `create_relationship` 在冲突时的 lastrowid 行为** (Task #16)
- `INSERT OR IGNORE` 在 SQLite 上: 冲突时 `lastrowid` 行为不稳定（0 或已存在行的 id）
- 调用方立即 `get_relationship` 可能拿到 None
- 建议: 后续 SELECT 拿真实 id，或文档化 "0 = duplicate"

### 优先级 2: Phase 118 (LLM agent 抽取)

**D. 真实 LLM agent 抽取** (替换 Task 22 的桩)
- `infra/world_db/agent_extractors.extract_proposals_from_chapters()` 当前返回 `[]`
- Phase 118 plan: 调用 LLM (类似 `infra/llm_quality_deep_check.py` 模式), 输出匹配 proposal payload schema (Pydantic 验证)
- Frontend `useWorldAgent.extractFromChapters()` + `extractFromPrompt()` 当前返回 mock — 同步替换
- 成本防护: 默认 chapter_range = 最近 10 章, 单次 token cap ~4000, 每次 session 限 5 次 (per handoff §5)

### 优先级 3: UI 集成

**E. LoreEditor / TimelineEditor 接入页面** (Task #18/19 的输出)
- 当前是独立组件，未被任何页面引用
- 类似 CharacterDetail → CharacterEditor 的 wiring pattern (Task 15)
- 需要: 在 TimelineEventDetail + LoreDetail 加 "编辑" toggle button

---

## 3. 推荐优先级 (新会话)

**短期 (Phase 118)**:
1. **Task #14** (DRY 助手) — 30 min, 立即收益
2. **Task #15** (RevisionConflict 基类) — 30 min, 与 #14 一起做
3. **Task E** (LLM agent 抽取) — 半天到 1 天, 是 Phase 118 主体
4. **Task E2** (LoreEditor/TimelineEditor 接入) — 1-2 小时

**短期 (清理)**:
5. **Task #16** (relationship lastrowid) — 30 min, 测试覆盖

**中长期 (v15.3+)**:
6. **Phase 119+**: 用户策略决策 (LLM provider 选择, prompt engineering)
7. 其他 carryover: Task E (创作者线 v7.0 已完成), Task F (可视化 已完成) — handoff 中的其他 carryover

**不建议**:
- **Prod preview 修复** (Phase 114 accepted debt) — 不要尝试, dev baseline 仍是 authoritative

---

## 4. 用户策略 (重要)

### 已批准且有效 (继承自 handoff §4)

**1. Inline apply small fixes 政策**
- 触发: plan 有 bug (typo/矛盾/过时)
- 行动: controller inline fix + commit with detailed message
- 跳过: BLOCKED → escalate → re-dispatch cycle

**2. Subagent workflow** (per `superpowers:subagent-driven-development`)
- 流程: implementer → spec reviewer → code quality reviewer
- 每 task 3 个 subagent dispatch
- 简化 (本会话实际做法):
  - 机械任务 (路由 stub, Vue 组件) → 1 implementer + inline review
  - 复杂任务 (markdown parser, query modules) → 完整 3 stages
  - 小 plan bug → inline fix

**3. Architecture invariants** (per AGENTS.md, 仍 valid)
- `infra/` 禁止依赖 `dashboard/` / `apps/`
- 检查器 = 纯函数规则引擎
- L3/L4 禁止引用 L2
- 写审分离
- 创作流必须支持 checkpoint 恢复
- Phase 117 新增: `infra/world_db/` 是 `infra/persistence/` 的姊妹模块, 同样不允许被 dashboard/ 直接依赖 (只走 FastAPI)

**4. 优先级源**
- `.lingwen/architecture.yml` 是 AI-readable 真源 (Phase 117 已更新加入 `world_db` 模块)
- AGENTS.md 文字版 backup
- CLAUDE.md 是新会话入口

### 新会话应当遵守的项目约定 (Phase 117 强化)

**5. testid-class-sync 规则** (Phase 8.36, v15.0+ 已应用)
- 每个 `data-testid="X"` 必须有 `class` 含 `X` 的 kebab-case token
- 反之亦然: 含有 testid-mirror class 的元素必须有 `data-testid`
- Phase 117 修复了 13 个 ESLint warnings; Phase 118+ 应保持清洁
- 见 `apps/dashboard/eslint-rules/testid-class-sync.js`

**6. no-class-selector-in-test 规则** (Phase 8.31, v15.0+ 已应用)
- 测试中禁止 `wrapper.find('.classname')`
- 用 `data-testid` 或 `wrapper.text()` 替代
- 已有 helper: `apps/dashboard/tests/helpers/by-testid.ts`

**7. vi.hoisted() 限制**
- hoisted callback 只能访问 `vi`, 不能访问 Vue/JS imports
- Vue `ref()` / `computed()` 必须在 top-level, hoisted 之外
- 见 `memory/patterns.md` §1

**8. vite-auto-imported globals**
- `LibraryPage`/`AskPage` 等调用 `getWriteResume()`, `fetchStudioQuality()` 等作为全局
- 测试环境无自动导入, 需要在 `globalThis` 上 stub
- 见 `memory/patterns.md` §4

**9. TDD per task** (per `superpowers:test-driven-development`)
- Write failing test → verify RED → implement → verify GREEN → commit
- 每个 task 独立 RED/GREEN cycle

---

## 5. 避免 (Don't Do)

继承自 handoff §5, 加上本会话发现:

- ❌ **不要尝试 prod preview fix** (Phase 114 accepted debt, 5 phase 投入失败, ROI 不匹配)
- ❌ **不要主动开第九本书 / 星陨 wave / SaaS / 录屏**
- ❌ **不要恢复 llm×7 每次 push 全跑** (改 `projects/**`/`infra/**` 或 label `llm-check` 才跑)
- � **不要把 spec/plan/audit 文档归档到 docs/archive/** — 让历史可见 (本会话已 supersede v1 handoff doc, 保留作为历史)
- ❌ **不要自作主张重命名 `lingwen` 命名空间** — 品牌字符串真源在 `apps/dashboard/src/config/brand.js`
- ❌ **不要加 `@ts-ignore` / `as any` / 空 catch** — 见 `.lingwen/constraints.yml`
- ❌ **不要直接 import `infra/` 在 `apps/dashboard/`** — 必须走 FastAPI (Phase 117 严格遵守)
- ❌ **不要在 query 模块里 mutate `cur.rowcount` / 静默吞错** — 见 Phase 117 修复的 `update_proposal_status` silent failure bug
- ❌ **不要用 cytoscape-fcose** — Phase 114 已 accept, 用 vis-network 替代

---

## 6. 项目入口

| 任务 | 命令 |
|------|------|
| 前端测试 | `cd apps/dashboard && pnpm vitest run` |
| 前端类型检查 | `cd apps/dashboard && pnpm tsc --noEmit` |
| 死代码检测 | `cd apps/dashboard && pnpm exec knip` |
| 构建 | `cd apps/dashboard && pnpm build` |
| Dev 启动 | `cd apps/dashboard && pnpm dev` |
| 后端测试 (Phase 117 文件) | `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/infra/world_db/ apps/studio_api/tests/test_world_route.py -v` |
| 后端全测试 | `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/ apps/studio_api/tests/ -v` |
| 后端 import 检查 | `/home/ailearn/miniconda3/bin/python -c "from infra.persistence.write_workspace_api import router; from apps.studio_api.routes.world import register_world"` |
| Ruff (Phase 117) | `/home/ailearn/miniconda3/bin/python -m ruff check infra/world_db/ apps/studio_api/routes/world.py apps/studio_api/tests/test_world_route.py` |

**注意**: 后端必须用 `/home/ailearn/miniconda3/bin/python` (Python 3.13 + fastapi)。系统 `pytest` (Python 3.10) 缺 fastapi/sqlite3 访问。

---

## 7. 关键文件指针

### Phase 117 新增

| 文件 | 用途 |
|------|------|
| `infra/world_db/__init__.py` | Module entry (re-exports init_schema + get_connection) |
| `infra/world_db/schema.py` | 6 SQLite tables + `SCHEMA_VERSION` + idempotency check |
| `infra/world_db/markdown_roundtrip.py` | 6 parser/serializer functions + `import_project_markdown` orchestrator |
| `infra/world_db/queries/characters.py` | character CRUD + `CharacterRevisionConflict` |
| `infra/world_db/queries/factions.py` | faction CRUD |
| `infra/world_db/queries/relationships.py` | `create_relationship` (INSERT OR IGNORE) + `list_relationships` |
| `infra/world_db/queries/lore.py` | lore CRUD + `LoreRevisionConflict` |
| `infra/world_db/queries/timeline.py` | timeline event CRUD + `TimelineRevisionConflict` |
| `infra/world_db/queries/proposals.py` | proposal CRUD + `update_proposal_status` (raises on missing pid) |
| `infra/world_db/agent_extractors.py` | LLM stub (Phase 118 wires real) |
| `apps/studio_api/routes/world.py` | 9 endpoints: 7 GET + POST proposal + accept/reject + import/export |
| `apps/dashboard/src/stores/useWorldStore.js` | Pinia store: activeTab, canonLevelFilter, selectedCharacterId, proposalInboxOpen |
| `apps/dashboard/src/composables/world/useWorldDb.js` | 6 fetch wrappers |
| `apps/dashboard/src/composables/world/useWorldReview.js` | 4 proposal action wrappers |
| `apps/dashboard/src/composables/world/useWorldImportExport.js` | 2 markdown I/O wrappers |
| `apps/dashboard/src/composables/world/useWorldAgent.js` | Agent stub composable (Phase 118 wires real) |
| `apps/dashboard/src/pages/WorldPage.vue` | `/world` route entry, composes PageLeadBar + WorldTabs + Inbox + ImportExport + 4 tab children |
| `apps/dashboard/src/components/world/WorldTabs.vue` | 4-tab switcher |
| `apps/dashboard/src/components/world/WorldProposalInbox.vue` | Proposal review UI |
| `apps/dashboard/src/components/world/WorldImportExport.vue` | Markdown I/O UI |
| `apps/dashboard/src/components/world/characters/*.vue` | List, Card, Detail, Relationships, Editor (5 components) |
| `apps/dashboard/src/components/world/factions/*.vue` | Graph (list/graph toggle), GraphCanvas (vis-network), Detail (3 components) |
| `apps/dashboard/src/components/world/timeline/*.vue` | View, EventDetail, Editor (3 components) |
| `apps/dashboard/src/components/world/lore/*.vue` | List, Detail, Editor (3 components) |

### Phase 117 修改

| 文件 | 修改 |
|------|------|
| `apps/dashboard/src/router/index.js` | 添加 `/world` route |
| `apps/dashboard/src/composables/index.ts` | re-export 4 个 world composables |
| `apps/studio_api/routes/__init__.py` | `register_world` 导入 + 注册到 `register_all_routes` |
| `apps/dashboard/package.json` | 添加 `vis-network@^10.1.2` |
| `.lingwen/architecture.yml` | 添加 `world_db` 模块条目 |
| `CLAUDE.md` | v15.2 + Phase 117 公告 + 6 个关键路径 |

### 测试

| 文件 | 测试数 |
|------|--------|
| `tests/infra/world_db/test_schema.py` | 1 |
| `tests/infra/world_db/test_character_queries.py` | 3 |
| `tests/infra/world_db/test_other_queries.py` | 5 |
| `tests/infra/world_db/test_markdown_roundtrip.py` | 6 |
| `tests/infra/world_db/test_agent_extractors.py` | 1 |
| `apps/studio_api/tests/test_world_route.py` | 3 |
| `apps/dashboard/tests/unit/pages/world-page.spec.ts` | 3 |
| `apps/dashboard/tests/unit/stores/useWorldStore.spec.js` | 3 |
| **Phase 117 合计** | **25 tests** |

### Spec + Plan

| 文件 | 用途 |
|------|------|
| `docs/superpowers/specs/2026-08-26-world-visualization-design.md` | v1 设计稿 (7 sections, brainstomed) |
| `docs/superpowers/plans/2026-08-26-world-visualization.md` | 23-task 实施计划 (3248 行) |
| `docs/superpowers/specs/2026-08-26-immersive-write-workspace-design.md` | Phase 115 design (历史) |
| `docs/superpowers/specs/2026-08-26-write-workspace-v1-session-handoff.md` | Phase 115 handoff (superseded by Phase 116) |

### CLAUDE.md / AGENTS.md / `.lingwen/`

| 文件 | 用途 |
|------|------|
| `CLAUDE.md` | **新会话入口** — v15.2 + 关键路径表 + 已知遗留 |
| `AGENTS.md` | 5 条架构不变量 (文字版 backup) |
| `.lingwen/architecture.yml` | 模块边界 (Phase 117 已更新含 world_db) |
| `.lingwen/constraints.yml` | 9 个 A00X 反反模式 (A001-A009) |

---

## 8. 历史背景

### 项目维护模式

- v15.2 闭环 — World Visualization v1 是**第三个**产品侧添加 (前两个: v15.0 Write Workspace, v14.x Creator beta pack)
- 之前 50+ phases 都是 dashboard 工程 (perf / knip / ESLint / maintenance)
- Phase 117 是 23 个 task 的完整 subagent-driven-development 实战 — 建立了 3 stage review 模式 (implementer + spec reviewer + code quality reviewer)

### Phase 117 关键决策 (已闭环, 不要重审)

1. **数据层**: SQLite + markdown round-trip (Phase 118+ 可加 JSON/SQLite 双源)
2. **vis-network**: 选择 vis-network 而非 cytoscape (避开 Phase 114 rollup 冲突, lazy-load 优化 bundle)
3. **Proposal 流程**: Human + agent 双轨, 必须 review 才能 apply (不可绕过)
4. **架构分层**: `infra/world_db/` 是 `infra/persistence/` 姊妹模块, dashboard 通过 FastAPI 访问, 不直接 import

### 已知技术约束 (新会话须知)

1. **vis-network bundle**: lazy-loaded, ~150kb gzipped, 只在 /world graph tab 激活时加载
2. **prod preview regression** (Phase 114): cytoscape-fcose CJS + rollup commonjs 不兼容, 5 phase 投入失败, dev baseline 仍是 authoritative; E2E Playwright runtime 阻塞
3. **Python 环境**: 后端必须用 `/home/ailearn/miniconda3/bin/python` (Python 3.13), 系统 `pytest` (Python 3.10) 缺 fastapi/sqlite3
4. **CLAUDE.md v15.2**: 是新会话入口, 含版本 + 关键路径 + 已知遗留

---

## 9. 下次会话快速启动清单

新会话第一件事:

1. 读 `CLAUDE.md` (v15.2)
2. 读本交接文档 (`docs/superpowers/specs/2026-08-26-phase-117-handoff.md`)
3. 跑验收:
   ```bash
   cd /home/ailearn/projects/LingWen
   /home/ailearn/miniconda3/bin/python -m pytest tests/infra/world_db/ apps/studio_api/tests/test_world_route.py -v
   cd apps/dashboard && pnpm vitest run tests/unit/pages/world-page.spec.ts
   ```
4. 决定下一步: Task #14/15/16 (DRY + exception + lastrowid) 或 Phase 118 (LLM agent) 或 Task E2 (editor 接入)

---

## 10. 备忘 (本会话发现的可复用模式)

### Vitest 测试模式 (已存入 `~/.claude/projects/.../memory/patterns.md`)

- `vi.hoisted()` 只能访问 `vi`, Vue `ref()`/`computed()` 必须 top-level
- getter mocks: `get projects() { return projectsRef.value }` 用于直接值传递
- 共享 module-level ref (如 `useAskPageTab`) 需要 `beforeEach` 重置
- jsdom form submit 不可靠, 用 `wrapper.vm.submitMessage()` 直接调用
- vite-auto-imported globals 需 `globalThis` stub

### ESLint 自定义规则 (重要)

- `testid-class-sync`: data-testid 和 class 双向必须 kebab-case 镜像
- `no-class-selector-in-test`: 测试中禁止 `.classname` selector
- `no-store-value-access`: 不要在 setup 外访问 `.value`

### 调试技巧

- `console.log('DEBUG HTML:', wrapper.html().slice(0, 2000))` 调试 Vue 组件渲染
- `console.log('DEBUG messages:', JSON.stringify(vm.messages))` 调试 ref 状态
- `git diff --cached --stat` 验证 stage 内容

### 已知工程问题 (不属于 Phase 117)

- 232 个 ruff 错误 (历史, Phase 117 文件外) — 不修, 不影响 CI
- 38+ knip unused exports (历史) — 不修
- 15 个 pytest collection errors (历史, 引用不存在的模块) — 不修

---

> **交接完成**。Phase 117 已合入 master (f890706e), 新会话可从 Phase 118 (LLM agent) 或清理 follow-ups (Task #14/15/16) 启动。
