# Phase 25 — SSE Batch 增强: Filter + Replay + Auth · Design

> **Status**: 设计稿 · 待用户 review
> **日期**: 2026-09-02
> **目标版本**: v25.0
> **作用域**: SSE 事件流增强 — 服务端事件过滤 + 连接时磁盘 replay + 读取鉴权 (hardening)

---

## 1. 背景与动机

Phase 24 已交付 `GET /api/studio/batch/<job_id>/events` SSE 流 (6 named events + 15s heartbeat + 磁盘初始 job_state re-sync)。Phase 24 carryover (见 §11) 提出三项增强：

- **SSE event filtering** (让 dashboard 只订阅特定事件类型)
- **Backend event replay** (重连时恢复 missed events)
- **SSE auth refinement** (目前依赖 session cookie，无实际鉴权)

**本阶段目标** (按建议优先级顺序落地三者)：
1. **服务端事件过滤** — subscriber 带 `event_types` 过滤；route 支持 `slug`/`mode` guard。
2. **连接时 replay** — 从磁盘重建 `job_state` + `chapter_completed` 历史，重连后不漏事件。
3. **读取鉴权 hardening** — events 读取与写同门 (`LINGWEN_ALLOW_DASHBOARD_BATCH`)，query 非法参数 400、slug/mode 不匹配 403。

> 现状事实：本地 Studio **无 cookie/auth** (app.py `allow_credentials=False`)。因此"auth"在此范围内 = 读取门控 + 参数校验，非完整登录体系。

---

## 2. 架构与端点形态

### 2.1 端点 (增强)

**`GET /api/studio/batch/<job_id>/events`** — 新增可选 query 参数：

| 参数 | 类型 | 默认 | 语义 |
|---|---|---|---|
| `event_types` | str | 无 | 逗号分隔的事件类型白名单，服务端过滤。未知类型 → **400** |
| `replay` | int(0/1) | 0 | 连接时先 emit 从磁盘重建的 `job_state`+`chapter_completed` 历史（重连不漏） |
| `slug` | str | 无 | 若提供，`job.slug != slug` → **403**（project guard） |
| `mode` | str | 无 | 若提供，`job.mode != mode` → **403**（mode guard） |

错误响应 (非流式)：
- **404** — job_id 不存在 (保留)
- **403** — batch 功能被门控关闭 (`dashboard_batch_allowed()==False`)；或 slug/mode guard 不匹配
- **400** — `event_types` 含未知类型 / 空 token

### 2.2 后端模块

**`infra/studio_batch_streamer.py`** (增强)：
- `_SUBSCRIBERS` 从 `dict[str, list[asyncio.Queue]]` → `dict[str, list[_Subscriber]]`，`_Subscriber` 为 dataclass `(queue, event_types)`。
- `subscribe(job_id, event_types=None) -> _Subscriber`。
- `publish`：若某 subscriber 的 `event_types` 非 None 且不含当前 `event_type`，跳过该 subscriber（不入队）。
- 新增 `KNOWN_EVENT_TYPES: frozenset[str]` 常量。
- `unsubscribe(job_id, queue)` 按 queue 匹配，log id 不变（避免破坏 Phase 24 语义）。

**`infra/studio_batch_runner.py`** (新增 replay 源)：
- 新增 `replay_events(job: BatchJob) -> list[tuple[str, dict]]`，从磁盘重建：
  1. `("job_state", job.to_dict())`
  2. 对每个 `_completed_chapter_nums(job)` 的章节：`("chapter_completed", {"chapter_num", "completed_at": _now_iso()})`
  3. 若终态：`("job_completed"|"job_failed"|"job_cancelled", job.to_dict())`
- 文档注明：`chapter_started` 无法从磁盘可靠重建，故仅 replay `job_state` + `chapter_completed` + 终态。

### 2.3 路由改动 (`apps/studio_api/routes/studio.py`)

在 Phase 24 `event_stream` generator 顶部，将"无条件 job_state 初始推送"改为"构造 `initial_events` 列表并**按 filter 过滤后 emit**"：

```
initial_events = [job_state]
if replay:
    initial_events += chapter_completed 序列
if 终态:
    initial_events += 终态事件

emit (受 event_types filter 约束)
if 终态: return
进入 live tail (subscribe(job_id, filter_set), heartbeat, terminal close) — Phase 24 原样
```

guard 顺序（subscribe 前）：
1. 404 job 不存在
2. 403 `dashboard_batch_allowed()` 为 False
3. 400 `event_types` 非法
4. 403 `slug`/`mode` guard 不匹配
5. `filter_set = frozenset(event_types)` 或 None

### 2.4 前端模块

**`useBatchEventStream.ts`** (增强)：
- 签名改为 `useBatchEventStream(jobId, options?: { replay?: boolean; eventTypes?: BatchEventType[] })`。
- 构造 URL 时追加 query：`replay=1`；`event_types=<comma-joined>`（若提供）。
- 导入 `BATCH_EVENT_BUFFER` 不变；`BatchEventStream` 返回接口不变。

**`usePilotBatch.ts`** (增强)：
- `useBatchEventStream(activeJobId, { replay: true })` — 任何重连/重载都先由磁盘回放 chapter 历史，`chapterEvents` 不丢。

### 2.5 架构不变量

- I001 (infra 不 import apps) ✅ 保持
- 不破坏 Phase 24 **#49** (SSE canonical + fallback only on disconnect) ✅
- **1 NEW invariant (#50)**: SSE 事件流支持服务端 `event_types` 过滤 + 连接时磁盘 replay；读取被 `LINGWEN_ALLOW_DASHBOARD_BATCH` 门控。

---

## 3. 组件与数据流

```
打开 /pilot → usePilotBatch() 挂载
   ↓ useBatchEventStream(activeJobId, { replay: true })
   ↓EventSource /api/studio/batch/<job>/events?replay=1
server: guard(403/400/404) → replay_events from disk → job_state + chapter_completed[]
   ↓ 进入 live tail (Phase 24) → 实时 chapter/terminal 事件
client: applyEvent (processedEventIndex 每次只消费一次)
   ↓ chapterEvents 首屏已由 replay 填充，无漏
```

### 复用与新文件

| 类型 | 新增 | 复用 |
|---|---|---|
| infra/studio_batch_streamer.py | `_Subscriber`, `KNOWN_EVENT_TYPES` | 现有 publish/subscribe |
| infra/studio_batch_runner.py | `replay_events()` | `_completed_chapter_nums`, `_now_iso` |
| routes/studio.py | query guards + replay + filter | Phase 24 event_stream |
| composables/useBatchEventStream.ts | options→query | 现有 EventSource 逻辑 |
| composables/usePilotBatch.ts | `{ replay: true }` | 现有 |

---

## 4. 错误处理 + 边界

| 场景 | 行为 |
|---|---|
| `event_types=foo` 未知 | 400 (非流式) |
| `slug`/`mode` 不匹配 job | 403 (非流式) |
| batch 功能被门控关闭 | 403 (非流式) |
| `replay=1` 且 job 为 running | emit job_state + 已完成的 chapter_completed → live tail |
| `replay=1` 且 job 为 completed | emit job_state + 全部 chapter_completed + 终态 → return (不订阅 live) |
| 过滤后无初始事件 | 仍进入 live tail（除非终态） |
| subscriber filter + queue 满 | 入队前先按 event_types 判定，不遇则跳过 |

---

## 5. 提交结构 (8 commits, atomic)

| # | Commit | 内容 |
|---|---|---|
| 1 | `feat(studio-batch-streamer): per-subscriber event_type filter` | streamer `_Subscriber` + filter |
| 2 | `feat(studio-batch-runner): replay_events from disk` | `replay_events()` |
| 3 | `feat(studio-api): events route filter/replay/guard` | query + 400/403 + replay 集成 |
| 4 | `test(studio-batch-streamer): event_type filter` | +2 tests |
| 5 | `test(studio-api): events route replay/guard/400/403` | +4 tests |
| 6 | `feat(composables): useBatchEventStream query options` | +2 tests |
| 7 | `refactor(composables): usePilotBatch replay on connect` | +1 test |
| 8 | `docs(phase-25): handoff + CLAUDE.md v25.0 + architecture.yml #50` | docs sync |

**测试 additions**: Backend +6 (2 streamer + 4 route) · Frontend +3 (2 eventstream + 1 pilotbatch)。

---

## 6. 风险矩阵

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| subscriber 结构变更破坏 Phase 24 | 低 | 高 | 按 queue 匹配 unsubscribe 不变；复用单测回归 |
| replay 与 live 初始 job_state 重复 | 低 | 低 | 统一改为 `initial_events` 单一入口，无重复 |
| `dashboard_batch_allowed()` 门控导致 dev 断流 | 中 | 中 | 门控仅 h发 read；与写一致，测试环境显式设 flag；spec 记录 |
| chapter replay 使用当前磁盘快照时序失真 | 低 | 低 | 仅回放已落盘章节，文档注明语义 |

---

## 7. 验证门 (Phase 25 closure)

- ruff check + format --check clean
- backend pytest: baseline +6 NEW (均过)
- vitest: baseline +3 NEW pass
- ESLint lint:all clean
- vue-tsc typecheck:app 仅 5 个 pre-existing PilotPage debt (ZERO 新增)
- knip `{"issues":[]}`
- 手动: /pilot 重载页面 → chapterEvents 由 replay 首屏填充

---

## 8. 实施后结构变更

```
infra/studio_batch_streamer.py   ← MODIFIED (_Subscriber, filter, KNOWN_EVENT_TYPES)
infra/studio_batch_runner.py     ← MODIFIED (+replay_events)
apps/studio_api/routes/studio.py ← MODIFIED (query guards + replay)
apps/dashboard/src/composables/useBatchEventStream.ts ← MODIFIED (options→query)
apps/dashboard/src/composables/usePilotBatch.ts       ← MODIFIED (replay=True)
tests/infra/test_studio_batch_streamer.py     ← +2
apps/studio_api/tests/test_studio_batch_events_route.py ← +4
apps/dashboard/tests/unit/composables/use-batch-event-stream.spec.ts ← +2
apps/dashboard/tests/unit/composables/use-pilot-batch.spec.ts      ← +1
```

---

## 9. Carryover to Phase 26+

- Per-chapter preview drawer in PilotLivePanel
- Batch templates / multi-LLM concurrent batches / priority queue / auto-restart
- Pilot + Insight dashboard integration
- `usePilotBatch` DTO migration 到 `@/api/studio` re-export
- event_types 前端的可选 UI 过滤开关（本阶段暴露 API，不强加 UI）