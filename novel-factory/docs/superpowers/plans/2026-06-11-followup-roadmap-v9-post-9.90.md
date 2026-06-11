# Followup Roadmap v9 — Post Phase 9.90 (F82)

> **For agentic workers:** 承接 `2026-06-11-followup-roadmap-v8-post-9.84.md` (F77-F82 已于 Phase 9.85-9.90 全部完成, commit `5c988f1`). 本 doc 定义 **360+ 章规模化生产** + **Memory RAG live** + **运维可观测性** 主线, 重新编号 **F83+**.
> **创建时间**: 2026-06-11 (v8 清空 + bookkeeping)
> **状态**: v9 进行中; **推荐 F88** ChaptersPage batch badge
> **前置**: baseline **2845 pytest + 400 vitest** (post `5c988f1`); ch360 + batch 361-363 已跑通

## 上下文 (Context)

Phase 9.85-9.90 (v8) 完成 **批量 pilot + Dashboard 运维 + Analytics rollup**:

| 交付 | 说明 |
|------|------|
| F78 | Settings 预算写入 UI |
| F79 | batch ch361-363 (~$0.083) |
| F80 | batch `--dry-run` + `batch_plan` |
| F81 | Analytics production rollup |
| F82 | Remote e2e-live 首绿 checklist |

**v8 清空后缺口:** 364+ 章 **尚未续跑**; `LINGWEN_MEMORY_RAG=live` **未 pilot**; 10 章 wave 运维 runbook 未写; 远程 e2e 首绿 **记录** 仍 optional manual。

本 v9 **不重复** F1-F82 已 done 项。详见 v8 doc + HANDOFF §6.

## 当前 Baseline (2026-06-11, post F77-F82 `5c988f1`)

| 项 | 值 |
|----|-----|
| **pytest** | 2845 collected |
| **vitest** | 400 passed |
| **Playwright** | 1 smoke + 5 live opt-in |
| **git** | `5c988f1` on master |
| **Pilot** | ch360 + batch 361-363 (gitignored records) |

---

## P0 Bookkeeping (v9-bk)

### F83-bk. Roadmap v9 文档 + HANDOFF §6/§8 更新

- **方案**: 本 doc + HANDOFF §6 指向 v9 + v8 顶部 superseded pointer
- **Phase 映射**: 9.91-bookkeeping

---

## P1 主线 — 360+ 章规模化生产

### F84. Phase 9.92 — Manual batch 续跑（364–366） ✅ **DONE**

- **manual gate**: ch364–366 MiniMax M2.7 batch 成功 (`$0.081`, 3/3 emit, 2026-06-11)
- **交付**: batch summary + per-chapter records · runbook §17
- **env**: 同 F79；dry-run 校准自 `batch-361-363.json`

### F85. Phase 9.93 — 10 章 wave runbook + dry-run 模板 ✅ **DONE**

- **产物**: runbook §18 · `batch-wave-dry-run.sh` · wave stub 模板 · CI 契约
- **wave**: ch367–376 · 默认 budget $0.30 · 校准 batch-364-366（fallback 361-363）
- **Out of scope**: F85 不默认跑真实 10 章 LLM（manual gate 另开）

### F86. Phase 9.94 — MEMORY_RAG=live 单章 pilot ✅

- **目标**: 1 章 pilot with `LINGWEN_MEMORY_RAG=live`（需 Qdrant + Embedder）
- **产物**: runbook §19 · `memory-rag-live-preflight.sh` · preflight gate · live stub 模板 · CI 契约
- **manual gate（已完成 2026-06-11）**: ch367 · MiniMax-only embedding · `memory_context_source=live` · ~$0.022 · record `ch367-live-rag.json`（gitignored）
- **estimated**: 3-5h

### F89. Phase 9.95 — Embedding Provider 解耦（MiniMax embo-01 beta） ✅

- **目标**: `embedding.provider: auto` — OpenAI 默认；仅 `MINIMAX_API_KEY` 时走 MiniMax embedding
- **产物**: `embeddings/{factory,openai,minimax}_provider` · `Embedder` facade · `embedding_provider_keys` preflight · runbook §19 更新 · CI 契约
- **manual gate**: MiniMax `/v1/embeddings` API 可用性（官方 beta；本机 ch367 已验证 embo-01 OK）
- **estimated**: 1-2d

---

## P2 Dashboard / 可观测性

| # | 主题 | 说明 | 估时 |
|---|------|------|------|
| F87 | Analytics 成本趋势 | production-records 按时间序列 mini chart | 3-4h |
| F88 | ChaptersPage 最新 batch badge | 显示最近 batch 范围 | 2h |

---

## P3 测试 / CI 卫生

| # | 主题 | 说明 | 估时 |
|---|------|------|------|
| F90 | e2e-live 首绿 JSON 记录 | 填 stub → ci_records（manual） | 30min |

---

## P4 明确不做 (沿袭 v5–v8)

| 项 | 说明 |
|----|------|
| Real LLM in default CI | opt-in only |
| 第二本书 workflow 变体 | 359+ 章同一 `novel_writing` 先跑通 |
| Settings per-run budget UI | 仍随 workflow run 传参 |

---

## 决策矩阵

| # | 主题 | 价值 | 紧急度 | 工作量 | 独立? |
|---|------|------|--------|--------|-------|
| F84 | Batch 364-366 | 高 | 🔴 高 | 2-4h | 需 API key |
| F85 | 10 章 wave runbook | 中 | 🟡 中 | 2h | 需 F84 |
| F86 | Memory RAG live | 高 | 🟡 中 | 3-5h | 需 Qdrant |
| F89 | Embedding 解耦 | 高 | 🟡 中 | 1-2d | ✅ |
| F87 | Analytics 趋势 | 中 | 🟢 低 | 3-4h | ✅ |
| F88 | Chapters badge | 低 | 🟢 低 | 2h | ✅ |

---

## 推荐下一期 phase 顺序

1. **F88** ChaptersPage 最新 batch badge
2. F89 后续（如有）或 v9 收尾

---

## 完成定义 (DoD) — Roadmap v9 本身

- [x] 本 doc 创建
- [x] HANDOFF §6 指向 v9 + baseline 2845/400
- [x] v8 顶部 superseded pointer
- [x] F85 10 章 wave runbook + dry-run script
- [x] F86 MEMORY_RAG=live preflight gate + runbook §19（live pilot manual gate）
- [x] F89 Embedding Provider 解耦 + MiniMax embo-01 beta
- [x] F86 manual ch367 live RAG pilot（MiniMax-only · record gitignored）
- [x] Qdrant `query_points` 兼容 fix（client 1.18+）
- [x] ch350–360 embed → live `related_segments` 验证（ch367 语义检索 5 hits）
- [x] F87 Analytics 生产成本趋势 mini chart（`/api/production-records/trend`）
