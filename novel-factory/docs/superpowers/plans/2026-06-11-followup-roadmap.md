# Followup Roadmap — Post Phase 9.19

> **Superseded by v2 (post 9.32):** `2026-06-11-followup-roadmap-v2-post-9.32.md` — F1-F16 全部完成, 新 backlog 见 F17-F28.
> **For agentic workers:** Bookkeeping 计划 — 整理 Phase 9.19 之后所有 deferred followup, 按 P0/P1/P2 分级 + dependencies 排序。
> **创建时间**: 2026-06-11 (主公要求 "重新整理后续计划")
> **状态**: 全部 deferred, 待主公决策每期 phase 启动时机
> **追溯**: 详见 `phases-8-dashboard.md` 各 phase entry "out of scope (有 followup)" 段落

## 上下文 (Context)

Phase 9.19 cascade user-controllable depth 已合并 (commit 2255dfd, 2026-06-11), 2451 pytest passed, 27 skipped, 0 failed. 既 9.10-9.19 期间累计 18+ followup 项散落在各 phase entry "out of scope" 段落, 没有任何集中跟踪文档. 本 plan 把它们汇总分级 + 标注 dependencies, 供主公决策下一期 phase 选哪条线.

## 当前 Baseline (2026-06-11)

- **代码**: 2451 pytest passed + 148 vitest passed + 10 e2e listed = 2609 total, 0 failed, 27 skipped
- **storage.py**: 1 new method (`preview_cascade`, Phase 9.19)
- **dashboard/app.py**: 2 endpoint 加 `?max_depth=` query param + `_validate_max_depth` helper
- **lingwen.py**: 1 new CLI subcommand (`cascade`)
- **git**: `2255dfd` 在 origin/master, working tree clean
- **memory**: `phases-8-dashboard.md` 217 行超 200 soft cap, 必拆

## P0 阻塞级 (bookkeeping)

### F1. MEMORY.md 拆 phases.md topic (long-deferred, 累计 5+ phase out_of_scope 提到)

- **状态**: phases-8-dashboard.md 217 行, 超 200 soft cap
- **影响**: 后续加 entry 会更超, 必拆
- **方案**: 拆 phases-8-dashboard-a.md (Phase 8.16-9.15 ~115L) + phases-8-dashboard-b.md (Phase 9.16-9.19 ~100L), MEMORY.md pointer 更新
- **estimated**: 30min, 0 new test, 0 改 production code
- **dependency**: 无 (无前置)
- **owner**: 主公下次起 phase 顺手做

### F2. MEMORY.md line 12 typo 修 ("Phase 8.16-8.45" → "Phase 8.16-9.19")

- **状态**: Phase 8.45 后又 5 个 phase 没更新
- **estimated**: 1min (一行 edit)
- **dependency**: 无 (跟 F1 一起做)

### F3. legacy `./memory/MEMORY.md` v6.1 → v9.24 sync

- **状态**: 老的根目录 `memory/MEMORY.md` 是 v6.1 旧版 (跟 `.claude/.../memory/MEMORY.md` 不同), 跟当前 v9.24 项目严重脱节
- **方案**: 要么删除 (active path 全走 `.claude/.../memory/`), 要么 sync v9.24 内容覆盖
- **estimated**: 5min
- **dependency**: 主公决策 "删 or sync"

## P1 主线 followup (cascade persistence 路线)

Phase 9.20-9.23 一条线, 把 Phase 9.19 `preview_cascade` (瞬时 BFS) 升级到持久化 + 回放 + 取消 + 过滤. 5 entry points 协同 (`RippleStorage` 新 method + `dashboard/app.py` endpoint + `lingwen.py` CLI + dashboard UI 回放 panel + e2e spec).

### F4. Phase 9.20 — cascade 持久化到 DB

- **承接**: Phase 9.19 `preview_cascade` (无持久化) → 加 `record_cascade_run` (持久化 cascade run)
- **设计**: 新表 `cascade_runs` (id / ripple_id / max_depth / depth_reached / algorithm / started_at / completed_at / status: running|completed|cancelled). 节点/边 JSON 内嵌 (跟 Phase 9.15 `ripple_cascade` 表 1:1 风格, 简化 query)
- **method**: `RippleStorage.record_cascade_run(ripple_id, cascaded)`, `get_cascade_runs(ripple_id, limit=10)`, `get_cascade_run_by_id(run_id)`
- **endpoint**: `GET /api/ripples/{id}/cascade-runs` (history list)
- **CLI**: `lingwen.py cascade --persist` (新增 flag, default off 保 backward compat 跟 Phase 9.19)
- **tests**: 8-12 new (3 storage + 5 endpoint + 2-4 CLI)
- **estimated**: 2-3 hours
- **dependency**: 无 (承接 Phase 9.19 preview_cascade)
- **scope boundary**: 0 改 Phase 9.19 既有 API 行为, 仅 additive 1 new table + 3 new method + 1 new endpoint + 1 new CLI flag

### F5. Phase 9.21 — cascade cancel (mark cancelled status)

- **承接**: Phase 9.20 cascade run 持久化后, 加 cancel 能力
- **方案**: 加 `status='cancelled'` 列值 (跟 'completed' 平级), `RippleStorage.cancel_cascade_run(run_id, reason)` method; endpoint `POST /api/ripples/{id}/cascade-runs/{run_id}/cancel`; CLI `lingwen.py cascade --cancel <run_id>` (新 subcommand)
- **caveat**: 真要 "中断长 BFS" 需 cooperative cancellation (cancel check in BFS loop), 但 cascade run 通常秒级完成, 0.5s 内结束, 实操只是 "mark 状态" 而非真中断. YAGNI: 0 实现 cooperative cancel, 仅 status mark
- **tests**: 5-8 new (2 storage + 3 endpoint + 2 CLI + 1 WS push)
- **estimated**: 1.5-2 hours
- **dependency**: F4 (cascade_runs 表先就位)
- **scope boundary**: 0 改 BFS 算法 (0 cooperative cancel 实现), 0 改 Phase 9.19/9.20 既有 API

### F6. Phase 9.22 — dashboard 历史 cascade run UI 回放 panel

- **承接**: Phase 9.20 cascade_runs list endpoint → 加 Vue panel
- **方案**: `CascadeRunsPanel.vue` (NEW) — show N historical runs per ripple (timestamp, depth_reached, status badge), 点击展开看 nodes/edges ECharts 图 (复用 Phase 9.16 CascadeGraph.vue)
- **tests**: 4-6 new vitest (component mount + click handler + empty state)
- **estimated**: 2 hours
- **dependency**: F4
- **scope boundary**: 0 改 Phase 9.16 CascadeGraph.vue, 仅 wrap 1 新 container panel + 1 新 endpoint

### F7. Phase 9.23 — cascade run 过滤 (by status / algorithm / depth range)

- **承接**: Phase 9.22 dashboard panel 加 filter dropdowns
- **方案**: `GET /api/ripples/{id}/cascade-runs?status=cancelled&min_depth=2&max_depth=5&algorithm=v2_weighted` query params (all additive, default None 走 Phase 9.20 path)
- **tests**: 4-5 new endpoint tests (one per filter)
- **estimated**: 1 hour
- **dependency**: F4 + F6
- **scope boundary**: 0 改 Phase 9.20 既有 endpoint signature, 仅 additive query params

## P2 其他 deferred (跨 phase 留 followup, 不紧急)

按累计 defer 次数排序 (越多次越老):

### F8. CI filter 收紧 (Phase 8.3 LOW 标) ✅ **RESOLVED 2026-06-11**

- **问题**: pytest -k 默认跑所有, 容易混入 OpenAI/MiniMax 真实 provider (env var 触发). 历史 1 次事故: 误装 openai 包后 ci 跑真实 LLM, 烧 $50
- **方案**: `pytest.ini` 加 `-k "not OpenAI and not MiniMax"`, 或 `conftest.py` 加 `--ignore` filter
- **estimated**: 30min
- **dependency**: 无 (跟其他独立)
- **resolution** (2026-06-11 brainstorming 决策): Phase 8.15 plan L1874 obsolete mark 是对的. 现场证据:
  - `tests/agent_system/test_novel_writing_real_llm.py` L23-33 `_REQUIRES_ANTHROPIC_KEY` / `_REQUIRES_OPENAI_KEY` / `_REQUIRES_MINIMAX_KEY` skipif markers (Phase 8/8.1/8.2 pattern, 默认 SKIP, opt-in 走 env var)
  - `tests/agent_system/test_e2e_workflow.py` L25-31 module-level skipif (任一 MINIMAX/OPENAI/ANTHROPIC API key)
  - 其他 test 引用 "OpenAI/MiniMax" 但走 mock provider (`_make_stub_router` / `_make_real_router` 等), 0 真 LLM 路径
  - 当前 default `pytest -q` baseline 2478 passed 0 failed, 跑时 0 真 LLM 调用 (Phase 9.24 F3 bookkeeping 验证)
- **主公决策** (2026-06-11): F8 标 resolved 不做, 未来 contributor 忘 skipif 是过程风险, lint rule 解决不了 (lint 不知道哪些是 "真" LLM test). 拿掉 P2 row, 留此 entry 作 audit trail.

### F9. DRY reset+rollback 内部 SQL (Phase 9.18 defer)

- **问题**: `RippleStorage.reset_ripple_for_test` (Phase 9.18) + `rollback_ripple` (Phase 9.13) 都做 `UPDATE reference_ripples SET status=?, applied_at=NULL`, 部分 SQL 重复
- **方案**: 抽 `_update_ripple_status_internal(conn, ripple_id, new_status, applied_at)` private helper, 2 caller 复用
- **estimated**: 1 hour (含 2 method 改 + 5-8 new test)
- **dependency**: 无

### F10. WebSocket 断线 indicator (Phase 7.x defer)

- **方案**: sidebar banner 加 ⚠️ 提示 when `useWorkflowSocket.isConnected === false`
- **tests**: 2-3 vitest (vi.mock useWorkflowSocket 返 disconnected)
- **estimated**: 1 hour
- **dependency**: 无

### F11. Tier budget alert 日志 (Phase 8.15 defer)

- **方案**: dashboard alert 列表 (sidebar 顶部), 记录超阈值 tier + 时间戳
- **estimated**: 2 hours
- **dependency**: 无

### F12. Per-tier 趋势线 (Phase 8.16 defer)

- **方案**: cost_by_day × cost_by_tier cross 维度, CostTrendChart 加 per-tier multi-line
- **estimated**: 2 hours
- **dependency**: 无

### F13. Cost cumulative 折线 (Phase 8.16 defer)

- **方案**: CostTrendChart 加 cumulative line (跟 daily line 互补)
- **estimated**: 1.5 hours
- **dependency**: F12 (共用 CostTrendChart)

### F14. data-testid convention 统一 (Phase 8.13 引入, 11 旧 specs 仍用 class selector)

- **方案**: 11 旧 vitest spec 加 `data-testid` 属性到 component (跟 Phase 8.37 unified convention 对齐)
- **estimated**: 3-4 hours (机械 11 spec 改)
- **dependency**: 无

### F15. 11 ceremonial Playwright specs 真 e2e 化 (Phase 8.30 plan, 累计 defer)

- **状态**: Phase 8.30b 已 vitest 化大部分, 剩 11 个 ceremonial Playwright (header 标 Playwright runner 未装)
- **方案**: 走 Phase 8.30b vitest 模式批量转换, 跑 component-level test @vue/test-utils + jsdom
- **estimated**: 4-5 hours
- **dependency**: 无

### F16. Phase 14 cascade BFS 续 (Phase 9.16 defer)

- **承接**: Phase 9.16 cascade weighted BFS 留 followup: max_nodes_cap=100 hardcoded, 大图 cascade (1k+ nodes) 会 truncate. 需可配置 cap
- **estimated**: 1.5 hours
- **dependency**: 无

## 决策矩阵

| Item | 价值 | 紧急度 | 工作量 | 总评 |
|------|------|--------|--------|------|
| F1 MEMORY 拆 | 低 | 🔴 高 | 0.5h | 必做, 顺路 |
| F2 typo | 0 | 🟢 低 | 1min | 跟 F1 一起 |
| F3 legacy sync | 0 | 🟡 中 | 5min | 主公决策删/sync |
| F4 9.20 持久化 | 高 | 🟡 中 | 2-3h | 主线, 主公选中 |
| F5 9.21 cancel | 中 | 🟢 低 | 1.5-2h | 跟 F4 配套 |
| F6 9.22 UI 回放 | 中 | 🟢 低 | 2h | 跟 F4 配套 |
| F7 9.23 过滤 | 低 | 🟢 低 | 1h | 跟 F6 配套 |
| F8 CI filter | 中 | 🟡 中 | 0.5h | 防事故 |
| F9 DRY SQL | 低 | 🟢 低 | 1h | refactor, 不紧急 |
| F10 WS indicator | 低 | 🟢 低 | 1h | UX 提升 |
| F11 budget alert | 中 | 🟢 低 | 2h | UX 提升 |
| F12 per-tier trend | 中 | 🟢 低 | 2h | 数据洞察 |
| F13 cumulative | 低 | 🟢 低 | 1.5h | 跟 F12 |
| F14 data-testid | 低 | 🟢 低 | 3-4h | mechanical |
| F15 Playwright vitest | 低 | 🟢 低 | 4-5h | mechanical |
| F16 BFS cap config | 低 | 🟢 低 | 1.5h | 性能 tuning |

## 推荐下一期 phase 顺序

主公决策 (按 1 个 phase = 1 个 PR 的节奏):

1. **Phase 9.20 (F4) — cascade 持久化到 DB** — 主线 next, 用户已经选 (上面 followup 排序)
2. **Phase 9.21 (F5) — cascade cancel** — 跟 F4 配套
3. **Phase 9.22 (F6) — dashboard 回放 panel** — UX 提升
4. **Phase 9.23 (F7) — cascade run 过滤** — 跟 F6 配套

或先做 bookkeeping:
1. **Phase 9.20-bookkeeping (F1+F2+F3) — MEMORY 拆 + typo + legacy** — 30min, 必做

## 完成定义 (DoD) — Roadmap 本身

- [ ] 本 doc 创建 + commit (1 commit `docs(superpowers): 2026-06-11 followup roadmap`)
- [ ] MEMORY.md L12 拆 pointer 更新 (跟 F1 一起做)
- [ ] phases-8-dashboard.md 加本 doc 链接 (closing section)
- [ ] phases.md 索引加 cross-era followup section 引用本 doc

## 后续

每期 phase 启动时, 主公从 P1 主线 4 项里选 1 个 (F4/F5/F6/F7) 或从 P2 跨 phase deferred 里选. 选完后用 brainstorming skill 走完整 design → spec → plan → implement 流程. P0 (F1/F2/F3) 建议主公下次起任意 phase 前顺手做 (30min 投资).

EOF