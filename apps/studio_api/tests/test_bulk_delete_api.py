"""Phase 107: T1-T10 bulk delete endpoint tests.

T1-T10 are RED until Commit 5 wires bulk_delete_assets + the _delete_asset_inner
helper extracted in Commit 4. Each test exercises one path in the per-asset
failure tracking contract (I090/I091/I095) via the new
``DELETE /api/illustrations?slug=...&ids=...`` route.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from lingwen_illustrations import audit_log, notifications
from lingwen_illustrations.exceptions import LoadError, StoreError
from lingwen_illustrations.metadata import IllustrationMetadata

from apps.studio_api.app import create_app
from apps.studio_api.routes import illustrations as illus_module


def _make_meta(asset_id: str, project_slug: str = "test-slug") -> "IllustrationMetadata":
    """Build a minimal valid IllustrationMetadata for storage.save_asset bootstrap."""
    from lingwen_illustrations.metadata import IllustrationMetadata

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


# ---------- T1: Happy path ----------
def test_bulk_delete_happy_path_records_per_asset(monkeypatch, tmp_path):
    """T1: 5 assets all in storage; expect 5× record_success + 5× audit + 5× publish."""
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

    # Mock storage.delete_asset to always succeed.
    monkeypatch.setattr(storage, "delete_asset", lambda pr, m: None)

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

    # Audit extra={"trigger":"manual","mode":"bulk"} — same ULID between audit and publish.
    for _, kwargs in captured_audit:
        assert kwargs.get("extra") == {"trigger": "manual", "mode": "bulk"}

    # I091: same ULID for audit + publish pair
    for i in range(5):
        assert captured_audit[i][1]["id"] == captured_publish[i].id

    # Phase 107 M3: verify 5 distinct ULIDs (per-asset semantics, not single batched)
    assert len({a[1]["id"] for a in captured_audit}) == 5


# ---------- T2: Partial failure ----------
def test_bulk_delete_partial_failure_records_failure_per_asset(monkeypatch, tmp_path):
    """T2: 5 assets; 3 storage success + 2 StoreError. Expect 3× record_success + 2× record_failure."""
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

    def fake_delete(pr, meta):
        if meta.id in ("asset-1", "asset-3"):
            raise StoreError(f"failed to delete {meta.id}")
        return None

    monkeypatch.setattr(storage, "delete_asset", fake_delete)
    monkeypatch.setattr(
        illus_module,
        "project_root_for",
        lambda slug: tmp_path if slug == "test-slug" else (_ for _ in ()).throw(
            LoadError(f"project {slug} not found")
        ),
    )

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
def test_bulk_delete_empty_ids_returns_422(monkeypatch, tmp_path):
    """T3: ids= (empty) → 422."""
    monkeypatch.setattr(
        illus_module,
        "project_root_for",
        lambda slug: tmp_path if slug == "test-slug" else (_ for _ in ()).throw(
            LoadError(f"project {slug} not found")
        ),
    )

    client = TestClient(create_app())
    resp = client.delete("/api/illustrations?slug=test-slug&ids=")
    assert resp.status_code == 422


# ---------- T4: Over 50 ids ----------
def test_bulk_delete_over_50_ids_returns_422(monkeypatch, tmp_path):
    """T4: 51 unique ids → 422."""
    monkeypatch.setattr(
        illus_module,
        "project_root_for",
        lambda slug: tmp_path if slug == "test-slug" else (_ for _ in ()).throw(
            LoadError(f"project {slug} not found")
        ),
    )

    client = TestClient(create_app())
    ids_csv = ",".join(f"a-{i}" for i in range(51))
    resp = client.delete(f"/api/illustrations?slug=test-slug&ids={ids_csv}")
    assert resp.status_code == 422


# ---------- T5: Slug not found ----------
def test_bulk_delete_slug_not_found_returns_404(monkeypatch, tmp_path):
    """T5: slug does not resolve → 404 (no iteration)."""
    monkeypatch.setattr(
        illus_module,
        "project_root_for",
        lambda slug: (_ for _ in ()).throw(LoadError(f"project {slug} not found")),
    )

    client = TestClient(create_app())
    resp = client.delete("/api/illustrations?slug=missing-slug&ids=a,b")
    assert resp.status_code == 404


# ---------- T6: LoadError upstream — endpoint must raise 404 before iteration ----------
def test_bulk_delete_load_error_returns_404_no_iteration(monkeypatch, tmp_path):
    """T6: project_root_for raises LoadError → 404 (no record_failure on this path).

    The endpoint catches LoadError and raises 404 directly; the per-asset helper
    is NOT invoked in the failure path (404 is pre-iteration, not per-asset).
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
    resp = client.delete("/api/illustrations?slug=missing-slug&ids=a,b,c")
    # T6: endpoint catches LoadError → 404 (NOT 200 with all in failed[])
    assert resp.status_code == 404
    # Endpoint should raise before calling the per-asset helper
    assert len(captured_failure) == 0


# ---------- T7: Dedupe ----------
def test_bulk_delete_dedupes_ids(monkeypatch, tmp_path):
    """T7: ids="a,a,b,b,b,c,d,d" (8 raw) → only 4 iterations; response has 4 entries."""
    from lingwen_illustrations import storage

    # Build 4 meta objects so list_assets returns them and helper reaches delete_asset.
    unique_ids = ["a", "b", "c", "d"]
    meta_by_id = {aid: _make_meta(aid) for aid in unique_ids}

    monkeypatch.setattr(
        storage, "list_assets",
        lambda pr: [meta_by_id[aid] for aid in unique_ids],
    )

    iteration_log = []
    monkeypatch.setattr(storage, "delete_asset", lambda pr, m: iteration_log.append(m.id) or None)
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
    resp = client.delete("/api/illustrations?slug=test-slug&ids=a,a,b,b,b,c,d,d")
    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"]["total"] == 4  # dedupe silently
    assert iteration_log == ["a", "b", "c", "d"]


# ---------- T8: Cross-project implicit-not-found ----------
def test_bulk_delete_cross_project_asset_marks_not_found(monkeypatch, tmp_path):
    """T8: slug=test-slug + an asset_id belonging to another project → not_found; not deleted.

    Storage layer's per-project directory isolation makes the asset lookup fail
    naturally (no asset in this project's storage) → helper returns `not_found`
    per Phase 106 5-path (record_success resets counter).
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
    resp = client.delete("/api/illustrations?slug=test-slug&ids=other-project-asset")
    assert resp.status_code == 200
    body = resp.json()
    assert body["deleted"] == []
    assert len(body["failed"]) == 1
    assert body["failed"][0]["status"] == "not_found"
    # 404 no-op success: record_success was called
    assert captured_success == [("test-slug", "deletion")]


# ---------- T9: Audit mode discriminator ----------
def test_bulk_delete_audit_log_includes_mode_bulk(monkeypatch, tmp_path):
    """T9: audit_log.record_event extra={'trigger':'manual','mode':'bulk'}."""
    from lingwen_illustrations import storage

    captured = []
    monkeypatch.setattr(audit_log, "record_event", lambda *a, **kw: captured.append(kw))
    monkeypatch.setattr(notifications, "record_success", lambda *a, **kw: None)
    monkeypatch.setattr(notifications, "publish", lambda ev: None)
    monkeypatch.setattr(notifications, "new_event_id", lambda: "test-ulid")

    meta = _make_meta("a")
    storage.save_asset(tmp_path, b"\xff\xd8\xff\xe0fake-jpeg", meta)
    monkeypatch.setattr(storage, "delete_asset", lambda pr, m: None)

    monkeypatch.setattr(
        illus_module,
        "project_root_for",
        lambda slug: tmp_path if slug == "test-slug" else (_ for _ in ()).throw(
            LoadError(f"project {slug} not found")
        ),
    )

    client = TestClient(create_app())
    resp = client.delete("/api/illustrations?slug=test-slug&ids=a")
    assert resp.status_code == 200
    assert len(captured) == 1
    assert captured[0].get("extra") == {"trigger": "manual", "mode": "bulk"}


# ---------- T10: Threshold crossing ----------
def test_bulk_delete_threshold_crossing_emits_one_warning(monkeypatch, tmp_path):
    """T10: 5 consecutive StoreError → threshold=3 → exactly 1 severity=warning notification."""
    from lingwen_illustrations import storage

    # Phase 106 pattern: pre-seed counter state, don't mock record_failure (counter
    # would never increment). Use a unique slug to isolate from other tests' state.
    notifications._consecutive_failures[("test-slug-t10", "deletion")] = 0
    notifications._warning_emitted[("test-slug-t10", "deletion")] = False

    captured_publishes = []
    monkeypatch.setattr(notifications, "publish", lambda ev: captured_publishes.append(ev))
    monkeypatch.setattr(audit_log, "record_event", lambda *a, **kw: None)

    # Force threshold=3 via settings.yaml (resolve_threshold reads it).
    settings_path = tmp_path / ".lingwen" / "illustration_settings.yaml"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text("notify_threshold:\n  deletion: 3\n", encoding="utf-8")

    # Bootstrap 5 assets so each iteration reaches storage.delete_asset.
    for i in range(5):
        meta = IllustrationMetadata(
            id=f"a-{i}",
            type="cover",
            project_slug="test-slug-t10",
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
        storage.save_asset(tmp_path, b"\xff\xd8\xff\xe0fake-jpeg", meta)

    monkeypatch.setattr(
        storage,
        "delete_asset",
        lambda pr, m: (_ for _ in ()).throw(StoreError(f"fail {m.id}")),
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
    resp = client.delete(f"/api/illustrations?slug=test-slug-t10&ids={ids}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"] == {"total": 5, "ok": 0, "fail": 5}
    # Phase 102 idempotent flag: exactly 1 warning despite 5 failures
    warnings = [
        e for e in captured_publishes
        if e.event_type == "deletion" and e.severity == "warning"
    ]
    assert len(warnings) == 1


# ---------- T11: I1 perf — bulk pre-resolves meta_by_id ONCE ----------
def test_bulk_delete_calls_list_assets_once_per_request(monkeypatch, tmp_path):
    """T11 (Phase 107 I1): bulk_delete_assets resolves storage.list_assets ONCE,
    not once per asset. O(M+N) reads, not O(N*M).

    Spy on storage.list_assets call count; assert it equals 1 for a 5-asset
    bulk request. Regression guard against the old per-asset pattern that did
    5×M filesystem reads.
    """
    from lingwen_illustrations import storage

    # Pre-populate 5 assets so the per-asset loop has work to do.
    asset_ids = []
    for i in range(5):
        meta = _make_meta(f"asset-{i}")
        storage.save_asset(tmp_path, b"\xff\xd8\xff\xe0fake-jpeg", meta)
        asset_ids.append(meta.id)

    # Spy on list_assets via monkeypatch wrapping.
    list_assets_calls: list[int] = []
    real_list_assets = storage.list_assets

    def spy_list_assets(pr):
        list_assets_calls.append(1)
        return real_list_assets(pr)

    monkeypatch.setattr(storage, "list_assets", spy_list_assets)
    monkeypatch.setattr(storage, "delete_asset", lambda pr, m: None)
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
    ids_csv = ",".join(asset_ids)
    resp = client.delete(f"/api/illustrations?slug=test-slug&ids={ids_csv}")

    assert resp.status_code == 200
    # Phase 107 I1: exactly 1 list_assets call (not 5 from per-asset helper).
    assert len(list_assets_calls) == 1, (
        f"Expected 1 list_assets call for 5-asset bulk, got {len(list_assets_calls)} "
        f"(regression to O(N*M) per-asset lookup)"
    )
