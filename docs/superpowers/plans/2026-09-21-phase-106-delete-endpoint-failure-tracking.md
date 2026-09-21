# Phase 106 — Delete Illustration Endpoint Failure Tracking — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the existing `DELETE /api/illustrations/{asset_id}` endpoint (Phase 90) into notifications failure tracking (`record_failure`/`record_success` with `event_type="deletion"`) + audit_log/publish double-write (I091) + Naive UI `<NPopconfirm>` on `IllustrationCard.vue`, completing I090/I091/I095 coverage for all 4 event_types.

**Architecture:** Phase 106 is a small additive extension following the Phase 102+ extension pattern (Phase 103/104/105 were extensions #1/#2/#3). Modifies 1 backend route file (add `_load_deletion_settings` helper + wire failure tracking + double-write into existing `delete_asset` handler), 1 frontend component (wrap 🗑 button in `<NPopconfirm>`), extends 3 invariants via docstring (I090/I091/I095 EXTENDED). ~9 atomic commits. No new dependencies, no new modules.

**Tech Stack:** FastAPI / Python 3.12 / Vue 3 + Naive UI / Pinia / TypeScript / pytest / vitest

**Spec:** `docs/superpowers/specs/2026-09-21-phase-106-delete-endpoint-failure-tracking-design.md`

**Phase**: v60.3 → v60.4 (Phase 102+ extension #4)

**Workflow**: Solo repo, no PR, direct commits on master (per 2026-09-15 simplified workflow)

---

## File Structure

### Files modified
- `apps/studio_api/routes/illustrations.py` — add `_load_deletion_settings` helper, add `import yaml` + `from lingwen_illustrations import audit_log, notifications` at module top, modify `delete_asset` handler at line 336
- `apps/dashboard/src/components/illustrations/IllustrationCard.vue` — wrap 🗑 button (line 34-40) in `<NPopconfirm>` (Naive UI)
- `.lingwen/architecture.yml` — extend I090 + I091 rule fields (add DELETE route as caller/double-write site), extend I095 rule field (4th extension mentions deletion event_type)
- `CLAUDE.md` — version bump v60.3 → v60.4, I090/I091/I095 EXTENDED rows, version line narrative
- `collaboration/CURRENT_STATUS.md` — last updated line, project state table row
- `collaboration/BACKLOG.md` — add Phase 106 entry to "已完成（近期）" + "最近变更"
- `docs/superpowers/handoffs/2026-09-21-phase-106-delete-endpoint-failure-tracking-handoff.md` — NEW handoff doc
- `home/ailearn/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md` — Phase 106 topic pointer

### Files extended (append tests)
- `apps/studio_api/tests/test_illustrations_api.py` — append T1-T6 (deletion failure path tests) after existing `test_delete_asset` (line 167)
- `apps/dashboard/tests/unit/components/illustrations/IllustrationCard.spec.ts` — append F1-F4 (NPopconfirm tests)

### Files created (new)
- `packages/lingwen-illustrations/tests/test_phase106_deletion_isolation.py` — T7-T9 (counter isolation + helper resilience)
- `tests/test_phase106_delete_endpoint_failure_tracking.py` — G1-G6 (regression guards)

### Invariant extensions
- I090 rule field: add `apps/studio_api/routes/illustrations.py (delete_asset)` as 4th caller
- I091 rule field: add `apps/studio_api/routes/illustrations.py (delete_asset)` as 4th double-write site
- I095 rule field: 4th extension via docstring only — `deletion` event_type now has ≥1 caller; counter resets via `record_success` in else branch + on 404 asset-not-found path

---

## Commit-by-commit breakdown

### Commit 1: spec (DONE in `f459ddad`)

**File**: `docs/superpowers/specs/2026-09-21-phase-106-delete-endpoint-failure-tracking-design.md`

Design spec covering: helper rationale, DELETE endpoint failure tracking semantics (5-path contract table), double-write pattern, Naive UI NPopconfirm UX, counter isolation, test matrix T1-T9, regression guards G1-G6, validation gates, §A test migration plan per I079.

### Commit 2: plan (this file)

**File**: `docs/superpowers/plans/2026-09-21-phase-106-delete-endpoint-failure-tracking.md`

### Commit 3: test — pytest T1-T6 (deletion failure paths, RED)

**File**: `apps/studio_api/tests/test_illustrations_api.py` (append after line 167's `test_delete_asset`)

Write 6 tests covering the 5-path failure tracking contract + threshold trigger:

```python
def test_delete_asset_load_error_records_failure_with_none_root(monkeypatch, tmp_path):
    """T1: LoadError on project_root_for → record_failure(event_type="deletion", project_root=None)."""
    from apps.studio_api.routes import cleanup_route as _cr  # noqa: F401  (load context)
    from apps.studio_api.routes.illustrations import _build_app  # if exists; else use create_app fixture
    from lingwen_illustrations import notifications
    from lingwen_illustrations.exceptions import LoadError

    captured = []
    monkeypatch.setattr(notifications, "record_failure",
                        lambda slug, err, *, project_root, threshold, event_type: captured.append(
                            (slug, str(err), project_root, threshold, event_type)
                        ))

    from apps.studio_api.routes._project_helpers import project_root_for
    monkeypatch.setattr("apps.studio_api.routes.illustrations.project_root_for",
                        lambda slug: (_ for _ in ()).throw(LoadError(f"project {slug} not found")))

    # Phase 106: use the delete_asset route via TestClient
    from apps.studio_api.app import create_app
    app = create_app()
    from fastapi.testclient import TestClient
    client = TestClient(app)

    resp = client.delete("/api/illustrations/asset-x?project_slug=missing-slug")
    assert resp.status_code == 404
    assert len(captured) == 1
    slug, err_str, root, threshold, et = captured[0]
    assert slug == "missing-slug"
    assert root is None  # Phase 106: LoadError path → project_root=None
    assert et == "deletion"


def test_delete_asset_not_found_records_success(monkeypatch, tmp_path):
    """T2: 404 asset-not-found → record_success(event_type="deletion") (no-op success)."""
    from lingwen_illustrations import notifications
    captured_success = []
    captured_failure = []
    monkeypatch.setattr(notifications, "record_success",
                        lambda slug, event_type: captured_success.append((slug, event_type)))
    monkeypatch.setattr(notifications, "record_failure",
                        lambda *args, **kwargs: captured_failure.append((args, kwargs)))

    from apps.studio_api.routes._project_helpers import project_root_for
    monkeypatch.setattr("apps.studio_api.routes.illustrations.project_root_for",
                        lambda slug: tmp_path)  # valid project_root, but no asset matches

    from apps.studio_api.app import create_app
    from fastapi.testclient import TestClient
    client = TestClient(create_app())

    resp = client.delete("/api/illustrations/nonexistent-id?project_slug=test-slug")
    assert resp.status_code == 404
    assert len(captured_success) == 1
    assert captured_success[0] == ("test-slug", "deletion")
    assert len(captured_failure) == 0  # Phase 106: NOT a failure


def test_delete_asset_success_records_success_and_publishes(monkeypatch, tmp_path):
    """T3: Successful delete → record_success + audit_log.record_event + notifications.publish."""
    from lingwen_illustrations import audit_log, notifications
    captured_success = []
    captured_publish = []
    captured_audit = []
    monkeypatch.setattr(notifications, "record_success",
                        lambda slug, event_type: captured_success.append((slug, event_type)))
    monkeypatch.setattr(notifications, "publish",
                        lambda event: captured_publish.append(event))
    monkeypatch.setattr(audit_log, "record_event",
                        lambda *args, **kwargs: captured_audit.append((args, kwargs)))

    # Bootstrap an asset via storage.save_asset (Phase 90 pattern)
    from lingwen_illustrations import storage
    from lingwen_illustrations.metadata import IllustrationMetadata
    meta = IllustrationMetadata(
        id="asset-y", type="cover", project_slug="test-slug",
        chapter_num=None, created_at="2026-09-21T10:00:00Z",
        style_preset="default", provider="minimax", model="minimax-image-01",
        prompt="x", extra={},
    )
    storage.save_asset(tmp_path, b"\xff\xd8\xff\xe0fake-jpeg", meta)

    from apps.studio_api.routes._project_helpers import project_root_for
    monkeypatch.setattr("apps.studio_api.routes.illustrations.project_root_for",
                        lambda slug: tmp_path)

    from apps.studio_api.app import create_app
    from fastapi.testclient import TestClient
    client = TestClient(create_app())

    resp = client.delete("/api/illustrations/asset-y?project_slug=test-slug")
    assert resp.status_code == 200
    assert resp.json() == {"deleted": "asset-y"}
    assert len(captured_success) == 1
    assert captured_success[0] == ("test-slug", "deletion")
    # Phase 106: audit_log + publish double-write (I091) with same ULID
    assert len(captured_audit) == 1
    assert len(captured_publish) == 1
    assert captured_audit[0][1]["id"] == captured_publish[0].id
    assert captured_publish[0].event_type == "deletion"


def test_delete_asset_store_error_records_failure_with_real_root(monkeypatch, tmp_path):
    """T4: StoreError on storage.delete_asset → record_failure(event_type="deletion", project_root=root)."""
    from lingwen_illustrations import notifications, storage
    from lingwen_illustrations.exceptions import StoreError
    captured_failure = []
    monkeypatch.setattr(notifications, "record_failure",
                        lambda slug, err, *, project_root, threshold, event_type: captured_failure.append(
                            (slug, str(err), project_root, threshold, event_type)
                        ))
    monkeypatch.setattr(storage, "delete_asset",
                        lambda root, meta: (_ for _ in ()).throw(StoreError("disk full")))

    from apps.studio_api.routes._project_helpers import project_root_for
    monkeypatch.setattr("apps.studio_api.routes.illustrations.project_root_for",
                        lambda slug: tmp_path)

    from apps.studio_api.app import create_app
    from fastapi.testclient import TestClient
    client = TestClient(create_app())

    resp = client.delete("/api/illustrations/asset-z?project_slug=test-slug")
    assert resp.status_code == 500
    assert len(captured_failure) == 1
    slug, err_str, root, threshold, et = captured_failure[0]
    assert slug == "test-slug"
    assert root is tmp_path  # Phase 106: real project_root for audit_log
    assert et == "deletion"


def test_delete_asset_success_resets_counter_from_prior_failures(monkeypatch, tmp_path):
    """T5: 1 deletion success resets counter from prior 1 failure (counter stays 0)."""
    from lingwen_illustrations import notifications, storage
    from lingwen_illustrations.exceptions import StoreError

    # Trigger 1 failure then 1 success — verify counter resets
    call_log = []
    monkeypatch.setattr(notifications, "record_failure",
                        lambda *a, **kw: call_log.append(("fail", a, kw)))
    monkeypatch.setattr(notifications, "record_success",
                        lambda slug, event_type: call_log.append(("ok", slug, event_type)))

    # First: StoreError
    monkeypatch.setattr(storage, "delete_asset",
                        lambda *a, **kw: (_ for _ in ()).throw(StoreError("boom")))

    from apps.studio_api.routes._project_helpers import project_root_for
    monkeypatch.setattr("apps.studio_api.routes.illustrations.project_root_for",
                        lambda slug: tmp_path)

    from apps.studio_api.app import create_app
    from fastapi.testclient import TestClient
    client = TestClient(create_app())

    resp = client.delete("/api/illustrations/asset-a?project_slug=test-slug")
    assert resp.status_code == 500

    # Now: success
    monkeypatch.undo()  # reset all monkeypatches
    # Re-bootstrap with original storage behavior
    from lingwen_illustrations.metadata import IllustrationMetadata
    meta = IllustrationMetadata(
        id="asset-b", type="cover", project_slug="test-slug",
        chapter_num=None, created_at="2026-09-21T10:00:00Z",
        style_preset="default", provider="minimax", model="minimax-image-01",
        prompt="x", extra={},
    )
    storage.save_asset(tmp_path, b"\xff\xd8\xff\xe0fake-jpeg", meta)

    from apps.studio_api.routes._project_helpers import project_root_for as prf
    monkeypatch.setattr("apps.studio_api.routes.illustrations.project_root_for", prf)  # restore real

    captured_success = []
    monkeypatch.setattr(notifications, "record_success",
                        lambda slug, event_type: captured_success.append((slug, event_type)))
    captured_failure = []
    monkeypatch.setattr(notifications, "record_failure",
                        lambda *a, **kw: captured_failure.append(1))

    resp = client.delete("/api/illustrations/asset-b?project_slug=test-slug")
    assert resp.status_code == 200
    assert len(captured_success) == 1
    assert len(captured_failure) == 0


def test_delete_asset_threshold_crossing_emits_warning(monkeypatch, tmp_path):
    """T6: 3 consecutive StoreErrors with threshold=2 → 1 severity=warning notification emitted."""
    from lingwen_illustrations import notifications, storage
    from lingwen_illustrations.exceptions import StoreError

    # Pre-seed threshold via direct notifications state mutation
    notifications._consecutive_failures[("test-slug", "deletion")] = 0
    notifications._warning_emitted[("test-slug", "deletion")] = False

    captured_publishes = []
    monkeypatch.setattr(notifications, "publish",
                        lambda event: captured_publishes.append(event))

    monkeypatch.setattr(storage, "delete_asset",
                        lambda *a, **kw: (_ for _ in ()).throw(StoreError("boom")))

    from apps.studio_api.routes._project_helpers import project_root_for
    monkeypatch.setattr("apps.studio_api.routes.illustrations.project_root_for",
                        lambda slug: tmp_path)

    from apps.studio_api.app import create_app
    from fastapi.testclient import TestClient
    client = TestClient(create_app())

    # Trigger 3 deletions, all fail. threshold=2.
    # Use a custom settings yaml with notify_threshold.deletion = 2
    settings_path = tmp_path / ".lingwen" / "illustration_settings.yaml"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text("notify_threshold:\n  deletion: 2\n", encoding="utf-8")

    for i in range(3):
        resp = client.delete(f"/api/illustrations/asset-{i}?project_slug=test-slug")
        assert resp.status_code == 500

    # Phase 102: exactly 1 warning emitted (idempotent on threshold crossing)
    warnings = [e for e in captured_publishes if e.event_type == "deletion" and e.severity == "warning"]
    assert len(warnings) == 1
```

**Validation**:
- `pytest apps/studio_api/tests/test_illustrations_api.py::test_delete_asset_load_error_records_failure_with_none_root -v` → FAIL (record_failure not yet called)
- All 6 tests should FAIL — record_failure/record_success not yet wired
- `ruff check apps/studio_api/tests/test_illustrations_api.py` → clean

**Risk mitigation**:
- Use unique slugs (`test-slug`, `missing-slug`) per test to avoid cross-test counter bleed (Phase 105 pattern)
- Monkeypatch `notifications.record_failure/record_success/publish` directly (Phase 105 T1 lesson: cleanup_route `from ... import X` creates local bindings, patch destination not source)
- Use `monkeypatch.undo()` for T5 to reset state between failure + success scenarios

### Commit 4: test — pytest T7-T9 (counter isolation + helper resilience, RED-ish)

**File**: `packages/lingwen-illustrations/tests/test_phase106_deletion_isolation.py` (NEW)

```python
"""Phase 106: deletion event_type counter isolation + helper resilience tests."""

import pytest
from lingwen_illustrations import notifications


@pytest.fixture(autouse=True)
def _reset_state():
    """Reset counter + warning flags per test (Phase 105 pattern)."""
    notifications._consecutive_failures.clear()
    notifications._warning_emitted.clear()
    yield
    notifications._consecutive_failures.clear()
    notifications._warning_emitted.clear()


def test_deletion_counter_isolated_from_generation():
    """T7: 3 deletion failures leave generation counter at 0."""
    for _ in range(3):
        notifications.record_failure(
            "iso-slug", RuntimeError("x"),
            project_root=None, threshold=1, event_type="deletion",
        )
    assert notifications._consecutive_failures.get(("iso-slug", "generation"), 0) == 0
    assert notifications._consecutive_failures[("iso-slug", "deletion")] == 3


def test_resolve_threshold_returns_int_for_configured_deletion_key():
    """T8a: resolve_threshold returns int for configured "deletion" key."""
    settings = {"notify_threshold": {"generation": 3, "regeneration": 3, "cleanup": 3, "deletion": 5}}
    assert notifications.resolve_threshold(settings, "deletion") == 5


def test_resolve_threshold_returns_infinity_for_missing_deletion_key():
    """T8b: resolve_threshold returns INFINITY for unconfigured "deletion" key."""
    settings = {"notify_threshold": {"generation": 3}}
    result = notifications.resolve_threshold(settings, "deletion")
    assert result == notifications.INFINITY_THRESHOLD


def test_load_deletion_settings_permissive_fallback_missing_file(tmp_path):
    """T9a: Missing .lingwen/illustration_settings.yaml → returns {}."""
    from apps.studio_api.routes.illustrations import _load_deletion_settings
    assert _load_deletion_settings(tmp_path) == {}


def test_load_deletion_settings_permissive_fallback_malformed_yaml(tmp_path):
    """T9b: Malformed yaml → returns {} (defensive read)."""
    from apps.studio_api.routes.illustrations import _load_deletion_settings
    settings_path = tmp_path / ".lingwen" / "illustration_settings.yaml"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text("not: valid: yaml: [[[", encoding="utf-8")
    assert _load_deletion_settings(tmp_path) == {}


def test_load_deletion_settings_returns_dict_when_present(tmp_path):
    """T9c: Valid yaml → returns dict with notify_threshold etc."""
    from apps.studio_api.routes.illustrations import _load_deletion_settings
    settings_path = tmp_path / ".lingwen" / "illustration_settings.yaml"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text("notify_threshold:\n  deletion: 7\n", encoding="utf-8")
    result = _load_deletion_settings(tmp_path)
    assert result == {"notify_threshold": {"deletion": 7}}
```

**Validation**:
- `pytest packages/lingwen-illustrations/tests/test_phase106_deletion_isolation.py -v` → PARTIAL FAIL (T9 tests fail — `_load_deletion_settings` not yet defined; T7/T8 pass — counter isolation + resolve_threshold already work from Phase 104)
- `ruff check` on new file → clean

**Risk mitigation**:
- Autouse fixture resets counter state between tests (Phase 105 lesson: in-memory state pollutes cross-test bleed)
- T7-T8 may pass before Commit 5 (counter isolation is inherited invariant); T9 must fail before helper exists

### Commit 5: feat — `_load_deletion_settings` helper + module imports in illustrations.py

**Files**:
- `apps/studio_api/routes/illustrations.py` — add `import yaml` at top; add `from lingwen_illustrations import audit_log, notifications` at top; add `_load_deletion_settings(project_root: Path) -> dict` helper (mirrors cleanup_route.py:67-74)

**Code** (add after existing imports around line 14-20):

```python
import yaml  # Phase 106: for _load_deletion_settings
```

Add to top imports:

```python
from lingwen_illustrations import audit_log, notifications  # Phase 99 + Phase 106: double-write + failure tracking
```

Add helper before `def register_routes`:

```python
def _load_deletion_settings(project_root: Path) -> dict:
    """Phase 106: load notification-relevant settings for deletion event_type.

    Reads .lingwen/illustration_settings.yaml and returns dict containing
    notify_threshold (or empty dict if file missing / malformed). Used by
    delete_asset to resolve per-event-type threshold via
    notifications.resolve_threshold(). Defensive: missing file silently
    returns {} (matches cleanup_route._load_cleanup_settings + pipeline
    _load_illustration_settings pattern).
    """
    settings_path = project_root / ".lingwen" / "illustration_settings.yaml"
    if not settings_path.exists():
        return {}
    try:
        data = yaml.safe_load(settings_path.read_text(encoding="utf-8")) or {}
        return dict(data) if isinstance(data, dict) else {}
    except (yaml.YAMLError, OSError):
        return {}
```

**Validation**:
- `pytest packages/lingwen-illustrations/tests/test_phase106_deletion_isolation.py::test_load_deletion_settings_permissive_fallback_missing_file -v` → PASS (helper exists)
- `pytest packages/lingwen-illustrations/tests/test_phase106_deletion_isolation.py -v` → T9 a/b/c PASS, T7/T8 PASS (counter isolation unaffected)
- `ruff check apps/studio_api/routes/illustrations.py` → clean

**Risk mitigation**:
- `import yaml` at module top is safe (no heavy deps; yaml is stdlib-adjacent PyYAML)
- `from lingwen_illustrations import audit_log, notifications` is safe (lightweight modules, no import-time side effects — verified in cleanup_route.py:27)
- `_load_deletion_settings` mirrors cleanup_route.py:67-74 exactly (DRY violation acceptable for module-locality per Phase 105 lesson)

### Commit 6: feat — wire `delete_asset` route (failure tracking + double-write, GREEN)

**File**: `apps/studio_api/routes/illustrations.py:336-353`

Replace existing `delete_asset` handler:

```python
    @app.delete("/api/illustrations/{asset_id}")
    def delete_asset(
        asset_id: str,
        project_slug: str = Query(...),
    ) -> dict:
        # Phase 106: failure tracking wiring (mirrors cleanup_route Phase 105 pattern).
        # LoadError path: record_failure with project_root=None (counter increments; audit_log skipped).
        try:
            project_root = project_root_for(project_slug)
        except LoadError as e:
            notifications.record_failure(
                project_slug, e,
                project_root=None,
                threshold=notifications.resolve_threshold({}, "deletion"),
                event_type="deletion",
            )
            raise HTTPException(404, detail=_err_detail(e)) from e

        # Real project_root exists — resolve actual threshold from settings.
        settings = _load_deletion_settings(project_root)
        threshold = notifications.resolve_threshold(settings, "deletion")

        # Find the asset by id (list_assets is idempotent and cheap).
        all_assets = storage.list_assets(project_root)
        meta = next((a for a in all_assets if a.id == asset_id), None)

        if meta is None:
            # Phase 106: 404 asset-not-found = no-op success (per user decision).
            # Asset is already gone (idempotent); record_success resets the
            # (slug, "deletion") counter to avoid stale warnings from prior
            # transient failures. Symmetric with cleanup_route "0 deleted under
            # limit" success path.
            notifications.record_success(project_slug, event_type="deletion")
            raise HTTPException(404, detail=f"asset {asset_id} not found")

        # Phase 106: real delete with failure tracking + double-write.
        try:
            storage.delete_asset(project_root, meta)
        except StoreError as e:
            # Phase 106: StoreError is a system failure — record_failure with
            # the real project_root (audit_log captures the warning event).
            notifications.record_failure(
                project_slug, e,
                project_root=project_root,
                threshold=threshold,
                event_type="deletion",
            )
            raise HTTPException(500, detail=_err_detail(e)) from e
        else:
            # Phase 106: successful delete resets (slug, "deletion") counter.
            notifications.record_success(project_slug, event_type="deletion")

        # Phase 99 I091 + Phase 106: double-write audit_log + publish (same ULID).
        event_id = notifications.new_event_id()
        audit_log.record_event(
            project_root,
            event="deletion",
            asset_meta=meta,
            id=event_id,
            extra={"trigger": "manual"},
        )
        notifications.publish(notifications.NotificationEvent(
            id=event_id,
            project_slug=project_slug,
            event_type="deletion",
            asset_id=meta.id,
            asset_type=meta.type,
            chapter_num=meta.chapter_num,
            style_preset=meta.style_preset,
            provider=meta.provider,
            ts=notifications.now_iso(),
            extra={"trigger": "manual"},
        ))

        return {"deleted": asset_id}
```

**Validation**:
- `pytest apps/studio_api/tests/test_illustrations_api.py -k "delete_asset" -v` → T1-T6 PASS
- `pytest packages/lingwen-illustrations/tests/test_phase106_deletion_isolation.py -v` → T7-T9 PASS
- `ruff check apps/studio_api/routes/illustrations.py` → clean
- Phase 102/103/104/105 guards preserved (no behavior change to generation/regeneration/cleanup paths)

**Risk mitigation**:
- `else` branch on `try: storage.delete_asset()` runs only after successful delete (Phase 105 lesson: never record_success on exception path)
- 404 LoadError raises BEFORE `_load_deletion_settings` call (no project_root yet — uses empty settings dict for threshold)
- 404 asset-not-found is in main flow (not exception path), record_success fires before HTTPException raise
- `audit_log.record_event` + `notifications.publish` use SAME `event_id` (ULID) — I091 invariant double-write contract

### Commit 7: test — vitest F1-F4 (NPopconfirm, RED)

**File**: `apps/dashboard/tests/unit/components/illustrations/IllustrationCard.spec.ts` (extend existing spec)

Append 4 tests at end of existing describe block:

```typescript
// Phase 106: NPopconfirm wrapping around 🗑 delete button
describe('IllustrationCard (Phase 106: NPopconfirm delete)', () => {
  beforeEach(() => {
    // Use a stub asset so card mounts
  })

  it('F1: clicking 🗑 button opens NPopconfirm', async () => {
    const wrapper = mount(IllustrationCard, {
      props: { asset: { id: 'a1', type: 'cover', chapter_num: null, /* ... */ } },
      global: { plugins: [createTestingPinia()] },
    })
    await wrapper.find('[data-testid="delete-btn"]').trigger('click')
    // Naive UI NPopconfirm renders confirmation in a portal — assert content
    expect(document.body.textContent).toContain('确定删除这张插图？')
  })

  it('F2: clicking "确认删除" emits delete event with asset.id', async () => {
    const wrapper = mount(IllustrationCard, {
      props: { asset: { id: 'a2', type: 'cover', chapter_num: null, /* ... */ } },
      global: { plugins: [createTestingPinia()] },
    })
    await wrapper.find('[data-testid="delete-btn"]').trigger('click')
    // Click positive button in popconfirm
    const confirmBtn = document.body.querySelector('.n-popconfirm__action .n-button--primary-type')
    if (confirmBtn) (confirmBtn as HTMLElement).click()
    expect(wrapper.emitted('delete')).toBeTruthy()
    expect(wrapper.emitted('delete')![0]).toEqual(['a2'])
  })

  it('F3: clicking "取消" does NOT emit delete event', async () => {
    const wrapper = mount(IllustrationCard, {
      props: { asset: { id: 'a3', type: 'cover', chapter_num: null, /* ... */ } },
      global: { plugins: [createTestingPinia()] },
    })
    await wrapper.find('[data-testid="delete-btn"]').trigger('click')
    const cancelBtn = document.body.querySelector('.n-popconfirm__action .n-button:not(.n-button--primary-type)')
    if (cancelBtn) (cancelBtn as HTMLElement).click()
    expect(wrapper.emitted('delete')).toBeFalsy()
  })

  it('F4: Esc key dismisses popconfirm', async () => {
    const wrapper = mount(IllustrationCard, {
      props: { asset: { id: 'a4', type: 'cover', chapter_num: null, /* ... */ } },
      global: { plugins: [createTestingPinia()] },
    })
    await wrapper.find('[data-testid="delete-btn"]').trigger('click')
    // Trigger Esc
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await nextTick()
    expect(document.body.textContent).not.toContain('确定删除这张插图？')
  })
})
```

**Validation**:
- `pnpm vitest run apps/dashboard/tests/unit/components/illustrations/IllustrationCard.spec.ts -v` → F1-F4 FAIL (NPopconfirm not yet wrapped around button)
- `pnpm tsc --noEmit` → no new errors

**Risk mitigation**:
- Use `document.body.textContent` to check NPopconfirm content (portal-mounted, not in component DOM)
- `wrapper.emitted('delete')` is the canonical Vue Test Utils pattern
- Keyboard event simulation per Naive UI conventions

### Commit 8: feat — wrap 🗑 button in NPopconfirm (GREEN)

**File**: `apps/dashboard/src/components/illustrations/IllustrationCard.vue` (modify lines 34-40)

Replace the standalone button:

```vue
<NPopconfirm
  positive-text="确认删除"
  negative-text="取消"
  @positive-click="emit('delete', asset.id)"
>
  <template #trigger>
    <button
      class="delete-btn"
      data-testid="delete-btn"
      :aria-label="`删除 ${label}`"
    >🗑 删除</button>
  </template>
  确定删除这张插图？删除后无法恢复。
</NPopconfirm>
```

**Validation**:
- `pnpm vitest run apps/dashboard/tests/unit/components/illustrations/IllustrationCard.spec.ts -v` → F1-F4 PASS
- `pnpm tsc --noEmit` → 0 new errors
- Existing IllustrationCard tests preserved (data-testid="delete-btn" still works — wrapped, not removed)

**Risk mitigation**:
- `data-testid="delete-btn"` preserved on inner button (Phase 90 convention) — existing tests don't break
- `:aria-label` preserved for screen readers (a11y Phase 41+ convention)
- NPopconfirm cancel path is purely frontend (no network call made, no counter touched)

### Commit 9: test — regression guards G1-G6

**File**: `tests/test_phase106_delete_endpoint_failure_tracking.py` (NEW)

```python
"""Phase 106: regression guards for delete_asset failure tracking wiring.

Guards G1-G6 prevent Phase 106 from being reverted to the no-tracking state
where DELETE /api/illustrations/{asset_id} does NOT call
notifications.record_failure/record_success or audit_log/publish.
"""

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ILLUSTRATIONS_ROUTE = REPO_ROOT / "apps/studio_api/routes/illustrations.py"
ARCHITECTURE_YML = REPO_ROOT / ".lingwen/architecture.yml"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _strip_docstrings(text: str) -> str:
    return re.sub(r'""".*?""""', "", text, flags=re.DOTALL)


def test_g1_delete_asset_route_has_at_least_two_record_failure_calls():
    """G1: delete_asset route has ≥2 record_failure(event_type='deletion') calls.

    Catches Phase 106 reverts to no-tracking state.
    """
    text = _strip_docstrings(_read(ILLUSTRATIONS_ROUTE))
    # Find the delete_asset function body
    match = re.search(r'def delete_asset\([^)]*\)[^:]*:(.*?)(?=\n    @app\.|^\Z)',
                      text, re.DOTALL | re.MULTILINE)
    assert match, "delete_asset function not found"
    body = match.group(1)
    count = body.count('event_type="deletion"')
    failure_calls = body.count('record_failure(')
    assert failure_calls >= 2, (
        f"Expected ≥2 record_failure calls in delete_asset body, found {failure_calls}"
    )
    assert count >= 2, (
        f"Expected ≥2 'event_type=\"deletion\"' references in delete_asset body, found {count}"
    )


def test_g2_delete_asset_route_has_at_least_one_record_success_call():
    """G2: delete_asset route has ≥1 record_success(event_type='deletion') call.

    Catches counter leak (counter stays elevated).
    """
    text = _strip_docstrings(_read(ILLUSTRATIONS_ROUTE))
    match = re.search(r'def delete_asset\([^)]*\)[^:]*:(.*?)(?=\n    @app\.|^\Z)',
                      text, re.DOTALL | re.MULTILINE)
    assert match
    body = match.group(1)
    success_calls = body.count('record_success(')
    assert success_calls >= 1, (
        f"Expected ≥1 record_success call in delete_asset body, found {success_calls}"
    )
    assert 'event_type="deletion"' in body


def test_g3_delete_asset_double_writes_audit_log_and_publish():
    """G3: delete_asset route calls audit_log.record_event + notifications.publish (I091).

    Catches double-write regression.
    """
    text = _strip_docstrings(_read(ILLUSTRATIONS_ROUTE))
    match = re.search(r'def delete_asset\([^)]*\)[^:]*:(.*?)(?=\n    @app\.|^\Z)',
                      text, re.DOTALL | re.MULTILINE)
    assert match
    body = match.group(1)
    assert 'audit_log.record_event(' in body, "audit_log.record_event not called"
    assert 'notifications.publish(' in body, "notifications.publish not called"


def test_g4_load_deletion_settings_helper_exists_in_illustrations_py():
    """G4: _load_deletion_settings helper exists in illustrations.py.

    Catches helper deletion regression.
    """
    text = _read(ILLUSTRATIONS_ROUTE)
    assert "def _load_deletion_settings" in text, (
        "_load_deletion_settings helper not found in illustrations.py"
    )
    assert ".lingwen/illustration_settings.yaml" in text, (
        "_load_deletion_settings must read .lingwen/illustration_settings.yaml"
    )


def test_g5_deletion_failures_dont_increment_generation_counter():
    """G5: 3 record_failure(slug, ..., event_type='deletion') calls leave generation counter = 0.

    Catches counter isolation break.
    """
    from lingwen_illustrations import notifications
    # Reset state
    notifications._consecutive_failures.clear()
    notifications._warning_emitted.clear()

    for _ in range(3):
        notifications.record_failure(
            "g5-slug", RuntimeError("x"),
            project_root=None, threshold=1, event_type="deletion",
        )

    assert notifications._consecutive_failures.get(("g5-slug", "generation"), 0) == 0
    assert notifications._consecutive_failures[("g5-slug", "deletion")] == 3

    # Cleanup
    notifications._consecutive_failures.clear()
    notifications._warning_emitted.clear()


def test_g6_i090_i091_i095_extended_to_deletion_event_type():
    """G6: I090/I091 rule fields mention DELETE route + I095 EXTENDED mentions deletion event_type.

    Catches invariant extension regression.
    """
    import yaml
    with ARCHITECTURE_YML.open(encoding="utf-8") as f:
        arch = yaml.safe_load(f)

    invariants = {inv["id"]: inv for inv in arch["architecture_invariants"]}

    # I090 EXTENDED: mentions DELETE route
    i090_rule = invariants["I090"]["rule"]
    assert "delete_asset" in i090_rule or "illustrations.py" in i090_rule, (
        f"I090 rule must mention delete_asset route or illustrations.py: {i090_rule}"
    )

    # I091 EXTENDED: mentions DELETE route
    i091_rule = invariants["I091"]["rule"]
    assert "delete_asset" in i091_rule or "illustrations.py" in i091_rule, (
        f"I091 rule must mention delete_asset route or illustrations.py: {i091_rule}"
    )

    # I095 EXTENDED: mentions deletion event_type (4th extension)
    i095_rule = invariants["I095"]["rule"]
    assert "deletion" in i095_rule, (
        f"I095 rule must mention deletion event_type: {i095_rule}"
    )
```

**Validation**:
- `pytest tests/test_phase106_delete_endpoint_failure_tracking.py -v` → G1-G6 FAIL (architecture.yml not yet extended in Commit 10)
- `ruff check tests/test_phase106_delete_endpoint_failure_tracking.py` → clean

**Risk mitigation**:
- Use `_strip_docstrings` helper (Phase 57b N.14 v21 lesson) to avoid docstring literal grep false-positives
- Regex anchored to function body (not raw substring) — verifies scope, not just existence
- G5 mutates in-memory counter state; cleanup at end (Phase 105 test pollution mitigation)

### Commit 10: docs — extend I090/I091/I095 in architecture.yml

**File**: `.lingwen/architecture.yml`

Edit I090 rule field — add `apps/studio_api/routes/illustrations.py (delete_asset)` as 4th caller.

Edit I091 rule field — add `apps/studio_api/routes/illustrations.py (delete_asset)` as 4th double-write site.

Edit I095 rule field — extend docstring to mention Phase 106 EXTENDED (4th extension of same invariant name):

```
I095: ...keyed per (project_slug, event_type) tuple... record_failure()/record_success()...
Phase 106 EXTENDED via docstring (delete_asset route is the third caller; all 4
event_types — generation/regeneration/cleanup/deletion — now have ≥1 caller;
404 asset-not-found treated as no-op success via record_success to defensively
reset counter; counter resets via record_success in else branch of
storage.delete_asset try/except — same pattern as cleanup_route).
```

Update scope field to include Phase 106 enforcement refs (test_phase106_*.py G1-G6).

**Validation**:
- `pytest tests/test_phase106_delete_endpoint_failure_tracking.py -v` → G1-G6 PASS
- `pytest tests/test_phase102_*.py tests/test_phase103_*.py tests/test_phase104_*.py tests/test_phase105_*.py -v` → all preserved GREEN
- `python -c "import yaml; yaml.safe_load(open('.lingwen/architecture.yml'))"` → parses cleanly

**Risk mitigation**:
- Use parsed YAML value check (Phase 77 lesson: not raw text grep)
- Preserve existing invariant structure (don't reorder IDs)
- Docstring extension format matches Phase 104/105 precedent

### Commit 11: docs — CLAUDE.md v60.3 → v60.4 + handoff + BACKLOG + CURRENT_STATUS + MEMORY sync

**Files**:
- `CLAUDE.md` — version line bump v60.3 → v60.4; add Phase 106 entry to "Previous" block; extend I090/I091/I095 rows in architecture invariants table
- `docs/superpowers/handoffs/2026-09-21-phase-106-delete-endpoint-failure-tracking-handoff.md` — NEW handoff doc (mirror Phase 105 handoff structure)
- `collaboration/CURRENT_STATUS.md` — last updated line + version row update
- `collaboration/BACKLOG.md` — add Phase 106 row to "已完成（近期）" + "最近变更"
- `/home/ailearn/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md` — version line v60.4 + Phase 106 topic pointer to handoff

**Validation**:
- `git diff --stat` shows only docs files changed
- `git log --oneline -12` shows clean atomic history
- All previous Phase 102-105 guard tests preserved

**Risk mitigation**:
- Docs sync is last commit (per 2026-09-15 simplified workflow)
- CLAUDE.md changes: version line + "Previous" block; don't touch invariant table structure
- BACKLOG.md: add to "已完成（近期）" + "最近变更" (append, don't reorder)

---

## Self-review

### 1. Spec coverage

| Spec section | Plan task |
|--------------|-----------|
| §1 NEW `_load_deletion_settings` helper | Commit 5 |
| §2 DELETE endpoint failure tracking (5-path contract) | Commit 6 |
| §3 Frontend NPopconfirm wrapping | Commit 8 |
| §4 Counter isolation preserved | Commit 9 G5 (covered by Phase 104 invariant) |
| §5 Settings persistence integration | Commit 5 (helper) + Commit 6 (resolve_threshold call) |
| §6 Invariant extensions I090/I091/I095 | Commit 10 |
| Test coverage matrix T1-T9 | Commit 3 (T1-T6) + Commit 4 (T7-T9) |
| Regression guards G1-G6 | Commit 9 |
| §A test files migration plan | N/A — Phase 106 is NOT P3-ARCHDEBT (no infra/* migrations) |
| Validation gates | Distributed across commits 3, 5, 6, 8, 9, 10 |
| Atomic commits (~9) | 11 atomic commits planned (matches spec target ±2) |

### 2. Placeholder scan
- No "TBD", "TODO", "implement later" — all code blocks complete
- No "add appropriate error handling" — explicit try/except in Commit 6
- No "similar to Task N" — each commit's code is self-contained
- No "write tests for the above" — actual test code in Commits 3, 4, 7, 9

### 3. Type consistency
- `_load_deletion_settings(project_root: Path) -> dict` defined in Commit 5, used in Commit 6
- `delete_asset(asset_id: str, project_slug: str = Query(...)) -> dict` signature unchanged from Phase 90
- `record_failure` / `record_success` / `publish` / `record_event` signatures match Phase 102/104/105 pattern
- `NotificationEvent` fields match Phase 99/101/105 shape (event_type / asset_id / asset_type / chapter_num / style_preset / provider / ts / extra)

### 4. Ambiguity check
- Commit 6 explicitly distinguishes LoadError (404) vs asset-not-found (404) vs StoreError (500) vs success (200) — 4 separate paths
- Commit 8 NPopconfirm cancel path is purely frontend (no counter touched)
- Commit 9 G6 uses parsed YAML value check (Phase 77 lesson)

All spec requirements have a task. No gaps detected.
