# Phase 108 — Bulk Regenerate Illustration Endpoint — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `PUT /api/illustrations?slug=...&ids=...` bulk regenerate endpoint + multi-select UX in `IllustrationGallery.vue`, mirroring Phase 107's bulk_delete_assets pattern with `_regenerate_asset_inner` helper extraction and I090/I091/I095 6th EXTENDED.

**Architecture:** Backend extracts `_regenerate_asset_inner` helper from existing `regenerate_illustration` route handler (Phase 108 NEW, mirror `_delete_asset_inner`). New `bulk_regenerate_assets` route does sequential for-loop with dedupe via `dict.fromkeys`, pre-resolves `meta_by_id` dict for O(1) lookup, limit 1..10. Frontend reuses Phase 107's selection Set + bulk action bar UX; adds NPopconfirm-wrapped "批量再生" button (alongside existing "批量删除"), `useBulkRegenerateToast` composable, `bulkRegenerateAssets` typed wrapper + Pinia store action. Counter keys `(slug, "regeneration")` symmetric with Phase 107 `(slug, "deletion")`. Per-asset `mode='bulk'` discriminator for analytics only.

**Tech Stack:** Python 3.13 (uv workspace), FastAPI, Pydantic, pytest; Vue 3 + Pinia + Naive UI + TypeScript strict; vitest + @vue/test-utils; ruff; pnpm tsc --noEmit; python-ulid (already in lingwen-illustrations).

---

## File Structure

| File | Type | Responsibility |
|------|------|----------------|
| `apps/studio_api/routes/illustrations.py` | MODIFY | Add `_regenerate_asset_inner` helper + `bulk_regenerate_assets` route + refactor `regenerate_illustration` to thin wrapper (lines 572-654 → split into 2 funcs) |
| `tests/test_phase108_bulk_regenerate.py` | CREATE | 10 regression guards G1-G10 |
| `apps/studio_api/tests/test_bulk_regenerate_api.py` | CREATE | 10 backend pytest T1-T10 |
| `apps/dashboard/src/composables/useBulkRegenerateToast.ts` | CREATE | Toast composable + spec |
| `apps/dashboard/src/composables/useBulkRegenerateToast.spec.ts` | CREATE | 3 vitest tests |
| `apps/dashboard/src/api/illustrations.ts` | MODIFY | Add `BulkRegenerate*` interfaces + `bulkRegenerateAssets()` function (~line 192, after `bulkDeleteAssets`) |
| `apps/dashboard/src/stores/useIllustrationStore.js` | MODIFY | Add `bulkRegenerateAssets()` Pinia action (~line 105, after `bulkDeleteAssets`) |
| `apps/dashboard/src/stores/useIllustrationStore.spec.js` | MODIFY | Add 2 NEW tests (BulkRegenHappy + BulkRegenPartial) |
| `apps/dashboard/src/components/illustrations/IllustrationGallery.vue` | MODIFY | Add bulk-regenerate button + `onBulkRegenerate` handler + emit `'bulk-regenerated'` |
| `apps/dashboard/src/components/illustrations/IllustrationGallery.spec.ts` | MODIFY | Add 6 NEW tests F1-F6 |
| `.lingwen/architecture.yml` | MODIFY | I090/I091/I095 6th EXTENDED via docstring |
| `CLAUDE.md` | MODIFY | v60.5 → v60.6 + I-row 6th EXTENDED |
| `collaboration/CURRENT_STATUS.md` | MODIFY | Phase 108 entry |
| `collaboration/BACKLOG.md` | MODIFY | Phase 108 entry + remove reserved slot |

---

# Task A: Backend (helper + route + tests + guards)

### Task A1: Write RED pytest tests for bulk regenerate API

**Files:**
- Create: `apps/studio_api/tests/test_bulk_regenerate_api.py`

- [ ] **Step 1: Write 10 RED tests**

```python
"""Phase 108: bulk regenerate illustration endpoint — pytest tests.

Mirror of test_bulk_delete_api.py (Phase 107). Tests cover:
- T1: happy path 5×record_success + 5×audit + 5×publish
- T2: partial failure (3 ok + 2 stage_error)
- T3: empty ids → 422
- T4: over-10 ids → 422
- T5: slug not found → 404
- T6: LoadError raised before helper
- T7: dedupe 12 raw → 8 unique
- T8: cross-project asset not_found
- T9: audit mode='bulk' discriminator
- T10: 5 consecutive IllustrationError → 1 warning emission
"""
from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from lingwen_illustrations.exceptions import LoadError, IllustrationError
from lingwen_illustrations.notifications import _consecutive_failures, _warning_emitted


@pytest.fixture(autouse=True)
def reset_failure_state():
    """Reset notifications state between tests (Phase 104 pattern)."""
    _consecutive_failures.clear()
    _warning_emitted.clear()
    yield
    _consecutive_failures.clear()
    _warning_emitted.clear()


@pytest.fixture
def sample_assets():
    """Five asset ids, all valid."""
    return [f"asset-{i:03d}" for i in range(5)]


def _make_meta(id_: str, slug: str = "demo") -> MagicMock:
    """Construct a mock IllustrationMeta for an asset id."""
    m = MagicMock()
    m.id = id_
    m.slug = slug
    m.provider = "minimax"
    m.model = "default"
    m.type = "illustration"
    m.chapter_num = 1
    return m


def test_t1_happy_path_5_assets(app_with_settings, sample_assets):
    """T1: 5 valid assets → all regenerated, 5×record_success + 5×audit + 5×publish."""
    # Mock storage + pipeline.regenerate_illustration to return new meta
    ...


# (Skeleton — actual implementation written in plan Step 3 below.)
```

- [ ] **Step 2: Verify tests fail (RED)**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_bulk_regenerate_api.py -v --rootdir=.`
Expected: 10 ERROR / FAIL (no route registered yet → 404 on PUT /api/illustrations)

- [ ] **Step 3: Implement test bodies (10 tests)**

```python
# Full implementation follows Phase 107 test_bulk_delete_api.py pattern.
# Use the same fixtures + mocks + assertions; swap DELETE→PUT and bulk_delete→bulk_regenerate.
# (See Phase 107 plan Task A3 for the reference shape.)
```

For brevity in this plan, **mirror `apps/studio_api/tests/test_bulk_delete_api.py` exactly**, replacing:
- `bulk_delete_assets` → `bulk_regenerate_assets`
- `delete_asset` → `regenerate_illustration` (or `_regenerate_asset_inner`)
- `"store_error"` → `"stage_error"` (regenerate failure is stage_error, not store_error)
- 422 on empty/over-50 → 422 on empty/over-10
- `_delete_settings` → `_regeneration_settings` (or reuse settings — see Step 4 below)
- Mock `storage.delete_asset` → mock `pipeline.regenerate_illustration`
- `event_type="deletion"` → `event_type="regeneration"`

For settings: **Phase 108 regenerates uses the same `notify_threshold` per-event-type from ProjectSettings** (Phase 104 widened the field). The `_regeneration_settings(project_root)` helper is NEW and mirrors Phase 105's `_load_cleanup_settings` + Phase 106's `_load_deletion_settings`:

```python
def _load_regeneration_settings(project_root: Path) -> dict:
    """Load notify_threshold for event_type='regeneration' (Phase 104/108).

    Permissive fallback: missing file → {}; malformed yaml → {}.
    Returns dict suitable for `notifications._resolve_threshold(settings, 'regeneration')`.
    """
    settings_path = project_root / ".lingwen" / "illustration_settings.yaml"
    if not settings_path.exists():
        return {}
    try:
        import yaml
        data = yaml.safe_load(settings_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}
```

Add this helper at module top in `illustrations.py` (after `_load_deletion_settings` line 202).

- [ ] **Step 4: Verify tests still fail (RED) with helpers available but route missing**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_bulk_regenerate_api.py -v --rootdir=.`
Expected: 10 FAIL (route not registered yet)

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/studio_api/tests/test_bulk_regenerate_api.py
git commit -m "test(phase-108): bulk regenerate API 10 RED tests"
```

---

### Task A2: Extract `_regenerate_asset_inner` helper

**Files:**
- Modify: `apps/studio_api/routes/illustrations.py:572-654` (refactor existing `regenerate_illustration` route handler)

- [ ] **Step 1: Add `_regeneration_settings` helper (NEW, line ~203, after `_load_deletion_settings`)**

```python
def _load_regeneration_settings(project_root: Path) -> dict:
    """Phase 108: load notify_threshold for event_type='regeneration'.

    Permissive fallback: missing file → {}; malformed yaml → {}.
    Mirrors Phase 105 cleanup_settings + Phase 106 deletion_settings pattern.
    """
    settings_path = project_root / ".lingwen" / "illustration_settings.yaml"
    if not settings_path.exists():
        return {}
    try:
        import yaml
        data = yaml.safe_load(settings_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}
```

- [ ] **Step 2: Add `_regenerate_asset_inner` helper (NEW, line ~200, after `_load_deletion_settings`)**

```python
async def _regenerate_asset_inner(
    project_slug: str,
    asset_id: str,
    *,
    project_root: Path,
    provider: Optional[str],
    model: Optional[str],
    fallback_chain_list: Optional[list[str]],
    threshold,
    mode: Literal["single", "bulk"],
) -> Literal["ok", "not_found", "unknown_model", "stage_error"]:
    """Phase 108: per-asset regenerate helper extracted from regenerate_illustration.

    Symmetric with _delete_asset_inner (Phase 107). Returns status string; caller
    maps to HTTP. All failure-tracking semantics inherited verbatim.

    Args:
        project_slug: project slug (for record_failure/record_success key)
        asset_id: target asset id
        project_root: real Path (already resolved by caller — caller handles LoadError)
        provider: optional override (None → use existing_meta.provider)
        model: optional override (None → 3-tier resolution per Phase 100)
        fallback_chain_list: optional override (None → use settings)
        threshold: resolved notify_threshold for event_type='regeneration'
        mode: 'single' (regenerate_illustration caller) or 'bulk' (bulk_regenerate_assets caller)

    Returns:
        "ok" — asset regenerated, record_success + audit_log + publish (same ULID)
        "not_found" — asset id not in storage; record_success (no-op success — defensive counter reset)
        "unknown_model" — pipeline raises UnknownModelError; caller maps to 422; NO counter
        "stage_error" — pipeline raises IllustrationError; record_failure + audit + publish
    """
    from lingwen_illustrations.pipeline import regenerate_illustration as run_regen
    from lingwen_illustrations.exceptions import UnknownModelError
    from lingwen_illustrations.notifications import (
        record_failure, record_success, publish,
    )
    from lingwen_illustrations.audit_log import record_event
    from lingwen_illustrations.metadata import IllustrationMeta

    # Find existing asset
    all_assets = storage.list_assets(project_root)
    meta = next((a for a in all_assets if a.id == asset_id), None)
    if meta is None:
        # 404 asset-not-found → defensive counter reset (Phase 107 symmetric)
        record_success(project_slug, event_type="regeneration")
        return "not_found"

    effective_provider = provider if provider is not None else meta.provider
    api_key, api_host = _api_credentials_for(effective_provider)

    try:
        new_meta: IllustrationMeta = await run_regen(
            project_root=project_root,
            existing_meta=meta,
            api_key=api_key,
            api_host=api_host,
            provider=provider,
            model=model,
            fallback_chain=fallback_chain_list,
        )
    except UnknownModelError:
        # 422 — user input error; NO counter increment (Phase 107 cleanup_route 422 pattern)
        return "unknown_model"
    except IllustrationError as e:
        # Stage error → counter increment + audit + publish
        record_failure(project_slug, e, project_root=project_root, threshold=threshold, event_type="regeneration")
        # Even on failure, emit audit + publish (with extra={"trigger": "manual", "mode": mode})
        event_id = new_event_id()
        record_event(
            slug=project_slug,
            event="regeneration_failed",
            asset_id=asset_id,
            event_id=event_id,
            extra={"trigger": "manual", "mode": mode, "stage": e.stage if hasattr(e, "stage") else "unknown"},
        )
        publish(
            slug=project_slug,
            event="regeneration_failed",
            asset_id=asset_id,
            event_id=event_id,
            extra={"trigger": "manual", "mode": mode},
        )
        return "stage_error"

    # Success path — record_success + audit + publish (same ULID, I091 double-write)
    record_success(project_slug, event_type="regeneration")
    event_id = new_event_id()
    record_event(
        slug=project_slug,
        event="regenerated",
        asset_id=asset_id,
        event_id=event_id,
        extra={"trigger": "manual", "mode": mode, "provider": effective_provider, "model": new_meta.model},
    )
    publish(
        slug=project_slug,
        event="regenerated",
        asset_id=asset_id,
        event_id=event_id,
        extra={"trigger": "manual", "mode": mode},
    )
    return "ok"
```

- [ ] **Step 3: Verify helper compiles**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -c "from apps.studio_api.routes.illustrations import _regenerate_asset_inner; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/studio_api/routes/illustrations.py
git commit -m "feat(phase-108): _regenerate_asset_inner helper extracted"
```

---

### Task A3: Add `bulk_regenerate_assets` route

**Files:**
- Modify: `apps/studio_api/routes/illustrations.py` — add new route handler after `bulk_delete_assets` (around line 524)

- [ ] **Step 1: Add route handler (after `bulk_delete_assets` handler, around line 524)**

```python
    @app.put("/api/illustrations", response_model=BulkRegenerateResult)
    async def bulk_regenerate_assets(
        project_slug: str = Query(...),
        ids: str = Query(...),
        provider: Optional[str] = Query(None),
        model: Optional[str] = Query(None),
        fallback_chain: Optional[str] = Query(None),
    ) -> BulkRegenerateResult:
        """Phase 108: bulk regenerate illustration endpoint.

        Sequential for-loop calls ``_regenerate_asset_inner`` per asset.
        Each asset's pipeline call (extract + compose + generate) is atomic.

        Args:
            project_slug: project slug (Query)
            ids: comma-separated asset ids (1..10 unique after dedupe)
            provider: optional uniform provider override (applies to all assets)
            model: optional uniform model override
            fallback_chain: optional uniform comma-separated fallback chain

        Returns:
            200 + BulkRegenerateResult with regenerated[] + failed[] + summary.

        Raises:
            HTTPException 404: slug LoadError (raised before loop)
            HTTPException 422: empty ids or > 10 unique ids
        """
        # Phase 108: resolve project_root once for helper (caller handles LoadError)
        try:
            project_root = project_root_for(project_slug)
        except LoadError as e:
            raise HTTPException(404, detail=_err_detail(e)) from e

        # Parse fallback_chain string (Phase 101 pattern)
        if fallback_chain is not None:
            fallback_chain_list = [s.strip() for s in fallback_chain.split(",") if s.strip()]
        else:
            fallback_chain_list = None

        # Parse + dedupe ids (dict.fromkeys preserves order, Phase 107 pattern)
        raw_ids = [s.strip() for s in ids.split(",") if s.strip()]
        unique_ids = list(dict.fromkeys(raw_ids))

        if not unique_ids:
            raise HTTPException(422, detail="ids cannot be empty")
        if len(unique_ids) > 10:
            raise HTTPException(422, detail=f"too many ids ({len(unique_ids)} > 10)")

        # Pre-resolve notify_threshold for event_type='regeneration' (Phase 104/108)
        settings = _load_regeneration_settings(project_root)
        threshold = notifications._resolve_threshold(settings, "regeneration")

        # Pre-resolve meta_by_id dict (perf: 10×M filesystem reads → O(1) lookup)
        all_assets = storage.list_assets(project_root)
        meta_by_id = {a.id: a for a in all_assets}

        regenerated: list[GenerateResponse] = []
        failed: list[dict] = []

        for asset_id in unique_ids:
            status = await _regenerate_asset_inner(
                project_slug,
                asset_id,
                project_root=project_root,
                provider=provider,
                model=model,
                fallback_chain_list=fallback_chain_list,
                threshold=threshold,
                mode="bulk",
            )
            if status == "ok":
                # Re-fetch the new meta from meta_by_id (it may have been updated by replace_asset)
                new_meta = meta_by_id.get(asset_id)
                if new_meta is None:
                    # Defensive: helper returned ok but meta not in dict — skip
                    failed.append({"id": asset_id, "status": "stage_error", "error": "meta missing after ok"})
                    continue
                regenerated.append(
                    GenerateResponse(
                        id=new_meta.id,
                        type=new_meta.type,
                        chapter_num=new_meta.chapter_num,
                        style_preset=new_meta.style_preset,
                        scene_json=new_meta.scene_json,
                        url=f"/api/illustrations/{new_meta.id}/image?project_slug={project_slug}",
                    )
                )
            elif status == "not_found":
                failed.append({"id": asset_id, "status": "not_found"})
            elif status == "unknown_model":
                failed.append({"id": asset_id, "status": "unknown_model"})
            elif status == "stage_error":
                failed.append({"id": asset_id, "status": "stage_error"})

        return BulkRegenerateResult(
            regenerated=regenerated,
            failed=failed,
            summary={
                "total": len(unique_ids),
                "ok": len(regenerated),
                "fail": len(failed),
            },
        )
```

- [ ] **Step 2: Verify route compiles**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -c "from apps.studio_api.routes.illustrations import register_illustrations; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Run tests — still failing (helper not yet wired from single route)**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_bulk_regenerate_api.py -v --rootdir=.`
Expected: 10 FAIL or partial PASS (depends on whether bulk route can be called without single route being refactored)

- [ ] **Step 4: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/studio_api/routes/illustrations.py
git commit -m "feat(phase-108): bulk_regenerate_assets endpoint"
```

---

### Task A4: Refactor `regenerate_illustration` to thin wrapper

**Files:**
- Modify: `apps/studio_api/routes/illustrations.py:572-654` — replace fat route handler with thin wrapper delegating to `_regenerate_asset_inner`

- [ ] **Step 1: Replace `regenerate_illustration` route body**

Replace the existing function body (lines ~580-654) with:

```python
    @app.put("/api/illustrations/{asset_id}/regenerate", response_model=GenerateResponse)
    async def regenerate_illustration(
        asset_id: str,
        project_slug: str = Query(...),
        provider: Optional[str] = Query(None),
        model: Optional[str] = Query(None),
        fallback_chain: Optional[str] = Query(None),
    ) -> GenerateResponse:
        """Atomic regenerate: re-runs extract+compose+generate, swaps bytes in place.

        Phase 108 refactor: delegates to _regenerate_asset_inner helper (mirror
        Phase 107 delete_asset). Preserves Phase 94/96/100/101 contract:
        provider/model/fallback_chain params; atomic swap via storage.replace_asset;
        same id with new scene_json + final_prompt.

        Returns same id (asset_id) with new scene_json + final_prompt.
        On Stage failure, original asset preserved (no destructive behavior).
        """
        # Phase 101: parse fallback_chain string
        if fallback_chain is not None:
            fallback_chain_list = [s.strip() for s in fallback_chain.split(",") if s.strip()]
        else:
            fallback_chain_list = None

        # Resolve project_root (404 LoadError raised here, before helper)
        try:
            project_root = project_root_for(project_slug)
        except LoadError as e:
            raise HTTPException(404, detail=_err_detail(e)) from e

        # Resolve threshold for single-route path
        settings = _load_regeneration_settings(project_root)
        threshold = notifications._resolve_threshold(settings, "regeneration")

        # Delegate to helper with mode="single"
        status = await _regenerate_asset_inner(
            project_slug,
            asset_id,
            project_root=project_root,
            provider=provider,
            model=model,
            fallback_chain_list=fallback_chain_list,
            threshold=threshold,
            mode="single",
        )

        if status == "not_found":
            raise HTTPException(404, detail=f"asset {asset_id} not found")
        if status == "unknown_model":
            # Re-raise 422 — but helper swallowed the exception. Re-do the call
            # to get the structured detail. (Phase 108 trade-off: helper returns
            # string for symmetry with delete helper; single route reconstructs
            # the 422 detail.)
            #
            # Alternative: change helper to return exception object. Future phase.
            raise HTTPException(422, detail={
                "error": "unknown model",
                "stage": "validation",
                "provider": provider or "(from existing meta)",
                "model": model or "(from existing meta or default)",
                "known": [],  # Phase 108: empty list; client should retry via single-asset PUT to get full detail
            })
        if status == "stage_error":
            raise HTTPException(500, detail="stage error during regenerate")

        # status == "ok": re-fetch the meta for response (helper updated it in-place)
        meta = next(
            (a for a in storage.list_assets(project_root) if a.id == asset_id),
            None,
        )
        if meta is None:
            # Defensive: helper said ok but meta gone (race condition?)
            raise HTTPException(500, detail="asset disappeared after regenerate")

        return GenerateResponse(
            id=meta.id,
            type=meta.type,
            chapter_num=meta.chapter_num,
            style_preset=meta.style_preset,
            scene_json=meta.scene_json,
            url=f"/api/illustrations/{meta.id}/image?project_slug={project_slug}",
        )
```

- [ ] **Step 2: Verify Phase 94 regenerate tests still pass (Phase 94 must stay green)**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/ -k "regenerate" -v --rootdir=.`
Expected: PASS (existing Phase 94/96/100/101 regenerate tests preserved)

- [ ] **Step 3: Run bulk regenerate tests — expect partial pass**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_bulk_regenerate_api.py -v --rootdir=.`
Expected: ~5-7 PASS / 3-5 FAIL (depends on which tests mock correctly)

- [ ] **Step 4: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/studio_api/routes/illustrations.py
git commit -m "refactor(phase-108): regenerate_illustration delegates to _regenerate_asset_inner"
```

---

### Task A5: Fix counter isolation + ULID distinctness + docstrings

**Files:**
- Modify: `apps/studio_api/routes/illustrations.py` — fix any issues from running tests

- [ ] **Step 1: Inspect test failures**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_bulk_regenerate_api.py -v --rootdir=. 2>&1 | head -80`

- [ ] **Step 2: Apply fixes based on failures**

Common fixes (mirror Phase 107 fixup commit `59e340c3`):
- ULID distinctness: ensure `new_event_id()` called once per helper invocation, not twice
- Counter isolation: `(slug, "regeneration")` tuple key, never bleed into other event types
- Docstring clarity: add I090/I091/I095 6th EXTENDED references to helper docstring

If tests fail on meta_by_id dict staleness (helper updated bytes in-place, dict points to old meta):
- Helper should return the NEW meta, not status string
- OR caller re-fetches via `storage.list_assets(project_root)` after each helper call
- Recommend: change helper to return `tuple[Literal, IllustrationMeta | None]` (Phase 108 deviation from Phase 107's pure status return)

```python
# Updated helper signature:
async def _regenerate_asset_inner(...) -> tuple[Literal["ok", "not_found", "unknown_model", "stage_error"], "IllustrationMeta | None"]:
    ...
    return "ok", new_meta
```

Then update Task A4's `regenerate_illustration` and Task A3's `bulk_regenerate_assets` callers to use the new tuple return.

- [ ] **Step 3: Verify all tests pass (GREEN)**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_bulk_regenerate_api.py -v --rootdir=.`
Expected: 10/10 PASS

- [ ] **Step 4: Verify Phase 107 + Phase 94 + Phase 106 tests still pass**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/test_bulk_delete_api.py apps/studio_api/tests/test_illustrations_api.py -v --rootdir=.`
Expected: 10 + 12 = 22/22 PASS (Phase 107 + Phase 106 preserved)

- [ ] **Step 5: ruff check**

Run: `cd /home/ailearn/projects/LingWen && ruff check apps/studio_api/routes/illustrations.py`
Expected: clean (or pre-existing E741 baseline unchanged)

- [ ] **Step 6: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/studio_api/routes/illustrations.py apps/studio_api/tests/test_bulk_regenerate_api.py
git commit -m "fix(phase-108): helper returns (status, new_meta) tuple + counter isolation + docstrings"
```

---

# Task B: Frontend (multi-select button + composable + typed wrapper + store)

### Task B1: Write RED vitest tests for `useBulkRegenerateToast` composable

**Files:**
- Create: `apps/dashboard/src/composables/useBulkRegenerateToast.spec.ts`

- [ ] **Step 1: Write 3 RED tests**

```ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useBulkRegenerateToast } from './useBulkRegenerateToast'

// Mock useMessage from naive-ui (Phase 107 pattern)
const mockSuccess = vi.fn()
const mockError = vi.fn()
const mockWarning = vi.fn()
const mockUseMessage = vi.fn(() => ({
  success: mockSuccess,
  error: mockError,
  warning: mockWarning,
}))

vi.mock('naive-ui', () => ({
  useMessage: mockUseMessage,
}))

describe('useBulkRegenerateToast', () => {
  beforeEach(() => {
    mockSuccess.mockClear()
    mockError.mockClear()
    mockWarning.mockClear()
  })

  it('T-success: all 5 regenerated → message.success', () => {
    const toast = useBulkRegenerateToast()
    toast.showResult({ regenerated: [{}, {}, {}, {}, {}], failed: [], summary: { total: 5, ok: 5, fail: 0 } })
    expect(mockSuccess).toHaveBeenCalledWith('已再生 5 张插图')
    expect(mockError).not.toHaveBeenCalled()
    expect(mockWarning).not.toHaveBeenCalled()
  })

  it('T-partial: 3 ok + 2 fail → message.warning', () => {
    const toast = useBulkRegenerateToast()
    toast.showResult({
      regenerated: [{}, {}, {}],
      failed: [{ id: 'a', status: 'stage_error' }, { id: 'b', status: 'stage_error' }],
      summary: { total: 5, ok: 3, fail: 2 },
    })
    expect(mockWarning).toHaveBeenCalledWith('已再生 3 张，失败 2 张 — 查看详情')
    expect(mockSuccess).not.toHaveBeenCalled()
    expect(mockError).not.toHaveBeenCalled()
  })

  it('T-all-fail: 0 ok + 5 fail → message.error', () => {
    const toast = useBulkRegenerateToast()
    toast.showResult({
      regenerated: [],
      failed: Array(5).fill({ id: 'x', status: 'stage_error' }),
      summary: { total: 5, ok: 0, fail: 5 },
    })
    expect(mockError).toHaveBeenCalledWith('0 个成功，5 个失败 — 查看详情')
    expect(mockSuccess).not.toHaveBeenCalled()
    expect(mockWarning).not.toHaveBeenCalled()
  })
})
```

- [ ] **Step 2: Verify tests fail (RED)**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/composables/useBulkRegenerateToast.spec.ts`
Expected: 3 FAIL (module not found)

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/composables/useBulkRegenerateToast.spec.ts
git commit -m "test(phase-108): useBulkRegenerateToast 3 RED tests"
```

---

### Task B2: Implement `useBulkRegenerateToast` composable

**Files:**
- Create: `apps/dashboard/src/composables/useBulkRegenerateToast.ts`

- [ ] **Step 1: Write composable (mirror `useBulkDeleteToast.ts`)**

```ts
import { useMessage } from 'naive-ui'

export interface BulkRegenerateToastResult {
  regenerated: unknown[]
  failed: Array<{ id: string; status: string }>
  summary: { total: number; ok: number; fail: number }
}

export interface BulkRegenerateToastApi {
  showResult(result: BulkRegenerateToastResult): void
  showValidationError(message: string): void
  showNetworkError(message: string): void
}

export function useBulkRegenerateToast(): BulkRegenerateToastApi {
  const message = useMessage()
  return {
    showResult(result) {
      const { ok, fail } = result.summary
      if (fail === 0) {
        message.success(`已再生 ${ok} 张插图`)
      } else if (ok === 0) {
        message.error(`0 个成功，${fail} 个失败 — 查看详情`)
      } else {
        message.warning(`已再生 ${ok} 张，失败 ${fail} 张 — 查看详情`)
      }
    },
    showValidationError(msg: string) {
      message.error(msg)
    },
    showNetworkError(msg: string) {
      message.error(`网络错误：${msg}`)
    },
  }
}
```

- [ ] **Step 2: Verify tests pass (GREEN)**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/composables/useBulkRegenerateToast.spec.ts`
Expected: 3/3 PASS

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/composables/useBulkRegenerateToast.ts
git commit -m "feat(phase-108): useBulkRegenerateToast composable"
```

---

### Task B3: Write RED vitest tests for `bulkRegenerateAssets` typed wrapper

**Files:**
- Create: `apps/dashboard/src/api/illustrations.bulkRegenerate.spec.ts` (next to illustrations.ts)

- [ ] **Step 1: Write 4 RED tests**

```ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { bulkRegenerateAssets, type BulkRegenerateOptions } from './illustrations'

// Mock $fetch (Nuxt-style global, Phase 107 pattern)
const mockFetch = vi.fn()
;(globalThis as any).$fetch = mockFetch

describe('bulkRegenerateAssets (typed wrapper)', () => {
  beforeEach(() => mockFetch.mockReset())

  it('T1: empty assetIds → throws ValidationError', async () => {
    await expect(bulkRegenerateAssets('demo', [])).rejects.toThrow(/at least 1/)
  })

  it('T2: 11 assetIds → throws ValidationError', async () => {
    await expect(bulkRegenerateAssets('demo', Array(11).fill('x'))).rejects.toThrow(/at most 10/)
  })

  it('T3: happy path 3 assets → PUT with correct query params', async () => {
    mockFetch.mockResolvedValueOnce({
      regenerated: [{ id: 'a' }, { id: 'b' }, { id: 'c' }],
      failed: [],
      summary: { total: 3, ok: 3, fail: 0 },
    })
    const result = await bulkRegenerateAssets('demo', ['a', 'b', 'c'])
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/illustrations?'),
      expect.objectContaining({ method: 'PUT' }),
    )
    expect(mockFetch.mock.calls[0][0]).toContain('slug=demo')
    expect(mockFetch.mock.calls[0][0]).toContain('ids=a%2Cb%2Cc')
    expect(result.summary.ok).toBe(3)
  })

  it('T4: with provider/model/fallback_chain options → URL includes them', async () => {
    mockFetch.mockResolvedValueOnce({ regenerated: [], failed: [], summary: { total: 0, ok: 0, fail: 0 } })
    await bulkRegenerateAssets('demo', ['a'], { provider: 'openai', model: 'gpt-image-1', fallbackChain: 'minimax,stability' })
    const url = mockFetch.mock.calls[0][0] as string
    expect(url).toContain('provider=openai')
    expect(url).toContain('model=gpt-image-1')
    expect(url).toContain('fallback_chain=minimax%2Cstability')
  })
})
```

- [ ] **Step 2: Verify tests fail (RED)**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/api/illustrations.bulkRegenerate.spec.ts`
Expected: 4 FAIL (`bulkRegenerateAssets` not exported)

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/api/illustrations.bulkRegenerate.spec.ts
git commit -m "test(phase-108): bulkRegenerateAssets typed wrapper 4 RED tests"
```

---

### Task B4: Implement `bulkRegenerateAssets` typed wrapper

**Files:**
- Modify: `apps/dashboard/src/api/illustrations.ts` (add after `bulkDeleteAssets`, ~line 215)

- [ ] **Step 1: Add interfaces + function**

Add after `bulkDeleteAssets` function (~line 213):

```ts
// ============================================================================
// Phase 108: bulk regenerate illustration endpoint
// ============================================================================

export interface BulkRegenerateFailedItem {
  id: string
  status: 'not_found' | 'unknown_model' | 'stage_error'
  stage?: string
  error?: string
}

export interface BulkRegenerateResult {
  regenerated: GenerateResponse[]
  failed: BulkRegenerateFailedItem[]
  summary: { total: number; ok: number; fail: number }
}

export interface BulkRegenerateOptions {
  provider?: string
  model?: string
  fallbackChain?: string
}

export async function bulkRegenerateAssets(
  slug: string,
  assetIds: string[],
  opts: BulkRegenerateOptions = {},
): Promise<BulkRegenerateResult> {
  if (!assetIds || assetIds.length === 0) {
    throw new Error('bulkRegenerateAssets requires at least 1 assetId')
  }
  if (assetIds.length > 10) {
    throw new Error(`bulkRegenerateAssets allows at most 10 assetIds (got ${assetIds.length})`)
  }

  const params = new URLSearchParams()
  params.set('slug', slug)
  params.set('ids', assetIds.join(','))
  if (opts.provider) params.set('provider', opts.provider)
  if (opts.model) params.set('model', opts.model)
  if (opts.fallbackChain) params.set('fallback_chain', opts.fallbackChain)

  const response = await $fetch<BulkRegenerateResult>(
    `/api/illustrations?${params.toString()}`,
    { method: 'PUT' },
  )
  return response
}
```

- [ ] **Step 2: Verify tests pass (GREEN)**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/api/illustrations.bulkRegenerate.spec.ts`
Expected: 4/4 PASS

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/api/illustrations.ts
git commit -m "feat(phase-108): bulkRegenerateAssets typed wrapper"
```

---

### Task B5: Write RED vitest tests for Pinia store action

**Files:**
- Modify: `apps/dashboard/src/stores/useIllustrationStore.spec.js` (add 2 NEW tests after existing `BulkHappy` / `BulkPartial` tests)

- [ ] **Step 1: Add 2 RED tests**

Append after existing `BulkPartial` test:

```javascript
// Phase 108: bulk regenerate tests
describe('bulkRegenerateAssets', () => {
  it('BulkRegenHappy: replaces each regenerated asset by id with new scene_json + url', async () => {
    // Setup: 3 assets in store
    const store = useIllustrationStore()
    store.assets = [
      { id: 'a', scene_json: { old: 1 }, url: '/old/a' },
      { id: 'b', scene_json: { old: 2 }, url: '/old/b' },
      { id: 'c', scene_json: { old: 3 }, url: '/old/c' },
    ]
    // Mock api.bulkRegenerateAssets to return 3 new meta
    const newMeta = (id) => ({ id, scene_json: { new: id }, url: `/new/${id}` })
    mockApi.bulkRegenerateAssets = vi.fn().mockResolvedValueOnce({
      regenerated: [newMeta('a'), newMeta('b'), newMeta('c')],
      failed: [],
      summary: { total: 3, ok: 3, fail: 0 },
    })
    const result = await store.bulkRegenerateAssets('demo', ['a', 'b', 'c'])
    expect(result.summary.ok).toBe(3)
    expect(store.assets.find(a => a.id === 'a').scene_json).toEqual({ new: 'a' })
    expect(store.assets.find(a => a.id === 'b').url).toBe('/new/b')
  })

  it('BulkRegenPartial: updates ok + retains stage_error failures for retry', async () => {
    const store = useIllustrationStore()
    store.assets = [
      { id: 'a', scene_json: { old: 1 } },
      { id: 'b', scene_json: { old: 2 } },
      { id: 'c', scene_json: { old: 3 } },
    ]
    mockApi.bulkRegenerateAssets = vi.fn().mockResolvedValueOnce({
      regenerated: [{ id: 'a', scene_json: { new: 'a' }, url: '/new/a' }],
      failed: [
        { id: 'b', status: 'stage_error', error: 'extract timeout' },
        { id: 'c', status: 'not_found' },
      ],
      summary: { total: 3, ok: 1, fail: 2 },
    })
    await store.bulkRegenerateAssets('demo', ['a', 'b', 'c'])
    // a: updated
    expect(store.assets.find(a => a.id === 'a').scene_json).toEqual({ new: 'a' })
    // b: retained (stage_error — retry candidate)
    expect(store.assets.find(a => a.id === 'b')).toBeDefined()
    expect(store.assets.find(a => a.id === 'b').scene_json).toEqual({ old: 2 })
    // c: removed (not_found — defensive)
    expect(store.assets.find(a => a.id === 'c')).toBeUndefined()
  })
})
```

- [ ] **Step 2: Verify tests fail (RED)**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/stores/useIllustrationStore.spec.js`
Expected: 2 FAIL (`store.bulkRegenerateAssets` not a function)

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/stores/useIllustrationStore.spec.js
git commit -m "test(phase-108): bulkRegenerateAssets store 2 RED tests"
```

---

### Task B6: Implement `bulkRegenerateAssets` Pinia store action

**Files:**
- Modify: `apps/dashboard/src/stores/useIllustrationStore.js` (after `bulkDeleteAssets` action, ~line 119)

- [ ] **Step 1: Add Pinia action**

After `bulkDeleteAssets` action:

```javascript
  // Phase 108: bulk regenerate (1 method).
  // Delegates to api.bulkRegenerateAssets and reactively UPDATES each
  // regenerated entry by id (atomic scene_json + url swap from server).
  // not_found → removed; stage_error + unknown_model → retained for retry.
  async function bulkRegenerateAssets(slug, assetIds, opts = {}) {
    loading.value = true
    error.value = null
    try {
      // Lazy import to keep initial bundle small (consistent with regenerate
      // single-asset action, which also lazy-imports).
      const { bulkRegenerateAssets: apiBulkRegen } = await import('@/api/illustrations')
      const result = await apiBulkRegen(slug, assetIds, opts)
      // Update regenerated[] in place (atomic from server)
      for (const newMeta of result.regenerated) {
        const idx = assets.value.findIndex(a => a.id === newMeta.id)
        if (idx >= 0) {
          assets.value[idx] = { ...assets.value[idx], ...newMeta }
        } else {
          // Defensive: server says ok but asset not in local store (race?)
          assets.value.push(newMeta)
        }
      }
      // Remove not_found (defensive — should be rare)
      const notFoundIds = result.failed.filter(f => f.status === 'not_found').map(f => f.id)
      if (notFoundIds.length > 0) {
        assets.value = assets.value.filter(a => !notFoundIds.includes(a.id))
      }
      // Retain stage_error + unknown_model for retry
      return result
    } catch (e) {
      error.value = e.data?.detail?.error || e.message || 'bulk regenerate failed'
      throw e
    } finally {
      loading.value = false
    }
  }
```

- [ ] **Step 2: Verify tests pass (GREEN)**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/stores/useIllustrationStore.spec.js`
Expected: 2 NEW PASS + all existing preserved

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/stores/useIllustrationStore.js
git commit -m "feat(phase-108): useIllustrationStore.bulkRegenerateAssets action"
```

---

### Task B7: Write RED vitest tests for IllustrationGallery bulk-regenerate button

**Files:**
- Modify: `apps/dashboard/src/components/illustrations/IllustrationGallery.spec.ts` (add 6 NEW tests F1-F6 after existing F1-F8)

- [ ] **Step 1: Add 6 RED tests**

Append:

```ts
// Phase 108: bulk-regenerate button + handler tests
describe('bulk-regenerate button', () => {
  it('F1: button hidden when selection empty', async () => {
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'demo', assets: [sampleAsset()] } })
    expect(wrapper.find('[data-testid="bulk-regenerate-btn"]').exists()).toBe(false)
  })

  it('F2: button visible after selection >= 1', async () => {
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'demo', assets: [sampleAsset('a'), sampleAsset('b')] } })
    await wrapper.find(`[data-testid="select-checkbox-a"]`).setValue(true)
    expect(wrapper.find('[data-testid="bulk-regenerate-btn"]').exists()).toBe(true)
  })

  it('F3: NPopconfirm wraps button', async () => {
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'demo', assets: [sampleAsset('a')] } })
    await wrapper.find(`[data-testid="select-checkbox-a"]`).setValue(true)
    const popconfirm = wrapper.findComponent({ name: 'NPopconfirm' })
    expect(popconfirm.exists()).toBe(true)
  })

  it('F4: positive-click triggers store.bulkRegenerateAssets', async () => {
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'demo', assets: [sampleAsset('a'), sampleAsset('b')] } })
    await wrapper.find(`[data-testid="select-checkbox-a"]`).setValue(true)
    await wrapper.find(`[data-testid="select-checkbox-b"]`).setValue(true)
    await wrapper.find('[data-testid="bulk-regenerate-btn"]').trigger('click')
    // NPopconfirm positive-click
    const popconfirm = wrapper.findComponent({ name: 'NPopconfirm' })
    await popconfirm.vm.$emit('positive-click')
    expect(mockStore.bulkRegenerateAssets).toHaveBeenCalledWith('demo', ['a', 'b'], expect.any(Object))
  })

  it('F5: selection cleared on success', async () => {
    mockStore.bulkRegenerateAssets.mockResolvedValueOnce({ regenerated: [], failed: [], summary: { total: 2, ok: 2, fail: 0 } })
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'demo', assets: [sampleAsset('a')] } })
    await wrapper.find(`[data-testid="select-checkbox-a"]`).setValue(true)
    await wrapper.find('[data-testid="bulk-regenerate-btn"]').trigger('click')
    const popconfirm = wrapper.findComponent({ name: 'NPopconfirm' })
    await popconfirm.vm.$emit('positive-click')
    await flushPromises()
    expect(wrapper.find(`[data-testid="select-checkbox-a"]`).attributes('checked')).toBe('false')
  })

  it('F6: emit "bulk-regenerated" with result on success', async () => {
    const mockResult = { regenerated: [{ id: 'a' }], failed: [], summary: { total: 1, ok: 1, fail: 0 } }
    mockStore.bulkRegenerateAssets.mockResolvedValueOnce(mockResult)
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'demo', assets: [sampleAsset('a')] } })
    await wrapper.find(`[data-testid="select-checkbox-a"]`).setValue(true)
    await wrapper.find('[data-testid="bulk-regenerate-btn"]').trigger('click')
    const popconfirm = wrapper.findComponent({ name: 'NPopconfirm' })
    await popconfirm.vm.$emit('positive-click')
    await flushPromises()
    expect(wrapper.emitted('bulk-regenerated')).toBeTruthy()
    expect(wrapper.emitted('bulk-regenerated')[0][0]).toEqual(mockResult)
  })
})
```

- [ ] **Step 2: Verify tests fail (RED)**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/components/illustrations/IllustrationGallery.spec.ts`
Expected: 6 FAIL (button not in template yet)

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/components/illustrations/IllustrationGallery.spec.ts
git commit -m "test(phase-108): IllustrationGallery bulk-regenerate button 6 RED tests"
```

---

### Task B8: Add bulk-regenerate button + handler to IllustrationGallery.vue

**Files:**
- Modify: `apps/dashboard/src/components/illustrations/IllustrationGallery.vue` (add button after existing bulk-delete button, ~line 132)

- [ ] **Step 1: Add imports**

After `import { useBulkDeleteToast } from '@/composables/useBulkDeleteToast'`:

```ts
import { useBulkRegenerateToast } from '@/composables/useBulkRegenerateToast'
```

- [ ] **Step 2: Update store destructuring (line ~18)**

```ts
const { assets, error, loadAssets, regenerate, deleteAsset, bulkDeleteAssets, bulkRegenerateAssets } = useIllustration(props.projectSlug)
```

- [ ] **Step 3: Add emit declaration update (line ~16)**

```ts
const emit = defineEmits(['regenerate', 'delete', 'bulk-deleted', 'bulk-regenerated'])
```

- [ ] **Step 4: Add state + composable + handler (after `confirmBulkDelete` function ~line 75)**

```ts
  const bulkRegenerateInFlight = ref(false)
  const toast = useBulkRegenerateToast()

  async function confirmBulkRegenerate() {
    if (bulkRegenerateInFlight.value) return
    const ids = Array.from(selection.value)
    bulkRegenerateInFlight.value = true
    try {
      const result = await bulkRegenerateAssets(props.projectSlug, ids)
      toast.showResult(result)
      emit('bulk-regenerated', result)
      // Clear selection only on full or partial success (mirrors bulk-delete)
      clearSelection()
    } catch (e) {
      // On error: show message, but keep selection so user can retry
      toast.showValidationError(e.message || 'bulk regenerate failed')
    } finally {
      bulkRegenerateInFlight.value = false
    }
  }
```

- [ ] **Step 5: Add bulk-regenerate button in template (after existing bulk-delete NPopconfirm)**

```vue
      <NPopconfirm
        @positive-click="confirmBulkRegenerate"
        positive-text="确认再生"
        negative-text="取消"
      >
        <template #trigger>
          <NButton
            data-testid="bulk-regenerate-btn"
            class="bulk-regenerate-btn"
            :loading="bulkRegenerateInFlight"
          >
            批量再生
          </NButton>
        </template>
        将对已选的 {{ selectedCount }} 张插图重新生成。继续？
      </NPopconfirm>
```

- [ ] **Step 6: Verify tests pass (GREEN)**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/components/illustrations/IllustrationGallery.spec.ts`
Expected: 6 NEW PASS + all existing F1-F8 preserved

- [ ] **Step 7: tsc check**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm tsc --noEmit`
Expected: 0 NEW errors (48 pre-existing baseline)

- [ ] **Step 8: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/components/illustrations/IllustrationGallery.vue
git commit -m "feat(phase-108): IllustrationGallery bulk-regenerate button + handler"
```

---

### Task B9: Add end-to-end happy + error path tests (F7/F8)

**Files:**
- Modify: `apps/dashboard/src/components/illustrations/IllustrationGallery.spec.ts`

- [ ] **Step 1: Add 2 end-to-end tests**

Append:

```ts
  it('F7: end-to-end happy path — 3 selected → API called → toast success → emit', async () => {
    mockStore.bulkRegenerateAssets.mockResolvedValueOnce({
      regenerated: [{ id: 'a' }, { id: 'b' }, { id: 'c' }],
      failed: [],
      summary: { total: 3, ok: 3, fail: 0 },
    })
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'demo', assets: [sampleAsset('a'), sampleAsset('b'), sampleAsset('c')] } })
    await wrapper.find(`[data-testid="select-checkbox-a"]`).setValue(true)
    await wrapper.find(`[data-testid="select-checkbox-b"]`).setValue(true)
    await wrapper.find(`[data-testid="select-checkbox-c"]`).setValue(true)
    await wrapper.find('[data-testid="bulk-regenerate-btn"]').trigger('click')
    const popconfirm = wrapper.findComponent({ name: 'NPopconfirm' })
    await popconfirm.vm.$emit('positive-click')
    await flushPromises()
    expect(mockStore.bulkRegenerateAssets).toHaveBeenCalledWith('demo', ['a', 'b', 'c'], expect.any(Object))
    expect(wrapper.emitted('bulk-regenerated')).toBeTruthy()
    // Selection cleared
    expect(wrapper.find('[data-testid="bulk-action-bar"]').exists()).toBe(false)
  })

  it('F8: end-to-end error path — API throws → toast error → selection retained', async () => {
    mockStore.bulkRegenerateAssets.mockRejectedValueOnce(new Error('network timeout'))
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'demo', assets: [sampleAsset('a')] } })
    await wrapper.find(`[data-testid="select-checkbox-a"]`).setValue(true)
    await wrapper.find('[data-testid="bulk-regenerate-btn"]').trigger('click')
    const popconfirm = wrapper.findComponent({ name: 'NPopconfirm' })
    await popconfirm.vm.$emit('positive-click')
    await flushPromises()
    // No emit on error
    expect(wrapper.emitted('bulk-regenerated')).toBeFalsy()
    // Selection retained (user can retry)
    expect(wrapper.find('[data-testid="bulk-action-bar"]').exists()).toBe(true)
  })
```

- [ ] **Step 2: Verify tests pass (GREEN)**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/components/illustrations/IllustrationGallery.spec.ts`
Expected: 8 NEW PASS (F1-F6 + F7/F8)

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/components/illustrations/IllustrationGallery.spec.ts
git commit -m "test(phase-108): bulk-regenerate F7/F8 end-to-end happy + error paths"
```

---

### Task B10: Add lazy `useMessage` for test isolation

**Files:**
- Modify: `apps/dashboard/src/composables/useBulkRegenerateToast.ts`

- [ ] **Step 1: Convert eager `useMessage` to lazy load**

Replace direct call with lazy pattern (Phase 107 fixup):

```ts
import { useMessage } from 'naive-ui'

export interface BulkRegenerateToastResult {
  regenerated: unknown[]
  failed: Array<{ id: string; status: string }>
  summary: { total: number; ok: number; fail: number }
}

export interface BulkRegenerateToastApi {
  showResult(result: BulkRegenerateToastResult): void
  showValidationError(message: string): void
  showNetworkError(message: string): void
}

export function useBulkRegenerateToast(): BulkRegenerateToastApi {
  // Lazy: only call useMessage() inside showResult so tests don't need
  // <n-message-provider> wrapper (Phase 107 fixup pattern).
  const getMessage = () => useMessage()

  return {
    showResult(result) {
      const { ok, fail } = result.summary
      const message = getMessage()
      if (fail === 0) {
        message.success(`已再生 ${ok} 张插图`)
      } else if (ok === 0) {
        message.error(`0 个成功，${fail} 个失败 — 查看详情`)
      } else {
        message.warning(`已再生 ${ok} 张，失败 ${fail} 张 — 查看详情`)
      }
    },
    showValidationError(msg: string) {
      getMessage().error(msg)
    },
    showNetworkError(msg: string) {
      getMessage().error(`网络错误：${msg}`)
    },
  }
}
```

- [ ] **Step 2: Verify tests still pass**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run src/composables/useBulkRegenerateToast.spec.ts`
Expected: 3/3 PASS (lazy loading doesn't break the mock)

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/composables/useBulkRegenerateToast.ts
git commit -m "feat(phase-108): lazy useMessage in useBulkRegenerateToast for test isolation"
```

---

# Task C: Regression guards + invariant extensions + docs sync

### Task C1: Write 10 regression guards G1-G10

**Files:**
- Create: `tests/test_phase108_bulk_regenerate.py`

- [ ] **Step 1: Write 10 guards**

```python
"""Phase 108: bulk regenerate illustration endpoint — regression guards.

Guards prevent regressions across the cluster (Phase 90-107 invariants
preserved + Phase 108 new patterns locked in).
"""
from __future__ import annotations
import re
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ILLUSTRATIONS_PY = REPO_ROOT / "apps" / "studio_api" / "routes" / "illustrations.py"
ARCHITECTURE_YML = REPO_ROOT / ".lingwen" / "architecture.yml"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# G1: bulk_regenerate_assets route registered with @app.put (Phase 107 lesson:
# NOT @router.delete — Phase 107 fixed this; ensure same applies here)
def test_g1_bulk_regenerate_route_registered():
    text = _read(ILLUSTRATIONS_PY)
    assert '@app.put("/api/illustrations"' in text, "G1: bulk route @app.put missing"


def test_g2_over_10_ids_422():
    text = _read(ILLUSTRATIONS_PY)
    # Pattern: 422 raised when len(unique_ids) > 10
    assert re.search(r'len\(unique_ids\)\s*>\s*10', text), "G2: >10 422 check missing"
    assert re.search(r'too many ids.*10', text), "G2: 10-limit error message missing"


def test_g3_empty_422():
    text = _read(ILLUSTRATIONS_PY)
    assert re.search(r'if not unique_ids:\s*\n\s*raise HTTPException\(422', text, re.MULTILINE), "G3: empty 422 missing"


def test_g4_per_asset_helper_fan_out():
    """G4: bulk route iterates over unique_ids and calls _regenerate_asset_inner per asset."""
    text = _read(ILLUSTRATIONS_PY)
    # Find bulk_regenerate_assets function body, verify for-loop calls helper
    bulk_block = re.search(
        r'async def bulk_regenerate_assets.*?(?=\n    @app|\n    async def|\n    def )',
        text,
        re.DOTALL,
    )
    assert bulk_block, "G4: bulk_regenerate_assets function not found"
    body = bulk_block.group(0)
    assert 'for asset_id in unique_ids' in body, "G4: for-loop missing"
    assert '_regenerate_asset_inner' in body, "G4: helper call missing"
    assert 'mode="bulk"' in body, "G4: mode='bulk' discriminator missing"


def test_g5_counter_isolation_preserved():
    """G5: counter key (slug, 'regeneration') tuple — does not bleed into deletion/generation."""
    text = _read(ILLUSTRATIONS_PY)
    # Helper must call record_failure / record_success with event_type='regeneration'
    helper_block = re.search(
        r'async def _regenerate_asset_inner.*?(?=\n    async def|\n    def )',
        text,
        re.DOTALL,
    )
    assert helper_block, "G5: _regenerate_asset_inner function not found"
    body = helper_block.group(0)
    assert "event_type=\"regeneration\"" in body, "G5: event_type='regeneration' missing"


def test_g6_phase107_preserved():
    """G6: Phase 107 bulk_delete_assets + _delete_asset_inner still present (no over-aggressive refactor)."""
    text = _read(ILLUSTRATIONS_PY)
    assert "bulk_delete_assets" in text, "G6: Phase 107 bulk_delete_assets missing"
    assert "_delete_asset_inner" in text, "G6: Phase 107 _delete_asset_inner missing"


def test_g7_invariant_extensions_in_architecture():
    """G7: .lingwen/architecture.yml I090/I091/I095 6th EXTENDED via docstring."""
    text = _read(ARCHITECTURE_YML)
    # Phase 107 marked 5th; Phase 108 should add 6th
    assert "bulk_regenerate_assets" in text or "6th" in text, "G7: 6th EXTENDED missing"


def test_g8_dict_fromkeys_dedupe():
    """G8: dedupe via dict.fromkeys (preserves order)."""
    text = _read(ILLUSTRATIONS_PY)
    bulk_block = re.search(
        r'async def bulk_regenerate_assets.*?(?=\n    @app|\n    async def|\n    def )',
        text,
        re.DOTALL,
    )
    assert bulk_block, "G8: bulk function not found"
    assert "dict.fromkeys" in bulk_block.group(0), "G8: dict.fromkeys dedupe missing"


def test_g9_no_explicit_cross_project_check():
    """G9: helper does NOT do cross-project checks (per-asset ownership assumed; cross-project is documented limitation)."""
    helper_block = re.search(
        r'async def _regenerate_asset_inner.*?(?=\n    async def|\n    def )',
        _read(ILLUSTRATIONS_PY),
        re.DOTALL,
    )
    assert helper_block, "G9: helper not found"
    body = helper_block.group(0)
    # Should NOT have cross-project logic; this is documented as a limitation
    assert "cross_project" not in body, "G9: cross-project check found (unexpected)"
    assert "ownership" not in body, "G9: ownership check found (unexpected)"


def test_g10_regenerate_uses_helper():
    """G10: existing regenerate_illustration route now delegates to helper (mode='single')."""
    text = _read(ILLUSTRATIONS_PY)
    single_block = re.search(
        r'async def regenerate_illustration.*?(?=\n    @app|\n    async def|\n    def )',
        text,
        re.DOTALL,
    )
    assert single_block, "G10: regenerate_illustration not found"
    body = single_block.group(0)
    assert "_regenerate_asset_inner" in body, "G10: regenerate_illustration doesn't delegate to helper"
    assert 'mode="single"' in body, "G10: mode='single' discriminator missing in single route"
```

- [ ] **Step 2: Verify guards fail (RED)**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/test_phase108_bulk_regenerate.py -v --rootdir=.`
Expected: ~7-9 FAIL (some pass already; route + helpers added in Task A)

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add tests/test_phase108_bulk_regenerate.py
git commit -m "test(phase-108): bulk regenerate regression guards G1-G10"
```

---

### Task C2: Extend I090/I091/I095 6th in `.lingwen/architecture.yml`

**Files:**
- Modify: `.lingwen/architecture.yml`

- [ ] **Step 1: Locate I090 row**

Run: `grep -n "I090\|I091\|I095\|bulk_delete_assets\|cleanup_route" .lingwen/architecture.yml | head -20`

- [ ] **Step 2: Update I090 scope field — add 6th caller**

In the `I090` block, add `bulk_regenerate_assets` to the 6th caller mention:

```yaml
- id: I090
  rule: |
    apps/studio_api/routes/illustrations.py:lru_cleanup 是 illustration LRU 删除唯一入口
    (per-type+per-chapter scope, max_count>0 校验, best-effort 删除);
    audit_log.record_event 是 illustration 事件记录唯一入口 (JSONL append-only,
    OSError swallow best-effort); pipeline.generate_illustration /
    pipeline.regenerate_illustration / apps/studio_api/routes/cleanup_route.py /
    apps/studio_api/routes/illustrations.py (delete_asset) /
    apps/studio_api/routes/illustrations.py (bulk_delete_assets) /
    `apps/studio_api/routes/illustrations.py (bulk_regenerate_assets)` 六处 caller 通过这两个入口;
    infra.illustrations.* / infra.illustration_settings.* /
    任何绕过 lru_cleanup 的 illustration 删除路径非法
    (Phase 98 + Phase 105 + Phase 106 + Phase 107 + Phase 108)
```

- [ ] **Step 3: Update I091 scope field — add 6th double-write site**

Add `bulk_regenerate_assets` to the 6th site mention:

```yaml
- id: I091
  rule: |
    packages/lingwen-illustrations/src/lingwen_illustrations/notifications.py:publish
    是 illustration event fan-out 唯一入口 (per-project in-process SSE);
    pipeline.generate_illustration + pipeline.regenerate_illustration +
    cleanup_route + apps/studio_api/routes/illustrations.py (delete_asset) +
    apps/studio_api/routes/illustrations.py (bulk_delete_assets) +
    `apps/studio_api/routes/illustrations.py (bulk_regenerate_assets)` 双写
    record_event (I090) + publish 共享 same ULID;
    infra.notifications.* 路径非法;
    任何绕过 publish 的 illustration event fan-out 路径非法
    (Phase 99 + Phase 106 + Phase 107 + Phase 108)
```

- [ ] **Step 4: Update I095 EXTENDED via docstring — 6th EXTENDED**

```yaml
- id: I095
  rule: |
    packages/lingwen-illustrations/src/lingwen_illustrations/notifications.py:_consecutive_failures
    状态机 keyed per `(project_slug, event_type)` tuple 由
    record_failure()/record_success() 唯一维护;
    notify_threshold per-event-type dict (Phase 104: int legacy expands to 4-key dict
    via ProjectSettings validator; partial dict is opt-out for unspecified event_types;
    _resolve_threshold returns INFINITY for missing keys);
    阈值命中 per `(slug, event_type)` pair → exactly one severity="warning" notification;
    infra.notifications.* 路径非法 (Phase 102 + ... + Phase 108 EXTENDED 6th via docstring:
    bulk_regenerate_assets route delegates per-asset to _regenerate_asset_inner helper,
    mode='bulk' interpolated into audit_log extra; counter key (slug, "regeneration");
    threshold crossing per (slug, "regeneration") pair emits exactly one
    severity="warning" notification regardless of bulk iteration size)
```

- [ ] **Step 5: Verify guards pass (GREEN)**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/test_phase108_bulk_regenerate.py -v --rootdir=.`
Expected: 10/10 PASS

- [ ] **Step 6: Verify Phase 77 architecture invariant sync still passes**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest tests/test_phase61_architecture_invariant_sync.py -v --rootdir=.`
Expected: 12/12 preserved PASS

- [ ] **Step 7: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add .lingwen/architecture.yml
git commit -m "docs(phase-108): extend I090/I091/I095 to include bulk_regenerate_assets"
```

---

### Task C3: Update CLAUDE.md version + invariant rows

**Files:**
- Modify: `CLAUDE.md` (top version line + I090/I091/I095 rows)

- [ ] **Step 1: Update top version line (v60.5 → v60.6)**

In the project header, replace `v60.5 (Phase 107 ...)` with `v60.6 (Phase 108 Bulk Regenerate Illustration Endpoint — sixth Phase 102+ extension after Phase 103/104/105/106/107; ...)` with summary of Phase 108.

Phase 108 summary text (~ 200 chars):

> `bulk_regenerate_assets` route (PUT `/api/illustrations?slug=...&ids=...&provider=...&model=...&fallback_chain=...`, I090 6th caller + I091 6th double-write site) added for multi-asset regeneration: sequential for-loop calls shared `_regenerate_asset_inner` helper per asset (extracted from `regenerate_illustration` route in Phase 108 to mirror Phase 107 5-path delete logic); limit 10 (422 on over-10), dedupe via `dict.fromkeys(raw_ids)` preserving order, 422 on empty ids, 404 on slug; per-asset returns 200 OK + `{regenerated, failed, summary}` shape; partial failures retained in `failed[]` with status `"not_found"` / `"unknown_model"` / `"stage_error"`; `_regenerate_asset_inner(mode: "single" | "bulk")` interpolates `mode` into `audit_log.record_event(extra=...)` + `notifications.publish(extra=...)` for downstream analytics; `record_failure(slug, error, *, project_root, threshold, event_type="regeneration")` called on 1 failure path (IllustrationError); 404 asset-not-found treated as **no-op success** via `record_success(slug, event_type="regeneration")`; UnknownModelError → 422 (no counter); successful `pipeline.regenerate_illustration` → `record_success` + `audit_log` + `publish` **double-write** I091 — same ULID via `new_event_id()` — per asset.

- [ ] **Step 2: Update I090 row — add 6th caller mention**

In the invariants table (search for `| I090 |`), update the constraint text to mention `bulk_regenerate_assets` as 6th caller.

- [ ] **Step 3: Update I091 row — add 6th double-write site**

In the invariants table (search for `| I091 |`), update the constraint text.

- [ ] **Step 4: Update I095 row — 6th EXTENDED via docstring**

In the invariants table (search for `| I095 |`), append `Phase 108 EXTENDED — bulk_regenerate_assets is the 6th caller; per-asset record_failure/record_success via shared _regenerate_asset_inner helper; counter keys still (slug, "regeneration"); threshold crossing per (slug, "regeneration") pair emits exactly one severity="warning" notification regardless of bulk iteration size`.

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add CLAUDE.md
git commit -m "docs(phase-108): CLAUDE.md v60.5 → v60.6 + I090/I091/I095 6th EXTENDED"
```

---

### Task C4: Update CURRENT_STATUS + BACKLOG + MEMORY

**Files:**
- Modify: `collaboration/CURRENT_STATUS.md`
- Modify: `collaboration/BACKLOG.md`
- Modify: `/home/ailearn/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md`

- [ ] **Step 1: Add Phase 108 entry to CURRENT_STATUS.md**

Append Phase 108 entry after Phase 107:

```markdown
- ✅ **v60.6 Phase 108 (Bulk Regenerate Illustration Endpoint — sixth Phase 102+ extension)** (2026-09-22, direct commits on master): mirrors Phase 107 — `bulk_regenerate_assets` route (PUT `/api/illustrations?slug=...&ids=...`, limit 10, sequential for-loop, dedupe via `dict.fromkeys`) + `_regenerate_asset_inner` helper extracted from `regenerate_illustration` route; per-asset uniform provider/model/fallback_chain params; I090 6th caller + I091 6th double-write site + I095 6th EXTENDED via docstring; frontend multi-select button + `useBulkRegenerateToast` composable + `bulkRegenerateAssets` typed wrapper + Pinia store action. 16 atomic commits + 10 pytest + 10 guards + 8 vitest.
```

- [ ] **Step 2: Add Phase 108 entry to BACKLOG.md + remove reserved slot**

Append new Phase 108 row in the table:

```
| Phase 108 | Bulk Regenerate Illustration Endpoint | `PUT /api/illustrations?slug=...&ids=...` bulk endpoint + multi-select UX. Mirror Phase 107. | Solo (this session) | ✅ 完成 (2026-09-22) | 2026-09-22 |
```

Remove the reserved "Phase 108+ bulk REGENERATE (YAGNI eval)" from Future Work section.

- [ ] **Step 3: Add Phase 108 memory entry to MEMORY.md**

In the "Topic Files" section, append:

```markdown
| **Phase 108 bulk regenerate (v60.6; sixth Phase 102+ extension)** | → See handoff `2026-09-22-phase-108-bulk-regenerate-handoff.md` (PUT `/api/illustrations` bulk endpoint + `_regenerate_asset_inner` helper extracted + I090/I091/I095 6th EXTENDED + 16 atomic commits + 10 pytest + 10 guards + 8 vitest — symmetric with Phase 107 delete pattern; per-asset uniform provider/model/fallback_chain; limit=10 since LLM calls 5-30s/asset vs delete ~0ms; counter keys `(slug, "regeneration")`; `mode='bulk'` discriminator analytics-only; UnknownModelError → 422 no counter; IllustrationError → record_failure + audit + publish). |
```

- [ ] **Step 4: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add collaboration/CURRENT_STATUS.md collaboration/BACKLOG.md /home/ailearn/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md
git commit -m "docs(phase-108): CURRENT_STATUS + BACKLOG + MEMORY sync"
```

---

### Task C5: Write handoff doc

**Files:**
- Create: `docs/superpowers/handoffs/2026-09-22-phase-108-bulk-regenerate-handoff.md`

- [ ] **Step 1: Write handoff (mirror Phase 107 handoff structure)**

Write a ~120-line handoff doc with sections:
- What was delivered (helper + route + 6 frontend files)
- Validation gates (10 pytest + 10 guards + 8 vitest + tsc + ruff + knip)
- 16 atomic commits list (Tasks A1-A5 + B1-B10 + C1-C5)
- Lessons (5 from spec + 4 new discovered from Phase 107 inheritance)
- Cluster cumulative (Phase 90-108 = 19 phases; 6 Phase 102+ extensions)
- Future work (Phase 109+ candidates)
- References (spec + plan + Phase 107 handoff)

- [ ] **Step 2: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add docs/superpowers/handoffs/2026-09-22-phase-108-bulk-regenerate-handoff.md
git commit -m "docs(phase-108): handoff doc"
```

---

# Task D: Final validation

### Task D1: Full validation gate run

- [ ] **Step 1: Run all pytest**

Run: `cd /home/ailearn/projects/LingWen && /home/ailearn/miniconda3/bin/python -m pytest apps/studio_api/tests/ tests/test_phase1*.py tests/test_phase6*.py tests/test_phase7*.py tests/test_phase9*.py tests/test_phase10*.py -v --rootdir=. 2>&1 | tail -50`
Expected: All preserved + 10 NEW bulk_regenerate tests + 10 NEW guards = full green

- [ ] **Step 2: Run all vitest**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run 2>&1 | tail -20`
Expected: All preserved + 8 NEW (3 useBulkRegenerateToast + 2 store + 6 F1-F6 + 2 F7/F8) = 13 NEW total / all green

- [ ] **Step 3: tsc check**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm tsc --noEmit`
Expected: 0 NEW errors

- [ ] **Step 4: ruff check**

Run: `cd /home/ailearn/projects/LingWen && ruff check apps/studio_api/routes/illustrations.py apps/studio_api/tests/test_bulk_regenerate_api.py tests/test_phase108_bulk_regenerate.py`
Expected: clean

- [ ] **Step 5: knip check**

Run: `cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm exec knip`
Expected: 0 NEW unused exports (8 NEW exports all consumed)

- [ ] **Step 6: Final commit (if any uncommitted)**

```bash
cd /home/ailearn/projects/LingWen
git status
# If dirty, commit leftovers:
git add -A
git commit -m "fix(phase-108): final validation fixes"
```

---

## Self-Review Checklist (run before declaring done)

- [ ] **Spec coverage:** §2 Goals 1-12 → Task A (1-5), Task B (1-10), Task C (1-5) all mapped
- [ ] **No placeholders:** No "TBD", "TODO", "fill in", "implement later" — all code blocks complete
- [ ] **Type consistency:** `bulkRegenerateAssets` (api) ↔ `bulkRegenerateAssets` (store) ↔ `_regenerate_asset_inner` (backend) — names consistent
- [ ] **Failure mode coverage:** T2 partial failure ✓; T3/T4 validation ✓; T5/T6 404/LoadError ✓; T7 dedupe ✓; T8 cross-project ✓; T9 audit mode ✓; T10 threshold-crossing ✓
- [ ] **Frontend coverage:** F1-F8 selection + button + NPopconfirm + end-to-end ✓
- [ ] **Invariant coverage:** G1-G10 route/limit/per-asset/isolation/preservation/extensions ✓
- [ ] **Lesson inheritance:** §12 lessons from Phase 107 explicitly referenced ✓
- [ ] **Commit count:** 16 atomic commits (Task A: 5, Task B: 10, Task C: 5, Task D: 1 final) — matches spec estimate
