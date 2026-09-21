# Phase 104 — Notify Threshold per Event Type — Design Spec

> **Date**: 2026-09-21
> **Phase**: v60.1 → v60.2
> **Cluster**: Phase 102+ extension #2 (Phase 103 was #1)
> **Type**: Full-stack inline extension (Phase 102/103 same mode延续)
> **Workflow**: Solo repo, no PR, direct commits on master (per 2026-09-15 simplified workflow)

## Summary

Phase 104 extends `notify_threshold` (introduced in Phase 102) from a single global `int=3` to per-event-type `dict[EventType, int]`. Each of the 4 illustration event types (`generation`, `regeneration`, `cleanup`, `deletion`) gets its own consecutive-failure counter and warning threshold. Counters are **independent per type** — 3 generation failures do not bleed into the regeneration counter.

**Backwards compat**: `int=3` legacy form is preserved. Pydantic validator auto-expands `int` to `{"generation": 3, "regeneration": 3, "cleanup": 3, "deletion": 3}` on load. Existing settings.yaml files with `notify_threshold: 3` continue to work without migration.

**Partial dict semantics**: strict. `{"generation": 5}` means only `generation` is monitored; unconfigured types default to `INFINITY_THRESHOLD = inf` (never warn). This is intentional: explicit opt-in to monitoring per type. Documented in validator docstring + tests.

**Out of scope** (Phase 105+ candidates): `cleanup_route` failure tracking, `deletion` event_type usage, telemetry-driven chain reorder.

## Sub-projects delivered

### 1. Schema evolution (`apps/studio_api/routes/project_settings.py`)

```python
# BEFORE (Phase 102):
notify_threshold: int = 3  # consecutive failures before warning

# AFTER (Phase 104):
notify_threshold: int | dict[str, int] = 3  # int=legacy auto-expand; dict=per-event_type
```

`_validate_notify_threshold` Pydantic validator (mode="before"):

- `int` shape: validate `>= 1`, return expanded `{et: v for et in KNOWN_EVENT_TYPES}`
- `dict` shape: validate keys are subset of `KNOWN_EVENT_TYPES = ("generation", "regeneration", "cleanup", "deletion")` and values are `int >= 1`, return `dict(v)` (preserves partial dict — unconfigured keys remain absent)
- `empty dict {}` is valid (opt-out from all warnings)
- Anything else → `ValueError`

`_load_illustration_settings` (in `pipeline.py`) returns normalized dict view; callers always see `dict[str, int]` post-load.

### 2. Counter state widening (`packages/lingwen-illustrations/src/lingwen_illustrations/notifications.py`)

```python
# BEFORE (Phase 102):
_consecutive_failures: dict[str, int] = {}  # slug → count
_warning_emitted: dict[str, bool] = {}      # slug → emitted?

# AFTER (Phase 104):
_consecutive_failures: dict[tuple[str, str], int] = {}  # (slug, event_type) → count
_warning_emitted: dict[tuple[str, str], bool] = {}      # (slug, event_type) → emitted?
INFINITY_THRESHOLD = float("inf")                        # sentinel: never warn
```

API changes:

```python
def record_failure(
    project_slug: str,
    error: BaseException,
    *,
    project_root: Path,
    threshold: int | float,  # widened: int (configured) or float (INFINITY for opt-out)
    event_type: str,         # NEW Phase 104
) -> None:
    key = (project_slug, event_type)
    _consecutive_failures[key] = _consecutive_failures.get(key, 0) + 1
    count = _consecutive_failures[key]
    if count >= threshold and not _warning_emitted.get(key, False):
        _warning_emitted[key] = True
        _emit_failure_warning(project_slug, count, error, project_root, event_type)


def record_success(project_slug: str, event_type: str) -> None:  # NEW event_type arg
    key = (project_slug, event_type)
    _consecutive_failures[key] = 0
    _warning_emitted[key] = False


def _emit_failure_warning(
    project_slug: str,
    count: int,
    error: BaseException,
    project_root: Path,
    event_type: str,  # NEW
) -> None:
    event_id = str(ulid.ULID())
    audit_log.record_event(
        project_root,
        event=event_type,  # was hardcoded "generation" in Phase 102
        extra={"severity": "warning", "consecutive_failures": count, "last_error": str(error), "id": event_id},
    )
    publish(NotificationEvent(
        id=event_id, project_slug=project_slug,
        event_type=event_type,  # was hardcoded "generation" in Phase 102
        severity="warning",
        asset_id=None, asset_type=None, chapter_num=None, style_preset=None, provider=None,
        ts=now_iso(),
        extra={"consecutive_failures": count, "last_error": str(error)},
    ))
```

I095 EXTENDED via docstring only: "consecutive failure counter state — keyed per `(project_slug, event_type)` tuple — only via `record_failure/record_success` helpers, threshold emit exactly one warning per `(slug, event_type)` pair".

### 3. Pipeline integration (`packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py`)

New helper near existing `_notify_threshold` lookups (lines 261, 498):

```python
import math

INFINITY_THRESHOLD = math.inf


def _resolve_threshold(settings: dict, event_type: str) -> int | float:
    """Resolve notify_threshold for specific event_type.

    After Pydantic normalization, settings["notify_threshold"] is dict[str, int].
    Missing key → INFINITY_THRESHOLD (never warn for that event type).

    Defensive: if int legacy form slips through (shouldn't post-validation),
    returns int directly.
    """
    nt = settings.get("notify_threshold", 3)
    if isinstance(nt, (int, float)) and not isinstance(nt, bool):
        return nt
    return nt.get(event_type, INFINITY_THRESHOLD)
```

Caller changes — 2 sites:

**`generate_illustration`** (around line 260-320):
```python
# Phase 102 → Phase 104:
_notify_threshold = _resolve_threshold(effective_settings, "generation")
...
notifications.record_failure(
    slug, e, project_root=root,
    threshold=_notify_threshold, event_type="generation",  # NEW
)
...
notifications.record_success(project_slug, event_type="generation")  # NEW arg
```

**`regenerate_illustration`** (around line 497-549):
```python
# Phase 102 → Phase 104 (event_type="regeneration" — matches the
# pipeline's existing event_type channel for regeneration events):
_notify_threshold = _resolve_threshold(effective_settings, "regeneration")
...
notifications.record_failure(
    existing_meta.project_slug, e, project_root=root,
    threshold=_notify_threshold, event_type="regeneration",  # NEW
)
...
notifications.record_success(existing_meta.project_slug, event_type="regeneration")  # NEW arg
```

### 4. TypeScript type widening (`apps/dashboard/src/api/illustrations.ts`)

```typescript
// Phase 102:
notify_threshold: number;

// Phase 104:
notify_threshold: number | Record<NotifyEventType, number>;

type NotifyEventType = "generation" | "regeneration" | "cleanup" | "deletion";

export const NOTIFY_EVENT_TYPES: readonly NotifyEventType[] = [
  "generation", "regeneration", "cleanup", "deletion",
] as const;
```

Pick<ProjectSettings, ...> whitelist mirror unchanged (already includes `notify_threshold`).

### 5. Store sync (`apps/dashboard/src/stores/useProjectSettings.js` + spec)

```javascript
// Phase 102:
notifyThreshold: number | undefined

// Phase 104:
notifyThreshold: number | Record<NotifyEventType, number> | undefined
```

Helper functions on the store:

```javascript
function normalizeNotifyThreshold(v) {
  // int → 4-key dict; dict → unchanged; undefined → empty dict
  if (typeof v === "number") {
    return Object.fromEntries(NOTIFY_EVENT_TYPES.map((et) => [et, v]));
  }
  return v ?? {};
}
```

Tests (4 NEW in `useProjectSettings.spec.js`):
- normalize int → 4-key dict
- normalize dict → unchanged
- normalize undefined → empty dict
- round-trip dict through fetch → store → write

### 6. UI component (`apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue`)

New subsection **"Notify Thresholds"** placed between existing `chapter_overrides` and the existing notify_threshold slider (the slider is removed — replaced by the new table).

```
Notify Thresholds
┌─────────────────┬─────────────────┐
│ Event type      │ Threshold       │
├─────────────────┼─────────────────┤
│ generation      │ [3]             │
│ regeneration │ [3]             │
│ cleanup │ [Infinity]      │ ← disabled/grayed (not in settings.yaml)
│ deletion        │ [Infinity]      │ ← disabled/grayed
└─────────────────┴─────────────────┘
Hint: leave empty to never warn for that event type.
                                          [Reset all to default]
```

UX details:
- 4 fixed rows (NOT editable list — events are fixed)
- Each row: event_type label (read-only) + NumberInput bound to `notifyThreshold[eventType]`
- Reset-all button: sets all 4 to 3 (default)
- "Empty" = Infinity — rendered as gray "—" placeholder
- Save: writes dict (or int for legacy compat)

Tests (6 NEW in `ProjectSettingsIllustration.spec.ts`):
- renders 4 rows with current values
- NumberInput change updates dict
- reset-all button sets all 4 to 3
- empty input → displays "—" placeholder, persists Infinity
- legacy int response → all 4 rows show same threshold
- partial dict response → empty cells for unconfigured types

## Tests + regression guards

### G1-G8 (Phase 104 NEW) — `packages/lingwen-illustrations/tests/test_phase104_notify_threshold_per_event_type.py`

| G | Description |
|---|-------------|
| G1 | `_validate_notify_threshold` accepts `int=3`, normalizes to 4-key dict |
| G2 | `_validate_notify_threshold` accepts partial dict, preserves only configured keys |
| G3 | `_validate_notify_threshold` rejects unknown event_type key |
| G4 | `_validate_notify_threshold` rejects value < 1 |
| G5 | `_resolve_threshold(effective_settings, event_type)` returns configured int or INFINITY for missing |
| G6 | `_consecutive_failures` keys are `(project_slug, event_type)` tuples (NOT bare slug) — I095 EXTENDED |
| G7 | `record_failure(slug, e, ..., event_type="generation")` increments `(slug, "generation")` only; `(slug, "regeneration")` counter untouched |
| G8 | `record_success(slug, "generation")` resets only `(slug, "generation")`; `(slug, "regeneration")` counter untouched |

### New test files

| File | Tests |
|------|-------|
| `packages/lingwen-illustrations/tests/test_notifications_phase104.py` | 6 NEW (counter state per tuple + record_failure/record_success with event_type + warning isolation) |
| `apps/dashboard/src/stores/useProjectSettings.spec.js` | +4 NEW (normalize/denormalize) |
| `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.spec.ts` | +6 NEW (Notify Thresholds table) |

### Phase 102 preserved tests
- Existing Phase 102 tests in `test_notifications.py` use `_consecutive_failures[slug]` key access → will break with tuple keys. **1 test file update required** (rewrite key access to use tuple form).
- All other Phase 102 tests preserved unchanged (semantics: counter still increments, warning still emitted once per threshold crossing).

## Commits (~12 atomic)

| # | Task | Commit |
|---|------|--------|
| 1 | T1 | `docs(phase-104): design spec for notify_threshold per event_type` |
| 2 | T2 | `docs(phase-104): implementation plan` |
| 3 | T3 | `feat(phase-104): Pydantic validator accepts int\|dict[str,int] + normalizes to dict` |
| 4 | T3 (RED) | `test(phase-104): validator int expansion + partial dict + reject unknown key` |
| 5 | T4 | `feat(phase-104): notifications.py — tuple-keyed counter + INFINITY_THRESHOLD sentinel` |
| 6 | T4 | `test(phase-104): record_failure/record_success with event_type + tuple isolation` |
| 7 | T5 | `feat(phase-104): pipeline.py — _resolve_threshold helper + 2 caller sites pass event_type` |
| 8 | T6 | `feat(phase-104): api/illustrations.ts — notify_threshold widened to number \| Record<...>` |
| 9 | T6 | `feat(phase-104): useProjectSettings store normalize/denormalize + 4 tests` |
| 10 | T7 | `feat(phase-104): ProjectSettingsIllustration Notify Thresholds subsection + 6 tests` |
| 11 | T8 | `test(phase-104): 8 regression guards G1-G8 + I095 EXTENDED` |
| 12 | T9 | `docs(phase-104): CLAUDE.md v60.1 → v60.2 + handoff + BACKLOG + MEMORY sync` |

## Invariants

- **I095 EXTENDED via docstring only** (no new invariant):
  - Old scope: "consecutive failure counter state only via record_failure/record_success helpers, threshold emit exactly one warning"
  - New scope: "consecutive failure counter state — keyed per `(project_slug, event_type)` tuple — only via `record_failure/record_success` helpers, threshold emit exactly one warning per `(slug, event_type)` pair"
- `.lingwen/architecture.yml` I095 entry docstring widened
- `CLAUDE.md` I095 line text extended

## Validation gates

| Gate | Target |
|------|--------|
| Backend pytest (validator) | 6/6 NEW GREEN |
| Backend pytest (notifications + pipeline) | 6/6 NEW + 12/12 Phase 102 preserved (after 1 test file key update) |
| Backend pytest (Phase 104 regression guards) | 8/8 G1-G8 GREEN |
| Frontend vitest (useProjectSettings) | 12/12 Phase 102 preserved + 4/4 NEW |
| Frontend vitest (ProjectSettingsIllustration) | 7/7 Phase 103 preserved + 6/6 NEW |
| `pnpm tsc --noEmit` | 0 new errors (48 pre-existing baseline unchanged) |
| `ruff check` | 0 errors on introduced |

## Risks

1. **Pydantic field type widening**: `int | dict[str, int]` with `mode="before"` validator is the established pattern (Phase 102 used it for `int`); works for the union shape too.
2. **Counter key migration**: Phase 102 tests asserting `_consecutive_failures[slug]` will break. 1 test file update to use tuple keys (rewrite key access, no semantic change). Phase 104 task includes this fixup.
3. **Frontend type widening** to `number | Record<...>`: TS strict accepts union widening; confirmed via existing Pick pattern.
4. **Pydantic default-fill back-compat**: existing settings.yaml with `notify_threshold: 3` loads successfully via auto-expand; no migration step.

## Lessons anticipated (will be filled in handoff)

1. Tuple-keyed counter state isolates failure windows per event_type — preserves semantic clarity, slight memory overhead.
2. Pydantic validator widens from `int` to `int | dict` cleanly via `mode="before"`.
3. Strict partial-dict semantics (`Infinity` for missing keys) means explicit opt-in to monitoring per type.
4. Pipeline caller pattern: `_resolve_threshold(settings, event_type)` at the start of each function; pass to `record_failure` as threshold.
5. Phase 103's `default_models` pattern (cascade picker UI + Pick-based TS whitelist) was a clean template; Phase 104 reuses same UI shape (keyed table) since event_type is also small enumerable.

## Future work

- **cleanup_route failure tracking**: extend `record_failure(event_type="cleanup")` to LRU cleanup errors (Phase 105 candidate)
- **`deletion` event_type**: when DELETE endpoint is added for illustrations, track via `record_failure(event_type="deletion")`
- **telemetry-driven chain reorder**: gated on Phase 102 failure tracker data accumulation (still on BACKLOG)
- **ARCHDEBT-REAL continuation**: if requested (still on BACKLOG)

## References

- Phase 102 spec: `docs/superpowers/specs/2026-09-20-phase-102-settings-persistence-extension-design.md`
- Phase 102 handoff: `docs/superpowers/handoffs/2026-09-20-phase-102-settings-persistence-extension-handoff.md`
- Phase 103 spec: `docs/superpowers/specs/2026-09-20-phase-103-per-chapter-default-models-design.md` (template for small extension pattern)
- Phase 103 handoff: `docs/superpowers/handoffs/2026-09-20-phase-103-per-chapter-default-models-handoff.md`
- I095 invariant: `.lingwen/architecture.yml` (Phase 102)
- I094 invariant: `.lingwen/architecture.yml` (Phase 102, EXTENDED in Phase 103)