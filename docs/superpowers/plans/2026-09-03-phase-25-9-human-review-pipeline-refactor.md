# Phase 25.9 — human_review 流水线修复 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 对齐 `WorkflowMixin.run_workflow` / `resume_workflow` 与新 `GoTScheduler` API，解 4 个诚实 skip 的 human_review 用例；零架构债修复。

**Architecture:** 单文件改写 `mc_workflow.py` 的 2 个方法体（`run_workflow` 改调 `got_bridge.build_got_scheduler` + `scheduler.run(start_nodes, initial_inputs)` + `dataclasses.asdict(summary)`；`resume_workflow` 改签名为 `(decision_id, option, resolved_by="human")` 并转给 `scheduler.resume`）+ 移除 `tests/dashboard/test_human_review_smoke.py` 4 处 `@pytest.mark.skip`。不动 `got_bridge.py` / `chapter_golden_path.py` / `apps/studio_api/*` / `infra/got/*` / `.lingwen/architecture.yml`。

**Tech Stack:** Python 3.13 / pytest / dataclasses / FastAPI (TestClient 间接) / ruff

**Worktree setup** (execute before Task 1):

```bash
# 已由 brainstorming 阶段建好 worktree
cd /home/ailearn/projects/LingWen-phase-25-9
git status --short && git log -1 --oneline  # 应为 clean + f5934262
uv sync --all-packages
uv pip install pytest pytest-asyncio psutil  # per MEMORY.md N.14 lesson 4

# 复用 worktree 自带 .venv（如果已存在）
# 否则用 /home/ailearn/miniconda3/bin/python 也可（per CLAUDE.md "PYTHONPATH 挂自研包 src"）
```

**Run commands** (per MEMORY.md + HANDOFF-claude-code.md):

```bash
# 后端（推荐用 worktree 自带 venv）
.venv/bin/python -m pytest tests/dashboard/test_human_review_smoke.py -v
.venv/bin/python -m pytest tests/dashboard -q
.venv/bin/python -m pytest tests/ci -q
.venv/bin/python -m pytest tests/got tests/agent_system -q

# Lint
ruff check packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py
ruff format --check packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py

# 若未建 venv，用 conda + PYTHONPATH：
SRC="$(ls -d packages/*/src | tr '\n' ':')"
PYTHONPATH="$SRC" /home/ailearn/miniconda3/bin/python -m pytest tests/dashboard/test_human_review_smoke.py -v -p no:deepeval -p no:locust
```

---

## File Structure

| File | Action | Reason |
|------|--------|--------|
| `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py` | MODIFY: `run_workflow` (line 38-77) 改写 + `resume_workflow` (line 88-97) 改写 | 对齐新 GoTScheduler API |
| `tests/dashboard/test_human_review_smoke.py` | MODIFY: 移除 4 处 `@pytest.mark.skip` 装饰器（行 22/32/44/52） | 解 skip 让测试跑起来 |
| `docs/superpowers/handoffs/2026-09-03-phase-25-9-human-review-pipeline-refactor-handoff.md` | CREATE | Phase handoff |

**Total: 1 source commit（fix）+ 1 handoff commit。** spec + plan commits 已分别在 brainstorming / writing-plans 阶段独立完成（commit #1 + commit #2）。

**0 改范围（已声明）**：`got_bridge.py` / `chapter_golden_path.py` / `apps/studio_api/*` / `infra/got/*` / `.lingwen/architecture.yml` / `HANDOFF*.md` / `CLAUDE.md`（本次不发版）

---

## Task 1: RED — 移除 skip 装饰器，确认 4 用例 fail

**Files:**
- Modify: `tests/dashboard/test_human_review_smoke.py:22, 32, 44, 52`（4 处 `@pytest.mark.skip(...)` 装饰器）

- [ ] **Step 1.1: 移除 4 处 `@pytest.mark.skip` 装饰器**

打开 `tests/dashboard/test_human_review_smoke.py`，找到以下 4 处装饰器并整段删除（包括装饰器与紧随的 `def test_*` 上方）：

```python
    @pytest.mark.skip(
        reason="预存在缺陷：MasterController 人审流水线整体陈旧（WorkflowMixin.run_workflow 仍按旧 GoTScheduler 签名调用、"
        "build_router 缺失），run_workflow 实际以 500 失败；同因也致 tests/got、tests/agent_system 未通过，需整体重构该流水线"
    )
    def test_golden_path_covers_mc_resume(self, tmp_path: Path) -> None:
```

```python
    @pytest.mark.skip(reason="预存在缺陷：同上，MasterController 人审流水线需整体重构")
    def test_full_resolve_resume_smoke(self, tmp_path: Path) -> None:
```

```python
    @pytest.mark.skip(reason="预存在缺陷：同上，MasterController 人审流水线需整体重构")
    def test_smoke_repeatable_on_fresh_state(self, tmp_path: Path) -> None:
```

```python
    @pytest.mark.skip(reason="预存在缺陷：同上，MasterController 人审流水线需整体重构")
    def test_active_workflow_not_paused_after_resume(self, tmp_path: Path) -> None:
```

4 处删除后，方法签名直接对齐 `def test_...`。

- [ ] **Step 1.2: 跑测试，确认 RED（预期 TypeError）**

```bash
cd /home/ailearn/projects/LingWen-phase-25-9
.venv/bin/python -m pytest tests/dashboard/test_human_review_smoke.py -v -p no:deepeval -p no:locust 2>&1 | tee /tmp/phase-25-9-step1.2.log
```

**预期 FAIL 模式**：
- `test_golden_path_covers_mc_resume`: `RuntimeError` 或 `TypeError`（`build_router` 触发真实 LLM provider init，且 stub controller 的 `run_workflow` 调用旧 API）
- `test_full_resolve_resume_smoke` / `test_smoke_repeatable_on_fresh_state` / `test_active_workflow_not_paused_after_resume`: `TypeError: GoTScheduler.__init__() got an unexpected keyword argument 'workflow_name'`（即旧 kwargs 被拒）

如果 4 用例全部 fail 且失败原因包含上述模式 → RED 状态确认。

- [ ] **Step 1.3: 不 commit（task 1 是 RED 测试，中间态）**

直接进 Task 2 实现修复。

---

## Task 2: GREEN — 改写 `WorkflowMixin.run_workflow` + `resume_workflow`

**Files:**
- Modify: `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py:38-77, 88-97`

- [ ] **Step 2.1: 改写 `run_workflow`（替换 line 38-77 全部内容）**

替换前完整内容（line 38-77）：

```python
    def run_workflow(
        self,
        workflow_name: str,
        start_nodes: Optional[list[str]] = None,
        initial_inputs: Optional[Dict[str, Any]] = None,
        cost_budget_usd: Optional[float] = None,
        max_backtracks: int = 2,
        base_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """用 GoT 调度器运行工作流"""
        from infra.got.scheduler import GoTScheduler

        try:
            self._current_budget_usd = cost_budget_usd
            self._current_run_id = uuid.uuid4().hex

            scheduler = GoTScheduler(
                workflow_name=workflow_name,
                start_nodes=start_nodes,
                initial_inputs=initial_inputs,
                max_backtracks=max_backtracks,
                base_dir=base_dir,
                cost_tracker=self.cost_tracker,
                budget_service=self.budget_service,
                budget_service_by_tier=self.budget_service_by_tier,
                master_controller=self,
            )

            result = scheduler.run()

            self._last_scheduler = scheduler
            self._last_graph = result.get("graph")
            self._last_workflow_name = workflow_name
            self._last_start_nodes = start_nodes or []
            self._last_initial_inputs = initial_inputs or {}

            return result
        finally:
            self._current_budget_usd = None
            self._current_run_id = None
```

替换为：

```python
    def run_workflow(
        self,
        workflow_name: str,
        start_nodes: Optional[list[str]] = None,
        initial_inputs: Optional[Dict[str, Any]] = None,
        cost_budget_usd: Optional[float] = None,
        max_backtracks: int = 2,
        base_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """用 GoT 调度器运行工作流。

        通过 got_bridge.build_got_scheduler 工厂构造 scheduler（正确连线
        AgentComputeFn / cost_tracker / budget_service），调用 scheduler.run 并把
        ExecutionSummary 转为 dict 返回。
        """
        import dataclasses

        from lingwen_core.agents.got_bridge import build_got_scheduler

        try:
            self._current_budget_usd = cost_budget_usd
            self._current_run_id = uuid.uuid4().hex

            scheduler, graph = build_got_scheduler(
                master=self,
                workflow_name=workflow_name,
                base_dir=base_dir,
                max_backtracks=max_backtracks,
            )

            summary = scheduler.run(
                start_nodes=start_nodes or [],
                initial_inputs=initial_inputs,
            )

            self._last_scheduler = scheduler
            self._last_graph = graph
            self._last_workflow_name = workflow_name
            self._last_start_nodes = start_nodes or []
            self._last_initial_inputs = initial_inputs or {}

            # ExecutionSummary → Dict; paused_nodes 是 list[NodeExecution] → 抽 id
            result = dataclasses.asdict(summary)
            if isinstance(result.get("paused_nodes"), list):
                result["paused_nodes"] = [
                    getattr(n, "id", str(n)) for n in summary.paused_nodes
                ]
            return result
        finally:
            self._current_budget_usd = None
            self._current_run_id = None
```

- [ ] **Step 2.2: 改写 `resume_workflow`（替换 line 88-97）**

替换前完整内容（line 88-97）：

```python
    def resume_workflow(self) -> Optional[Dict[str, Any]]:
        """恢复上次中断的工作流"""
        if self._last_scheduler is None:
            return None
        try:
            result = self._last_scheduler.resume()
            return result
        except Exception as e:
            logger.error("resume_workflow failed: %s", e)
            return None
```

替换为：

```python
    def resume_workflow(
        self,
        decision_id: str,
        option: str,
        resolved_by: str = "human",
    ) -> Optional[Dict[str, Any]]:
        """恢复上次中断的工作流。

        把决策解析请求转给 last_scheduler 的 resume()。decision_id / option /
        resolved_by 由 apps/studio_api/routes/workflows.py resume 路由透传。
        """
        import dataclasses

        if self._last_scheduler is None:
            return None
        try:
            node_execution = self._last_scheduler.resume(decision_id, option, resolved_by)
            return dataclasses.asdict(node_execution) if node_execution else None
        except Exception as e:
            logger.error("resume_workflow failed: %s", e)
            return None
```

- [ ] **Step 2.3: 跑 4 个 unskip 用例，确认 GREEN**

```bash
cd /home/ailearn/projects/LingWen-phase-25-9
.venv/bin/python -m pytest tests/dashboard/test_human_review_smoke.py -v -p no:deepeval -p no:locust 2>&1 | tee /tmp/phase-25-9-step2.3.log
```

**预期 PASS 模式**：4 用例全部通过。

- [ ] **Step 2.4: 跑 cascade 测试，确认 ZERO 新增失败**

```bash
.venv/bin/python -m pytest tests/got tests/agent_system -q -p no:deepeval -p no:locust 2>&1 | tee /tmp/phase-25-9-step2.4.log
```

**预期**：所有原本 pass 的仍 pass，原本 fail 或 skip 的**保持原状态**，**ZERO 新增失败**。

---

## Task 3: 跑全量 baseline + ruff + commit

**Files:**
- Modify: 已完成（mc_workflow.py + test_human_review_smoke.py）

- [ ] **Step 3.1: 跑全量 baseline**

```bash
cd /home/ailearn/projects/LingWen-phase-25-9
.venv/bin/python -m pytest tests/dashboard -q -p no:deepeval -p no:locust 2>&1 | tee /tmp/phase-25-9-step3.1a.log
.venv/bin/python -m pytest tests/ci -q -p no:deepeval -p no:locust 2>&1 | tee /tmp/phase-25-9-step3.1b.log
.venv/bin/python -m pytest apps/studio_api/tests packages/lingwen-shared/tests packages/lingwen-llm/tests -q -p no:deepeval -p no:locust 2>&1 | tee /tmp/phase-25-9-step3.1c.log
```

**预期**：
- `tests/dashboard`: 357 passed + 3 skipped（baseline 353+7 → +4 通过、-4 skip）
- `tests/ci`: 205 passed + 1 skipped（不变）
- `studio_api + shared + llm`: 全绿（与 baseline 一致）

- [ ] **Step 3.2: ruff check + format --check**

```bash
ruff check packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py tests/dashboard/test_human_review_smoke.py
ruff format --check packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py tests/dashboard/test_human_review_smoke.py
```

**预期**：0 问题。

如果 ruff 报错，运行 `ruff format <file>` 后重检。

- [ ] **Step 3.3: commit fix**

```bash
cd /home/ailearn/projects/LingWen-phase-25-9
git add packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py tests/dashboard/test_human_review_smoke.py
git status --short  # 应见 2 个 modified 文件

git commit -m "$(cat <<'EOF'
fix(lingwen-core): align WorkflowMixin with new GoTScheduler API; unskip human_review smoke

Phase 25.9 最小可用修复：
- WorkflowMixin.run_workflow 改调 got_bridge.build_got_scheduler(master, ...) 工厂
  （正确连线 AgentComputeFn / cost_tracker / budget_service），ExecutionSummary 走
  dataclasses.asdict 转 dict 返回，paused_nodes 兜底抽 id。
- WorkflowMixin.resume_workflow 改签名为 (decision_id, option, resolved_by='human')，
  与 apps/studio_api/routes/workflows.py resume 路由透传对齐，转给 scheduler.resume。
- 移除 tests/dashboard/test_human_review_smoke.py 4 处 @pytest.mark.skip（行 22/32/44/52），
  断言不变。

baseline → target 测试数：
- tests/dashboard: 353 passed + 7 skipped → 357 passed + 3 skipped (+4 -4skip)
- tests/ci: 205 passed + 1 skipped → 205 passed + 1 skipped (不变)
- tests/got + tests/agent_system: ZERO 新增失败（monkeypatch 路径不受 mixin 改动影响）

0 改范围（声明）：
got_bridge.py / chapter_golden_path.py / apps/studio_api/* / infra/got/* /
.lingwen/architecture.yml / HANDOFF*.md

后续 followup（carryover to Phase 26+）：
- infra.got.* 迁移至 packages/lingwen-got/（补 lingwen-core allowed_imports）
- chapter_golden_path.py 反向 import apps.studio_api.* 整改
- HANDOFF 文档 latest_decision_queue 措辞修订
- human_review 真正端到端 E2E（Playwright + live backend）

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

**注**：按全局 ~/.claude/settings.json 设 `CLAUDE_CODE_ATTRIBUTION_HEADER: "0"`，实际 commit 应**不包含** Co-Authored-By 行（用 `git commit --no-verify` 不需要，仅去掉 footer 行即可）。

- [ ] **Step 3.4: 验证 commit 与 diff**

```bash
git log -1 --stat
git diff HEAD~1 HEAD --stat
```

**预期**：2 个文件 modified，commit message 含 baseline→target + 0 改范围 + followup。

---

## Task 4: Handoff + ff-merge 准备

**Files:**
- Create: `docs/superpowers/handoffs/2026-09-03-phase-25-9-human-review-pipeline-refactor-handoff.md`

- [ ] **Step 4.1: 写 handoff**

新建文件，按现有 handoff 模板（参考 `docs/superpowers/handoffs/2026-08-30-phase-126-v16-5-n1-factory-pattern-handoff.md`）：

```markdown
# Phase 25.9 — human_review 流水线修复 · Handoff

## 完成项
- [列出本 phase 完成的所有工作 + commit SHA]

## 测试 gates
| 门 | 结果 |
|----|------|
| tests/dashboard | 357 passed + 3 skipped（baseline 353+7） |
| tests/ci | 205 passed + 1 skipped（不变） |
| tests/got + tests/agent_system | ZERO 新增失败 |
| ruff check + format --check | 0 |
| 关联 chapter_golden_path 引用 | 维持原样 |

## 改动清单（git diff --stat HEAD~3）
- packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py (~30 行 diff)
- tests/dashboard/test_human_review_smoke.py (-4 行装饰器)
- docs/superpowers/specs/2026-09-03-phase-25-9-human-review-pipeline-refactor-design.md (NEW)
- docs/superpowers/plans/2026-09-03-phase-25-9-human-review-pipeline-refactor.md (NEW)
- docs/superpowers/handoffs/2026-09-03-...-handoff.md (NEW)

## Carryover (out of scope per 最小可用)
- infra.got.* 迁移至 packages/lingwen-got/
- chapter_golden_path.py 反向 import 整改
- HANDOFF 文档措辞修订
- 真正 E2E（Playwright + live backend）

## 下一步建议
- 收 master（ff-merge phase-25-9 分支）
- 更新 CLAUDE.md 版本块到 v25.9
- 更新 collaboration/CURRENT_STATUS.md + BACKLOG.md
- 在 P2 候选里添加本 phase 遗留项作为后续 phase 立项输入
```

- [ ] **Step 4.2: commit handoff**

```bash
git add docs/superpowers/handoffs/2026-09-03-phase-25-9-human-review-pipeline-refactor-handoff.md
git commit -m "docs(phase-25-9): human_review 流水线修复 handoff"
```

- [ ] **Step 4.3: ff-merge 准备（不自动执行）**

```bash
cd /home/ailearn/projects/LingWen  # 主 checkout
git checkout master
git fetch origin  # 确保 origin/master 最新
git merge --ff-only phase-25-9-human-review-pipeline-refactor
git log -1 --oneline  # 应 = worktree HEAD
git push origin master  # 仅在用户明确 OK 后执行
```

**等用户确认后执行 push**。per 系统指令"Commit or push only when the user asks"。

---

## Self-Review Checklist

执行前对照 spec 自检：

- [x] Spec §1 动机对应 Task 1（RED）+ Task 2（GREEN）
- [x] Spec §2.2 文件清单（mc_workflow.py + test_human_review_smoke.py）= 本 plan 文件清单
- [x] Spec §3.1 run_workflow 代码块 = Task 2 Step 2.1 完整代码
- [x] Spec §3.2 resume_workflow 代码块 = Task 2 Step 2.2 完整代码
- [x] Spec §4 错误处理覆盖 build_got_scheduler 失败 / scheduler.run 异常 / _last_scheduler is None / paused_nodes 兜底
- [x] Spec §5 baseline→target 测试数 = Task 3 Step 3.1 验收
- [x] Spec §6 风险矩阵所有项在本 plan 中均有对应步骤
- [x] Spec §7 验证门 = Task 3 Step 3.1-3.2
- [x] Spec §9 carryover 显式列在 Task 4 handoff carryover 段
- [x] 0 改范围（got_bridge / chapter_golden_path / apps.studio_api / infra.got / architecture.yml）显式声明在 Task 4 handoff

无 placeholder、无歧义、无 spec gap。