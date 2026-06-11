# Followup Roadmap v4 — Post Phase 9.54 (F43)

> **For agentic workers:** 承接 `2026-06-11-followup-roadmap-v3-post-9.40.md` (F29-F43 已于 Phase 9.41-9.54 全部完成). 本 doc 汇总 v3 清空后各 phase entry「out of scope」散落项 + Phase 8.44/9.14/9.18/9.19 遗留, 重新编号 **F44+** 并按 P0/P1/P2/P3 分级.
> **创建时间**: 2026-06-11 (主公选「开 v4 roadmap」)
> **状态**: F44 deferred, 待主公决策每期 phase 启动时机
> **前置**: Phase 9.54 F43 ✅ (`337fd8a`), baseline **2622 pytest + 227 vitest**

## 上下文 (Context)

Phase 9.41-9.54 完成了 v3 全部 track:

- **P1 CVG 可视化 + 性能**: impact graph (F30) + query_impact cache (F31) + calibrate 闭环 (F32)
- **P2 Cascade 运维 + Dashboard**: broadcast log / retention / global runs / algorithm badge / lifecycle timeline / cascade 3rd view (F33-F40)
- **P2 DevInfra**: Playwright opt-in / TS strict 全量 / coverage 80% + GH Pages / ECharts 6.x (F37-F38, F42-F43)
- **P3 UI testid 收尾**: DecisionCard meta-info + WorkflowGraph state (F41)

v3 触发条件已满足 (F30-F32 done + F29-F43 全清). 剩余工作分散在:

- F38 followup: **`vue-tsc` 对 `src/`** (tests-only typecheck 已就位)
- F42 followup: **statements/functions/branches** 仍低于 80% (lines 已 80.87%)
- Phase 9.14 out of scope: **audit export / retention / WS push**
- Phase 9.16/9.18 defer: **cross-volume impact scoring**
- Phase 9.18/9.19 defer: **cascade depth ≥ 2 / 链式 ripple**
- Phase 9.11 defer: **backfill 增量** (跟 workflow 章节完成 hook)
- Phase 8.44 defer: **pre-commit pytest smoke**
- v1 F1 长期 defer: **auto-memory `phases-8-dashboard-b.md` 拆分 / HANDOFF §8 stale**

本 v4 roadmap **不重复** F1-F43 已 done 项. 详见 v3 doc 决策矩阵 + HANDOFF §6.

## 当前 Baseline (2026-06-11, post 9.54)

| 项 | 值 |
|----|-----|
| **pytest** | 2622 passed, 27 skipped |
| **vitest** | 227 passed (52 files) |
| **coverage (frontend)** | lines 80.87% / statements 78.21% / functions 76.87% / branches 64.91% |
| **Playwright** | 1 smoke spec opt-in (`app-root.spec.js`); vitest primary gate |
| **git** | `337fd8a` on origin/master |
| **ECharts** | 6.1.0 |
| **TS** | strict tests/** + `pnpm typecheck` CI |
| **CVG** | backfill + calibrate + impact graph + cascade 全链路 + broadcast log 就位 |

---

## P0 阻塞级 (bookkeeping, ~30min)

顺路做, 建议任意新 phase 启动前完成.

### F44. Roadmap v4 文档同步 + HANDOFF §6/§8 更新 ✅ **DONE Phase 9.55-bk**

- **问题**: v3 全 done 但 §6 仍写「v3 已清空」; §8 检查清单 stale (2564 pytest / 196 vitest / 推荐 F30)
- **方案**:
  - 本 doc 创建 + commit
  - HANDOFF §6 指向 v4 + F44-F56 表
  - v3 roadmap 顶部加「superseded by v4」pointer
  - HANDOFF §8 baseline 同步 2622/227 + 推荐 **F47** 或 **F50**
- **estimated**: 30min, 0 new test, 0 改 production code
- **dependency**: 无
- **Phase 映射**: 9.55-bookkeeping
- **完成 (2026-06-11)**: v4 doc + HANDOFF §6/§8/§9 sync; F45 顺路完成

### F45. HANDOFF §9 命令注释 + baseline 字符串全量 sync ✅ **DONE Phase 9.55-bk**

- **承接**: F44 顺路
- **完成 (2026-06-11)**: §9 pytest/vitest/typecheck 注释更新至 2622/227

### F46. auto-memory `phases-8-dashboard-b.md` 拆分 / index sync (可选)

- **承接**: v1 F1 long-deferred; `phases-8-dashboard-b.md` 随 9.41-9.54 持续增长
- **方案**: 拆 `phases-8-dashboard-c.md` (9.41+) 或按 era 归档; 更新 `phases.md` index
- **estimated**: 30-45min
- **dependency**: 无 (用户级 auto-memory, 0 进 git 除非 copy 到 `docs/HANDOFF-HISTORY/`)
- **caveat**: 仅当主公使用 Claude auto-memory 时高价值; Cursor-only 可 skip

---

## P1 主线 — DevInfra 收尾 (Phase 9.55-9.57)

承接 F38/F42 partial; 跟功能正交, 可穿插.

### F47. Phase 9.56 — `vue-tsc` 对 `src/` + CI 契约

- **承接**: F38 followup「vue-tsc 可选」; 当前仅 `tests/**/*.ts` strict
- **目标**: `pnpm typecheck:app` (或扩现有 script) 覆盖 `src/**/*.{vue,ts,js}`; CI 非阻塞或 blocking 由主公定
- **方案**: devDep `vue-tsc`; 新/扩 `tsconfig.app.json`; 修 type errors 分批或 1 super-phase
- **tests**: 2-4 pytest CI contract (script exists / workflow step)
- **estimated**: 3-5h
- **dependency**: F38

### F48. Phase 9.57 — Coverage 四维 → 80% (statements / functions / branches)

- **承接**: F42 lines 80 已就位; statements 78.21 / functions 76.87 / branches 64.91
- **目标**: vitest thresholds 全 80; 补 targeted vitest 覆盖 pages/composables 低覆盖区
- **方案**: 优先 `WorkflowsPage` / `DecisionsPage` / `useCostWindow` smoke specs; 阈值最后提
- **tests**: +8-15 vitest (估), 0 改 production behavior
- **estimated**: 3-4h
- **dependency**: F42

### F49. Phase 9.58 — pre-commit pytest smoke (backend)

- **承接**: Phase 8.44 out of scope「pre-commit backend pytest smoke」
- **目标**: husky hook 跑 ~30s smoke subset (`tests/ci/` + 1 integration) 或 `--last-failed` 模式
- **tests**: 2 pytest 契约 (hook 存在 / 子集 green)
- **estimated**: 1.5-2h
- **dependency**: 无
- **caveat**: 0 阻塞 vitest hook (已有 lint-staged); 慢则 opt-in env `LINGWEN_PRECOMMIT_PYTEST=1`

---

## P1 主线 — CVG 产品增强 (Phase 9.59-9.62)

Dashboard 可感知价值; 跟 9.33-9.54 数据层互补.

### F50. Phase 9.59 — cross-volume impact scoring 排名

- **承接**: Phase 9.16/9.18 defer「1 ripple cascade 影响分数 dashboard 排名」
- **目标**: 计算 ripple → affected node/edge 加权分; RipplesPage 列表 sort/filter by score
- **方案**: `infra/cross_volume/scoring.py` + API field `impact_score`; 0 改 BFS 核心
- **tests**: 6-8 pytest (math/fixtures) + 3-4 vitest (badge/sort UI)
- **estimated**: 2-3h
- **dependency**: F30 impact graph 建议先 (UI 容器已就位)

### F51. Phase 9.60 — ripple audit log export (CSV/JSON)

- **承接**: Phase 9.14 out of scope「Audit log export」
- **目标**: `GET /api/ripples/{id}/audit/export?format=csv|json` 或 CLI `ripple-audit export`
- **tests**: 4-5 pytest
- **estimated**: 1.5-2h
- **dependency**: 9.14 audit 表

### F52. Phase 9.61 — ripple audit retention policy

- **承接**: Phase 9.14 out of scope「Audit retention policy」
- **目标**: `lingwen.py ripple-audit purge --older-than Nd` (dry-run/execute), 跟 F34 cascade purge 模式 1:1
- **tests**: 4-5 pytest
- **estimated**: 1.5h
- **dependency**: F51 可选

### F53. Phase 9.62 — audit entry WS push (optional)

- **承接**: Phase 9.14「audit 新增不主动 WS push, 客户端 fetch」
- **目标**: `useWorkflowSocket` 新 event `audit_created` → RippleDrawer 静默 refresh audit list
- **tests**: 3-4 vitest + 2 pytest (payload shape)
- **estimated**: 2h
- **dependency**: 9.14/9.16 WS 基础设施

### F54. Phase 9.63 — backfill 增量 (workflow hook)

- **承接**: Phase 9.11 out of scope「章节完成时增量扫新章」
- **目标**: workflow 节点完成 → trigger incremental `ripple-scan` on new chapter range
- **方案**: hook in MasterController / workflow callback; 0 改 359 章 batch 逻辑
- **tests**: 5-7 pytest (mock workflow event → scan invoked)
- **estimated**: 3-4h
- **dependency**: F18 backfill execute 已就位

---

## P2 大项 — 链式 Cascade (Phase 9.64+, 可拆多 commit)

### F55. Phase 9.64 — cross-volume cascade depth ≥ 2 / 链式 ripple

- **承接**: Phase 9.18/9.19 defer「cascade 触发新 cascade, depth ≥ 2, parent_ripple_id」
- **目标**: `reference_ripples.parent_ripple_id`; BFS 链式 apply; dashboard 显示 parent/child 关系
- **方案**: 拆 sub-phase: (1) schema + storage (2) BFS hook (3) UI tree/badge
- **tests**: 10-15 pytest + 4-6 vitest (估, 按 sub-phase)
- **estimated**: 8-12h (3-4 phases)
- **dependency**: F40 cascade graph 3-view 已就位
- **caveat**: 最大 scope 项; 主公需确认是否开 multi-phase epic

---

## P3 低优先 / 按需 (F56+)

### F56. Playwright e2e 加深 (ripples-audit / decisions resolve)

- **承接**: Phase 9.18 ripples-audit unskip 部分仍 opt-in; F37 仅 app-root smoke
- **目标**: 2-3 opt-in e2e specs 走真 backend + `ripple-reset` fixture; **非 primary gate**
- **tests**: 2-3 playwright + 2 CI contract pytest
- **estimated**: 3-4h
- **dependency**: F37, live backend 或 testcontainer 决策

### 明确不做 / RESOLVED (继承 v3)

| 项 | 状态 | 说明 |
|----|------|------|
| F1-F43 | ✅ done | v1-v3 全部完成, 见 HANDOFF §6 |
| Real LLM in default tests | 硬规则 | 永不做, opt-in only (`LINGWEN_REAL_LLM=1`) |
| Playwright 全量 e2e 替代 vitest | 不做 | vitest 227 tests primary gate |
| 多用户权限 / 跨项目 ripple | never | blueprint out-of-scope |
| `/audit` 独立页 | YAGNI | drawer inline 足够 (9.14) |
| 改 historical spec/plan `:NNN` 行号 | never | audit trail 保留 |

---

## 决策矩阵

| # | 主题 | 价值 | 紧急度 | 工作量 | Phase | 独立? |
|---|------|------|--------|--------|-------|-------|
| F44 | roadmap v4 文档同步 | 中 | 🔴 高 | 0.5h | 9.55-bk | ✅ |
| F45 | HANDOFF baseline sync | 低 | 🟡 中 | 0.3h | 9.55-bk | ✅ |
| F46 | auto-memory 拆分 | 低 | 🟢 低 | 0.5h | — | ✅ |
| F47 | vue-tsc src/ | 中 | 🟡 中 | 3-5h | 9.56 | ✅ |
| F48 | coverage 四维 80% | 中 | 🟡 中 | 3-4h | 9.57 | ✅ |
| F49 | pre-commit pytest smoke | 低 | 🟢 低 | 1.5-2h | 9.58 | ✅ |
| F50 | impact scoring | 高 | 🟡 中 | 2-3h | 9.59 | ✅ |
| F51 | audit export | 中 | 🟢 低 | 1.5-2h | 9.60 | ✅ |
| F52 | audit retention | 低 | 🟢 低 | 1.5h | 9.61 | ✅ |
| F53 | audit WS push | 低 | 🟢 低 | 2h | 9.62 | ✅ |
| F54 | backfill 增量 | 中 | 🟡 中 | 3-4h | 9.63 | ✅ |
| F55 | 链式 cascade ≥2 | 高 | 🟢 低 | 8-12h | 9.64+ | ❌ epic |
| F56 | Playwright 加深 | 低 | 🟢 低 | 3-4h | — | ✅ |

---

## 推荐下一期 phase 顺序

主公决策 (1 phase = 1 commit 节奏):

### Track A — DevInfra 收尾 (推荐默认, 低风险)

1. **Phase 9.55-bk (F44+F45)** — v4 文档 + HANDOFF sync (~30min, **必做顺路**)
2. **Phase 9.56 (F47)** — vue-tsc src/ — 补 F38 最后一里
3. **Phase 9.57 (F48)** — coverage 四维 80% — 补 F42 最后一里

### Track B — CVG 产品 (穿插, 价值导向)

1. **Phase 9.59 (F50)** — impact scoring — **RipplesPage 可排序**, 用户可感知
2. **Phase 9.60 (F51)** — audit export — 运维/调试友好
3. **Phase 9.63 (F54)** — backfill 增量 — 359 章后新书 pipeline 前置

### Track C — 大项 (需主公 explicit 批准)

1. **Phase 9.64+ (F55)** — 链式 cascade — 拆 3-4 sub-phases, 单独 epic

### 默认推荐 (主公未指定时)

```
F44 (bookkeeping) → F47 (vue-tsc) → F50 (impact scoring) → F48 (coverage 80) → F51 (audit export)
```

理由: bookkeeping 解锁 v4 跟踪; vue-tsc 跟 TS strict 自然延伸; impact scoring 产品价值最高且独立; coverage/audit 可穿插.

---

## 每期启动流程 (不变)

1. 主公从上表选 1 项 (F44-F56)
2. `brainstorming` → 1 question at a time → 2-3 approaches
3. `writing-plans` → spec + plan (各 1 commit)
4. implement + reviewers → feat commit (body 中文 + baseline→target 测试数)
5. append auto-memory `phases-8-dashboard-b.md` (或 c) + 更新 HANDOFF §5/§6

---

## 完成定义 (DoD) — Roadmap v4 本身

- [x] 本 doc 创建 + commit (`docs(superpowers): followup roadmap v4 post 9.54`)
- [x] HANDOFF §6 更新 (F44-F56 表 + 推荐顺序)
- [x] v3 roadmap 顶部加「superseded by v4」pointer
- [x] HANDOFF §8 检查清单 baseline 更新 (2622/227)

---

## 后续

v4 清空后下一版 roadmap (v5) 触发条件:

- F47-F54 DevInfra + CVG 增强 track 全 done, 或
- 主公开 **正文生产新蓝图** (v9.13+ 章节 pipeline / 359 章后新书 / 多 Agent 协作新场景)
