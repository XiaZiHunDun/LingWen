# Followup Roadmap v6 — Post Phase 9.72 (F64)

> **For agentic workers:** 承接 `2026-06-11-followup-roadmap-v5-post-9.65.md` (F57-F64 已于 Phase 9.66-9.72 全部完成, commit `0983bd0`). 本 doc 定义 **真实正文生产** 主线 + Dashboard 余量 + 测试卫生。
> **创建时间**: 2026-06-11 (v5 清空 + bookkeeping)
> **状态**: v6 **P1–P3 全部完成** (F65–F70); 可选 bookkeeping / 新 roadmap
> **前置**: baseline **2742 pytest + 367 vitest** (post `0983bd0`); Playwright live 5/5; CI opt-in `e2e-live` / `e2e-smoke`

## 上下文 (Context)

Phase 9.66-9.72 (v5) 完成 **stub 正文生产 pipeline** 全链路:

| 交付 | 说明 |
|------|------|
| Runbook | `docs/chapter-production-runbook.md` §1–11 |
| Golden path | `chapter_golden_path` + human review smoke |
| Hooks | `LINGWEN_INCREMENTAL_BACKFILL` · `LINGWEN_MEMORY_RAG=stub\|live` |
| Dashboard | `ChaptersPage` + `incremental_backfill` badge |
| CI | `dashboard-e2e-live.yml` (opt-in) |

**v5 清空后缺口:** stub 路径已验收, 但 **359+ 章真实 LLM 正文** 尚未作为一期 phase 跑通; Dashboard **分析 / 设置** 仍为占位; 全量 pytest 有 **2 个 state 并发用例** 偶发失败。

本 v6 **不重复** F1-F64 已 done 项。详见 v5 doc + HANDOFF §6。

## 当前 Baseline (2026-06-11, post F57-F64)

| 项 | 值 |
|----|-----|
| **pytest** | 2742 collected, 27 skipped (~2708 passed 全绿; 2 state 并发偶发 fail) |
| **vitest** | 367 passed (71 files) |
| **Playwright** | 1 smoke + 5 live opt-in |
| **git** | `0983bd0` on master |
| **Hooks** | backfill (F54/F60) · memory RAG stub/live (F62) · chapter golden (F59) |

---

## P0 Bookkeeping (v6-bk) ✅ **DONE**

- HANDOFF §0/§6/§8/§9 sync post `0983bd0`
- v5 roadmap 标记完成 + superseded pointer
- auto-memory `phases-8-dashboard-c.md` append F57-F64
- 本 v6 doc 创建

---

## P1 主线 — 真实正文生产 (Phase 9.73+)

### F65. Phase 9.73 — 真实章节生产 pilot（1 章） ✅ **DONE**

- **目标**: `novel_writing` + **真实 LLM** 跑通 1 章 (非 CI 默认)
- **交付**:
  - runbook §12「生产环境 checklist」（API keys / corpus / state 目录） ✅
  - `infra/agent_system/chapter_production_pilot.py` + CLI ✅
  - pilot 记录模板: `docs/templates/chapter-pilot-record.example.json` ✅
  - pytest + CI 契约（opt-in `LINGWEN_REAL_LLM=1`） ✅
- **manual gate**: 有 API key 时跑 1 章并填记录模板（不在 CI 默认跑真实 LLM）
- **estimated**: 4–8h（含人工审）
- **env**: `LINGWEN_REAL_LLM=1` · `LINGWEN_INCREMENTAL_BACKFILL=1` · `LINGWEN_MEMORY_RAG=live`
- **Out of scope**: 批量 10 章 · 第二本书 workflow 变体

### F66. Phase 9.74 — 生产 observability 加深 ✅ **DONE**

- **目标**: ChaptersPage / WorkflowStatus 展示 **per-run** 生产摘要（chapter_num + backfill + memory source）
- **交付**:
  - `infra/agent_system/production_summary.py` ✅
  - API/WS `production_summary` + `incremental_backfill` on active workflow ✅
  - `dashboard/frontend/src/utils/productionSummary.js` ✅
  - ChaptersPage + WorkflowStatus UI ✅

---

## P2 Dashboard 余量

| # | 主题 | 说明 | 估时 |
|---|------|------|------|
| F67 | Analytics 页 MVP | 复用 overview charts + 生产 KPI | 3–5h | ✅ |
| F68 | Settings 页 MVP | budget / env 说明只读面板 | 2–3h | ✅ |

### F68. Phase 9.78 — Settings 页 MVP ✅ **DONE**

- **交付**: `SettingsPage.vue` · `utils/settingsBudget.js` · `utils/settingsEnv.js`
- **数据源**: `GET /api/budgets` · `GET /api/budgets/by-tier` · WS `budget_by_tier` snapshot
- **只读**: Token 预算表 + 生产/API key 环境变量说明（不展示密钥值）

### F67. Phase 9.77 — Analytics 页 MVP ✅ **DONE**

- **交付**: `AnalyticsPage.vue` · `utils/analyticsKpi.js` · 生产/涟漪 KPI + 追读力 charts
- **数据源**: `useOverviewStore` · `useRippleStore` · `useWorkflowSocket` (production_summary)

Dashboard **分析 / 设置** 占位已全部替换为 MVP 页（F67/F68）。

---

## P3 测试 / CI 卫生

| # | 主题 | 说明 | 估时 | 状态 |
|---|------|------|------|------|
| F69 | state 并发 pytest 稳定化 | `test_sqlite_state` / `test_workflow_db` | 1–2h | ✅ |
| F70 | e2e-live CI 首跑验证 | label `e2e-live` / local CI parity | 1h | ✅ |

### F69. Phase 9.75 — state 并发 pytest 稳定化 ✅ **DONE**

- **根因**: `test_concurrent_updates_serialized` 错误断言最终必为 `STEP_10`；flock 测试依赖 wall-clock 易 flake
- **修复**: `_fetch_current_step_from_conn` · `flock_probe.peak == 1` · conn 空安全

### F70. Phase 9.76 — e2e-live CI 首跑验证 ✅ **DONE**

- **本地**: `CI=true LINGWEN_E2E_LIVE=1 pnpm e2e:live` → **5 passed** (2026-06-11)
- **脚本**: `scripts/verify-e2e-live-ci.sh`（mirrors `dashboard-e2e-live.yml`）
- **远程**: GitHub Actions → Dashboard E2E Live → Run workflow（或 PR label `e2e-live`）
- **Out of scope**: 并入 primary merge gate

---

## P4 明确不做 (沿袭 v4/v5)

| 项 | 说明 |
|----|------|
| Playwright 全量替代 vitest | vitest primary gate |
| Real LLM in default CI | opt-in only |
| 多用户权限 / 跨项目 ripple | never |
| 改历史 spec `:NNN` 行号 | never |

---

## 决策矩阵

| # | 主题 | 价值 | 紧急度 | 工作量 | 独立? |
|---|------|------|--------|--------|-------|
| F65 | 真实 1 章 pilot | 高 | 🔴 高 | 4–8h | ✅ |
| F66 | 生产 observability | 中 | 🟡 中 | 2–4h | 需 F65 |
| F67 | Analytics MVP | 中 | 🟢 低 | 3–5h | ✅ |
| F68 | Settings MVP | 低 | 🟢 低 | 2–3h | ✅ |
| F69 | state 测试稳定 | 中 | 🟡 中 | 1–2h | ✅ |
| F70 | e2e-live CI 验证 | 低 | 🟢 低 | 1h | ✅ |

---

## 推荐下一期 phase 顺序

v6 清单已清空。可选后续：

1. Manual F65 真实 1 章 pilot（opt-in `LINGWEN_REAL_LLM=1`）
2. v6 bookkeeping commit + 新 roadmap（真实批量生产 / 第二本书等）

---

## 每期启动流程 (不变)

1. 主公从上表选 1 项
2. `brainstorming` → spec + plan（各 1 commit）
3. implement + reviewers → feat commit（body 中文 + baseline→target）
4. append auto-memory + 更新 HANDOFF §5/§6

---

## 完成定义 (DoD) — Roadmap v6 本身

- [x] 本 doc 创建
- [x] HANDOFF §6 指向 v6 + baseline 2742/367
- [x] v5 顶部 superseded pointer
- [x] F70 e2e-live local CI parity 5/5
- [x] F68 Settings MVP + vitest/pytest CI 契约
