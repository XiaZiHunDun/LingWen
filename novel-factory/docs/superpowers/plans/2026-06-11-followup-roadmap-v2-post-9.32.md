# Followup Roadmap v2 — Post Phase 9.32

> **For agentic workers:** 承接 `2026-06-11-followup-roadmap.md` (F1-F16 已于 Phase 9.24-9.32 全部完成). 本 doc 汇总 Phase 9.10-9.32 各 entry「out of scope」散落项 + Phase 8.x 工程化遗留, 重新编号 F17+ 并按 P0/P1/P2/P3 分级.
> **创建时间**: 2026-06-11 (主公选「重新开 roadmap」)
> **状态**: F17 ✅ (Phase 9.33-bk, 2026-06-11); F18-F28 deferred, 待主公决策
> **前置**: Phase 9.32 F16 ✅ (`1a23bbe`), baseline **2501 pytest + 192 vitest**

## 上下文 (Context)

Phase 9.10-9.32 完成了 CVG 数据层 + dashboard cascade 全链路 (持久化/取消/回放/过滤/max_nodes_cap). 原 roadmap F1-F16 清零. 剩余工作分散在:

- Phase 9.17/9.19 out of scope (LLM 校准 / cascade 实时拓扑 / backfill 未跑)
- Phase 8.35-8.42 out of scope (ESLint 9 / coverage / CI pytest / TS strict)
- Phase 8.7 遗留 (cost 柱状图 / `*_with_usage`)
- Roadmap v1 自身 DoD 未完成项 (phases.md 索引 stale)

本 v2 roadmap **不重复** F1-F16 已 done 项. 详见 v1 doc「已完成」段 + HANDOFF §6.

## 当前 Baseline (2026-06-11, post 9.32)

| 项 | 值 |
|----|-----|
| **pytest** | 2501 passed, 27 skipped |
| **vitest** | 192 passed (46 files) |
| **Playwright** | 0 listed (`pnpm e2e:smoke --list`) |
| **git** | `1a23bbe` on origin/master |
| **CVG** | ripple.db + cascade_runs + preview/persist/cancel/filter/max_nodes_cap 全就位 |
| **backfill** | Phase 9.11 rule-based extractor 就位, **359 章历史扫未跑** (dry-run only) |
| **LLM scanner** | Phase 9.12 opt-in 就位, **confidence 阈值未校准** |

---

## P0 阻塞级 (bookkeeping, ~30min)

顺路做, 建议任意新 phase 启动前完成.

### F17. Roadmap v2 文档同步 + 索引 stale 修复 ✅ **DONE Phase 9.33-bk**

- **问题**: v1 roadmap DoD 4 项未全完成; auto-memory `phases.md` 仍写「推荐 F4 Phase 9.20」; HANDOFF §6 空
- **方案**:
  - 本 doc 创建 + commit
  - HANDOFF §6 指向 v2 + F17-F28 表
  - auto-memory `phases.md` Closing 段更新 (F1-F16 done + v2 pointer)
  - `phases-8-dashboard-b.md` Closing 段 append v2 link
- **estimated**: 30min, 0 new test, 0 改 production code
- **dependency**: 无
- **Phase 映射**: 9.33-bookkeeping (或跟首个功能 phase 同 commit 不推荐, 独立 1 commit 更清晰)

---

## P1 主线 — CVG 生产化 (Phase 9.33-9.36)

承接 Phase 9 blueprint「Phase 10-14」中 **尚未 production 化** 的部分. 跟 dashboard cascade UI (9.20-9.23) 互补: 本 track 填 **数据** + **观测**, 不是 UI.

### F18. Phase 9.33 — 359 章历史 backfill 正式跑 ✅ **DONE Phase 9.33**

- **承接**: Phase 9.11 `extraction_rules.yaml` 4 维 rule-based extractor + Backfiller CLI, **仅 dry-run, 0 跑全量**
- **目标**: 对《星陨纪元》359 章跑 1 次 production backfill, 写入 ripple.db / reference graph
- **方案**:
  - `lingwen.py ripple-backfill --execute` (或等价 flag, default 仍 dry-run 保 backward compat)
  - 跑前 snapshot / 跑后 node+edge count 日志
  - idempotent: 已存在 node 跳过或 merge (跟 Phase 9.11 design 1:1)
- **tests**: 4-6 new (CLI flag / idempotent re-run / count assertion on fixture corpus)
- **estimated**: 2-3h (含 fixture 359 章 subset, 0 真跑 359 章 in CI)
- **dependency**: 无 (F17 建议先做 bookkeeping)
- **caveat**: CI **0 真 LLM**; production run 走主公本地 opt-in. CI 只测 CLI + 小 fixture (≤10 章)
- **scope boundary**: 0 改 extractor 规则逻辑 unless backfill 暴露 bug; 0 改 dashboard

### F19. Phase 9.34 — LLM scanner confidence 校准 ✅ **DONE Phase 9.34**

- **承接**: Phase 9.12 LLM scanner opt-in + Phase 9.17 out of scope「4 维 confidence 校准 + 阈值 adjust after real LLM run」
- **目标**: 基于真实 LLM 跑样本 (≥20 章) 调 `llm_scanner.py` / `edge_inferrer.py` 阈值, 降 false positive
- **方案**:
  - 新增 `infra/cross_volume/scanner_calibration.yaml` (阈值外置, 0 hardcode magic number)
  - CLI `lingwen.py ripple-scan --calibrate` 输出 precision/recall 摘要 (走 fixture + opt-in API key)
  - default 阈值 backward compat (未校准 path 行为不变)
- **tests**: 6-8 new (yaml load / threshold boundary / mock LLM response)
- **estimated**: 2-3h
- **dependency**: F18 建议先 (有真实 graph 数据校准更有意义); 可独立 if 主公只想调阈值
- **caveat**: 0 真 LLM in default pytest; skipif opt-in 跟 Phase 9.12 1:1

### F20. Phase 9.35 — cascade 广播 latency 监控 + dashboard 拓扑实时刷新 ✅ **DONE Phase 9.35**

- **承接**: Phase 9.17 out of scope「CascadeUpdatePayload 广播 latency 监控 + dashboard 拓扑实时刷新 (跟 Phase 8.21 idx_timestamp 镜像)」
- **目标**: append_ripple 触发 cascade WS 广播时记录 latency_ms; dashboard CascadeGraph 收到 `onCascadeUpdate` 后 auto-refresh (0 手动 reload)
- **方案**:
  - `cascade_notifier.py` 加 `latency_ms` field (optional, additive)
  - `CascadeGraph.vue` / `useWorkflowSocket` 已有 hook → 加 debounced re-fetch
  - 可选: SQLite `cascade_broadcast_log` 表 (YAGNI: 先内存+log, 表留 followup)
- **tests**: 5-7 pytest (notifier latency) + 3-4 vitest (graph refresh on mock WS event)
- **estimated**: 2h
- **dependency**: 无 (F4-F7 cascade 持久化已就位)
- **scope boundary**: 0 改 BFS 算法 / 0 改 cascade_runs schema

### F21. Phase 9.36 — v1→v2 cascade 数据迁移 (optional) ✅ **DONE Phase 9.36**

- **承接**: 多处 out of scope「0 cascade data migration (旧 v1 cascade 仍可读)」
- **目标**: 提供 opt-in migration CLI, 把历史 v1 BFS 结果重算为 v2_weighted (0 强制)
- **方案**: `lingwen.py cascade migrate --dry-run|--execute`, 读 cascade_runs JSON, 重写 algorithm field + nodes/edges
- **tests**: 4-5 new (dry-run / execute / idempotent)
- **estimated**: 1.5-2h
- **dependency**: F4 (cascade_runs 表)
- **priority**: 🟢 低 — 旧 v1 仍可读, 主公无 pain 可 indefinitely defer

---

## P2 工程化 — DevInfra (Phase 9.37-9.40)

Phase 8.35-8.42 super-phase 留 followup, 跟 CVG 功能独立, 可穿插做.

### F22. Phase 9.37 — CI pytest gate ✅ **DONE Phase 9.37**

- **承接**: Phase 8.52「CI 测 pytest (45s 慢, 留 followup)」
- **方案**: GitHub Actions 加 `pytest -q` job (或 `-x --timeout=120` 防 hang); 跟 vitest job 并行
- **estimated**: 1-1.5h (含 workflow yaml + cache pip)
- **dependency**: 无
- **caveat**: 90s CI 预算; 可先用 `-k "not slow"` 若存在 slow marker (当前 0 slow marker → 全跑)

### F23. Phase 9.38 — Vitest coverage 报告 ✅ **DONE Phase 9.38**

- **承接**: Phase 8.46「0 装 @vitest/coverage-v8」
- **方案**: devDep `@vitest/coverage-v8` + `vitest.config.js` coverage block + CI upload (Codecov 已就位 Phase 8.41)
- **estimated**: 1h
- **dependency**: 无

### F24. Phase 9.39 — ESLint 8 → 9 升级 ✅ **DONE Phase 9.39**

- **承接**: Phase 8.43
- **方案**: eslint 9 + flat config migration (跟 vue/eslint 生态对齐)
- **estimated**: 1.5-2h (含 rule 破 fix)
- **dependency**: 无

### F25. Phase 9.40 — TypeScript strict mode (incremental)

- **承接**: Phase 8.47
- **方案**: 新 spec 强制 `.ts`; 旧 `.js` spec 0 强迁; `tsconfig.json` strict + allowJs
- **estimated**: 2h (首批 3-5 spec 转 .ts pilot)
- **dependency**: 无

---

## P3 低优先 / 按需 (F26-F28)

不排期, 主公点名再做.

### F26. Cost 柱状图 UI 改 (Phase 8.7 defer)

- **方案**: CostBarChart 视觉/交互 polish (跟 CostTrendChart 9.29 累计线对齐)
- **estimated**: 1.5h + 2-3 vitest

### F27. `polish_merge_synthesis` `*_with_usage` variant (Phase 8.7 defer)

- **方案**: cost 走真实 token usage 而非估算
- **estimated**: 2h + pytest
- **dependency**: ai_service usage tracking 已就位

### F28. Spec 编号错位标注 (doc-only)

- **问题**: commit 0a8a900 spec 跟 Phase 9.10 spec c32015d Phase 编号不一致
- **方案**: 在 spec header 加 `> **Note**: Phase 编号以 c32015d 为准` 1 行, 0 改正文
- **estimated**: 15min

### 明确不做 / RESOLVED

| 项 | 状态 | 说明 |
|----|------|------|
| F8 CI filter 收紧 | ✅ RESOLVED | skipif + mock 双保险, v1 已标 |
| Playwright 真 browser e2e | opt-in | devDep 保留, 非 primary gate, 0 排 F 编号 |
| Real LLM in default tests | 硬规则 | 永不做, opt-in only |

---

## 决策矩阵

| # | 主题 | 价值 | 紧急度 | 工作量 | Phase | 独立? |
|---|------|------|--------|--------|-------|-------|
| F17 | roadmap v2 文档同步 | 中 | 🔴 高 | 0.5h | 9.33-bk | ✅ |
| F18 | 359 章 backfill 正式跑 | 高 | 🟡 中 | 2-3h | 9.33 | ✅ |
| F19 | LLM scanner 校准 | 高 | 🟡 中 | 2-3h | 9.34 | ✅ |
| F20 | cascade 实时拓扑刷新 | 中 | 🟢 低 | 2h | 9.35 | ✅ |
| F21 | v1→v2 cascade 迁移 | 低 | 🟢 低 | 1.5h | 9.36 | ✅ |
| F22 | CI pytest | 高 | 🟡 中 | 1.5h | 9.37 | ✅ |
| F23 | Vitest coverage | 中 | 🟢 低 | 1h | 9.38 | ✅ |
| F24 | ESLint 9 | 低 | 🟢 低 | 2h | 9.39 | ✅ |
| F25 | TS strict pilot | 低 | 🟢 低 | 2h | 9.40 | ✅ |
| F26 | Cost 柱状图 UI | 低 | 🟢 低 | 1.5h | — | ✅ |
| F27 | *_with_usage | 低 | 🟢 低 | 2h | — | ✅ |
| F28 | spec 编号标注 | 0 | 🟢 低 | 15m | — | ✅ |

---

## 推荐下一期 phase 顺序

主公决策 (1 phase = 1 commit 节奏):

### Track A — CVG 生产化 (推荐主线)

1. **Phase 9.33-bookkeeping (F17)** — 文档同步 (~30min, 必做顺路)
2. **Phase 9.33 (F18)** — 359 章 backfill 正式跑 — **产品价值最高**, 让 CVG 有真实数据
3. **Phase 9.34 (F19)** — LLM scanner 校准 — 跟 F18 配套
4. **Phase 9.35 (F20)** — cascade 拓扑实时刷新 — dashboard 体验闭环

### Track B — 工程化 (可穿插)

1. **Phase 9.37 (F22)** — CI pytest — 防回归, 跟任何功能 phase 正交
2. **Phase 9.38 (F23)** — Vitest coverage
3. **Phase 9.39-9.40 (F24-F25)** — ESLint 9 + TS strict

### 默认推荐 (主公未指定时)

```
F17 (bookkeeping) → F18 (backfill) → F22 (CI pytest) → F19 (LLM calibrate) → F20 (cascade realtime)
```

理由: backfill 解锁 CVG 真实价值; CI pytest 在 backfill 改 storage 前锁住 baseline; LLM 校准需有数据; 实时拓扑是 UX 收尾.

---

## 每期启动流程 (不变)

1. 主公从上表选 1 项 (F17-F28)
2. `brainstorming` → 1 question at a time → 2-3 approaches
3. `writing-plans` → spec + plan (各 1 commit, 跟 Phase 9.14-9.32 模式)
4. `subagent-driven-development` → implement + 2 reviewers → feat commit
5. append `phases-8-dashboard-b.md` + 更新 HANDOFF §5/§6

---

## 完成定义 (DoD) — Roadmap v2 本身

- [x] 本 doc 创建 + commit (`docs(superpowers): followup roadmap v2 post 9.32`)
- [x] HANDOFF §6 更新 (F17-F28 表 + 推荐顺序)
- [x] auto-memory `phases.md` Closing 段 sync
- [x] v1 roadmap 顶部加「superseded by v2」1 行 pointer (0 删 v1, audit trail)

---

## 后续

v2 清空后下一版 roadmap (v3) 触发条件:

- F18-F20 CVG 生产化 track 全 done, 或
- 主公开 Phase 10 新蓝图 (e.g. 正文 v9.13 生产 pipeline / Agent 协作新场景)

EOF
