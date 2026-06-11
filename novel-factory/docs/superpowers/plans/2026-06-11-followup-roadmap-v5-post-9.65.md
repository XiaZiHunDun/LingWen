# Followup Roadmap v5 — Post Phase 9.65 (F56)

> **Superseded by v6 (post 9.72):** `2026-06-11-followup-roadmap-v6-post-9.72.md` — F57-F64 全部完成 (`0983bd0`); 新 backlog 见 F65+.
> **For agentic workers:** 承接 `2026-06-11-followup-roadmap-v4-post-9.54.md` (F44-F56 已于 Phase 9.55-9.65 全部完成). 本 doc 定义 **正文生产 pipeline** 主线 + 顺路 hygiene, 重新编号 **F57+**.
> **创建时间**: 2026-06-11 (主公认同 v5 方向)
> **状态**: **F57-F64 ✅ 全部完成** (2026-06-11, `0983bd0`)
> **前置**: baseline **2742 pytest + 367 vitest** (post F57-F64)

## 上下文 (Context)

Phase 9.55-9.65 (v4) 完成了 Dashboard / CVG / Cascade / DevInfra 收尾:

- DevInfra: vue-tsc src/ · coverage 四维 80% · pre-commit pytest smoke · Playwright live e2e
- CVG: impact scoring · audit export/retention · audit WS push · backfill 增量 · 链式 cascade
- Bookkeeping: auto-memory phases-8-dashboard-c · HANDOFF sync

**v4 清空后缺口:** 359 章《星陨纪元》已发布, 系统下一价值是 **稳定产出下一批正文** — CLI runbook、workflow hook、人审闭环尚未文档化/验收化。Dashboard 章节/分析/设置占位页应 **跟着 pipeline 数据需求** 长出来, 不先行做空壳。

本 v5 **不重复** F1-F56 已 done 项. 详见 v4 doc + HANDOFF §6.

## 当前 Baseline (2026-06-11, post F57-F64 `0983bd0`)

| 项 | 值 |
|----|-----|
| **pytest** | 2742 collected, 27 skipped |
| **vitest** | 367 passed (71 files) |
| **Playwright** | 1 smoke + 5 live opt-in |
| **git** | `0983bd0` on master |
| **Hooks** | backfill · memory RAG stub/live · chapter golden path |

---

## P0 阻塞级 (bookkeeping + hygiene, ~1h)

顺路做, 建议 F59 启动前完成.

### F57-bk. Roadmap v5 文档 + HANDOFF §6/§8 更新

- **方案**: 本 doc + HANDOFF §6 指向 v5 + v4 顶部 superseded pointer
- **estimated**: 30min, 0 new test
- **Phase 映射**: 9.66-bookkeeping

### F58-bk. cascade_notifier 跨线程 broadcast 修复

- **问题**: sync storage path (AnyIO worker thread) 调 `notify_audit_created` → `There is no current event loop in thread 'AnyIO worker thread'`; coroutine 未 schedule
- **方案**: lifespan 注入 main event loop; 非 running loop 线程走 `asyncio.run_coroutine_threadsafe`
- **estimated**: 45min, +1-2 pytest
- **Phase 映射**: 9.66-hygiene

---

## P1 主线 — 正文生产 Pipeline (Phase 9.67-9.69)

Dashboard 占位页 (章节/分析) **不在此 track** — 等 F60 有明确数据契约后再开.

### F59. Phase 9.67 — Chapter runbook + golden path ✅ **DONE**

- **完成 (2026-06-11)**: `docs/chapter-production-runbook.md` + `chapter_golden_path.py` CLI + 4 pytest + 3 CI contract

### F60. Phase 9.68 — Workflow 章节完成 hook 产品化 ✅ **DONE**

- **完成 (2026-06-11)**: `describe_incremental_backfill_hook` + `explain_incremental_backfill_skip` + `backfill_stats_to_dict`; Dashboard `WorkflowStatusResponse.incremental_backfill` + `WorkflowStatus.vue` badge; runbook §7; +7 pytest + 3 CI + 1 vitest

### F61. Phase 9.69 — 人审闭环 smoke (resolve → resume) ✅ **DONE**

- **完成 (2026-06-11)**: `run_human_review_smoke` + `create_golden_dashboard_client`; runbook §4; +4 pytest + 3 CI contract

### F62. Phase 9.70 — MemoryGateway 最小 RAG hook ✅ **DONE**

- **完成 (2026-06-11)**: `chapter_memory_hook.py` + MC `_maybe_memory_context`; golden path 默认 stub; runbook §9; +10 pytest + 3 CI

---

## P2 第二条线 — 记忆 / UI (F63–F64 ✅)

| # | 主题 | 状态 |
|---|------|------|
| F63 | Dashboard 章节页 MVP | ✅ **DONE** |
| F64 | live e2e CI workflow | ✅ **DONE** |

### F63. Phase 9.71 — Dashboard 章节页 MVP ✅ **DONE**

- **完成 (2026-06-11)**: `ChaptersPage.vue`（ChapterTable + 生产状态 + backfill badge）+ 4 vitest + 3 CI contract

### F64. Phase 9.72 — live e2e CI workflow ✅ **DONE**

- **完成 (2026-06-11)**: `.github/workflows/dashboard-e2e-live.yml`（opt-in `e2e-live` label / workflow_dispatch）+ 2 CI contract

---

## P3 明确不做 (继承 v4)

| 项 | 说明 |
|----|------|
| Playwright 全量替代 vitest | vitest primary gate |
| Real LLM in default CI | opt-in only |
| 多用户权限 / 跨项目 ripple | never |
| 改 historical spec `:NNN` 行号 | never |

---

## 决策矩阵

| # | 主题 | 价值 | 紧急度 | 工作量 | Phase | 独立? |
|---|------|------|--------|--------|-------|-------|
| F57-bk | v5 doc + HANDOFF | 中 | 🔴 高 | 0.5h | 9.66-bk | ✅ |
| F58-bk | cascade_notifier 线程 | 中 | 🔴 高 | 0.75h | 9.66-hygiene | ✅ |
| F59 | chapter runbook | 高 | 🔴 高 | 2-3h | 9.67 | ✅ |
| F60 | workflow hook 产品化 | 高 | 🟡 中 | 3-4h | 9.68 | 需 F59 |
| F61 | 人审闭环 smoke | 高 | 🟡 中 | 2-3h | 9.69 | 需 F59 |
| F62 | RAG hook | 中 | 🟢 低 | 4-6h | — | ✅ |
| F63 | 章节页 MVP | 中 | 🟢 低 | 3-5h | — | 需 F60 |

---

## 推荐下一期 phase 顺序

1. **F60** hook 产品化
2. **F61** 人审闭环

---

## 每期启动流程 (不变)

1. 主公从上表选 1 项
2. `brainstorming` → spec + plan (各 1 commit)
3. implement + reviewers → feat commit (body 中文 + baseline→target)
4. append auto-memory `phases-8-dashboard-c.md` + 更新 HANDOFF §5/§6

---

## 完成定义 (DoD) — Roadmap v5 本身

- [x] 本 doc 创建
- [x] HANDOFF §6 更新 (F57+ 表 + 推荐顺序)
- [x] v4 roadmap 顶部加「superseded by v5」pointer
- [x] HANDOFF §8 检查清单指向 v5

---

## 后续

**v5 已全部完成 (F57-F64, `0983bd0`).** 下一版 → **`2026-06-11-followup-roadmap-v6-post-9.72.md`**（推荐 **F65** 真实 1 章 pilot）。
