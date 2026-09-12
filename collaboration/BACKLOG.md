# 待办事项列表

> **最后更新**: 2026-09-12 (Phase 58 complete, v54.3 ready for ff-merge)
> **更新者**: 协调者（Phase 58 cross_volume 16 failures fix 闭环：220/220 GREEN；4 atomic commits; v54.2 → v54.3）
> **优先级**: P0 > P1 > P2 > P3
> **事实来源**: 本仓库当前版本在 `CLAUDE.md` v54.3；并行开发入口见根 `COORDINATION.md`

---

## 如何认领任务

1. 从列表中选择一个任务
2. 检查「状态」是 📋 待开始
3. 将「状态」改为 🔄 进行中，填入「认领人」
4. 大型任务在 `ACTIVE_TASK.md` 中添加详情
5. 开始工作

> 小型任务直接在 BACKLOG 中跟踪；大型任务移入 `ACTIVE_TASK.md`

---

## P0 - 阻塞项（无）

| ID | 标题 | 描述 | 认领人 | 状态 | 创建日期 |
|----|------|------|--------|------|----------|
| - | - | 当前无 P0 阻塞项 | - | - | - |

---

## P1 - 立即处理（追平双会话遗留）

| ID | 标题 | 描述 | 认领人 | 状态 | 创建日期 |
|----|------|------|--------|------|----------|
| P1-SHIM | batch-templates 契约 shim | 后端已 codegen `lingwen_shared` 的 batch-templates DTO（`StudioBatchTemplate`/`Create|Update`/`ListResponse`）但未更新 `apps/dashboard-contracts` 的 *DTO shim → 前端暂消费不到新类型。前端补 shim 后 Pilot 方可落地模板 UI | 前端 A（自服务完成） | ✅ 完成 | 2026-09-02 |

---

## P2 - Phase 26+ 候选（继承 carryover，按价值排序）

| ID | 标题 | 描述 | 认领人 | 状态 | 创建日期 |
|----|------|------|--------|------|----------|
| P2-INSIGHT | Pilot + Insight 看板集成 | 让 batch 进度汇入主看板 | 前端 A（自服务完成） | ✅ 完成 | 2026-09-02 |
| P2-DRAWER | per-chapter preview drawer | PilotLivePanel 章节预览抽屉 | 前端 A（自服务完成） | ✅ 完成 | 2026-09-02 |
| P2-QUEUE | batch priority queue | 生产排队，多任务有序。**后端 B 自服务列表第一个** | 后端 B（自服务）+ 前端 A（`PilotQueuePanel` 排队面板） | ✅ 完成 | 2026-09-02 |
| P2-RESTART | auto-restart on failure | 失败自动重启。**后端 B 自服务列表第二个** | 后端 B（自服务） | ✅ 完成 | 2026-09-02 |
| P2-MULTI | multi-LLM 并发批次 | 并行吞吐能力（较大，后端 B 自服务列表收尾项） | 后端 B（自服务完成） | ✅ 完成 | 2026-09-02 |
| P2-DTOMIGR | usePilotBatch DTO migration | 迁移至 `@/api/studio` re-export（技术债） | 会话-A（自服务完成） | ✅ 完成 | 2026-09-02 |
| P2-REG | Phase 114 prod preview regression | 2026-09-03 实测：cytoscape-fcose 历史根因已随图库迁移 vis-network 消失；真实回归为 v16.2.8 迁移遗留 3 处陈旧引用（useCreatorAdvanceBatch 旧名 generateCreatorVolumeSummary + api/index.js 桶内陈旧别名 + 补缺失 fetchCreatorOverview） | 协调者（本会话） | ✅ 修复 `80790b76` | 2026-09-03 |
| P2-WFSTATE | _last_* 散点 → WorkflowState dataclass | mc_workflow.py 5 个 self._last_* (不同默认值) 易半初始化。整合 dataclass 更类型安全、易测 | 后端 B（自服务） | ✅ 完成（Phase 26 commit `ee3396ae`） | 2026-09-03 |
| ~~P2-WFRUNNER~~ | ✅ Phase 27 DONE (2026-09-04) — see handoff | ~~run_workflow orchestration 90+ 行偏多。拆 service 后 run_workflow 仅做编排、helper 收口~~ | 后端 B（自服务） | ✅ Phase 27 完成（commit `9b57d16a` 待 ff-merge） | 2026-09-04 |
| ~~P2-RESUME-VERIFY~~ | ✅ Phase 28 DONE (2026-09-04) — see handoff | ~~start_nodes=None 时 resume_workflow 重跑 E2E 验证。代码 review 列为 important。scheduler 对已完成节点是否幂等无测试覆盖~~ | 后端 B（自服务） | ✅ Phase 28 完成（7 commits 待 ff-merge） | 2026-09-04 |
| P2-MC-WRITING | 84 pre-existing cascade failures 根因 | tests/got + tests/agent_system 共 84 failing，pre-existing（推测 mc_writing.py 类似 gutted）。需独立 phase | 后端 B（自服务） | ✅ Phase 29 完成（17 commits ff-merge `b1b748ad`，84→14 failed (-70)，1 prod 改动 `mc_editing.py:202`，11 测试文件调整） | 2026-09-04 |
| ~~P2-ARCHDEBT (剩余)~~ | ~~infra.got.* → packages/lingwen-got/ 迁移 + infra.world_model split~~ | ~~Phase 33+ 候选剩余：infra.got.* 迁 packages/lingwen-got/ + world_model/__init__ split (5 consumer migration)~~ | 后端 B（自服务） | ✅ **Phase 33+34+35 全部完成**（v33.0 LINGWEN-GOT 11 commits + v34.0 WORLD-MODEL-PACKAGE 10 commits；P2-ARCHDEBT 全部 CLOSED） | 2026-09-08 |
| **P3-ARCHDEBT** (NEW) | infra.{paths, project_config, logging_config, errors, studio_registry} → packages/ 迁移 | 5 个 infra 跨切关注点模块：paths (path resolver) / project_config (settings) / logging_config (logging setup) / errors (error base classes) / studio_registry (FastAPI app registry)。每个需独立 phase 评估 consumer 数 + 迁移策略；预计 multi-week。建议从依赖最少的 `errors` 开始（基础类被广泛 import 但消费者数可控）。**Phase 36 errors pilot 已闭环**（infra/errors → packages/lingwen-errors/; 4 packages + 8 intra-infra migrated; invariant #51 NEW; 6 phase36 guards GREEN）。**Phase 37 paths 已闭环**（86 consumers；invariant #52 NEW；6 phase37 guards GREEN）。**Phase 38 project_config 已闭环**（26 consumers；7 function-body via `\1` sed；1 fixup；invariant #53 NEW；7 atomic commits）。**Phase 39 logging_config 已闭环**（7 consumers + 1 wildcard；LEAF package；invariant #54 NEW；6 atomic commits）。**Phase 40a studio_registry 5/5a 已闭环**（50 consumers：47 production + 1 wildcard；NOT-LEAF 3-dep package；shim-not-delete pattern；C1.5 `factory_root()` fixup；invariant #55 NEW；8 atomic commits）。**Phase 40b studio_registry 5/5b 待启动**（~33 tests/ edits + DELETE shim + DELETE wildcard；4-5 atomic commits）。 | 后端 B（自服务） | 🔄 **Phase 36+37+38+39+40a 全部完成（P3-ARCHDEBT 5/5a CLOSED）**；Phase 40b 继续 tests/ migration + shim delete | 2026-09-09 |
| **P2-30-FAILURES** | ~~Phase 29 剩余 14 failed 一次性清零~~ | ~~5 类根因：① 7 stub `_state` 注入（一行修复）② 1 `_collect_decision_specs_from_graph` re-export 或 test 迁移 ③ 2 `_impl_audit_chapter` 韧性契约（真 prod 改动，需 design 确认边界）④ 2 `CostTrackerDB._connect()` API 迁移 ⑤ 2 env-var tests 重写 → `make_master_with_router()`~~ | 后端 B（自服务） | ✅ Phase 30 完成（9 commits ff-merge `38b854e7`，14→0 failed (-14)，2 prod 改动 mc_writing.py + cost_persistence.py + 5 test 文件调整） | 2026-09-07 |
| **P2-ARCHDEBT-MINI** | ~~P2-ARCHDEBT 子集 2/4 清理~~ | ~~**Sub-task A**：chapter_golden_path 反向 import 修复（迁 apps/studio_api/tests/golden_path_smoke.py）；**Sub-task B**：4 薄代理 → OrchestratorProxyMixin（mc_orchestrator_proxy.py new + MasterController MRO）；**12 文件 doc 同步** 修 stale "5 薄代理" → "4 薄代理"~~ | 后端 B（自服务） | ✅ Phase 31 完成（6 commits ff-merge `4dbe8939`，sub-task A -87/+106 行 + sub-task B mc_workflow 119→99 行 + 5 refactor-guard tests + 12 文件 doc 同步） | 2026-09-07 |
| **P2-SHIM-CLEANUP** | ~~P2-ARCHDEBT PHASE-COMPAT shim 删除 3/4~~ | ~~**Sub-task 1**：`infra/subplot/data_structures.py` (32 行, 0 消费者) 删除。**Sub-task 2**：`infra/world_model/data_structures.py` (69 行, 0 消费者) 删除。**Sub-task 3**：`packages/lingwen-core/src/lingwen_core/agents/master_controller.py` (11 行) 删除 + 6 test consumers (12 sites) 迁移到 canonical `lingwen_pipeline.master_controller`。**+1 fixup commit** 修 5 处漏检的 relative imports (infra/subplot/__init__.py:19 / infra/world_model/{__init__.py:60,key_point_graph.py:24,snapshot_store.py:24} / packages/lingwen-core/src/lingwen_core/agents/got_bridge.py:32)。**+10 regression guard tests** in tests/test_phase32_shim_cleanup.py。**N.14 lesson 1 (6th time)**：literal-text grep misses relative imports (`from .X`, `from ..X`); future shim-deletion phases must include `grep -rn "from \\.X\\b"` in audit~~ | 后端 B（自服务） | ✅ Phase 32 完成（8 commits ff-merge `9980e393`, -112 行 shim + 5 fixup files + 10 guard tests + 5 doc flips; invariant #48 NEW） | 2026-09-07 |

> **后端 B 自服务顺序**：P2-QUEUE → P2-RESTART → P2-MULTI。每任务：rebase origin/master → 实现 → 完整 `pytest` + `ruff check` + `ruff format --check` 全绿 → 自 ff-merge 到 master → 认领下一个。**common 前置**：worktree 内跑测试/codegen 需 `export PYTHONPATH=$PWD/packages/lingwen-shared/src:$PYTHONPATH`（见 COORDINATION.md §6.5）。

---

## 已完成（近期）

| 版本/阶段 | 内容 | 状态 |
|------|------|------|
| v25.9 (Phase 25.9) | human_review 流水线修复：mc_workflow.py 还原（git history 5c4259e5）+ 新 GoTScheduler API 对齐 + 4 dashboard smoke 解 skip + cascade +15 fixed / 0 new。master `0a6f4346` 4 commit | ✅ |
| v25.1 (Phase 25.1) | 双会话并行开发合流：Track A event_types 过滤开关 + Track B batch templates，0 冲突 ff-merge 至 `a1826b33` | ✅ |
| v25.0 (Phase 25) | SSE batch 增强 Filter/Replay/Auth（服务端 event_types 过滤 + 连接重放 + 读取门控） | ✅ |
| v24.0 (Phase 24) | SSE 实时 batch 进度（`studio_batch_streamer.py` + `/events` 路由）替代 3s 轮询 | ✅ |
| v23.0 (Phase 23) | Pilot 页（`PilotPage.vue` + 5 组件 + `usePilotBatch`） | ✅ |
| v22.0 (Phase 22) | test-env + ruff format 清理 | ✅ |
| v21.0 (Phase 21) | shim cleanup（删 `infra/consistency/` + `infra/agent_system/`） | ✅ |

> 完整历史版本链见 `CLAUDE.md` 版本块（v21.0 → v25.1）。

---

## 需求池（待评估）

| ID | 标题 | 来源 | 描述 | 优先级建议 |
|----|------|------|------|------------|
| REQ-001 | 创作者模式增强 | 用户 | 陪伴/推进模式功能扩展（Track A 已交付 A/B/C/D/E 全部切片：`useCreatorMode` 单一来源、陪伴「今日下一步」、推进「批改节奏带」、写栏「模式引导条」、「差异收尾」清单） | 完成 |
| REQ-002 | 多模态支持 | 用户 | 封面/插图生成 | P3 |
| REQ-003 | 移动端适配 | 用户 | Dashboard 移动端体验优化。✅ `34f0b0f2`：接通锁层移动抽屉（汉堡+遮罩+Esc/导航收起），旧 style.css 选择器失配修复；核心页经审计已由 flex-wrap + 既有 media query 自然适配 | 完成 |
| REQ-004 | 团队协作功能 | 用户 | 多用户协作编辑 | P4 |

---

## 素材生成任务（Trae Worker）

| ID | 标题 | 描述 | 认领人 | 状态 | 创建日期 |
|----|------|------|--------|------|----------|
| ASSET-001~011 | sidebar SVG 图标（11 模块 + 1 Pilot follow-up） | 侧栏 emoji → Phosphor 双色 SVG；Vue SFC 扁平；`--lingwen-icon-accent` CSS var 主题；nav 配置 `.map()` 集成 | 协调者（自服务） | ✅ 完成 | 2026-09-10 |

> 风格要求：现代科技/动漫风格、暗色底、霓虹紫蓝、渐变发光。

---

## 标签索引

| 标签 | 说明 |
|------|------|
| 📋 | 待开始 |
| 🔄 | 进行中 |
| ⏳ | 待验证/待规划 |
| ✅ | 已完成 |
| 🔴 | 阻塞 |
| ❌ | 已取消 |

---

## 新增任务模板

```markdown
| Px-XXX | 任务标题 | 简短描述 | 待认领 | 📋 待开始 | YYYY-MM-DD |
```

---

## 最近变更

| 时间 | 更新者 | 变更 |
|------|--------|------|
| 2026-09-12 | 协调者 | **v54.3 Phase 58 cross_volume 16 failures fix 闭环**：220/220 cross_volume tests GREEN (was 204/220)。4 atomic commits on `phase-57-p3-archdebt-reading-power` = C1 fix(cli) lazy-init Command base.py `5d4d0d30` / C2 fix(cross-volume) test paths to apps.studio_api.X `d87a5a08` / C3 test(phase-58) 5 guards + v54.2→v54.3 `d90e29d7` / C4 docs。**2 root causes collapsed 16 fails**：(RC2) `Command.__init__` eagerly validated `ProjectPaths.get()` → 12 tests broke on construction → fix: lazy @property pattern in base.py (32 + / 4 -); (RC1) tests used legacy `dashboard.X` import paths (Vue frontend, never Python) → 4 tests patched wrong module → fix: update 3 test files to canonical `apps.studio_api.X`. **Validation**: 220/220 GREEN from 3 cwds (repo root / package dir / tests dir; Phase 56b2 lesson); 5/5 phase58 guards GREEN (G1 no eager ProjectPaths.get() / G2 no eager project_max_chapter / G3 no dashboard.X in cross_volume tests / G4 220/220 / G5 lazy construction succeeds); 158/158 phase5x preserved; 163/163 phase5x+58 cumulative. **Lessons**：(1) handoff hypotheses overcount root causes — 5 RCs in handoff §146 collapsed to 2 via `pytest -xvs`; (2) `assert 0 == 1` where `len([]) == 0` is signature of monkeypatch path mismatch; (3) eager construction with side effects is a test smell — "construction should be side-effect-free" applies to CLI base classes; (4) 1 production code edit (base.py) + 3 test file edits — minimal blast radius. **Carryover CLOSED**: Phase 56c §146 16 carryover failures → 0. **Next candidates**: Phase 53c infra/tools/ residual audit OR product brainstorm (Write Workspace / World / Reading Power). 详见 `docs/superpowers/handoffs/2026-09-12-phase-58-cross-volume-failures-handoff.md` |
| 2026-09-09 | 协调者 | **v39.0 P3-ARCHDEBT (studio_registry) 5/5a 闭环**：P3-ARCHDEBT 5/5a 完成。8 commits on phase-40-p3-archdebt-studio-registry (C0 spec+plan / C1 scaffold / C1.5 factory_root() fixup / C2a intra-infra 6 sites / C2b bulk 41 sites: 17 apps + 18 packages + 5 apps test patches + 1 doc / C3 shim-not-delete (infra/studio_registry.py → 1-line shim) / C4 invariant #55 NEW + v38.0→v39.0 / C5 11 phase40a guards + Phase 38 guard fixup + handoff) ff-merge。infra/studio_registry.py (1 module, 422 lines, 18 public symbols: 1 frozen dataclass StudioProject + 17 public funcs) → packages/lingwen-studio-registry/ (5 sub-modules: models + discovery + state + summary + reports, 491 lines total)。47 production edits migrated; 0 function-body import misses; 0 relative imports; 0 filesystem path literals; 1 wildcard infra/studio/__init__.py:2 paired with C3 shim approach。**NOT-LEAF package** — 3 workspace deps: lingwen-paths + lingwen-project-config + lingwen-core (first non-LEAF P3-ARCHDEBT package)。**CRITICAL C1.5 fixup**: factory_root() path-relative formula broke after file relocation (used env var + parents[4] instead)。**Validation gates**: 11/11 phase40a guards GREEN + 7/7 phase38 preserved (after C5 fixup: test_canonical_symbols_migrated swapped infra/studio_registry.py → infra/project_characters.py as intra-infra representative) + 6/6 phase37 + 6/6 phase36 + 39 phase32-35 + 69 lingwen-core+pipeline baselines + 73 lingwen-creator (isolated) + ruff clean (new files)。9 pre-existing ruff I001 unchanged。**Carryover**: P3-ARCHDEBT 5/5b (~33 tests/ root edits + DELETE shim + DELETE wildcard + +33 regression guards; 4-5 atomic commits) → Phase 40b |
| 2026-09-08 | 协调者 | v35.0 P3-ARCHDEBT (errors pilot) 闭环：P3-ARCHDEBT 1/5 完成。6 commits on phase-36-p3-archdebt-errors (C0 spec / C0b plan / C1 scaffold / C2 14-consumer migration / C3 infra/errors.py deletion / C4 invariant #51 NEW + version bump / C5 6 phase36 guards + doc sync) ff-merge。infra/errors.py (1 module, 380 lines, 23 public symbols) → packages/lingwen-errors/。14 consumer migration (4 packages: lingwen-quality/world-model/pipeline/llm + 8 intra-infra)。Validation: 6 phase36 guards GREEN + 7 baselines preserved (lingwen-core 68/68 + lingwen-world-model 201/201 + lingwen-got 208/208 + studio_api 82/82 + lingwen-quality + lingwen-pipeline + lingwen-llm) + ruff clean + grep audit 0 hits (infra.errors.* 引用清零)。C5 T4 follow-up fixes: architecture.yml I051 scope test name `test_infra_errors_module_deleted` → `test_infra_errors_deleted` + CLAUDE.md v35.0 entry package list (6 wrong → 4 correct)。carryover 1 项：P3-ARCHDEBT remaining 4/5 (paths/project_config/logging_config/studio_registry) → Phase 37+ |
| 2026-09-07 | 协调者 | v31.0 ARCHDEBT-MINI 闭环：P2-ARCHDEBT 子集 2/4 清理。6 commits `8f8c3e1a..4dbe8939` ff-merge：Sub-task A chapter_golden_path 反向 import 修复（create_golden_dashboard_client + run_human_review_smoke + HumanReviewSmokeResult 从 lingwen-core 迁 apps/studio_api/tests/golden_path_smoke.py；-87 行 / +106 行；fixes I001 spirit violation）+ Sub-task B 4 薄代理 (advance_step/dispatch_task/verify_task/get_workflow_status) 从 WorkflowMixin 抽到 mc_orchestrator_proxy.py（MasterController MRO 加 OrchestratorProxyMixin + +5 refactor-guard tests + mc_workflow.py 119→99 行）+ 12 文件 doc 同步（"5 薄代理" → "4 薄代理"，Phase 27 拆 WorkflowRunner 后 stale）+ handoff。carryover 1 项：P2-ARCHDEBT (剩余 infra.got 迁移 + shim cleanup) |
| 2026-09-07 | 协调者 | v30.0 TACKLE-14-FAILURES 闭环：tests/agent_system 14→0 failed (-14)，tests/got 156 / lingwen-core 68 / ruff 不变。9 commits `2de95a80..38b854e7` ff-merge：1 spec + 1 plan + 5 atomic tasks (T1 stub `_state` 注入 / T5 env-var rewrite / T4 cost record_at + migration / T2 WorkflowRunner 迁移 / T3 audit try/except) + 1 handoff。**2 真 prod 改动**（mc_writing.py 韧性契约 broad except + log warning + 空 audit report 兜底 / cost_persistence.py `record_at()` public helper）+ 5 test 文件调整 + 2 处 stale assertion 修正。carryover 1 项：P2-ARCHDEBT |
| 2026-09-07 | 协调者 | v29.0 P2-MC-WRITING 闭环：tests/agent_system 84→14 failed (-70)，tests/got 156 / lingwen-core 68 / ruff 不变。17 commits `106dd21d..b1b748ad` ff-merge：1 spec + 1 plan + 5 production-fix (skill-registry pilot memory-hook budget-endpoints master-controller) + 1 真 prod 改动 (`mc_editing.py:202` 修 Phase 15.0 P3-SPLIT 迁移遗留 `from mc_utils import ...`) + 8 test-only (master-controller-e2e phase7-1 master-controller-with-usage agent-config cost-persistence path-asserts) + 1 handoff。剩余 14 failed 按 5 类根因归档（7 stub `_state` / 1 export / 2 audit 韧性 / 2 `_connect()` API / 2 env-var）→ P2-30-FAILURES Phase 候选。carryover 2 项：P2-30-FAILURES / P2-ARCHDEBT |
| 2026-09-04 | 协调者 | v28.0 P2-RESUME-VERIFY 闭环：5 E2E tests 用真实 GoTScheduler + ThoughtGraph（非 MagicMock）验证 scheduler 对已 COMPLETED 节点幂等 + DECISION resume continuation + start_nodes=None derivation + state.start_nodes 持久化 + WorkflowRunner.run→resume 完整 cycle。0 改范围 9 类文件不动 (workflow_runner / mc_workflow / workflow_state / got_bridge / infra.got / graph / shim / facade / HANDOFF*)；0 new failure (master 84 baseline = worktree 84, +5 NEW PASS)；2 RED 学习点（scheduler.run 二次调用 paused=False 不报告旧 paused；scheduler.run(start_nodes) 不限制执行范围到 start_nodes chain）。7 commits `05e4f91b` spec + `d3f164c8` plan + 5 tests + `7f9049f3` handoff 待 ff-merge。carryover 2 项：P2-MC-WRITING（独立大 phase 调查 84 pre-existing cascade）/ P2-ARCHDEBT（战术分散 + 删 PHASE-COMPAT shim） |
| 2026-09-04 | 协调者 | v27.0 P2-WFRUNNER 闭环：`WorkflowRunner` service class 从 WorkflowMixin 抽出（workflow_runner.py 307 行 new）+ mc_workflow.py 404 → 119 行 (-70%)；TDD 21 tests + 2 refactor guards；0 改范围 7 类文件不动；0 new failure (master 90 → worktree 84, net -6)。13 commits `9b57d16a` 待 ff-merge。carryover 3 项：P2-RESUME-VERIFY（紧接 Phase 28 建议）/ P2-MC-WRITING（独立大 phase）/ P2-ARCHDEBT（战术分散 + 4 薄代理 → OrchestratorProxyMixin） |
| 2026-09-03 | 协调者 | v25.9 human_review 流水线修复闭环：mc_workflow.py 还原（105→376 行）+ 4 dashboard smoke 解 skip + cascade +15 fixed / 0 new failures；master `0a6f4346` 4 commit ff-merge；carryover 5 项 Phase 26+ 候选 |
| 2026-09-03 | 协调者 | v25.4 收尾：前端类型债清零（vue-tsc 0 error）+ batch templates 前端闭环（PilotTemplatePanel）+ socksio 依赖修复 + stash@{0} 清理。P2-DTOMIGR 由会话-A 完成，P2 候选全部完成 |
| 2026-09-02 | Track A | REQ-001 切片 E「差异收尾」：`CreatorDeviationFinalize.vue` 可操作收尾清单，复用 `utils/batchDeviation.ts`（与节奏带共享批次偏差推导）+ 按批次持久化复核状态。至此 REQ-001 全部切片完成 |
| 2026-09-02 | 协调者 | 黑板从 v12/Phase15 刷新至 v25.1：废弃过期 P1/P2/P15 记录，改为 P1-SHIM + Phase 26+ 候选 backlog |