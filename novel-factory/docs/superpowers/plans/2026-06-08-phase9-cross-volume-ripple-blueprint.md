# Phase 9 — 跨卷涟漪 实施蓝图 (Cross-Volume Ripple Blueprint)

> **For agentic workers:** 本蓝图 = Phase 9 spec (设计) → Phase 10-14 (实施) 的 5 phase roadmap.
> Spec 在 `2026-06-08-phase9-cross-volume-ripple-design.md`. 本文档不动 spec, 只列分阶段实施计划.
> 配套 skill: superpowers:subagent-driven-development (1 phase = 1+ 原子 commit).

## Context

**Phase 9 (本文)** = 1 蓝图 + 1 spec 配套, 0 代码. 设计 4 维 (角色/伏笔/设定/plot point) × 半自动触发.

**Phase 10-14 (后续)** = 5 阶段实施, 每 phase 1 atomic commit, 跟 Phase 8.5-8.30 同模式 (TDD + subagent dispatch + review).

**Baseline (Phase 8.30 后)**:
- 测试: 2262 passed 27 skipped (Python), 20 vitest passed (3 spec 文件)
- 5 维 dashboard (cost / budget / radar / hook / chapter) 已就位
- Plot / PlotStatus / Ripple 卷内模型已就位 (Doc 2026-06-03)
- 359 章已生成, V1-V7 7 卷结构 (主公已发布 v9.10)
- 0 改 CLAUDE.md / pyproject.toml / pytest.ini

---

## 5 阶段 Roadmap

### Phase 10: Data Model + CVG 抽取 (基础)

**目标**: 1 `CrossVolumeReferenceGraph` (CVG) + `CrossVolumeRipple` (CVR) dataclass + 4 维 ReferenceNode attrs + `RippleStorage` sqlite + 历史 359 章 backfill 抽取.

**文件 (新增)**:
- `infra/cross_volume/__init__.py` (NEW, 5L)
- `infra/cross_volume/reference_graph.py` (NEW, ~180L) — ReferenceNode / ReferenceEdge / CrossVolumeReferenceGraph + by_volume / by_node index + query_impact + detect_cycle
- `infra/cross_volume/ripple.py` (NEW, ~150L) — RippleCandidate / CandidateDiff / RippleDecision / CrossVolumeRipple dataclass + status 6 态机
- `infra/cross_volume/storage.py` (NEW, ~120L) — RippleStorage 3 表 (ripple_events / ripple_decisions / reference_graph_snapshots) 复用 Phase 8.12 sqlite pattern
- `infra/cross_volume/backfill.py` (NEW, ~100L) — 1-shot LLM 扫 359 章抽取引用图 (~$0.5)

**测试 (新增 ~250L)**:
- `tests/cross_volume/test_reference_graph.py` (NEW, ~120L) — 8 tests: node 增删 / edge append-only / query_impact / detect_cycle
- `tests/cross_volume/test_ripple.py` (NEW, ~80L) — 5 tests: candidate 构造 / decision 流转 / status 6 态机
- `tests/cross_volume/test_storage.py` (NEW, ~50L) — 3 tests: save/load round-trip / snapshot fsync

**核心设计点**:
- CVG 是 **append-only**, 不重建 (历史 359 章 1 次性 backfill 写死)
- node_id 格式 `{dim}:{slug}`, slug = hash(title+birth_chapter) 6-char hex (防 rename 漂移)
- 索引 by_volume / by_node lazy build (避免冷启动慢)
- ripple.db 跟 cost_tracker.db / workflow.db 同目录 `infra/.state/` (gitignored)
- backfill LLM 1 call / 50 章 batch (359 章 / 50 = 8 calls, ~$0.5 一次性)

**验证 (DoD)**:
- [ ] 3 文件 + 3 test 文件 created
- [ ] 16 tests passed (8 + 5 + 3)
- [ ] backfill 359 章 → 引用图 ~500-800 节点 (4 维), ~3000-5000 edges
- [ ] sqlite ripple.db 持久化 + 0 改 cost_tracker.db
- [ ] ruff 0
- [ ] 1 commit

**风险**:
- LLM backfill 失败 → retry 3 次, 仍失败标 partial (后续可重跑)
- 引用图太大 → 按 vol 切分存储 (1 vol 1 file, lazy merge)
- backfill 成本超预算 → 限 batch 10 章 (LLM 36 calls, ~$2 兜底)

---

### Phase 11: 4 维 LLM Prompt + Scanner (识别层)

**目标**: 1 scanner.py (LLM 扫 V_N 找 trigger events) + 4 维 prompt 模板 (character / foreshadow / setting / plot_point) + diff gen (每个 impact edge 1 candidate diff).

**文件 (新增)**:
- `infra/cross_volume/scanner.py` (NEW, ~140L) — scan_volume_for_ripple_triggers (1 LLM call) + query_impact_for_trigger (graph query) + generate_diffs (4 LLM calls, 1 / dim)
- `infra/cross_volume/prompts/__init__.py` (NEW, 5L)
- `infra/cross_volume/prompts/character_ripple.py` (NEW, ~60L) — CHARACTER_RIPPLE_PROMPT template + JSON schema
- `infra/cross_volume/prompts/foreshadow_ripple.py` (NEW, ~60L)
- `infra/cross_volume/prompts/setting_ripple.py` (NEW, ~60L)
- `infra/cross_volume/prompts/plot_point_ripple.py` (NEW, ~60L)
- `infra/cross_volume/pydantic_schemas.py` (NEW, ~80L) — 4 维 event / impact / diff 强校验 schema (Pydantic v2)

**测试 (新增 ~250L)**:
- `tests/cross_volume/test_scanner.py` (NEW, ~120L) — 6 tests: 扫 1 vol mock LLM 返 trigger / 4 维各 1 test / confidence 过滤 / empty case
- `tests/cross_volume/test_prompts.py` (NEW, ~80L) — 4 tests: 1 / 维 prompt 模板渲染 (mock LLM 验证 JSON schema)
- `tests/cross_volume/test_pydantic_schemas.py` (NEW, ~50L) — 4 tests: 1 / 维 schema 校验 (合法 / 非法 / 缺字段 / retry 1 次)

**核心设计点**:
- LLM 调复用 Phase 7 polisher LLM 路径 (ClaudeProvider + ModelRouter), 0 引入新 client
- 4 维 prompt 独立文件 (跟 Phase 7 polisher_prompts.py 同 pattern, 易维护)
- Pydantic v2 强校验 (跟 Phase 8.5 CostTracker Pydantic schema 同模式)
- retry 1 次 (LLM 返非法 JSON), 失败 → candidate confidence = 0.0 (走 reject path)
- confidence < 0.6 过滤 (不浪费 author 注意力)
- scanner 1 call / vol (50 章 batch) → 节省成本, 跟 backfill 同模式

**验证 (DoD)**:
- [ ] 7 文件 + 3 test 文件 created
- [ ] 14 tests passed (6 + 4 + 4)
- [ ] 4 维 prompt 各自 1 sample 跑通 (mock LLM)
- [ ] scanner 端到端 mock: 输入 1 vol + 引用图 → 返 candidates 列表
- [ ] Pydantic schema 100% 校验 (4 维)
- [ ] 0 改 Phase 7 polisher / Phase 8 cost tracker
- [ ] ruff 0
- [ ] 1 commit

**风险**:
- LLM 4 维 prompt 命中率低 → Phase 11 不强求, 留 Phase 12 UI feedback 调 prompt
- 4 维 prompt 重复 (e.g. character + plot_point 偶有重叠) → 通过 confidence 让 author 判重
- scanner 跑历史 V1-V7 → 5 vol × 1 call = 5 calls, ~$0.3 (一次性, 用于校验)

---

### Phase 12: Review UI + 半自动 Endpoint (交互层)

**目标**: 1 Vue 3 review page (impact 列表 + diff preview + 风险评分 + 批量 confirm) + 3 FastAPI endpoint (scan / review / apply) + apply 流程 (snapshot → 改文件 → mark applied).

**文件 (新增)**:
- `dashboard/protocols.py` (MODIFY, +50L) — 加 3 endpoint handler: `POST /api/cross-volume/ripples/scan` / `GET /api/cross-volume/ripples` / `POST /api/cross-volume/ripples/{id}/apply`
- `dashboard/frontend/src/pages/CrossVolumeRipplePage.vue` (NEW, ~250L) — review UI (Vue 3 + Vite, 跟 Phase 7.6 ScoreRadarPage 同 pattern)
- `dashboard/frontend/src/components/RippleImpactRow.vue` (NEW, ~120L) — 1 impact row (original vs proposed + rationale + risk + confirm/reject/edit 按钮)
- `dashboard/frontend/src/components/RippleDiffPreview.vue` (NEW, ~80L) — diff 高亮 (新增绿 / 删除红, 简单 <pre> 渲染, 不引入 diff lib)
- `dashboard/frontend/src/composables/useCrossVolumeRipple.js` (NEW, ~100L) — module-level singleton, 跟 useWorkflowSocket.js 同 pattern
- `dashboard/router.js` (MODIFY, +5L) — 加 /cross-volume-ripple route

**文件 (新增 backend)**:
- `infra/cross_volume/api.py` (NEW, ~150L) — FastAPI router 3 endpoint 实施 (scan / list / apply), 复用 Phase 8 cost_tracker endpoint pattern

**测试 (新增 ~300L)**:
- `tests/cross_volume/test_api.py` (NEW, ~150L) — 8 tests: scan mock 返 200 / list 返 ripple / apply mock 改 1 file / 4xx 错 (vol not found / ripple already applied)
- `tests/dashboard/test_cross_volume_ripple_page.spec.ts` (NEW, ~80L) — 4 tests: render impact list / click confirm 调 apply / diff preview 高亮 / risk=high 默认折叠
- `tests/dashboard/test_ripple_impact_row.spec.ts` (NEW, ~70L) — 3 tests: confirm emit / reject emit / edit mode toggle

**核心设计点**:
- Apply 前自动 snapshot (写到 `infra/.state/ripple_snapshots/{ripple_id}.json`, fsync)
- Apply 改前卷段落 = 直接写 `正文/第NNNN章-*.md` (git 控, author 误改可 git revert)
- Review UI 跟 Phase 7.6 ScoreRadarPage 同模式 (Vue 3 + Vite + ECharts 不用, 简单表格)
- 风险评分 visual: low=绿 / medium=黄 / high=红, 跟 Phase 8.28 soft warning 3 态同色板
- Default 1 candidate 展开 1 次, 不一次全开 (避免 author 注意力散)
- Apply 前 modal 再次确认: "将修改 12 处前卷段落, 不可撤销 (除 rollback)"

**验证 (DoD)**:
- [ ] 5 backend 文件 (含 1 protocol modify) + 3 test 文件 created
- [ ] 15 tests passed (8 + 4 + 3)
- [ ] 3 endpoint 跑通 (mock LLM / mock filesystem)
- [ ] Review UI 端到端: 1 ripple mock 5 impacts → author 确认 3 个 → apply 3 改文件 + snapshot 落盘
- [ ] 0 改 Phase 8 dashboard (5 维 cost/budget/radar/hook/chapter)
- [ ] ruff 0
- [ ] 1 commit

**风险**:
- 改前卷 359 章 markdown 文件 → 备份 + 写 fsync, 防半路崩溃
- Review UI 慢 (100+ impacts) → lazy render + pagination
- 多 author 冲突 → 1 author 模型, 不实现 (后续)

---

### Phase 13: Rollback + Audit Log (安全层)

**目标**: 1 rollback 机制 (snapshot 1-click revert) + 1 audit log (所有 ripple 决策留痕) + fsync 保护 (snapshot / 改文件 / DB 写均 fsync).

**文件 (新增)**:
- `infra/cross_volume/rollback.py` (NEW, ~120L) — RippleRollback.snapshot_before_apply / rollback / list_recent_rollbacks
- `infra/cross_volume/audit.py` (NEW, ~80L) — AuditLogger 写 JSON lines to `infra/.state/ripple_audit.log` (gitignored), 每次 decision / apply / rollback 1 行
- `infra/cross_volume/fsync.py` (NEW, ~40L) — fsync helper, 复用 Phase 8.12 cost_tracker 模式 (os.fsync + DB 事务)

**测试 (新增 ~200L)**:
- `tests/cross_volume/test_rollback.py` (NEW, ~120L) — 5 tests: snapshot 写盘 / rollback 还原 / 不存在 snapshot 报错 / 多次 rollback 不叠加 / audit log 写入
- `tests/cross_volume/test_audit.py` (NEW, ~50L) — 3 tests: decision log 格式 / apply log 含 snapshot_id / rollback log 含 reason
- `tests/cross_volume/test_fsync.py` (NEW, ~30L) — 2 tests: 文件 fsync / sqlite 事务 fsync

**核心设计点**:
- Snapshot 存独立 JSON file (不混 DB, 便于 git 跟踪 — **不 commit**, gitignored)
- Rollback = 写回 original_text 到指定 (vol, ch, paragraph_idx)
- Audit log JSON lines 格式, 后续可重放 / 统计
- Fsync 3 处: snapshot file / 前卷 markdown file / ripple.db transaction
- 0 改 Phase 8.12 CostTracker fsync 模式 (复用相同 pattern)

**验证 (DoD)**:
- [ ] 3 文件 + 3 test 文件 created
- [ ] 10 tests passed (5 + 3 + 2)
- [ ] Snapshot 写 fsync 通过 (mock crash 模拟, 读回验证)
- [ ] Rollback 端到端: apply 5 改 → rollback → 文件还原
- [ ] Audit log JSON lines 格式校验
- [ ] 0 改 Phase 8.12 CostTracker
- [ ] ruff 0
- [ ] 1 commit

**风险**:
- Snapshot 文件丢失 (disk fail) → RAID / backup (out of scope, 留 ops 团队)
- Rollback 误操作 (rollback 错了) → 留 audit trail + UI "view audit" button
- Fsync 性能 → 5ms / 写, 接受 (1 apply 5 改 = 25ms, 无感)

---

### Phase 14: 性能优化 + 级联涟漪 (高级)

**目标**: 1 lazy graph build (大项目 100+ 卷不卡) + 1 cache layer (4 维 query 缓存) + 1 级联涟漪 detect (改 V1 触发 V2 新涟漪).

**文件 (新增)**:
- `infra/cross_volume/cache.py` (NEW, ~80L) — query_impact cache (LRU, 1 min TTL), 跟 Phase 8 cost_tracker cache 同 pattern
- `infra/cross_volume/cascade.py` (NEW, ~120L) — CascadeDetector detect 改 V1 → 触发 V2 新涟漪候选 (1 LLM call 验证)
- `infra/cross_volume/perf.py` (NEW, ~60L) — lazy graph build helper (按需加载 vol)

**测试 (新增 ~200L)**:
- `tests/cross_volume/test_cache.py` (NEW, ~80L) — 4 tests: LRU evict / TTL expire / cache hit 加速 / cache miss 走 query
- `tests/cross_volume/test_cascade.py` (NEW, ~80L) — 4 tests: detect 1 跳 / detect 2 跳 / cycle detect / 限 3 跳 (防死循环)
- `tests/cross_volume/test_perf.py` (NEW, ~40L) — 2 tests: lazy vol 加载 / 大项目 100 vol 不爆内存

**核心设计点**:
- Cache LRU 100 entries / 1 min TTL (跟 Phase 8 cost tracker 同)
- Cascade 限 3 跳 (防 LLM 反复触发, 4+ 跳 author 手动处理)
- Lazy graph 按 vol 加载 (大项目 100 vol + 1000 章, 全 load 4 GB, lazy 100 MB)
- 0 改 Phase 8.12 cost_tracker cache 模式 (复用)

**验证 (DoD)**:
- [ ] 3 文件 + 3 test 文件 created
- [ ] 10 tests passed (4 + 4 + 2)
- [ ] Cache hit / miss 性能差 ≥ 10x (大项目)
- [ ] Cascade 1 跳 + 2 跳 + cycle + 限 3 跳端到端
- [ ] 0 改 Phase 8.12
- [ ] ruff 0
- [ ] 1 commit

**风险**:
- Cache 失效 (引用图更新后 stale) → invalidate on save_graph
- Cascade 误报 (LLM 假阳性) → 标 low confidence, author 逐条 confirm (跟主涟漪同)
- Lazy load IO 慢 → 启动时 warm-up 1 vol

---

## 实施顺序 + 依赖图

```
Phase 9 (本文)
   ↓ spec + 蓝图 (设计)
Phase 10 (Data Model + CVG)
   ↓ 数据基座
Phase 11 (Scanner + Prompts)
   ↓ 识别层
Phase 12 (Review UI + API)
   ↓ 交互层
Phase 13 (Rollback + Audit)
   ↓ 安全层
Phase 14 (Cache + Cascade)
   ↓ 性能优化
```

**关键依赖**:
- Phase 11 依赖 Phase 10 (scanner 调 storage)
- Phase 12 依赖 Phase 10 + 11 (UI 调 scanner + 写 storage)
- Phase 13 依赖 Phase 12 (rollback 在 apply 后才有意义)
- Phase 14 依赖 Phase 10-13 (cache / cascade 优化所有层)

**可并行点**:
- Phase 10 + 11 后端 + Phase 12 前端 UI 可并行 (跨 frontend/backend), 但 frontend 需等 backend API shape 稳定
- Phase 14 cache 可跟 Phase 13 并行 (独立模块)

---

## 关键文件汇总 (5 phase 总览)

| 类别 | Phase 10 | Phase 11 | Phase 12 | Phase 13 | Phase 14 |
|------|----------|----------|----------|----------|----------|
| 新建 backend module | 5 文件 | 7 文件 | 1 文件 (api.py) | 3 文件 | 3 文件 |
| 新建 tests | 3 文件 | 3 文件 | 3 文件 | 3 文件 | 3 文件 |
| 改 dashboard | 0 | 0 | 5 文件 (前端 + protocol) | 0 | 0 |
| 改 infra/ | 0 (新) | 0 (新) | 0 (新) | 0 (新) | 0 (新) |
| 改 Phase 7/8 | 0 | 0 | 0 | 0 | 0 |
| 估计代码量 | ~550L | ~470L | ~720L | ~240L | ~260L |
| 估计测试量 | ~250L | ~250L | ~300L | ~200L | ~200L |
| LLM 成本 (1 次性) | $0.5 (backfill) | $0.3 (scanner 校验) | $0 | $0 | $0 |
| commit 数 | 1 | 1 | 1 | 1 | 1 |

**5 phase 累计**: 19 新建 backend + 3 改 dashboard + 15 新建 tests + 5 commits. 0 改 Phase 7/8 existing code.

---

## 跟主公协作节点 (per phase AskUserQuestion)

- **Phase 10 启动前**: 1 question (backfill 跑不跑, 影响 ~$0.5 成本 + 1-2h LLM 时间)
- **Phase 11 启动前**: 1 question (4 维 prompt 优先级 — 角色先行 / 伏笔先行 / 设定先行 / plot point 先行)
- **Phase 12 启动前**: 1 question (review UI 风格 — 表格 / 卡片 / 双栏 diff)
- **Phase 13 启动前**: 1 question (rollback UI — 单按钮 / 历史栈 / 审计详情)
- **Phase 14 启动前**: 1 question (cascade 跳数限制 — 2 / 3 / 5 / author 手动)

---

## 风险汇总 (5 phase)

| Phase | 风险 | 缓解 |
|-------|------|------|
| 10 | backfill LLM 失败 | retry 3 次 + partial 标 |
| 10 | 引用图太大 | lazy load by_volume |
| 11 | LLM 4 维 prompt 命中率低 | Phase 12 UI feedback 调 prompt |
| 12 | 改前卷 markdown 文件 | 备份 + fsync |
| 12 | Review UI 慢 | lazy render + pagination |
| 13 | Snapshot 文件丢失 | RAID / backup (out of scope) |
| 13 | Rollback 误操作 | audit trail + view audit button |
| 14 | Cache stale | invalidate on save_graph |
| 14 | Cascade 误报 | low confidence + author confirm |
| 14 | Lazy load IO 慢 | warm-up 1 vol 启动 |

---

## Verification (per phase)

- [ ] Phase 10: 16 tests passed + ruff 0 + 1 commit + backfill 359 章完成
- [ ] Phase 11: 14 tests passed + ruff 0 + 1 commit + 4 维 prompt 各自 1 sample 跑通
- [ ] Phase 12: 15 tests passed + ruff 0 + 1 commit + 3 endpoint 端到端 + Review UI 跑通
- [ ] Phase 13: 10 tests passed + ruff 0 + 1 commit + snapshot fsync + rollback 端到端
- [ ] Phase 14: 10 tests passed + ruff 0 + 1 commit + cache 性能 ≥ 10x + cascade 限 3 跳

**累计 5 phase**: 65 tests passed (16+14+15+10+10), 5 commits, 0 改 Phase 7/8.

---

## 后续 (Phase 15+)

- **Phase 15**: MEMORY.md 拆 30+ entries 到 phases.md topic (累计 8.30 + 9 + 10-14 必超 200, 必拆)
- **Phase 16**: 级联涟漪可视化 (跨卷 impact graph 渲染, Vue 3 + ECharts)
- **Phase 17**: 跨项目涟漪 (留 out of scope, 1 项目边界 — 主公确认永不实施)
- **Phase 18**: 多 author 协作 (留 out of scope, 当前 1 author 模型)

---

## DoD (本蓝图)

- [x] **5 阶段 roadmap**: Phase 10-14 完整任务分解
- [x] **每 phase 文件 map**: 新建 + 改 + 测试明确
- [x] **每 phase 验证**: DoD + 测试数 + ruff + commit
- [x] **依赖图**: 5 phase 顺序 + 可并行点
- [x] **LLM 成本估算**: $0.5 + $0.3 一次性, 可忽略
- [x] **主公协作节点**: 5 phase 各 1 AskUserQuestion
- [x] **风险表**: 10 项, 各自 mitigation
- [x] **0 改 Phase 7/8**: 仅 1 改 Phase 8 protocols.py (Phase 12 实施)
- [x] **0 改 WorldSnapshot schema**: 扩 nodes + edges 字段, 0 改 active_subplots
- [x] **0 spec 行号漂移**: 0 引用 8.5-8.30 spec 的 :NNN
