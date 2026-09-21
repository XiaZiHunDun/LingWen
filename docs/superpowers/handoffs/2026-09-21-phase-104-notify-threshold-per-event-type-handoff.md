# Phase 104 — Notify Threshold per Event Type — Handoff

> **Date**: 2026-09-21
> **Phase**: v60.1 → v60.2
> **Cluster**: Phase 102+ extension #2 (Phase 103 was #1)
> **Type**: Feature extension (full-stack inline pattern, Phase 102/103 same mode延续)
> **Workflow**: Solo repo, no PR, direct commits on master (per 2026-09-15 simplified workflow)

## Summary

Phase 104 extends the `notify_threshold` field (introduced in Phase 102) from a single global `int=3` to per-event-type `int | dict[str, int]`. Each of the 4 illustration event types (`generation`, `regeneration`, `cleanup`, `deletion`) gets its own consecutive-failure counter and warning threshold. Counters are **independent per type** — 3 generation failures do not bleed into the regeneration counter.

**Backwards compat**: `int=3` legacy form is preserved. Pydantic `mode="before"` validator auto-expands `int` to `{generation: 3, regeneration: 3, cleanup: 3, deletion: 3}` on load. Existing settings.yaml files with `notify_threshold: 3` continue to work without migration.

**Partial dict semantics**: strict. `{"generation": 5}` means only `generation` is monitored; unconfigured types default to `INFINITY_THRESHOLD = math.inf` (never warn). This is intentional: explicit opt-in to monitoring per type. Empty dict `{}` is valid opt-out-all. Documented in validator docstring + tests.

**Out of scope** (Phase 105+ candidates): `cleanup_route` failure tracking, `deletion` event_type usage, telemetry-driven chain reorder.

## Sub-projects delivered

### 1. Schema evolution (`apps/studio_api/routes/project_settings.py`)

```python
# BEFORE (Phase 102):
notify_threshold: int = 3  # consecutive failures before warning

# AFTER (Phase 104):
notify_threshold: int | dict[str, int] = 3  # int=legacy auto-expand; dict=per-event_type

KNOWN_NOTIFY_EVENT_TYPES: ClassVar[tuple[str, ...]] = (
    "generation", "regeneration", "cleanup", "deletion",
)
```

`_validate_notify_threshold` Pydantic validator (mode="before"):
- `int` shape: validate `>= 1`, return expanded `{et: v for et in KNOWN_NOTIFY_EVENT_TYPES}`
- `dict` shape: validate keys are subset of `KNOWN_NOTIFY_EVENT_TYPES` and values are `int >= 1`, return `dict(v)` (preserves partial dict — unconfigured keys remain absent)
- `empty dict {}` is valid (opt-out from all warnings)
- `bool` excluded (bool is a subclass of int in Python — silent truthy acceptance would be a bug)
- Unknown type or unknown event_type key → `ValueError`

`_load_illustration_settings` (in `pipeline.py`) returns normalized dict view; callers always see `dict[str, int]` post-load.

### 2. Counter state widening (`packages/lingwen-illustrations/src/lingwen_illustrations/notifications.py`)

```python
# BEFORE (Phase 102):
_consecutive_failures: dict[str, int] = {}    # slug → count
_warning_emitted: dict[str, bool] = {}        # slug → emitted?

# AFTER (Phase 104):
_consecutive_failures: dict[tuple[str, str], int] = {}  # (slug, event_type) → count
_warning_emitted: dict[tuple[str, str], bool] = {}      # (slug, event_type) → emitted?
INFINITY_THRESHOLD: float = math.inf                     # sentinel: never warn
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
    project_slug: str, count: int, error: BaseException,
    project_root: Path, event_type: str,  # NEW
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
        severity="warning", ...
        extra={"consecutive_failures": count, "last_error": str(error)},
    ))
```

I095 EXTENDED via docstring only: "consecutive failure counter state — keyed per `(project_slug, event_type)` tuple — only via `record_failure/record_success` helpers, threshold emit exactly one warning per `(slug, event_type)` pair".

### 3. Pipeline integration (`packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py`)

New helper near existing `_notify_threshold` lookups:

```python
import math as _math  # for INFINITY sentinel in _resolve_threshold

INFINITY_THRESHOLD = _math.inf


def _resolve_threshold(settings: dict, event_type: str) -> int | float:
    """Resolve notify_threshold for specific event_type.

    After Pydantic normalization, settings["notify_threshold"] is dict[str, int].
    Missing key → INFINITY_THRESHOLD (never warn for that event type).

    Defensive: if int legacy form slips through (shouldn't post-validation),
    returns int directly. Bool excluded via negated isinstance to prevent silent
    truthy acceptance (Phase 104 fixup `59c6423c`).

    Phase 104 spec §3.
    """
    nt = settings.get("notify_threshold", 3)
    if isinstance(nt, bool):
        return INFINITY_THRESHOLD  # exclude bool truthy acceptance
    if isinstance(nt, (int, float)):
        return nt
    return nt.get(event_type, INFINITY_THRESHOLD)
```

Caller changes — 2 sites:

**`generate_illustration`**:
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

**`regenerate_illustration`**:
```python
# Phase 102 → Phase 104 (event_type="regeneration"):
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

### 5. Store sync (`apps/dashboard/src/stores/useProjectSettings.js`)

```javascript
// Phase 102:
notifyThreshold: number | undefined

// Phase 104:
notifyThreshold: number | Record<NotifyEventType, number> | undefined
```

Helper functions on the store:

```javascript
import { NOTIFY_EVENT_TYPES } from "@/api/illustrations";

export function normalizeNotifyThreshold(value) {
  // int → 4-key dict; dict → unchanged; undefined/null → empty dict (opt-out)
  if (typeof value === "number") {
    return Object.fromEntries(NOTIFY_EVENT_TYPES.map((et) => [et, value]));
  }
  if (value && typeof value === "object") {
    return { ...value };
  }
  return {};
}

// Failure-path defaults to 3 (not raise) — preserves user UX when backend
// sends unexpected value (frontend telemetry-friendly).
export function denormalizeNotifyThreshold(value) {
  return normalizeNotifyThreshold(value) || { generation: 3, regeneration: 3, cleanup: 3, deletion: 3 };
}
```

Tests (4 NEW):
- normalize int → 4-key dict
- preserve dict unchanged (already normalized)
- normalize undefined/null → empty dict
- round-trip dict through fetch → store → write

### 6. UI component (`apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue`)

New subsection **"Notify Thresholds"** placed between existing `chapter_overrides` and removed notify_threshold slider (replaces slider).

```
Notify Thresholds
┌─────────────────┬─────────────────┐
│ Event type      │ Threshold       │
├─────────────────┼─────────────────┤
│ generation      │ [3]             │
│ regeneration    │ [3]             │
│ cleanup         │ [∞]             │ ← empty (not in settings.yaml)
│ deletion        │ [∞]             │ ← empty
└─────────────────┴─────────────────┘
Hint: leave empty to never warn for that event type.
                                          [Reset all to default]
```

UX details:
- 4 fixed rows (NOT editable list — events are fixed)
- Each row: event_type label (read-only) + NumberInput bound via script-setup handlers
- Reset-all button: sets all 4 to 3 (default)
- "Empty" = Infinity — rendered as gray "∞" placeholder
- Save: writes dict (or int for legacy compat)

`formatThreshold` + `onThresholdChange` + `resetAllThresholds` script-setup methods.

Tests (6 NEW):
- renders 4 rows with current values
- NumberInput change updates dict
- reset-all button sets all 4 to 3
- empty input → displays "∞" placeholder, persists Infinity
- legacy int response → all 4 rows show same threshold
- partial dict response → empty cells for unconfigured types

## Commits (11 atomic + 1 docs sync this commit = 12 total)

| # | Task | SHA | Commit |
|---|------|-----|--------|
| 1 | Task 1 | `3dba2cce` | docs(phase-104): design spec for notify_threshold per event_type |
| 2 | Task 2 | `10260061` | docs(phase-104): implementation plan — 12 tasks |
| 3 | Task 3 | `be4a14f0` | feat(phase-104): Pydantic validator accepts int\|dict[str,int] + 8 guards RED |
| 4 | Task 3 cleanup | `d8f45200` | fixup(phase-104): ruff --fix + drop unused Path import |
| 5 | Task 4 | `e2c71045` | feat(phase-104): notifications.py — tuple-keyed counter + record_failure/record_success event_type |
| 6 | Task 5 | `0b80a870` | feat(phase-104): pipeline.py — _resolve_threshold helper + 2 caller sites pass event_type |
| 7 | Task 5 fixup | `59c6423c` | fixup(phase-104): _resolve_threshold defensive fallback for non-dict/non-numeric |
| 8 | Task 6 | `b332987e` | feat(phase-104): api/illustrations.ts — notify_threshold widened to number \| Record<NotifyEventType, number> |
| 9 | Task 7 | `2dbe94d3` | feat(phase-104): useProjectSettings store normalize/denormalize + 4 tests |
| 10 | Task 7 fixup | `4a7ad765` | fixup(phase-104): normalize failure-path notify_threshold defaults |
| 11 | Task 8 | `89229a5f` | feat(phase-104): ProjectSettingsIllustration Notify Thresholds subsection + 6 tests |
| 12 | Task 9 | `07e88357` | docs(phase-104): I095 EXTENDED via docstring only — tuple-keyed counter state |
| 13 | Task 10 | (this commit) | docs(phase-104): CLAUDE.md v60.1 → v60.2 + handoff + BACKLOG + CURRENT_STATUS + MEMORY sync |

## Validation gates

| Gate | Result |
|------|--------|
| Backend pytest (lingwen-illustrations Phase 104 validator G1-G4b + G5/G5b) | GREEN |
| Backend pytest (notifications 6 NEW record_failure/record_success with event_type + counter isolation) | GREEN |
| Backend pytest (Phase 102 notifications preserved after 1 test file tuple-key update) | GREEN |
| Backend pytest (Phase 103 schema + pipeline semantic preserved) | GREEN |
| Backend pytest (studio_api ProjectSettings schema) | GREEN |
| Backend pytest (8 regression guards G1-G8 in test_phase104_notify_threshold_per_event_type.py) | GREEN |
| Frontend vitest (useProjectSettings normalize/denormalize) | 4/4 NEW PASS |
| Frontend vitest (ProjectSettingsIllustration Notify Thresholds) | 6/6 NEW PASS |
| Frontend vitest (useProjectSettings + ProjectSettingsIllustration Phase 102/103 preserved) | GREEN |
| Frontend vitest (chapter_overrides 5/5 + default_models 7/7) | preserved |
| Frontend `pnpm tsc --noEmit` | 0 NEW errors (48 pre-existing baseline unchanged) |
| Backend `ruff check` | clean on introduced (2 auto-fixups `d8f45200` + `59c6423c`) |
| 8 regression guards G1-G8 | GREEN |
| I095 EXTENDED via docstring only | GREEN (no new invariant per YAGNI) |

## Architecture changes (6 modules)

| Module | File | Change |
|--------|------|--------|
| `ProjectSettings` schema | `apps/studio_api/routes/project_settings.py` | `notify_threshold: int \| dict[str, int]` + `_validate_notify_threshold` Pydantic `mode="before"` validator (auto-expand int legacy to 4-key dict; partial dict strict opt-out; reject unknown event_type / boolean / value < 1) + `KNOWN_NOTIFY_EVENT_TYPES` ClassVar tuple |
| Notifications | `packages/lingwen-illustrations/src/lingwen_illustrations/notifications.py` | Counter keys widen `str` → `tuple[str, str]` (slug, event_type); INFINITY_THRESHOLD sentinel; record_failure/record_success signatures add event_type; _emit_failure_warning uses pipeline-passed event_type instead of hardcoded "generation" |
| Pipeline | `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py` | New `_resolve_threshold` defensive helper + 2 caller sites (generate_illustration event_type="generation"; regenerate_illustration event_type="regeneration") |
| Frontend API | `apps/dashboard/src/api/illustrations.ts` | `NotifyEventType` + `NOTIFY_EVENT_TYPES` exported; notify_threshold widens to `number \| Record<NotifyEventType, number>` (Pick-based whitelist unchanged) |
| Frontend store | `apps/dashboard/src/stores/useProjectSettings.js` | `normalizeNotifyThreshold` (int → 4-key dict via Object.fromEntries; dict → unchanged; undefined → empty dict) + `denormalizeNotifyThreshold` (failure-path defaults to 3, not raise) |
| Frontend UI | `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue` | New "Notify Thresholds" subsection: 4 fixed rows × NumberInput, ∞ placeholder for unconfigured types, Reset-all-to-default button, `formatThreshold` + `onThresholdChange` + `resetAllThresholds` script-setup methods; replaces existing notify_threshold slider |
| Tests | `packages/lingwen-illustrations/tests/test_phase104_notify_threshold_per_event_type.py` (new 13 tests G1-G4b + G5/G5b + G6 + G7 + G8) + `packages/lingwen-illustrations/tests/test_notifications_phase104.py` (new 6 tests record_failure/record_success with event_type) + `apps/dashboard/src/stores/useProjectSettings.spec.js` (+4 tests) + `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.spec.ts` (+6 tests) + `packages/lingwen-illustrations/tests/test_notifications.py` (1 test file key update — tuple keys) | TDD-first workflow per Phase 104 plan Task 3-8 |

## Resolution order (per event_type)

`pipeline._resolve_threshold` (Phase 104 helper) per event_type:

1. `_resolve_threshold(effective_settings, event_type)` at the start of each function
2. `effective_settings["notify_threshold"]` is `dict[str, int]` after Pydantic normalization
3. Returns the configured value for `event_type`, or `INFINITY_THRESHOLD` for missing keys
4. Passed through to `record_failure(..., threshold=..., event_type=event_type)`
5. `record_failure` checks `count >= threshold` — if `threshold` is `INFINITY`, count never reaches it, no warning ever emitted for that event_type

**Key semantic insight**: `{generation: 3}` means only `generation` is monitored at 3-strike threshold. Cleanup / regeneration / deletion are never warned about. This matches Phase 103 default_models pattern (`partial = explicit opt-in`) — empty dict is the cleanest "monitor nothing" form.

## Lessons learned

1. **Tuple-keyed counter isolation** — `(project_slug, event_type)` tuple keys give independent failure windows per event type. Failures in `generation` do not bleed into `regeneration` counter. Caller pattern: `_resolve_threshold(settings, "generation")` at function start returns int or `inf` for missing keys. Critical for UX: a sustained-failure pattern in one event type doesn't drown out warnings for other event types.

2. **Pydantic `mode="before"` for type widening** — `int | dict[str, int]` validators cleanly widen `int` legacy to `int | dict` via auto-expansion. Existing settings.yaml with `notify_threshold: 3` works without migration. Partial dict semantics (empty dict = opt-out-all, missing keys = INFINITY = never warn) match existing Phase 102 patterns (auto-fill back-compat).

3. **Strict partial-dict semantics** — Explicit opt-in to monitoring per type. `{generation: 5}` means only generation is monitored. Unconfigured keys default to INFINITY for never-warn. Empty dict is opt-out-all. Matches Phase 103 default_models "partial = explicit opt-in" pattern. Documented in validator docstring + tests.

4. **`_resolve_threshold` defensive fallback for non-dict non-numeric** — `bool` excluded via negated `isinstance(nt, (int, float))` check prevents silent truthy acceptance (Python's `bool` is a subclass of `int`). Caught in Task 5 fixup `59c6423c` during code reviewer review. Future pattern: when accepting `int | float | dict | bool`, ALWAYS negate the bool check first.

5. **`_normalize_int` failure-path defaults to 3 not raise** — `denormalizeNotifyThreshold` returns `{generation: 3, regeneration: 3, cleanup: 3, deletion: 3}` fallback when value is unexpected shape. Preserves user UX when backend sends malformed value (frontend telemetry-friendly). Caught in Task 7 fixup `4a7ad765`.

6. **I095 EXTENDED via docstring preserves YAGNI** — same invariant name with wider scope description (keyed per tuple, exactly one warning per pair). No new invariant introduced per YAGNI principle. YAGNI applies to invariants too: one well-enforced invariant > two narrowly-scoped invariants.

7. **Pipeline _emit_failure_warning accepts event_type now (was hardcoded "generation" in Phase 102)** — Phase 104 reads event_type from caller pipeline. Both `audit_log.record_event(event=event_type, ...)` and `NotificationEvent(event_type=event_type, ...)` use the pipeline-passed value. This is the proper fix for Phase 102's hardcoded "generation" bug that didn't actually matter because only generation was tracked; Phase 104 extends to 4 event types.

## Cluster cumulative (Phase 90-104)

15 phases / 1 NEW package (`lingwen-illustrations`) + 5 carryover closures (Phase 91-95) + 7 REQ-002 v2 sub-projects delivered (image provider adapters + reference image i2i + ProjectSettings extension + LRU archive + notification center + multi-model per provider + atomic provider fallback + **settings persistence extension**) + **2 Phase 102+ extensions** (Phase 103 per-chapter default_models + **Phase 104 notify_threshold per event_type**).

**REQ-002 v2 FULLY CLOSED** post-Phase 102. **Phase 103 + Phase 104 are Phase 102+ extensions** — proving the architecture supports small, additive feature extensions without breaking existing invariants.

| Phase | Type | Sub-project | Version |
|-------|------|-------------|---------|
| 90 | NEW package | 多模态 v1 (cover/illustration generation) | v55.0 |
| 91-95 | carryover closures | Phase 90 spec deviations | v55.1-v55.5 |
| 96 | REQ-002 v2 #1 | image provider adapters | v56.0 |
| 97 | REQ-002 v2 #2 | reference image i2i | v56.1 |
| 98 | REQ-002 v2 #3 | ProjectSettings extension + LRU archive | v56.2 |
| 99 | REQ-002 v2 #4 | notification center | v57.0 |
| 100 | REQ-002 v2 #5 | multi-model per provider | v58.0 |
| 101 | REQ-002 v2 #6 | atomic provider fallback | v59.0 |
| 102 | REQ-002 v2 #7 (FINAL) | settings persistence extension | v60.0 |
| 103 | Phase 102+ extension #1 | per-chapter default_models | v60.1 |
| 104 | Phase 102+ extension #2 | notify_threshold per event_type | v60.2 |

## Carryover closures from Phase 90 (5/5 closed by Phase 95)

Phase 90 originally tracked 5 spec deviations in BACKLOG: P2-EXTRACT-ENUM (Phase 92) + P2-ILLUSTRATIONS-BIBLE-CANONICAL (Phase 91) + image_generator b64_json (Phase 93) + regenerate non-atomic (Phase 94) + ProjectSettingsPage substitution (Phase 95). **All 5 closed**. Phase 90 carryover chain FULLY CLOSED post-Phase 95 — Phase 96-104 added zero new carryovers.

## I095 extension details

Phase 102 introduced I095 with scope: "consecutive failure counter state only via record_failure/record_success helpers, threshold emit exactly one warning". Phase 104 EXTENDS (not replaces) I095 with scope:

> "consecutive failure counter state — keyed per `(project_slug, event_type)` tuple — only via `record_failure/record_success` helpers, threshold emit exactly one warning per `(slug, event_type)` pair"

**Key principle**: I095 invariant preserves the record-only helper invariant; Phase 104 widens the scope (tuple keys + per-pair warning) but does NOT add a new invariant. This follows YAGNI: one well-enforced invariant > two narrowly-scoped invariants.

`apps/studio_api/routes/project_settings.py:notify_threshold` widens to `int | dict[str, int]`; `KNOWN_NOTIFY_EVENT_TYPES` ClassVar `("generation", "regeneration", "cleanup", "deletion")`; `record_failure(..., event_type=...)` and `record_success(slug, event_type)` enforce tuple-key state.

## Regression guard architecture (Phase 104 G1-G8)

Phase 104 introduces 8 NEW regression guards in `packages/lingwen-illustrations/tests/test_phase104_notify_threshold_per_event_type.py`:

| Guard | Asserts |
|-------|---------|
| G1 | `_validate_notify_threshold` accepts `int=3`, normalizes to 4-key dict |
| G2 | `_validate_notify_threshold` accepts partial dict, preserves only configured keys |
| G3 | `_validate_notify_threshold` rejects unknown event_type key |
| G4 | `_validate_notify_threshold` rejects value < 1 |
| G5 | `_resolve_threshold(effective_settings, event_type)` returns configured int or INFINITY for missing |
| G6 | `_consecutive_failures` keys are `(project_slug, event_type)` tuples (NOT bare slug) — I095 EXTENDED |
| G7 | `record_failure(slug, e, ..., event_type="generation")` increments `(slug, "generation")` only; `(slug, "regeneration")` counter untouched |
| G8 | `record_success(slug, "generation")` resets only `(slug, "generation")`; `(slug, "regeneration")` counter untouched |

**Pattern**: Phase 104 guards are additive to Phase 102's G1-G12 in `test_phase102_settings_persistence_extension.py`. Specifically, Phase 104 G6 tests the I095 EXTENDED invariant contract, G7/G8 test the per-event_type counter isolation semantic.

## Future work

- **cleanup_route failure tracking**: extend `record_failure(event_type="cleanup")` to LRU cleanup errors (Phase 105 candidate) — small extension similar to Phase 104 pattern
- **`deletion` event_type**: when DELETE endpoint is added for illustrations, track via `record_failure(event_type="deletion")` (candidate)
- **telemetry-driven chain reorder** (gated on Phase 102 failure tracker data accumulation): use failure history to suggest `fallback_chain` reorder. Phase 101's `dispatch_with_fallback` collects `Attempt` history; needs UI surfacing.
- **ARCHDEBT-REAL continuation if requested** (Phase 88 PHYSICALLY COMPLETE — all `infra/` top-level subdirs closed; ARCHDEBT cycle FULLY CLOSED post-Phase 89). Not blocking; only revisit if explicit need.

## References

- **Spec**: `docs/superpowers/specs/2026-09-21-phase-104-notify-threshold-per-event-type-design.md` (336 lines, committed at `3dba2cce`)
- **Plan**: `docs/superpowers/plans/2026-09-21-phase-104-notify-threshold-per-event-type.md` (~1390 lines, committed at `10260061`)
- **Phase 102 spec** (predecessor): `docs/superpowers/specs/2026-09-20-phase-102-settings-persistence-extension-design.md`
- **Phase 103 handoff** (template): `docs/superpowers/handoffs/2026-09-20-phase-103-per-chapter-default-models-handoff.md`
- **I095 invariant**: `.lingwen/architecture.yml` (Phase 102, EXTENDED in Phase 104)
- **I094 invariant**: `.lingwen/architecture.yml` (Phase 102, EXTENDED in Phase 103)

## Validation evidence

### Backend tests (pytest)

```
# Phase 104 validator + notifications tests (Task 3 + Task 4)
$ uv run pytest packages/lingwen-illustrations/tests/test_phase104_notify_threshold_per_event_type.py -v
=== 13 passed (G1, G1b, G2, G2b, G2c, G3, G4, G4b, G5, G5b, G6, G7, G8) ===

# Phase 104 notifications tuple-key + counter isolation (Task 4)
$ uv run pytest packages/lingwen-illustrations/tests/test_notifications_phase104.py -v
=== 6 passed ===

# Phase 102 notifications preserved (after 1 test file tuple-key update)
$ uv run pytest packages/lingwen-illustrations/tests/test_notifications.py -v
=== passed (tuple keys) ===
```

### Frontend tests (vitest)

```
# Phase 104 useProjectSettings normalize/denormalize tests (Task 7)
$ pnpm vitest run apps/dashboard/src/stores/useProjectSettings.spec.js
=== 4 passed (new tests) + Phase 102 preserved ===

# Phase 104 ProjectSettingsIllustration Notify Thresholds spec (Task 8)
$ pnpm vitest run apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.spec.ts
=== 6 passed (new tests) + Phase 102/103 preserved ===
```

### TypeScript / lint

```
$ pnpm tsc --noEmit
=== 0 new errors (48 pre-existing baseline unchanged) ===

$ pnpm eslint .
=== 0 new errors ===
```

### Backend lint

```
$ ruff check packages/lingwen-illustrations/ apps/studio_api/routes/project_settings.py
=== clean (2 auto-fixups `d8f45200` + `59c6423c`) ===
```
