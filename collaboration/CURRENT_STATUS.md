# 灵文项目状态看板

> **最后更新**: 2026-09-08
> **更新者**: 协调者（v36.0 P3-ARCHDEBT (paths) 闭环；P3-ARCHDEBT 2/5 完成）
> **下一协作**: v36.0 P3-ARCHDEBT (paths) 已闭环: `infra/paths.py` (1 module, 125 lines, 5 top-level public symbols: ProjectPaths / resolve_project_root / get_paths / get_chapters_dir / get_rules_dir) → `packages/lingwen-paths/`。86 consumer 迁移 (8 intra-infra + 16 cross-package in 5 packages + 1 apps + 61 tests + 3 tools); `infra/paths.py` 删除; invariant #52 NEW. 6 atomic commits on phase-37-p3-archdebt-paths (C0 spec+plan / C1 scaffold / C2 migrate / C3 delete / C4 invariant+version / C5 guards+doc-sync). Validation: 6 phase37 guards GREEN + 9 baselines preserved (lingwen-core 68/68 + lingwen-world-model 201/201 + lingwen-got 208/208 + lingwen-creator 73/73 + studio_api 82/82 + lingwen-quality 3/3 + lingwen-pipeline 1/1 + lingwen-llm 11/11 + lingwen-cli 3/3) + ruff 4 pre-existing E741 unchanged (2 I001 auto-fixed). C5 修复 guard test (regex `^from lingwen_paths` 不匹配 indented function-body imports per Phase 33 lesson → `^\s*from lingwen_paths`). Carryover closure: P3-ARCHDEBT 2/5 (paths) → CLOSED; P3-ARCHDEBT remaining 3/5 (project_config / logging_config / studio_registry) → Phase 38+. v35.0 P3-ARCHDEBT (errors pilot) 已闭环: `infra/errors.py` (1 module, 380 lines, 23 public symbols) → `packages/lingwen-errors/`。14 consumer 迁移 (4 packages: lingwen-quality / lingwen-world-model / lingwen-pipeline / lingwen-llm + 8 intra-infra); `infra/errors.py` 删除; invariant #51 NEW. 6 atomic commits on phase-36-p3-archdebt-errors (C0 spec / C0b plan / C1 scaffold / C2 migrate / C3 delete / C4 invariant+version / C5 guards+doc-sync). Validation: 6 phase36 guards GREEN + 7 baselines preserved (lingwen-core 68/68 + lingwen-world-model 201/201 + lingwen-got 208/208 + studio_api 82/82 + lingwen-quality + lingwen-pipeline + lingwen-llm) + ruff clean. C5 修复 test name (architecture.yml I051 scope `test_infra_errors_module_deleted` → `test_infra_errors_deleted`) + CLAUDE.md v35.0 entry package list (6 packages wrong → 4 packages correct). Carryover closure: P3-ARCHDEBT 1/5 (errors) → CLOSED; P3-ARCHDEBT remaining 4/5 (paths / project_config / logging_config / studio_registry) → Phase 37+. v34.0 WORLD-MODEL-PACKAGE 已闭环 (P2-ARCHDEBT 收官): infra.world_model.* (2282 lines, 37 symbols) + infra/subplot/helpers.py (52 lines) → packages/lingwen-world-model/. 16 consumer migration (1 POC + 2 consistency + 1 subplot + 12 in-package tests); 13 test files → packages/lingwen-world-model/tests/; infra/world_model/ + infra/subplot/helpers.py deleted; invariant #50 NEW. 10 commits on phase-35-world-model-package (C0-C8 + preC7). Validation: 836 + 1skip tests pass (lingwen-world-model 201/201 + lingwen-core 68/68 + lingwen-got 208/208 + studio_api 82/82 + subplot 11/11 + consistency 22/22 + prompt_engineering 244/1skip + 17 phase35 guards); ruff clean. preC7 fixup: 6 file string literal references migrated (Phase 34 N.14 lesson #4, 5th occurrence). Carryover closure: P2-ARCHDEBT → CLOSED. v32.0 SHIM-CLEANUP 已闭环：P2-ARCHDEBT PHASE-COMPAT shim 删除 3/4 完成。**Sub-task 1**：`infra/subplot/data_structures.py`（32 行, 0 消费者）删除。**Sub-task 2**：`infra/world_model/data_structures.py`（69 行, 0 消费者）删除 + `infra/world_model/links.py:28-31` stale 注释清理。**Sub-task 3**：`packages/lingwen-core/src/lingwen_core/agents/master_controller.py`（11 行）删除 + 6 test consumers (12 import sites) 迁移到 canonical `lingwen_pipeline.master_controller`。**+1 fixup commit** 修 5 处漏检的 relative import (`from .data_structures` / `from .master_controller`): `infra/subplot/__init__.py:19` / `infra/world_model/__init__.py:60` / `infra/world_model/key_point_graph.py:24` / `infra/world_model/snapshot_store.py:24` / `packages/lingwen-core/src/lingwen_core/agents/got_bridge.py:32`。**+10 regression guard tests** in `tests/test_phase32_shim_cleanup.py` (3 path-deleted + 6 consumer-migrated + 1 canonical-symbol)。**Validation gates**: G1 ruff clean (on modified files) / G2 guard 10/10 GREEN / G3 6 consumer tests baseline 116+1 skip / G4 critical paths 201 (world_model) + 68 (5 broken) passed post-fixup / G8 grep audit 0 hits. Carryover 新增: `polisher/prompts.py:132` `_safe_label` latent broken import (Explore agent flag).

---

## 📊 项目总体状态

| 项目 | 状态 |
|------|------|
| **版本** | v32.0（Phase 32 — SHIM-CLEANUP P2-ARCHDEBT PHASE-COMPAT shim 删除 3/4） |
| **git main** | master `9980e393`（v32.0 ff-merge 完成，8 commit `3570a86f..9980e393`） |
| **当前阶段** | v32.0 SHIM-CLEANUP 收尾：8 atomic commits = C0 spec/plan docs + C1 RED guard (10 tests) + C2 subplot shim deletion (32 lines) + C3 world_model shim deletion (69 lines) + C4 6 test consumer migration (12 sites → canonical lingwen_pipeline) + C5 master_controller shim deletion (11 lines) + C2.5 fixup (5 missed relative imports) + C6 docs sync (CLAUDE.md v32.0 + architecture.yml 32.0 + 5 doc flips)。G1 ruff clean on modified / G2 guard 10/10 GREEN / G3 6 consumer tests baseline preserved / G4 critical paths 201+68 PASS post-fixup / G8 grep audit 0 hits. **1 NEW architecture invariant #48** (NO PHASE-COMPAT shim files). **Pre-existing 40 fails** confirmed unrelated to Phase 32 via stash baseline (9 fails in 5 representative files on master HEAD) |
| **并行开发** | [COORDINATION.md](https://github.com) §3 自治契约：两会话自认领→全量门绿→自 ff-merge 到 master（常驻 worktree `track-a`/`track-b`）|
| **阻塞项** | 无 |

---

## 🟡 进行中任务

| ID | 任务 | 进度 | 认领人 | 状态 |
|----|------|------|--------|------|
| P2-DRAWER | per-chapter preview drawer（前端） | ✅ 完成 | 会话-A | ✅ |
| P2-INSIGHT | Pilot + Insight 看板集成（前端） | ✅ 完成 | 会话-A | ✅ |
| REQ-001 A/B | 创作者模式增强：`useCreatorMode` 单一来源 + 陪伴「今日下一步」卡（前端） | ✅ 完成 | 会话-A `13f3a63c`；全量门绿 |
| REQ-001 C | 推进「批改节奏带」：`CreatorBatchRhythm.vue` 只读复用 `usePilotBatch`，展示批次范围完成进度 + 越序偏差提示 | ✅ 完成 | 会话-A；vitest/ESLint/knip 绿 |
| REQ-001 D | 写栏「模式引导条」：`CreatorModeGuideBar.vue` 随模式变化的引导条，可关闭、关闭状态按模式本地记忆 | ✅ 完成 | 会话-A；vitest/ESLint/knip 绿 |
| REQ-001 E | 推进「差异收尾」：`CreatorDeviationFinalize.vue` 越序差异收尾清单，复用 `utils/batchDeviation.ts`，复核状态按批次持久化 | ✅ 完成 | 会话-A；vitest/ESLint/knip 绿 |
| REQ-001 全量 | 创作者模式增强 A/B/C/D/E 全部交付 | ✅ 完成 | 会话-A |
| P2-MULTI | multi-LLM 并发批次（后端，自服务完成） | 后端 B 已认领并完成 | 后端 B | ✅ 完成 |

> 详见 [BACKLOG.md](BACKLOG.md)：后端 B 已自服务完成 P2-QUEUE ✅ + P2-RESTART ✅ + P2-MULTI ✅（后端 P2 系列收尾标 ✅）。

---

## ✅ 已完成（近期，合流后）

| 项 | 内容 | 验证 |
|----|------|------|
| **v25.9 human_review 流水线修复** | master 4 commit ff-merge `0a6f4346`：mc_workflow.py 自仓库迁移后是 hallucinated stub，从 git history `5c4259e5:novel-factory/infra/agent_system/master_controller.py` 还原真实实现，对齐新 GoTScheduler API。`run_workflow` 改调 `got_bridge.build_got_scheduler(master, ...)` + 返回 wrapper dict；`resume_workflow` 改签名 `(decision_id, option, resolved_by='human')` 三步走（resolve queue → scheduler.resume → re-harvest → re-run scheduler）；`list_pending_decisions` 改调 `queue.pending()`；`resolve_decision` 签名修正。恢复 4 个未迁移 helper（`_collect_executions` / `_maybe_memory_context` / `_maybe_incremental_backfill` / `_harvest_decision_specs`）。Phase 8.12 `budget_service.set(scope="run", ...)` 恢复。tests/dashboard/test_human_review_smoke.py 4 处 `@pytest.mark.skip` 移除。**0 改范围**：got_bridge.py / chapter_golden_path.py / apps.studio_api/* / infra/got/* / architecture.yml / HANDOFF*.md | ✅ tests/dashboard 357 passed + 3 skipped（+4 -4skip）；cascade +15 fixed / 0 new failures；ruff clean |
| **v27.0 P2-WFRUNNER service 拆分** | Phase 27 branch `phase-27-wfrunner` 13 commits（48c26b5c spec + 8c988a7c plan + d2167e0f skeleton + 849aecae/d2135d85 polish + 1d04f5f8 budget + ec30f37f scheduler + f86f7c7c RAG/DECISION + 9309fbd8 run() 11 步 + 9208d0d7/18e6cee5/954edcab resume() 8 步 + bfc9e126 helpers move + fc08d113 guards + b042a22b stub fix + 9b57d16a gate pass）待 ff-merge。新增 `packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py` (307 行，`WorkflowRunner` service class: `run()` 11 步 + `resume()` 8 步 + 5 internal helpers + `_resolve_decision_locked` Phase 6.5 fcntl lock)；`mc_workflow.py` 404 → 119 行 (-70%, 4 薄代理 + 3 决策委托 + `_get_runner()` lazy accessor + run/resume 1-line delegates)。新增测试 `tests/agent_system/test_workflow_runner.py` (669 行, 21 tests: TDD 覆盖 construction + run() 11 步 + resume() 8 步 + 4 helpers)。修改测试: `test_workflow_state.py` (+2 refactor guards `TestWorkflowRunnerRefactorGuard` 防 runner 有 `_last_*` 和 `_state`); `test_master_controller_budget.py` (6 sed + `_harvest_decision_specs` 改走 `master._get_runner()` + stub init `master._state = WorkflowState.empty()`); `test_incremental_backfill.py` (1 monkeypatch target 迁 `WorkflowRunner._maybe_incremental_backfill`)。**0 改范围**: 7 类文件不动 (gateway facade / route / helper / dataclass / shim / got_bridge / architecture.yml / HANDOFF*)。**Verification gates**: 10 gates 全过 (G3 有 2 pre-existing env FileNotFoundError out of scope) | ✅ G1 test_workflow_state 13/13 (11 + 2 guard) / G2 test_workflow_runner 21/21 / G3 test_master_controller_budget 6/6 target / G4 tests/agent_system 84 fail = master 84 baseline (0 new failure, net -6 from Task 11 fix) / G5 test_decision_pause_resume 17/17 / G6 test_incremental_backfill 15/15 / G7 ruff clean / G8 grep 7 fields 0 hits / G9 mc_workflow 119 lines / G10 workflow_runner 307 lines。**Carryover**: P2-RESUME-VERIFY (Phase 28 建议) / P2-MC-WRITING (独立大 phase) / P2-ARCHDEBT (战术分散)。**Handoff**: `docs/superpowers/handoffs/2026-09-04-phase-27-wfrunner-handoff.md` |
| **v26.0 P2-WFSTATE 散点整合** | master Phase 26 6 commits 待 ff-merge `ee3396ae`：`99bed427` spec + `14f40bd6` plan + `01c504cf` feat WorkflowState dataclass (TDD 8 unit) + `1409663b` refactor src (7 files 7 散点 → 1 dataclass + 2 atomic with_updates) + `6ec11b1b` refactor tests (9 files Pattern A/B/C) + `ee3396ae` refactor guard (3 守护测试防回潮)。`_last_scheduler` / `_last_graph` / `_last_workflow_name` / `_last_start_nodes` / `_last_initial_inputs` / `_last_incremental_backfill` / `_last_memory_context` → `self._state: WorkflowState` (frozen dataclass with `with_updates(**kwargs)` + `empty()` classmethod + `default_factory` list/dict 独立)。0 行为变更；外部 API 不动 | ✅ tests/dashboard 357 + 3（UNCHANGED）；tests/cross_volume/test_incremental_backfill.py 15（UNCHANGED）；tests/got/test_decision_pause_resume.py 17（UNCHANGED）；tests/agent_system/test_workflow_state.py 11 NEW（8 unit + 3 guard）；grep 7 fields 0 hits (down from 15 baseline)；ruff clean；0 new failure 验证（stash 回退到 src commit 上同样 9 fail pre-existing） |
| **v25.8 遗留 2 项处置** | ① **creator 偏好契约真缺陷修复**：`CreatorPreferencesResponse`（lingwen-shared 契约）强制要求 `creation_mode`/`quality_profile`，而 lingwen-creator 迁移后 payload 未提供 → GET /api/creator/preferences 触发 pydantic 校验错误。修复：`preferences.py` 新增 `creation_settings_from_project` 从项目 `config/project.yaml` 解析创作模式/质量配置并入 payload；`test_creator_preferences_get_put` 去 skip 并按契约校验 ② **human_review 迁移**：应用迁移友好修复（`GotScheduler`→`GoTScheduler`、`dashboard.*`→`apps.studio_api.*` 导入），深查确认 MasterController 人审流水线整体陈旧（WorkflowMixin.run_workflow 仍按旧 GoTScheduler 签名、build_router 缺失、cost_tracker/latest_decision_queue 未初始化），run_workflow 实际 500 失败 → 归类为预存在缺陷需整体重构，4 用例诚实 skip | ✅ tests/dashboard 353 passed + 7 skipped；tests/ci 205 passed + 1 skipped；ruff 0 |
| **v25.7 全面验收** | 全门复核：前端 vitest 1862 passed + ESLint/knip/vue-tsc/build 0；后端 studio_api+shared 222 / lingwen-llm 11 / tests/ci+dashboard 557 passed 9 skipped；`lingwen.py doctor` 需 PYTHONPATH + 仓库外内容仓库 | ✅ 全绿 |
| **v25.7 tests/dashboard 基线清理** | `82e75fd9` tests/dashboard 由 15 failed 归零（352 passed + 8 skipped）：契约漂移修复（cascade id→run_id、ref-graph total_nodes/edges、health 断言放宽）；**真 bug 修复** infra/cross_volume/storage.py 3 处遗留 `dashboard.*` 懒导入改 `apps.studio_api.*`（级联/审计/cvg_ws WS 推送此前为被 try/except 吞掉的死代码）；8 项环境基线诚实 skip（均需仓库外内容仓库或 agent 侧修复） | ✅ ruff 0 / 全绿 |
| **v25.6 REQ-003 移动端** | `34f0b0f2` 接通锁层移动抽屉：header-actions 加汉堡（≤768px 显示），侧栏绑定 `open`，点击遮罩/导航项/路由/Esc 收起 + 锁 body 滚动；修复旧 style.css 未接线（模板无汉堡、`.main-content`/`.nav-item-label` 选择器失配）；核心页经审计已由 flex-wrap + 既有 media query 自然适配 | ✅ vitest 1862 passed + 1 skipped / ESLint 0 / knip 0 / vue-tsc 0 / vite build exit 0 |
| **v25.6 P2-REG 修复** | prod preview build 回归（`80790b76`）：实测 cytoscape-fcose 历史根因已随图库迁移 vis-network 消失；真实回归为 v16.2.8 迁移遗留 3 处陈旧引用（useCreatorAdvanceBatch 旧名 `generateCreatorVolumeSummary` + api/index.js 桶内陈旧别名 + 补缺失 `fetchCreatorOverview`） | ✅ vite build exit 0；vitest 1861 + ESLint/knip/vue-tsc 0 |
| **v25.5 首次启动引导** | 新增 `NoProjectOnboarding.vue` + `useBootState.js`：无项目/404 → 全屏引导（本地 `init-project` 命令 + 刷新重试），后端离线走错误态不误判；`App.vue` 挂载期 boot 门控；`composables` 桶补导出通过架构守卫 | ✅ 前端 vitest 1861 passed + 1 skipped / ESLint 0 / knip 0 / vue-tsc 改动文件 0 error |
| **v25.5 质量检查诚实标注** | `WriteWorkspacePage` 中 `/quality/run`（未接入端点）失败不静默：`WriteInlineAnnotationLayer` 显示「质量检查暂不可用」轻提示；附 2 条测试；并修复 `use-quality-typed-wrapper.spec.ts` 过时守卫(3→4) + 移除 `useWriteQualityCheck` 死 re-export(knip) | ✅ 全绿 |
| **v25.5 细节润色** | 紧凑 human-first L1 头部页面标题补省略号防护（`nowrap+ellipsis+min-width:0`）；「>15 控件」全量核查无页面超限，最密的「进阶」模板库默认折叠不改 | ✅ 前端 vitest 全量绿 / ESLint 0 |
| **v25.4 类型债清零** | vue-tsc typecheck:app 5 pre-existing + tests-relaxed 3 pre-existing 全部清零：`useStudioProject` JSDoc 返回类型 + `runPreflight` 参数类型 + 3 处 creator DTO cast 改具体契约类型（`CreatorMemoryQueryResult`/`CreatorPublishEntry`/`CreatorVolumeTemplateApproval`）+ pilot-history-list spec 补 `slug` | ✅ 前端 vitest 1850 passed + 1 skipped / ESLint 0 / knip 0 / vue-tsc **0 error** |
| **v25.4 依赖修复** | pyproject.toml 增 `socksio>=1.0` + uv.lock（httpx SOCKS 代理访问 LLM provider 缺失，此前 4+ provider 测试失败） | ✅ lingwen-llm 11 passed |
| **v25.4 仓库清理** | 清理 stash@{0} `trackb-baseline-check-residual`（确认无价值的基线对比残留） | ✅ |
| **v25.3 双会话合流** | Track A REQ-001 创作者模式增强 5 切片 + P2-QUEUE 前端；Track B P2-QUEUE/RESTART/MULTI 后端全部入 master | ✅ master `3d009514` |
| v25.1 双会话合流 | Track A event_types 过滤开关（前端）+ Track B batch templates（后端），0 冲突 ff-merge | ✅ 见 CLAUDE.md v25.1 |
| 合并门复核 | 发现并修复 Track A 引入的 9 个测试类型错误（`1c1d3a82`），vue-tsc 回到 5 pre-existing | ✅ |
| 合并态验证 | 后端 pytest 32 + ruff clean；前端 vitest/ESLint/knip 通过；vue-tsc 5 pre-existing | ✅ |
| P1-SHIM | Track A 自服务完成 batch-templates *DTO shim（`studio.ts` + `shared/index.ts`），已 ff-merge | ⭐ `23aa1ffc`；全量门绿 |
| P2-DTOMIGR | Track A 自服务把 `usePilotBatch` DTO 迁移至 `@/api/studio` re-export（技术债） | ⭐ `1ea4fce3`；全量门绿 |
| P2-QUEUE（前端配合） | Track A 接入批次优先级队列：`listStudioBatchQueue` API + `usePilotBatch.queue/refreshQueue` + `PilotQueuePanel` 只读排队面板 | ⭐ 全量门绿 |
| P2-QUEUE | Track B 自服务完成 batch priority queue（提交/排队/优先级自动推进 + `/api/studio/batch/queue` 端点） | ⭐ `d3347d3b`；batch 受影响子集 18 passed + ruff 全绿，ZERO 新增失败 |
| P2-RESTART | Track B 自服务完成 auto-restart（失败自动重启，`max_attempts` 上限 + 同 job_id 重试，默认 1 零行为变化） | ⭐ `dac678b3`；全量 pytest 3479 passed（272 环境基线，ZERO 新增）+ ruff 全绿 |
| P2-MULTI | Track B 自服务完成 multi-LLM 并发批次（`--parallel` + `--provider`/`--provider-map`，`run_production_batch_parallel` 线程并发不同 chapter 不同 provider，默认串行零行为变化） | 新测试 12 passed + ruff check/format 全绿；agent_system/ci batch 相关簇 ZERO 新增失败 |

> 完整版本链（v21.0 → v25.1）见 `CLAUDE.md`；并发协调点见 `COORDINATION.md`。

---

## 🧪 测试状态（v25.4 收尾态 + 环境基线清零，2026-09-03）

| 测试类型 | 结果 |
|----------|------|
| 后端 pytest（lingwen-llm 受影响） | ✅ 11 passed（socksio 依赖已修复） |
| 后端 pytest（studio_api + lingwen-shared） | ✅ 222 passed |
| 后端 pytest（tests/ci/ + tests/dashboard） | ✅ 557 passed + 9 skipped（v25.7 清理 15 基线；8 skip 为环境基线/agent 迁移诚实标注） |
| 后端 ruff check / ruff format --check | ✅ 0 问题 |
| 前端 vitest（全量） | ✅ 1862 passed + 1 skipped（含 REQ-003 抽屉测试） |
| 前端 ESLint | ✅ 0 |
| 前端 knip | ✅ 0 issues |
| 前端 vue-tsc --noEmit | ✅ **0 error**（typecheck:app + tests-relaxed 均清零） |

> ✅ **环境基线已清零（v25.4 修复）**：`tests/ci/` 迁移路径陈旧（旧 `dashboard/frontend/` / `infra/agent_system|memory_system|state/` → monorepo `apps/dashboard`、`packages/lingwen-core|lingwen-memory`）39 个契约测试已重新定位+校正断言；`test_get_endpoint_registered` 因 starlette 1.6 `_IncludedRouter` 回归改递归收集 `original_router.routes`；health 单测对齐现实（真实 DB + `status∈{healthy,degraded}`）。详见 `b7e2b6c9`。

---

## ⚠️ 已知问题 / 待办追踪（后续工作）

| ID | 问题/事项 | 关联 | 状态 |
|----|----------|------|------|
| P1-SHIM | 前端 `dashboard-contracts` 缺 batch-templates *DTO shim → 已由 Track A 补齐并合并 | 后端已 codegen `lingwen_shared` | ✅ 完成 |
| P2-* | Phase 26+ 候选（Insight 集成/预览抽屉/优先级队列/多 LLM 并发/自动重启/DTO 迁移/Phase114 债） | 见 BACKLOG P2 | 📋 待排期 |

---

## 📝 项目数据（星陨纪元）

| 字段 | 值 |
|------|-----|
| 项目名称 | 星陨纪元 |
| 总章节 | 360 章 |
| AI 痕迹问题 | 已大幅优化 |
| 伏笔回收率 | 55.4% |
| 角色档案 | 9 角色 |

---

## 🤝 协作备注

### 当前协作情况
- **活跃任务数**: 0（待认领 P1-SHIM）
- **阻塞任务**: 0
- **待认领任务**: 2（P1-SHIM + Phase 26+ 各候选）
- **并行会话入口**: 根 `COORDINATION.md`（如何启动双会话、轨道边界、协调点）

### 协作提示
1. 认领任务前先看 `ACTIVE_TASK.md`（如有）
2. 完成工作后及时更新本看板
3. 遇到问题标记 🔴 阻塞并说明需要什么帮助
4. 详细协作规范见 `COLLABORATION_GUIDE.md`（若存在）

### 最近变更记录
| 时间 | 变更 |
|------|------|
| 2026-09-07 | v31.0 ARCHDEBT-MINI 闭环：P2-ARCHDEBT 子集 2/4 清理。6 commits `8f8c3e1a..4dbe8939` ff-merge：Sub-task A chapter_golden_path 反向 import 修复（create_golden_dashboard_client + run_human_review_smoke + HumanReviewSmokeResult 从 lingwen-core 迁 apps/studio_api/tests/golden_path_smoke.py；-87 行 / +106 行；fixes I001 spirit violation）+ Sub-task B 4 薄代理 (advance_step/dispatch_task/verify_task/get_workflow_status) 从 WorkflowMixin 抽到 mc_orchestrator_proxy.py（MasterController MRO 加 OrchestratorProxyMixin + +5 refactor-guard tests + mc_workflow.py 119→99 行）+ 12 文件 doc 同步（"5 薄代理" → "4 薄代理"，Phase 27 拆 WorkflowRunner 后 stale）+ handoff。carryover 1 项：P2-ARCHDEBT (剩余 infra.got 迁移 + shim cleanup) |
| 2026-09-07 | v30.0 TACKLE-14-FAILURES 闭环：tests/agent_system 14→0 failed (-14)，tests/got 156 / lingwen-core 68 / ruff 不变。9 commits `2de95a80..38b854e7` ff-merge：1 spec + 1 plan + 5 atomic tasks (T1 stub `_state` 注入 / T5 env-var rewrite / T4 cost record_at + migration / T2 WorkflowRunner 迁移 / T3 audit try/except) + 1 handoff。**2 真 prod 改动**（mc_writing.py 韧性契约 broad except + log warning + 空 audit report 兜底 / cost_persistence.py `record_at()` public helper）+ 5 test 文件调整 + 2 处 stale assertion 修正。carryover 2 项：P2-ARCHDEBT（infra.got 迁移 + chapter_golden_path 反向 import + 4 薄代理 → OrchestratorProxyMixin + PHASE-COMPAT shim 删）/ Prod preview regression（accepted debt） |
| 2026-09-07 | v29.0 P2-MC-WRITING 闭环：tests/agent_system 84→14 failed (-70)，11 测试文件 + 1 prod-path 修复（`mc_editing.py:202` 修 Phase 15.0 P3-SPLIT 迁移遗留）；tests/got 156 / lingwen-core 68 / ruff 不变；剩余 14 失败按 5 类根因归档（7 stub `_state` / 1 export / 2 audit 韧性 / 2 `_connect()` API / 2 env-var）→ Phase 30 候选。master `b1b748ad`，carryover 2 项：TACKLE-14-FAILURES / P2-ARCHDEBT |
| 2026-09-03 | v25.8 处理 2 项遗留：① creator 偏好契约真缺陷修复（`creation_settings_from_project` 从 config/project.yaml 解析 creation_mode/quality_profile 补 CreatorPreferencesResponse 缺字段，`test_creator_preferences_get_put` 去 skip 通过）② human_review 迁移（`GoTScheduler` + `apps.studio_api.*` 导入迁移友好修复；深查确认 MasterController 人审流水线整体陈旧需重构，4 用例诚实 skip）；tests/dashboard 353 passed + 7 skipped / tests/ci 205 passed + 1 skipped |
| 2026-09-03 | v25.7 全面验收 + tests/dashboard 基线清理（`82e75fd9`）：tests/dashboard 15 failed 归零；契约漂移修复（cascade id→run_id、ref-graph total_nodes/edges、health 断言放宽）+ 真 bug 修复 infra/cross_volume/storage.py 遗留 `dashboard.*` 懒导入 → `apps.studio_api.*`（级联/审计/cvg_ws WS 推送死代码复活）+ 8 项环境基线诚实 skip；后端全套件全绿（ci+dashboard 557/9skip、studio+shared 222、llm 11）|
| 2026-09-03 | v25.6 修复 P2-REG prod preview build 回归（`80790b76`，3 处 v16.2.8 迁移陈旧引用）+ REQ-003 移动端壳层抽屉（`34f0b0f2`，汉堡+遮罩+Esc 收起）；前端 1862 passed + ESLint/knip/vue-tsc 0 |
| 2026-09-03 | v25.5 打磨完善：首次启动引导（NoProjectOnboarding + useBootState + App 门控）+ 质量检查不可用诚实标注（WriteInlineAnnotationLayer 提示 + 2 测试）+ L1 标题省略号防护；清 2 项存量门（quality wrapper 守卫 3→4、useWriteQualityCheck 死 re-export/knip）；前端 1861 全绿 + ESLint/knip/vue-tsc(改动文件) 0 |
| 2026-09-03 | v25.4 收尾：前端类型债清零（vue-tsc 0 error）+ batch templates 前端闭环（PilotTemplatePanel）+ socksio 依赖修复 + stash@{0} 清理 |
| 2026-09-02 | 黑板从 v12/Phase15 刷新至 v25.1 真实状态；废弃过期 P1/P2/P15 记录，接入 CLAUDE.md v25.1 + COORDINATION.md 事实来源 |