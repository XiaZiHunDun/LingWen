# 灵文 · 工业化小说生产系统

> **版本**: v41.0 (Phase 43 P3-ARCHDEBT lingwen-llm-service) + Phase 42 (project_init) + Phase 41 mini (brand 字串闭环) + Phase 41+ mini (asset rename) + Phase 41++ mini (sidebar nav micro-interaction polish) + Phase 41+++ mini (infra/ 残留审查 + Top 5 候选识别) + v40.0 (asset sidebar icons 闭环：11 emoji → Phosphor-duotone SVG + 1 Pilot follow-up icon) · 更新: 2026-09-11
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
| I049 | `packages/lingwen-got/` 是 GoT 引擎唯一实包; `infra.got.*` 路径非法 (Phase 34+) |
| I050 | `packages/lingwen-world-model/` 是 World Model (Ripple + Subplot + Snapshot) 引擎唯一实包; `infra.world_model.*` 路径非法 (Phase 35+) |
| I051 | `packages/lingwen-errors/` 是错误基类系统唯一实包；`infra.errors.*` 路径非法 (Phase 36+) |
| I052 | `packages/lingwen-paths/` 是项目路径管理（ProjectPaths / resolve_project_root / get_paths / get_chapters_dir / get_rules_dir）的唯一实包；`infra.paths.*` 路径非法 (Phase 37+) |
| I053 | `packages/lingwen-project-config/` 是项目配置管理（ProjectConfig / update_project_creation_mode）的唯一实包；`infra.project_config.*` 路径非法 (Phase 38+) |
| I054 | `packages/lingwen-logging-config/` 是日志配置（StructuredFormatter / setup_logging / logger）的唯一实包；`infra.logging_config.*` 路径非法 (Phase 39+) |
| I055 | `packages/lingwen-studio-registry/` 是 Studio 多项目注册表（factory_root + StudioProject + active project state + summaries + reports）的唯一实包；`infra.studio_registry.*` 路径非法 (Phase 40a P3-ARCHDEBT studio_registry) |
| I056 | `packages/lingwen-project-init/` 是项目初始化器（InitProjectResult + validate_slug + default_project_parent + init_minimal_short_project + 7 markdown helpers）的唯一实包；`infra.project_init.*` 路径非法 (Phase 42 P3-ARCHDEBT project_init) |
| I057 | `packages/lingwen-llm-service/` 是 LLM 服务（LLMService class + get_llm_service / create_task + DP-02 模块加载时 LLMServiceAdapter factory 注册）的唯一实包；`infra.llm_service.*` 路径非法 (Phase 43 P3-ARCHDEBT lingwen-llm-service) | |

> 完整不变量与设计原则 DP-01..06 见 `.lingwen/architecture.yml`；提交纪律与反模式见 `.lingwen/constraints.yml`。

## 品牌与命名

- **产品名**：灵文工作室（用户可见 UI 标题、侧栏副标题、对外文档统一使用）。
- **工程命名空间**：沿用历史 `lingwen`（包名 / import path / Python module 全部使用 `lingwen`，**不要改成 moling**）。
- 2026-09-10 已闭环：`apps/dashboard/src/config/brand.js` 与所有用户可见消费方（App.vue / NoProjectOnboarding / TodayPage / e2e smoke）统一为「灵文工作室 / 灵文」。
- 2026-09-10 Phase 41+ mini：asset 文件名 `moling-logo.jpg` → `lingwen-logo.jpg`（`apps/dashboard/public/assets/brand/`，2 个 runtime 引用迁移）。`public/assets/concepts/moling-ui-concept.jpg` 为美术资产（非品牌字串），留 known legacy。

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

- ✅ **v40.0 Phase 42 P3-ARCHDEBT (project_init)**（2026-09-10 ff-merge on `phase-42-p3-archdebt-project-init`，7 atomic commits：`2200e1b4` spec / `5d088a96` C1 scaffold 3 sub-modules / `9f5146ae` C2a 4 sites intra-infra / `45aefa16` C2b 47 sites bulk / `7c8d8119` C3 FULL DELETE / `caab594a` C4 v39.0→v40.0+I056 / handoff + guards）：`infra/project_init.py` (453 行, 14 symbols: 1 class InitProjectResult + 9 public funcs + 4 private + 2 consts) → `packages/lingwen-project-init/` (3 sub-modules: models + slug + beats, ~440 LOC). 51 consumer call-sites migrated (1 cli + 1 multi-symbol test + 44 test_creator_* + 5 function-body in test_creator_volume_templates + 1 wildcard `infra/project/__init__.py:4` + 3 function-body in `infra/cross_volume/e2e_seed.py`). **C3 FULL DELETE (NOT shim)** — all 51 consumer migrated in C2b, 0 deferred. 7 atomic commits (C0 spec+plan / C1 scaffold / C2a intra-infra+wildcard / C2b bulk / C3 delete / C4 version+invariant / C5 guards). NOT-LEAF package — 2 workspace deps: lingwen-paths + lingwen-shared (similar to P40a but simpler). 1 NEW invariant (#56 lingwen-project-init 是项目初始化器唯一实包；infra.project_init.* 路径非法). **Validation**: 10/10 phase42 guards GREEN + 5/5 test_project_init PASSED + 50 test_creator_* (245/246, 1 pre-existing Qdrant fail unrelated) + ruff clean (4 pre-existing E741 Phase 35 baseline) + 4 prior phase guards preserved + `from infra.project_init import X` → ModuleNotFoundError. **4 lessons** (`phase-42-p3-archdebt-project-init.md`)：(1) pre-spec 9-pattern audit 漏检 wildcard in `__init__.py` (N.14 lesson 1 第 15 次变体)；(2) C3 FULL DELETE vs shim decision tree (all consumers in C2b → full delete)；(3) Other locked worktree 污染 grep audit — `.claude/worktrees/agent-a7eb86a3e8912a954/` 仍 locked 含历史 refs, guard 必须 `rel_path.startswith(".claude/worktrees/")` 过滤 (N.14 lesson 1 第 16 次变体)；(4) `__all__` count spec drift — smoke test 必须 `assert len(package.__all__) == N`。详见 `docs/superpowers/handoffs/2026-09-10-phase-42-p3-archdebt-project-init-handoff.md`。
- ✅ **v40.1 Phase 41+++ mini (infra/ 残留审查 + Top 5 候选)**（2026-09-10 ff-merge on `phase-41-plus-plus-infra-residual-audit`，3 atomic commits：`c775c66c` infra-residual-audit.md / `d1280520` ARCHDEBT-CANDIDATES.md / handoff）：P3-ARCHDEBT 5/5b 闭环后，infra/ 仍剩 24 顶层 .py + 17 子目录 (~18K LOC / 141 .py)。**本 phase 仅审计，不真迁移** — 输出 2 文档：(1) `docs/superpowers/infra-residual-audit.md` — 完整模块清单 + 4 类分类（TRUE LEAF 8 / NEAR-LEAF 8 / NOT-LEAF 7 / 引擎子系统 10）+ §4 策略建议（不批量迁移）；(2) `docs/superpowers/ARCHDEBT-CANDIDATES.md` — Top 5 候选 ranked：#1 `project_init` 46 consumers (NOT-LEAF, 类似 P40a studio_registry 模式) → Phase 42; #2 `llm_service` 9 consumers + 半迁移 shim cleanup → Phase 43; #3 `prose_calibration` TRUE LEAF → Phase 44; #4 `cache` TRUE LEAF batch → Phase 45; #5 `filter` near-LEAF boundary check → Phase 46。**3 lessons**: (1) 审计 grep 必须 exclude self + `__pycache__` + archive（false-positive）；(2) workspace deps 数 ≠ 迁移难度，consumer count 优先（NOT-LEAF 但 high fan-out 反而高 ROI）；(3) `# v[0-9]+\.[0-9]+ relocation:` 注记 = 半迁移 shim = 低风险 P3-ARCHDEBT 候选。详见 `docs/superpowers/handoffs/2026-09-10-phase-41-plus-plus-infra-residual-audit-handoff.md`。
- ✅ **v40.1 Phase 41++ mini (sidebar nav micro-interaction)**（2026-09-10 ff-merge on `phase-41-plus-sidebar-micro-interaction`，3 atomic commits：`243cb9f1` App.vue 6 polish CSS items / `163c07e6` regression spec 7 tests / handoff + MEMORY）：sidebar nav hover/active 已存在（translateX 2px / gradient / accent border），本 phase 补 **6 项 polish**：(1) `.nav-item` `transition: all` → 显式 `transition-property: background-color, color, transform, box-shadow` (anti-pattern 修复)；(2) `.nav-item:hover .nav-icon` → `transform: scale(1.08)` chip "lifts" toward cursor；(3) `.nav-item:active` → `transform: translateX(2px) scale(0.98)` 按下反馈覆盖 hover；(4) `.nav-item:focus-visible` → `outline: 2px solid var(--color-accent); outline-offset: 2px` 键盘聚焦环；(5) `svg.nav-icon path` → `transition: fill var(--transition-normal)` duotone accent 平滑切换；(6) `@media (prefers-reduced-motion: reduce)` 全 strip transitions + transforms (a11y)。**复用** `LibraryPage.vue:212-220` 现有 a11y 模式（focus-visible + reduced-motion）。**新增** `tests/unit/sidebar-nav-micro-interaction.spec.ts` (74 lines, 7 tests) — 静态源校验（读 App.vue + grep 6 markers），比 mount App.vue 更稳/更快。**2 lessons**: (1) CSS 测试 regex 必须 strip `/* */` 注释（首次跑 fail 命中注释里的 `transition: all` 字面量 → stripComments() helper 修复，N.14 lesson 1 第 11 次变体）；(2) CSS-only edit → 静态源校验 > runtime mount（mount App.vue 需 Pinia + vue-router + 5+ stores，启动 cost 高）。详见 `docs/superpowers/handoffs/2026-09-10-phase-41-plus-sidebar-micro-interaction-handoff.md`。
- ✅ **v40.1 Phase 41+ mini (asset rename)**（2026-09-10 ff-merge on `phase-41-plus-asset-rename`，3 atomic commits：`19050c00` git mv + 2 runtime refs / `e8b3a2f1` clean 5 stale doc claims / handoff + MEMORY）：品牌闭环延续 — `apps/dashboard/public/assets/brand/moling-logo.jpg` → `lingwen-logo.jpg` (134 KB, git mv 100% similarity) + App.vue:17 + NoProjectOnboarding.vue:4 两处 `<img src>` 迁移；5 stale 文档清理（CLAUDE.md:105 + HANDOFF.md:49 + brand.js:15 JSDoc + apps/dashboard/README.md:3 "墨灵 Studio" → "灵文工作室" + sidebar-icons spec lines 16/171 拆分两条 carryover）。**未改**（故意保留）：`apps/dashboard/dist/assets/brand/moling-logo.jpg` (build 产物，下次 build 覆盖) / `public/assets/concepts/moling-ui-concept.jpg` (美术资产，非品牌字串，known legacy) / archive/ + 历史 spec/plan/handoff 的 moling-logo 引用 (commit blame)。**Lessons**：(1) `git mv` 在 cwd 非 repo root 时需用绝对路径 (`/home/ailearn/projects/LingWen/...`)，相对路径会被 prepend 当前 cwd (Phase 41+ lesson 1)。(2) stale-claim 清理时要区分 **runtime 引用** (必须迁移) / **描述性元数据** (改后作为闭环注保留) / **build 产物** (忽略) / **历史 archive** (commit blame 保护) — 4 类区分 (Phase 41+ lesson 2)。详见 `docs/superpowers/handoffs/2026-09-10-phase-41-plus-asset-rename-handoff.md`。
- ✅ **v40.1 Phase 41 mini (brand 字串闭环)**（2026-09-10 ff-merge on `master`，4 atomic commits: `2fad5730` / `90fe4459` / `24158500` / `fdb7fc71`）：品牌字串真源统一 — `apps/dashboard/src/config/brand.js` productNameZh `'墨灵 Studio' → '灵文工作室'`，7 消费方（App.vue / NoProjectOnboarding / TodayPage / e2e smoke + 3 JSDoc）同步迁移；untrack pytest artifact `infra/.state/social_engine/relationship_network.db` (28 KB) 防 commit leak；docs sync (CLAUDE/CURRENT_STATUS/BACKLOG/HANDOFF) dedupe ~6000 字符重复；`pilotBatch` mock value type widening 修 vue-tsc 3 个 pre-existing 类型错。**5 quality gates**: vitest 1884 + 1 skip / knip 0 / eslint 0 (7 pre-existing warnings) / tsc 0 / build exit 0。**3 lessons** (`phase-41-mini.md`)：(1) HANDOFF 状态文字 stale-claim 必须 fresh run 验证；(2) `vi.hoisted()` mock factory type inference 太窄 — 用 `as X | null` widening；(3) `git commit -m` bash backtick 陷阱 — heredoc `<<'EOF'`。详见 `docs/superpowers/handoffs/2026-09-10-phase-41-mini-handoff.md`。
- ✅ **v40.0 asset sidebar icons**（2026-09-10 ff-merge at `be5e73d1`，8 commits on `phase-asset-sidebar-icons`）：sidebar 11 emoji 占位 → 12 Phosphor-duotone SVG icons（11 plan + 1 Pilot follow-up，phase 内发现 SIDEBAR_ICONS 缺 `pilot` 即补 `IconSidebarPilot`）。新增 `apps/dashboard/src/components/icons/sidebar/` (12 SFC + `index.js` barrel + spec)。`--lingwen-icon-accent` CSS var（`oklch(70% 0.18 280)`）主题化霓虹紫蓝 accent。`App.vue` nav 配置 `.map()` 优雅集成（零散文件改动）。**5 quality gates 全过**：vitest / ESLint / knip / vue-tsc / build 零问题。视觉验证：desktop light + dark、sidebar 折叠态、移动端 drawer、hover/focus/active state 全部 OK。**4 follow-up lessons（已记入 MEMORY.md）**：① Vite static import-analysis all-or-nothing（barrel + SFC 必须 atomic，否则整 suite 加载失败）② vue-tsc strict catches `$attrs['x']` as `unknown`（`:aria-label="($attrs['aria-label'] as string | undefined)"` 强制 cast）③ nav item ids ≠ icon registry keys（wire 前必须 cross-check `humanFirstNav.js` ids vs `SIDEBAR_ICONS` keys）④ spec test 太松会漏视觉 bug（`viewBox + ≥1 path` 不够，要 `paths.length === 2` + base `fill="currentColor"` + accent `--lingwen-icon-accent`）。**P3-ARCHDEBT 5/5b + v40.0 双闭环**。
- ✅ **v39.0 P3-ARCHDEBT (studio_registry)**（2026-09-09 ff-merge `phase-40-p3-archdebt-studio-registry` + 2026-09-09 Phase 40b closure ff-merged at `af3ef427`）：P3-ARCHDEBT item 5/5 — `infra/studio_registry.py` (1 module, 422 lines, 18 top-level public symbols: 1 frozen dataclass StudioProject + 17 public funcs) → `packages/lingwen-studio-registry/` (5 sub-modules: models + discovery + state + summary + reports, 491 lines total). **Phase 40a** (8 atomic commits: C0 spec+plan / C1 scaffold / C1.5 fixup / C2a intra-infra / C2b bulk / C3 shim / C4 invariant+version / C5 guards+handoff): 47 production edits 迁移 (6 C2a intra-infra + 41 C2b bulk: 17 apps + 18 packages + 5 apps test patches + 1 doc); 0 function-body import misses (verified via \1 backreference sed, Phase 37 lesson); 0 relative imports (clean); 0 filesystem path literals (clean); 1 wildcard `infra/studio/__init__.py:2` paired with C3 shim approach; `infra/studio_registry.py` CONVERTED TO 1-LINE SHIM (NOT deleted — full deletion deferred to Phase 40b); invariant #55 NEW; +1 fixup commit (C1.5: `factory_root()` defect — original `Path(__file__).parent.parent` formula broke after file relocation to `packages/lingwen-studio-registry/src/lingwen_studio_registry/discovery.py`; fix: LINGWEN_PROJECT_ROOT env var + parents[4]). **NOT-LEAF package** — 3 workspace deps: lingwen-paths + lingwen-project-config + lingwen-core (first non-LEAF P3-ARCHDEBT package, lesson 1). **Phase 40b** (closure on `phase-40b-p3-archdebt-studio-registry` HEAD `5ccbe6e9`, doc-only): ~33 edits in `tests/` root 迁移到 canonical `lingwen_studio_registry` (21 `from` + 4 `import as` + 7 `monkeypatch.setattr` + 1 lazy + 1 doc); `infra/studio_registry.py` shim **DELETED**; `infra/studio/__init__.py:2` wildcard **DELETED**; `tests/test_phase40_lingwen_studio_registry.py` 守卫 11 → **12**（新增 Tests 5/6/7/8：shim-deleted / no-wildcard / production-audit / test-audit）；walkthrough scripts (`scripts/verify-companion-walkthrough.sh:48` + `scripts/verify-advance-walkthrough.sh:44`) 已 canonical，无变更。**Validation (Phase 40b)**: Phase 36-40 guards **31 passed** / consumer suite 222 passed + 4 skipped / ruff clean on changed Python files / old-path audit clean (production + tests). **P3-ARCHDEBT 5/5 (studio_registry) FULLY CLOSED** — 无残留 `infra.studio_registry.*` canonical module. 详见 `docs/superpowers/handoffs/2026-09-09-phase-40b-p3-archdebt-studio-registry-handoff.md`（Phase 40b closure handoff）; 历史：`docs/superpowers/handoffs/2026-09-09-phase-40-p3-archdebt-studio-registry-handoff.md`（Phase 40a handoff, merged `1c473405`）。

- ✅ **v38.0 P3-ARCHDEBT (logging_config)**（2026-09-08 ff-merge `phase-39-p3-archdebt-logging-config`）：P3-ARCHDEBT item 4/5 — `infra/logging_config.py` (1 module, 59 lines, 3 top-level public symbols: StructuredFormatter + setup_logging + logger module-level instance) → `packages/lingwen-logging-config/`。7 consumer 迁移 (6 packages + 1 intra-infra; 0 function-body imports — pre-spec verified per Phase 38 lesson 3; 0 test consumers; 0 filesystem path literals; 1 wildcard `infra/core/__init__.py:6` paired with C3 source deletion); `infra/logging_config.py` 删除 + wildcard cleanup; invariant #54 NEW; **5 atomic commits** on phase-39-p3-archdebt-logging-config (C0 spec+plan / C1 scaffold / C2 migrate / C3 delete / C4 invariant+version / C5 guards+doc-sync). **Validation gates**: ruff clean + phase39 guards GREEN + phase38 guards preserved + baselines preserved. **LEAF package** (no workspace deps — only stdlib: json/logging/datetime/pathlib). **Carryover closure**: P3-ARCHDEBT 4/5 (logging_config) → CLOSED; P3-ARCHDEBT remaining 1/5 (studio_registry, 50 consumers) → Phase 40+. 详见 `docs/superpowers/handoffs/2026-09-08-phase-39-p3-archdebt-logging-config-handoff.md`。

- ✅ **v37.0 P3-ARCHDEBT (project_config)**（2026-09-08 ff-merge `phase-38-p3-archdebt-project-config`）：P3-ARCHDEBT item 3/5 — `infra/project_config.py` (1 module, 170 lines, 2 top-level public symbols: ProjectConfig + update_project_creation_mode) → `packages/lingwen-project-config/`。26 consumer 迁移 (2 apps + 16 packages + 4 infra intra + 4 tests; 7 function-body imports via `^([[:space:]]*)from` sed pattern — N.14 lesson 1, 8th occurrence); `infra/project_config.py` 删除 + `infra/project/__init__.py` wildcard 清理; invariant #53 NEW; +1 Phase 37 guard fixup (test_phase37_lingwen_paths.py:145 — N.14 lesson 1, 9th occurrence: filesystem-path string literal in prior-phase regression guard). 7 atomic commits on phase-38-p3-archdebt-project-config (C0 spec+plan / C1 scaffold / C2 migrate / C3 delete / C3.5 phase37-guard-fixup / C4 invariant+version / C5 guards+doc-sync). **Validation gates**: ruff clean + 6 phase38 guards GREEN + 6 phase37 guards restored (after C3.5 fixup) + baselines preserved. **Carryover closure**: P3-ARCHDEBT 3/5 (project_config) → CLOSED; P3-ARCHDEBT remaining 2/5 (logging_config + studio_registry) → Phase 39+。详见 `docs/superpowers/handoffs/2026-09-08-phase-38-p3-archdebt-project-config-handoff.md`。

- ✅ **v36.0 P3-ARCHDEBT (paths)**（2026-09-08 ff-merge `phase-37-p3-archdebt-paths`）：P3-ARCHDEBT item 2/5 — `infra/paths.py` (1 module, 125 lines, 5 top-level public symbols: ProjectPaths / resolve_project_root / get_paths / get_chapters_dir / get_rules_dir) → `packages/lingwen-paths/`。86 consumer 迁移 (8 intra-infra + 16 cross-package in 5 packages + 1 apps + 61 tests + 3 tools)；`infra/paths.py` 删除；invariant #52 NEW。6 atomic commits on phase-37-p3-archdebt-paths (C0 spec+plan / C1 scaffold / C2 migrate / C3 delete / C4 invariant+version / C5 guards+doc-sync)。**Validation gates**: 6 phase37 guards GREEN + 9 baselines preserved (lingwen-core 68/68 + lingwen-got 208/208 + lingwen-world-model 201/201 + lingwen-creator 73/73 + studio_api 82/82 + lingwen-quality 3/3 + lingwen-pipeline 1/1 + lingwen-llm 11/11 + lingwen-cli 3/3) + ruff 4 pre-existing E741 unchanged (2 I001 auto-fixed by ruff --fix). **Carryover closure**: P3-ARCHDEBT 2/5 (paths) → CLOSED; P3-ARCHDEBT remaining 3/5 (project_config / logging_config / studio_registry) → Phase 38+。详见 `docs/superpowers/handoffs/2026-09-08-phase-37-p3-archdebt-paths-handoff.md`。
- ✅ **v35.0 P3-ARCHDEBT (errors pilot)**（2026-09-08 ff-merge `phase-36-p3-archdebt-errors`）：P3-ARCHDEBT pilot — `infra/errors.py` (1 module, 380 lines, 23 public symbols) → `packages/lingwen-errors/`。14 consumer 迁移 (4 packages: lingwen-quality / lingwen-world-model / lingwen-pipeline / lingwen-llm + 8 intra-infra)；`infra/errors.py` 删除；invariant #51 NEW。6 atomic commits on phase-36-p3-archdebt-errors (C0 spec / C0b plan / C1 scaffold / C2 migrate / C3 delete / C4 invariant+version / C5 guards+doc-sync)。**Validation gates**: lingwen-errors 全部测试 + lingwen-core 68/68 + ruff clean + grep audit 0 行（infra.errors.* 引用清零）+ 6 phase36 guards GREEN + 7 baselines preserved。**Carryover closure**: P3-ARCHDEBT 1/5 (errors) → CLOSED; P3-ARCHDEBT remaining 4/5 (paths / project_config / logging_config / studio_registry) → Phase 37+。详见 `docs/superpowers/handoffs/2026-09-08-phase-36-p3-archdebt-errors-handoff.md`。
- ✅ **v34.0 WORLD-MODEL-PACKAGE**（2026-09-08 ff-merge）：P2-ARCHDEBT 收官 — `infra.world_model.*` (10 modules, 2282 lines) + `infra/subplot/helpers.py` (52 lines, 3 functions) → `packages/lingwen-world-model/` (37 public symbols; subplot_helpers 改名 package-locality)。16 consumer 迁移 (1 POC + 2 consistency + 1 subplot + 12 in-package tests)；13 test files 搬到 `packages/lingwen-world-model/tests/`；`infra/world_model/` 删除 + `infra/subplot/helpers.py` 删除；invariant #50 NEW。10 commits on phase-35-world-model-package (C0 spec+plan / C1 scaffold / C2 src+mv / C3 test-mv / C4 subplot-test / C5 poc / C6 consistency / preC7 string-literal-audit / C7 invariant+version / C8 guards+doc-sync)。**Validation gates**: lingwen-world-model 201/201 + lingwen-core 68/68 + lingwen-got 208/208 + studio_api 82/82 + subplot 11/11 + consistency 22/22 + prompt_engineering 244/1skip + 17 phase35 guards (总计 836 + 1skip); ruff clean。**preC7 fixup**: 6 file string literal references migrated to lingwen_world_model (Phase 34 N.14 lesson #4, 5th occurrence: lingwen-prompt scenarios+data_structures + tests/prompt_engineering fixtures+assertions)。**Carryover closure**: P2-ARCHDEBT remaining 1/1 (infra.world_model) → CLOSED; P3-ARCHDEBT (NEW) → `infra.{paths, project_config, logging_config, errors, studio_registry}` → packages/ (Phase 36+) — 5 模块，需 multi-week。详见 `docs/superpowers/handoffs/2026-09-08-phase-35-world-model-package-handoff.md`。
- ✅ **v33.0 LINGWEN-GOT**（2026-09-08 ff-merge）：P2-ARCHDEBT 最大块 — `infra.got.*` (9 modules, 1788 lines) → `packages/lingwen-got/` (32 public symbols)。30 consumer 迁移 (4 lingwen-core + 3 apps/studio_api + 2 infra + 21 tests)；12 got-related test files 搬到 `packages/lingwen-got/tests/`；workflow YAML data dir 跟随；`infra/got/` 删除；invariant #49 NEW。11 commits on phase-34-lingwen-got。**Validation gates**: lingwen-got 208/208 + lingwen-core 68/68 + studio_api 82/82 + ruff (3 pre-existing errors in unrelated files)。**Pre-C6 fixup**: 5 file workflow path references migrated to dynamic `lingwen_got.workflow_loader.__file__` resolution (Phase 32 N.14 lesson 1, 3rd occurrence)。**Carryover closure**: P2-ARCHDEBT remaining 1/2 (infra.got) → CLOSED; P2-ARCHDEBT remaining 1/1 → `infra/world_model/__init__.py` split (Phase 35); P3-ARCHDEBT (NEW) → `infra.{paths, project_config, logging_config, errors, studio_registry}` → packages/ (Phase 36+)。详见 `docs/superpowers/handoffs/2026-09-08-phase-34-lingwen-got-handoff.md`。
- ✅ **v32.0 SHIM-CLEANUP**（2026-09-07 ff-merge `<phase-32 HEAD>`，6 commit `3570a86f..<end>`）：P2-ARCHDEBT PHASE-COMPAT shim 清理 3/4 完成。**删除 3 个零/低消费者 shim**：(1) `infra/subplot/data_structures.py`（32 行，纯 re-export，0 消费者）、(2) `infra/world_model/data_structures.py`（69 行，纯 re-export，0 消费者）、(3) `packages/lingwen-core/src/lingwen_core/agents/master_controller.py`（11 行，6 test 消费者已迁移）。**+1 fixup commit** 修 5 处漏检的 relative import (`from .data_structures` / `from .master_controller` 在 `infra/subplot/__init__.py:19` / `infra/world_model/__init__.py:60` / `infra/world_model/key_point_graph.py:24` / `infra/world_model/snapshot_store.py:24` / `packages/lingwen-core/src/lingwen_core/agents/got_bridge.py:32`)。**+10 regression guard tests** in `tests/test_phase32_shim_cleanup.py` (3 path-deleted + 6 consumer-migrated + 1 canonical-symbol)。**Validation gates**: G1 ruff clean / G2 guard 10/10 GREEN / G3 6 consumer tests baseline 116+1 skip / G4 tests/world_model/ 201 ✅ (C2.5 修复后) / G5 tests/{agent_system,ci,tools}/test_chapter_emit/test_got_bridge/test_got_bridge_budget/test_phase7_1_production_fixes/test_polish_merge_with_usage_ci = 68 ✅ (C2.5 修复后). 剩余 P2-ARCHDEBT 1 项: `infra.got.*` 迁 `packages/lingwen-got/`。详见 `docs/superpowers/handoffs/2026-09-07-phase-32-shim-cleanup-handoff.md`。
- ✅ **v31.0 ARCHDEBT-MINI**（2026-09-07 ff-merge `4dbe8939`，6 commit `8f8c3e1a..4dbe8939`）：P2-ARCHDEBT 子集 2/4 清理。**Sub-task A**：chapter_golden_path 反向 import 修复（create_golden_dashboard_client + run_human_review_smoke + HumanReviewSmokeResult 从 lingwen-core 迁 apps/studio_api/tests/golden_path_smoke.py；-87 行 / +106 行；fixes I001 spirit violation）。**Sub-task B**：4 薄代理 (advance_step/dispatch_task/verify_task/get_workflow_status) 从 WorkflowMixin 抽到 mc_orchestrator_proxy.py；MasterController MRO 加 OrchestratorProxyMixin；+5 refactor-guard tests（test_workflow_state.py）；mc_workflow.py 119→99 行。**12 文件 doc 同步**："5 薄代理" → "4 薄代理"（实际 4 不是 5，Phase 27 拆 WorkflowRunner 后 stale）。详见 `docs/superpowers/handoffs/2026-09-07-phase-31-archdebt-mini-handoff.md`。
- ✅ **v30.0 TACKLE-14-FAILURES**（2026-09-07 ff-merge `38b854e7`，9 commit `2de95a80..38b854e7`）：Phase 29 剩余 14 failed 按 5 类根因一次性清零（ 0 failed / 480 passed / 20 skipped）。**2 真 prod 改动**：`mc_writing.py:155` 加 try/except 韧性契约（broad except + logger.warning + 空 audit report 兜底）+ `cost_persistence.py` 加 `record_at()` public helper（历史数据 seeding / migration / test fixture 用）。**3 test-only 清理**：stub factory `WorkflowState.empty()` 注入（-7）、`make_master_with_router` 替代 bare `MasterController()`（-2）、`WorkflowRunner._harvest_decision_specs` 迁移（-1）+ 2 处 stale assertion 修正。详见 `docs/superpowers/handoffs/2026-09-07-phase-30-tackle-14-handoff.md`。
- ✅ **v29.0 P2-MC-WRITING**（2026-09-07 ff-merge `b1b748ad`，17 commit `106dd21d..b1b748ad`）：恢复 `tests/agent_system` 路径发现 / memory gateway import / dashboard test entry point / stale test patches。84 → 14 failed (-70)，tests/got 156 / lingwen-core 68 / ruff clean 不变；11 测试文件 + **1 真 prod 改动** `packages/lingwen-core/src/lingwen_core/agents/mc_editing.py:202`（Phase 15.0 P3-SPLIT 迁移遗留 `from mc_utils import ...` 旧路径）。详见 `docs/superpowers/handoffs/2026-09-04-phase-29-mc-writing-handoff.md`。
- ✅ **v28.0 P2-RESUME-VERIFY**（2026-09-04 ff-merge）：5 E2E tests 用真实 GoTScheduler + ThoughtGraph 验证 scheduler 幂等 + start_nodes=None derivation + state.start_nodes 持久化 + WorkflowRunner.run→resume 完整 cycle；0 改范围 9 类文件不动。
- ✅ **v27.0 P2-WFRUNNER**（2026-09-04）：`WorkflowRunner` service 从 WorkflowMixin 抽出（workflow_runner.py 307 行 new + mc_workflow.py 404→119 行 -70%）；TDD 21 tests + 2 refactor guards；0 new failure。
- ✅ **v26.0 P2-WFSTATE**（2026-09-04）：`_last_*` 散点 → `WorkflowState` dataclass（with_updates + empty classmethod + 7 字段整合）；0 行为变更；3 refactor guards 防回潮。
- ✅ **v25.9 human_review 流水线修复**（2026-09-03 ff-merge `0a6f4346`）：mc_workflow.py 自仓库迁移后是 hallucinated stub；从 git history `5c4259e5:novel-factory/infra/agent_system/master_controller.py` 还原真实实现，对齐新 GoTScheduler API，解 4 个 dashboard smoke skip + 顺带 +15 cascade fixed。0 改范围（got_bridge.py / chapter_golden_path.py / apps.studio_api/* / infra/got/* / architecture.yml / HANDOFF*.md）。
- **Prod preview regression** (Phase 114 accepted)：cytoscape-fcose CJS 与 rollup commonjs 插件不兼容，5 个 phase 投入失败。dev baseline 仍是 authoritative measurement。E2E Playwright runtime 暂时阻塞。
- **vis-network install on fresh clone** (Phase 118 发现)：fresh checkout 下 `apps/dashboard/node_modules/` 缺 vis-network, 跑 frontend test 全失败。必须 `cd apps/dashboard && pnpm install`。
- **架构债候选（v40.0 + Phase 41+++ 后）**：HANDOFF 文档 `latest_decision_queue` 措辞修订已完成；P3-ARCHDEBT 5/5 已全部闭环（Phase 36-40 + 40b）；**Phase 41+++ mini 完成 infra/ 残留审查 + Top 5 候选识别**（`docs/superpowers/infra-residual-audit.md` + `docs/superpowers/ARCHDEBT-CANDIDATES.md`）。**Phase 42+ next-actionable**：`infra/project_init` 迁 `packages/lingwen-project-init/`（46 consumers, NOT-LEAF 类似 P40a studio_registry 模式）。详见 `ARCHDEBT-CANDIDATES.md`。

---

> 版本史已整体归档至 `docs/superpowers/archive/PHASE_HISTORY.md`；本文件不再维护版本记录表。