# Phase 94 — atomic regenerate via PUT design

> **Date**: 2026-09-16
> **Phase**: 94
> **Carryover source**: Phase 90 REQ-002 multimodal (deviation 4 of 5: "regenerate non-atomic (DELETE+POST)")
> **Spec status**: spec — informs implementation

## 1. Problem

`apps/dashboard/src/stores/useIllustrationStore.js:57-73` (v1):

```javascript
async function regenerate(slug, assetId) {
  const original = assets.value.find(a => a.id === assetId)
  // ...
  await deleteAsset(slug, assetId)   // ← DELETE first
  return await generate(slug, params) // ← then POST
}
```

This is **two HTTP calls** with a destructive window between them:
- T0: DELETE returns 200, asset removed from disk
- T1: Network blip / user closes tab / backend exception during POST
- T2: User's illustration is **permanently lost** — never to be recovered

**Why it exists**: The v1 backend has no atomic regenerate endpoint. Frontend worked
around it with DELETE+POST, documenting "v2: backend could add a PUT /{id}/regenerate
endpoint for atomic swap" in the store comment.

## 2. Goal

Provide single-call atomic regenerate via backend endpoint:

1. Backend route `PUT /api/illustrations/{asset_id}/regenerate`
2. Re-runs pipeline stages 1-4 (load → extract → compose → generate)
3. Atomically swaps image bytes + sidecar in place (preserve asset_id)
4. Returns same id with new scene_json + final_prompt + created_at
5. Frontend switches to PUT (replaces DELETE+POST)

Atomicity: temp file + POSIX rename on the .jpg. Concurrent readers see either old bytes
or new bytes — never a partial mix. Sidecar is small (JSON); direct overwrite acceptable.

## 3. Design choices

### 3.1 New helpers

**`lingwen_illustrations.storage.replace_asset`** (~50 LOC):

```python
def replace_asset(project_root, image_bytes, meta) -> Path:
    """Atomically replace image bytes + sidecar in place."""
    jpg_path = asset_path(project_root, type=meta.type, id=meta.id, chapter_num=meta.chapter_num)
    if not jpg_path.exists():
        # No existing asset — bootstrap via save_asset.
        return save_asset(project_root, image_bytes, meta)

    # Write to sibling temp file (same filesystem = atomic rename).
    tmp_path = jpg_path.with_suffix(jpg_path.suffix + ".tmp")
    tmp_path.write_bytes(image_bytes)
    try:
        tmp_path.replace(jpg_path)  # POSIX atomic
    except OSError as e:
        tmp_path.unlink(missing_ok=True)
        raise StoreError(f"rename failed: {e}") from e

    # Sidecar rewrite (small, acceptable to overwrite directly).
    sidecar = jpg_path.with_suffix(jpg_path.suffix + ".meta.json")
    sidecar.write_text(meta.to_json(), encoding="utf-8")
    return jpg_path
```

Key invariants:
- On rename failure, temp file is cleaned up; original asset preserved.
- Concurrent readers see either old or new — never a partial mix (POSIX atomicity).
- Falls back to save_asset when no existing target (idempotent bootstrap).

**`lingwen_illustrations.pipeline.regenerate_illustration`** (~75 LOC):

```python
async def regenerate_illustration(
    *,
    project_root: Path,
    existing_meta: IllustrationMetadata,
    api_key: str,
    api_host: str,
) -> IllustrationMetadata:
    """Re-run stages 1-4 for an existing asset. Preserves asset_id."""
    type = existing_meta.type
    chapter_num = existing_meta.chapter_num
    style_preset = existing_meta.style_preset
    custom_prompt = existing_meta.custom_prompt

    chapter_text = _load_chapter_text(project_root, type, chapter_num)
    character_bible = load_character_bible(project_root)

    scene_json = extract_scene(chapter_text=chapter_text, character_bible=character_bible)
    final_prompt = compose_prompt(style_preset, scene_json=scene_json, custom_prompt=custom_prompt)
    image_bytes = await image_generator.generate(prompt=final_prompt, api_key=api_key, api_host=api_host)

    prompt_hash = f"sha256:{hashlib.sha256(final_prompt.encode('utf-8')).hexdigest()[:16]}"
    new_meta = IllustrationMetadata(
        id=existing_meta.id,  # preserve identity
        type=existing_meta.type,
        project_slug=existing_meta.project_slug,
        chapter_num=existing_meta.chapter_num,
        style_preset=style_preset,
        custom_prompt=custom_prompt,
        scene_json=scene_json,
        final_prompt=final_prompt,
        prompt_hash=prompt_hash,
        model="minimax-multimodal",
        created_at=_iso_utc_now(),  # refresh timestamp
    )

    storage.replace_asset(project_root, image_bytes, new_meta)
    return new_meta
```

Difference from `generate_illustration`: reuses existing asset_id + style_preset +
custom_prompt; refreshes scene_json + final_prompt + prompt_hash + created_at.

### 3.2 New endpoint

`apps/studio_api/routes/illustrations.py` — append after DELETE handler:

```python
@app.put("/api/illustrations/{asset_id}/regenerate", response_model=GenerateResponse)
async def regenerate_illustration(
    asset_id: str,
    project_slug: str = Query(...),
) -> GenerateResponse:
    try:
        project_root = _project_root_for(project_slug)
    except LoadError as e:
        raise HTTPException(404, detail=_err_detail(e)) from e

    all_assets = storage.list_assets(project_root)
    meta = next((a for a in all_assets if a.id == asset_id), None)
    if meta is None:
        raise HTTPException(404, detail=f"asset {asset_id} not found")

    api_key, api_host = _api_credentials()
    from lingwen_illustrations.pipeline import regenerate_illustration as run_regen

    try:
        new_meta = await run_regen(
            project_root=project_root,
            existing_meta=meta,
            api_key=api_key,
            api_host=api_host,
        )
    except IllustrationError as e:
        _raise_stage_error(e)

    return GenerateResponse(
        id=new_meta.id,
        type=new_meta.type,
        chapter_num=new_meta.chapter_num,
        style_preset=new_meta.style_preset,
        scene_json=new_meta.scene_json,
        url=f"/api/illustrations/{new_meta.id}/image?project_slug={project_slug}",
    )
```

Error mapping (same as POST generate):
- LoadError → 404
- ExtractError → 502
- ComposeError → 400
- GenerateError → 502 (rate-limit headers preserved)
- StoreError → 500

Non-destructive: any stage failure raises HTTP error and leaves the original asset intact.

### 3.3 Frontend update

`apps/dashboard/src/stores/useIllustrationStore.js` — replace regenerate body:

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
      assets.value = [
        ...assets.value.slice(0, idx),
        res,
        ...assets.value.slice(idx + 1),
      ]
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
- Single PUT instead of DELETE+POST.
- Replaces in-place (same id) — no longer needs to look up original metadata client-side
  (backend derives params from existing_meta).
- Manages loading + error state (was missing in v1 — caller couldn't tell if it was running).

## 4. Backward-compat

- `POST /generate` + `DELETE /{id}` unchanged — frontends that still call them work.
- `assets.value.find(a => a.id === assetId)` no longer needed in caller — but the new
  regenerate() doesn't fail if asset isn't in cache (prepends defensively).
- `IllustrationMetadata` signature unchanged.

## 5. Test strategy

### 5.1 storage tests (`test_storage.py`)

5 new tests:
1. `test_replace_asset_preserves_id_and_swaps_bytes` — happy path; bytes changed, id preserved.
2. `test_replace_asset_no_temp_leftover_on_success` — no `.tmp` siblings after success.
3. `test_replace_asset_falls_back_to_save_when_missing` — bootstrap path (no existing target).
4. `test_replace_asset_invalidates_listing_via_created_at` — list_assets reflects new metadata.
5. `test_replace_asset_preserves_existing_on_failure` — simulated rename failure: original preserved.

### 5.2 Endpoint tests (`test_illustrations_api.py`)

4 new tests:
1. `test_put_regenerate_preserves_asset_id` — happy path; id unchanged, content changed.
2. `test_put_regenerate_404_when_asset_not_found` — no destructive create.
3. `test_put_regenerate_extract_error_preserves_original` — stage failure → original bytes intact.
4. `test_put_regenerate_load_error_for_missing_chapter_returns_404` — chapter gone → 404, original preserved.

### 5.3 Regression guards (`test_phase90_illustrations.py`)

G12 — four-fold defense:
- **G12a** PUT endpoint registered (regex scan of route file).
- **G12b** `storage.replace_asset` exists with correct signature.
- **G12c** `pipeline.regenerate_illustration` exists with correct signature.
- **G12d** frontend `regenerate()` calls PUT (not DELETE+POST).

G12d uses regex on the function body to catch v1 pattern re-regression.

## 6. Files touched (4 production + 2 test + 3 docs)

```
packages/lingwen-illustrations/src/lingwen_illustrations/storage.py
packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py
apps/studio_api/routes/illustrations.py
apps/dashboard/src/stores/useIllustrationStore.js
packages/lingwen-illustrations/tests/test_storage.py
apps/studio_api/tests/test_illustrations_api.py
tests/test_phase90_illustrations.py
collaboration/BACKLOG.md
collaboration/CURRENT_STATUS.md
CLAUDE.md
docs/superpowers/handoffs/2026-09-16-phase-94-regenerate-atomic-handoff.md
docs/superpowers/specs/2026-09-16-phase-94-regenerate-atomic-design.md  # this file
docs/superpowers/plans/2026-09-16-phase-94-regenerate-atomic.md
```

## 7. Validation matrix

| Gate | Expected |
|------|----------|
| `pytest packages/lingwen-illustrations/tests/test_storage.py` | 16/16 (was 11, +5) |
| `pytest packages/lingwen-illustrations/tests/` | 83/83 (was 78, +5) |
| `pytest apps/studio_api/tests/test_illustrations_api.py` | 12/12 (was 8, +4) |
| `pytest apps/studio_api/tests/` | 94/94 (was 90, +4) |
| `pytest tests/test_phase90_illustrations.py` | **26/26** (was 22, +G12 a/b/c/d) |
| `pnpm vitest run tests/unit/components/illustrations` | 17/17 unchanged |
| `pnpm tsc --noEmit` | 0 new errors (pre-existing FactionGraphCanvas.spec.ts errors untouched) |
| `ruff check <changed files>` | clean on introduced (pre-existing E741 in test_phase90:102 untouched) |

## 8. Non-goals

- Not adding image provider adapters (separate REQ-002 v2 sub-project).
- Not adding LRU archive (separate sub-project).
- Not changing regenerate UX (no confirmation dialog — backend is now atomic so destructive confirm is unnecessary).
- Not adding rate limiting (separate backend infra phase).
- Not changing the POST /generate or DELETE /{id} endpoints (still public API).

## 9. Risks and mitigations

| Risk | Mitigation |
|------|------------|
| `Path.replace()` is not atomic on Windows | Documented limitation; POSIX rename(2) is atomic when source/target on same FS. Windows MoveFileEx replaces require `MOVEFILE_REPLACE_EXISTING` flag — Python's `Path.replace()` uses it on Windows since 3.3. Cross-FS rename not atomic (rare) — out of scope for dev. |
| Temp file leftover on crash mid-rename | Test verifies no `.tmp` siblings after success; on failure, `tmp_path.unlink(missing_ok=True)` cleans up. Crash mid-write leaves a `.tmp` — recoverable manually but not auto-recovered (acceptable; rare). |
| Frontend cache desync after regenerate | New frontend code uses `findIndex + splice` to update in-place. If backend returns 404 (asset gone), frontend cache becomes stale — defensive: prepend to list (treats as new asset). Acceptable: PUT only fails if asset was deleted between two client calls (rare). |
| Old `generateIllustration` flow could be invoked from another place | `grep` shows only `useIllustrationStore.js` calls regenerate — single call site. No other consumers to migrate. |
| Sidecar rewrite non-atomic (small file, but technically readable during write) | Acceptable: sidecars are small JSON (~1 KB). Worst case: reader sees truncated JSON → `list_assets` skips it (existing defensive code in `list_assets`). |
| `Path.replace` raises OSError when target is open by another process (Windows file lock) | On Windows, replace fails with PermissionError. Documented: retry / abort cleanly. Out of scope for dev. |