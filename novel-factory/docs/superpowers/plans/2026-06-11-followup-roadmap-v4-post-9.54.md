# Followup Roadmap v4 — Post Phase 9.54 (F43)

> **For agentic workers:** 承接 `2026-06-11-followup-roadmap-v3-post-9.40.md` (F29-F43 已于 Phase 9.41-9.54 全部完成). 本 doc 汇总 v3 清空后各 phase entry「out of scope」散落项 + Phase 8.44/9.14/9.18/9.19 遗留, 重新编号 **F44+** 并按 P0/P1/P2/P3 分级.
> **创建时间**: 2026-06-11 (主公选「开 v4 roadmap」)
> **状态**: F44-F56 ✅ (2026-06-11); v4 roadmap 已清空
> **前置**: baseline **2670 pytest + 361 vitest** (post F56)

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

## 当前 Baseline (2026-06-11, post F56)

| 项 | 值 |
|----|-----|
| **pytest** | 2670 passed, 27 skipped |
| **vitest** | 361 passed (70 files) |
| **coverage (frontend)** | lines 94.37% / statements 92% / functions 91.23% / branches 80.02% |
| **Playwright** | 1 smoke spec opt-in (`app-root.spec.js`); vitest primary gate |
| **git** | `aa1d29b` on master (F47-F51 4 commits) |
| **ECharts** | 6.1.0 |
| **TS** | strict tests/** + `pnpm typecheck:app` src/** CI |
| **CVG** | backfill + calibrate + impact graph + impact scoring + audit export |

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

### F46. auto-memory `phases-8-dashboard-b.md` 拆分 / index sync ✅ **DONE**

- **完成 (2026-06-11)**: `phases-8-dashboard-c.md` (9.41+) + phases.md / MEMORY.md index sync

---

## P1 主线 — DevInfra 收尾 (Phase 9.55-9.57)

承接 F38/F42 partial; 跟功能正交, 可穿插.

### F47. Phase 9.56 — `vue-tsc` 对 `src/` + CI 契约 ✅ **DONE**

- **完成 (2026-06-11)**: `5b8a543` — tsconfig.app.json + `pnpm typecheck:app` + CI step + 3 pytest 契约

### F48. Phase 9.57 — Coverage 四维 → 80% (statements / functions / branches) ✅ **DONE**

- **完成 (2026-06-11)**: `aa1d29b` — vitest thresholds 全 80; branches 80.02% 达标; +120 vitest

### F49. Phase 9.58 — pre-commit pytest smoke (backend) ✅ **DONE**

- **完成 (2026-06-11)**: opt-in `LINGWEN_PRECOMMIT_PYTEST=1|last-failed`; smoke subset tests/ci/ + health (~2s)

---

## P1 主线 — CVG 产品增强 (Phase 9.59-9.62)

Dashboard 可感知价值; 跟 9.33-9.54 数据层互补.

### F50. Phase 9.59 — cross-volume impact scoring 排名 ✅ **DONE**

- **完成 (2026-06-11)**: `ab4423f` — scoring.py + API sort_by/min_score + RipplesPage badge/sort UI

### F51. Phase 9.60 — ripple audit log export (CSV/JSON) ✅ **DONE**

- **完成 (2026-06-11)**: `GET /api/cvg/ripples/{id}/audit/export?format=csv|json` + 5 pytest

### F52. Phase 9.61 — ripple audit retention policy ✅ **DONE**

- **完成 (2026-06-11)**: audit_retention.py + storage purge helpers + ripple-audit purge subcommand

### F53. Phase 9.62 — audit entry WS push (optional) ✅ **DONE**

- **完成 (2026-06-11)**: `audit.created` WS event + `notify_audit_created` + RippleDrawer 静默 refresh; +3 pytest +3 vitest

### F54. Phase 9.63 — backfill 增量 (workflow hook) ✅ **DONE**

- **完成 (2026-06-11)**: `Backfiller.run_chapters` + `incremental_backfill.py` + MC hook; opt-in `LINGWEN_INCREMENTAL_BACKFILL=1`

---

## P2 大项 — 链式 Cascade (Phase 9.64+, 可拆多 commit)

### F55. Phase 9.64 — cross-volume cascade depth ≥ 2 / 链式 ripple ✅ **DONE**

- **完成 (2026-06-11)**: `parent_ripple_id` schema + `spawn_child_ripples` + RippleCard/Drawer parent-child badge; +5 pytest +3 vitest

---

## P3 低优先 / 按需 (F56+)

### F56. Playwright e2e 加深 (ripples-audit / decisions resolve) ✅ **DONE**

- **完成 (2026-06-11)**: `ripples-audit.spec.js` (3) + `decisions-resolve.spec.js` (2) + `e2e_seed.py` + `e2e:live` script; +5 pytest

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
| F52 | audit retention | 低 | 🟢 低 | 1.5h | 9.61 | ✅ |
| F53 | audit WS push | 低 | 🟢 低 | 2h | 9.62 | ✅ |
| F54 | backfill 增量 | 中 | 🟡 中 | 3-4h | 9.63 | ✅ |
| F55 | 链式 cascade ≥2 | 高 | 🟢 低 | 8-12h | 9.64+ | ✅ |
| F56 | Playwright 加深 | 低 | 🟢 低 | 3-4h | 9.65 | ✅ |

---

## 推荐下一期 phase 顺序

**v4 (F44-F56) 已于 2026-06-11 全部完成.** 主公决策是否开 v5 roadmap.

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
