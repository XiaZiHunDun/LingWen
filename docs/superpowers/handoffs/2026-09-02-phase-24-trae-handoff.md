# Phase 24 — Trae 交接文档

> **用途**: 给 Trae AI 编程工具的 Phase 24 实施交接
> **日期**: 2026-09-02
> **当前 master HEAD**: `b6de01be` (Phase 23 v23.0 已 merged + Phase 24 design spec 已 commit)
> **Worktree branch**: `phase-24-sse-batch-progress` (待创建)

---

## 0. 项目速览

**LingWen · 工业化小说生产系统**

- 后端: Python 3.13 + FastAPI + SQLite (uv workspaces)
- 前端: Vue 3 + Pinia + TypeScript strict + Naive UI
- 包管理: pnpm workspace (前端) + uv workspace (后端)
- 测试: pytest (后端) + Vitest (前端)
- 质量: ruff / ESLint / vue-tsc / knip / import-linter

**重要约定** (从 CLAUDE.md 提炼):

- 不建 PR。Worktree + commit + ff-merge + push master
- 不重命名 `lingwen` 命名空间 (品牌已迁移到 `墨灵 Studio`,但代码用 `lingwen`)
- 不主动开新项目 / SaaS / 录屏
- 不动 Phase 114 prod preview accepted debt
- 测试必须在 worktree venv 跑 (`.venv/bin/python -m pytest`),NOT conda python
- pytest 用 `DEEPEVAL_DISABLE_DOTENV=1` (Phase 22 修复) — 不需要 `env -u MINIMAX_API_KEY`

---

## 1. 当前状态 (Phase 24 开始)

### 1.1 已完成

- **Phase 23 v23.0** (merged): Pilot Page feature (cancel/ETA/history) — 16 source commits + 3 fixup + 1 docs = 20 commits
- **Phase 24 design spec**: `docs/superpowers/specs/2026-09-02-phase-24-sse-batch-progress-design.md` (324 行, 已 commit `b6de01be`)
- master clean at `b6de01be`, no uncommitted changes (`.turbo/` + `docs/resume/` 是 pre-existing untracked)

### 1.2 Phase 24 范围

**Phase 23 carryover #1**: SSE/WebSocket real-time batch progress (替换 Phase 23 3s polling)

**方案**: SSE 单向推送 + REST cancel (cancel 走 Phase 23 Task 5 的 POST endpoint)
- 简化 (HTTP/1.1 兼容, EventSource 自动重连)
- Cancel 状态同步无 race condition

**事件类型**: `job_state` / `chapter_started` / `chapter_completed` / `job_completed` / `job_failed` / `job_cancelled`

---

## 2. 实施计划 (8 commits, atomic 1-task-per-commit)

| # | Commit 格式 | 文件 | 测试 |
 |---|---|---|---|
| 1 | `feat(studio-batch-runner): BatchEventPublisher + chapter/job event hooks` | `infra/studio_batch_streamer.py` (NEW, ~200行) + hooks in `infra/studio_batch_runner.py` | — |
| 2 | `feat(studio-api): GET /api/studio/batch/<job_id>/events SSE route` | `apps/studio_api/routes/studio.py` (append route) | — |
| 3 | `test(studio-batch-streamer): event publisher + streamer unit tests` | `tests/infra/test_studio_batch_streamer.py` (NEW, 5 tests) | backend |
| 4 | `test(studio-api): SSE route integration tests` | `apps/studio_api/tests/test_studio_batch_events_route.py` (NEW, 4 tests) | backend |
| 5 | `feat(composables): useBatchEventStream with EventSource` | `apps/dashboard/src/composables/useBatchEventStream.ts` (NEW, ~120行) + tests | frontend (5 tests) |
| 6 | `refactor(composables): usePilotBatch replaces polling with SSE` | `apps/dashboard/src/composables/usePilotBatch.ts` (UPDATE: 删 setInterval) + tests | frontend (1 NEW) |
| 7 | `feat(components): PilotLivePanel chapter events scrollable list` | `apps/dashboard/src/components/pilot/PilotLivePanel.vue` (UPDATE: chapterEvents prop) + tests | frontend (1 NEW) |
| 8 | `docs(phase-24): handoff + CLAUDE.md v24.0 + architecture.yml invariant #49` | `docs/superpowers/handoffs/2026-09-02-phase-24-sse-batch-progress-handoff.md` (NEW) + CLAUDE.md + .lingwen/architecture.yml | — |

**预期总测试**: 9 backend + 7 frontend = 16 NEW tests + ~5 updates

---

## 3. Worktree 设置 (Task 0 — 实施前必须)

```bash
cd /home/ailearn/projects/LingWen
git worktree add .worktrees/phase-24-sse-batch-progress -b phase-24-sse-batch-progress master
cd .worktrees/phase-24-sse-batch-progress
uv sync --all-packages
uv pip install pytest pytest-asyncio psutil   # per MEMORY.md N.14 lesson 4
```

**关键**: 用 worktree 的 `.venv/bin/python`,NOT `/home/ailearn/miniconda3/bin/python`(conda 有 stale PYTHONPATH)。

---

## 4. 详细任务规格 (来自 design spec)

完整规格见 `docs/superpowers/specs/2026-09-02-phase-24-sse-batch-progress-design.md`。以下是每任务关键细节。

### Task 1: BatchEventPublisher + hooks

**Files:**
- Create: `infra/studio_batch_streamer.py` (~200行)
- Modify: `infra/studio_batch_runner.py` (加 4 个 hooks)

**`infra/studio_batch_streamer.py`** 关键结构:
```python
import asyncio
import json
from typing import AsyncIterator

from infra.studio_batch_runner import _load_job

# Per-job subscriber registry: job_id → list[asyncio.Queue]
_SUBSCRIBERS: dict[str, list[asyncio.Queue]] = {}
# Cap per queue to: prevent unbounded growth
_MAX_QUEUE = 100


def publish(job_id: str, event_type: str, payload: dict) -> None:
    """Non-blocking fire-and-forget event publish."""
    if job_id not in _SUBSCRIBERS:
        return  # no subscribers
    data = f"event: {event_type}\ndata: {json.dumps(payload)}\n\n".encode()
    for queue in list[(_SUBSCRIBERS[job_id])]:
        try:
            queue.put_nowait(data)
        except asyncio.QueueFull:
            # Drop oldest, enqueue newest
            try:
                queue.get_nowait()
                queue.put_nowait(data)
            except Exception:
                pass


def subscribe(job_id: str) -> asyncio.Queue:
    """Create new subscriber queue for job_id; returns queue."""
    q: asyncio.Queue = asyncio.Queue(maxsize=_MAX_QUEUE)
    _SUBSCRIBERS.setdefault(job_id, []).append(q)
    return q


def unsubscribe(job_id: str, q: asyncio.Queue) -> None:
    if job_id in _SUBSCRIBERS:
        try:
            _SUBSCRIBERS[job_id].remove(q)
        except ValueError:
            pass
        if not _SUBSCRIBERS[job_id]:
            del _SUBSCRIBERS[job_id]
```

**`infra/studio_batch_runner.py` hooks** (在现有函数末尾插入):
- `start_batch_job` 末尾 (返回前): `publish(job_id, "job_started", {"start_chapter": job.start_chapter, "end_chapter": job.end_chapter, "mode": job.mode, "budget_usd": job.budget_usd})`
- `_poll_job` 检测到 `_process_running == False` (status terminal) 后: `publish(job_id, "job_completed" if job.exit_code == 0 else "job_failed", {"exit_code": job.exit_code, "finished_at": job.finished_at})`
- `cancel_batch_job` 末尾: `publish(job_id, "job_cancelled", {"finished_at": job.finished_at, "error": job.error})`
- pilot_records.jsonl append 后 (找现有 hook 点): `publish(job_id, "chapter_completed", {"chapter_num": N, "completed_at": iso, "duration_sec": dur})`

### Task 2: SSE route

**Modify `apps/studio_api/routes/studio.py`** — 在 `register_studio` 末尾加:
```python
    @app.get("/api/studio/batch/{job_id}/events")
    async def studio_batch_events_endpoint(
        job_id: str, request: Request
    ) -> StreamingResponse:
        """SSE stream of batch job events (job_state + chapter + terminal)."""
        from fastapi.responses import StreamingResponse
        from infra.studio_batch_streamer import subscribe, unsubscribe, publish
        from infra.studio_batch_runner import _load_job
        
        job = _load_job(job_id)
        if job is None:
            raise HTTPException(404, f"batch job not not {job_id!r}")
        # Auth check (per Phase 23 Task 3 pattern: RoutesContext check)
        if ctx is not None:
            if not ctx.can_access_project(job.slug):
                raise HTTPException(403, "no access to project")
        
        queue = subscribe(job_id)
        
        async def event_stream():
            try:
                # Initial state push
                yield f"event: job_state\ndata: {json.dumps(job.to_dict())}\n\n".encode()
                last_heartbeat = time.time()
                while True:
                    try:
                        data = await asyncio.wait_for(queue.get(), timeout=5.0)
                        yield data
                        last_heartbeat = time.time()
                        # Check terminal: if event was job_completed/failed/cancelled, close
                        if b'"job_completed"' in data or b'"job_failed"' in data or b'"job_cancelled"' in data:
                            break
                    except asyncio.TimeoutError:
                        # Heartbeat
                        yield b": ping\n\n"
                        last_heartbeat = time.time()
            finally finally:
                unsubscribe(job_id, queue)
        
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )
```

**注意**: 上面代码含 markdown 渲染 artifacts (`! not`),需用正确 Python syntax: `f"batch job not not {job_id!r}"` 实际应该是 `f"batch job not found: {job_id!r}"`,`raise` 应该是 `raise HTTPException(...)`。

**Import additions at top of studio.py**:
```python
import asyncio
import json
import time
from fastapi.responses import StreamingResponse
```

### Task 3: Backend unit tests

Create `tests/infra/test_studio_batch_streamer.py` (5 tests):
- `test_publish_with_no_subscribers_is_noop`
- `test_subscribe_creates_queue_and_receives_published_events`
- `test_publish_to_multiple_subscribers_fans_out`
- `test_unsubscribe_removes_subscriber`
- `test_queue_overflow_drops_oldest` (cap=100, publish 101 events, verify only latest 100 retained)

### Task 4: SSE route integration tests

Create `apps/studio_api/tests/test_studio_batch_events_route.py` (4 tests):
- `test_events_route_returns_404_for_missing_job`
- `test_events_route_returns_401_when_unauthenticated` (if auth required)
- `test_events_route_returns_200_sse_headers_for_valid_job`
- `test_events_route_sends_initial_job_state_event`

### Task 5: useBatchEventStream composable

Create `apps/dashboard/src/composables/useBatchEventStream.ts` (~120行):

```typescript
import { onBeforeUnmount, ref, watch, type Ref } from 'vue';

export interface BatchEvent {
  type: 'job_state' | 'chapter_started' | 'chapter_completed' | 'job_completed' | 'job_failed' | 'job_cancelled';
  data: Record<string, unknown>;
  receivedAt: string;
}

const MAX_EVENTS_BUFFER = 50;

export function useBatchEventStream(jobId: Ref<string | null>) {
  const events = ref<BatchEvent[]>([]);
  const isConnected = ref(false);
  const lastError = ref<string | null>(null);
  let eventSource: EventSource | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  
  function connect(id: string) {
    if (eventSource) eventSource.close();
    eventSource = new EventSource(`/api/studio/batch/${encodeURIComponent(id)}/events`);
    
    eventSource.onopen = () => {
      isConnected.value = true;
      lastError.value = null;
    };
    
    eventSource.onerror = (e) => {
      isConnected.value = false;
      lastError.value = `SSE error: ${e}`;
      // EventSource auto-reconnects; manual backup after 5s
      if (reconnectTimer) clearTimeout(reconnectTimer);
      reconnectTimer = setTimeout(() => {
        if (eventSource && !isConnected.value) {
          // Force reconnect by recreating
          connect(id);
        }
      }, 5000);
    };
    
    eventSource.onmessage = (e) => {
      // Generic message (no event: prefix)
    };
    
    // Type-specific handlers
    ['job_state', 'chapter_started', 'chapter_completed', 'job_completed', 'job_failed', 'job_cancelled'].forEach(type => {
      eventSource!.addEventListener(type, (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          events.value.push({ type: type as any, data, receivedAt: new Date().toISOString() });
          if (events.value.length > MAX_EVENTS_BUFFER) {
            events.value = events.value.slice(-MAX_EVENTS_BUFFER);
          }
        } catch (err) {
          console.warn(`[useBatchEventStream] parse error for ${type}:`, err);
        }
      });
    });
  }
  
  function disconnect() {
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    isConnected.value = false;
  }
  
  watch(jobId, (id) => {
    disconnect();
    if (id) connect(id);
  }, { immediate: true });
  
  onBeforeUnmount(() => disconnect());
  
  return { events, isConnected, lastError };
}
```

Create `apps/dashboard/tests/unit/composables/use-batch-event-stream.spec.ts` (5 tests):
- `test_connect_creates_event_source_on_job_id`
- `test_onmessage_handler_appends_to_events_buffer`
- `test_auto_reconnect_on_disconnect` (mock EventSource error event)
- `test_cleanup_on_unmount` (verify eventSource.close called)
- `test_connection_error_sets_fallback_flag`

### Task 6: usePilotBatch SSE migration

Modify `apps/dashboard/src/composables/usePilotBatch.ts`:
- 删除 `setInterval(refreshActive, 3000)` polling block (~10 行)
- 删除 `pollHandle` ref + `startPolling`/`stopPolling` helpers
- 新增 `chapterEvents: Ref<BatchEvent[]>` (默认 `[]`, 与 Phase 23 activeJob/history 同级 ref)
- 内部接入 `useBatchEventStream`: 在 composable 内根据 `activeJob.value?.status` 自动启动/关闭 SSE
- `refreshActive` 保留作为 fallback: 当 `isConnected === false` 时启 5s polling
- 更新测试 1 NEW: chapter event 更新 activeJob state

**关键 code pattern**:
```typescript
import { useBatchEventStream } from './useBatchEventStream';

export function usePilotBatch() {
  // ... existing state ...
  const chapterEvents = ref<BatchEvent[]>([]);
  
  const { events: sseEvents, isConnected } = useBatchEventStream(
    computed(() => activeJob.value?.status === 'running' ? activeJob.value?.job_id ?? null : null)
  );
  
  // Update activeJob on chapter events
  watch(sseEvents, (newEvents) => {
    for (const ev of newEvents) {
      if (ev.type === 'job_state') {
        activeJob.value = { ...activeJob.value, ...ev.data };
      } else if (ev.type === 'chapter_completed') {
        chapterEvents.value.push(ev);
      } else if (ev.type === 'job_completed' || 'job_failed' || 'job_cancelled') {
        activeJob.value = { ...activeJob.value, status: ev.type.replace('job_', ''), ...ev.data };
        chapterEvents.value.push(ev);
      }
    }
  }, { deep: true });
  
  // Polling fallback: 5s when disconnected
  watch(isConnected, (connected) => {
    if (!connected && activeJob.value?.status === 'running') {
      const interval = setInterval(refreshActive, 5000);
      onBeforeUnmount(() => clearInterval(interval));
    }
  });
  
  // ... rest of existing ...
}
```

### Task 7: PilotLivePanel chapter events UI

Modify `apps/dashboard/src/components/pilot/PilotLivePanel.vue`:
- 新增 prop `chapterEvents: BatchEvent[]`
- 在 log_tail 上方渲染 recent 5 chapter events 滚动列表
- ETA 计算融合 chapter events (累加 actual duration)

Add 1 NEW test: chapterEvents prop renders scrollable list.

### Task 8: Docs sync

Create `docs/superpowers/handoffs/2026-09-02-phase-24-sse-batch-progress-handoff.md`:
- 用 Phase 23 handoff doc (200行) 做模板
- 章节: What shipped / Architecture invariants / Verification gates / Test counts / Lessons / Carryover

Modify `CLAUDE.md`:
- 加 v24.0 entry 在 v23.0 之前
- 描述 Phase 24 SSE 实施

Modify `.lingwen/architecture.yml`:
- version: "24.0"
- 加 invariant I049: SSE canonical; polling only as short-bridge

---

## 5. 验证门 (执行后必跑跑)

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-24-sse-batch-progress

# Backend
.venv/bin/python -m pytest tests/infra/test_studio_batch_streamer.py apps/studio_api/tests/test_studio_batch_events_route.py -v
.venv/bin/python -m pytest tests/infra/test_studio_batch_runner.py tests/infra/test_studio_batch_runner_cancel.py tests/infra/test_studio_batch_runner_eta.py -v  # no regression

# Frontend
cd apps/dashboard
pnpm vitest run tests/unit/composables/use-batch-event-stream.spec.ts
pnpm vitest run tests/unit/composables/use-pilot-batch.spec.ts
pnpm vitest run tests/unit/components/pilot/pilot-live-panel.spec.ts
pnpm vitest run  # 全套 1816+ pass
pnpm tsc --noEmit  # 0 errors
pnpm eslint .  # 0 errors
pnpm exec knip  # clean
cd ../..

# Lint
ruff check .  # clean
ruff format --check .  # clean
```

**预期**: 全部 pass。Phase 23 baseline vitest 1800+1 + ~16 NEW = ~1816+1。

---

## 6. Phase 23 lessons (必读)

执行 Phase 24 时,这些 Phase 23 lessons 直接 relevant:

1. **Verify-before-design (N.14 lesson 1)**: 实现前 verify plan 里的所有 wrapper name / file path / DTO 名称在 codebase 里真实存在。Phase 23 Task 7 plan 引用 `fetchStudioStartBatchJob` (不存在), implementer 用了实际 canonical `studioProductionRun`。类似 audit 必做。

2. **Plan bugs are inevitable**: Phase 23 plan 有 ~8 个 deviations(YAML syntax error / non-existent wrapper / missing re-export / 错的 testid / `attachTo: true` invalid / `<button type="submit">` jsdom 限制 / `DASHBOARD_NAV_ENTRIES` 不存在)。每 implementer 必读 plan 仔细,catch deviation 后先 self-verify 再 commit。

3. **`request()` from `core.js` 是 canonical wrapper pattern**: 不要 raw `fetch()`。若 frontend 任务需要新 wrapper,必走 `request()` + DTO 来自 `@lingwen/dashboard-contracts/shared`。

4. **`/api/` prefix 必须 NOT in code**: `core.js` BASE_URL 已 prepend。Hardcoded prefix 是 v16.2.1 已知 regression。

5. **vue-test-utils v2.4.11 `attachTo` 限制**: 只接受 `string | Element | undefined`。Boolean `true` 报 TS error + runtime error。

6. **`<button type="submit">` 在 jsdom + `trigger('click')` 不模拟 form submission**: 用 `type="button"` + 显式 `@click`。

7. **DTO re-export chain**: wrapper 从 `@lingwen/dashboard-contracts/shared` 拿 DTO,该路径 resolve 到 `shared/index.ts`。新 DTO 必须同时加到 `studio.ts` AND `index.ts`。

8. **knip must run from `apps/dashboard/` CWD** (or via `pnpm knip` from root)。

9. **CLAUDE.md + .lingwen/architecture.yml 是 source of truth**: 新 invariants 加到 architecture.yml,版本号 bump,CLAUDE.md 加 version entry。

10. **ruff I001 自动 fix**: 若 ruff 报错,跑 `ruff check --select I001 --fix .` 自动修。

---

## 7. 已知坑 (Phase 23 实测)

1. **FastAPI StreamingResponse 需要 `X-Accel-Buffering: no` header**: 否则 nginx 会 buffer,client 收不到 events。
3. **pytest deepeval plugin**: Phase 22 已修 (DEEPEVAL_DISABLE_DOTENV=1),不应该再需要 `env -u MINIMAX_API_KEY`。若仍看到 real LLM calls hang,先跑 `.venv/bin/python -m pytest tests/infra/test_studio_batch_streamer.py -v --co` 看 collection 是否干净。

4. **vitest jsdom 不支持 EventSource**: 用 vitest mock(per Phase 126 pattern)。`vi.stubGlobal('EventSource', class { ... })`。

5. **FastAPI StreamingResponse generator 中 `await queue.get()` vs `await asyncio.wait_for(queue.get(), timeout=5.0)`**: 必须 timeout, 否则 EventSource 心跳会 hang generator。

6. **import 顺序**: 新加 `asyncio`, `json`, `time` imports 到 `studio.py` 顶部,按字母序。`ruff --fix` 自动 sort。

---

## 8. 测试模式 (从 Phase 19+ 提取)

**Backend pytest RED → GREEN 流程**:
```python
# RED: 函数不存在 → ImportError
# GREEN: 实现函数 → 跑测试
.venv/bin/python -m pytest tests/path/test.py::test_name -v
```

**Frontend vitest RED → GREEN 流程**:
```typescript
// RED: import 缺失
// GREEN: 实现 → vitest pass
cd apps/dashboard && pnpm vitest run tests/unit/path/test.spec.ts
```

**Commit message 格式** (from CLAUDE.md):
```
<type>: <description>

<optional body>

Co-Authored-By: Claude <noreply@anthropic.com>
```
Types: feat / fix / refactor / docs / test / chore / perf / ci

---

## 9. 收尾 (Merge + Cleanup)

Phase 24 完成后:

```bash
# 在 worktree
git add -A
git commit -m "..."  # 若有 ruff --fix 等 cleanup

# Master merge (per MEMORY.md workflow)
cd /home/ailearn/projects/LingWen
git checkout master
git merge --ff-only phase-24-sse-batch-progress
git push origin master

# Cleanup worktree + branch
git worktree remove .worktrees/phase-24-sse-batch-progress --force
git branch -d phase-24-sse-batch-progress

# 写 handoff doc (Task 8 内容)
```

---

## 10. Carryover (Phase 25+)

Phase 24 完成后,SSE-related carryover:
- **SSE event filtering** (client subscribe to subset)
- **Backend event replay** (missed-event recovery on reconnect)
- **SSE auth refinement** (token-based for multi-dashboard)

其他 Phase 23 carryover:
- Per-chapter preview drawer in PilotLivePanel
- Batch templates (save common mode/budget/chapters)
- Multi-LLM provider concurrent batches
- Pilot + Insight dashboard integration

---

## 11. 联系 / 反馈

- 设计 spec: `docs/superpowers/specs/2026-09-02-phase-24-sse-batch-progress-design.md`
- 当前 CLAUDE.md master: master HEAD `b6de01be`
- 工程 namespace: `lingwen` (品牌: 墨灵 Studio)

如有问题,follow Phase 23 lessons (Section 6) — 那是过去 16 tasks 实测的坑列表。