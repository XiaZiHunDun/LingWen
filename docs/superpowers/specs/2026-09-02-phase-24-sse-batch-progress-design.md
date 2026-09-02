# Phase 24 — SSE Real-time Batch Progress · Design

> **Status**: 设计稿 · 待用户 review
> **日期**: 2026-09-02
> **目标版本**: v24.0
> **作用域**: 后端 SSE endpoint + 前端 EventSource composable + 替换 Phase 23 3s polling

---

## 1. 背景与动机

**当前状态** (post Phase 23):
- `usePilotBatch` composable 用 `setInterval(refreshActive, 3000)` 每3秒轮询 `fetchStudioActiveBatchJob()`
- 轮询限制: 3s 延迟, N users × 3s × backend fetches = 流量放大
- Phase 23 handoff 第1项 carryover: "SSE/WebSocket real-time progress (replace 3s polling with push)"

**本阶段目标**:
- 后端新增 SSE endpoint 实时推 batch 状态 (job_state + per-chapter events)
- 前端 `useBatchEventStream` composable 用浏览器原生 EventSource API 接收事件
- 替换 Phase 23 3s polling(保留短时 fallback polling 作为 SSE 失败的 bridge)
- 5 NEW events: `job_state` / `chapter_started` / `chapter_completed` / `job_completed` / `job_failed` / `job_cancelled`

---

## 2. 架构与端点形态

### 2.1 端点

**`GET /api/studio/batch/<job_id>/events`**
- Response: FastAPI `StreamingResponse(generator(), media_type="text/event-stream")`
- Headers: `Cache-Control: no-cache`, `X-Accel-Buffering: no` (nginx-friendly), `Connection: keep-alive`
- Error responses (non-streaming):
  - 404 — job_id 不存在
  - 403 — 当前 session 无权访问该 project
  - 401 — 未登录
- Heartbeat: 每15s 推 `: ping\n\n` 防止 intermediate proxy timeout

### 2.2 事件 schema (SSE-formatted)

```
event: job_state
data: {"status": "running", "mode": "pilot", "start_chapter": 1, "end_chapter": 10, "started_at": "2026-09-02T00:00:00+00:00", "log_tail": "..."}

event: chapter_started
data: {"chapter_num": 5, "started_at": "2026-09-02T00:01:00+00:00"}

event: chapter_completed
data: {"chapter_num": 5, "completed_at": "2026-09-02T00:02:30+00:00", "duration_sec": 90.4}

event: job_completed
data: {"exit_code": 0, "finished_at": "...", "total_chapters": 10, "duration_sec": 360.0}

event: job_failed
data: {"exit_code": 1, "error": "...", "finished_at": "..."}

event: job_cancelled
data: {"finished_at": "...", "error": "force killed after 5s grace"}
```

### 2.3 后端模块

**`infra/studio_batch_streamer.py`** (NEW, ~200 行):
- `BatchEventPublisher` (module-level singleton, thread-safe): 
  - `publish(job_id: str, event_type: str, payload: dict)` — non-blocking, fire-and-forget
  - `subscribe(job_id: str) -> AsyncIterator[bytes]` — yields SSE-formatted bytes
  - Per-job subscriber list + asyncio.Queue per subscriber (cap 100 events, drop oldest)
  - `unsubscribe(job_id, queue)` — cleanup on client disconnect
- `BatchEventStreamer` (FastAPI endpoint class):
  - On connect: validate job exists, auth check, send initial `job_state` event from disk JSON
  - Forward publisher events as SSE
  - 15s heartbeat loop
  - On terminal event: close generator (FastAPI cleans up)
  - finally: unsubscribe

### 2.4 Hook points in `infra/studio_batch_runner.py`

- `start_batch_job` 末尾 → `publish("job_started", {start_ch, end_ch, mode, budget_usd})`
- `_poll_job` 检测到 `_process_running == False` → `publish("job_completed" | "job_failed", {exit_code, finished_at})`
- `cancel_batch_job` 末尾 → `publish("job_cancelled", {finished_at, error})`
- pilot_records.jsonl append 后 → `publish("chapter_completed", {chapter_num, completed_at, duration_sec})`

### 2.5 前端模块

**`apps/dashboard/src/composables/useBatchEventStream.ts`** (NEW, ~120 行):
- Input: `jobId: Ref<string | null>`
- Output: 
  - `events: Ref<BatchEvent[]>` (recent 50, FIFO buffer)
  - `isConnected: Ref<boolean>`
  - `lastError: Ref<string | null>`
- 内部: `new EventSource('/api/studio/batch/<encoded jobId>/events')`
- Handlers:
  - `onmessage`: parse `event:` + `data:`, append to events buffer
  - `onerror`: set `isConnected=false`, schedule reconnect
- `onBeforeUnmount`: `eventSource.close()`

**Type definition**:
```typescript
export interface BatchEvent {
  type: 'job_state' | 'chapter_started' | 'chapter_completed' | 'job_completed' | 'job_failed' | 'job_cancelled';
  data: Record<string, unknown>;
  receivedAt: string;  // ISO timestamp from client
}
```

### 2.6 架构不变量保持

- I001 (infra 不 import apps) ✅
- DP-02 (LLMServiceAdapter) ✅
- DP-03 (StorageAdapter) ✅
- 12+ existing invariants preserved
- **1 NEW invariant (#49)**: SSE推 batch 状态为 canonical; Phase 23 3s polling 仅在 SSE disconnected 时作为 short-bridge fallback (5s 间隔)

---

## 3. 组件与数据流

### 3.1 后端 4 处改动

| 文件 | 改动 |
|---|---|
| `infra/studio_batch_streamer.py` | NEW, ~200 行 (BatchEventPublisher + BatchEventStreamer) |
| `apps/studio_api/routes/studio.py` | +1 SSE route (StreamingResponse + 404/401/403 handling) |
| `infra/studio_batch_runner.py` | +4 hooks (start / poll-completed / cancel / chapter) |
| `apps/studio_api/tests/test_studio_batch_events_route.py` | NEW, 4 tests |

### 3.2 前端 3 处改动

| 文件 | 改动 |
|---|---|
| `apps/dashboard/src/composables/useBatchEventStream.ts` | NEW, ~120 行 |
| `apps/dashboard/src/composables/usePilotBatch.ts` | UPDATE: 删 setInterval, 接入 SSE 事件流; 新增 `chapterEvents` ref; polling fallback 仅在 disconnected 时启用 |
| `apps/dashboard/src/components/pilot/PilotLivePanel.vue` | UPDATE: 新增 `chapterEvents` prop, 渲染 recent 5 chapter 完成通知; ETA 用 actual duration 累加 |

### 3.3 用户视角数据流

```
打开 /pilot
   ↓
usePilotBatch() 挂载
   ↓
activeJob 通过 initial fetchActiveBatchJob() 读取磁盘 JSON
   ↓
若有 running job → useBatchEventStream(activeJob.job_id) 订阅 SSE
   ↓
server 推 job_state 初始事件 (from disk JSON re-sync)
   ↓
chapter 完成 → server 推 chapter_completed 事件
   ↓
client onmessage → 更新 activeJob (累积) + append to chapterEvents buffer
   ↓
LivePanel 渲染 status pill + recent chapter 列表 + 实时 ETA
   ↓
job 终态 → server 推 terminal 事件 → client 处理 → 关闭 EventSource
```

### 3.4 复用与新文件

| 类型 | 新增 | 复用 |
|---|---|---|
| Python module | `BatchEventPublisher`,` + `BatchEventStreamer` | existing `BatchJob` dataclass |
| FastAPI route | 1 (events endpoint) | existing `register_studio` |
| TS composable | `useBatchEventStream` | EventSource native browser API |
| TS composable update | `usePilotBatch` (删 polling, 加 chapterEvents) | `useBatchEventStream`,` existing `useStudioProject` |
| Vue component update | `PilotLivePanel` (新增 chapterEvents prop) | existing |

---

## 4. 错误处理 + 边界条件

### 4.1 后端

| 场景 | 行为 |
|---|---|
| SSE client disconnect | `finally` 块清理 subscriber + 关闭 queue |
| 多个 subscriber 同 job | per-job subscriber list,顺序 fan-out |
| Subscriber 慢 (queue满 100) | drop oldest + log warning |
| Backend 重启 in-flight batch | queue 内存丢失; subscriber 重连时收到 `job_state` 重 sync |
| Job 完成时 subscriber 仍在 stream | 推 terminal event + close generator |
| Auth (session cookie) | 现有 middleware 透传;StreamingResponse 不需要特殊处理 |
| 401/403/404 | 返回 standard HTTP error (non-streaming) BEFORE streaming starts |
| Heartbeat | 每15s 推 `: ping\n\n` 防 nginx/proxy timeout |
| Job 在 backend restart前已完成 (磁盘有 JSON) | 新 client connect 推 `job_state` event from disk; subscriber 立即收到终态 |

### 4.2 前端

| 场景 | 行为 |
|---|---|
| EventSource 长 disconnect (>5s) | 触发 fallback polling (Phase 23 refreshActive 5s 间隔) 作为 bridge |
| 重连后 | server立即推 `job_state` event 重 sync (防止 missed events) |
| Job 在 disconnect期间 completed | SSE 重连后收到 `job_completed` event,UI 自动切到 completed state |
| chapterEvents 滚动 buffer | 保留最近 50 events; UI 渲染最近 5 |
| Composable unmount | `eventSource.close()` |
| Multiple PilotPage instances | 各自独立 EventSource; 后端 fan-out 安全 |
| jsdom 不支持 EventSource | vitest jsdom mock (per Phase 126 pattern) |
| SSE connection 失败 3 次连续 | 切换 fallback polling (5s 间隔) + 显示"实时连接中断"banner |

### 4.3 测试覆盖

| 文件 | 覆盖 |
|---|---|
| `tests/infra/test_studio_batch_streamer.py` (NEW) | 5 tests: initial state push / event propagation / terminal close / multi-subscriber fan-out / queue overflow |
| `apps/studio_api/tests/test_studio_batch_events_route.py` (NEW) | 4 tests: 404 / 401 / 200 SSE headers / Content-Type |
| `apps/dashboard/tests/unit/composables/use-batch-event-stream.spec.ts` (NEW) | 5 tests: connect / onmessage handler / auto-reconnect / cleanup / connection error fallback |
| `tests/unit/composables/use-pilot-batch.spec.ts` (UPDATE) | 1 NEW: chapter event updates activeJob state |
| `tests/unit/components/pilot/pilot-live-panel.spec.ts` (UPDATE) | 1 NEW: chapterEvents prop renders scrollable list |

---

## 5. 提交结构 (8 commits, atomic 1-task-per-commit)

| # | Commit | 内容 |
|---|---|---|
| 1 | `feat(studio-batch-runner): BatchEventPublisher + chapter/job event hooks` | `infra/studio_batch_streamer.py` + hooks in `infra/studio_batch_runner.py` |
| 2 | `feat(studio-api): GET /api/studio/batch/<job_id>/events SSE route` | route + StreamingResponse |
| 3 | `test(studio-batch-streamer): event publisher + streamer unit tests` | 5 backend tests |
| 4 | `test(studio-api): SSE route integration tests` | 4 backend tests |
| 5 | `feat(composables): useBatchEventStream with EventSource` | new composable + 5 tests |
| 6 | `refactor(composables): usePilotBatch replaces polling with SSE` | update existing + 1 NEW test |
| 7 | `feat(components): PilotLivePanel chapter events scrollable list` | update existing + 1 NEW test |
| 8 | `docs(phase-24): handoff + CLAUDE.md v24.0 + architecture.yml invariant #49` | docs sync |

**测试 additions**:
- Backend: 5 + 4 = 9 NEW tests
- Frontend: 5 + 1 + 1 = 7 NEW tests + ~5 updates
- Total: ~16 NEW tests + ~5 updates

---

## 6. 风险矩阵

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| **EventSource 长 disconnect + 期间 batch 完成** | 中 | 中 | client reconnect 推 `job_state` 重 sync;短期 disconnect 期间 polling fallback |
| **per-job asyncio.Queue 内存 unbounded** | 低 | 中 | subscriber-side cap 100 events, drop oldest + log warning |
| **Phase 23 polling + SSE双轨冲突** | 低 | 低 | polling 仅在 SSE disconnected 时启用 (`isConnected.value === false`); publish 触发 immediate update |
| **EventSource 在 vitest jsdom 不支持** | 中 | 中 | vitest mock EventSource (per jsdom pattern); 集成测试在 Playwright (Phase 114 accepted debt) |
| **Heartbeat 占流量** | 低 | 低 | 15s ping interval (1 byte/event); nginx-friendly |
| **后端重启 in-flight batch queue 丢失** | 低 | 低 | acceptable; client reconnect gets `job_state` 重新 sync |
| **FastAPI StreamingResponse + middleware 不兼容** | 低 | 中 | testing 验证;若有问题 fallback 到 SSE-style `Response(generator)` |
| **Cancel + SSE race condition** | 低 | 中 | cancel 走 REST POST (Phase 23 Task 5); SSE 推 `job_cancelled` event 是单向通知, 不会有 dual-write race |

### 6.1 回退策略

- 每 Part 之间独立可 revert
- Part C (Task 6) 替换 polling 是最大 risk - 拆2 个 sub-commit:
  - 6a: 加 SSE composable (新增,不删 polling)
  - 6b: 切换 usePilotBatch (删 polling, 完全切换到 SSE)
- 任何 commit 可独立 cherry-pick / revert

---

## 7. 与现有债务 +关系

- **Phase 114 prod preview** (accepted): 不影响 dev baseline; SSE 在 jsdom 集成测试在 Playwright (Phase 114 accepted debt, 不在 scope)
- **Phase 23 carryover** (本 phase 实现其中1项 - SSE) +4 项 carryover:
  - Per-chapter preview drawer in PilotLivePanel
  - Batch templates (save common mode/budget/chapters)
  - Multi-LLM provider concurrent batches
  - Pilot + Insight dashboard integration
- 12+ existing architecture invariants preserved

---

## 8. 性能预算

- SSE overhead per connection: < 1 KB/min (idle heartbeat) + variable events
- Backend publisher memory: O(jobs × subscribers) = small for typical usage
- Frontend EventSource: native browser optimization, zero custom overhead
- chapterEvents buffer cap: 50 events (内存 bound)
- Initial connection latency: < 100ms (local dev)

---

## 9. 验证门 (Phase 24 closure gates)

- vitest: 1816+ pass (1800 baseline + ~16 NEW)
- vue-tsc: 0
- ESLint: 0
- knip: `{"issues":[]}`
- ruff clean + format --check clean
- lint-imports: 3 contracts KEPT (~317 files / ~1390 deps)
- Backend pytest: ~9 NEW (publisher 5 + route 4)
- Manual verification: open /pilot in browser → start a batch → see chapter_completed events stream in real-time

---

## 10. 实施后结构变更

```
apps/dashboard/src/
├── composables/
│   ├── useBatchEventStream.ts   ← NEW
│   └── usePilotBatch.ts          ← MODIFIED (删 polling, 加 SSE)
├── components/pilot/
│   └── PilotLivePanel.vue        ← MODIFIED (chapterEvents prop)
apps/studio_api/routes/
└── studio.py                     ← +1 SSE route

infra/
└── studio_batch_streamer.py      ← NEW (publisher + streamer)

tests/infra/
└── test_studio_batch_streamer.py      ← NEW (5 tests)
apps/studio_api/tests/
└── test_studio_batch_events_route.py  ← NEW (4 tests)
```

---

## 11. Carryover to Phase 25+

- **Per-chapter preview drawer in PilotLivePanel** (click chapter to view AI output text)
- **Batch templates** (save common mode/budget/chapters combos as named templates)
- **Multi-LLM provider concurrent batches** (different chapters use different providers)
- **Pilot + Insight dashboard integration** (embed active batch progress in InsightPage)
- **SSE event filtering** (let dashboard subscribe to specific event types only)
- **Backend event replay** (for missed-event recovery on reconnect)
- **SSE auth refinement** (currently relies on session cookie; explore token-based for multi-dashboard scenarios)

---

## 12. Open Questions (无)

设计已与用户 4 段对话收敛: 架构 + 组件 + 错误处理 + 提交节奏。用户已 OK 全部 4 段。