# Phase 94 — atomic regenerate via PUT plan

> **Date**: 2026-09-16
> **Phase**: 94
> **Spec**: `docs/superpowers/specs/2026-09-16-phase-94-regenerate-atomic-design.md`
> **Workflow**: 2026-09-15 simplified (solo, direct master commits)

## 1. Atomic commit sequence

5 atomic direct-master commits (combined where per-concern atomicity makes more sense than per-file):

| # | Subject | Files |
|---|---------|-------|
| 1 | `docs(phase-94): spec atomic regenerate via PUT` | spec only |
| 2 | `docs(phase-94): plan atomic regenerate via PUT` | plan only |
| 3 | `feat(phase-94): storage.replace_asset + pipeline.regenerate_illustration + PUT endpoint + storage tests + endpoint tests` | 4 production + 2 test files |
| 4 | `test(phase-94): G12 a/b/c/d regression guards` | test_phase90 only |
| 5 | `feat(phase-94): frontend regenerate() uses PUT (atomic)` | useIllustrationStore.js |
| 6 | `docs(phase-94): close carryover + handoff + CLAUDE.md v55.4 + CURRENT_STATUS` | 3 doc files + handoff |

(Slightly more than typical 5-commit because backend + frontend changes are split for blame clarity.)

## 2. Per-step code changes

### Commit 1 (spec)

Create `docs/superpowers/specs/2026-09-16-phase-94-regenerate-atomic-design.md`.

### Commit 2 (plan)

Create `docs/superpowers/plans/2026-09-16-phase-94-regenerate-atomic.md` (this file).

### Commit 3 (feat: backend)

`packages/lingwen-illustrations/src/lingwen_illustrations/storage.py`:

```diff
+def replace_asset(project_root, image_bytes, meta) -> Path:
+    """Atomically replace image bytes + sidecar in place. ..."""
+    jpg_path = asset_path(...)
+    if not jpg_path.exists():
+        return save_asset(project_root, image_bytes, meta)
+    tmp_path = jpg_path.with_suffix(jpg_path.suffix + ".tmp")
+    tmp_path.write_bytes(image_bytes)
+    try:
+        tmp_path.replace(jpg_path)
+    except OSError as e:
+        tmp_path.unlink(missing_ok=True)
+        raise StoreError(f"rename failed: {e}") from e
+    sidecar = jpg_path.with_suffix(jpg_path.suffix + ".meta.json")
+    sidecar.write_text(meta.to_json(), encoding="utf-8")
+    return jpg_path

 __all__ = ["asset_path", "save_asset", "delete_asset", "replace_asset", "list_assets"]
```

`packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py`:

```diff
+async def regenerate_illustration(*, project_root, existing_meta, api_key, api_host):
+    """Re-run stages 1-4 + atomic swap. Preserves asset_id."""
+    # ... reuses type / chapter_num / style_preset / custom_prompt from existing_meta
+    # ... runs extract + compose + generate
+    # ... builds new_meta with same id + refreshed scene_json + final_prompt + created_at
+    storage.replace_asset(project_root, image_bytes, new_meta)
+    return new_meta

-__all__ = ["generate_illustration"]
+__all__ = ["generate_illustration", "regenerate_illustration"]
```

`apps/studio_api/routes/illustrations.py`:

```diff
+    @app.put("/api/illustrations/{asset_id}/regenerate", response_model=GenerateResponse)
+    async def regenerate_illustration(
+        asset_id: str,
+        project_slug: str = Query(...),
+    ) -> GenerateResponse:
+        # ... find meta, run regenerate_illustration, return GenerateResponse
```

`packages/lingwen-illustrations/tests/test_storage.py` — add 5 tests (see spec §5.1).

`apps/studio_api/tests/test_illustrations_api.py` — add 4 tests (see spec §5.2).

After edits, `ruff check --fix` for import order.

### Commit 4 (test: guards)

`tests/test_phase90_illustrations.py` — append G12 a/b/c/d (4 guards).

### Commit 5 (feat: frontend)

`apps/dashboard/src/stores/useIllustrationStore.js`:

```diff
-  // NOTE: regenerate is intentionally non-atomic (DELETE then POST).
-  async function regenerate(slug, assetId) {
-    const original = assets.value.find(a => a.id === assetId)
-    if (!original) throw new Error(`asset ${assetId} not found`)
-    const params = {
-      type: original.type,
-      chapter_num: original.chapter_num,
-      style_preset: original.style_preset,
-      custom_prompt: original.custom_prompt,
-    }
-    await deleteAsset(slug, assetId)
-    return await generate(slug, params)
-  }
+  // v55.4 Phase 94 — atomic regenerate via PUT /{id}/regenerate.
+  async function regenerate(slug, assetId) {
+    loading.value = true
+    error.value = null
+    try {
+      const res = await $fetch(
+        `/api/illustrations/${assetId}/regenerate?project_slug=${slug}`,
+        { method: 'PUT' }
+      )
+      const idx = assets.value.findIndex(a => a.id === assetId)
+      if (idx >= 0) {
+        assets.value = [...assets.value.slice(0, idx), res, ...assets.value.slice(idx + 1)]
+      } else {
+        assets.value = [res, ...assets.value]
+      }
+      return res
+    } catch (e) {
+      error.value = e.data?.detail?.error || e.message || 'regenerate failed'
+      throw e
+    } finally {
+      loading.value = false
+    }
+  }
```

### Commit 6 (docs)

- `collaboration/BACKLOG.md` — strike "regenerate non-atomic" + add recent change entry
- `collaboration/CURRENT_STATUS.md` — append Phase 94 row
- `CLAUDE.md` — bump version line v55.3 → v55.4
- `docs/superpowers/handoffs/2026-09-16-phase-94-regenerate-atomic-handoff.md` — write

## 3. Validation gates

Run in this order (per Phase 89 lesson — separate rootdir per package):

```bash
# Backend (4 separate rootdirs)
.venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_storage.py -v
.venv/bin/python -m pytest apps/studio_api/tests/test_illustrations_api.py -v
.venv/bin/python -m pytest tests/test_phase90_illustrations.py -v
.venv/bin/python -m pytest apps/studio_api/tests/ -v

# Frontend
cd apps/dashboard
pnpm exec vitest run tests/unit/components/illustrations
pnpm exec vitest run tests/unit/stores
pnpm tsc --noEmit
cd /home/ailearn/projects/LingWen

# Lint
.venv/bin/python -m ruff check \
  packages/lingwen-illustrations/src/lingwen_illustrations/storage.py \
  packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py \
  apps/studio_api/routes/illustrations.py \
  apps/studio_api/tests/test_illustrations_api.py \
  packages/lingwen-illustrations/tests/test_storage.py \
  tests/test_phase90_illustrations.py
```

Acceptance: all GREEN; ruff clean on introduced (1 pre-existing E741 in test_phase90:102 untouched).

## 4. Risk mitigation

- **Risk**: frontend cache desync after regenerate.
  - **Mitigation**: `findIndex + splice` updates in-place; if asset not in cache, prepends (defensive).
- **Risk**: temp file leftover on crash.
  - **Mitigation**: `tmp_path.unlink(missing_ok=True)` on rename failure; tests verify no `.tmp` siblings after success.
- **Risk**: old frontend DELETE+POST pattern restored by mistake.
  - **Mitigation**: G12d regex-check on function body asserts no `deleteAsset(slug` call + requires `method: 'PUT'`.
- **Risk**: `Path.replace` atomicity differs by platform.
  - **Mitigation**: documented limitation in spec; out of scope for dev. Python 3.3+ uses `MoveFileEx` with `MOVEFILE_REPLACE_EXISTING` on Windows.
- **Risk**: sidecar rewrite not atomic.
  - **Mitigation**: existing `list_assets` skips corrupt sidecars (defensive); readers see old or new, never partial JSON.

## 5. Rollback plan

Single revert: `git revert <commit-3-hash>..<commit-5-hash>`. Backend endpoint becomes 404
(but DELETE+POST in frontend would still work — old `regenerate` function code in commit
history). Reapply the v1 frontend by checking out the pre-commit-5 file.

No data loss: no schema changes, no migrations. Storage just gains a new function
(`replace_asset`) that's safe to keep even after rollback (no other callers yet).

## 6. Time estimate

| Step | Est. |
|------|------|
| spec + plan docs | 10 min |
| storage.replace_asset (50 LOC) | 10 min |
| pipeline.regenerate_illustration (75 LOC) | 15 min |
| PUT endpoint + docstring (50 LOC) | 10 min |
| storage tests (5 new) | 15 min |
| endpoint tests (4 new) | 15 min |
| G12 a/b/c/d guards | 10 min |
| frontend regenerate() | 10 min |
| pytest + vitest + ruff + tsc | 10 min |
| docs sync + handoff | 15 min |
| 6 atomic commits + push | 5 min |
| **Total** | **~115 min** |

User-estimated "~45 min" was optimistic — the spec/plan overhead + multi-package test
runs + frontend commit split push it past 90 min. Still well under 2 hours.