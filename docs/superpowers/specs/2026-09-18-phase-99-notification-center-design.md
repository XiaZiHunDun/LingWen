# Phase 99 Notification Center (REQ-002 v2 #4) — Design Spec

> **Date**: 2026-09-18
> **Phase**: v56.2 → v57.0
> **Status**: design approved, awaiting implementation
> **Cluster**: Phase 90-99 = 10 phases / 1 NEW package + 5 carryover closures + 4 REQ-002 v2 sub-projects delivered

---

## 1. Motivation

Phase 98 shipped illustration ProjectSettings extension (auto_generate / max_assets / confirm_before_generate) + LRU archive. Users now have **persistent state changes happening in the background** (cleanup triggers when chapter count exceeds max_assets, regenerate swaps atoms silently, auto-generate fires on chapter complete). Phase 90-98 give zero visibility into "what just happened to my illustrations?"

**Phase 99 goal**: a notification center that surfaces illustration events in real time, with full history.

### In scope

- Backend SSE publisher for 3 illustration event types: **generation / regeneration / cleanup**
- Backend REST history endpoint (audit_log JSONL as source-of-truth)
- Frontend header bell + dropdown panel + dedicated history page
- Active-project-scoped subscription (only current project's events)

### Out of scope (deferred)

- `deletion` event publish (Phase 98 audit_log declares it; **zero callers in v1** — add publish when manual delete path gets audit_log integration)
- Multi-project aggregation (one bell per active project only)
- Webhook / email / digest channels (covered by Phase 19 `useOnboardingNotifications` for onboarding; Phase 99 stays in-app only)
- Action affordance on notification items (regenerate retry button, etc.) — read-only feed, click jumps to detail

---

## 2. Architecture

### Component boundary

```
┌─────────────────────────────────────────────────────────┐
│  apps/dashboard (Vue 3 + Pinia)                         │
│   ├─ components/notifications/                          │
│   │   ├─ NotificationBell.vue        (header bell+badge)│
│   │   ├─ NotificationDropdown.vue    (popover 20 条)    │
│   │   └─ NotificationListItem.vue    (单条渲染)         │
│   ├─ pages/NotificationsPage.vue     (全量 history)     │
│   ├─ composables/useNotificationStream.js (SSE)         │
│   ├─ stores/useNotificationStore.js (Pinia)             │
│   └─ api/notifications.ts            (typed wrappers)   │
└─────────────────────────────────────────────────────────┘
                    ↑ EventSource  +  fetch REST
                    ↓
┌─────────────────────────────────────────────────────────┐
│  apps/studio_api (FastAPI)                              │
│   └─ routes/notifications.py                            │
│       ├─ GET /api/projects/{slug}/illustrations/events │
│       │     (SSE stream)                                │
│       └─ GET /api/projects/{slug}/illustrations/events/history│
│             (REST, since_id + limit pagination)         │
└─────────────────────────────────────────────────────────┘
                    ↑ publish(NotificationEvent)
                    ↓
┌─────────────────────────────────────────────────────────┐
│  packages/lingwen-illustrations/ (Python)               │
│   ├─ notifications.py (NEW: in-memory publisher)        │
│   │     - subscribe(slug) → asyncio.Queue               │
│   │     - unsubscribe(slug, queue)                       │
│   │     - publish(event: NotificationEvent)             │
│   │     - format_event (mirrors studio_batch_streamer)  │
│   │     - new_event_id (ULID factory)                    │
│   └─ audit_log.py (existing, I090 unchanged)            │
│         ↑ pipeline.* + cleanup_route  双写:             │
│            record_event (audit) + publish (fan-out)     │
└─────────────────────────────────────────────────────────┘
```

### Invariant (I091 NEW)

`packages/lingwen-illustrations/src/lingwen_illustrations/notifications.py:publish` is the sole fan-out entry point for illustration events. `pipeline.generate_illustration` / `pipeline.regenerate_illustration` / `apps/studio_api/routes/cleanup_route.py` call **BOTH** `audit_log.record_event` (I090) and `notifications.publish` with the same `id`. Any path bypassing `publish` for illustration event fan-out is illegal. `infra.notifications.*` paths are illegal.

### Double-write strategy

Each illustration event triggers two calls in this exact order:

1. `audit_log.record_event(project_root, event=..., asset_meta=meta, id=new_ulid, ...)` — JSONL append (durability, I090)
2. `notifications.publish(NotificationEvent(id=same_ulid, project_slug=..., ...))` — in-memory fan-out (I091)

Same `id` on both calls is a hard invariant — otherwise SSE events and REST history cannot be reconciled via `since_id`.

`publish` is fire-and-forget (synchronous `put_nowait`, returns immediately). Zero consumer = zero cost.

---

## 3. Data Model

### Backend dataclass

```python
# packages/lingwen-illustrations/src/lingwen_illustrations/notifications.py
EventType = Literal["generation", "regeneration", "cleanup", "deletion"]

@dataclass(frozen=True)
class NotificationEvent:
    id: str                 # ULID (26 chars, lexicographic time-sortable)
    project_slug: str       # route key
    event_type: EventType
    asset_id: str | None
    asset_type: str | None  # "cover" | "chapter" | None
    chapter_num: int | None
    style_preset: str | None
    provider: str | None    # Phase 96 — for "regenerated with provider=X" UI hint
    ts: str                 # ISO 8601 UTC
    extra: dict | None = None
```

### SSE wire format (mirrors Phase 24 `studio_batch_streamer`)

```
event: generation
data: {"id":"01HZX7K3...","project_slug":"星陨纪元","event_type":"generation","asset_id":"ch12-cover-v3","asset_type":"cover","chapter_num":null,"style_preset":"水墨写意","provider":"minimax","ts":"2026-09-18T07:12:34.567890+00:00","extra":{"auto_generate":true}}

event: cleanup
data: {"id":"01HZX7K4...","project_slug":"星陨纪元","event_type":"cleanup","asset_id":null,"asset_type":"chapter","chapter_num":12,"ts":"...","extra":{"lru_count":2,"trigger":"manual"}}
```

### REST history response

```python
class HistoryResponse(BaseModel):
    events: list[NotificationEvent]
    has_more: bool         # server returns limit+1 → has_more=true when truncated
    last_id: str | None    # client passes back as since_id on next poll
```

### Frontend Pinia store shape

```typescript
interface NotificationItem {
  id: string
  projectSlug: string
  eventType: 'generation' | 'regeneration' | 'cleanup' | 'deletion'
  assetId: string | null
  assetType: 'cover' | 'chapter' | null
  chapterNum: number | null
  stylePreset: string | null
  provider: string | null
  ts: string
  extra: Record<string, unknown> | null
}

state: {
  history: NotificationItem[]        // capped at 200 (client-side buffer)
  unreadCount: number                // badge count
  isConnected: boolean               // SSE status
  lastError: string | null
  activeProjectSlug: string | null   // triggers reconnect on switch
}
```

### JSONL source-of-truth (audit_log 兼容)

Phase 98 audit_log one JSONL line = one event; Phase 99 history endpoint parses `.lingwen/illustration_audit.jsonl`, filters by `project_slug == slug`, slices by ULID `id > since_id`, returns latest N. Zero new files; schema gains one optional field (`id`).

```jsonl
{"ts":"...","event":"generation","asset_id":"ch12-cover-v3","asset_type":"cover","chapter_num":null,"confirmed":true,"bypassed":false,"provider":"minimax","id":"01HZX7K3..."}
```

---

## 4. Backend module: `notifications.py`

```python
"""In-process async publisher for illustration notification SSE (Phase 99).

Mirrors lingwen_studio_batch_streamer pattern (Phase 24). In-memory subscriber
registry keyed by project_slug. publish() is non-blocking, fire-and-forget.

I091 (Phase 99): publish() is the only fan-out entry point for illustration
events. record_event (I090) remains audit_log's source of truth. pipeline and
cleanup_route call BOTH (record_event first for durability, publish second
for fan-out).
"""
from __future__ import annotations

import asyncio
import json
import ulid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Literal

EventType = Literal["generation", "regeneration", "cleanup", "deletion"]


@dataclass(frozen=True)
class NotificationEvent:
    id: str
    project_slug: str
    event_type: EventType
    asset_id: str | None
    asset_type: str | None
    chapter_num: int | None
    style_preset: str | None
    provider: str | None
    ts: str
    extra: dict | None = None


_SUBSCRIBERS: dict[str, list[asyncio.Queue]] = {}
_MAX_QUEUE = 100


def subscribe(project_slug: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=_MAX_QUEUE)
    _SUBSCRIBERS.setdefault(project_slug, []).append(q)
    return q


def unsubscribe(project_slug: str, q: asyncio.Queue) -> None:
    subs = _SUBSCRIBERS.get(project_slug)
    if subs and q in subs:
        subs.remove(q)
        if not subs:
            _SUBSCRIBERS.pop(project_slug, None)


def publish(event: NotificationEvent) -> None:
    subs = _SUBSCRIBERS.get(event.project_slug)
    if not subs:
        return
    data = format_event(event)
    for q in list(subs):
        try:
            q.put_nowait(data)
        except asyncio.QueueFull:
            try:
                q.get_nowait()
                q.put_nowait(data)
            except Exception:
                pass


def format_event(event: NotificationEvent) -> bytes:
    payload = asdict(event)
    return f"event: {event.event_type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n".encode()


def new_event_id() -> str:
    """ULID — lexicographic time-sortable, used as since_id cursor."""
    return str(ulid.new())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = [
    "NotificationEvent", "EventType",
    "subscribe", "unsubscribe", "publish", "format_event",
    "new_event_id", "now_iso",
]
```

---

## 5. audit_log.py 改动 (minimal, backward-compatible)

### record_event 新增 `id` kwarg

```python
def record_event(
    project_root: Path,
    *,
    event: EventType,
    asset_meta: IllustrationMetadata | None = None,
    confirmed: bool | None = None,
    bypassed: bool = False,
    extra: dict | None = None,
    id: str | None = None,  # NEW (Phase 99). None → omit from payload.
) -> None:
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        ...
        **(extra or {}),
    }
    if id is not None:
        payload["id"] = id  # Phase 99: prepend id for since_id compatibility
    ...
```

**Existing A1-A4 tests must remain green** — `id` is optional kwarg, default None, no payload change for callers that don't pass it.

### 新增 `read_history(slug, since_id, limit)`

```python
def read_history(
    project_slug: str,
    *,
    since_id: str | None = None,
    limit: int = 20,
) -> tuple[list[dict], bool]:
    """Parse JSONL, filter by project_slug + id > since_id, return latest N+1.

    Returns (events, has_more) where has_more is True if more rows exist
    beyond the limit.
    """
    target = _audit_path_for_project(project_slug)  # derived from project_root, passed by caller
    if not target.exists():
        return [], False
    rows = []
    try:
        with target.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if row.get("project_slug") != project_slug:
                    continue
                if since_id and row.get("id", "") <= since_id:
                    continue
                rows.append(row)
    except OSError:
        return [], False
    rows.sort(key=lambda r: r.get("id", ""), reverse=True)  # ULID lex-sort = time-sort
    has_more = len(rows) > limit
    return rows[:limit], has_more
```

**Note**: `record_event` is called with `project_root` (Path), not `project_slug` (str). The history route receives `project_slug` from path; it resolves `project_root` via `project_root_for(slug)` and passes to a thin helper that scans the same JSONL file. The `project_slug` filter is applied row-side because the JSONL file is per-project-root already.

---

## 6. Double-write sites (3 callers)

### `pipeline.generate_illustration` (after `record_event`)

```python
# existing Phase 98 record_event call:
audit_log.record_event(
    project_root,
    event="generation",
    asset_meta=meta,
    confirmed=...,
    bypassed=...,
    extra={"provider": provider, "auto_generate": ...},
)
# NEW (Phase 99) publish:
event_id = notifications.new_event_id()
# rewrite the call above to pass id=event_id, OR call publish separately.
# DECISION: call publish separately — record_event signature stays clean for A1-A4.
notifications.publish(notifications.NotificationEvent(
    id=event_id,
    project_slug=project_slug,
    event_type="generation",
    asset_id=meta.id,
    asset_type=meta.type,
    chapter_num=meta.chapter_num,
    style_preset=meta.style_preset,
    provider=provider,
    ts=notifications.now_iso(),
    extra={"auto_generate": auto_generate},
))
```

**Critical**: same `event_id` flows to both `record_event` (after Phase 99 audit_log gains `id` kwarg) and `publish`. The cleanest path: refactor each callsite to compute `event_id = new_event_id()` once, pass it to both.

### `pipeline.regenerate_illustration`

Same pattern with `event_type="regeneration"`.

### `apps/studio_api/routes/cleanup_route.py`

Inside `cleanup_illustrations` after `lru_cleanup` returns, loop over `deleted` and emit one `cleanup` event per asset. For `dry_run`, emit one synthetic event with `extra={"dry_run": True, "would_delete": N}` and `asset_id=None`.

---

## 7. Backend route: `routes/notifications.py`

```python
"""Phase 99: illustration notification center routes.

Two endpoints:
- GET /api/projects/{slug}/illustrations/events          (SSE stream)
- GET /api/projects/{slug}/illustrations/events/history  (REST history)

SSE delivers real-time events; REST serves history from audit_log JSONL.
"""
from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from lingwen_illustrations import audit_log, notifications
from lingwen_illustrations.exceptions import LoadError

from apps.studio_api.routes._project_helpers import project_root_for
from apps.studio_api.routes.ctx import RoutesContext


class HistoryResponse(BaseModel):
    events: list[dict]
    has_more: bool
    last_id: Optional[str]


def register_notifications(app: FastAPI, ctx: RoutesContext) -> None:
    _ = ctx

    @app.get("/api/projects/{slug}/illustrations/events")
    async def stream_events(slug: str) -> StreamingResponse:
        try:
            project_root_for(slug)  # 404 if unknown
        except LoadError as e:
            raise HTTPException(404, detail={"error": e.message}) from e

        queue = notifications.subscribe(slug)

        async def gen():
            try:
                # Send a hello frame so EventSource flips to OPEN immediately.
                yield b": hello\n\n"
                while True:
                    data = await queue.get()
                    yield data
            finally:
                notifications.unsubscribe(slug, queue)

        return StreamingResponse(
            gen(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get(
        "/api/projects/{slug}/illustrations/events/history",
        response_model=HistoryResponse,
    )
    def history(
        slug: str,
        since_id: Optional[str] = Query(None),
        limit: int = Query(20, ge=1, le=200),
    ) -> HistoryResponse:
        try:
            project_root = project_root_for(slug)
        except LoadError as e:
            raise HTTPException(404, detail={"error": e.message}) from e

        events, has_more = audit_log.read_history(
            project_root,
            since_id=since_id,
            limit=limit,
        )
        last_id = events[-1].get("id") if events else None
        return HistoryResponse(events=events, has_more=has_more, last_id=last_id)


__all__ = ["register_notifications", "HistoryResponse"]
```

**Registration** in `apps/studio_api/routes/__init__.py` facade (same convention as Phase 96/97/98 routes).

---

## 8. Frontend UX

### App.vue header integration

```
┌────────────────────────────────────────────────────────────┐
│ ☰  灵文工作室        [项目名▼]   [🔔³]   [Avatar]         │ ← 头部
└────────────────────────────────────────────────────────────┘
                              ↓ click
                    ┌───────────────────────┐
                    │ 通知 (3)        [全部已读] │
                    ├───────────────────────┤
                    │ 🖼  生成封面 (水墨)    │
                    │    ch12 · minimax      │
                    │    2 分钟前            │
                    ├───────────────────────┤
                    │ ♻️ 清理了 2 张旧插图   │
                    │    chapter 12          │
                    │    5 分钟前            │
                    ├───────────────────────┤
                    │ 🖼  重生成 chapter 8   │
                    │    openai · 已跳过     │
                    │    1 小时前            │
                    └───────────────────────┘
                    [查看全部 →]
```

### NotificationBell.vue

```vue
<template>
  <button class="bell" @click="open = !open" data-testid="notification-bell">
    <IconSidebarNotifications />
    <span v-if="unreadCount > 0" class="badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
    <span class="status-dot" :class="statusClass" />
  </button>
  <NotificationDropdown v-if="open" @close="open = false" />
</template>
```

- Status dot: green = connected, red = error, gray = disconnected
- Badge capped at "99+"

### NotificationDropdown.vue

- Renders `history.slice(0, 20)`
- Empty state: `您还没有任何插图通知`
- Time display via existing `useTimeOptions.js` helper
- "查看全部" link → `router.push('/notifications')`

### pages/NotificationsPage.vue

- Full history (200 client buffer)
- Event type tabs: 全部 / 生成 / 重生成 / 清理
- Auto-scroll to top on new event ONLY if user is near top (avoid disrupting read)

### useNotificationStore.js — lifecycle

```javascript
// mount sequence:
//  1. fetch REST history (non-blocking; bell shows empty until done)
//  2. open SSE EventSource (non-blocking)

// active project switch:
watch(activeProjectSlug, (slug, prev) => {
  if (prev) source.close()  // prevent leak
  reset()                    // clear history + unreadCount
  if (slug) {
    fetchHistory(slug)        // REST fallback first
    openSSE(slug)             // then SSE
  }
})

// before unmount:
onBeforeUnmount → source.close()
```

### localStorage read-state

```
key:   lingwen.notifications.lastSeen.{projectSlug}
value: ULID string
write:  bell clicked / "全部已读" button / single item clicked
read:   app boot + active project switch → compute unreadCount = (history[0].id > lastSeenId) count
corrupt JSON: clear key + treat lastSeenId=null
```

### Error UX

| Scenario | Behavior |
|----------|----------|
| SSE connection fails | bell red dot + `lastError` shown at top of dropdown: "实时连接中断，显示缓存" |
| REST history fails | dropdown empty state: "无法加载历史" + retry button |
| localStorage corrupted | clear key + treat as no lastSeen |
| Active project 404 | clear store + don't connect SSE |

---

## 9. Test strategy

| Level | Count | Focus |
|-------|-------|-------|
| Unit (`notifications.py`) | 8 | subscribe/unsubscribe lifecycle + format_event bytes shape + queue-full drop-oldest + ULID monotonic + publish 0-subscribers no-op |
| Unit (`audit_log.py` changes) | 5 | `id` kwarg backward-compat (A1-A4 preserved) + `read_history` pagination + `since_id` filter + `limit` truncation + empty file graceful |
| Integration (pipeline double-write) | 4 | generate/regenerate/cleanup routes call BOTH record_event + publish with same `id` |
| Integration (`routes/notifications.py`) | 6 | SSE first-byte hello frame + history filter + 404 unknown project + since_id cursor + limit truncation + has_more edge |
| Frontend (vitest) | 10 | useNotificationStream EventSource mock + store SSE reconnect on project switch + localStorage read-state + NotificationBell badge count cap |
| Regression guards | 12 | G1 audit_log A1-A4 unchanged + G2 3 double-write sites + G3 I091 route registered + G4 publish not-blocking pipeline + G5 publish 0-subscriber no-op + G6 ULID in audit_log + G7 SSE route returns text/event-stream + G8 history route registered + G9 frontend typed wrapper + G10 bell mounted in App.vue + G11 sidebar nav entry + G12 I091 in architecture.yml |

---

## 10. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| SSE long connections saturate uvicorn worker | MED | Default 100 active connections acceptable; reverse proxy (nginx) `proxy_buffering off` |
| in-memory registry multi-worker isolation | LOW | LingWen default single uvicorn worker; REST history from JSONL is the cross-worker reconciliation source |
| Browser 6-conn/domain limit | LOW | bell uses 1 SSE; existing PilotPage batch event stream + world ripple socket = ~3-4 total |
| Restart loses in-memory queue | LOW | audit_log JSONL is source-of-truth; SSE reconnect triggers REST `since_id` pull to backfill |
| localStorage corruption | LOW | try/parse + clear key fallback |
| ULID library dep | LOW | `python-ulid>=2.0` in pyproject; stdlib has no equivalent |
| publish blocks main path | LOW | `put_nowait` + drop-oldest on overflow; O(1) fan-out |
| Active project switch flicker | LOW | dropdown shows old history ~200ms before REST replaces |
| Cleanup batch event flood | MED | Cleanup emits N events (one per deleted asset); client buffer cap 200 drops oldest |

---

## 11. Integration points

- `apps/studio_api/routes/__init__.py` facade registers `notifications` route
- `apps/dashboard/src/router.js` adds `/notifications` route with lazy `NotificationsPage.vue`
- `apps/dashboard/src/App.vue` header-actions section: insert `<NotificationBell />` between project switcher and avatar
- `apps/dashboard/src/components/icons/sidebar/SIDEBAR_ICONS`: add `notifications` key + `IconSidebarNotifications.vue` SFC (Phosphor-duotone, `oklch(70% 0.18 280)` accent — same convention as Phase v40.0)
- `apps/dashboard/src/config/humanFirstNav.js`: add `notifications` entry
- `pyproject.toml` workspace deps of `lingwen-illustrations`: add `python-ulid>=2.0`
- `.lingwen/architecture.yml`: I091 NEW; I090 annotation extended to note double-write pattern
- `apps/dashboard/src/api/notifications.ts`: typed wrappers `fetchNotificationHistory(slug, sinceId, limit)` (Phase 124 convention: typed `.ts`, no zod, paths relative to BASE_URL)

---

## 12. Task breakdown (14 atomic commits, ~1000 LOC + 44 tests)

| # | Task | LOC est. | Tests |
|---|------|----------|-------|
| T1 | spec + plan (this doc + `2026-09-18-phase-99-notification-center.md`) | — | — |
| T2 | `notifications.py` module (publish/subscribe/format_event/new_event_id) | ~120 | 8 |
| T3 | `audit_log.read_history()` + `record_event(id=)` + 4 compat tests | ~50 | 5 |
| T4 | pipeline 3 double-write sites + 4 integration tests | ~30 | 4 |
| T5 | routes/notifications.py (SSE + REST history) + 6 route tests | ~80 | 6 |
| T6 | pyproject.toml ulid dep + lock sync | ~3 | — |
| T7 | `composables/useNotificationStream.js` (EventSource wrapper) | ~80 | 3 |
| T8 | `stores/useNotificationStore.js` (Pinia + active project watch + localStorage) | ~100 | 3 |
| T9 | `api/notifications.ts` typed wrappers | ~40 | 2 |
| T10 | `NotificationBell.vue` + `NotificationDropdown.vue` + `NotificationListItem.vue` | ~150 | 4 |
| T11 | `pages/NotificationsPage.vue` + tabs | ~120 | 2 |
| T12 | App.vue header integration + router + sidebar nav + sidebar icon SFC | ~60 | 1 |
| T13 | 12 regression guards + 1 SSE+history+bell integration test | ~150 | 13 |
| T14 | docs (CLAUDE.md v56.2 → v57.0 + I091 + handoff + BACKLOG row) | — | — |

---

## 13. Validation gates

| Gate | Target |
|------|--------|
| Backend pytest | lingwen-illustrations 194 → ~218 + studio_api 137 → ~149 + phase90 + phase98 + phase99 guards all GREEN |
| Frontend vitest | 2063 → ~2090 + NotificationBell/Dropdown/Page suites GREEN |
| `pnpm tsc --noEmit` | 0 new errors |
| `ruff check` | clean on introduced |
| Manual smoke | generate → bell badge++ → click → jump gallery → regenerate → bell dropdown show → cleanup endpoint → bell show cleanup event |
| I090 + I091 invariants | recorded in `.lingwen/architecture.yml` + preserved by G1-G12 |

---

## 14. Cluster cumulative (post-Phase 99)

| Phase | Sub-project |
|-------|-------------|
| 96 | image provider adapters (minimax/openai/stability) |
| 97 | reference image i2i |
| 98 | ProjectSettings extension + LRU archive |
| **99** | **notification center** |
| 100+ (candidates) | multi-model per provider / atomic provider fallback / v2 settings persistence extension |

**REQ-002 v2 进度**: 4 / 7 sub-projects delivered (image providers + i2i + ProjectSettings+LRU + notification center). 3 remaining.

---

## 15. Lessons anticipated (per Phase 90-98 pattern)

1. **ULID > UUID for SSE + cursor**: lexicographic time-sort gives free pagination cursor; Phase 98 audit_log was pre-ULID, Phase 99 retrofit is opt-in (`id` kwarg default None).
2. **Double-write is dual invariant**: I090 (record_event) + I091 (publish). Test must verify SAME id flows to both — separate id generation on either side is a silent data drift bug.
3. **In-memory SSE queue + JSONL durability is a known trade-off**: Phase 24 studio_batch_streamer established the pattern. Restart loses live events but REST history fills the gap.
4. **Frontend localStorage read-state is opt-in opt-out**: don't push users to read-state. Bell badge is informational; clearing it is a 1-click action.
5. **Sidebar icons + nav must be added at the same commit as the page**: orphan icons and orphan pages both ship visual debt. Phase v40.0 lesson 3 reaffirmed.

---

## 16. Acceptance criteria

Phase 99 is complete when:

1. ✅ Backend `notifications.py` module shipped + 8 unit tests + I091 invariant
2. ✅ `audit_log.read_history()` works with `since_id` + limit pagination
3. ✅ Pipeline 3 double-write sites emit same `id` to record_event + publish
4. ✅ SSE route streams with `: hello\n\n` first byte + text/event-stream content-type
5. ✅ REST history route serves from JSONL with backward-compatible `id` kwarg on `record_event`
6. ✅ Frontend bell mounted in App.vue + sidebar nav + dedicated page
7. ✅ Active project switch closes old SSE + opens new (no leak)
8. ✅ localStorage read-state persists across page reload
9. ✅ All 12 regression guards GREEN
10. ✅ pytest + vitest + tsc + ruff clean
11. ✅ Manual smoke test: generate/regenerate/cleanup → bell shows event
12. ✅ CLAUDE.md v56.2 → v57.0 + I091 + handoff doc committed
