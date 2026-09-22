"""Phase 108: T1-T10 bulk regenerate endpoint tests.

T1-T10 are RED until Commit 5 wires bulk_regenerate_assets + the
_regenerate_asset_inner helper extracted in Commit 4. Each test exercises
one path in the per-asset failure tracking contract (I090/I091/I095 6th
EXTENDED) via the new ``PUT /api/illustrations?slug=...&ids=...`` route.

Mirrors Phase 107 test_bulk_delete_api.py exactly with these translations:
  - bulk_delete_assets → bulk_regenerate_assets
  - DELETE → PUT
  - limit 50 → limit 10
  - storage.delete_asset → pipeline.regenerate_illustration
  - "store_error" → "stage_error" (regenerate fails on Stage 1/2/3, not Stage 4)
  - "deletion" → "regeneration" event_type
  - counter keys (slug, "deletion") → (slug, "regeneration")
  - _load_deletion_settings → _load_regeneration_settings (NEW helper)
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from lingwen_illustrations import audit_log, notifications
from lingwen_illustrations.exceptions import (
    GenerateError,
    IllustrationError,
    LoadError,
    UnknownModelError,
)
from lingwen_illustrations.metadata import IllustrationMetadata

from apps.studio_api.app import create_app
from apps.studio_api.routes import illustrations as illus_module


def _make_meta(asset_id: str, project_slug: str = "test-slug") -> "IllustrationMetadata":
    """Build a minimal valid IllustrationMetadata for storage.save_asset bootstrap."""
    return IllustrationMetadata(
        id=asset_id,
        type="cover",
        project_slug=project_slug,
        chapter_num=None,
        style_preset="default",
        custom_prompt=None,
        scene_json={},
        final_prompt="x",
        prompt_hash="sha256:x",
        model="minimax-image-01",
        provider="minimax",
        used_reference_image=False,
        created_at="2026-09-22T10:00:00Z",
    )


@pytest.fixture(autouse=True)
def _reset_notifications_state():
    """Clear per-(slug, event_type) counters between tests for isolation.

    Phase 104 tuple-keyed counters + Phase 102 idempotent _warning_emitted
    flag survive across tests in the same process. Clear all (slug, "regeneration")
    keys before AND after each test to prevent bleed.
    """
    keys_to_clear = [
        k for k in list(notifications._consecutive_failures.keys())
        if isinstance(k, tuple) and len(k) == 2 and k[1] == "regeneration"
    ]
    for k in keys_to_clear:
        notifications._consecutive_failures.pop(k, None)
        notifications._warning_emitted.pop(k, None)
    yield
    keys_to_clear = [
        k for k in list(notifications._consecutive_failures.keys())
        if isinstance(k, tuple) and len(k) == 2 and k[1] == "regeneration"
    ]
    for k in keys_to_clear:
        notifications._consecutive_failures.pop(k, None)
        notifications._warning_emitted.pop(k, None)


# ---------- T1: Happy path ----------
def test_bulk_regenerate_happy_path_records_per_asset(monkeypatch, tmp_path):
    """T1: 5 assets all in storage; expect 5× record_success + 5× audit + 5× publish.

    Mirrors Phase 107 T1 exactly with regenerate mocks instead of delete.
    """
    from lingwen_illustrations import storage

    captured_success, captured_audit, captured_publish = [], [], []

    monkeypatch.setattr(
        notifications,
        "record_success",
        lambda slug, event_type: captured_success.append((slug, event_type)),
    )
    monkeypatch.setattr(
        audit_log,
        "record_event",
        lambda *args, **kwargs: captured_audit.append((args, kwargs)),
    )

    def fake_publish(event):
        captured_publish.append(event)
        return None

    monkeypatch.setattr(notifications, "publish", fake_publish)

    # Patch project_root_for to resolve to tmp_path.
    monkeypatch.setattr(
        illus_module,
        "project_root_for",
        lambda slug: tmp_path if slug == "test-slug" else (_ for _ in ()).throw(
            LoadError(f"project {slug} not found")
        ),
    )

    # Pre-populate storage with 5 assets (real sidecar + .jpg so list_assets finds them).
    asset_ids = []
    for i in range(5):
        meta = _make_meta(f"asset-{i}")
        storage.save_asset(tmp_path, b"\xff\xd8\xff\xe0fake-jpeg", meta)
        asset_ids.append(meta.id)

    # Mock pipeline.regenerate_illustration to always succeed (return new_meta).
    async def fake_regenerate(*args, **kwargs):
        existing_meta = kwargs.get("existing_meta")
        # Mutate timestamp to mirror real pipeline (new created_at); return
        # new metadata instance.
        from datetime import datetime, timezone

        return IllustrationMetadata(
            id=existing_meta.id,
            type=existing_meta.type,
            project_slug=existing_meta.project_slug,
            chapter_num=existing_meta.chapter_num,
            style_preset=existing_meta.style_preset,
            custom_prompt=existing_meta.custom_prompt,
            scene_json={},
            final_prompt="regenerated-x",
            prompt_hash="sha256:regen",
            model=existing_meta.model,
            provider=existing_meta.provider,
            used_reference_image=False,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    # The route lazy-imports `regenerate_illustration as run_regen` inside the
    # handler — so the canonical patch target is the source module attribute,
    # not any route attribute.
    monkeypatch.setattr(
        "lingwen_illustrations.pipeline.regenerate_illustration",
        fake_regenerate,
    )

    client = TestClient(create_app())
    ids_csv = ",".join(asset_ids)
    resp = client.put(f"/api/illustrations?slug=test-slug&ids={ids_csv}")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body["regenerated"]) == 5
    assert body["failed"] == []
    assert body["summary"] == {"total": 5, "ok": 5, "fail": 0}

    # 5 record_success calls
    assert len(captured_success) == 5
    assert all(s == ("test-slug", "regeneration") for s in captured_success)

    # 5 audit_log.record_event + 5 notifications.publish
    assert len(captured_audit) == 5
    assert len(captured_publish) == 5

    # Audit extra={"trigger":"manual","mode":"bulk"} — same ULID between audit and publish.
    for _, kwargs in captured_audit:
        assert kwargs.get("extra") == {"trigger": "manual", "mode": "bulk"}

    # I091: same ULID for audit + publish pair
    for i in range(5):
        assert captured_audit[i][1]["id"] == captured_publish[i].id

    # Phase 108 M3: verify 5 distinct ULIDs (per-asset semantics, not single batched)
    assert len({a[1]["id"] for a in captured_audit}) == 5


# ---------- T2: Partial failure ----------
def test_bulk_regenerate_partial_failure_records_failure_per_asset(monkeypatch, tmp_path):
    """T2: 5 assets; 3 regen success + 2 IllustrationError. Expect 3× record_success + 2× record_failure."""
    from lingwen_illustrations import storage

    captured_success, captured_failure = [], []

    monkeypatch.setattr(
        notifications,
        "record_success",
        lambda slug, event_type: captured_success.append((slug, event_type)),
    )
    monkeypatch.setattr(
        notifications,
        "record_failure",
        lambda slug, err, *, project_root, threshold, event_type: captured_failure.append(
            (slug, str(err), project_root, event_type)
        ),
    )
    monkeypatch.setattr(audit_log, "record_event", lambda *a, **kw: None)
    monkeypatch.setattr(notifications, "publish", lambda ev: None)

    # Pre-populate 5 assets.
    asset_ids = []
    for i in range(5):
        meta = _make_meta(f"asset-{i}")
        storage.save_asset(tmp_path, b"\xff\xd8\xff\xe0fake-jpeg", meta)
        asset_ids.append(meta.id)

    async def fake_regenerate(*args, **kwargs):
        existing_meta = kwargs.get("existing_meta")
        if existing_meta.id in ("asset-1", "asset-3"):
            raise GenerateError(f"failed to regenerate {existing_meta.id}")
        # Return new meta for successful assets.
        return IllustrationMetadata(
            id=existing_meta.id,
            type=existing_meta.type,
            project_slug=existing_meta.project_slug,
            chapter_num=existing_meta.chapter_num,
            style_preset=existing_meta.style_preset,
            custom_prompt=existing_meta.custom_prompt,
            scene_json=existing_meta.scene_json,
            final_prompt=existing_meta.final_prompt,
            prompt_hash=existing_meta.prompt_hash,
            model=existing_meta.model,
            provider=existing_meta.provider,
            used_reference_image=False,
            created_at="2026-09-22T10:00:00Z",
        )

    monkeypatch.setattr(
        "lingwen_illustrations.pipeline.regenerate_illustration",
        fake_regenerate,
    )
    monkeypatch.setattr(
        illus_module,
        "project_root_for",
        lambda slug: tmp_path if slug == "test-slug" else (_ for _ in ()).throw(
            LoadError(f"project {slug} not found")
        ),
    )

    client = TestClient(create_app())
    resp = client.put("/api/illustrations?slug=test-slug&ids=" + ",".join(asset_ids))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert sorted(body["regenerated"]) == ["asset-0", "asset-2", "asset-4"]
    assert len(body["failed"]) == 2
    assert {f["id"] for f in body["failed"]} == {"asset-1", "asset-3"}
    assert all(f["status"] == "stage_error" for f in body["failed"])
    assert body["summary"] == {"total": 5, "ok": 3, "fail": 2}

    assert len(captured_success) == 3
    assert len(captured_failure) == 2
    for slug, err_str, root, et in captured_failure:
        assert slug == "test-slug"
        assert et == "regeneration"
        assert root is not None  # real project_root (not None)


# ---------- T3: Empty ids ----------
def test_bulk_regenerate_empty_ids_returns_422(monkeypatch, tmp_path):
    """T3: ids= (empty) → 422."""
    monkeypatch.setattr(
        illus_module,
        "project_root_for",
        lambda slug: tmp_path if slug == "test-slug" else (_ for _ in ()).throw(
            LoadError(f"project {slug} not found")
        ),
    )

    client = TestClient(create_app())
    resp = client.put("/api/illustrations?slug=test-slug&ids=")
    assert resp.status_code == 422


# ---------- T4: Over 10 ids ----------
def test_bulk_regenerate_over_10_ids_returns_422(monkeypatch, tmp_path):
    """T4: 11 unique ids → 422 (Phase 108 limit=10 vs Phase 107 limit=50)."""
    monkeypatch.setattr(
        illus_module,
        "project_root_for",
        lambda slug: tmp_path if slug == "test-slug" else (_ for _ in ()).throw(
            LoadError(f"project {slug} not found")
        ),
    )

    client = TestClient(create_app())
    ids_csv = ",".join(f"a-{i}" for i in range(11))
    resp = client.put(f"/api/illustrations?slug=test-slug&ids={ids_csv}")
    assert resp.status_code == 422


# ---------- T5: Slug not found ----------
def test_bulk_regenerate_slug_not_found_returns_404(monkeypatch, tmp_path):
    """T5: slug does not resolve → 404 (no iteration)."""
    monkeypatch.setattr(
        illus_module,
        "project_root_for",
        lambda slug: (_ for _ in ()).throw(LoadError(f"project {slug} not found")),
    )

    client = TestClient(create_app())
    resp = client.put("/api/illustrations?slug=missing-slug&ids=a,b")
    assert resp.status_code == 404


# ---------- T6: LoadError upstream — endpoint must raise 404 before iteration ----------
def test_bulk_regenerate_load_error_returns_404_no_iteration(monkeypatch, tmp_path):
    """T6: project_root_for raises LoadError → 404 (no record_failure on this path).

    The endpoint catches LoadError and raises 404 directly; the per-asset helper
    is NOT invoked in the failure path (404 is pre-iteration, not per-asset).
    Mirrors Phase 107 T6 with regenerate semantics.
    """
    captured_failure = []
    monkeypatch.setattr(
        illus_module,
        "project_root_for",
        lambda slug: (_ for _ in ()).throw(LoadError(f"project {slug} not found")),
    )
    monkeypatch.setattr(
        notifications,
        "record_failure",
        lambda slug, err, *, project_root, threshold, event_type: captured_failure.append(
            (slug, str(err), project_root, event_type)
        ),
    )

    client = TestClient(create_app())
    resp = client.put("/api/illustrations?slug=missing-slug&ids=a,b,c")
    # T6: endpoint catches LoadError → 404 (NOT 200 with all in failed[])
    assert resp.status_code == 404
    # Endpoint should raise before calling the per-asset helper
    assert len(captured_failure) == 0


# ---------- T7: Dedupe ----------
def test_bulk_regenerate_dedupes_ids(monkeypatch, tmp_path):
    """T7: ids="a,a,b,b,b,c,d,d,d,d,d,d" (12 raw) → only 4 iterations; response has 4 entries."""
    from lingwen_illustrations import storage

    # Build 4 meta objects so list_assets returns them and helper reaches pipeline.regenerate.
    unique_ids = ["a", "b", "c", "d"]
    meta_by_id = {aid: _make_meta(aid) for aid in unique_ids}

    monkeypatch.setattr(
        storage, "list_assets",
        lambda pr: [meta_by_id[aid] for aid in unique_ids],
    )

    iteration_log = []

    async def fake_regenerate(*args, **kwargs):
        existing_meta = kwargs.get("existing_meta")
        iteration_log.append(existing_meta.id)
        return IllustrationMetadata(
            id=existing_meta.id,
            type=existing_meta.type,
            project_slug=existing_meta.project_slug,
            chapter_num=existing_meta.chapter_num,
            style_preset=existing_meta.style_preset,
            custom_prompt=existing_meta.custom_prompt,
            scene_json=existing_meta.scene_json,
            final_prompt=existing_meta.final_prompt,
            prompt_hash=existing_meta.prompt_hash,
            model=existing_meta.model,
            provider=existing_meta.provider,
            used_reference_image=False,
            created_at="2026-09-22T10:00:00Z",
        )

    monkeypatch.setattr(
        "lingwen_illustrations.pipeline.regenerate_illustration",
        fake_regenerate,
    )
    monkeypatch.setattr(notifications, "record_success", lambda *a, **kw: None)
    monkeypatch.setattr(notifications, "publish", lambda ev: None)
    monkeypatch.setattr(audit_log, "record_event", lambda *a, **kw: None)

    monkeypatch.setattr(
        illus_module,
        "project_root_for",
        lambda slug: tmp_path if slug == "test-slug" else (_ for _ in ()).throw(
            LoadError(f"project {slug} not found")
        ),
    )

    client = TestClient(create_app())
    # 12 raw → 4 unique after dedupe.
    resp = client.put("/api/illustrations?slug=test-slug&ids=a,a,b,b,b,c,d,d,d,d,d,d")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["summary"]["total"] == 4  # dedupe silently
    assert len(body["regenerated"]) == 4
    assert iteration_log == ["a", "b", "c", "d"]


# ---------- T8: Cross-project implicit-not-found ----------
def test_bulk_regenerate_cross_project_asset_marks_not_found(monkeypatch, tmp_path):
    """T8: slug=test-slug + an asset_id belonging to another project → not_found; not regenerated.

    Storage layer's per-project directory isolation makes the asset lookup fail
    naturally (no asset in this project's storage) → helper returns `not_found`
    per Phase 108 4-path (record_success resets counter as defensive no-op).
    Mirrors Phase 107 T8 + Phase 106 5-path contract.
    """
    from lingwen_illustrations import storage

    # Empty storage for test-slug → all asset_ids return not_found
    monkeypatch.setattr(storage, "list_assets", lambda pr: [])

    captured_success = []
    monkeypatch.setattr(
        notifications,
        "record_success",
        lambda slug, event_type: captured_success.append((slug, event_type)),
    )

    monkeypatch.setattr(
        illus_module,
        "project_root_for",
        lambda slug: tmp_path if slug == "test-slug" else (_ for _ in ()).throw(
            LoadError(f"project {slug} not found")
        ),
    )

    client = TestClient(create_app())
    resp = client.put("/api/illustrations?slug=test-slug&ids=other-project-asset")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["regenerated"] == []
    assert len(body["failed"]) == 1
    assert body["failed"][0]["status"] == "not_found"
    # 404 no-op success: record_success was called
    assert captured_success == [("test-slug", "regeneration")]


# ---------- T9: Audit mode discriminator ----------
def test_bulk_regenerate_audit_log_includes_mode_bulk(monkeypatch, tmp_path):
    """T9: audit_log.record_event extra={'trigger':'manual','mode':'bulk'}."""
    from lingwen_illustrations import storage

    captured = []
    monkeypatch.setattr(audit_log, "record_event", lambda *a, **kw: captured.append(kw))
    monkeypatch.setattr(notifications, "record_success", lambda *a, **kw: None)
    monkeypatch.setattr(notifications, "publish", lambda ev: None)
    monkeypatch.setattr(notifications, "new_event_id", lambda: "test-ulid")

    meta = _make_meta("a")
    storage.save_asset(tmp_path, b"\xff\xd8\xff\xe0fake-jpeg", meta)

    async def fake_regenerate(*args, **kwargs):
        existing_meta = kwargs.get("existing_meta")
        return IllustrationMetadata(
            id=existing_meta.id,
            type=existing_meta.type,
            project_slug=existing_meta.project_slug,
            chapter_num=existing_meta.chapter_num,
            style_preset=existing_meta.style_preset,
            custom_prompt=existing_meta.custom_prompt,
            scene_json=existing_meta.scene_json,
            final_prompt=existing_meta.final_prompt,
            prompt_hash=existing_meta.prompt_hash,
            model=existing_meta.model,
            provider=existing_meta.provider,
            used_reference_image=False,
            created_at="2026-09-22T10:00:00Z",
        )

    monkeypatch.setattr(
        "lingwen_illustrations.pipeline.regenerate_illustration",
        fake_regenerate,
    )

    monkeypatch.setattr(
        illus_module,
        "project_root_for",
        lambda slug: tmp_path if slug == "test-slug" else (_ for _ in ()).throw(
            LoadError(f"project {slug} not found")
        ),
    )

    client = TestClient(create_app())
    resp = client.put("/api/illustrations?slug=test-slug&ids=a")
    assert resp.status_code == 200, resp.text
    assert len(captured) == 1
    assert captured[0].get("extra") == {"trigger": "manual", "mode": "bulk"}


# ---------- T10: Threshold crossing ----------
def test_bulk_regenerate_threshold_crossing_emits_one_warning(monkeypatch, tmp_path):
    """T10: 5 consecutive GenerateError → threshold=3 → exactly 1 severity=warning notification.

    Phase 104 tuple-keyed counter + Phase 102 idempotent _warning_emitted flag:
    even with 5 sequential failures, exactly ONE severity=warning notification
    fires per (slug, "regeneration") pair. Mirrors Phase 107 T10 with
    event_type="regeneration" + IllustrationError (not StoreError).
    """
    from lingwen_illustrations import storage

    # Phase 106 pattern: pre-seed counter state, don't mock record_failure
    # (counter would never increment). Use a unique slug to isolate from
    # other tests' state.
    notifications._consecutive_failures[("test-slug-t10", "regeneration")] = 0
    notifications._warning_emitted[("test-slug-t10", "regeneration")] = False

    captured_publishes = []
    monkeypatch.setattr(notifications, "publish", lambda ev: captured_publishes.append(ev))
    monkeypatch.setattr(audit_log, "record_event", lambda *a, **kw: None)

    # Force threshold=3 via settings.yaml (resolve_threshold reads it).
    settings_path = tmp_path / ".lingwen" / "illustration_settings.yaml"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text("notify_threshold:\n  regeneration: 3\n", encoding="utf-8")

    # Bootstrap 5 assets so each iteration reaches pipeline.regenerate_illustration.
    for i in range(5):
        meta = _make_meta(f"a-{i}", project_slug="test-slug-t10")
        storage.save_asset(tmp_path, b"\xff\xd8\xff\xe0fake-jpeg", meta)

    async def fake_regenerate(*args, **kwargs):
        existing_meta = kwargs.get("existing_meta")
        raise GenerateError(f"fail {existing_meta.id}")

    monkeypatch.setattr(
        "lingwen_illustrations.pipeline.regenerate_illustration",
        fake_regenerate,
    )
    monkeypatch.setattr(
        illus_module,
        "project_root_for",
        lambda slug: tmp_path if slug == "test-slug-t10" else (_ for _ in ()).throw(
            LoadError(f"project {slug} not found")
        ),
    )

    client = TestClient(create_app())
    ids = ",".join(f"a-{i}" for i in range(5))
    resp = client.put(f"/api/illustrations?slug=test-slug-t10&ids={ids}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["summary"] == {"total": 5, "ok": 0, "fail": 5}
    # Phase 102 idempotent flag: exactly 1 warning despite 5 failures
    warnings = [
        e for e in captured_publishes
        if e.event_type == "regeneration" and e.severity == "warning"
    ]
    assert len(warnings) == 1


# ---------- T11: UnknownModelError → unknown_model status (no counter increment) ----------
def test_bulk_regenerate_unknown_model_status_no_counter(monkeypatch, tmp_path):
    """T11: Phase 108 NEW per-asset status 'unknown_model' (Phase 107 has no equivalent).

    UnknownModelError is a USER input error (model not in adapter.models), so:
      - failed[].status == "unknown_model"
      - NO record_failure call (counter is for runtime failures, not config bugs)
      - NO record_success call (only not_found triggers defensive record_success)

    Only 2 assets so the test is fast.
    """
    from lingwen_illustrations import storage

    captured_success, captured_failure = [], []

    monkeypatch.setattr(
        notifications,
        "record_success",
        lambda slug, event_type: captured_success.append((slug, event_type)),
    )
    monkeypatch.setattr(
        notifications,
        "record_failure",
        lambda slug, err, *, project_root, threshold, event_type: captured_failure.append(
            (slug, str(err), project_root, event_type)
        ),
    )
    monkeypatch.setattr(audit_log, "record_event", lambda *a, **kw: None)
    monkeypatch.setattr(notifications, "publish", lambda ev: None)

    # Pre-populate 2 assets
    asset_ids = []
    for i in range(2):
        meta = _make_meta(f"asset-{i}")
        storage.save_asset(tmp_path, b"\xff\xd8\xff\xe0fake-jpeg", meta)
        asset_ids.append(meta.id)

    async def fake_regenerate(*args, **kwargs):
        raise UnknownModelError("minimax", "nonexistent-model", ["minimax-image-01"])

    monkeypatch.setattr(
        "lingwen_illustrations.pipeline.regenerate_illustration",
        fake_regenerate,
    )
    monkeypatch.setattr(
        illus_module,
        "project_root_for",
        lambda slug: tmp_path if slug == "test-slug" else (_ for _ in ()).throw(
            LoadError(f"project {slug} not found")
        ),
    )

    client = TestClient(create_app())
    resp = client.put(f"/api/illustrations?slug=test-slug&ids={','.join(asset_ids)}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["regenerated"] == []
    assert len(body["failed"]) == 2
    assert all(f["status"] == "unknown_model" for f in body["failed"])
    assert body["summary"] == {"total": 2, "ok": 0, "fail": 2}

    # No counter increment: UnknownModelError is a user-input error, not runtime failure
    assert captured_failure == []
    # No no-op success either: only not_found triggers defensive record_success
    assert captured_success == []


# ---------- T12: meta_by_id pre-resolved once (Phase 107 invariant preserved) ----------
def test_bulk_regenerate_meta_by_id_pre_resolved(monkeypatch, tmp_path):
    """T12: storage.list_assets called exactly once per request (not per asset).

    Mirrors Phase 107 T11 invariant. bulk_regenerate performs LLM API calls
    per asset (5-30s each), so O(N×M) filesystem lookups would compound with
    the LLM cost. This guard catches any regression to per-asset list_assets.
    """
    from lingwen_illustrations import storage

    list_call_count = [0]
    original_list_assets = storage.list_assets

    def counting_list_assets(*args, **kwargs):
        list_call_count[0] += 1
        return original_list_assets(*args, **kwargs)

    monkeypatch.setattr(storage, "list_assets", counting_list_assets)

    # Pre-populate 3 assets
    asset_ids = []
    for i in range(3):
        meta = _make_meta(f"asset-{i}")
        storage.save_asset(tmp_path, b"\xff\xd8\xff\xe0fake-jpeg", meta)
        asset_ids.append(meta.id)

    async def fake_regenerate(*args, **kwargs):
        existing_meta = kwargs.get("existing_meta")
        return IllustrationMetadata(
            id=existing_meta.id,
            type=existing_meta.type,
            project_slug=existing_meta.project_slug,
            chapter_num=existing_meta.chapter_num,
            style_preset=existing_meta.style_preset,
            custom_prompt=existing_meta.custom_prompt,
            scene_json=existing_meta.scene_json,
            final_prompt=existing_meta.final_prompt,
            prompt_hash=existing_meta.prompt_hash,
            model=existing_meta.model,
            provider=existing_meta.provider,
            used_reference_image=False,
            created_at="2026-09-22T10:00:00Z",
        )

    monkeypatch.setattr(
        "lingwen_illustrations.pipeline.regenerate_illustration",
        fake_regenerate,
    )
    monkeypatch.setattr(
        illus_module,
        "project_root_for",
        lambda slug: tmp_path if slug == "test-slug" else (_ for _ in ()).throw(
            LoadError(f"project {slug} not found")
        ),
    )
    monkeypatch.setattr(notifications, "record_success", lambda *a, **kw: None)
    monkeypatch.setattr(notifications, "publish", lambda ev: None)
    monkeypatch.setattr(audit_log, "record_event", lambda *a, **kw: None)

    client = TestClient(create_app())
    resp = client.put(f"/api/illustrations?slug=test-slug&ids={','.join(asset_ids)}")
    assert resp.status_code == 200, resp.text
    # meta_by_id pre-resolved once before loop (not per-asset)
    assert list_call_count[0] == 1
