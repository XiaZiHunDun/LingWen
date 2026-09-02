# Phase 23 — Pilot Page · 独立批章节流水线页面

> **状态**: 设计稿 · 待用户 review
> **日期**: 2026-09-02
> **作者**: Claude (brainstorming → design)
> **目标版本**: v23.0
> **作用域**: 后端轻触（cancel endpoint）+ 前端重构（独立页 + 5 组件 + 1 composable）

---

## 1. 背景与动机

**当前状态**:
- Backend 完备: `infra/studio_batch_runner.py` 提供 `start_batch_job` / `find_running_job` / `active_batch_job_for_project` / `get_batch_job` (含 log_tail) / `list_batch_jobs_for_slug`, 状态机 `running/completed/failed`, 通过 `LINGWEN_ALLOW_DASHBOARD_BATCH` env gate。
- Frontend 零散: Pilot 表面被埋在 `StudioPage.vue` 中（mode select + budget + preflight + batch cmd + job panel 一块），没有专门的 start/observe/cancel/history 闭环。
- 用户体验痛点: 想观察运行中 batch 的进度必须停留/刷新 StudioPage；想 cancel 必须 SSH 到机器 `kill -TERM <pid>`；历史无法集中查看。

**本阶段目标**:
- 把 Pilot 表面从 StudioPage 抽出成独立顶级页面 `PilotPage`
- 提供完整的 start → observe (live + ETA) → cancel → history 闭环
- 后端补齐 cancel endpoint (SIGTERM + 5s grace + SIGKILL fallback)
- 不引入 SSE/WebSocket（YAGNI，phase 24+ 按需补）

---

## 2. 架构与页面定位

### 2.1 页面入口

新增顶级页面 `PilotPage.vue`（与 StudioPage/ChaptersPage/WorkflowsPage 同级），侧边栏新增 `Pilot流水线` 入口。**不**嵌入 ProducePage（后者已 3 tabs，再加拥挤）。

### 2.2 模块结构

```
侧边栏导航
   ↓
PilotPage.vue (新顶级页)
   ├─ PilotStartForm.vue     ← mode/budget/chapters/preflight + Start 按钮
   ├─ PilotLivePanel.vue     ← active job + log_tail + ETA + Cancel
   └─ PilotHistoryList.vue   ← past jobs (status/范围/成本/退出码)
   ↓
usePilotBatch.ts (composable)
   ├─ state: activeJob, history, preflightRows, formState, *Error, *Loading
   ├─ actions: refreshActive / refreshHistory / runPreflight / startBatch / cancelBatch
   └─ auto polling: status==='running' → 每 3s refreshActive
   ↓
apps/dashboard/src/api/studio.ts (已有 + 新增)
   ├─ fetchStudioStartBatchJob(...) — 已有
   ├─ fetchStudioActiveBatchJob() — 已有
   ├─ fetchStudioBatchJob(id) — 已有
   ├─ listStudioBatchJobs(slug, limit) — 新增
   └─ cancelStudioBatchJob(id) — 新增
```

### 2.3 后端轻触（仅 3 处）

| 位置 | 改动 |
|---|---|
| `infra/studio_batch_runner.py` | 新增 `cancel_batch_job(job_id) -> BatchJob` |
| `apps/studio_api/routes/studio.py` | 新增 `POST /api/studio/batch/<job_id>/cancel` |
| `packages/lingwen-shared/src/lingwen_shared/contracts/python/studio.py` | 不变（`StudioBatchJobResponse.status` 已支持 `cancelled`，无需扩 DTO） |

### 2.4 复用

- `infra/studio_registry.batch_command` + `production_preflight` 不动
- `pilot_records.jsonl`（已有 per-chapter 记录）用于 ETA 计算，无需新增字段
- 现有 `apps/dashboard/src/api/studio.ts` 复用 + 2 wrapper 新增
- `PageLeadBar` / `HubPageHeader` / `HubEmptyGuide` / `StatCard` 等通用组件复用

### 2.5 架构不变量保持

- I001: `infra/` 不 import `apps/` ✓
- I002: 检查器纯函数（Pilot 不涉及）✓
- DP-02/03: 不需要新增 port ✓
- lint-imports 3 contracts KEPT（本次只新增内容，不改依赖关系）✓
- v22.0 已闭环的 12+ architecture invariants 全部保持

---

## 3. 组件与数据流

### 3.1 5 个新组件

| 组件 | 行数预估 | Props | 关键交互 |
|---|---|---|---|
| `PilotStartForm.vue` | ~150 | `preflightRows`, `preflightLoading`, `formState`, `disabled` | emit `submit-preflight` / `submit-start` |
| `PilotPreflightTable.vue` | ~80 | `rows: PreflightRow[]` | — |
| `PilotLivePanel.vue` | ~200 | `activeJob`, `eta`, `logTail` | emit `request-cancel` |
| `PilotCancelDialog.vue` | ~60 | `jobId`, `visible` | emit `confirm` / `hold-on` |
| `PilotHistoryList.vue` | ~150 | `history: BatchJobSummary[]` | emit `select-job` |

### 3.2 Composable 设计 — `usePilotBatch.ts`

**State (refs):**
- `activeJob: Ref<StudioBatchJobResponseDTO | null>`
- `history: Ref<StudioBatchJobSummaryDTO[]>`
- `preflightRows: Ref<PreflightRow[]>`
- `preflightLoading`, `startLoading`, `cancelLoading`, `preflightError`, `startError`, `cancelError`

**Lifecycle — auto polling:**
```ts
watch(activeJob, (job) => {
  if (job?.status === 'running') startPolling()
  else stopPolling()
})
```
- `startPolling()`: `setInterval(refreshActive, 3000)`
- `stopPolling()`: `clearInterval`, on unmount + status 变 terminal

**Actions:**
- `refreshActive(): Promise<void>` → `fetchStudioActiveBatchJob()`
- `refreshHistory(limit=20): Promise<void>` → `listStudioBatchJobs(currentSlug, limit)`
- `runPreflight(form: PilotForm): Promise<void>` → backend `production_preflight`
- `startBatch(form: PilotForm): Promise<void>` → `fetchStudioStartBatchJob(form)`
- `cancelBatch(jobId: string): Promise<void>` → `cancelStudioBatchJob(jobId)`

**Computed:**
- `etaSeconds: ComputedRef<number | null>` — 见 §4.3 ETA 算法
- `isJobActive: ComputedRef<boolean>` — `activeJob?.status === 'running'`

### 3.3 用户视角数据流

```
用户打开 /pilot
   ↓
usePilotBatch() onMounted
   ├─ refreshActive() → 显示已有 active job (或空状态)
   └─ refreshHistory() → 渲染历史表
   ↓
填表 → 点 Preflight → 后端返回 chapter-by-chapter 结果 → PilotPreflightTable 渲染
   ↓
Start 按钮启用 → 点 Start → POST /api/studio/batch/start → 拿到 job_id
   ↓
activeJob ref 更新 → watcher 触发 → polling (3s/次)
   ↓
LivePanel 显示 status=running + log_tail (40 lines) + ETA
   ↓
点 Cancel → CancelDialog → cancelBatch() → POST /api/studio/batch/<id>/cancel
   ↓
backend SIGTERM + 5s grace → status='cancelled' → polling 收敛
   ↓
LivePanel 显示 cancelled + log tail（含 SIGTERM 收尾）
```

### 3.4 新增 vs 复用

| 类型 | 新增 | 复用 |
|---|---|---|
| 页面 | `PilotPage.vue` | — |
| 组件 | 5 个 (`components/pilot/*`) | `PageLeadBar`, `HubPageHeader`, `HubEmptyGuide`, `StatCard`, `NDialog`, `NTabs`, `NTable` |
| Composable | `usePilotBatch.ts` | — |
| API wrapper | `cancelStudioBatchJob` + `listStudioBatchJobs` | 已有 start/active/get |
| 类型 | 0 | `StudioBatchJobResponseDTO` 已含 status 字段 |
| 状态 | — | — |

---

## 4. 错误处理与边界条件

### 4.1 前端错误处理

| 场景 | 表现 | 处理 |
|---|---|---|
| Preflight 失败 | PilotPreflightTable 显示 FAIL 行 + reason | Start 按钮 disabled, tooltip 提示 |
| 已有 job 在跑 (409) | form 顶部 banner "已有 job abc123 在运行" + 跳转链接 | — |
| env 禁用 (`LINGWEN_ALLOW_DASHBOARD_BATCH=0`) | 全部按钮 disabled + 顶部 banner 提示设置 env | — |
| startBatch 网络/5xx 失败 | form 显示 error, banner 显示 message, 按钮 re-enable | retry |
| preflight 网络/5xx 失败 | preflight error 区显示 message, form re-enable | retry |
| log_path 不存在 | log_tail 空 + 行内灰字 "log 文件已丢失" | 不报错 |
| cancel 失败 | Cancel dialog 显示 error + "job仍在运行" 提示 | 重试 |
| polling 网络中断 | 静默 1 次, 下次 retry; 连续 3 次失败 → "连接中断" banner + 手动 refresh 按钮 | — |
| ETA 无数据 (0 完成) | 显示 "等待首个 chapter 完成…" 灰字 | — |
| 页面卸载时 active job 仍在跑 | unmount 时 `stopPolling()`, job 在 backend 继续跑 | — |

### 4.2 后端 cancel 边界

| 场景 | 行为 |
|---|---|
| cancel 已 completed 的 job | 返回 409 "job 已完成, 无法取消" |
| cancel 已 cancelled 的 job | 返回 200 幂等, status 保持 cancelled |
| cancel 不存在的 job_id | 返回 404 |
| SIGTERM 后 5s 内进程未退 | 发送 SIGKILL 强杀, status='cancelled', error="force killed after 5s grace" |
| cancel 时 log_path 已删 | log_tail 空, 正常返回 |
| cancel 后 poll 显示仍在 running (race) | 下一次 `_poll_job` 读到 exit_code → status='cancelled', 自动收敛 |
| batch 启动后立刻 cancel | grace period 内可能还没写 PID 文件 → cancel 返回 409 "job 还在初始化中, 请稍后再试" |

### 4.3 Cancel 状态机

```
running ──cancel──> cancelling (5s grace) ──进程退──> cancelled
   │                    │
   │                    └─超时──> SIGKILL ──> cancelled (with error="force killed")
   ├─正常完成──> completed
   └─异常退出──> failed (exit_code != 0)
```

新增过渡态 `cancelling`（橙色 pill），5s 后自动刷新成 `cancelled`（或 force-killed cancelled）。

### 4.4 ETA 计算

```python
completed_chapters = count pilot_records.jsonl lines where chapter_num in [start, end]
elapsed_seconds = (now - started_at).total_seconds()
remaining_seconds = (total - completed) / (completed / elapsed) if completed > 0 else None
```

精度限制（接受）:
- 首个 chapter 完成前无 ETA（pilot_records 是事后写）
- cancel / failed 后不重算（status 变 terminal 后停止 ETA）
- 多 batch 同 slug（已 backend 拦截, UI 不需处理）

### 4.5 测试覆盖

| 测试文件 | 覆盖 |
|---|---|
| `tests/infra/test_studio_batch_runner_cancel.py` | cancel_batch_job 4 路径 (happy/409/404/SIGKILL timeout) |
| `tests/infra/test_studio_batch_runner_eta.py` | ETA helper 3 路径 (无完成/部分完成/完成) |
| `apps/dashboard/tests/unit/composables/use-pilot-batch.spec.ts` | state 转移 + polling 启停 + cancel flow + ETA mock |
| `apps/dashboard/tests/unit/pages/pilot-page.spec.ts` | 4 主路径渲染 + 错误 banner 显隐 |
| `apps/dashboard/tests/unit/components/pilot/*.spec.ts` | 每个组件 3-5 用例 |
| `apps/dashboard/tests/unit/api/cancel-studio-batch-job.spec.ts` | URL 契约 |
| `apps/dashboard/tests/unit/api/list-studio-batch-jobs.spec.ts` | URL 契约 |

---

## 5. 提交结构（预计 13-15 commits）

按 Phase 126 v16.x 节奏：atomic 1-task-per-commit。

### Part A — Backend (4 commits)

| # | Commit | 内容 |
|---|---|---|
| A1 | `feat(studio-api): POST /api/studio/batch/<job_id>/cancel route` | route + 404/409 边界 |
| A2 | `feat(studio-batch-runner): cancel_batch_job()` | SIGTERM + 5s grace + SIGKILL fallback |
| A3 | `test(studio-batch-runner): cancel 4 paths` | 4 个 pytest (happy/409/404/timeout) |
| A4 | `test(studio-api): cancel route integration` | 3 个 FastAPI test |

### Part B — Frontend API wrapper (2 commits)

| # | Commit | 内容 |
|---|---|---|
| B1 | `feat(api): cancelStudioBatchJob wrapper + URL contract tests` | 6 URL 测试 |
| B2 | `feat(api): listStudioBatchJobs wrapper + URL contract tests` | 4 URL 测试 |

### Part C — Composable (1 commit)

| # | Commit | 内容 |
|---|---|---|
| C1 | `feat(composables): usePilotBatch()` | state + actions + polling + ETA computed + 8 单元测试 |

### Part D — Components (5 commits)

| # | Commit | 内容 |
|---|---|---|
| D1 | `feat(components): PilotStartForm.vue + PilotPreflightTable.vue` | form + table + 8 测试 |
| D2 | `feat(components): PilotLivePanel.vue` | live + log tail + ETA 显示 + 5 测试 |
| D3 | `feat(components): PilotCancelDialog.vue` | 二次确认 + grace 倒计时 + 3 测试 |
| D4 | `feat(components): PilotHistoryList.vue` | 历史表 + 展开 log + 4 测试 |
| D5 | `chore(ruff): ruff --fix for any I001 import sort` | 单一清理 commit (按需) |

### Part E — Page wiring (2 commits)

| # | Commit | 内容 |
|---|---|---|
| E1 | `feat(pages): PilotPage.vue` | 4 组件组合 + 4 路径 page test |
| E2 | `feat(nav): Pilot sidebar entry + dashboardNav config` | 1 个 nav 测试 |

### Part F — Cleanup + docs (2 commits)

| # | Commit | 内容 |
|---|---|---|
| F1 | `refactor(studio-page): remove embedded pilot section` | 旧 form / job panel 从 StudioPage 删, 由 PilotPage 替代 |
| F2 | `docs(phase-23): handoff + CLAUDE.md v23.0 + architecture.yml` | lessons + carryover |

**总计**: 16 commits (4+2+1+5+2+2), 匹配 Phase 126 v16.2.x 节奏（10-20 commits/phase）。D1 涵盖 2 个组件（StartForm + PreflightTable 共享 form 子结构），其他组件 1-file-per-commit。

---

## 6. 风险矩阵

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| cancel 误杀其他进程 (PID 复用) | 低 | 高 | cancel 用 `_load_job` 拿到 pid 后立刻 `os.kill(pid, 0)` 验证 alive 才发 SIGTERM |
| polling 风暴 (3s × N 用户) | 低 | 中 | 仅 `status==='running'` 才 polling; stopPolling 在 status 变 terminal 时跑; page unmount cleanup |
| Pilot 与 Cascade 命名冲突 (cvg.py 也有 cancel) | 低 | 低 | URL 路径独立 `/api/studio/batch/<id>/cancel` vs `/api/cvg/cascade/run/<id>/cancel`, 不冲突 |
| 新文件超 lint 800 行 | 中 | 低 | 每个组件控制在 100-250 行; composable ≤ 300 行; 超则拆 |
| PilotPage 在 dashboardNav 中路径冲突 | 低 | 低 | nav key 用 `'pilot'`, 复用现有 `DASHBOARD_NAV_ENTRIES` 模式 |
| rebase 冲突 (跟 master) | 极低 | 低 | Phase 22 merged, master clean, 本 phase 工作在 worktree |
| ruff I001 新 import | 中 | 低 | 收尾前 `ruff --fix` 单独 commit |
| PilotPage 导致 knip 误报 unused | 低 | 低 | nav entry + page 都直接 export, 无 dead code |

### 回退策略

- **A1-A4** backend: 完全独立, 无外部 consumer 改动; revert 单 commit 即可
- **B1-B2** API: 仅新增 wrapper, 无旧路径迁移; revert 安全
- **C1-D5** composable + 组件: 新文件, 删文件即回退
- **E1-E2** page + nav: nav 加 entry 是 append, revert 即从 sidebar 隐藏
- **F1** StudioPage cleanup: 本阶段唯一带 risk 的步骤, revert 即可恢复

---

## 7. 范围排除 (YAGNI)

- SSE / WebSocket 实时推送 (phase 24+ 按需补)
- per-chapter live preview (pilot_records 已是事后记录, 不动 schema)
- 自动恢复 / 断点续传 (cancel 后重起新 batch 是当前 pattern)
- multi-project 并发 batch (backend 已通过 slug 拦截)
- 失败自动 retry
- batch job 优先级 (目前是 FIFO per slug)

---

## 8. 性能预算

| 指标 | 预算 |
|---|---|
| PilotPage TTI (dev) | < 1.5s |
| PilotPage TTI (prod) | < 800ms |
| polling 频率 | 3s (仅 active 时) |
| polling 单请求耗时 | < 200ms (fetchStudioActiveBatchJob 已知 ~30ms) |
| log_tail size | 40 lines (已有 backend 默认) |

---

## 9. 与现有债务的关系

- **Phase 114 prod preview** (accepted): 不影响 dev baseline, 本 phase 全在 dev 跑
- **SSE/实时** (YAGNI): 本 phase 显式排除, carryover 到 phase 24+ 如需要
- **per-chapter progress** (backend 没字段): ETA 靠 pilot_records join 实现, 不动 BatchJob schema
- **multi-project concurrent batches**: backend 已通过 slug 拦截, 前端不需要处理

---

## 10. 验证门（Phase 23 closure gates）

- vitest 1762+ pass + N new (新组件/composable/page 测试)
- vue-tsc 0
- ESLint 0
- knip `{"issues":[]}`
- ruff clean (`ruff check` + `ruff format --check`)
- lint-imports 3 contracts KEPT (315+ files)
- new pytest: cancel 4 + ETA 3 = 7+ 通过
- 手动验证: 启动 Pilot batch → cancel → 看到 cancelled 状态; preflight FAIL 不让 start

---

## 11. 实施后结构变更

```
apps/dashboard/src/
├── pages/
│   └── PilotPage.vue               ← NEW
├── components/
│   └── pilot/                      ← NEW
│       ├── PilotStartForm.vue
│       ├── PilotPreflightTable.vue
│       ├── PilotLivePanel.vue
│       ├── PilotCancelDialog.vue
│       └── PilotHistoryList.vue
├── composables/
│   └── usePilotBatch.ts            ← NEW
└── api/
    └── studio.ts                   ← +2 wrappers

apps/studio_api/routes/
└── studio.py                       ← +1 route

infra/
└── studio_batch_runner.py          ← +cancel_batch_job

packages/lingwen-shared/src/lingwen_shared/contracts/python/
└── studio.py                       ← 不变

tests/infra/
├── test_studio_batch_runner_cancel.py  ← NEW
└── test_studio_batch_runner_eta.py     ← NEW
```

---

## 12. Carryover to Phase 24+

- SSE/WebSocket 推 batch 状态 (如需)
- per-chapter preview (在 PilotPage 内嵌 chapter preview drawer)
- batch 模板（保存常用 mode/budget/chapters 组合）
- batch 优先级队列
- 多 LLM provider 并发 batch（不同 chapter 用不同 provider）
- 与 Insight 仪表盘集成（把 active batch 进度嵌入 Insight page）
- 与 Decisions 联动（batch 完成后生成 decisions）

---

## 13. Open Questions (无)

设计已与用户 4 段对话收敛：架构 → 组件 → 错误处理 → 提交节奏。用户已 OK 全部 4 段。