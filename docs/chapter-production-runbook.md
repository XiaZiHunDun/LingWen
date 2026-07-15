# 正文生产 Runbook（Phase 9.67 F59）

> **目标**: 可复制的一章生产路径 — 从 workflow 触发到人工决策、恢复执行，以及可选的 CVG 增量 backfill。  
> **约束**: 默认 **0 真实 LLM**；验收用 stub golden path。

---

## 1. 状态目录与环境变量

| 路径 / 变量 | 用途 |
|------------|------|
| `infra/.state/decisions.json` | 人工决策队列（HumanDecisionQueue） |
| `.state/cross_volume.db` | CVG ripple / reference graph |
| `infra/.state/` | 其它 agent 状态（按 MC 配置） |
| `LINGWEN_INCREMENTAL_BACKFILL=1` | workflow 完成后 opt-in 增量 backfill（F54） |
| `LINGWEN_REAL_LLM=1` | **仅**显式 opt-in 真实 LLM（勿在 CI 默认开） |

---

## 2. 生产路径（`novel_writing`）

### 2.1 启动章节 workflow

```bash
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
cd dashboard/frontend
CI=true LINGWEN_E2E_LIVE=1 pnpm e2e:live
# 期望: 5 passed (decisions-resolve ×2 + ripples-audit ×3)
```

**一键脚本**（含 pip/pnpm/playwright install）:

```bash
bash scripts/verify-e2e-live-ci.sh
```

**GitHub 触发**:

1. Actions → **Dashboard E2E Live (opt-in)** → **Run workflow**（`workflow_dispatch`）
2. 或 PR 打 label **`e2e-live`**

**验收**: workflow 绿 + 5 tests passed；失败时 artifact `playwright-live-trace` 可下载。

**pytest 契约**:

```bash
pytest tests/ci/test_e2e_live_ci_f64.py tests/ci/test_e2e_live_f70_ci.py -q
```

### 11.2 F76 — Remote e2e-live 首绿 checklist

**目标**: GitHub Actions 远程首跑可重复、可诊断（本地 F70 parity 已通过）。

**Workflow 页面**: `https://github.com/XiaZiHunDun/LingWen/actions/workflows/dashboard-e2e-live.yml`

**一键打印 checklist**（0 网络）:

```bash
bash scripts/e2e-live-remote-checklist.sh
```

**推荐首跑顺序**:

| 步骤 | 动作 | 通过标准 |
|------|------|----------|
| 1 | 本地 `verify-e2e-live-ci.sh` | exit 0 · 5 passed |
| 2 | Actions → **Run workflow**（master） | job 绿 |
| 3 | 打开 run **Summary** | 见 “Dashboard E2E Live — passed” |
| 4 | （可选）开 PR + label `e2e-live` | 同 job 绿 |

**失败排查**:

1. 下载 artifact `playwright-live-trace`
2. 本地复现: `bash scripts/verify-e2e-live-ci.sh`
3. 常见: pnpm lock 漂移 · Playwright browser 未装 · port 8765/5173 占用（仅本地）

**Badge**（可选 README）: opt-in workflow，**不**并入 primary merge gate。

**pytest 契约**:

```bash
pytest tests/ci/test_e2e_live_f76_ci.py -q
```

### 11.3 F82 — Remote e2e-live 首绿确认记录

**目标**: 在 F76 checklist 基础上，**记录** GitHub Actions 首次全绿 run（manual gate）。

**前置**: 本地 parity 已通过（步骤 1）。

**确认步骤**:

| 步骤 | 动作 | 记录字段 |
|------|------|----------|
| 1 | `bash scripts/verify-e2e-live-ci.sh` | `local_parity.passed=true` |
| 2 | Actions → **Run workflow**（master） | `github_run_id` / `github_run_url` |
| 3 | Job 绿 + Summary 含 **Dashboard E2E Live — passed** | `summary_phrase` |
| 4 | （可选）复制 stub 填真实 run | `docs/templates/e2e-live-first-green.stub.example.json` |

**记录存放**（gitignored，可选）: `infra/.state/ci_records/e2e-live-first-green.json`

**一键打印 F82 确认清单**（0 网络）:

```bash
bash scripts/e2e-live-first-green-checklist.sh
```

**pytest 契约**:

```bash
pytest tests/ci/test_e2e_live_f82_ci.py -q
```

### 11.4 F90 — e2e-live 首绿 JSON 记录写入

**目标**: 在 F82 checklist 基础上，用脚本把 stub 字段写入 `ci_records`（local parity manual gate）。

**前置**: 本地 parity 已通过（`verify-e2e-live-ci.sh` exit 0）。

**写入步骤**:

| 步骤 | 动作 | 说明 |
|------|------|------|
| 1 | `bash scripts/verify-e2e-live-ci.sh` | 5/5 live-backend e2e |
| 2 | **仅本地记录**（待远程 run 后更新 id/url） | `--local-only` |
| 3 | **远程首绿后** | 填真实 `github_run_id` / `github_run_url` |
| 4 | 校验 | `pytest tests/agent_system/test_ci_records.py -q` |

**一键写入**（local parity 已绿，占位 run id）:

```bash
bash scripts/write-e2e-live-first-green-record.sh --local-only
```

**含 verify + 写入**:

```bash
bash scripts/write-e2e-live-first-green-record.sh --from-verify --local-only
```

**远程首绿后更新**:

```bash
bash scripts/write-e2e-live-first-green-record.sh \
  --github-run-id 1234567890 \
  --github-run-url 'https://github.com/XiaZiHunDun/LingWen/actions/runs/1234567890' \
  --operator your-handle
```

**记录路径**（gitignored）: `infra/.state/ci_records/e2e-live-first-green.json`

**首绿参考**（2026-06-22）:

| commit | run | job |
|--------|-----|-----|
| `9132168` | [`27928203388`](https://github.com/XiaZiHunDun/LingWen/actions/runs/27928203388) | Playwright live-backend 5/5 |
| `67c8ad8` | [`27928469270`](https://github.com/XiaZiHunDun/LingWen/actions/runs/27928469270) | 维护对齐 · test 全绿 |

**模块**: `infra/agent_system/ci_records.py` · `validate_e2e_live_first_green_record()`

**pytest 契约**:

```bash
pytest tests/ci/test_e2e_live_f90_ci.py tests/agent_system/test_ci_records.py -q
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
python -m infra.agent_system.chapter_production_pilot --preflight-only --chapter-num 360
```

### 12.2 跑 1 章 pilot

```bash
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

---

## 13. Manual pilot 执行与记录 (F72)

**前提**: §12 preflight 全绿 + 主公人工审章。

### 13.1 跑 pilot 并自动写记录

```bash
export LINGWEN_REAL_LLM=1
export LINGWEN_INCREMENTAL_BACKFILL=1
export LINGWEN_MEMORY_RAG=stub
export ANTHROPIC_API_KEY=sk-ant-...

python -m infra.agent_system.chapter_production_pilot \
  --chapter-num 360 \
  --save-record infra/.state/pilot_records/ch360.json \
  --operator your-name
# exit 0 + record JSON 写入 PATH
```

`--save-record` 可在 preflight-only 模式下写入 checklist 快照（用于调试）:

```bash
python -m infra.agent_system.chapter_production_pilot \
  --preflight-only \
  --save-record /tmp/preflight-ch360.json
```

### 13.2 人工审章 checklist

| 项 | 通过标准 |
|----|----------|
| `emit_chapter_completed` | `true` |
| `total_cost_usd` | 在 per-run budget 内（Dashboard Settings 只读） |
| `incremental_backfill` | 若开启： `nodes_written >= 1` 或 dry_run 符合预期 |
| `memory_context_source` | `stub` 或 `live` 与 env 一致 |
| 正文质量 | 人工读 emit 产出（不在 JSON 记录内） |

脱敏示例: `docs/templates/chapter-pilot-record.stub.example.json`

### 13.3 pytest

```bash
pytest tests/agent_system/test_chapter_production_pilot.py -q -k "PilotRecord"
pytest tests/ci/test_chapter_production_pilot_f72_ci.py -q
```

---

## 14. 批量章节生产 (F73)

**Gate**: 同 §12 `LINGWEN_REAL_LLM=1` · 顺序跑 **1–10 章** · stop-on-fail · 可选累计 `--budget-usd`

### 14.1 CLI

```bash
export LINGWEN_REAL_LLM=1 LINGWEN_INCREMENTAL_BACKFILL=1 LINGWEN_MEMORY_RAG=stub
export MINIMAX_API_KEY=...

# preflight（0 LLM）
python -m infra.agent_system.chapter_production_batch \
  --preflight-only --start-chapter 361 --max-chapters 3

# 跑 3 章 + 写 batch summary
python -m infra.agent_system.chapter_production_batch \
  --start-chapter 361 --max-chapters 3 --budget-usd 0.15 \
  --save-summary infra/.state/pilot_records/batch-361-363.json \
  --save-chapter-records-dir infra/.state/pilot_records/
```

| 参数 | 说明 |
|------|------|
| `--start-chapter` | 起始章号 |
| `--max-chapters` | 1–10，默认 3 |
| `--budget-usd` | 累计成本硬停（跑完一章后检查，超限不再开下一章） |
| `--save-summary` | batch JSON（含每章 PilotResult） |
| `--save-chapter-records-dir` | 每章 `chNNN.json` pilot 记录 |

### 14.2 stopped_reason

| 值 | 含义 |
|----|------|
| `completed` | 计划章数全部成功 |
| `chapter_failed` | 某一章 emit 失败 / error，后续不再跑 |
| `budget_exceeded` | 累计 cost ≥ budget，停止 |
| `preflight_failed` | checklist 未通过 |

### 14.3 pytest

```bash
pytest tests/agent_system/test_chapter_production_batch.py -q
pytest tests/ci/test_chapter_production_batch_f73_ci.py -q
```

---

## 15. Manual batch pilot 执行与记录 (F79)

**前提**: §14 preflight 全绿 · 已有 §13 单章 pilot 经验（推荐先跑 1 章）。

### 15.1 跑 3 章 batch 并写记录

```bash
export LINGWEN_REAL_LLM=1
export LINGWEN_INCREMENTAL_BACKFILL=1
export LINGWEN_MEMORY_RAG=stub
export MINIMAX_API_KEY=...

python -m infra.agent_system.chapter_production_batch \
  --start-chapter 361 --max-chapters 3 --budget-usd 0.15 \
  --save-summary infra/.state/pilot_records/batch-361-363.json \
  --save-chapter-records-dir infra/.state/pilot_records/ \
  --operator your-name
# exit 0 · stopped_reason=completed · chapters_succeeded=3
```

### 15.2 验收 checklist

| 项 | 通过标准 |
|----|----------|
| `stopped_reason` | `completed`（非 `chapter_failed` / `budget_exceeded`） |
| `chapters_succeeded` | 等于 `chapters_attempted` |
| `total_cost_usd` | ≤ `--budget-usd`（若设置） |
| 每章 `emit_chapter_completed` | 全部为 `true` |
| per-chapter JSON | `--save-chapter-records-dir` 下 `chNNN.json` 与 summary 一致 |
| 正文质量 | 人工审 361–363 emit 产出 |

**2026-06-11 首跑参考** (MiniMax M2.7, stub memory):

| 章 | cost (USD) | emit |
|----|------------|------|
| 361 | ~0.025 | ✅ |
| 362 | ~0.027 | ✅ |
| 363 | ~0.030 | ✅ |
| **合计** | **~0.083** / budget 0.15 | 3/3 |

脱敏 batch 示例: `docs/templates/chapter-batch-record.stub.example.json`

### 15.3 pytest

```bash
pytest tests/ci/test_chapter_production_batch_f73_ci.py -q
pytest tests/ci/test_chapter_production_batch_f79_ci.py -q
```

---

## 16. Batch dry-run 与成本预估 (F80)

**目标**: 真实 LLM 开跑前，输出章节范围 + 预估成本上限（基于 F79 校准或历史 batch JSON）。

### 16.1 `--dry-run`

需 `LINGWEN_REAL_LLM=1`（与真实 batch 同 gate），**0 LLM**。

```bash
export LINGWEN_REAL_LLM=1 LINGWEN_INCREMENTAL_BACKFILL=1 LINGWEN_MEMORY_RAG=stub
export MINIMAX_API_KEY=...

python -m infra.agent_system.chapter_production_batch \
  --dry-run --start-chapter 364 --max-chapters 3 --budget-usd 0.15 \
  --calibrate-from infra/.state/pilot_records/batch-361-363.json
# stopped_reason=dry_run · batch_plan 含 chapter_range / estimated_total_cost_usd
```

| `batch_plan` 字段 | 说明 |
|-----------------|------|
| `chapter_range` | 如 `364-366` |
| `cost_per_chapter_usd` | 默认 F79 均值 (~0.0276)；可被 env / calibrate 覆盖 |
| `estimated_total_cost_usd` | `cost_per_chapter × max_chapters` |
| `estimated_chapters_within_budget` | budget 内预计可跑满章数 |
| `budget_headroom_usd` | budget − 预估总成本 |
| `calibration_source` | `default:F79-ch361-363` / `calibrated:…` / `env:…` |

**校准优先级**: `LINGWEN_BATCH_COST_ESTIMATE_USD` env → `--calibrate-from` batch JSON → F79 默认。

### 16.3 Studio DoD · budget cap 与校准（12.12）

Studio batch（`verify-studio-production-dod.sh --real-llm-batch`）**默认不设** `--budget-usd`（DoD D 3/3 · ~$0.19）。

带 cap 时须 `--calibrate-from` 或脚本自动选最新 `studio-dod-batch*.json`；F79 默认 (~$0.028/章) 低于 Studio MiniMax 实测 (~**$0.063**/章)，易触发 `budget_exceeded`。

| 来源 | ~$/章 | 适用 |
|------|-------|------|
| F79 默认 | 0.028 | 星陨 stub batch |
| studio-dod-batch JSON | 0.063 | Studio 新书 |
| `batch-367-376.json` | 0.028 | 星陨 10 章 wave |

`--preflight-only` 同样附带 `batch_plan`（不要求 REAL_LLM gate）。

### 16.2 pytest

```bash
pytest tests/agent_system/test_chapter_production_batch.py -q -k "dry_run or calibrate or batch_plan"
pytest tests/ci/test_chapter_production_batch_f80_ci.py -q
```

---

## 17. Batch 续跑 364–366 (F84)

**前提**: F79 batch 361–363 已成功 · 建议先 `--dry-run`（§16）。

```bash
export LINGWEN_REAL_LLM=1 LINGWEN_INCREMENTAL_BACKFILL=1 LINGWEN_MEMORY_RAG=stub
export MINIMAX_API_KEY=...

python -m infra.agent_system.chapter_production_batch \
  --dry-run --start-chapter 364 --max-chapters 3 --budget-usd 0.15 \
  --calibrate-from infra/.state/pilot_records/batch-361-363.json

python -m infra.agent_system.chapter_production_batch \
  --start-chapter 364 --max-chapters 3 --budget-usd 0.15 \
  --save-summary infra/.state/pilot_records/batch-364-366.json \
  --save-chapter-records-dir infra/.state/pilot_records/ \
  --operator your-name
```

**2026-06-11 首跑参考** (MiniMax M2.7, stub memory):

| 章 | cost (USD) | emit |
|----|------------|------|
| 364 | ~0.032 | ✅ |
| 365 | ~0.025 | ✅ |
| 366 | ~0.024 | ✅ |
| **合计** | **~0.081** / budget 0.15 | 3/3 |

**累计 (360–366)**: ch360 pilot + batch 361-363 + batch 364-366 ≈ **$0.19**（Analytics rollup 去重后可见）。

### 17.1 pytest

```bash
pytest tests/ci/test_chapter_production_batch_f84_ci.py -q
```

---

## 18. 10 章 wave 预检（367–376, F85）

**目标**: 在首次 `--max-chapters 10` 真实 LLM 跑批前，固定 wave  playbook + dry-run 预算。

**Wave 定义**: 起始 **367**，连续 **10 章** → `367-376`（`MAX_BATCH_CHAPTERS=10`）。

### 18.1 一键 dry-run

```bash
export LINGWEN_REAL_LLM=1 LINGWEN_INCREMENTAL_BACKFILL=1 LINGWEN_MEMORY_RAG=stub
export MINIMAX_API_KEY=...

# 默认: start=367 max=10 budget=0.30；校准 batch-364-366.json（fallback 361-363）
bash scripts/batch-wave-dry-run.sh
# 或显式: bash scripts/batch-wave-dry-run.sh 367 10 0.35
```

**推荐 budget 档位**（基于 F84 校准 ~$0.027/章）:

| `--budget-usd` | 说明 |
|---------------|------|
| **0.28** | 紧预算（约 10 章预估，少 headroom） |
| **0.30** | **默认**（~10 章 + 小幅余量） |
| **0.35** | 宽松（含 polish JSON fallback 波动） |

**2026-06-11 dry-run 参考**（calibrate `batch-364-366.json`）:

| 项 | 值 |
|----|-----|
| `chapter_range` | 367-376 |
| `estimated_total_cost_usd` | ~$0.269 |
| `estimated_chapters_within_budget` | 10 @ $0.30 |
| `budget_headroom_usd` | ~$0.031 @ $0.30 |

### 18.2 真实 wave 执行（manual gate，非 F85 默认跑）

**2026-06-12 首跑 ✅**：`batch-367-376.json` · **10/10** · ~**$0.283** · stub memory · 正文已落盘 `ch367–376.md`。

确认 dry-run 后（续跑 / 重跑）：

```bash
python -m infra.agent_system.chapter_production_batch \
  --start-chapter 367 --max-chapters 10 --budget-usd 0.30 \
  --save-summary infra/.state/pilot_records/batch-367-376.json \
  --save-chapter-records-dir infra/.state/pilot_records/ \
  --operator your-name
```

**运维注意**:
- stop-on-fail：任一章失败则停止，需人工审后再开下一 wave
- 建议 wave 间留 **人工审章** 窗口，不要连续无人值守 10 章
- 脱敏 wave 计划: `docs/templates/chapter-batch-wave.stub.example.json`

### 18.3 pytest

```bash
pytest tests/ci/test_chapter_production_batch_f85_ci.py -q
```

---

## 19. MEMORY_RAG=live 单章 pilot (F86 + F89 Embedding Provider)

**目标**: 用 **真实 MemoryGateway**（Qdrant + 可插拔 Embedder）跑 1 章 pilot，验证 `memory_context_source=live`。

### 19.1 前置条件

| 项 | 要求 |
|----|------|
| Qdrant | 默认 `http://127.0.0.1:6333` 可访问 |
| **Embedding** | `memory_config.yaml` → `embedding.provider: auto`（F89） |
| | **auto**：有 `OPENAI_API_KEY` → OpenAI；**仅** `MINIMAX_API_KEY` → MiniMax embo-01（beta） |
| | 显式覆盖：`LINGWEN_EMBEDDING_PROVIDER=openai\|minimax` |
| | 国内 MiniMax embedding 建议 `MINIMAX_GROUP_ID` |
| `MINIMAX_API_KEY`（或 Anthropic） | novel_writing **LLM**（与 embedding 可共用 MiniMax key） |
| `LINGWEN_MEMORY_RAG=live` | 显式开启 live hook |
| Preflight | `embedding_provider_keys` + `memory_rag_live_gateway` **required** |

> **F89 变更**：live RAG **不再硬绑** `OPENAI_API_KEY`；仅 MiniMax key 时可走 `provider=minimax`（API 可用性需 manual 验证）。

### 19.2 一键 preflight

```bash
export LINGWEN_REAL_LLM=1
export LINGWEN_MEMORY_RAG=live
export LINGWEN_EMBEDDING_PROVIDER=minimax   # 仅 MiniMax key 时建议显式指定
export MINIMAX_API_KEY=...
export MINIMAX_GROUP_ID=...                 # 国内 endpoint 常需

bash scripts/memory-rag-live-preflight.sh 367
```

OpenAI embedding 路径（与 F86 前兼容）：

```bash
export LINGWEN_EMBEDDING_PROVIDER=openai
export OPENAI_API_KEY=sk-...
export MINIMAX_API_KEY=...    # LLM
bash scripts/memory-rag-live-preflight.sh 367
```

### 19.3 跑 live pilot 并写记录

```bash
python -m infra.agent_system.chapter_production_pilot \
  --chapter-num 367 \
  --save-record infra/.state/pilot_records/ch367-live-rag.json \
  --operator your-name \
  --pilot-id 2026-06-11-ch367-live-rag-001
# 验收: memory_context_source=live · emit_chapter_completed=true
```

脱敏示例: `docs/templates/chapter-pilot-live-rag.stub.example.json`

**与 stub 对比**: F72/F84 用 `LINGWEN_MEMORY_RAG=stub`；live 必须 Gateway **非 NoOp** 且 embedder probe 通过。

### 19.4 pytest

```bash
pytest tests/memory_system/test_embedding_factory.py -q
pytest tests/memory_system/test_minimax_embedding_provider.py -q
pytest tests/ci/test_embedding_provider_f89_ci.py -q
pytest tests/agent_system/test_chapter_memory_hook.py -q -k gateway_check
pytest tests/ci/test_chapter_memory_rag_live_f86_ci.py -q
```

### 19.5 ch367 live pilot 结果

| 日期 | pilot_id | memory | 节点 | 成本 | emit 落盘 |
|------|----------|--------|------|------|-----------|
| 2026-06-11 | `2026-06-11-ch367-live-rag-001` | live · MiniMax embo-01 | 7/7 | ~$0.022 | ✅ |
| **2026-06-22** | `2026-06-22-ch367-live-rag-001` | live · Qdrant OK | 7/7 | ~$0.032 | **`LINGWEN_EMIT_CHAPTER=0`**（仅验 live hook，不改 ch367 正文） |

记录：`infra/.state/pilot_records/ch367-live-rag.json`（gitignored，后跑覆盖前跑）。

**2026-06-11 已知**：当时 Qdrant client 1.18 仍调用已废弃的 `.search()`；已在后续修复为 `query_points`（见 §19.6）。

### 19.6 Qdrant client 1.18+ 检索（post ch367 fix）

- `QdrantClientWrapper` 优先 `query_points`，旧 client 仍走 `.search()`
- `memory_config.yaml` → `qdrant.check_compatibility: false` 抑制版本告警
- **向量库需有数据**：先 `python -m infra.memory_system.scripts.init_memory` 创建 `chapters_seg` 等集合，再 `embed_chapters` 写入向量；空库时 live hook 仍成功但 `related_segments=[]`

```bash
python -m infra.memory_system.scripts.init_memory
python -m infra.memory_system.scripts.embed_chapters \
  --start 350 --end 360 \
  --create-collection \
  --resume
export LINGWEN_EMBEDDING_PROVIDER=minimax   # 或 openai
```

**注意**：361–367 正文若尚未落盘到 `03_内容仓库/04_正文/`，只能 embed 已有章节（2026-06-11 为 ch350–360）；ch367 live pilot 的 `related_segments` 会语义检索邻近已 embed 章节。

**验证**（post embed 2026-06-11）：

```bash
python - <<'PY'
import infra.memory_service as ms
ms._memory_gateway = None
from infra.memory_service import get_memory_gateway
ctx = get_memory_gateway().auto_push_context(367)
print(len(ctx.get("related_segments", [])))  # 期望 >0
PY
```

