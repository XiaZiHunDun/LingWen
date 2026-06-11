# 正文生产 Runbook（Phase 9.67 F59）

> **目标**: 可复制的一章生产路径 — 从 workflow 触发到人工决策、恢复执行，以及可选的 CVG 增量 backfill。  
> **约束**: 默认 **0 真实 LLM**；验收用 stub golden path。

---

## 1. 状态目录与环境变量

| 路径 / 变量 | 用途 |
|------------|------|
| `novel-factory/infra/.state/decisions.json` | 人工决策队列（HumanDecisionQueue） |
| `novel-factory/.state/cross_volume.db` | CVG ripple / reference graph |
| `novel-factory/infra/.state/` | 其它 agent 状态（按 MC 配置） |
| `LINGWEN_INCREMENTAL_BACKFILL=1` | workflow 完成后 opt-in 增量 backfill（F54） |
| `LINGWEN_REAL_LLM=1` | **仅**显式 opt-in 真实 LLM（勿在 CI 默认开） |

---

## 2. 生产路径（`novel_writing`）

### 2.1 启动章节 workflow

```bash
cd novel-factory
# 需已配置 MasterController / API keys（生产环境）
python lingwen.py run-workflow novel_writing \
  --chapter-num 360 \
  # 其它参数见 lingwen.py --help
```

或通过 Dashboard → **工作流** 页触发等价 API（`POST /api/workflows/{name}/run`）。

### 2.2 预期行为

1. GoT 执行至 **DECISION** 节点 → `summary.paused=True`
2. `pending_decisions` 写入 `decisions.json`；Dashboard **决策中心** WS 推送 pending
3. 人工在 Dashboard 选择选项 → `resolve` → `resume_workflow`
4. workflow 继续直至 `emit_chapter` 完成

### 2.3 可选：增量 backfill

```bash
export LINGWEN_INCREMENTAL_BACKFILL=1
# 再跑 novel_writing；emit_chapter COMPLETED 后自动 backfill 该章
```

---

## 3. Stub 验收（golden path，0 LLM）

最小 DECISION 工作流 `chapter_golden`：`write_chapter → outline_judgment → finalize`

```bash
cd novel-factory
python -m infra.agent_system.chapter_golden_path --state-dir /tmp/lingwen-golden-state
# exit 0 + JSON 含 completed_after_resume: true
```

或 pytest：

```bash
pytest tests/agent_system/test_chapter_golden_path.py -q
```

**通过标准**:

- 首次 `run_workflow` 后 workflow **paused**
- `decisions.json` 存在且含 pending 决策
- `resume_workflow(approve)` 后 **finalize** 节点 **COMPLETED**

---

## 4. 人审后恢复（F61 smoke）

**目标**: Dashboard 上 resolve → resume 闭环可重复验收（stub MC，0 API key）。

### 4.1 API 顺序

1. `POST /api/workflows/run` — `chapter_golden` + `base_dir` 指向含 workflow YAML 的 state 目录
2. `GET /api/decisions/pending` — 应 ≥1 条 pending
3. `POST /api/workflows/resume` — `{ decision_id, option: "approve" }`
4. `GET /api/decisions/pending` — 应为空；`GET /api/decisions/all` 对应决策 `status=resolved`
5. `GET /api/workflows/active` — `paused=False`

`resume` 会在 MC 内 resolve 决策；无需单独调 `POST /api/decisions/{id}/resolve`（除非只改状态不恢复 workflow）。

### 4.2 一键 smoke

```bash
cd novel-factory
pytest tests/dashboard/test_human_review_smoke.py -q
```

实现：`infra/agent_system/chapter_golden_path.run_human_review_smoke(state_dir, db_path)`（内部 `create_golden_dashboard_client` + 上述 HTTP 序列）。

**通过标准**:

- run 后 `paused=True`，pending ≥1
- resume 后 `paused=False`，pending 清空，决策已 resolved

---

## 5. Dashboard 联调（可选）

Live e2e（需 backend）：

```bash
cd dashboard/frontend
LINGWEN_E2E_LIVE=1 pnpm e2e:live
```

覆盖：决策列表渲染、resolve 只读态（`decisions-resolve.spec.js`）。

---

## 6. 故障排查

| 现象 | 检查 |
|------|------|
| 无 pending 决策 | workflow 是否含 `type: decision` 节点；`decisions.json` 权限 |
| resume 报 no active workflow | 是否先 `run_workflow` 再 resolve |
| backfill 未触发 | `LINGWEN_INCREMENTAL_BACKFILL=1`；`novel_writing` 是否 failed/paused；`emit_chapter` 是否 COMPLETED |
| Dashboard 决策不刷新 | WS `/api/ws/workflows`；dev 模式 API 走 Vite `/api` 代理 |

---

## 7. 相关文档

- v5 roadmap: `docs/superpowers/plans/2026-06-11-followup-roadmap-v5-post-9.65.md`（F59–F61）
- Incremental backfill: Phase 9.63 F54 / `infra/cross_volume/incremental_backfill.py`
- DECISION 暂停语义: `tests/got/test_decision_pause_resume.py`

---

## 8. Incremental backfill hook (F60)

**Env**: `LINGWEN_INCREMENTAL_BACKFILL=1`（默认 off）

**行为表**（与 `describe_incremental_backfill_hook()` 同步）:

| 条件 | 行为 |
|------|------|
| `LINGWEN_INCREMENTAL_BACKFILL` | `1`/`true`/`yes` 启用；否则 skip |
| `workflow_name` | 仅 `novel_writing` |
| `ExecutionSummary` | `failed=0` 且 `paused=False` |
| `emit_chapter` 节点 | `NodeStatus.COMPLETED` |
| `chapter_num` | 来自 `initial_inputs` 或节点 output |
| `Backfiller.run_chapters` | 单章规则抽取；已有节点 idempotent skip |

**Skip 诊断**: `explain_incremental_backfill_skip(...)` 返回人类可读原因；`None` 表示会执行 backfill。

**Dashboard / API**: `POST /api/workflows/run` 与 `POST /api/workflows/resume` 响应字段 `incremental_backfill`（dict 或 `null`）。示例:

```json
{
  "incremental_backfill": {
    "character_count": 1,
    "foreshadow_count": 0,
    "setting_count": 0,
    "plot_point_count": 0,
    "total_count": 1,
    "elapsed_s": 0.12,
    "dry_run": false,
    "nodes_written": 1,
    "nodes_skipped": 0,
    "pre_node_count": 10,
    "post_node_count": 11
  }
}
```

未触发时字段为 `null`（env 未开、workflow 失败/paused、章节号未解析等）。

---

## 9. Memory RAG hook (F62)

**Env**: `LINGWEN_MEMORY_RAG=stub|live|off`（默认 off；golden path 内置 stub）

| 值 | 行为 |
|----|------|
| `off` / 未设置 | 不注入 `memory_context` |
| `stub` | 确定性 stub 上下文（0 Qdrant，CI / golden path 默认） |
| `live` / `1` / `true` | `MemoryGateway.auto_push_context(chapter_num)` |

**适用 workflow**: `novel_writing`, `chapter_golden`

MC `run_workflow` 在 scheduler 运行前把 `memory_context` 合并进 `initial_inputs`（若调用方未显式提供）。Golden path stub MC 默认 `_memory_rag_mode="stub"`。

**验收**:

```bash
pytest tests/agent_system/test_chapter_memory_hook.py -q
```

行为表: `describe_memory_rag_hook()`（与 runbook 同步）。

---

## 10. Dashboard 章节页 (F63)

导航 **章节** → `ChaptersPage.vue`：

- 章节指标表：`GET /api/chapters?range=1-30`（范围可选 1-30 / 1-50 / 31-60 / 61-90）
- **正文生产状态**：读 WS `useWorkflowSocket().status`；有 `incremental_backfill` 时显示 backfill 摘要

验收：

```bash
cd dashboard/frontend && pnpm exec vitest run tests/unit/chapters-page.spec.ts
```

---

## 11. Live e2e CI (F64)

Opt-in GitHub Actions workflow `.github/workflows/dashboard-e2e-live.yml`：

- 触发：`workflow_dispatch` 或 PR label `e2e-live`
- 命令：`LINGWEN_E2E_LIVE=1 pnpm e2e:live`（vite + `dashboard/e2e_entry.py`）
- **非** primary merge gate（primary 仍是 vitest CI）

### 11.1 F70 — e2e-live CI 首跑验证

**目标**: GitHub Actions `dashboard-e2e-live.yml` 与本地 CI 模拟一致、可绿。

**本地 CI 模拟**（与 workflow 同 env）:

```bash
cd novel-factory/dashboard/frontend
CI=true LINGWEN_E2E_LIVE=1 pnpm e2e:live
# 期望: 5 passed (decisions-resolve ×2 + ripples-audit ×3)
```

**一键脚本**（含 pip/pnpm/playwright install）:

```bash
bash novel-factory/scripts/verify-e2e-live-ci.sh
```

**GitHub 触发**:

1. Actions → **Dashboard E2E Live (opt-in)** → **Run workflow**（`workflow_dispatch`）
2. 或 PR 打 label **`e2e-live`**

**验收**: workflow 绿 + 5 tests passed；失败时 artifact `playwright-live-trace` 可下载。

**pytest 契约**:

```bash
pytest tests/ci/test_e2e_live_ci_f64.py tests/ci/test_e2e_live_f70_ci.py -q
```

---

## 12. 真实章节生产 pilot (F65)

**Gate**: `LINGWEN_REAL_LLM=1`（默认 off；CI 永不设置）

**推荐 env 组合**（生产 1 章 pilot）:

```bash
export LINGWEN_REAL_LLM=1
export LINGWEN_INCREMENTAL_BACKFILL=1
export LINGWEN_MEMORY_RAG=stub   # 首次 pilot 可用 stub；有 Qdrant 时改 live
export ANTHROPIC_API_KEY=sk-ant-...   # 或 MINIMAX / OPENAI
```

### 12.1 生产环境 checklist

| 检查项 | 要求 |
|--------|------|
| `LINGWEN_REAL_LLM=1` | 显式 opt-in（`real_llm_enabled()`） |
| API key | `MINIMAX_API_KEY` / `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` 至少一个 |
| state 目录 | `infra/.state/` 或 `--state-dir` 可写 |
| workflow | `infra/got/workflows/novel_writing.yaml` 存在 |
| Memory RAG | `stub`（0 Qdrant）或 `live`（需 Qdrant 环境） |
| Backfill | 可选 `LINGWEN_INCREMENTAL_BACKFILL=1` |

一键 preflight（**0 LLM**，不强制 REAL_LLM gate）:

```bash
cd novel-factory
python -m infra.agent_system.chapter_production_pilot --preflight-only --chapter-num 360
```

### 12.2 跑 1 章 pilot

```bash
cd novel-factory
python -m infra.agent_system.chapter_production_pilot --chapter-num 360
# exit 0 + JSON: emit_chapter_completed=true, total_cost_usd, incremental_backfill, ...
```

**说明**: `novel_writing` **无 DECISION 节点**，workflow 一次性跑至 `emit_chapter`（`paused=false`）。人审 pause/resume 仍用 §3 `chapter_golden` stub 验收。

### 12.3 pilot 记录模板

复制 `docs/templates/chapter-pilot-record.example.json`，填入实际 `total_cost_usd`、provider、backfill / memory 结果。

### 12.4 pytest（默认 0 真实 LLM）

```bash
pytest tests/agent_system/test_chapter_production_pilot.py -q
pytest tests/ci/test_chapter_production_pilot_f65_ci.py -q
```

Opt-in 真实 LLM preflight:

```bash
export LINGWEN_REAL_LLM=1 ANTHROPIC_API_KEY=...
pytest tests/agent_system/test_chapter_production_pilot.py::TestProductionPilotRealLlmOptIn -v
```

