# Followup Roadmap v7 — Post Phase 9.78 (F70)

> **For agentic workers:** 承接 `2026-06-11-followup-roadmap-v6-post-9.72.md` (F65-F70 已于 Phase 9.73-9.78 全部完成, commit `6d5d899`). 本 doc 定义 **真实正文执行** 主线 + 生产运维 + 顺路 CI 卫生, 重新编号 **F71+**.
> **创建时间**: 2026-06-11 (v6 清空 + bookkeeping)
> **状态**: v7 进行中; **推荐 F75** 决策 deep link
> **前置**: baseline **2781 pytest + 384 vitest** (post `6d5d899`); Playwright live 5/5; pilot scaffold ready

## 上下文 (Context)

Phase 9.73-9.78 (v6) 完成 **真实生产脚手架 + Dashboard 收尾 + 测试卫生**:

| 交付 | 说明 |
|------|------|
| F65 | `chapter_production_pilot.py` + runbook §12 + record 模板 |
| F66 | `production_summary` + ChaptersPage / WorkflowStatus 摘要 |
| F67 | `AnalyticsPage` MVP |
| F68 | `SettingsPage` 只读 budget / env |
| F69 | state 并发 pytest 稳定 |
| F70 | e2e-live local CI parity + `verify-e2e-live-ci.sh` |

**v6 清空后缺口:** pilot **脚手架已就绪**, 但 **尚未在有 API key 的环境跑通 1 章真实 LLM**; 359→360+ 批量生产、Dashboard 生产历史、远程 e2e-live 首绿均未做。

本 v7 **不重复** F1-F70 已 done 项。详见 v6 doc + HANDOFF §6.

## 当前 Baseline (2026-06-11, post F65-F70 `6d5d899`)

| 项 | 值 |
|----|-----|
| **pytest** | 2781 collected, 27 skipped |
| **vitest** | 384 passed (76 files) |
| **Playwright** | 1 smoke + 5 live opt-in |
| **git** | `6d5d899` on master |
| **Hooks** | backfill · memory RAG stub/live · production_summary · pilot preflight |

---

## P0 Bookkeeping (v7-bk)

### F71-bk. Roadmap v7 文档 + HANDOFF §6/§8 更新

- **方案**: 本 doc + HANDOFF §6 指向 v7 + v6 顶部 superseded pointer
- **estimated**: 30min, 0 new test
- **Phase 映射**: 9.79-bookkeeping

---

## P1 主线 — 真实正文执行 (Phase 9.80+)

### F72. Phase 9.80 — Manual 1 章 pilot 执行与记录 ✅ **DONE**

- **manual gate**: ch360 MiniMax M2.7 pilot 成功 (`$0.025`, emit ok, 2026-06-11)
- **交付**:
  - `--save-record` + `_json_safe(BackfillStats)` ✅
  - runbook §13 ✅
- **env**: `LINGWEN_REAL_LLM=1` · `LINGWEN_INCREMENTAL_BACKFILL=1` · `LINGWEN_MEMORY_RAG=stub`（首跑推荐 stub）
- **estimated**: 2–4h（含人工审）
- **Out of scope**: 批量 >1 章 · 改 workflow YAML

### F73. Phase 9.81 — 批量章节生产 runner（3–10 章） ✅ **DONE**

- **交付**:
  - `infra/agent_system/chapter_production_batch.py` + CLI ✅
  - `--max-chapters` · `--start-chapter` · `--budget-usd` hard stop ✅
  - batch summary JSON + runbook §14 + pytest ✅

---

## P2 Dashboard / 生产运维

| # | 主题 | 说明 | 估时 |
|---|------|------|------|
| F74 | ChaptersPage 生产历史 | 最近 pilot/batch 记录只读面板 | 3–4h |
| F75 | 决策中心 ↔ 章节 deep link | paused workflow 从章节页跳转 resolve | 2–3h |

### F74. Phase 9.82 — ChaptersPage 生产历史面板 ✅ **DONE**

- **交付**: `GET /api/production-records` · `production_records.py` · ChaptersPage 历史表 + 章节 badge

### F75. Phase 9.83 — 决策中心 ↔ 章节 deep link

- **目标**: ChaptersPage 行点击 → 若该章 workflow paused → 打开 Decision 面板预填 context
- **依赖**: F61 human review smoke 已有; 补 URL query / store 桥接

---

## P3 测试 / CI 卫生

| # | 主题 | 说明 | 估时 |
|---|------|------|------|
| F76 | Remote e2e-live 首绿 | GitHub Actions workflow_dispatch 文档化 + badge 说明 | 1h |

### F76. Phase 9.84 — Remote e2e-live CI 首绿验证

- **本地 parity 已有** (F70); 本项 = 远程 Actions 首跑 checklist + runbook §11.2
- **Out of scope**: 并入 primary merge gate

---

## P4 明确不做 (沿袭 v4–v6)

| 项 | 说明 |
|----|------|
| Real LLM in default CI | opt-in only |
| Settings 预算写入 UI | F68 只读; API PUT 已有, UI 写入另开 v8 |
| 第二本书 workflow 变体 | 359+ 章同一 `novel_writing` 先跑通 |
| Playwright 全量替代 vitest | vitest primary gate |

---

## 决策矩阵

| # | 主题 | 价值 | 紧急度 | 工作量 | 独立? |
|---|------|------|--------|--------|-------|
| F72 | Manual 1 章 pilot | 高 | 🔴 高 | 2–4h | ✅ |
| F73 | 批量 3–10 章 runner | 高 | 🟡 中 | 4–6h | 需 F72 |
| F74 | ChaptersPage 生产历史 | 中 | 🟡 中 | 3–4h | 需 F72/F73 有记录 |
| F75 | 决策 deep link | 中 | 🟢 低 | 2–3h | ✅ |
| F76 | Remote e2e-live | 低 | 🟢 低 | 1h | ✅ |

---

## 推荐下一期 phase 顺序

1. **F75** 决策中心 ↔ 章节 deep link
2. **F76** Remote e2e-live 首绿

---

## 每期启动流程 (不变)

1. 主公从上表选 1 项
2. `brainstorming` → spec + plan（各 1 commit）
3. implement + reviewers → feat commit（body 中文 + baseline→target）
4. append auto-memory + 更新 HANDOFF §5/§6

---

## 完成定义 (DoD) — Roadmap v7 本身

- [x] 本 doc 创建
- [x] 本 doc 创建
- [x] HANDOFF §6 指向 v7 + baseline 2781/384
- [x] v6 顶部 superseded pointer
- [ ] F72 manual pilot 1 章 + 记录文件（脚手架 `--save-record` ✅；需 API key 人工跑）
