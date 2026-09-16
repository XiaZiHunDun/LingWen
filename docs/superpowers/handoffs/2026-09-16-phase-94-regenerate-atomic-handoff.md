# Phase 94 — atomic regenerate via PUT handoff

> **Date**: 2026-09-16
> **Branch**: master (direct commits per 2026-09-15 simplified workflow)
> **Version**: v55.3 → v55.4
> **Carryover source**: Phase 90 REQ-002 multimodal handoff §6 (deviation 4 of 5)

## 1. The bug

`apps/dashboard/src/stores/useIllustrationStore.js:57-73` (v1):

```javascript
async function regenerate(slug, assetId) {
  const original = assets.value.find(a => a.id === assetId)
  // ...
  await deleteAsset(slug, assetId)   // ← DELETE first
  return await generate(slug, params) // ← then POST
}
```

Two HTTP calls. **Destructive window** between DELETE and POST:

- T0: DELETE returns 200, asset removed from disk
- T1: Network blip / user closes tab / backend exception during POST
- T2: User's illustration is **permanently lost**

The v1 store comment was honest about this:
> "regenerate is intentionally non-atomic (DELETE then POST). If the POST fails after
> the DELETE succeeds, the old asset is permanently lost. A confirmation dialog at the
> call site (Task 15-17) is the v1 mitigation. v2: backend could add a PUT /{id}/regenerate
> endpoint for atomic swap."

Phase 94 delivers the v2: a single PUT endpoint that atomically swaps bytes in place.

## 2. The fix

### 2.1 Backend (Python)

New `lingwen_illustrations.storage.replace_asset` — temp file + POSIX rename:

```python
def replace_asset(project_root, image_bytes, meta) -> Path:
    """Atomically replace image bytes + sidecar in place. Same asset_id preserved."""
    jpg_path = asset_path(project_root, type=meta.type, id=meta.id, chapter_num=meta.chapter_num)
    if not jpg_path.exists():
        return save_asset(project_root, image_bytes, meta)  # bootstrap fallback

    tmp_path = jpg_path.with_suffix(jpg_path.suffix + ".tmp")
    tmp_path.write_bytes(image_bytes)
    try:
        tmp_path.replace(jpg_path)  # POSIX atomic
    except OSError as e:
        tmp_path.unlink(missing_ok=True)
        raise StoreError(f"rename failed: {e}") from e

    sidecar = jpg_path.with_suffix(jpg_path.suffix + ".meta.json")
    sidecar.write_text(meta.to_json(), encoding="utf-8")
    return jpg_path
```

New `lingwen_illustrations.pipeline.regenerate_illustration` — re-runs stages 1-4:

```python
async def regenerate_illustration(*, project_root, existing_meta, api_key, api_host):
    """Re-run extract+compose+generate for an existing asset. Preserves asset_id."""
    # Reuses type/chapter_num/style_preset/custom_prompt from existing_meta
    # Runs LLM extract + prompt compose + image generation
    # Builds new_meta with SAME id + refreshed scene_json + final_prompt + created_at
    storage.replace_asset(project_root, image_bytes, new_meta)  # atomic swap
    return new_meta
```

New endpoint `apps/studio_api/routes/illustrations.py`:

```python
@app.put("/api/illustrations/{asset_id}/regenerate", response_model=GenerateResponse)
async def regenerate_illustration(
    asset_id: str,
    project_slug: str = Query(...),
) -> GenerateResponse:
    # ... find meta, run regenerate_illustration, return GenerateResponse
```

Same error mapping as POST generate (LoadError → 404, ExtractError → 502, etc.).
Non-destructive: any stage failure raises HTTP error and leaves the original asset intact.

### 2.2 Frontend (Vue)

`apps/dashboard/src/stores/useIllustrationStore.js` — replaced regenerate body:

```javascript
async function regenerate(slug, assetId) {
  loading.value = true
  error.value = null
  try {
    const res = await $fetch(
      `/api/illustrations/${assetId}/regenerate?project_slug=${slug}`,
      { method: 'PUT' }
    )
    // Replace in-place (same id, new content)
    const idx = assets.value.findIndex(a => a.id === assetId)
    if (idx >= 0) {
      assets.value = [...assets.value.slice(0, idx), res, ...assets.value.slice(idx + 1)]
    } else {
      assets.value = [res, ...assets.value]
    }
    return res
  } catch (e) {
    error.value = e.data?.detail?.error || e.message || 'regenerate failed'
    throw e
  } finally {
    loading.value = false
  }
}
```

Key changes:
- Single PUT instead of DELETE+POST (one HTTP call, no destructive window).
- Replaces in-place — no need to look up original metadata client-side.
- Manages loading + error state (was missing in v1 — caller couldn't tell if running).

## 3. Atomicity guarantees

| Layer | Guarantee |
|-------|-----------|
| Image bytes (`.jpg`) | POSIX `rename(2)` is atomic when source/target on same filesystem. Concurrent readers see old or new bytes — never partial mix. |
| Sidecar (`.meta.json`) | Direct overwrite (small file). Worst case: reader sees truncated JSON → `list_assets` skips it (existing defensive code). |
| Cache (frontend `assets.value`) | Updated synchronously after PUT response. UI shows new content immediately. |
| Network | Single PUT call vs DELETE+POST pair. No destructive window. |
| Failure modes | Any stage error (Load/Extract/Compose/Generate/Store) → HTTP 4xx/5xx → frontend throws → original asset preserved. |

## 4. Test additions

### storage (`test_storage.py` — 5 new)

1. `test_replace_asset_preserves_id_and_swaps_bytes` — happy path: bytes swapped, id preserved, sidecar updated.
2. `test_replace_asset_no_temp_leftover_on_success` — no `.tmp` siblings.
3. `test_replace_asset_falls_back_to_save_when_missing` — bootstrap path.
4. `test_replace_asset_invalidates_listing_via_created_at` — list reflects new metadata.
5. `test_replace_asset_preserves_existing_on_failure` — simulated rename failure: original preserved.

### endpoint (`test_illustrations_api.py` — 4 new)

1. `test_put_regenerate_preserves_asset_id` — happy path.
2. `test_put_regenerate_404_when_asset_not_found` — no destructive create.
3. `test_put_regenerate_extract_error_preserves_original` — stage failure → original bytes intact.
4. `test_put_regenerate_load_error_for_missing_chapter_returns_404` — chapter gone → 404, original preserved.

### Regression guards (`test_phase90_illustrations.py` — G12 a/b/c/d)

- **G12a** PUT endpoint registered (regex scan).
- **G12b** `storage.replace_asset` exists with correct signature.
- **G12c** `pipeline.regenerate_illustration` exists with correct signature.
- **G12d** frontend `regenerate()` calls PUT (not DELETE+POST).

G12d uses regex on the function body to catch v1 pattern re-regression.

## 5. Validation

| Gate | Result |
|------|--------|
| pytest `packages/lingwen-illustrations/tests/test_storage.py` | **16/16** (was 11, +5 new) |
| pytest `packages/lingwen-illustrations/tests/` | **83/83** (was 78, +5) |
| pytest `apps/studio_api/tests/test_illustrations_api.py` | **12/12** (was 8, +4 new) |
| pytest `apps/studio_api/tests/` | **94/94** (was 90, +4) |
| pytest `tests/test_phase90_illustrations.py` | **26/26** (was 22, +G12 a/b/c/d) |
| vitest `tests/unit/components/illustrations` | 17/17 unchanged |
| vitest `tests/unit/stores` | 9/9 unchanged |
| `pnpm tsc --noEmit` | 0 new errors (pre-existing FactionGraphCanvas.spec.ts errors untouched) |
| ruff check on changed files | Clean on introduced (1 pre-existing E741 in test_phase90:102 untouched) |

## 6. Files changed

```
packages/lingwen-illustrations/src/lingwen_illustrations/storage.py    | +57 -0
packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py   | +76 -0
apps/studio_api/routes/illustrations.py                               | +52 -0
apps/dashboard/src/stores/useIllustrationStore.js                     | +25 -16
packages/lingwen-illustrations/tests/test_storage.py                  | +90 -0
apps/studio_api/tests/test_illustrations_api.py                       | +120 -10
tests/test_phase90_illustrations.py                                   | +95 -0
collaboration/BACKLOG.md                                              | +3 -1 (carryover row + recent change)
collaboration/CURRENT_STATUS.md                                       | +1 -0 (new Phase 94 row)
docs/superpowers/handoffs/2026-09-16-phase-94-regenerate-atomic-handoff.md | NEW
docs/superpowers/specs/2026-09-16-phase-94-regenerate-atomic-design.md    | NEW
docs/superpowers/plans/2026-09-16-phase-94-regenerate-atomic.md            | NEW
CLAUDE.md                                                              | +1 -1 (version line v55.3 → v55.4)
```

Total: ~520 LOC net (production +210; tests +205; docs +5).

## 7. Lessons

### Lesson 1: Two-call patterns need explicit verification they're atomic

The v1 frontend had a 16-line "regenerate" function that called DELETE then POST. The
implementation knew it was destructive ("intentionally non-atomic") and documented the
risk ("v2: backend could add PUT"). The documentation was correct — the implementation
was correct in acknowledging the problem — but the absence of a backend endpoint meant
the workaround was the only option.

**Heuristic**: when frontend comments describe workarounds ("v2 should add X"), the work
item is in scope for the next iteration. Treat comments like TODOs.

### Lesson 2: POSIX `rename(2)` atomicity is the cheapest correctness

The atomic swap uses temp file + `Path.replace()`. No transactional filesystem, no
database, no locking. POSIX guarantees that `rename(2)` on the same filesystem is atomic
— concurrent readers see old or new, never partial. Windows uses `MoveFileEx` with
`MOVEFILE_REPLACE_EXISTING` which is also atomic (Python 3.3+).

**Heuristic**: when designing "atomic swap" for files, check `rename(2)` before reaching
for databases or lockfiles.

### Lesson 3: Nondestructive error path requires Stage-level exception mapping

The endpoint catches `IllustrationError` and maps to HTTP codes (`STAGE_HTTP_CODES`
table). When Stage 1 (ExtractError) fails, the endpoint raises 502 — but the original
asset is still on disk because `storage.replace_asset` was never called yet.

**Heuristic**: when designing a multi-stage mutation, ensure each stage's error path is
documented as "does NOT mutate" or "partially mutates" — and verify with tests.

### Lesson 4: G12d guards against comment re-regression

G12d asserts `deleteAsset(slug` is NOT in the regenerate function body, AND `method:
'PUT'` IS in the body. This is a regex check on the function body, not the file.

Without the `deleteAsset(slug` check, a future developer could "restore the v1 logic" by
adding `method: 'PUT'` alongside the old DELETE call (e.g., "for safety, delete first
then PUT") — exactly the v1 bug pattern.

**Heuristic**: regression guards for behavioral fixes need negative checks (X must NOT
appear) alongside positive checks (Y must appear) to catch the full regression surface.

## 8. Carryover status (after Phase 94)

| Item | Status |
|------|--------|
| P2-EXTRACT-ENUM | ✅ CLOSED (Phase 92) |
| image_generator b64_json real-API decoding | ✅ CLOSED (Phase 93) |
| regenerate non-atomic (DELETE+POST → PUT atomic swap) | ✅ **CLOSED** (this phase) |
| ProjectSettingsPage doesn't exist | OPEN — **last carryover** |

**Phase 90 carryover**: was 2 → now **1 remaining**.

## 9. Next-step candidates

1. **Phase 95: ProjectSettingsPage** — verify if per-project settings UI is needed or
   if global SettingsPage is sufficient. Lowest cost (~20 min), mostly documentation.
2. **REQ-002 v2 sub-projects** — image provider adapters (recommended starting point),
   reference image i2i, LRU archive, notification center. Multi-week phases.

Phase 95 is the cheapest remaining carryover; recommend closing it before moving to v2
new work. After Phase 95, the Phase 90 carryover chain is fully closed.