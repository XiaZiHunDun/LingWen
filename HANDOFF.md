# 灵文 · LingWen 项目 Handoff 文档

[![codecov frontend](https://codecov.io/gh/XiaZiHunDun/LingWen/graph/badge.svg?flag=frontend)](https://codecov.io/gh/XiaZiHunDun/LingWen?flags%5B0%5D=frontend)

> **目的**: 项目切换开发工具 (Cursor / Windsurf / Cline / Aider / 其他) 时, 任何 AI 助手打开本目录读这份文件即可衔接工作。
> **版本**: v9.84 (Phase 9.84 v7 全量交付 + v8 roadmap, 2026-06-11)
> **更新 (2026-06-11)**: F79 batch ch361-363 真实 LLM 3/3; v8 推荐 **F80** dry-run。

---

## 0. 30 秒速览 (TL;DR)

| 项目 | 内容 |
|------|------|
| **项目名** | 灵文 (LingWen) · 工业化小说生产系统 |
| **当前小说** | 《星陨纪元》359 章 (v9.10 已发布, v9.11/v9.12/v9.24 未触发正文变更) |
| **核心架构** | 5 核心 Agent + 角色池 (content_writer/auditor/polisher × 作家/审核员/读者池) |
| **后端** | Python 3.13 · FastAPI · SQLite (`.state/*.db`) · Pydantic v2 · pytest **2781** collected |
| **前端** | Vue 3 SFC · Vite · ECharts **6.1** · Vitest **384** passed · Playwright 1 smoke + 5 live opt-in · TS strict |
| **总测试** | **~3192** (2781 pytest + 384 vitest + 27 pytest skip) |
| **GitHub** | `git@github.com:XiaZiHunDun/LingWen.git` (master 单分支) |
| **当前 commit** | `f429533` — feat(F77-bk,F78) v8 Settings 预算写入 |
| **CI** | `test.yml` · `dashboard-frontend-ci.yml` · `dashboard-e2e-smoke.yml` · **`dashboard-e2e-live.yml`** (opt-in) |
| **下一期推荐** | **F81** Analytics batch rollup — 见 §6 + v8 roadmap |

---

## 1. 项目结构

```
LingWen/                                    # 本目录 (项目根, git root)
├── HANDOFF.md                              # 本文件 (新工具先读这里)
├── novel-factory/                          # 主项目目录 (~95% 代码)
│   ├── README.md                           # 主 README (项目对外介绍, v8.3 stale)
│   ├── pyproject.toml + pytest.ini         # pytest 配置
│   ├── CLAUDE.md                           # 项目级 CLAUDE.md (主控 agent prompt 模板)
│   ├── docs/
│   │   ├── superpowers/
│   │   │   ├── specs/                      # 18+ spec doc (设计文档)
│   │   │   └── plans/                      # 18+ plan doc (实施计划)
│   │   ├── followup-roadmap.md            # 后续 followup 16 项 (P0/P1/P2)
│   │   └── ...
│   ├── infra/                              # 后端基础设施
│   │   ├── agent_system/                   # 5 核心 Agent + MasterController
│   │   ├── ai_service/                     # OpenAI/Anthropic/MiniMax provider + router + cost tracker
│   │   ├── cross_volume/                   # 跨卷涟漪 (CVG) Phase 9.10-9.18
│   │   ├── state/                          # workflow_validator
│   │   ├── memory_system/                  # RAG/Qdrant
│   │   ├── quality/                        # 检测器/修复器
│   │   └── ...
│   ├── dashboard/                          # FastAPI 后端 + Vue 前端
│   │   ├── app.py                          # FastAPI 入口
│   │   ├── protocols.py                    # Pydantic schemas
│   │   ├── frontend/                       # Vue 3 + Vite
│   │   │   ├── src/
│   │   │   │   ├── components/             # Vue SFC
│   │   │   │   ├── composables/            # useWorkflowSocket / useCostWindow / useRippleStore
│   │   │   │   └── api/
│   │   │   ├── tests/
│   │   │   │   ├── unit/                   # 46 vitest spec (192 tests)
│   │   │   │   └── e2e-smoke/              # (空) Phase 9.31 F15 Playwright 已 vitest 化
│   │   │   └── package.json + vite.config.js + vitest.config.js + playwright.config.js
│   │   └── ...
│   ├── tests/                              # 2484 pytest
│   │   ├── agent_system/                   # 90% 测试
│   │   ├── ai_service/
│   │   ├── cross_volume/
│   │   └── ...
│   ├── lingwen.py                          # CLI 统一入口
│   ├── .state/                             # SQLite 状态库 (gitignored)
│   │   ├── cost_tracker.db
│   │   ├── workflow.db
│   │   └── ripple.db
│   └── ...
├── reference/                              # 参考文档
├── tests/                                  # 早期测试 (deprecated)
├── tools/                                  # 工具脚本
├── 01_灵感库/ ... 11_方法论/                # 小说素材 + 方法论目录
└── 灵文心流.txt                             # 项目哲学
```

---

## 2. 5+ 硬规则 (违反任意一条 = 重做)

### 2.1 Git 规则

- **0 Co-Authored-By footer** — 全局 `~/.claude/settings.json` 设 `CLAUDE_CODE_ATTRIBUTION_HEADER: "0"`, 任何 commit 不带 Co-Authored-By
- **0 force-push, 0 amend** — 所有修改走新 commit, 不用 `--amend` 改 published history
- **0 --no-verify 滥用** — 除非紧急救火 (e.g. CI 阻断 hotfix), 不用 `--no-verify` 绕过 hook
- **提交格式**: `<type>(<scope>): <subject>\n\n<body 中文注释>` (type: feat/fix/refactor/docs/test/chore/perf/ci)
- **commit body 写中文** (per `feedback_chinese_conversation` 偏好), 代码英文
- **commit body 必含**: baseline→target 测试数 (e.g. `pytest 2451 → 2478 (+27)`) + 0 改范围 + 后续 followup

### 2.2 代码规则

- **0 改 historical spec/plan doc `:NNN` 行号** — 8+ 历史 spec/plan docs 的行号引用, 改反误导, 永不做
- **0 改 CLAUDE.md / pyproject.toml / pytest.ini / vite.config.js / vitest.config.js / playwright.config.js** — 除非该 phase 显式声明改 (跟项目约定)
- **0 改 production behavior 除非显式声明** — additive only, 不破旧契约
- **0 真实 LLM 调用 in tests** — `test_novel_writing_real_llm.py` 走 skipif, 默认 SKIP, opt-in 走 `ANTHROPIC_API_KEY=xxx pytest -k real_llm`
- **0 .env 改 / 0 API key 泄漏** — 任何 .env 改动走 user 审批
- **0 改 infra/.state/*.db** (gitignored)
- **0 提交 灵文心流.txt / 01-11_目录** (git-tracked, 0 改即可)

### 2.3 测试规则

- **TDD RED → GREEN → commit** — 写 test 先 (RED), 写实现 (GREEN), 重构, commit
- **2 reviewers per task** — 1 spec compliance + 1 code quality (subagent-driven-development skill)
- **80%+ 覆盖率** — `pytest --cov` + `vitest --coverage` (已 CI 化)
- **测试 entry**: pytest `pytest -q` (~90s), vitest `pnpm test` (~5s), coverage `pnpm test:coverage`, lint `pnpm lint`, e2e `pnpm e2e:smoke`
- **0 ceremonial e2e** — Playwright spec 已 Phase 9.31 F15 全删, 契约走 vitest jsdom (Phase 8.30b pattern)
- **0 改 baseline 0 测试代码** — 2512 pytest + 192 vitest 全部不动, 只加新

### 2.4 文档规则

- **0 改 `:NNN` 行号** (历史 spec/plan) — 改必坏所有 cross-ref, 永不做
- **1 spec + 1 plan per phase** — `docs/superpowers/specs/YYYY-MM-DD-phaseX.Y-<feature>-design.md` + 同名 plan
- **spec 必含**: Context / Goals / Non-goals / Design / Risks + mitigations / Verification / Critical files / Out of scope / DoD
- **plan 必含**: Header (Goal/Architecture/Tech Stack) / File map / Sub-tasks / Critical files / Out of scope / DoD
- **spec/plan 写完 self-review** (placeholder scan / consistency / scope / ambiguity)
- **每 phase commit 必含 spec + plan 独立 commit** (跟 Phase 9.14/9.16/9.17/9.19 模式)
- **commit body 含 deviation 说明** — 任何跟 spec/plan 不符的 (e.g. T3 amend, 漏 test), 1 行标 [实现说明 — plan 偏差]

### 2.5 工作流规则

- **subagent-driven-development** — 1 task 1 fresh subagent + 2 reviewers (spec compliance + code quality)
- **brainstorming 先** — 非平凡实施前先 brainstorm, 1 question at a time, 2-3 approaches with recommendation
- **writing-plans 必含 Goal/Architecture/Tech Stack header** (per skill mandate)
- **finishing-a-development-branch** — 完成 phase 跑 verify tests → 4 options (merge/PR/keep/discard)
- **0 自己改文件** — 改文件必走 subagent (跟 CLAUDE.md "三条铁律" 一致)

---

## 3. 快速开始 (新工具先跑这 3 步)

```bash
# 1. Setup
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen
cd novel-factory
pip install -e .                 # 后端 (含 pytest/vitest 框架)
cd dashboard/frontend && pnpm install && cd ../..

# 2. 验证 baseline (sanity check, 跟 Handoff 同步时的测试数比对)
pytest -q                          # 期望: 2495 passed, 27 skipped, ~90s
cd dashboard/frontend && pnpm test && cd ../..              # 期望: 193 passed, ~5s
cd dashboard/frontend && pnpm test:coverage && cd ../..     # 期望: 193 passed + lcov (lines ≥70%)
cd novel-factory && pytest -q                          # 期望: 2512 passed, ~90s
# (e2e 14 tests, 部分 baseline fail 不是回归, 是 Phase 9.18 已知)

# 3. 启动 dashboard (optional, 看 UI)
# 后端:
cd novel-factory && python dashboard/app.py &  # port 8000
# 前端:
cd novel-factory/dashboard/frontend && pnpm dev --port 5173 --strictPort &
# 浏览器: http://localhost:5173
```

如果 baseline 不匹配 (2512 + 192), 跑 `git log --oneline -20` 跟 git log 校对, 跟 origin/master 比对 (本机 + origin 同步 check: `git rev-parse HEAD origin/master` 应 2 行同 SHA)。

---

## 4. 核心概念速览 (新工具先理解这些)

### 4.1 5 核心 Agent 体系

| Agent | 路径 | 角色池 | 用例 |
|-------|------|--------|------|
| `outline_master` | `infra/agent_system/agents/outline_master/` | 无 (通用) | 大纲生成 |
| `character_designer` | `infra/agent_system/agents/character_designer/` | 无 (通用) | 角色卡 |
| `content_writer` | `infra/agent_system/agents/content_writer/` | 作家 A-J (10 个) | 写正文 |
| `auditor` | `infra/agent_system/agents/auditor/` | 审核员 A-J (10 个) | S1-S8 审核 |
| `polisher` | `infra/agent_system/agents/polisher/` | 读者 A-T (20 个) | 润色 |

每个 agent 通过 `switch_role("writer_b")` 切角色池, 角色池配置在 `.skills/writer-dept/writer-b/SKILL.md`。

### 4.2 12 SCENARIOS 路由

`infra/agent_system/got_bridge.py:SCENARIO_HANDLERS` 路由表, 12 个 scenario 名称 (e.g. `chapter_writing`, `chapter_review`, `polish_emotional_pacing`, `cascade_preview` 等)。每个 scenario 对应 1 个 handler function, handler 调 MasterController 暴露的方法。

### 4.3 跨卷涟漪 (CVG, Cross-Volume Graph)

Phase 9.10-9.19 建立的"跨卷涟漪下游级联"机制, 关键概念:
- `Ripple` (涟漪): 1 个可传播的跨卷引用
- `cascade` (级联): BFS/weighted BFS 找下游涟漪
- `cascade_runs` (历史): 持久化每次 cascade 跑 (Phase 9.20+)
- 4 维 rule-based extractor + LLM scanner (opt-in)
- `audit log` + `real rollback` (Phase 9.14)

### 4.4 5-layer Real LLM Usage

`provider → router → AgentBase → MasterController → got_bridge`, 真实 token 跟踪 (不是估算), 喂 `cost_tracker` → `cost_tracker.db` (SQLite 持久化) → dashboard 展示 (cost by day / by scenario / by tier)。

### 4.5 状态机: workflow.db + ripple.db + cost_tracker.db

3 个 SQLite 库 (全部 gitignored):
- `infra/.state/workflow.db` — 工作流 step/状态
- `infra/.state/ripple.db` — 跨卷涟漪数据
- `infra/.state/cost_tracker.db` — LLM cost 记录 (idx_cost_records_timestamp 索引)

---

## 5. 最近工作 (Phase 8.16 → 9.39)

详细条目在 `~/.claude/projects/.../memory/phases-8-dashboard-a.md` (8.16-9.15) + `phases-8-dashboard-b.md` (9.16-9.23+Closing)。简要:

| Phase | 日期 | 主题 | tests |
|-------|------|------|-------|
| 8.16-8.24 | 2026-06-07/08 | dashboard 时间窗 + composables + CostTrendChart | 2262 |
| 8.30b | 2026-06-08 | 11 ceremonial Playwright → vitest 真 e2e 化 (167 vitest) | 2262 |
| 8.31-8.32 | 2026-06-08 | data-testid 顶层 + 内层统一 | 2262 |
| 8.33-8.45 | 2026-06-08/09 | ESLint 8→10 + husky + CI + Codecov + Playwright install | 2404 |
| 9.10-9.12 | 2026-06-09 | CVG data model + backfill + LLM scanner | 2411 |
| 9.13-9.15 | 2026-06-10 | CVG UI + drawer + audit log + real rollback + 9.15 followup | 2404 |
| 9.16-9.17 | 2026-06-10/11 | cascade weighted BFS + WS push + Pydantic payload + e2e fix | 2438 |
| 9.18-9.19 | 2026-06-11 | ripples-audit unskip + ripple-reset CLI + cascade depth 用户可控制 | 2451 |
| 9.20-9.21 | 2026-06-11 | cascade 持久化 (cascade_runs 表) + cancel | ~2465 |
| 9.22-9.23 | 2026-06-11 | dashboard CascadeRunsPanel UI 回放 + cascade run 过滤 | 2478 |
| 9.24 P0 bookkeeping | 2026-06-11 | F1 (auto-memory 拆) + F2 (typo) + F3 (legacy memory 删) + F8 RESOLVED | 2478 |
| 9.25 F9 DRY SQL | 2026-06-11 | `_update_ripple_status_internal` 抽 helper, reset+rollback 复用 | 2484 |
| 9.26 F10 WS indicator | 2026-06-11 | `SidebarWsDisconnectedBanner` 全局 sidebar, 不依赖 hasCost | 2484/166 vitest |
| 9.27 F11 tier alert | 2026-06-11 | `SidebarTierBudgetAlerts` + `useTierBudgetAlerts` 告警日志 | 2484/175 vitest |
| 9.28 F12 per-tier trend | 2026-06-11 | `cost_by_day_per_tier` 后端聚合 + CostTrendChart multi-series 接通 | 2495/176 vitest |
| 9.29 F13 cumulative line | 2026-06-11 | 单线模式「每日+累计」双 series + `computeCumulativeSeries` helper | 2495/180 vitest |
| 9.30 F14 testid unify | 2026-06-11 | DecisionsPage/WorkflowsPage testid + 2 page spec 0 class selector | 2495/182 vitest |
| 9.31 F15 playwright vitest | 2026-06-11 | 删 10 ceremonial Playwright + 3 vitest page spec (+10) | 2495/192 vitest |
| 9.32 F16 BFS cap config | 2026-06-11 | `max_nodes_cap` 可配置 (default 100, 1..1000) + API/CLI 透传 | 2501/192 |
| 9.33-bk F17 roadmap v2 | 2026-06-11 | followup roadmap v2 (F17-F28) + HANDOFF §6 + v1 superseded pointer | 2501/192 |
| 9.33 F18 backfill execute | 2026-06-11 | `--execute` 幂等 skip + pre/post counts + `--corpus-root` | 2507/192 |
| 9.37 F22 CI pytest | 2026-06-11 | repo root `.github/workflows/` + `--timeout=120` + 5 ci tests | 2512/192 |
| 9.34 F19 LLM calibrate | 2026-06-11 | `scanner_calibration.yaml` + `ripple-scan --calibrate` + edge/backfill 阈值外置 | 2522/192 |
| 9.35 F20 cascade realtime | 2026-06-11 | `CascadeUpdatePayload.latency_ms` + RippleDrawer debounced graph refresh | 2528/193 |
| 9.36 F21 cascade migrate | 2026-06-11 | `cascade migrate --execute` v1→v2_weighted 重写 cascade_runs JSON | 2539/193 |
| 9.38 F23 vitest coverage | 2026-06-11 | `pnpm test:coverage` + CI Codecov 契约测试 (Phase 8.44 补全) | 2545/193 |
| 9.39 F24 eslint flat | 2026-06-11 | `pnpm lint` + ESLint 9+ flat config 契约测试 (Phase 8.43 补全) | 2552/193 |
| 9.40 F25 TS strict | 2026-06-11 | tsconfig strict pilot + 5 spec .js→.ts + typecheck | 2556/193 |
| 9.40-b F26 cost bar | 2026-06-11 | CostBarChart title + tier 配色/legend 对齐 trend | 2556/196 |
| 9.40-c F27 with_usage | 2026-06-11 | polish_merge_synthesis_with_usage CI 契约 | 2562/196 |
| 9.40-d F28 spec note | 2026-06-11 | phase8.45 spec c32015d 编号标注 | 2564/196 |
| 9.41-bk F29 roadmap v3 | 2026-06-11 | followup roadmap v3 (F29-F43) + HANDOFF §6 | 2564/196 |
| 9.41 F30 impact graph | 2026-06-11 | GET /api/cvg/reference-graph + ImpactGraph + RipplesPage | 2569/202 |
| 9.42 F31 query_impact cache | 2026-06-11 | QueryImpactCache + lazy volume load + storage volume filter | 2578/202 |
| 9.43 F32 calibrate feedback | 2026-06-11 | per-dim precision/recall + --yaml-example | 2584/202 |
| 9.44 F33 broadcast log | 2026-06-11 | cascade_broadcast_log + GET broadcast-log API | 2592/202 |
| 9.45 F34 cascade purge | 2026-06-11 | cascade purge --older-than + retention helpers | 2599/202 |
| 9.46 F35 global runs page | 2026-06-11 | CascadeRunsPage + GET /api/cascade/runs | 2605/205 |
| 9.47 F36 algorithm badge | 2026-06-11 | CascadeRunsPanel v1/v2_weighted badge | 2605/207 |
| 9.48 F37 playwright opt-in | 2026-06-11 | dashboard-e2e-smoke.yml + app-root smoke | 2612/207 |

**最近 7 commit** (跟 handoff 同步时校对):
```
[本 commit] test(dashboard): phase 9.39 F24 — ESLint 9+ flat config contract
d838557 ci: phase 9.37 F22 — pytest gate at repo root
3c2020f feat(cvg): phase 9.33 F18 — production backfill execute idempotent
7790864 test(dashboard): phase 9.31 F15 — ceremonial Playwright vitest migration
364b0b1 feat(dashboard): phase 9.30 F14 — page data-testid convention unify
41d7129 feat(dashboard): phase 9.29 F13 — cost cumulative trend line
743838d docs(handoff): v9.28 F12 完成 — HANDOFF 补全
9223222 feat(dashboard): phase 9.28 F12 — per-tier cost trend lines
463046c feat(dashboard): phase 9.27 F11 — tier budget alert log sidebar
61803aa feat(dashboard): phase 9.26 F10 — global sidebar WS disconnect banner
9928a08 refactor(storage): phase 9.25 F9 — DRY ripple status SQL helper
355825e docs(handoff): v9.24 切换开发工具 — 项目进展 + 后续规划整理
572ef0e docs(followup): phase 9.24 F8 ✅ RESOLVED — CI filter 收紧 不做
4c9ddbe chore(memory): phase 9.24 P0 bookkeeping — delete legacy memory/MEMORY.md
edae8a8 feat(dashboard): phase 9.23 T6 — cascade-runs-filter e2e (2 tests)
e07fc12 feat(dashboard): phase 9.23 T5b — CascadeRunsPanel URL sync via window.history
18c8868 Revert "feat(dashboard): phase 9.23 T5 — CascadeRunsPanel URL sync + 3 vitest"
e584dc1 feat(dashboard): phase 9.23 T5 — CascadeRunsPanel URL sync + 3 vitest
[earlier phase 9.22 cascade UI panel commits]
```

---

## 6. 后续 followup (v8, post 9.84)

**汇总 (v8)**: `novel-factory/docs/superpowers/plans/2026-06-11-followup-roadmap-v8-post-9.84.md`

**v7 (F71-F76) 已全部完成** (`e746bdc`). 见 v7 doc: `2026-06-11-followup-roadmap-v7-post-9.78.md`

| # | 主题 | Phase | 估时 | Track | 状态 |
|---|------|-------|------|-------|------|
| F71-bk | v7 roadmap | 9.79-bk | 30min | P0 | ✅ |
| F72 | Manual 1 章 pilot | 9.80 | 2-4h | P1 | ✅ |
| F73 | 批量 runner | 9.81 | 4-6h | P1 | ✅ |
| F74 | ChaptersPage 生产历史 | 9.82 | 3-4h | P2 | ✅ |
| F75 | 决策 deep link | 9.83 | 2-3h | P2 | ✅ |
| F76 | Remote e2e-live | 9.84 | 1h | P3 | ✅ |

**v8 待启动 (推荐顺序):**

| # | 主题 | Phase | 估时 | Track | 状态 |
|---|------|-------|------|-------|------|
| F77-bk | v8 roadmap + HANDOFF | 9.85-bk | 30min | P0 | ✅ |
| **F78** | Settings 预算写入 UI | 9.86 | 2-3h | P2 | ✅ |
| **F79** | Manual batch 3 章 pilot | 9.87 | 2-4h | P1 | ✅ |
| **F80** | Batch dry-run 增强 | 9.88 | 2-3h | P1 | ✅ |
| **F81** | Analytics batch rollup | 9.89 | 3-4h | P2 | 🔴 推荐下一项 |

**推荐下一项**: **F79** Manual batch 3 章 pilot（F78 代码交付后）

---

## 7. 已知 issues / 不破 baseline 区域

### 7.1 Playwright e2e (Phase 9.31 F15 后)

Phase 9.31 F15 已删全部 ceremonial Playwright spec. 契约全走 vitest (`tests/unit/`). Phase 9.48 F37 新增 **1** opt-in smoke spec; Phase 9.65 F56 新增 **2** live-backend spec; Phase 9.72 F64 新增 **`dashboard-e2e-live.yml`**（label `e2e-live` / workflow_dispatch）。CI:
- `dashboard-e2e-smoke.yml` — label `e2e-smoke`, 1 test
- `dashboard-e2e-live.yml` — label `e2e-live`, 5 tests
- **均非 primary merge gate**
- `pnpm e2e:smoke` — vite only，1 test
- `LINGWEN_E2E_LIVE=1 pnpm e2e:live` — vite + `dashboard/e2e_entry.py`，5 tests

### 7.2 MEMORY.md 路径歧义

本项目有 2 套 memory:
- **auto-memory** (用户级, `~/.claude/projects/.../memory/`): 索引 + 详细 phase 历史 (phases-1-to-5.md / phases-6-to-7.md / phases-8-cost.md / phases-8-dashboard-a.md / **phases-8-dashboard-b.md (9.16–9.40)** / **phases-8-dashboard-c.md (9.41+)** / phases.md / MEMORY.md / etc.)。
- **legacy project memory** (`./memory/MEMORY.md`): 已删除 (Phase 9.24 F3), 0 reference。

切换工具时如果新工具不读 auto-memory, 把 phases-8-dashboard-a.md / phases-8-dashboard-b.md 复制一份到 `docs/HANDOFF-HISTORY/` 即可, 但不推荐 (会 drift)。

### 7.3 .state/*.db 不在 git

`infra/.state/cost_tracker.db` / `workflow.db` / `ripple.db` 全 gitignored, 切换工具后第一次跑测试会自动 init (幂等)。

### 7.4 `pnpm dev` 端口约定

Vite dev server 走 `pnpm dev --port 5173 --strictPort` (跟 Playwright e2e 的 `cascade-realtime.spec.js` 1:1 约定)。

---

## 8. 开发工具切换检查清单 (新工具开跑前)

新工具 (e.g. Cursor / Windsurf / Cline / Aider) 打开项目时:

- [ ] 读本 HANDOFF.md (3 分钟)
- [ ] 读 `novel-factory/CLAUDE.md` (主控 agent prompt 模板, 5 分钟)
- [ ] 读 `novel-factory/docs/superpowers/plans/2026-06-11-followup-roadmap-v8-post-9.84.md` (F77+, 5 分钟)
- [ ] 读 auto-memory `phases-8-dashboard-c.md` (最近 phase 详细, 10 分钟)
- [ ] 跑 `pytest -q` 验证 baseline ~2781 collected (~2min)
- [ ] 跑 `cd novel-factory/dashboard/frontend && pnpm vitest run` 验证 vitest **384** passed (~8s)
- [ ] 跑 `git log --oneline -5` 确认 HEAD=`6d5d899` 或更新
- [ ] 跑 `git status` 确认 working tree 干净
- [ ] 选 1 个 v7 item (推荐 **F72** manual pilot; 需 API key)

---

## 9. 关键命令速查

```bash
# === Tests ===
cd novel-factory && pytest -q                                    # ~2781 collected, ~2min
# 增量 backfill (workflow 完成后 opt-in):
# LINGWEN_INCREMENTAL_BACKFILL=1 · LINGWEN_MEMORY_RAG=stub|live
cd novel-factory/dashboard/frontend && pnpm vitest run             # 384 vitest, ~8s
cd novel-factory/dashboard/frontend && pnpm typecheck              # TS strict (tests/**)
cd novel-factory/dashboard/frontend && pnpm typecheck:app          # vue-tsc src/** (F47)
cd novel-factory/dashboard/frontend && pnpm e2e:smoke --list       # 1 smoke test
cd novel-factory/dashboard/frontend && LINGWEN_E2E_LIVE=1 pnpm e2e:live --list  # 5 live tests (opt-in)
cd novel-factory && ruff check .                                 # 0 issues
cd novel-factory/dashboard/frontend && pnpm lint:all             # 0 errors
cd novel-factory/dashboard/frontend && pnpm build                # 0 errors

# === Lint ===
cd novel-factory && ruff check .
cd novel-factory && ruff format --check .

# === Git ===
git log --oneline -20                  # 最近 20 commit
git log --oneline origin/master -20    # origin 最近 20
git rev-parse HEAD origin/master       # 2 行同 SHA = 同步
git status                             # 干净 = 无 pending 改

# === Dashboard ===
cd novel-factory && python dashboard/app.py &                       # port 8000
cd novel-factory/dashboard/frontend && pnpm dev --port 5173 --strictPort &  # port 5173
# 浏览器: http://localhost:5173

# === CLI ===
cd novel-factory && python lingwen.py --help                        # 列出所有 subcommand
cd novel-factory && python lingwen.py status                        # workflow status
cd novel-factory && python lingwen.py cascade <ripple_id>          # cascade preview
cd novel-factory && python -m infra.agent_system.chapter_golden_path  # stub golden path (F59)
```

---

## 10. 紧急联系 / 决策记录

- **GitHub**: `git@github.com:XiaZiHunDun/LingWen.git` (master 单分支, linear history)
- **CLAUDE.md 主控 prompt**: `novel-factory/CLAUDE.md` — 必读, 5 核心 Agent + 22 步 workflow + 强制反馈循环
- **决策模式**: 主公 (user) 决策, 主控 agent 执行, 关键决策点 (大纲审核 / 发布 / 重大变更) 必显式确认
- **协作模式**: 提问 → 选项 → 决策 → 草稿 → 审批 (CLAUDE.md "协作模式" 段)

---

## 11. Auto-memory 文件清单 (新工具可读)

```
~/.claude/projects/-home-ailearn-projects-AI-Incursion-domains-IP---projects-LingWen/memory/
├── MEMORY.md                   # 索引 (32 lines, 必读)
├── phases.md                   # 索引 (66 lines, era split 说明 + 关键里程碑)
├── phases-1-to-5.md            # Phase 1.1-5 基础期 (52 lines)
├── phases-6-to-7.md            # Phase 6-7 dashboard backend (64 lines)
├── phases-8-cost.md            # Phase 8.0-8.15 cost tracking (80 lines)
├── phases-8-dashboard-a.md     # Phase 8.16-9.15 dashboard polish (106 lines)
├── phases-8-dashboard-b.md     # Phase 9.16-9.40 dashboard polish (135 lines)
├── phases-8-dashboard-c.md     # Phase 9.41+ v3/v4/v5 roadmap (9.41+)
├── architecture.md             # 5 核心 Agent + 22 步 (123 lines)
├── history.md                  # v7.0-v9.10 修复史 (111 lines)
├── patterns.md                 # 6 会话并行测试法 + 检测器设计 (170 lines)
├── debugging.md                # bug 解决方案 (32 lines)
├── audit-stale-report.md       # 2026-06-01 深度检查报告 (36 lines, 70% stale)
└── feedback_chinese_conversation.md  # 中文叙述/英文代码/中文 commit 偏好 (14 lines)
```

切换工具如果新工具能读 `~/.claude/projects/.../memory/`, 直接 read MEMORY.md 起步; 不能读就复制本 HANDOFF.md + 关键 phase docs 到 `novel-factory/docs/HANDOFF-HISTORY/`。

---

> **版本**: v9.72 (2026-06-11)
> **下次更新**: 启动 F65+ 后, append entry 到 `phases-8-dashboard-c.md` + 更新本 HANDOFF.md §6
