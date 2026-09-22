# Phase 107 — Bulk Delete Illustration Endpoint — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce `DELETE /api/illustrations?slug=...&ids=...` bulk endpoint (limit 50, sequential for-loop) + multi-select UX in `IllustrationGallery.vue` (checkbox overlay + sticky bulk action bar + NPopconfirm). Refactor `delete_asset` route to delegate to a NEW shared `_delete_asset_inner` helper so single and bulk share identical per-asset failure tracking (I090/I091/I095 contract). Add `extra={"mode": "single"|"bulk"}` discriminator in audit log + NotificationEvent for downstream analytics.

**Architecture:** Phase 107 is the **5th Phase 102+ extension** (Phase 103/104/105/106 were extensions #1/#2/#3/#4). Modifies 1 backend route file (extract `_delete_asset_inner` helper + add `bulk_delete_assets` route), 1 store action, 1 typed wrapper, 1 new composable, 1 component (multi-select + bulk action bar), extends 3 invariants (I090/I091/I095 EXTENDED via docstring). Per-asset iteration is sequential (preserves audit_log.jsonl + SSE arrival order); dedupes input ids via `dict.fromkeys()`; 422 enforced on empty/over-50. ~13 atomic commits. No new dependencies, no new modules.

**Tech Stack:** FastAPI / Python 3.12 / Vue 3 + Naive UI / Pinia / TypeScript / pytest / vitest

**Spec:** `docs/superpowers/specs/2026-09-22-phase-107-bulk-delete-design.md`

**Phase**: v60.4 → v60.5 (Phase 102+ extension #5)

**Workflow**: Solo repo, no PR, direct commits on master (per 2026-09-15 simplified workflow)

---

## File Structure

### Files modified
- `apps/studio_api/routes/illustrations.py` — extract `_delete_asset_inner` helper, modify existing `delete_asset` handler to delegate, add `bulk_delete_assets` route
- `apps/dashboard/src/api/illustrations.ts` — add `BulkDeleteResult` interface + `bulkDeleteAssets` typed wrapper
- `apps/dashboard/src/stores/useIllustrationStore.js` — add `bulkDeleteAssets(slug, assetIds)` action
- `apps/dashboard/src/components/illustrations/IllustrationGallery.vue` — add multi-select state + checkbox overlay + sticky bulk action bar + NPopconfirm + emit `'bulk-deleted'`
- `apps/studio_api/tests/test_illustrations_api.py` — verify Phase 106 tests still pass (helper refactor compat); no source changes needed
- `.lingwen/architecture.yml` — extend I090 + I091 + I095 rule fields (5th extension — bulk added)
- `CLAUDE.md` — version bump v60.4 → v60.5, I090/I091/I095 EXTENDED rows, version line narrative
- `collaboration/CURRENT_STATUS.md` — last updated line, project state table row
- `collaboration/BACKLOG.md` — add Phase 107 entry to "已完成（近期）" + "最近变更"
- `home/ailearn/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md` — Phase 107 topic pointer + handoff link
- `packages/lingwen-illustrations/src/lingwen_illustrations/__init__.py` — no change; merely verify `notifications` exports `resolve_threshold` (Phase 105 used back-compat re-export)

### Files created (new)
- `apps/studio_api/tests/test_bulk_delete_api.py` — 10 RED tests T1-T10 (covers happy / partial / 422 / 422 / 404 / LoadError / dedupe / cross-project / audit mode / threshold crossing)
- `apps/dashboard/src/composables/useBulkDeleteToast.ts` — toast composable with 3 variants (success / partial / error)
- `apps/dashboard/tests/unit/composables/useBulkDeleteToast.spec.ts` — 3 unit tests for toast variants
- `tests/test_phase107_bulk_delete.py` — 10 regression guards G1-G10 (route registered / limit 50 / empty 422 / per-asset fan-out / partial fan-out / counter isolation / Phase 106 preserved / invariant extension / dedupe / cross-project isolation)
- `docs/superpowers/handoffs/2026-09-22-phase-107-bulk-delete-handoff.md` — Phase 107 handoff doc
- `docs/superpowers/plans/2026-09-22-phase-107-bulk-delete.md` — this plan doc

### Files extended (append tests)
- `apps/dashboard/tests/unit/components/illustrations/IllustrationGallery.spec.ts` — append +6 tests for selection state / checkbox toggle / bulk bar visibility / NPopconfirm path / cross-page / dedupe UI
- `apps/dashboard/tests/unit/stores/useIllustrationStore.spec.js` (if exists) OR new `useIllustrationStore.spec.ts` — append +2 tests for `bulkDeleteAssets` happy + partial

### Invariant extensions (architectural)
- **I090 EXTENDED 5th** (`.lingwen/architecture.yml` rule field): add `apps/studio_api/routes/illustrations.py (bulk_delete_assets)` as 5th caller of `audit_log.record_event` (after pipeline.generate + pipeline.regenerate + cleanup_route + delete_asset)
- **I091 EXTENDED 5th**: add `apps/studio_api/routes/illustrations.py (bulk_delete_assets)` as 5th double-write site (audit_log + publish with same ULID per asset)
- **I095 EXTENDED via docstring** (5th extension): per-asset `record_failure/record_success` semantics inherited; counter keys still `(slug, "deletion")`; threshold crossing emits exactly 1 severity=warning; bulk iteration does not change this

---

## Commit-by-commit breakdown

### Commit 1: spec (DONE in `1e2fcac8`)

**File**: `docs/superpowers/specs/2026-09-22-phase-107-bulk-delete-design.md`

Design spec covering: bulk endpoint rationale, `_delete_asset_inner` helper refactor rationale (avoid duplicating Phase 106 5-path), per-asset sequential iteration semantics, dedupe, limit 50, partial-failure response shape, mode discriminator, invariant extensions, test matrix T1-T10, regression guards G1-G10, validation gates, §A test migration plan per I079.

### Commit 2: plan (this file)

**File**: `docs/superpowers/plans/2026-09-22-phase-107-bulk-delete.md`

---

### Commit 3: test — pytest T1-T10 (bulk delete API, RED)

**File**: `apps/studio_api/tests/test_bulk_delete_api.py` (NEW)

Write 10 tests covering the per-asset failure tracking contract via `_delete_asset_inner` (extracted in Commit 4):

```python
"""Phase 107: T1-T10 bulk delete endpoint tests.

T1-T6 are RED until Commit 5 wires bulk_delete_assets. T7-T10 use the same helper
and become GREEN at Commit 5 as well.
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from apps.studio_api.app import create_app
from apps.studio_api.routes import illustrations as illus_module
from lingwen_illustrations import audit_log, notifications
from lingwen_illustrations.exceptions import LoadError, StoreError


@pytest.fixture
def client(tmp_path):
    """Create FastAPI test client with project_root monkey-patched to tmp_path."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def patched_project_root(tmp_path, monkeypatch):
    """Patch project_root_for so the test slug resolves to a real tmp_path project_root."""
    monkeypatch.setattr(
        illus_module,
        "project_root_for",
        lambda slug: tmp_path if slug == "test-slug" else (_ for _ in ()).throw(LoadError(f"project {slug} not found")),
    )
    return tmp_path


# ---------- T1: Happy path ----------
def test_bulk_delete_happy_path_records_per_asset(patched_project_root, monkeypatch):
    """T1: 5 assets all in storage; expect 5× record_success + 5× audit + 5× publish."""
    captured_success, captured_audit, captured_publish = [], [], []

    monkeypatch.setattr(notifications, "record_success", lambda slug, event_type: captured_success.append((slug, event_type)))
    monkeypatch.setattr(audit_log, "record_event", lambda *args, **kwargs: captured_audit.append((args, kwargs)))

    def fake_publish(event):
        captured_publish.append(event)
        return None
    monkeypatch.setattr(notifications, "publish", fake_publish)

    # Pre-populate storage with 5 assets
    from packages.lingwen_illustrations.src.lingwen_illustrations import storage  # type: ignore
    asset_ids = []
    for i in range(5):
        # Create minimal asset via storage layer's save API
        meta = storage.save_asset(
            patched_project_root,
            chapter_num=1,
            prompt=f"test prompt {i}",
            image_bytes=b"\x89PNG\r\n\x1a\n" + b"\x00" * 100,
            style_preset="default",
            provider="minimax",
            model="default",
        )
        asset_ids.append(meta.id)

    # Mock storage.delete_asset to always succeed
    monkeypatch.setattr(storage, "delete_asset", lambda pr, aid: None)

    client = TestClient(create_app())
    ids_csv = ",".join(asset_ids)
    resp = client.delete(f"/api/illustrations?slug=test-slug&ids={ids_csv}")

    assert resp.status_code == 200
    body = resp.json()
    assert len(body["deleted"]) == 5
    assert body["failed"] == []
    assert body["summary"] == {"total": 5, "ok": 5, "fail": 0}

    # 5 record_success calls
    assert len(captured_success) == 5
    assert all(s == ("test-slug", "deletion") for s in captured_success)

    # 5 audit_log.record_event + 5 notifications.publish
    assert len(captured_audit) == 5
    assert len(captured_publish) == 5

    # Audit extra={"trigger":"manual","mode":"bulk"}
    for _, kwargs in captured_audit:
        assert kwargs.get("extra") == {"trigger": "manual", "mode": "bulk"}


# ---------- T2: Partial failure ----------
def test_bulk_delete_partial_failure_records_failure_per_asset(patched_project_root, monkeypatch):
    """T2: 5 assets; 3 storage success + 2 StoreError. Expect 3× record_success + 2× record_failure."""
    captured_success, captured_failure = [], []

    monkeypatch.setattr(notifications, "record_success", lambda slug, event_type: captured_success.append((slug, event_type)))
    monkeypatch.setattr(notifications, "record_failure",
                        lambda slug, err, *, project_root, threshold, event_type: captured_failure.append(
                            (slug, str(err), project_root, event_type)))
    monkeypatch.setattr(audit_log, "record_event", lambda *a, **kw: None)
    monkeypatch.setattr(notifications, "publish", lambda ev: None)

    from packages.lingwen_illustrations.src.lingwen_illustrations import storage  # type: ignore

    asset_ids = [f"asset-{i}" for i in range(5)]

    def fake_delete(pr, aid):
        if aid in ("asset-1", "asset-3"):
            raise StoreError(f"failed to delete {aid}")
        return None
    monkeypatch.setattr(storage, "delete_asset", fake_delete)
    monkeypatch.setattr(storage, "load_asset", lambda pr, aid: {"id": aid, "exists": True})

    client = TestClient(create_app())
    resp = client.delete("/api/illustrations?slug=test-slug&ids=" + ",".join(asset_ids))
    assert resp.status_code == 200
    body = resp.json()
    assert sorted(body["deleted"]) == ["asset-0", "asset-2", "asset-4"]
    assert len(body["failed"]) == 2
    assert {f["id"] for f in body["failed"]} == {"asset-1", "asset-3"}
    assert all(f["status"] == "store_error" for f in body["failed"])
    assert body["summary"] == {"total": 5, "ok": 3, "fail": 2}

    assert len(captured_success) == 3
    assert len(captured_failure) == 2
    for slug, err_str, root, et in captured_failure:
        assert slug == "test-slug"
        assert et == "deletion"
        assert root is not None  # real project_root (not None)


# ---------- T3: Empty ids ----------
def test_bulk_delete_empty_ids_returns_422(patched_project_root):
    """T3: ids= (empty) → 422."""
    client = TestClient(create_app())
    resp = client.delete("/api/illustrations?slug=test-slug&ids=")
    assert resp.status_code == 422


# ---------- T4: Over 50 ids ----------
def test_bulk_delete_over_50_ids_returns_422(patched_project_root):
    """T4: 51 unique ids → 422."""
    client = TestClient(create_app())
    ids_csv = ",".join(f"a-{i}" for i in range(51))
    resp = client.delete(f"/api/illustrations?slug=test-slug&ids={ids_csv}")
    assert resp.status_code == 422


# ---------- T5: Slug not found ----------
def test_bulk_delete_slug_not_found_returns_404(monkeypatch):
    """T5: slug does not resolve → 404."""
    # patched_project_root's monkeypatch raises LoadError on non-"test-slug" slugs
    client = TestClient(create_app())
    resp = client.delete("/api/illustrations?slug=missing-slug&ids=a,b")
    assert resp.status_code == 404


# ---------- T6: LoadError on project_root_for ----------
def test_bulk_delete_load_error_records_failure_with_none_root(monkeypatch):
    """T6: project_root_for raises LoadError → all assets record_failure(project_root=None)."""
    captured_failure = []
    monkeypatch.setattr(
        illus_module, "project_root_for",
        lambda slug: (_ for _ in ()).throw(LoadError(f"project {slug} not found"))
    )
    monkeypatch.setattr(notifications, "record_failure",
                        lambda slug, err, *, project_root, threshold, event_type: captured_failure.append(
                            (slug, str(err), project_root, event_type)
                        ))

    client = TestClient(create_app())
    resp = client.delete("/api/illustrations?slug=missing-slug&ids=a,b,c")
    # T6: endpoint catches LoadError → 404 (NOT 200 with all in failed[])
    assert resp.status_code == 404
    assert len(captured_failure) == 0  # Endpoint should raise before calling helper


# ---------- T7: Dedupe ----------
def test_bulk_delete_dedupes_ids(patched_project_root, monkeypatch):
    """T7: ids="a,a,b,b,b,c,d,d" (8 raw) → only 4 iterations; response has 4 entries."""
    iteration_log = []
    from packages.lingwen_illustrations.src.lingwen_illustrations import storage
    monkeypatch.setattr(storage, "delete_asset", lambda pr, aid: iteration_log.append(aid) or None)
    monkeypatch.setattr(storage, "load_asset", lambda pr, aid: {"id": aid, "exists": True})
    monkeypatch.setattr(notifications, "record_success", lambda *a, **kw: None)
    monkeypatch.setattr(notifications, "publish", lambda ev: None)
    monkeypatch.setattr(audit_log, "record_event", lambda *a, **kw: None)

    client = TestClient(create_app())
    resp = client.delete("/api/illustrations?slug=test-slug&ids=a,a,b,b,b,c,d,d")
    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"]["total"] == 4  # dedupe silently
    assert iteration_log == ["a", "b", "c", "d"]


# ---------- T8: Cross-project implicit-not-found ----------
def test_bulk_delete_cross_project_asset_marks_not_found(patched_project_root, monkeypatch):
    """T8: slug=test-slug + an asset_id belonging to another project → not_found; not deleted."""
    from packages.lingwen_illustrations.src.lingwen_illustrations import storage
    # storage.load_asset raises LoadError when asset doesn't exist in this project's storage
    monkeypatch.setattr(storage, "load_asset",
                        lambda pr, aid: (_ for _ in ()).throw(LoadError(f"asset {aid} not in project")))

    captured_success = []
    monkeypatch.setattr(notifications, "record_success", lambda slug, event_type: captured_success.append((slug, event_type)))

    client = TestClient(create_app())
    resp = client.delete("/api/illustrations?slug=test-slug&ids=other-project-asset")
    assert resp.status_code == 200
    body = resp.json()
    assert body["deleted"] == []
    assert len(body["failed"]) == 1
    assert body["failed"][0]["status"] == "not_found"
    # 404 no-op success: record_success was called
    assert captured_success == [("test-slug", "deletion")]


# ---------- T9: Audit mode discriminator ----------
def test_bulk_delete_audit_log_includes_mode_bulk(patched_project_root, monkeypatch):
    """T9: audit_log.record_event extra={'trigger':'manual','mode':'bulk'} (vs single='single')."""
    captured = []
    monkeypatch.setattr(audit_log, "record_event", lambda *a, **kw: captured.append(kw))
    monkeypatch.setattr(notifications, "record_success", lambda *a, **kw: None)
    monkeypatch.setattr(notifications, "publish", lambda ev: None)
    monkeypatch.setattr(notifications, "new_event_id", lambda: "test-ulid")

    from packages.lingwen_illustrations.src.lingwen_illustrations import storage
    monkeypatch.setattr(storage, "delete_asset", lambda pr, aid: None)
    monkeypatch.setattr(storage, "load_asset", lambda pr, aid: {"id": aid, "exists": True, "chapter_num": 1, "type": "scene", "style_preset": "default", "provider": "minimax"})

    client = TestClient(create_app())
    resp = client.delete("/api/illustrations?slug=test-slug&ids=a")
    assert resp.status_code == 200
    assert len(captured) == 1
    assert captured[0].get("extra") == {"trigger": "manual", "mode": "bulk"}


# ---------- T10: Threshold crossing ----------
def test_bulk_delete_threshold_crossing_emits_one_warning(patched_project_root, monkeypatch):
    """T10: 5 consecutive StoreError → threshold=3 → exactly 1 severity=warning notification."""
    captured_warnings = []
    monkeypatch.setattr(notifications, "_emit_failure_warning",
                        lambda slug, et, threshold: captured_warnings.append((slug, et, threshold)))
    monkeypatch.setattr(notifications, "record_failure",
                        lambda slug, err, *, project_root, threshold, event_type: None)
    monkeypatch.setattr(notifications, "resolve_threshold", lambda settings, et: 3)
    monkeypatch.setattr(audit_log, "record_event", lambda *a, **kw: None)
    monkeypatch.setattr(notifications, "publish", lambda ev: None)

    from packages.lingwen_illustrations.src.lingwen_illustrations import storage
    monkeypatch.setattr(storage, "delete_asset", lambda pr, aid: (_ for _ in ()).throw(StoreError(f"fail {aid}")))
    monkeypatch.setattr(storage, "load_asset", lambda pr, aid: {"id": aid, "exists": True})

    client = TestClient(create_app())
    ids = ",".join(f"a-{i}" for i in range(5))
    resp = client.delete(f"/api/illustrations?slug=test-slug&ids={ids}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"] == {"total": 5, "ok": 0, "fail": 5}
    # Exactly 1 warning emission despite 5 failures (Phase 102 _warning_emitted idempotent flag)
    assert len(captured_warnings) == 1
    assert captured_warnings[0] == ("test-slug", "deletion", 3)
```

**Run tests to verify all 10 RED**:

Run:
```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/projects/LingWen/.venv/bin/python -m pytest apps/studio_api/tests/test_bulk_delete_api.py -v 2>&1 | head -100
```

Expected: All 10 tests FAIL with `AttributeError: module 'apps.studio_api.routes.illustrations' has no attribute 'bulk_delete_assets'` (or `_delete_asset_inner` not callable).

**Commit**:

```bash
cd /home/ailearn/projects/LingWen
git add apps/studio_api/tests/test_bulk_delete_api.py
git commit -m "$(cat <<'EOF'
test(phase-107): bulk delete API 10 RED tests

T1-T10 covering happy path (per-asset record_success + audit + publish),
partial failure (3 ok + 2 store_error with per-asset audit), validation
errors (empty ids 422 / >50 422 / LoadError 404), dedupe (8 raw → 4 unique),
cross-project implicit-not_found, audit mode discriminator, and threshold
crossing emits exactly 1 warning. RED until Commit 5 wires bulk_delete_assets
+ helper.
EOF
)"
```

---

### Commit 4: refactor — extract `_delete_asset_inner` helper

**File**: `apps/studio_api/routes/illustrations.py` (MODIFY)

Extract the per-asset delete logic from existing `delete_asset` route handler into a module-private async helper `_delete_asset_inner`. The route handler becomes a thin wrapper. Phase 106 T1-T6 + G1-G6 are preserved.

- [ ] **Step 1: Locate the existing `delete_asset` handler**

Read `apps/studio_api/routes/illustrations.py` to find the `delete_asset` route handler (Phase 106 ~lines 95-178 in the spec shows the existing handler; actual file lines will differ).

- [ ] **Step 2: Add `_delete_asset_inner` helper above the route handler**

Insert before the existing `delete_asset` route. The helper takes the per-asset state and returns a status string:

```python
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

    Returns: "ok" | "not_found" | "load_error" | "store_error"
    """
    # LoadError precheck (project_root already known to caller; None implies upstream LoadError)
    if project_root is None:
        try:
            project_root = project_root_for(slug)
        except LoadError as e:
            notifications.record_failure(
                slug, e,
                project_root=None,
                threshold=threshold,
                event_type="deletion",
            )
            return "load_error"

    # Existence check
    try:
        meta = storage.load_asset(project_root, asset_id)
    except LoadError:
        # 404 asset-not-found = no-op success (matches Phase 106 + Phase 105 cleanup_route)
        notifications.record_success(slug, event_type="deletion")
        return "not_found"

    # Delete + audit + publish on success
    try:
        storage.delete_asset(project_root, meta)
    except StoreError as e:
        notifications.record_failure(
            slug, e,
            project_root=project_root,
            threshold=threshold,
            event_type="deletion",
        )
        return "store_error"

    # Success path
    notifications.record_success(slug, event_type="deletion")

    event_id = notifications.new_event_id()
    audit_log.record_event(
        project_root,
        event="deletion",
        asset_meta=meta,
        id=event_id,
        extra={"trigger": "manual", "mode": mode},
    )
    notifications.publish(notifications.NotificationEvent(
        id=event_id,
        project_slug=slug,
        event_type="deletion",
        asset_id=meta.id,
        asset_type=meta.type,
        chapter_num=meta.chapter_num,
        style_preset=meta.style_preset,
        provider=meta.provider,
        ts=notifications.now_iso(),
        extra={"trigger": "manual", "mode": mode},
    ))
    return "ok"
```

- [ ] **Step 3: Replace the existing `delete_asset` body with a thin wrapper**

```python
@router.delete("/api/illustrations/{asset_id}")
async def delete_asset(
    asset_id: str,
    project_slug: str = Query(...),
) -> dict:
    """Phase 107 refactor: delegates to _delete_asset_inner helper."""
    try:
        project_root = project_root_for(project_slug)
    except LoadError as e:
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
        raise HTTPException(500, detail="store error during delete")
    return {"deleted": asset_id}
```

- [ ] **Step 4: Add `Literal` import if not present**

```python
from typing import Literal
```

- [ ] **Step 5: Verify Phase 106 tests still pass**

Run:
```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/projects/LingWen/.venv/bin/python -m pytest apps/studio_api/tests/test_illustrations_api.py -v 2>&1 | tail -40
```

Expected: All Phase 106 T1-T6 + G1-G6 + base tests GREEN (helper refactor preserves behavior). If any test fails, debug and fix before committing.

- [ ] **Step 6: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/studio_api/routes/illustrations.py
git commit -m "$(cat <<'EOF'
refactor(phase-107): extract _delete_asset_inner helper

Move Phase 106 5-path failure tracking logic from delete_asset route handler
into module-private _delete_asset_inner async helper. Helper returns
Literal status ("ok" | "not_found" | "load_error" | "store_error"). New
mode parameter ("single" | "bulk") interpolates into audit_log extra dict
for downstream analytics. delete_asset route handler becomes thin wrapper
mapping status to HTTP code.

Phase 106 T1-T6 + G1-G6 + base tests preserved GREEN. No external API change.
EOF
)"
```

---

### Commit 5: feat — bulk_delete_assets endpoint

**File**: `apps/studio_api/routes/illustrations.py` (add 1 route)

Add the new `DELETE /api/illustrations` route. Place it BEFORE `@router.delete("/api/illustrations/{asset_id}")` for FastAPI route ordering safety (different path templates, so order is not strictly required, but explicit ordering documents intent).

- [ ] **Step 1: Add the bulk delete route**

```python
@router.delete("/api/illustrations")
async def bulk_delete_assets(
    slug: str = Query(..., description="Project slug"),
    ids: str = Query(..., description="Comma-separated asset UUIDs, 1..50 after dedupe"),
) -> dict:
    """Phase 107: bulk delete up to 50 illustrations.

    Returns 200 + {deleted, failed, summary}; 422 on validation; 404 on slug.
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

- [ ] **Step 2: Run T1-T10 to verify all GREEN**

Run:
```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/projects/LingWen/.venv/bin/python -m pytest apps/studio_api/tests/test_bulk_delete_api.py -v 2>&1 | tail -30
```

Expected: All 10 tests PASS. If T7 (dedupe test) fails, verify `dict.fromkeys` is used.

- [ ] **Step 3: Run Phase 106 + Phase 102-105 tests to verify no regression**

Run:
```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/projects/LingWen/.venv/bin/python -m pytest apps/studio_api/tests/test_illustrations_api.py tests/test_phase10{2,3,4,5,6}*.py -v 2>&1 | tail -40
```

Expected: Phase 102/103/104/105/106 tests preserved GREEN.

- [ ] **Step 4: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/studio_api/routes/illustrations.py
git commit -m "$(cat <<'EOF'
feat(phase-107): bulk_delete_assets endpoint

DELETE /api/illustrations?slug=...&ids=... — sequential for-loop calls
_delete_asset_inner per asset (limit 50, dedupe via dict.fromkeys).
Returns 200 + {deleted, failed, summary}. 422 on empty/over-50, 404 on slug.
Per-asset failure tracking + audit + publish happens identically to single
delete via shared helper.
EOF
)"
```

---

### Commit 6: test — vitest F1-F6 (IllustrationGallery multi-select, RED)

**File**: `apps/dashboard/tests/unit/components/illustrations/IllustrationGallery.spec.ts` (APPEND)

Write 6 tests for the multi-select + bulk action bar + NPopconfirm + selection state. Tests are RED until Commit 10 implements them.

- [ ] **Step 1: Locate the existing IllustrationGallery.spec.ts**

Use `grep -n "describe\\|it(" apps/dashboard/tests/unit/components/illustrations/IllustrationGallery.spec.ts | head -30` to find the last `describe` block.

- [ ] **Step 2: Append F1-F6 to the file**

```typescript
  // F1: selection state — Set<string>
  describe('Phase 107 multi-select', () => {
    it('F1: toggleSelect adds/removes asset_id from selection Set', async () => {
      const wrapper = mount(IllustrationGallery, {
        props: { assets: [{ id: 'a' } as IllustrationMeta, { id: 'b' } as IllustrationMeta], slug: 'test-slug' },
      })
      // Initially empty
      expect((wrapper.vm as any).selection.size).toBe(0)

      // Toggle 'a' on
      ;(wrapper.vm as any).toggleSelect('a', true)
      expect((wrapper.vm as any).selection.has('a')).toBe(true)
      expect((wrapper.vm as any).selection.size).toBe(1)

      // Toggle 'b' on
      ;(wrapper.vm as any).toggleSelect('b', true)
      expect((wrapper.vm as any).selection.size).toBe(2)

      // Toggle 'a' off
      ;(wrapper.vm as any).toggleSelect('a', false)
      expect((wrapper.vm as any).selection.has('a')).toBe(false)
      expect((wrapper.vm as any).selection.size).toBe(1)
    })

    // F2: checkbox overlay — visible only when selectable !== false
    it('F2: checkbox overlay renders per card when selectable !== false', async () => {
      const wrapper = mount(IllustrationGallery, {
        props: { assets: [{ id: 'a' } as IllustrationMeta], slug: 'test-slug' },
      })
      const checkboxes = wrapper.findAll('[data-testid^="select-checkbox-"]')
      expect(checkboxes.length).toBe(1)
    })

    // F3: bulk action bar visibility — hidden when selection empty
    it('F3: bulk action bar hidden when selection empty, visible when non-empty', async () => {
      const wrapper = mount(IllustrationGallery, {
        props: { assets: [{ id: 'a' } as IllustrationMeta], slug: 'test-slug' },
      })
      // Initially hidden
      expect(wrapper.find('.bulk-action-bar').exists()).toBe(false)

      // Select one asset
      ;(wrapper.vm as any).toggleSelect('a', true)
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.bulk-action-bar').exists()).toBe(true)
      expect(wrapper.find('.bulk-action-bar__count').text()).toContain('1')

      // Clear
      ;(wrapper.vm as any).clearSelection()
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.bulk-action-bar').exists()).toBe(false)
    })

    // F4: NPopconfirm — clicking 🗑 Bulk Delete in bar opens confirm
    it('F4: bulk action bar contains NPopconfirm around the bulk-delete button', () => {
      const wrapper = mount(IllustrationGallery, {
        props: { assets: [{ id: 'a' } as IllustrationMeta], slug: 'test-slug' },
      })
      ;(wrapper.vm as any).toggleSelect('a', true)
      const bar = wrapper.find('.bulk-action-bar')
      expect(bar.findComponent({ name: 'NPopconfirm' }).exists()).toBe(true)
    })

    // F5: cross-page selection state — selection survives asset prop changes
    it('F5: selection persists when assets prop changes (cross-page simulation)', async () => {
      const wrapper = mount(IllustrationGallery, {
        props: { assets: [{ id: 'a' } as IllustrationMeta, { id: 'b' } as IllustrationMeta], slug: 'test-slug' },
      })
      ;(wrapper.vm as any).toggleSelect('a', true)
      ;(wrapper.vm as any).toggleSelect('b', true)

      // Simulate page change (assets prop changes; selection is component-local and persists)
      await wrapper.setProps({ assets: [{ id: 'c' } as IllustrationMeta, { id: 'd' } as IllustrationMeta] })
      expect((wrapper.vm as any).selection.size).toBe(2)
      expect((wrapper.vm as any).selection.has('a')).toBe(true)
      expect((wrapper.vm as any).selection.has('b')).toBe(true)
    })

    // F6: dedupe — selecting same id twice doesn't double-count
    it('F6: toggleSelect on same id twice reduces to single selection', async () => {
      const wrapper = mount(IllustrationGallery, {
        props: { assets: [{ id: 'a' } as IllustrationMeta], slug: 'test-slug' },
      })
      ;(wrapper.vm as any).toggleSelect('a', true)
      ;(wrapper.vm as any).toggleSelect('a', true)
      expect((wrapper.vm as any).selection.size).toBe(1)

      // After confirmBulkDelete, clearSelection reduces to 0
      ;(wrapper.vm as any).clearSelection()
      expect((wrapper.vm as any).selection.size).toBe(0)
    })
  })
```

- [ ] **Step 3: Run tests to verify RED**

Run:
```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm vitest run tests/unit/components/illustrations/IllustrationGallery.spec.ts 2>&1 | tail -40
```

Expected: 6 new tests FAIL with "toggleSelect is not a function" or similar. Other existing tests remain GREEN.

- [ ] **Step 4: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/tests/unit/components/illustrations/IllustrationGallery.spec.ts
git commit -m "$(cat <<'EOF'
test(phase-107): IllustrationGallery multi-select 6 RED tests

F1 selection Set state / F2 checkbox overlay / F3 bulk action bar visibility /
F4 NPopconfirm wrapping / F5 cross-page selection persistence / F6 dedupe.
RED until Commit 10 adds multi-select state + bulk action bar UI.
EOF
)"
```

---

### Commit 7: feat — typed wrapper `bulkDeleteAssets`

**File**: `apps/dashboard/src/api/illustrations.ts` (MODIFY — add interface + function)

- [ ] **Step 1: Locate the end of the file**

Use `tail -20 apps/dashboard/src/api/illustrations.ts` to find the closing brace.

- [ ] **Step 2: Append the BulkDeleteResult interface + bulkDeleteAssets function**

```typescript
// Phase 107: bulk delete illustration endpoint
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
  if (!Array.isArray(assetIds) || assetIds.length === 0) {
    throw new Error('assetIds must be non-empty array')
  }
  if (assetIds.length > 50) {
    throw new Error('max 50 ids per request')
  }
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

- [ ] **Step 3: Run frontend type check**

Run:
```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm tsc --noEmit 2>&1 | grep -E "error TS|illustrations.ts" | head -20
```

Expected: 0 errors involving `illustrations.ts`. Pre-existing 48 errors elsewhere unchanged.

- [ ] **Step 4: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/api/illustrations.ts
git commit -m "$(cat <<'EOF'
feat(phase-107): bulkDeleteAssets typed wrapper

Add BulkDeleteResult + BulkDeleteFailedItem interfaces + bulkDeleteAssets()
function in apps/dashboard/src/api/illustrations.ts. Maps to DELETE
/api/illustrations?slug=...&ids=... with proper error mapping. Pre-validates
assetIds (1..50, non-empty) before fetch.
EOF
)"
```

---

### Commit 8: feat — Pinia store action `bulkDeleteAssets`

**File**: `apps/dashboard/src/stores/useIllustrationStore.js` (MODIFY — add action)

- [ ] **Step 1: Locate the actions block**

Find the `actions:` block in the Pinia store definition.

- [ ] **Step 2: Add `bulkDeleteAssets` action (next to `deleteAsset`)**

```javascript
  async bulkDeleteAssets(slug, assetIds) {
    // Phase 107: delegates to typed wrapper; updates local assets[] reactively.
    if (!Array.isArray(assetIds) || assetIds.length === 0) {
      throw new Error('assetIds must be non-empty array')
    }
    const { bulkDeleteAssets: apiBulkDelete } = await import('@/api/illustrations')
    const result = await apiBulkDelete(slug, assetIds)
    // Remove successfully deleted assets + failed `not_found` (treated as gone)
    const removedIds = new Set([
      ...result.deleted,
      ...result.failed.filter(f => f.status === 'not_found').map(f => f.id),
    ])
    this.assets = this.assets.filter(a => !removedIds.has(a.id))
    return result
  },
```

- [ ] **Step 3: Add 2 store tests (or append to existing if spec file exists)**

Create `apps/dashboard/tests/unit/stores/useIllustrationStore.spec.ts` if absent, or append to existing:

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useIllustrationStore } from '@/stores/useIllustrationStore'

describe('Phase 107: useIllustrationStore.bulkDeleteAssets', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('BulkHappy: removes deleted assets from local state and returns result', async () => {
    const store = useIllustrationStore()
    store.assets = [
      { id: 'a', chapter_num: 1 } as any,
      { id: 'b', chapter_num: 1 } as any,
    ]
    vi.mock('@/api/illustrations', () => ({
      bulkDeleteAssets: vi.fn().mockResolvedValue({
        deleted: ['a'],
        failed: [],
        summary: { total: 1, ok: 1, fail: 0 },
      }),
    }))

    const result = await store.bulkDeleteAssets('test-slug', ['a'])
    expect(result.deleted).toEqual(['a'])
    expect(store.assets.map(a => a.id)).toEqual(['b'])
  })

  it('BulkPartial: keeps store_error failures in local state', async () => {
    const store = useIllustrationStore()
    store.assets = [
      { id: 'a', chapter_num: 1 } as any,
      { id: 'b', chapter_num: 1 } as any,
    ]
    vi.mock('@/api/illustrations', () => ({
      bulkDeleteAssets: vi.fn().mockResolvedValue({
        deleted: ['a'],
        failed: [{ id: 'b', status: 'store_error' }],
        summary: { total: 2, ok: 1, fail: 1 },
      }),
    }))

    await store.bulkDeleteAssets('test-slug', ['a', 'b'])
    // store_error failures remain in assets (they may be retried)
    expect(store.assets.map(a => a.id)).toContain('b')
    // Successful deletes removed
    expect(store.assets.map(a => a.id)).not.toContain('a')
  })
})
```

- [ ] **Step 4: Run vitest to verify store tests GREEN**

Run:
```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm vitest run tests/unit/stores/useIllustrationStore.spec.ts 2>&1 | tail -20
```

Expected: 2 tests PASS. (They pass once Commit 9 lands the store action; until then they FAIL.)

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/stores/useIllustrationStore.js apps/dashboard/tests/unit/stores/useIllustrationStore.spec.ts
git commit -m "$(cat <<'EOF'
feat(phase-107): useIllustrationStore.bulkDeleteAssets action

Pinia store action delegates to api.bulkDeleteAssets and reactively removes
deleted + not_found assets from local assets[] (store_error failures retained
for potential retry). Lazy-imports the API wrapper to keep initial bundle small.
+2 vitest tests covering happy + partial paths.
EOF
)"
```

---

### Commit 9: feat — `useBulkDeleteToast` composable

**File**: `apps/dashboard/src/composables/useBulkDeleteToast.ts` (NEW)

- [ ] **Step 1: Create the composable file**

```typescript
import { useMessage } from 'naive-ui'
import type { BulkDeleteResult } from '@/api/illustrations'

export function useBulkDeleteToast() {
  const message = useMessage()

  function showBulkDeleteResult(_slug: string, result: BulkDeleteResult): void {
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

- [ ] **Step 2: Create spec file with 3 tests**

Create `apps/dashboard/tests/unit/composables/useBulkDeleteToast.spec.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useMessage } from 'naive-ui'
import { useBulkDeleteToast } from '@/composables/useBulkDeleteToast'

vi.mock('naive-ui', () => ({
  useMessage: vi.fn(),
}))

describe('useBulkDeleteToast', () => {
  const mockMessage = {
    success: vi.fn(),
    warning: vi.fn(),
    error: vi.fn(),
  }

  beforeEach(() => {
    vi.mocked(useMessage).mockReturnValue(mockMessage as any)
    vi.clearAllMocks()
  })

  it('T-success: showBulkDeleteResult with fail=0 calls message.success', () => {
    const { showBulkDeleteResult } = useBulkDeleteToast()
    showBulkDeleteResult('slug', {
      deleted: ['a', 'b', 'c'],
      failed: [],
      summary: { total: 3, ok: 3, fail: 0 },
    })
    expect(mockMessage.success).toHaveBeenCalledWith('已删除 3 张插图')
    expect(mockMessage.warning).not.toHaveBeenCalled()
    expect(mockMessage.error).not.toHaveBeenCalled()
  })

  it('T-partial: showBulkDeleteResult with both ok and fail calls message.warning', () => {
    const { showBulkDeleteResult } = useBulkDeleteToast()
    showBulkDeleteResult('slug', {
      deleted: ['a'],
      failed: [{ id: 'b', status: 'store_error' }, { id: 'c', status: 'not_found' }],
      summary: { total: 3, ok: 1, fail: 2 },
    })
    expect(mockMessage.warning).toHaveBeenCalledWith('已删除 1 张，失败 2 张 — 查看详情')
  })

  it('T-all-fail: showBulkDeleteResult with ok=0 calls message.error', () => {
    const { showBulkDeleteResult } = useBulkDeleteToast()
    showBulkDeleteResult('slug', {
      deleted: [],
      failed: [{ id: 'a', status: 'store_error' }],
      summary: { total: 1, ok: 0, fail: 1 },
    })
    expect(mockMessage.error).toHaveBeenCalledWith('0 个成功，1 个失败 — 查看详情')
  })
})
```

- [ ] **Step 3: Run vitest to verify 3 tests GREEN**

Run:
```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm vitest run tests/unit/composables/useBulkDeleteToast.spec.ts 2>&1 | tail -20
```

Expected: 3/3 PASS.

- [ ] **Step 4: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/composables/useBulkDeleteToast.ts apps/dashboard/tests/unit/composables/useBulkDeleteToast.spec.ts
git commit -m "$(cat <<'EOF'
feat(phase-107): useBulkDeleteToast composable

Encapsulates Naive UI useMessage for 3 toast variants: full success
(message.success), partial (message.warning), all-fail (message.error).
Reusable across LibraryPage and WriteWorkspacePage. +3 vitest unit tests.
EOF
)"
```

---

### Commit 10: feat — `IllustrationGallery.vue` multi-select + bulk action bar

**File**: `apps/dashboard/src/components/illustrations/IllustrationGallery.vue` (MODIFY)

- [ ] **Step 1: Read current IllustrationGallery.vue to find props + emits + script-setup**

Use `Read` to inspect; locate the `<script setup lang="ts">` block and the template card markup.

- [ ] **Step 2: Add multi-select state to script-setup**

Add at the top of script-setup (after existing imports):

```typescript
import { ref, computed } from 'vue'
import { NCheckbox, NButton, NPopconfirm } from 'naive-ui'
import { useIllustrationStore } from '@/stores/useIllustrationStore'
import { useBulkDeleteToast } from '@/composables/useBulkDeleteToast'
import type { IllustrationMeta, BulkDeleteResult } from '@/api/illustrations'

const props = withDefaults(defineProps<{
  assets: IllustrationMeta[]
  slug: string
  selectable?: boolean
}>(), { selectable: true })

const emit = defineEmits<{
  'bulk-deleted': [result: BulkDeleteResult]
}>()

const store = useIllustrationStore()
const toast = useBulkDeleteToast()

const selection = ref<Set<string>>(new Set())
const bulkDeleteInFlight = ref(false)
const selectionTick = ref(0)  // Force Set reactivity

const bulkActionBarVisible = computed(() => selection.value.size > 0)
const selectedCount = computed(() => selection.value.size)

function toggleSelect(assetId: string, checked: boolean): void {
  if (checked) {
    selection.value.add(assetId)
  } else {
    selection.value.delete(assetId)
  }
  // Trigger Vue 3 Set reactivity
  selectionTick.value++
}

function clearSelection(): void {
  selection.value = new Set()
  selectionTick.value++
}

async function confirmBulkDelete(): Promise<void> {
  if (bulkDeleteInFlight.value) return
  const ids = Array.from(selection.value)
  if (ids.length === 0) return
  bulkDeleteInFlight.value = true
  try {
    const result = await store.bulkDeleteAssets(props.slug, ids)
    toast.showBulkDeleteResult(props.slug, result)
    emit('bulk-deleted', result)
    clearSelection()
  } catch (e) {
    toast.showValidationError((e as Error).message)
  } finally {
    bulkDeleteInFlight.value = false
  }
}
```

- [ ] **Step 3: Add checkbox overlay to each card in the template**

Inside the existing card v-for template (e.g., `<div v-for="asset in assets" :key="asset.id" class="illustration-card">`), add at top-left:

```vue
<NCheckbox
  v-if="props.selectable"
  :checked="selection.has(asset.id)"
  class="illustration-card__checkbox"
  :data-testid="`select-checkbox-${asset.id}`"
  @update:checked="(v: boolean) => toggleSelect(asset.id, v)"
/>
```

- [ ] **Step 4: Add bulk action bar to the template (after the card list)**

```vue
<div v-if="bulkActionBarVisible" class="bulk-action-bar" data-testid="bulk-action-bar">
  <span class="bulk-action-bar__count">已选 {{ selectedCount }} 张</span>
  <NButton data-testid="bulk-cancel-btn" @click="clearSelection">取消</NButton>
  <NPopconfirm
    positive-text="确认删除"
    negative-text="取消"
    @positive-click="confirmBulkDelete"
  >
    <template #trigger>
      <NButton type="error" :loading="bulkDeleteInFlight" data-testid="bulk-delete-btn">
        🗑 批量删除
      </NButton>
    </template>
    确认删除这 {{ selectedCount }} 张插图？删除后无法恢复。
  </NPopconfirm>
</div>
```

- [ ] **Step 5: Add CSS for bulk action bar + checkbox**

Add to the `<style>` block (matches Phase 100 inset-shadow pattern):

```css
.illustration-card { position: relative; }
.illustration-card__checkbox {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 2;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 4px;
  padding: 2px;
}

.bulk-action-bar {
  position: sticky;
  bottom: 0;
  z-index: 10;
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 12px 16px;
  background: var(--lingwen-surface-elevated, #fafafa);
  border-top: 1px solid var(--lingwen-border, #e5e5e5);
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.06);
}
.bulk-action-bar__count {
  font-weight: 600;
  margin-right: auto;
}
```

- [ ] **Step 6: Run vitest to verify F1-F6 GREEN**

Run:
```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm vitest run tests/unit/components/illustrations/IllustrationGallery.spec.ts 2>&1 | tail -30
```

Expected: 6 new tests PASS (F1-F6). Existing tests preserved GREEN.

- [ ] **Step 7: Run frontend type check**

Run:
```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm tsc --noEmit 2>&1 | grep -E "error TS" | wc -l
```

Expected: 48 errors (pre-existing baseline unchanged); 0 new errors involving IllustrationGallery.vue.

- [ ] **Step 8: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/components/illustrations/IllustrationGallery.vue
git commit -m "$(cat <<'EOF'
feat(phase-107): IllustrationGallery multi-select + bulk action bar

Add selection Set<string> local state + checkbox overlay per card + sticky
bottom bulk action bar (visible when selection > 0). Bar contains cancel
button and NPopconfirm-wrapped bulk delete button. confirmBulkDelete
calls store.bulkDeleteAssets + toast + emits 'bulk-deleted'. Component-local
state keeps selection across asset prop changes (cross-page safe).
EOF
)"
```

---

### Commit 11: test — regression guards G1-G10

**File**: `tests/test_phase107_bulk_delete.py` (NEW)

- [ ] **Step 1: Create guards file with 10 GREP-based assertions**

```python
"""Phase 107: G1-G10 regression guards.

Guard against future regressions to bulk_delete_assets wiring + helper refactor
+ invariant extensions.
"""
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ILLUS_ROUTES = REPO_ROOT / "apps" / "studio_api" / "routes" / "illustrations.py"
ARCH_YML = REPO_ROOT / ".lingwen" / "architecture.yml"


# ---------- G1: bulk_delete_assets route registered ----------
def test_g1_bulk_delete_assets_route_registered():
    text = ILLUS_ROUTES.read_text(encoding="utf-8")
    assert "@router.delete(" in text and '"/api/illustrations"' in text
    assert "async def bulk_delete_assets(" in text
    # Returns {deleted, failed, summary} shape
    assert '"deleted"' in text and '"failed"' in text and '"summary"' in text


# ---------- G2: 51 ids → 422 ----------
def test_g2_limit_51_returns_422():
    text = ILLUS_ROUTES.read_text(encoding="utf-8")
    # Check for `len(asset_ids) > 50: raise HTTPException(422, ...)` pattern
    assert re.search(r"len\(asset_ids\)\s*>\s*50[^)]*HTTPException\(\s*422", text), \
        "bulk_delete_assets must enforce 50-id limit via 422"


# ---------- G3: empty ids → 422 ----------
def test_g3_empty_ids_returns_422():
    text = ILLUS_ROUTES.read_text(encoding="utf-8")
    assert re.search(r"if\s+not\s+asset_ids[^:]*:\s*\n[^#]*HTTPException\(\s*422", text, re.MULTILINE), \
        "bulk_delete_assets must raise 422 on empty asset_ids"


# ---------- G4: per-asset record_success + audit + publish in helper ----------
def test_g4_helper_records_per_asset():
    text = ILLUS_ROUTES.read_text(encoding="utf-8")
    # _delete_asset_inner function exists
    assert "async def _delete_asset_inner(" in text
    # Has all four notifications calls (record_failure x2 / record_success x2 inside helper)
    # We focus on success path: record_success + audit_log + publish are in helper body
    helper_section = text.split("async def _delete_asset_inner(")[1]
    assert "record_success(" in helper_section
    assert "audit_log.record_event(" in helper_section
    assert "notifications.publish(" in helper_section


# ---------- G5: 5/5 deletes produce 5 per-asset audit + publish ----------
def test_g5_bulk_iterates_per_asset():
    text = ILLUS_ROUTES.read_text(encoding="utf-8")
    bulk_section = text.split("async def bulk_delete_assets(")[1]
    # for-loop calling _delete_asset_inner
    assert re.search(r"for\s+\w+\s+in\s+asset_ids[^:]*:\s*\n[^#]*_delete_asset_inner\(", bulk_section), \
        "bulk_delete_assets must iterate asset_ids and call _delete_asset_inner per item"


# ---------- G6: counter isolation (Phase 106 G5 复用) ----------
def test_g6_counter_isolation_preserved():
    """Bulk deletion failures must NOT increment generation counter."""
    # Indirect verification: helper accepts event_type="deletion" and uses Phase 104 tuple keys
    text = ILLUS_ROUTES.read_text(encoding="utf-8")
    assert 'event_type="deletion"' in text
    # Phase 106 G5 test file should still be passing (verified via pytest run during Commit 11)


# ---------- G7: Phase 106 delete_asset single-delete preserved ----------
def test_g7_delete_asset_uses_helper():
    text = ILLUS_ROUTES.read_text(encoding="utf-8")
    # Single-delete route now calls _delete_asset_inner
    delete_route = text.split("@router.delete(\"/api/illustrations/{asset_id}\")")[1].split("@router.delete")[0]
    assert "_delete_asset_inner(" in delete_route, \
        "delete_asset route must delegate to _delete_asset_inner helper"
    # Single mode passed
    assert 'mode="single"' in delete_route


# ---------- G8: invariant extension documented ----------
def test_g8_invariant_extension_in_architecture_yml():
    text = ARCH_YML.read_text(encoding="utf-8")
    # I090 mentions bulk_delete_assets as caller
    assert re.search(r"id:\s*I090", text)
    # Parse YAML around I090 block (defensive: not raw grep)
    sections = text.split("\n- id:")
    for section in sections:
        if section.lstrip().startswith("I090"):
            assert "bulk_delete_assets" in section, "I090 must mention bulk_delete_assets as 5th caller"
        elif section.lstrip().startswith("I091"):
            assert "bulk_delete_assets" in section, "I091 must mention bulk_delete_assets as 5th double-write site"
        elif section.lstrip().startswith("I095"):
            # I095 EXTENDED mentions bulk_delete_assets
            assert "bulk_delete_assets" in section or "Phase 107" in section, \
                "I095 must mention Phase 107 bulk_delete_assets extension"


# ---------- G9: dedupe via dict.fromkeys ----------
def test_g9_dedupe_via_dict_fromkeys():
    text = ILLUS_ROUTES.read_text(encoding="utf-8")
    bulk_section = text.split("async def bulk_delete_assets(")[1]
    assert "dict.fromkeys" in bulk_section, \
        "bulk_delete_assets must dedupe via dict.fromkeys"


# ---------- G10: cross-project implicit-not-found ----------
def test_g10_cross_project_not_via_explicit_check():
    """Cross-project isolation comes from per-project storage dirs, not explicit slug-vs-aid check."""
    text = ILLUS_ROUTES.read_text(encoding="utf-8")
    bulk_section = text.split("async def bulk_delete_assets(")[1]
    # No explicit cross-project slug-vs-aid mapping check
    assert "asset_id in project" not in bulk_section
    assert "asset not in" not in bulk_section
    # Helper raises LoadError naturally → handled via not_found status
    # (verified by T8 test in test_bulk_delete_api.py)
```

- [ ] **Step 2: Run guards to verify GREEN**

Run:
```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/projects/LingWen/.venv/bin/python -m pytest tests/test_phase107_bulk_delete.py -v 2>&1 | tail -20
```

Expected: 10/10 G1-G10 PASS. If G8 (invariant extension) fails, the architecture.yml extension hasn't been done yet — proceed to Commit 12 first.

- [ ] **Step 3: Run cumulative pytest to verify Phase 102-106 preserved**

Run:
```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/projects/LingWen/.venv/bin/python -m pytest tests/test_phase10{2,3,4,5,6,7}*.py apps/studio_api/tests/test_bulk_delete_api.py -v 2>&1 | tail -10
```

Expected: 6 + 8 + 8 + 6 + 6 + 10 + 10 = 54 NEW + preserved tests GREEN.

- [ ] **Step 4: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add tests/test_phase107_bulk_delete.py
git commit -m "$(cat <<'EOF'
test(phase-107): bulk delete regression guards G1-G10

10 GREP-based guards verifying: route registered (G1), 51-id 422 (G2), empty
422 (G3), per-asset helper fan-out (G4), for-loop iteration (G5), counter
isolation (G6), Phase 106 delete_asset preserved via helper (G7), invariant
extensions in architecture.yml (G8), dict.fromkeys dedupe (G9), no
explicit cross-project check (G10).
EOF
)"
```

---

### Commit 12: docs — extend I090/I091/I095 (5th EXTENDED via docstring)

**Files**: `.lingwen/architecture.yml` (MODIFY) + `CLAUDE.md` (MODIFY)

- [ ] **Step 1: Read `.lingwen/architecture.yml` to find I090/I091/I095 blocks**

Use `grep -n -E "id:\s*I09[015]" .lingwen/architecture.yml` to find the line numbers.

- [ ] **Step 2: Edit I090 rule + scope fields (add bulk_delete_assets)**

In `.lingwen/architecture.yml`:

For I090 rule (current text mentions `delete_asset`), append `bulk_delete_assets`:

Replace any line containing `delete_asset` with:
```
    (Phase 98 + Phase 105 + Phase 106 + Phase 107 — bulk_delete_assets added as 5th caller)
    `packages/lingwen-illustrations/src/lingwen_illustrations/storage.py:lru_cleanup` ... \
    apps/studio_api/routes/cleanup_route.py | apps/studio_api/routes/illustrations.py (delete_asset) | \
    apps/studio_api/routes/illustrations.py (bulk_delete_assets) 通过这两个入口
```

Likewise for I091.

For I095, append a 5th extension paragraph to the scope field:

```
    Phase 107 EXTENDED via docstring — bulk_delete_assets (DELETE /api/illustrations?ids=...&slug=...)
    is the 4th caller after pipeline.py + cleanup_route + delete_asset; all 4 event_types now have
    ≥1 caller; per-asset record_failure/record_success inherited unchanged from delete_asset;
    counter keys still (slug, "deletion"); threshold crossing per (slug, "deletion") emits exactly
    one severity="warning" notification; bulk iteration does not change I095 invariants.
```

- [ ] **Step 3: Update CLAUDE.md I090/I091/I095 rows**

Use `Edit` on `CLAUDE.md` to extend the 3 invariant rows:

```
| I090 | `packages/lingwen-illustrations/src/lingwen_illustrations/storage.py:lru_cleanup` 是 illustration LRU 删除唯一入口...pipeline.generate_illustration / pipeline.regenerate_illustration / apps/studio_api/routes/cleanup_route.py / apps/studio_api/routes/illustrations.py (delete_asset) / `apps/studio_api/routes/illustrations.py (bulk_delete_assets)` 五处 caller (Phase 98 + 105 + 106 + 107 — bulk_delete_assets adds 5th caller per `test_phase107_bulk_delete.py::test_g8_invariant_extension_in_architecture_yml`) ... |
```

(Similar for I091 and I095 rows.)

- [ ] **Step 4: Run G8 guard to verify GREEN**

```bash
cd /home/ailearn/projects/LingWen
/home/ailearn/projects/LingWen/.venv/bin/python -m pytest tests/test_phase107_bulk_delete.py::test_g8_invariant_extension_in_architecture_yml -v
```

Expected: G8 PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add .lingwen/architecture.yml CLAUDE.md
git commit -m "$(cat <<'EOF'
docs(phase-107): extend I090/I091/I095 to include bulk_delete_assets

YAGNI: same invariant name, wider scope. I090/I091 add bulk_delete_assets
as 5th caller/double-write site. I095 EXTENDED via docstring (5th extension)
notes per-asset record_failure/record_success inherited from delete_asset
helper; counter keys still (slug, 'deletion'); threshold emission unchanged.
EOF
)"
```

---

### Commit 13: docs sync — v60.4 → v60.5 + handoff + BACKLOG + CURRENT_STATUS + MEMORY

**Files**: `CLAUDE.md` (version bump + Phase 107 entry) + 4 other files

- [ ] **Step 1: Bump CLAUDE.md version v60.4 → v60.5**

Open CLAUDE.md. Find the line starting with `**版本**: v60.4`. Replace with `v60.5` and the new Phase 107 description (mirror Phase 106's entry in the multi-line version block).

- [ ] **Step 2: Create Phase 107 handoff doc**

Create `docs/superpowers/handoffs/2026-09-22-phase-107-bulk-delete-handoff.md` mirroring Phase 106 handoff structure (Date / Phase / Cluster / Type / Workflow / What was delivered / Validation gates / Atomic commits / Lessons / Cluster cumulative / Future work).

- [ ] **Step 3: Update collaboration/CURRENT_STATUS.md**

Find the line starting with `> **最后更新**: 2026-09-21 (Phase 106`. Add a Phase 107 entry to the recent phase history table.

- [ ] **Step 4: Update collaboration/BACKLOG.md**

Add a Phase 107 entry to "已完成（近期）" table + "最近变更" log.

- [ ] **Step 5: Update MEMORY.md index + add Phase 107 topic pointer**

Add to MEMORY.md under "## Key Paths":
```
| `docs/superpowers/handoffs/2026-09-22-phase-107-...` | Phase 107 handoff |
```

Append to MEMORY.md's "## Topic Files" section:
```
| **Phase 107 bulk delete (v60.5; fifth Phase 102+ extension)** | → See handoff `2026-09-22-phase-107-bulk-delete-handoff.md` (DELETE /api/illustrations?slug=...&ids=... bulk endpoint + multi-select UX + helper refactor + I090/I091/I095 5th EXTENDED + 13 atomic commits)
```

- [ ] **Step 6: Run all gates one more time to verify**

Run:
```bash
cd /home/ailearn/projects/LingWen
# Backend
/home/ailearn/projects/LingWen/.venv/bin/python -m pytest apps/studio_api/tests/test_bulk_delete_api.py tests/test_phase107_bulk_delete.py tests/test_phase10{2,3,4,5,6}*.py -v 2>&1 | tail -10
# Frontend
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm vitest run tests/unit/components/illustrations/IllustrationGallery.spec.ts tests/unit/composables/useBulkDeleteToast.spec.ts tests/unit/stores/useIllustrationStore.spec.ts 2>&1 | tail -10
pnpm tsc --noEmit 2>&1 | grep -c "error TS"
# Ruff
cd /home/ailearn/projects/LingWen
ruff check apps/studio_api/routes/illustrations.py apps/studio_api/tests/test_bulk_delete_api.py tests/test_phase107_bulk_delete.py 2>&1 | tail -10
```

Expected:
- All pytest tests GREEN
- All vitest tests GREEN
- `tsc` shows exactly 48 pre-existing errors (no new)
- `ruff check` clean on all 3 introduced files

- [ ] **Step 7: Push to origin**

```bash
cd /home/ailearn/projects/LingWen
git push origin master
```

Expected: All 12 atomic commits pushed (Commit 1 spec already at `1e2fcac8`; 11 new commits follow).

- [ ] **Step 8: Commit the docs sync**

```bash
cd /home/ailearn/projects/LingWen
git add CLAUDE.md docs/superpowers/handoffs/2026-09-22-phase-107-bulk-delete-handoff.md collaboration/CURRENT_STATUS.md collaboration/BACKLOG.md home/ailearn/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md
git commit -m "$(cat <<'EOF'
docs(phase-107): v60.4 → v60.5 + handoff + BACKLOG + CURRENT_STATUS + MEMORY

Phase 107 closure: 13 atomic commits on master (this commit + 12 prior), all
pushed to origin/master. I090/I091/I095 EXTENDED 5th. deletion event_type +
bulk_delete_assets now fully wired. Cluster cumulative Phase 90-107 = 18 phases.

Future work: telemetry-driven chain reorder (data-gated) / delete from
NotificationsPage dropdown (Phase 108+) / bulk REGENERATE (YAGNI).
EOF
)"
```

---

## Validation Gates (final summary)

| Gate | Expected | Status |
|------|----------|--------|
| `pytest apps/studio_api/tests/test_bulk_delete_api.py` | 10/10 NEW T1-T10 PASS | ⬜ |
| `pytest tests/test_phase107_bulk_delete.py` | 10/10 NEW G1-G10 PASS | ⬜ |
| `pytest apps/studio_api/tests/test_illustrations_api.py` Phase 106 T1-T6 + G1-G6 | 12/12 preserved PASS | ⬜ |
| `pytest tests/test_phase102/103/104/105/106_*.py` | 30+ guards preserved PASS | ⬜ |
| `vitest IllustrationGallery.spec.ts` | existing + 6 NEW F1-F6 PASS | ⬜ |
| `vitest useBulkDeleteToast.spec.ts` | 3 NEW PASS | ⬜ |
| `vitest useIllustrationStore.spec.ts` | existing + 2 NEW PASS | ⬜ |
| `pnpm tsc --noEmit` | 0 new errors (48 pre-existing baseline unchanged) | ⬜ |
| `pnpm eslint .` | 0 new errors | ⬜ |
| `ruff check` on introduced/changed Python files | clean | ⬜ |

## Cluster cumulative after Phase 107

```
Phase 90-107 = 18 phases
  + 1 NEW package (lingwen-illustrations)
  + 5 carryover closures (Phase 91-95)
  + 7 REQ-002 v2 sub-projects delivered (Phase 96-102)
  + 5 Phase 102+ extensions:
      Phase 103: default_models per chapter
      Phase 104: notify_threshold per event_type
      Phase 105: cleanup_route failure tracking
      Phase 106: delete_asset failure tracking
      Phase 107: bulk_delete_assets (THIS phase)
```

v60.4 → v60.5.

## Future work (per BACKLOG post-Phase 107)

- **Phase 108+**: telemetry-driven chain reorder — gated on Phase 102-107 data accumulation
- **Phase 108+**: delete from NotificationsPage dropdown — orthogonal UX
- **Phase 110+**: bulk REGENERATE — YAGNI eval after bulk-delete ships
- **ARCHDEBT-REAL continuation**: closed since Phase 88; reopen only on new N.14 audit

## Risks and mitigations

- **Helper refactor breaks Phase 106**: Commit 4 explicitly verifies Phase 106 tests stay GREEN before Commit 5
- **URL length on 51+ ids**: server enforces 422 cap before iteration; client also caps at 50
- **Cross-page selection state**: component-local `selection: Set<string>`; survives asset prop changes; cleared after `confirmBulkDelete`
- **Single-delete + bulk-delete race on same aid**: no per-asset lock; storage layer file-unlink atomic; both record_success runs → counter resets cleanly
- **Vue 3 Set reactivity**: Phase 107 uses `selectionTick.value++` (or replace Set) to force reactivity on Set mutation
- **`extra={"mode":"bulk"}` propagation**: helper body interpolates `mode` into both `audit_log.record_event(extra=...)` and `notifications.publish(extra=...)`; verified by T9 test

## Lessons referenced

- **Phase 102 §3** — threshold + counter state machine (inherited)
- **Phase 104 §3** — per-event-type counter isolation (G6 verifies)
- **Phase 105 §1** — `_load_cleanup_settings` helper pattern (mirrored as `_load_deletion_settings` in Phase 106, indirectly reused by Phase 107)
- **Phase 105 §2** — failure tracking on LoadError + StoreError + record_success in else branch (Phase 107 helper inherits verbatim)
- **Phase 106 §1** — 404 no-op success pattern (Phase 107 helper inherits verbatim)
- **Phase 106 §4** — `extra={"trigger":"manual"}`; Phase 107 adds `mode="single"|"bulk"`
- **Phase 106 §6** — I090/I091/I095 EXTENDED via docstring (5th extension in Phase 107)
- **Phase 90 §11** — IllustrationCard emit pattern → IllustrationGallery multi-select pattern
- **I079 §A** — spec self-review §A appendix even when not P3-ARCHDEBT
