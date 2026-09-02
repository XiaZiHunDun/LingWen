# Phase 25 — SSE Batch 增强 Filter/Replay/Auth · Handoff

> **Status**: 已实现并待合并 · **日期**: 2026-09-02
> **Branch**: `phase-25-sse-batch-enhance` · **Design spec**: [../specs/2026-09-02-phase-25-sse-batch-enhance-design.md](../specs/2026-09-02-phase-25-sse-batch-enhance-design.md)
> **Scope**: SSE 事件流增强 — 服务端 event_types 过滤 + 连接时磁盘 replay + 读取鉴权门控 (hardening)

## Summary

Phase 25 增强 Phase 24 的 batch SSE 流，落地三项 carryover（按建议优先级）：**服务端事件过滤**、**连接时磁盘 replay**、**读取鉴权 hardening**。**7 个 source commits + 1 个 docs commit**。

```
9145bda4 style(phase-25): ruff format replay_events append
c6d43be8 fix(composables): stop barrel-exporting private BatchEventType
1d8c5185 refactor(composables): usePilotBatch enables replay on connect
998097c4 feat(composables): useBatchEventStream query options
fac378a3 test(studio-api): events route filter/replay/guard
6f43d7d3 feat(studio-api): events route filter/replay/guard
8d6308a2 feat(studio-batch-runner): replay_events from disk
517a7d1a feat(studio-batch-streamer): per-subscriber event_type filter
```

**1 NEW architecture invariant (#50)** — SSE 事件流支持服务端 `event_types` 过滤 + 连接时磁盘 replay；读取被 `LINGWEN_ALLOW_DASHBOARD_BATCH` 门控。

## What shipped

### Backend

- **`infra/studio_batch_streamer.py`**: subscriber registry 从 `dict[job_id, list[Queue]]` → `dict[job_id, list[_Subscriber]]`（dataclass `queue + event_types`）。`subscribe(job_id, event_types)`；`publish` 对 event_types 非 None 且不含当前类型的 subscriber 跳过（不入队）。新增 `KNOWN_EVENT_TYPES` + `_normalize_filter`。`unsubscribe` 仍按 queue 身份匹配（保留 Phase 24 语义）。
- **`infra/studio_batch_runner.py`** + `replay_events(job)`：从磁盘重建 `job_state` + 每个 on-disk chapter 的 `chapter_completed` + 终态事件（`chapter_started` 无法可靠重建，省略）。
- **`apps/studio_api/routes/studio.py`** `GET /api/studio/batch/<job_id>/events` 新增 query param：
  - `event_types` — 逗号分隔白名单；未知类型 400。
  - `replay=1` — 连接先 emit 磁盘历史再进 live tail。
  - `slug` / `mode` — project/mode guard，不匹配 403。
  - 读取门控：`dashboard_batch_allowed()==False` → 403。
  - 初始事件单点构造（replay 或 job_state+终态），按 filter 过滤，保住 Phase 24 终态即关流的语义。

### Frontend

- **`useBatchEventStream(jobId, options)`**: `options.replay` / `options.eventTypes` → `buildUrl()` 构造 `?replay=1` / `?event_types=...`。
- **`usePilotBatch`** 传 `{ replay: true }` — 每次 connect 都从磁盘回放 chapter 历史，重连/重载不丢 `chapterEvents`。
- **`composables/index.ts`** 从 type re-export 中移除 `BatchEventType`（保持 module-private 以满足 knip；否则 barrel 引用非导出成员触发 vue-tsc TS2724）。

## Verification gates

| Gate | Result |
|---|---|
| Backend new `tests/infra/test_studio_batch_streamer.py` | **7/7 pass**（5 Phase-24 + 2 filter） |
| Backend new `apps/studio_api/tests/test_studio_batch_events_route.py` | **10/10 pass**（4 Phase-24 + 6 replay/guard/400/403） |
| Backend affected subsets `apps/studio_api/tests + tests/infra` | **440 pass / 5 fail** — 5 个均为 documented baseline env fails（LLM Provider / `_IncludedRouter` / socksio），与 master 一致，**ZERO 新增** |
| ruff check + format --check | **clean** |
| vitest (full) | **1810 pass / 1 skipped**（+3 NEW phase-25） |
| ESLint `lint:all` | **clean** |
| knip | **`{"issues":[]}`** |
| vue-tsc `typecheck:app` | 5 个 pre-existing PilotPage debt —— baseline 验证过，**ZERO 新增** |

> **Gate baseline NON-ZERO（同 Phase 24）。** `vue-tsc` 5 个 `PilotPage.vue` 类型错误为 master 遗留；受影响 pytest subsets 的 5 个失败为环境 baseline（无 LLM key/socksio/`_IncludedRouter` 漂移）。完整 6000+ 测试跑不完（11min 到 43%），但受影响子集已验证 ZERO 新增。

## Test counts added

- **Backend：8 NEW**（2 streamer filter + 6 route）。
- **Frontend：3 NEW**（2 useBatchEventStream options + 1 usePilotBatch replay）。

## Lessons

1. **knip 对「export 但只在本模块内部用」的 type 报警**（Phase 24 lesson 6 复现）：`BatchEventType` 若 export 会被 knip 标 unused；但要满足 barrel 时不能引用非导出成员。**解法**：保持 type module-private + 从 `composables/index.ts` type re-export 中删除该名（`BatchEvent`/`BatchEventStream` 内部引用它不需要它本身可导出）。这是一对 knip↔vue-tsc 的约束，需同时处理。
2. **FastAPI SSE route 的 query param** 用 func-arg `Query(default=...)`，与普通 route 一致，且在 subscribe 前做 guard 校验（400/403 非流式）。
3. **磁盘 replay 只覆盖 `job_state` + `chapter_completed` + 终态**（`chapter_started` 无法从磁盘可靠重建）——replay 是"确定性历史"而非完整 event log。
4. **阻塞式 TestClient 会卡在 running-job 的 SSE live tail**（无限循环）：测试对 filter/运行态行为改用 terminal job，让 generator 立即返回。
5. **ruff format 是提交后 diff 的来源**：writer 的 `events.append(...)` 在 `ruff format` 后折叠成单行——应把源文件按目标 format 直接写好，减少 amend/style commit。
6. **完整后端 suite 过多且 baseline 非零**：用"受影响子集 + ZERO 新增"作为验证标准，而非全量；相交改动（streamer/runner/studio route）已单独全绿。

## Carryover to Phase 26+

- Per-chapter preview drawer in PilotLivePanel
- Batch templates / multi-LLM concurrent batches / batch priority queue / auto-restart on failure
- Pilot + Insight dashboard integration
- `usePilotBatch` DTO migration 到 `@/api/studio` re-export
- event_types 前端的可选 UI 过滤开关（本阶段暴露 API，不强加 UI）
- Phase 114 prod preview regression（accepted, pre-existing）

## Files added/changed (summary)

### Modified backend

- `infra/studio_batch_streamer.py` — `_Subscriber` + `KNOWN_EVENT_TYPES` + `_normalize_filter` + subscribe/publish filter
- `infra/studio_batch_runner.py` — +`replay_events()`
- `apps/studio_api/routes/studio.py` — events route query guards + replay + filter

### Modified frontend

- `apps/dashboard/src/composables/useBatchEventStream.ts` — `options{replay,eventTypes}` + `buildUrl()`
- `apps/dashboard/src/composables/usePilotBatch.ts` — `{ replay: true }`
- `apps/dashboard/src/composables/index.ts` — drop `BatchEventType` from type re-export

### Tests added

- `tests/infra/test_studio_batch_streamer.py` (+2 filter, +2 assertion updates for `_Subscriber`)
- `apps/studio_api/tests/test_studio_batch_events_route.py` (+6, autouse batch flag fixture)
- `apps/dashboard/tests/unit/composables/use-batch-event-stream.spec.ts` (+2)
- `apps/dashboard/tests/unit/composables/use-pilot-batch.spec.ts` (+1)

### Docs

- `docs/superpowers/specs/2026-09-02-phase-25-sse-batch-enhance-design.md`（已有）
- `docs/superpowers/handoffs/2026-09-02-phase-25-sse-batch-enhance-handoff.md`（本条）
- `CLAUDE.md` → v25.0
- `.lingwen/architecture.yml` → 25.0 + `phase_25:` block + invariant #50

## Related phases

- Phase 24（SSE 源；本 phase 是对其增强）
- Phase 23（Pilot page / polling 来源）