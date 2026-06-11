# Followup Roadmap v8 — Post Phase 9.84 (F76)

> **Superseded by v9 planning (post 9.90):** v8 F77–F82 全部完成 (`pending commit`); 新 backlog 待 v9-bk.
> **For agentic workers:** 承接 `2026-06-11-followup-roadmap-v7-post-9.78.md` (F71-F76 已于 Phase 9.79-9.84 全部完成, commit `e746bdc`). 本 doc 定义 **批量正文执行** + **Dashboard 运维写入** + **生产可观测性** 主线, 重新编号 **F77+**.
> **创建时间**: 2026-06-11 (v7 清空 + bookkeeping)
> **状态**: **F77–F82 ✅ 全部完成** (2026-06-11); v8 已清空
> **前置**: baseline **2819 pytest + 384 vitest** (post `e746bdc`); ch360 pilot 已跑通; batch runner 脚手架就绪

## 上下文 (Context)

Phase 9.79-9.84 (v7) 完成 **真实正文首章 + 批量脚手架 + Dashboard 生产链路**:

| 交付 | 说明 |
|------|------|
| F72 | ch360 MiniMax M2.7 pilot (~$0.025) |
| F73 | `chapter_production_batch.py` + runbook §14 |
| F74 | `GET /api/production-records` + ChaptersPage 历史 |
| F75 | 决策中心 ↔ 章节 deep link |
| F76 | Remote e2e-live checklist + workflow summary |

**v7 清空后缺口:** ~~批量 3–10 章尚未真实 LLM 执行~~ F79 ✅; Analytics 未聚合 batch 成本; 360+ 章规模化运维未规划。

本 v8 **不重复** F1-F76 已 done 项。详见 v7 doc + HANDOFF §6.

## 当前 Baseline (2026-06-11, post F71-F76 `e746bdc`)

| 项 | 值 |
|----|-----|
| **pytest** | 2819 collected |
| **vitest** | 384 passed |
| **Playwright** | 1 smoke + 5 live opt-in |
| **git** | `e746bdc` on master |
| **Pilot** | ch360 record in `infra/.state/pilot_records/` (gitignored) |

---

## P0 Bookkeeping (v8-bk)

### F77-bk. Roadmap v8 文档 + HANDOFF §6/§8 更新

- **方案**: 本 doc + HANDOFF §6 指向 v8 + v7 顶部 superseded pointer
- **estimated**: 30min, 0 new test
- **Phase 映射**: 9.85-bookkeeping

---

## P1 主线 — 批量正文执行

### F79. Phase 9.87 — Manual batch pilot（3 章） ✅ **DONE**

- **manual gate**: ch361–363 MiniMax M2.7 batch 成功 (`$0.083`, 3/3 emit, 2026-06-11)
- **交付**: batch summary + per-chapter records · runbook §15 · stub template
- **env**: 同 F72 (`LINGWEN_REAL_LLM=1` · stub memory · `--budget-usd 0.15`)

### F80. Phase 9.88 — Batch 生产 dry-run / preflight 增强 ✅ **DONE**

- **产物**: `--dry-run` · `batch_plan`（章节范围 + 成本预估）· `--calibrate-from` · runbook §16
- **校准**: F79 batch 默认 ~$0.0276/章；env `LINGWEN_BATCH_COST_ESTIMATE_USD` 可覆盖

---

## P2 Dashboard / 运维写入

| # | 主题 | 说明 | 估时 |
|---|------|------|------|
| F78 | Settings 预算写入 UI | day/week + tier PUT 表单 | 2–3h |
| F81 | Analytics batch 成本 rollup | production-records 聚合进 AnalyticsPage | 3–4h |

### F81. Phase 9.89 — Analytics batch 成本 rollup ✅ **DONE**

- **产物**: `GET /api/production-records/rollup` · `rollup_production_records`（成本去重）· AnalyticsPage「生产记录汇总」
- **去重规则**: batch 总计 + 不在 batch 范围内的 pilot 单章成本

### F78. Phase 9.86 — Settings 预算写入 UI ✅ **DONE**

- **交付**: SettingsPage 编辑表单 · `setBudget` / `setBudgetByTier` · `settingsBudgetEdit.js` · vitest + pytest CI 契约
- **Out of scope**: per-run budget UI（仍随 workflow run 传参）

---

## P3 测试 / CI 卫生

| # | 主题 | 说明 | 估时 |
|---|------|------|------|
| F82 | Remote e2e-live 首绿确认 | GitHub Actions 人工 Run workflow 记录 | 30min |

### F82. Phase 9.90 — Remote e2e-live 首绿确认 ✅ **DONE**

- **交付**: runbook §11.3 · `e2e-live-first-green-checklist.sh` · stub 记录模板 · CI 契约
- **manual gate**: GitHub Actions Run workflow（本环境无 `gh` CLI）；本地 parity 见 §11.1

---

## P4 明确不做 (沿袭 v4–v7)

| 项 | 说明 |
|----|------|
| Real LLM in default CI | opt-in only |
| 第二本书 workflow 变体 | 359+ 章同一 `novel_writing` 先跑通 |
| Playwright 全量替代 vitest | vitest primary gate |
| Dashboard 展示 API key | 永不读取密钥值 |

---

## 决策矩阵

| # | 主题 | 价值 | 紧急度 | 工作量 | 独立? |
|---|------|------|--------|--------|-------|
| F78 | Settings 预算写入 | 中 | 🟡 中 | 2–3h | ✅ |
| F79 | Batch 3 章 pilot | 高 | 🔴 高 | 2–4h | 需 API key |
| F80 | Batch dry-run | 中 | 🟢 低 | 2–3h | 需 F79 |
| F81 | Analytics rollup | 中 | 🟢 低 | 3–4h | 需 F79 记录 |
| F82 | Remote e2e 确认 | 低 | 🟢 低 | 30min | ✅ |

---

## 推荐下一期 phase 顺序

v8 清单已清空。可选：GitHub Actions 手动 Run workflow 填首绿记录 · 规划 v9 roadmap（360+ 章规模化等）。

---

## 每期启动流程 (不变)

1. 主公从上表选 1 项
2. `brainstorming` → spec + plan（各 1 commit）
3. implement + reviewers → feat commit（body 中文 + baseline→target）
4. append auto-memory + 更新 HANDOFF §5/§6

---

## 完成定义 (DoD) — Roadmap v8 本身

- [x] 本 doc 创建
- [x] HANDOFF §6 指向 v8 + baseline 2819/384
- [x] v7 顶部 superseded pointer
- [x] F82 remote e2e-live 首绿确认 checklist
