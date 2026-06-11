# Followup Roadmap v3 — Post Phase 9.40

> **For agentic workers:** 承接 `2026-06-11-followup-roadmap-v2-post-9.32.md` (F17-F28 已于 Phase 9.33-9.40 全部完成). 本 doc 汇总 Phase 9.33-9.40 后各 entry「out of scope」散落项 + Phase 8.45+ / CVG blueprint Phase 14-16 遗留, 重新编号 F29+ 并按 P0/P1/P2/P3 分级.
> **创建时间**: 2026-06-11 (主公选「开 v3 roadmap」)
> **状态**: F29 ✅ (Phase 9.41-bk, 2026-06-11); F30-F43 deferred, 待主公决策
> **前置**: Phase 9.40 F25-F28 ✅ (`7122002`), baseline **2564 pytest + 196 vitest**

## 上下文 (Context)

Phase 9.33-9.40 完成了 v2 全部 track:

- **P1 CVG 生产化**: backfill execute (F18) + LLM 校准 (F19) + cascade 实时拓扑 (F20) + v1→v2 迁移 (F21)
- **P2 DevInfra**: CI pytest (F22) + Vitest coverage (F23) + ESLint 9 (F24) + TS strict pilot (F25)
- **P3 收尾**: CostBarChart polish (F26) + `*_with_usage` closure (F27) + spec 编号标注 (F28)

v2 触发条件已满足. 剩余工作分散在:

- Phase 9 blueprint **Phase 14-16** (perf cache / impact graph viz) 未落地
- Phase 9.20/9.22/9.16 out of scope (cascade runs retention / global runs page / algorithm badge)
- F20 defer (`cascade_broadcast_log` SQLite 表)
- Phase 8.45 out of scope (Playwright CI / TS strict 全量 / DecisionCard meta-info testid)
- F25 pilot 仅 5 spec — `tsconfig.json` include 未扩全

本 v3 roadmap **不重复** F1-F28 已 done 项. 详见 v2 doc 决策矩阵 + HANDOFF §6.

## 当前 Baseline (2026-06-11, post 9.40)

| 项 | 值 |
|----|-----|
| **pytest** | 2564 passed, 27 skipped |
| **vitest** | 196 passed (46 files) |
| **Playwright** | 0 listed (`pnpm e2e:smoke --list`); runner devDep 保留 opt-in |
| **git** | `7122002` on origin/master |
| **CVG** | backfill execute + LLM calibrate + cascade realtime + migrate CLI 全就位 |
| **DevInfra** | CI pytest + coverage + ESLint flat + TS strict pilot (5 spec) |
| **Dashboard cost** | CostBarChart tier polish + CostTrendChart cumulative/per-tier |

---

## P0 阻塞级 (bookkeeping, ~30min)

顺路做, 建议任意新 phase 启动前完成.

### F29. Roadmap v3 文档同步 + HANDOFF §6/§8 更新 ✅ **DONE Phase 9.41-bk**

- **问题**: v2 全部 done 但 §6 无 F29+ 表; HANDOFF §8 仍指向 v2 + stale baseline (2512/192); §9 命令注释过期
- **方案**:
  - 本 doc 创建 + commit
  - HANDOFF §6 指向 v3 + F29-F43 表
  - v2 roadmap 顶部加「superseded by v3」pointer
  - auto-memory `phases.md` / `phases-8-dashboard-b.md` Closing 段 sync
- **estimated**: 30min, 0 new test, 0 改 production code
- **dependency**: 无
- **Phase 映射**: 9.41-bookkeeping

---

## P1 主线 — CVG 可视化 + 性能 (Phase 9.41-9.43)

承接 Phase 9 cross-volume blueprint **Phase 14-16** 中 dashboard 可感知部分. 跟 9.33-9.36 数据/观测 track 互补: 本 track 填 **可视化** + **查询性能**.

### F30. Phase 9.41 — 跨卷 impact graph ECharts 可视化

- **承接**: Blueprint Phase 16「Cross-volume impact graph visualization in dashboard」
- **目标**: RipplesPage / CVG 区域渲染 reference graph 拓扑 (节点/边/维度配色), 跟 CascadeGraph 模式对齐
- **方案**:
  - 新 `ImpactGraph.vue` 或扩展现有 CVG panel
  - API: 复用 `GET /api/ripples/...` 或新增 graph endpoint (additive)
  - ECharts graph series + lazy init + data-testid 契约
- **tests**: 4-6 vitest (mount/empty/data) + 3-5 pytest (API shape)
- **estimated**: 3-4h
- **dependency**: F18 backfill 建议先 (有真实 node/edge 数据); 可 fixture-only if 主公只想 UI skeleton
- **scope boundary**: 0 改 BFS / 0 改 cascade_runs schema

### F31. Phase 9.42 — CVG Phase 14 perf: query_impact LRU + lazy load

- **承接**: Blueprint Phase 14 (`cache.py`, `perf.py`); 当前 `infra/cross_volume/` 仅有 `llm_cache.py`
- **目标**: `query_impact()` 热路径加 LRU cache; 大 volume graph lazy per-volume load
- **方案**:
  - `infra/cross_volume/cache.py` + `@lru_cache` / TTL wrapper
  - storage 层 optional `volume_id` filter 减少全表 scan
  - metrics log (hit/miss count, 0 Prometheus 强依赖)
- **tests**: 6-8 pytest (cache hit/miss / invalidation / lazy load boundary)
- **estimated**: 2-3h
- **dependency**: 无 (跟 F30 正交, 可先做)

### F32. Phase 9.43 — LLM scanner prompt 调优反馈闭环

- **承接**: Blueprint Phase 11→12 defer「prompt hit-rate tuning after UI feedback」; F19 已外置阈值但未闭环
- **目标**: `--calibrate` 输出 + dashboard/CLI 摘要 → 建议阈值调整 (human-in-the-loop, 0 自动写 yaml)
- **方案**:
  - 扩 `ripple-scan --calibrate` 输出 precision/recall per-dim + 推荐 delta
  - 可选: 写 `scanner_calibration.yaml.example` diff 模板 (0 自动 apply)
- **tests**: 4-6 pytest (mock fixture corpus / recommendation math)
- **estimated**: 2-3h
- **dependency**: F19 已就位; F18 建议有数据
- **caveat**: 0 真 LLM in default pytest

---

## P2 Dashboard / 运维 / 工程化 (Phase 9.44-9.51)

跟 CVG 功能独立, 可穿插做.

### F33. Phase 9.44 — `cascade_broadcast_log` SQLite 持久化

- **承接**: F20 out of scope「YAGNI: 先内存+log, 表留 followup」
- **目标**: append_ripple WS 广播 latency 持久化, 供 dashboard 历史查询 / debug
- **方案**: 新表 `cascade_broadcast_log` (ripple_id, latency_ms, ts); storage append + list API (additive)
- **tests**: 5-7 pytest
- **estimated**: 1.5h
- **dependency**: F20

### F34. Phase 9.45 — `cascade_runs` retention cleanup CLI

- **承接**: Phase 9.20 design out of scope「retention policy / purge old runs」
- **目标**: `lingwen.py cascade purge --older-than 90d --dry-run|--execute`
- **tests**: 4-5 pytest (dry-run count / execute / idempotent)
- **estimated**: 1-1.5h
- **dependency**: F4 cascade_runs 表

### F35. Phase 9.46 — Global CascadeRunsPage

- **承接**: Phase 9.22 design「global cross-ripple runs view deferred; drawer tab only」
- **目标**: 新 page 或 Overview 区块: 全 ripple cascade runs 列表 + filter (status/date/algorithm)
- **tests**: 4-5 vitest + 3 pytest (API list endpoint if new)
- **estimated**: 2h
- **dependency**: 9.22 CascadeRunsPanel 组件可复用

### F36. Phase 9.47 — v1/v2 cascade algorithm badge

- **承接**: Phase 9.16 defer「UI badge for bfs_algorithm_version」
- **目标**: CascadeRunsPanel / run row 显示 `v1` / `v2_weighted` badge + data-testid
- **tests**: 2-3 vitest
- **estimated**: 1h
- **dependency**: F21 migrate 可选 (有 v2 数据时 badge 更有意义)

### F37. Phase 9.48 — Playwright CI opt-in workflow

- **承接**: Phase 8.45 out of scope「0 Playwright test in dashboard-frontend-ci.yml」; HANDOFF §7.1 runner devDep only
- **目标**: GH Actions optional job `e2e-smoke` (manual dispatch / label trigger), 1 smoke spec 真 browser
- **方案**: workflow `workflow_dispatch` + `@playwright/test` browser cache; **非 primary gate**
- **tests**: 1 smoke spec + 2-3 CI contract pytest (workflow yaml 存在性)
- **estimated**: 3-4h
- **dependency**: 无
- **caveat**: 跟 vitest primary gate 并存, 0 阻塞 merge

### F38. Phase 9.49 — TypeScript strict 全量 rollout

- **承接**: F25 pilot (5 spec only); Phase 8.47 full strict
- **目标**: 扩 `tsconfig.json` include 至全部 `tests/**/*.ts`; 修 type errors; `pnpm typecheck` CI 契约
- **方案**: 分批 commit 或 1 super-phase; 加 `vue-tsc` 可选 followup
- **tests**: 0 新 vitest; 扩 CI contract + typecheck green
- **estimated**: 4-6h (incremental)
- **dependency**: F25

### F39. Phase 9.50 — Ripple 6-state 生命周期 timeline viz

- **承接**: Phase 9.13/9.14 defer「full status lifecycle graph beyond audit timeline」
- **目标**: RippleDrawer 或 RipplesPage 加 6-state (pending/approved/...) timeline 组件
- **tests**: 3-4 vitest
- **estimated**: 2h
- **dependency**: 9.14 audit log 已就位

### F40. Phase 9.51 — Cascade graph 第 3 视图

- **承接**: Phase 9.18 defer「3rd cascade graph view beyond dry-run + weighted emphasis」
- **目标**: 新 view mode toggle (e.g. depth-layer / action-type cluster) 或 side-by-side compare
- **tests**: 3-4 vitest + 2 pytest
- **estimated**: 2-3h
- **dependency**: 9.15/9.16 CascadeGraph

---

## P3 低优先 / 按需 (F41-F43)

不排期, 主公点名再做.

### F41. DecisionCard meta-info testid + WorkflowGraph 4 status testid

- **承接**: Phase 8.45 out of scope (8.45.1 做了 status badge; meta-info 4 fields + WorkflowGraph 4 status 未做)
- **estimated**: 1-2h + vitest

### F42. Coverage 阈值 70→80 + Codecov badge + GH Pages HTML report

- **承接**: Phase 8.44 / F23 partial (coverage 已跑, 阈值/badge 未 tighten)
- **estimated**: 1.5-2h

### F43. ECharts 5.5 → 6.x 升级

- **承接**: Phase 9.16 defer (security patch)
- **estimated**: 1.5h + vitest smoke

### 明确不做 / RESOLVED

| 项 | 状态 | 说明 |
|----|------|------|
| F1-F28 | ✅ done | v1 + v2 全部完成, 见 HANDOFF §6 |
| F8 CI filter 收紧 | ✅ RESOLVED | skipif + mock 双保险 |
| Real LLM in default tests | 硬规则 | 永不做, opt-in only (`LINGWEN_REAL_LLM=1`) |
| Playwright 全量 e2e 替代 vitest | 不做 | vitest 196 tests 是 primary gate; Playwright opt-in only |
| 多用户权限 / 跨项目 ripple | never | blueprint 标 out-of-scope |
| Cost budget alarm | ✅ done | Phase 8.8 已就位; 9.x doc stale 引用忽略 |

---

## 决策矩阵

| # | 主题 | 价值 | 紧急度 | 工作量 | Phase | 独立? |
|---|------|------|--------|--------|-------|-------|
| F29 | roadmap v3 文档同步 | 中 | 🔴 高 | 0.5h | 9.41-bk | ✅ |
| F30 | CVG impact graph viz | 高 | 🟡 中 | 3-4h | 9.41 | ✅ |
| F31 | CVG query_impact cache | 中 | 🟡 中 | 2-3h | 9.42 | ✅ |
| F32 | LLM prompt 调优闭环 | 中 | 🟢 低 | 2-3h | 9.43 | ✅ |
| F33 | cascade_broadcast_log | 低 | 🟢 低 | 1.5h | 9.44 | ✅ |
| F34 | cascade_runs retention | 低 | 🟢 低 | 1.5h | 9.45 | ✅ |
| F35 | Global CascadeRunsPage | 中 | 🟢 低 | 2h | 9.46 | ✅ |
| F36 | algorithm version badge | 低 | 🟢 低 | 1h | 9.47 | ✅ |
| F37 | Playwright CI opt-in | 中 | 🟢 低 | 3-4h | 9.48 | ✅ |
| F38 | TS strict 全量 | 低 | 🟢 低 | 4-6h | 9.49 | ✅ |
| F39 | Ripple lifecycle timeline | 低 | 🟢 低 | 2h | 9.50 | ✅ |
| F40 | Cascade graph 3rd view | 低 | 🟢 低 | 2-3h | 9.51 | ✅ |
| F41 | meta-info + WFGraph testid | 0 | 🟢 低 | 1-2h | — | ✅ |
| F42 | coverage 80% + badge | 低 | 🟢 低 | 2h | — | ✅ |
| F43 | ECharts 6.x | 低 | 🟢 低 | 1.5h | — | ✅ |

---

## 推荐下一期 phase 顺序

主公决策 (1 phase = 1 commit 节奏):

### Track A — CVG 可视化 + 性能 (推荐主线)

1. **Phase 9.41-bk (F29)** — v3 文档同步 (~30min, 必做顺路) ✅
2. **Phase 9.41 (F30)** — impact graph 可视化 — **产品价值最高**, dashboard 可看见 CVG 拓扑
3. **Phase 9.42 (F31)** — query_impact cache — 大图性能兜底
4. **Phase 9.43 (F32)** — LLM prompt 调优闭环 — 跟 F19 配套

### Track B — Cascade 运维 + Dashboard (可穿插)

1. **Phase 9.44 (F33)** — broadcast log 持久化
2. **Phase 9.45 (F34)** — cascade_runs retention CLI
3. **Phase 9.46 (F35)** — Global CascadeRunsPage
4. **Phase 9.47 (F36)** — algorithm badge

### Track C — 工程化 (可穿插)

1. **Phase 9.48 (F37)** — Playwright CI opt-in
2. **Phase 9.49 (F38)** — TS strict 全量

### 默认推荐 (主公未指定时)

```
F29 (bookkeeping) ✅ → F30 (impact graph) → F33+F34 (cascade ops) → F31 (perf cache) → F37 or F38 (DevInfra 二选一)
```

理由: impact graph 解锁 CVG dashboard 产品价值; cascade ops 低成本运维闭环; perf cache 在大图场景前备好; DevInfra 跟功能正交可穿插.

---

## 每期启动流程 (不变)

1. 主公从上表选 1 项 (F30-F43)
2. `brainstorming` → 1 question at a time → 2-3 approaches
3. `writing-plans` → spec + plan (各 1 commit, 跟 Phase 9.14-9.40 模式)
4. `subagent-driven-development` → implement + 2 reviewers → feat commit
5. append `phases-8-dashboard-b.md` + 更新 HANDOFF §5/§6

---

## 完成定义 (DoD) — Roadmap v3 本身

- [x] 本 doc 创建 + commit (`docs(superpowers): followup roadmap v3 post 9.40`)
- [x] HANDOFF §6 更新 (F29-F43 表 + 推荐顺序)
- [x] auto-memory `phases.md` Closing 段 sync
- [x] v2 roadmap 顶部加「superseded by v3」1 行 pointer (0 删 v2, audit trail)

---

## 后续

v3 清空后下一版 roadmap (v4) 触发条件:

- F30-F32 CVG viz+perf track 全 done, 或
- 主公开新蓝图 (e.g. 正文 v9.13 生产 pipeline / 多 Agent 协作新场景 / 新书项目)
