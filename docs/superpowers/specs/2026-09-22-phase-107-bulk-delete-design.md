# Phase 107 — Bulk Delete Illustration Endpoint — Design Spec

> **Date**: 2026-09-22
> **Phase**: v60.4 → v60.5
> **Cluster**: Phase 102+ extension #5 (Phase 103 was #1, Phase 104 was #2, Phase 105 was #3, Phase 106 was #4)
> **Type**: Backend + frontend medium extension (1 backend route refactor + 1 new endpoint + 1 new composable + 1 store + 1 typed wrapper + 1 component modification + 3 test files)
> **Workflow**: Solo repo, no PR, direct commits on master (per 2026-09-15 simplified workflow)

## Summary

Phase 107 introduces a `bulk_delete_assets` endpoint and multi-select UX so users can delete up to 50 illustrations in a single request instead of clicking through 50 separate `<NPopconfirm>` confirmations. The single-asset `delete_asset` route (Phase 106) is preserved as a thin wrapper that delegates to a NEW module-private helper `_delete_asset_inner`. The bulk endpoint reuses this helper for each asset in a sequential for-loop, so per-asset failure tracking, audit log entries, and notifications publish — **all of I090/I091/I095** — happen identically for single and bulk deletes. The single observable difference is `extra={"trigger": "manual", "mode": "bulk"}` in the audit log + NotificationEvent for bulk deletes, enabling "bulk vs single" analytics downstream.

**Architectural changes**:
1. **Refactor** `apps/studio_api/routes/illustrations.py:delete_asset` route handler to delegate to NEW module-private helper `_delete_asset_inner(slug, asset_id, *, project_root, threshold) -> Literal["ok","not_found","load_error","store_error"]`. The existing 5-path failure tracking logic moves verbatim into the helper; the route handler becomes a thin wrapper that maps `status → HTTPException`. External API behavior unchanged.
2. **NEW endpoint** `DELETE /api/illustrations?slug=...&ids=...` — sequential for-loop over `set(ids.split(","))` (deduped), limit 50, returns `200 + {deleted, failed, summary}`; `422` on empty ids or >50 after dedupe; `404` if `slug` doesn't resolve to a project via `_project_root_for`. Each per-asset invocation calls `_delete_asset_inner`.
3. **NEW composable** `apps/dashboard/src/composables/useBulkDeleteToast.ts` — encapsulates Naive UI `useMessage()` (success/partial/error toast) + `<NDrawer>` (failure list drawer with "重试全部" affordance). Both `LibraryPage` and `WriteWorkspacePage` reuse it.
4. **MODIFY** `apps/dashboard/src/components/illustrations/IllustrationGallery.vue` — adds local `selection: Set<string>` state, checkbox overlay per card (top-left), sticky bottom bulk action bar (visible when `selection.size > 0`), and a confirmation `<NPopconfirm>` (Phase 106 UX pattern). Emits `bulk-deleted(result)` so parent pages can refetch lists.
5. **NEW typed wrapper** `apps/dashboard/src/api/illustrations.ts:bulkDeleteAssets(slug, assetIds) -> BulkDeleteResult`.
6. **MODIFY Pinia store** `useIllustrationStore.js` — adds `bulkDeleteAssets(slug, assetIds)` method.

**Invariant extensions** (via docstring only — YAGNI, matches Phase 103+ pattern):
- **I090 EXTENDED**: `bulk_delete_assets` is the **5th** caller of `audit_log.record_event` + `lru_cleanup` (after `pipeline.generate_illustration` + `pipeline.regenerate_illustration` + `cleanup_route` + `delete_asset`).
- **I091 EXTENDED**: `bulk_delete_assets` is the **5th** double-write site (audit_log + publish, same ULID per asset).
- **I095 EXTENDED via docstring** (5th extension): per-(slug, "deletion") counter state machine unchanged; bulk inherits the same per-asset `record_failure`/`record_success` semantics.

**Out of scope** (future candidates):
- Telemetry-driven chain reorder — still gated on Phase 102-107 data accumulation
- Bulk REGENERATE — YAGNI (Phase 94 atomic regenerate + PUT already handles single bulk intent)
- Delete from NotificationsPage dropdown — separate UX (Phase 108+)
- Bulk archive/zip/restore — YAGNI
- Bulk delete with chapter filter (e.g., "delete all stickers in chapter 5") — Phase 108+ if requested

## Sub-projects delivered

### 1. Backend helper refactor: extract `_delete_asset_inner`

**Rationale**: Without a shared helper, the bulk endpoint would have to duplicate Phase 106's 5-path failure tracking logic (~40 lines of conditional `record_failure`/`record_success` + `audit_log.record_event` + `notifications.publish` calls). The single-asset `delete_asset` route handler would also bloat further (currently ~60 lines). Extracting `_delete_asset_inner` deduplicates the per-asset logic and gives bulk a clean iteration target.

**NEW** (`apps/studio_api/routes/illustrations.py` module-level):

```python
from typing import Literal

async def _delete_asset_inner(
    slug: str,
    asset_id: str,
    *,
    project_root: Path | None,
    threshold: int | float,
    mode: Literal["single", "bulk"] = "single",
) -> Literal["ok", "not_found", "load_error", "store_error"]:
    """Phase 107: shared per-asset delete + failure tracking.

    Used by BOTH:
      - delete_asset route (DELETE /{asset_id}, Phase 106 5-path) — mode="single"
      - bulk_delete_assets route (DELETE ?ids=...&slug=..., Phase 107 sequential loop) — mode="bulk"

    Phase 106 5-path lives here verbatim:
      1. project_root is None (LoadError upstream) → record_failure(project_root=None)
         → return "load_error"
      2. asset not found (no storage entry) → record_success (no-op success, defensive reset)
         → return "not_found"
      3. StoreError on storage.delete_asset → record_failure(project_root=root)
         → return "store_error"
      4. success → record_success + audit_log.record_event + notifications.publish (same ULID)
         → return "ok"

    `extra={"trigger": "manual", "mode": mode}` records single vs bulk in audit_log
    and NotificationEvent for downstream analytics.
    """
    # ... full Phase 106 delete_asset body minus HTTPException raises
```

**REFACTOR** of `delete_asset` route (`apps/studio_api/routes/illustrations.py`):

**Before** (Phase 106 lines 95-178):
```python
@app.delete("/api/illustrations/{asset_id}")
def delete_asset(asset_id: str, project_slug: str = Query(...)) -> dict:
    # ~60 lines of inline try/except + record_failure/record_success
    # + 404/500 HTTPException raises
```

**After**:
```python
@app.delete("/api/illustrations/{asset_id}")
async def delete_asset(asset_id: str, project_slug: str = Query(...)) -> dict:
    try:
        project_root = project_root_for(project_slug)
    except LoadError as e:
        # project_root is None — caller handles through helper too
        status = await _delete_asset_inner(
            project_slug, asset_id,
            project_root=None,
            threshold=notifications.resolve_threshold({}, "deletion"),
            mode="single",
        )
        raise HTTPException(404, detail=_err_detail(e)) from e

    settings = _load_deletion_settings(project_root)
    threshold = notifications.resolve_threshold(settings, "deletion")
    status = await _delete_asset_inner(
        project_slug, asset_id,
        project_root=project_root,
        threshold=threshold,
        mode="single",
    )
    if status == "not_found":
        raise HTTPException(404, detail=f"asset {asset_id} not found")
    if status == "store_error":
        raise HTTPException(500, detail=_err_detail(StoreError("delete failed")))
    return {"deleted": asset_id}
```

External HTTP API unchanged; all Phase 106 T1-T6 + G1-G6 guards preserved GREEN.

### 2. NEW bulk_delete_assets endpoint

**NEW** (`apps/studio_api/routes/illustrations.py`):

```python
@app.delete("/api/illustrations")
async def bulk_delete_assets(
    slug: str = Query(..., description="Project slug"),
    ids: str = Query(..., description="Comma-separated asset UUIDs, 1..50 after dedupe"),
) -> dict:
    """Phase 107: bulk delete up to 50 illustrations.

    Returns 200 + {deleted, failed, summary} — per-asset iteration; each
    asset follows the SAME 5-path contract as single-delete via _delete_asset_inner.

    Returns:
      200 OK + {deleted: [...], failed: [{id, status}, ...], summary: {total, ok, fail}}
      422 - empty ids or > 50 after dedupe
      404 - slug doesn't resolve to a project via _project_root_for

    Each per-asset failure tracking record_failure/record_success + audit_log +
    notifications.publish executes sequentially in asset_id order.
    """
    raw_ids = [a.strip() for a in ids.split(",") if a.strip()]
    asset_ids = list(dict.fromkeys(raw_ids))  # dedupe preserving order
    if not asset_ids:
        raise HTTPException(422, detail="ids must be 1..50 comma-separated asset_ids")
    if len(asset_ids) > 50:
        raise HTTPException(422, detail="max 50 ids per request")

    try:
        project_root = project_root_for(slug)
    except LoadError as e:
        raise HTTPException(404, detail=_err_detail(e)) from e

    settings = _load_deletion_settings(project_root)
    threshold = notifications.resolve_threshold(settings, "deletion")

    deleted: list[str] = []
    failed: list[dict] = []
    for aid in asset_ids:
        status = await _delete_asset_inner(
            slug, aid, project_root=project_root, threshold=threshold, mode="bulk",
        )
        if status == "ok":
            deleted.append(aid)
        else:
            failed.append({"id": aid, "status": status})

    return {
        "deleted": deleted,
        "failed": failed,
        "summary": {"total": len(asset_ids), "ok": len(deleted), "fail": len(failed)},
    }
```

**Route registration order**: FastAPI matches routes in declaration order. `bulk_delete_assets` is `DELETE /api/illustrations` (no path segment); `delete_asset` is `DELETE /api/illustrations/{asset_id}` (with path segment). These are **different path templates** so there is no order collision — FastAPI correctly dispatches `DELETE /api/illustrations` to `bulk_delete_assets` regardless of order. No registration-order change required.

**Per-asset iteration semantics**:
- **Sequential** (not parallel) — preserves audit_log.jsonl append order + NotificationStream SSE arrival order for downstream consumers. Parallel execution would interleave events; out-of-order audit log is harder to review chronologically.
- **Idempotent** — re-submitting the same `ids` returns same `deleted[]` (already-gone assets → `not_found` per Phase 106 no-op success, which is added to `failed[]`).
- **Best-effort, partial-failure aware** — each asset's outcome independent; one storage failure doesn't abort the batch.

### 3. NEW typed wrapper

**NEW** (`apps/dashboard/src/api/illustrations.ts`):

```typescript
export interface BulkDeleteFailedItem {
  id: string
  status: 'not_found' | 'load_error' | 'store_error'
}

export interface BulkDeleteResult {
  deleted: string[]
  failed: BulkDeleteFailedItem[]
  summary: {
    total: number
    ok: number
    fail: number
  }
}

export async function bulkDeleteAssets(
  slug: string,
  assetIds: string[],
): Promise<BulkDeleteResult> {
  const response = await fetch(
    `${BASE_URL}/illustrations?slug=${encodeURIComponent(slug)}&ids=${assetIds.map(encodeURIComponent).join(',')}`,
    { method: 'DELETE', headers: { 'Content-Type': 'application/json' } },
  )
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`bulk delete failed: ${response.status} ${detail}`)
  }
  return response.json()
}
```

### 4. MODIFY Pinia store

**MODIFY** (`apps/dashboard/src/stores/useIllustrationStore.js`):

```javascript
// Phase 107: bulk delete (1 method)
async bulkDeleteAssets(slug, assetIds) {
  if (!Array.isArray(assetIds) || assetIds.length === 0) {
    throw new Error('assetIds must be non-empty array')
  }
  const result = await apiBulkDeleteAssets(slug, assetIds)
  // Local state: remove successfully deleted assets + failed `not_found` (treated as gone)
  const removedIds = new Set([
    ...result.deleted,
    ...result.failed.filter(f => f.status === 'not_found').map(f => f.id),
  ])
  this.assets = this.assets.filter(a => !removedIds.has(a.id))
  return result
}
```

> Note: failed assets with `store_error` / `load_error` status remain in `assets[]` because they may be retried. `not_found` removes locally because the asset is genuinely gone.

### 5. NEW composable

**NEW** (`apps/dashboard/src/composables/useBulkDeleteToast.ts`):

```typescript
import { useMessage } from 'naive-ui'

export function useBulkDeleteToast() {
  const message = useMessage()

  function showBulkDeleteResult(slug: string, result: BulkDeleteResult): void {
    const { ok, fail } = result.summary
    if (fail === 0) {
      message.success(`已删除 ${ok} 张插图`)
    } else if (ok === 0) {
      message.error(`0 个成功，${fail} 个失败 — 查看详情`)
    } else {
      message.warning(`已删除 ${ok} 张，失败 ${fail} 张 — 查看详情`)
    }
  }

  function showValidationError(detail: string): void {
    message.error(`批量删除失败：${detail}`)
  }

  return { showBulkDeleteResult, showValidationError }
}
```

> Phase 107 does NOT extract the failure-list `<NDrawer>` into the composable — the drawer requires per-asset interaction (selective retry) which is specific to the page that owns the gallery state. Each page can mount its own drawer driven by the `failed[]` array it received. This keeps the composable narrow (toast only).

### 6. MODIFY IllustrationGallery.vue

**MODIFY** (`apps/dashboard/src/components/illustrations/IllustrationGallery.vue`):

Add local state:
```typescript
const selection = ref<Set<string>>(new Set())
const bulkDeleteInFlight = ref(false)

const bulkActionBarVisible = computed(() => selection.value.size > 0)
const selectedCount = computed(() => selection.value.size)
```

Template additions:
```vue
<!-- Checkbox overlay per card (top-left) -->
<NCheckbox
  v-if="props.selectable !== false"
  :checked="selection.has(asset.id)"
  class="illustration-card__checkbox"
  :data-testid="`select-checkbox-${asset.id}`"
  @update:checked="(v: boolean) => toggleSelect(asset.id, v)"
/>

<!-- Sticky bottom bulk action bar -->
<div v-if="bulkActionBarVisible" class="bulk-action-bar">
  <span class="bulk-action-bar__count">已选 {{ selectedCount }} 张</span>
  <NButton @click="clearSelection">取消</NButton>
  <NPopconfirm
    positive-text="确认删除"
    negative-text="取消"
    @positive-click="confirmBulkDelete"
  >
    <template #trigger>
      <NButton type="error" :loading="bulkDeleteInFlight">
        🗑 批量删除
      </NButton>
    </template>
    确认删除这 {{ selectedCount }} 张插图？删除后无法恢复。
  </NPopconfirm>
</div>
```

Methods:
```typescript
function toggleSelect(assetId: string, checked: boolean): void {
  if (checked) selection.value.add(assetId)
  else selection.value.delete(assetId)
  // Trigger reactivity for Set
  selection.value = new Set(selection.value)
}

function clearSelection(): void {
  selection.value = new Set()
}

async function confirmBulkDelete(): Promise<void> {
  if (bulkDeleteInFlight.value) return
  const ids = Array.from(selection.value)
  if (ids.length === 0) return
  bulkDeleteInFlight.value = true
  try {
    const result = await store.bulkDeleteAssets(props.slug, ids)
    showBulkDeleteResult(props.slug, result)
    emit('bulk-deleted', result)
    clearSelection()
  } catch (e) {
    showValidationError((e as Error).message)
  } finally {
    bulkDeleteInFlight.value = false
  }
}
```

Props:
```typescript
interface Props {
  assets: IllustrationMeta[]
  slug: string
  selectable?: boolean  // default true; allows parent to disable (e.g., empty preview)
}
defineProps<Props>()
const emit = defineEmits<{
  'bulk-deleted': [result: BulkDeleteResult]
}>()
```

**No changes** to `LibraryPage.vue` or `WriteWorkspacePage.vue` — they already mount `<IllustrationGallery :assets="..." :slug="...">` and will receive `bulk-deleted` events automatically. They can optionally listen via `@bulk-deleted` to refetch via existing `GET /api/illustrations` if local cache freshness matters.

> Phase 107 keeps the `emit('bulk-deleted')` event for future use (e.g., page-level refetch + analytics), but the **store already updates its own `assets[]` reactively** so the gallery's list updates immediately without needing a parent refetch.

### 7. Invariant extensions via docstring only

**I090 EXTENDED** (`.lingwen/architecture.yml`):

```yaml
- id: I090
  rule: |
    lru_cleanup + audit_log.record_event are unique entrypoints.
    Callers: pipeline.generate_illustration | pipeline.regenerate_illustration |
             apps/studio_api/routes/cleanup_route.py |
             apps/studio_api/routes/illustrations.py:delete_asset |
             apps/studio_api/routes/illustrations.py:bulk_delete_assets.
    (Phase 98 + 105 + 106 + 107: 5 callers total; bulk added in this phase)
  scope: |
    All Phase 98 (LRU) + Phase 105 (cleanup_route) + Phase 106 (delete_asset) +
    Phase 107 (bulk_delete_assets) enforcement.
```

**I091 EXTENDED**:
```yaml
- id: I091
  rule: |
    notifications.py:publish is the sole fan-out entry for illustration events.
    Double-write callers (audit_log.record_event + publish with same ULID):
      pipeline.generate_illustration, pipeline.regenerate_illustration,
      apps/studio_api/routes/cleanup_route.py,
      apps/studio_api/routes/illustrations.py:delete_asset,
      apps/studio_api/routes/illustrations.py:bulk_delete_assets.
    (Phase 99 + 105 + 106 + 107: 5 double-write sites; bulk added per-asset)
```

**I095 EXTENDED via docstring** (5th extension):
```yaml
- id: I095
  rule: |
    _consecutive_failures state keyed per (project_slug, event_type) tuple
    maintained ONLY via record_failure/record_success helpers. notify_threshold
    per-event-type dict (Phase 104 int legacy expands). Phase 107 EXTENDED:
    bulk_delete_assets iterates _delete_asset_inner per asset — each asset's
    record_failure/record_success is independent; counter keys still
    (slug, "deletion"); threshold crossing per (slug, "deletion") emits
    exactly one severity="warning" notification.
```

## Test coverage matrix

| Path | Counter state | Test |
|------|---------------|------|
| Happy path 5 assets | 5× `record_success` + 5× `audit_log.record_event` + 5× `notifications.publish` (5 distinct ULIDs) | T1 |
| Partial: 3 succeed, 2 store_error | 3× `record_success` + 2× `record_failure(project_root=root)`. Response: deleted=[3 ids], failed=[{id, store_error}, ...] | T2 |
| Empty ids query | `422` immediately (no iteration) | T3 |
| >50 ids after dedupe | `422` immediately | T4 |
| Slug not found (404 from `_project_root_for`) | `404` no iteration | T5 |
| LoadError on `project_root_for` then iterate | First asset gets `LoadError` → all assets in batch get `record_failure(project_root=None)`. Response: all in `failed[]`. URL/iteration still continues. | T6 |
| Dedupe: `"a,a,b,b,b,c,d,d"` (8 raw, 4 unique) | Only 4 actual deletes; response has 4 (mix of deleted/failed) | T7 |
| Cross-project implicit-not-found: slug=foo but query contains one aid belonging to slug=bar | bar's storage doesn't have that aid under foo's project_root → helper returns `not_found` (Phase 106 no-op success: record_success + failed.append); bar's project files unaffected | T8 |
| Audit log `extra={"trigger": "manual", "mode": "bulk"}` vs single mode | Mode distinct in audit_log entries | T9 |
| Threshold crossing: 5 consecutive `store_error` for deletion event (3 + 2 from T2) | Threshold=3 reached at 3rd failure; `record_success(1)/record_failure(4)` triggers exactly 1 severity=warning notification for (slug, deletion) | T10 |

## Regression guards G1-G10 in `tests/test_phase107_bulk_delete.py`

| # | Asserts | Catches |
|---|---------|---------|
| G1 | `bulk_delete_assets` route registered on `DELETE /api/illustrations` (slug + ids query params); returns `{deleted, failed, summary}` on 200 | Route registration missing |
| G2 | 51 ids after dedupe → `422` (limit boundary) | Limit regression / off-by-one |
| G3 | Empty `ids` or missing `ids` → `422` (validation) | Empty input crash |
| G4 | Happy path 5 ids → 5× `record_success` + 5× `audit_log.record_event` + 5× `notifications.publish` (5 distinct ULIDs, all `mode="bulk"`) | Per-asset fan-out missing |
| G5 | 2/5 `StoreError` storage failures → 2× `record_failure(project_root=root)` + 3× `record_success`; response 200 + 2 in `failed[]` + 3 in `deleted[]` (per-asset audit + publish on the 3 successes) | Per-asset error tracking missing |
| G6 | counter isolation (Phase 106 G5 复用): bulk deletion failures leave generation counter = 0 | Counter bleed between event_types |
| G7 | `delete_asset` (`/{asset_id}`) route still passes all Phase 106 T1-T6 + G1-G6 guards after helper refactor | Helper refactor broke single-delete |
| G8 | `.lingwen/architecture.yml` I090/I091 rule fields mention `bulk_delete_assets`; I095 EXTENDED mentions `bulk_delete_assets` | Invariant extension regression |
| G9 | Dedupe: `ids="a,a,b,b,b,c,d,d"` (8 raw, 4 unique) → only 4 iterations; response lists only 4 ids | Dedupe regression |
| G10 | Cross-project implicit-not-found: slug=foo but query contains one aid belonging to slug=bar → that aid lands in `failed[]` as `not_found`; bar's storage path is **unaffected** (verified by reading bar project_root listing pre/post) | Cross-project data leak |

## Out of scope

- **Bulk REGENERATE** (DELETE-then-PUT-N times in one bulk endpoint) — YAGNI; users currently re-issue generate request 1-at-a-time, which is fast enough
- **Bulk delete with chapter filter** (e.g., "delete all stickers in chapter 5") — Phase 108+; would need new query param + storage.list_assets filter pattern
- **Delete from NotificationsPage dropdown** — orthogonal UX, separate phase
- **Audit log batching/digest** (e.g., 1 bulk event with child refs) — YAGNI; per-asset events keep audit_log readable
- **Cancellable bulk request** (client disconnect → server stops) — FastAPI doesn't easily support mid-iteration cancellation; out of scope for v1
- **Concurrency-safe per-asset lock** (single-delete + bulk-delete on same aid) — Phase 106 already doesn't lock; storage layer's file-unlink is atomic; last-writer-wins is acceptable; out of scope

## Validation gates

- `pytest apps/studio_api/tests/test_bulk_delete_api.py` → 10 NEW tests (T1-T10) GREEN
- `pytest tests/test_phase107_bulk_delete.py` → 10 NEW G1-G10 guards GREEN
- `pytest apps/studio_api/tests/test_illustrations_api.py` Phase 106 T1-T6 + G1-G6 → 12/12 preserved GREEN (helper refactor preserves behavior)
- `pytest tests/test_phase102/103/104/105/106_*.py` → 30+ guards preserved GREEN (cumulative)
- `vitest IllustrationGallery.spec.ts` → existing + 6 NEW (selection set / checkbox / bulk bar / NPopconfirm / cross-page / dedupe UI) GREEN
- `vitest useIllustrationStore.spec.ts` → existing + 2 NEW (bulkDeleteAssets happy + partial) GREEN
- `pnpm tsc --noEmit` → 0 new errors (48 pre-existing baseline unchanged)
- `pnpm eslint .` → 0 new errors
- `ruff check` on introduced/changed Python files → clean

## Atomic commits (~13)

```
# docs
1. docs(phase-107): design spec                                       — yyyy-MM-DD-phase-107-bulk-delete-design.md
2. docs(phase-107): implementation plan                                — yyyy-MM-DD-phase-107-bulk-delete.md

# backend RED → refactor → GREEN
3. test(phase-107): test_bulk_delete_api.py 10 RED                     — T1-T10 covering happy/partial/422/422/404/LoadError/dedupe/cross-project/audit+publish/threshold
4. refactor(phase-107): extract _delete_asset_inner helper             — Phase 106 GREEN preserved verification
5. feat(phase-107): bulk_delete_assets endpoint                        — 422/404/200 path + for-loop + helper call

# frontend RED → GREEN
6. test(phase-107): IllustrationGallery.spec.ts +6 RED                 — selection state / checkbox / bulk bar / NPopconfirm / cross-page / dedupe UI
7. feat(phase-107): api/illustrations.ts bulkDeleteAssets typed wrapper
8. feat(phase-107): useIllustrationStore.bulkDeleteAssets action       — local assets filter on success
9. feat(phase-107): useBulkDeleteToast composable                      — toast variants (success / partial / error)
10. feat(phase-107): IllustrationGallery.vue multi-select + bulk action bar + NPopconfirm

# invariants + guards
11. test(phase-107): tests/test_phase107_bulk_delete.py 10 G1-G10
12. docs(phase-107): extend I090/I091/I095 in architecture.yml + CLAUDE.md  (5th EXTENDED)

# docs sync
13. docs(phase-107): CLAUDE.md v60.4 → v60.5 + handoff + BACKLOG + CURRENT_STATUS + MEMORY
```

## §A. Test files migration plan (I079)

Per I079 invariant, all P3-ARCHDEBT specs must include §A. **Phase 107 is NOT a P3-ARCHDEBT phase** (no `infra/*` migration, no test files in `tests/infra/` to migrate). New tests are added to canonical locations:

| Test file | Location | Notes |
|-----------|----------|-------|
| T1-T10 (bulk delete API tests) | `apps/studio_api/tests/test_bulk_delete_api.py` (NEW) | Mirrors `test_illustrations_api.py` structure |
| F1-F6 (UI selection + bulk action bar) | `apps/dashboard/tests/unit/components/illustrations/IllustrationGallery.spec.ts` (extend existing) | Existing spec has Phase 96+ tests for single-delete; append multi-select |
| G1-G10 (regression guards) | `tests/test_phase107_bulk_delete.py` (NEW) | Mirrors Phase 105/106 guards location |

No `tests/infra/` migrations needed. No file deletions needed. New files in canonical package test directories.

## Risk assessment

| Risk | Mitigation |
|------|-----------|
| Helper refactor breaks Phase 106 single-delete behavior | T1-T6 of Phase 106 still pass + Phase 106 G1-G6 still pass → G7 re-verifies explicitly |
| URL length limit on >50 ids | Cap enforced server-side (422) BEFORE iteration; client-side cap also recommended (50 is conservative proxy ceiling) |
| Counter leak during for-loop iterations | Each iteration is its own `_delete_asset_inner` call which manages `(slug, "deletion")` counter via record_failure/record_success — counter correctly maintained regardless of loop context |
| audit_log.jsonl grows linearly with batch size | Phase 102 already documents in-memory SSE + JSONL append-only durability trade-off; bulk doesn't change this — adds N rows instead of 1. YAGNI to compress |
| Selection state cross-page pollution | `selection` is component-local (`ref<Set<string>>`); if IllustrationGallery remounts on page change, selection resets. Phase 107 does NOT persist selection across pagination |
| Same asset in id list duplicated | `dict.fromkeys(raw_ids)` dedupes silently (idempotent delete) |
| Cross-project ID attempt via same query | Storage layer's per-project directory isolation makes asset_id lookup fail naturally → `_delete_asset_inner` returns `not_found` (Phase 106 5-path handles); no data leak |
| Single-delete + bulk-delete race on same aid | No per-asset lock; both fire concurrently. Storage delete is file-unlink (atomic). Both record_success happens → counter resets cleanly. Audit may double-log "deleted" → acceptable (append-only is intentional) |
| `extra={"mode": "bulk"}` not propagating to consumers | Phase 99 NotificationCenter card UI doesn't display `mode`; it does display `asset_id` + `event_type`; analytics is the only consumer and Phase 107 doesn't ship analytics — YAGNI to verify UI |
| Toast composable Naive UI message instance not in setup | Phase 99 `useNotificationStream.spec.ts` confirms message is provided via app context; `useMessage()` works inside script-setup of any component that mounts under `<n-message-provider>` (which App.vue provides) |

## Lessons referenced

- **Phase 102 §3**: threshold + counter state machine — Phase 107 inherits unchanged
- **Phase 104 §3**: per-event-type counter isolation — verified via G6
- **Phase 105 §1**: `_load_cleanup_settings` helper pattern — Phase 107 mirrors `_load_deletion_settings` (Phase 106 already did)
- **Phase 105 §2**: failure tracking on LoadError + StoreError + record_success in else branch — `_delete_asset_inner` Phase 107 inherits verbatim
- **Phase 106 §1**: 404 no-op success pattern — Phase 107 inherits for `not_found` status
- **Phase 106 §4**: `extra={"trigger": "manual"}` — Phase 107 adds `mode="single"|"bulk"` discriminator
- **Phase 106 §6**: I090/I091/I095 EXTENDED via docstring preserves YAGNI — Phase 107 EXTENDS again (5th extension)
- **Phase 90 §11**: IllustrationCard existing delete button + emit pattern → IllustrationGallery.vue Phase 107 mirrors for multi-select
- **Phase 99 §NPopconfirm pattern**: Phase 106 used NPopconfirm for single-delete confirm; Phase 107 reuses for bulk-delete confirm
- **I079 §A**: spec self-review requires §A even when not P3-ARCHDEBT (defensive for test-files-migration-plan consistency)

## Future phases

- **Phase 108+**: telemetry-driven chain reorder — gated on Phase 102-107 cumulative failure tracker data accumulation
- **Phase 108+**: delete from NotificationsPage dropdown — orthogonal UX; per-item clear from notification history
- **Phase 108+**: bulk delete with chapter filter — `?slug=...&chapter=N` to delete all assets in chapter N
- **Phase 110+**: bulk REGENERATE (atomic per-asset via PUT /{id}/regenerate in sequence) — YAGNI evaluate after bulk-delete ships
- **ARCHDEBT-REAL continuation**: closed since Phase 88; only if new N.14 audit reveals candidates
