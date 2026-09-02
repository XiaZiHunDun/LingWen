# Phase 24 — SSE Real-time Batch Progress · Handoff

> **Status**: 已实现并合并 · **日期**: 2026-09-02
> **Branch**: `phase-24-sse-batch-progress` · **Design spec**: [../specs/2026-09-02-phase-24-sse-batch-progress-design.md](../specs/2026-09-02-phase-24-sse-batch-progress-design.md)
> **Scope**: 后端 SSE endpoint + 前端 EventSource composable + 替换 Phase 23 3s polling

## Summary

Phase 24 用服务器推送(SSE)替换了 Phase 23 的 3 秒轮询，实时推送 batch 进度。**9 个 source commits**(`322b10e9..48fe0f39`)+ 1 个 docs commit。

```
48fe0f39 style(phase-24): lint gate fixes
f71c78df feat(components): PilotLivePanel chapter events scrollable list
917948df refactor(composables): usePilotBatch replaces polling with SSE
49e76ade feat(composables): useBatchEventStream with EventSource
e1a172ca test(studio-api): SSE route integration tests
5de67d21 test(studio-batch-streamer): event publisher + streamer unit tests
c47e2ddf feat(studio-api): GET /api/studio/batch/<job_id>/events SSE route
322b10e9 feat(studio-batch-runner): BatchEventPublisher + chapter/job event hooks
```

**1 NEW architecture invariant (#49)** — SSE 推 batch 状态为 canonical；Phase 23 3s polling 仅在 SSE disconnected 时作为 5s short-bridge fallback。

## What shipped

### Backend

- **NEW `infra/studio_batch_streamer.py`**: `BatchEventPublisher`(module-level thread-safe singleton，per-job subscriber list + 每个 subscriber 一个 asyncio.Queue cap 100 drop-oldest) + `BatchEventStreamer`。
- **NEW route** `GET /api/studio/batch/<job_id>/events`(`apps/studio_api/routes/studio.py`)：`StreamingResponse(media_type="text/event-stream")`，headers `Cache-Control: no-cache` + `X-Accel-Buffering: no` + `Connection: keep-alive`；15s heartbeat(`: ping`)。错误响应非流式：404 / 401 / 403。
- **6 named events**：`job_state` / `chapter_started` / `chapter_completed` / `job_completed` / `job_failed` / `job_cancelled`。
- **4 hooks in `infra/studio_batch_runner.py`**：start / poll-completed / cancel / chapter_records.append。

### Frontend

- **NEW `apps/dashboard/src/composables/useBatchEventStream.ts`**：原生 `EventSource`，50-event FIFO buffer，`addEventListener` 按事件类型挂载(named SSE event 不能只用 `onmessage`——它只触发 unnamed frame)。
- **`usePilotBatch`** 删掉 3s `setInterval`，接入 SSE：`processedEventIndex` 保证每个事件只消费一次；`chapterEvents` ref(最近 20)；fallback polling 只在 `isConnected === false` 时启用(5s bridge)。
- **`PilotLivePanel`** 新增 `chapterEvents` prop，渲染最近 5 个 chapter 完成通知。

## Architecture invariants

### 1 NEW invariant

- **#49** SSE推 batch 状态为 canonical；Phase 23 3s polling 仅 SSE disconnected 时作为 5s fallback bridge。

## Verification gates

| Gate | Result |
|---|---|
| Backend new tests `tests/infra/test_studio_batch_streamer.py` | **5/5 pass** |
| Backend new tests `apps/studio_api/tests/test_studio_batch_events_route.py` | **4/4 pass** |
| Backend `tests/infra apps/studio_api/tests` | 只有 baseline 环境失败(coverage 未装/无 LLM key/_IncludedRouter 漂移)——与 master 一致，ZERO 新增 |
| ruff check + format --check | **clean**(autofix 修复 4 errors + 2 format) |
| vitest | **1807 pass / 1 skipped(234 files)** |
| ESLint `lint:all` | **clean** |
| knip | **`{"issues":[]}`**(drop unused `BatchEventType` export) |
| vue-tsc `typecheck:app` | 只有 5 个 pre-existing PilotPage Phase-23 debt errors —— baseline 验证过，ZERO 新增 |

> **Gate baseline NON-ZERO。** `vue-tsc` 的 5 个 `PilotPage.vue` 类型错误是 master `8a09af0a` 上就存在的 Phase 23 debt；`typecheck:app` 在 main repo(master)上结果完全相同。本次改动 **没有新增任何 vue-tsc 错误**。修复 PilotPage 类型超出本阶段范围。

## Test counts added

- **Backend：9 NEW**(5 streamer + 4 SSE route)。
- **Frontend：19** phase-24(5 useBatchEventStream + 6 usePilotBatch + 8 PilotLivePanel)+ pilot-page spec mock 补充。

## Lessons

1. **named SSE event 必须 `addEventListener(type, ...)`**，不能只用 `onmessage`。原生 EventSource 的消息分发依赖 `event:` 字段；`onmessage` 只触发 unnamed frame。vitest jsdom 的 EventSource mock 同理，每个 `addEventListener` 单独触发。
2. **asyncio.Queue 每个 subscriber 一个 + cap 100 drop-oldest**——慢消费者不阻塞发布者，溢出丢最旧并 log。
3. **backend 重启 in-flight job 的 state re-sync** 靠 client 重连后的初始 `job_state` event(from disk JSON)，避免 missing events。
4. **fallback polling 只在 `isConnected === false` 启用**——是 bridge 不是 source of truth；terminal status 后关停。
5. **EventSource 对 transient error 会自动重连**；前端用 `isConnected` 标志判断是否需要 fallback，而非依赖重连机制本身。
6. **knip 对「只在本模块内部使用但被 export 的 type」会报警**——`BatchEventType` 只被 `useBatchEventStream.ts` 内部使用，去掉 `export` 即可。
7. **page-level spec 的 composable mock 需要同步补上新字段**——`PilotPage.vue` 绑定 `pilot.chapterEvents` 后，`pilot-page.spec.ts` 的 mock 缺该字段会导致 `Cannot read properties of undefined`。
8. **Edit 工具对超长单行 `old_string` 会报「String to replace not found」**——拆短或用 Python 精确改单行(CLAUDE.md / architecture.yml 版本行)。

## Carryover to Phase 25+

- SSE 增强：按 project/mode filter + event replay/history window + auth hardening for batch event stream。
- Per-chapter preview drawer in PilotLivePanel。
- Batch templates / multi-LLM concurrent batches / batch priority queue / auto-restart on failure / Pilot + Insight 集成。
- `usePilotBatch` DTO migration 到 `@/api/studio` re-export。
- Phase 114 prod preview regression(accepted, pre-existing)。

## Files added/changed (summary)

### New backend

- `infra/studio_batch_streamer.py` — BatchEventPublisher + BatchEventStreamer
- `tests/infra/test_studio_batch_streamer.py`(5 tests)
- `apps/studio_api/tests/test_studio_batch_events_route.py`(4 tests)

### Modified backend

- `apps/studio_api/routes/studio.py` — +SSE route
- `infra/studio_batch_runner.py` — +4 hooks

### New frontend

- `apps/dashboard/src/composables/useBatchEventStream.ts`
- `apps/dashboard/tests/unit/composables/use-batch-event-stream.spec.ts`(5)

### Modified frontend

- `apps/dashboard/src/composables/usePilotBatch.ts`(+ 其 spec)
- `apps/dashboard/src/components/pilot/PilotLivePanel.vue`(+ 其 spec)
- `apps/dashboard/src/pages/PilotPage.vue`(chapterEvents binding)+ `tests/unit/pages/pilot-page.spec.ts`(mock)

### Docs

- `docs/superpowers/specs/2026-09-02-phase-24-sse-batch-progress-design.md`(已有)
- `docs/superpowers/handoffs/2026-09-02-phase-24-trae-handoff.md`(本条)
- `CLAUDE.md` → v24.0
- `.lingwen/architecture.yml` → 24.0 + `phase_24:` block + invariant #49

## Related phases

- Phase 23(来源 polling + batch cancel/history)
- Phase 14x jsdom EventSource mock 模式
