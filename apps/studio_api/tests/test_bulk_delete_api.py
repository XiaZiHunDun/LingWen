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

from apps.studio_api.app import create_app
from apps.studio_api.routes import illustrations as illus_module
from lingwen_illustrations import audit_log, notifications
from lingwen_illustrations.exceptions import LoadError, StoreError


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


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create FastAPI test client with project_root_for patched to tmp_path.

    The patch is scoped to the `illus_module` binding, which is what the
    route handler uses (per Phase 106 tests at line 907).
    """
    from lingwen_illustrations import storage

    # Pre-create the assets directory so list_assets works on a real project.
    (tmp_path / "assets").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        illus_module,
        "project_root_for",
        lambda slug: tmp_path if slug == "test-slug" else (_ for _ in ()).throw(
            LoadError(f"project {slug} not found")
        ),
    )
    return TestClient(create_app())


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

    captured_warnings = []
    monkeypatch.setattr(
        notifications,
        "_emit_failure_warning",
        lambda slug, et, threshold: captured_warnings.append((slug, et, threshold)),
    )
    monkeypatch.setattr(
        notifications,
        "record_failure",
        lambda slug, err, *, project_root, threshold, event_type: None,
    )
    monkeypatch.setattr(notifications, "resolve_threshold", lambda settings, et: 3)
    monkeypatch.setattr(audit_log, "record_event", lambda *a, **kw: None)
    monkeypatch.setattr(notifications, "publish", lambda ev: None)

    # Pre-populate so list_assets finds them and we reach storage.delete_asset.
    for i in range(5):
        meta = _make_meta(f"a-{i}")
        storage.save_asset(tmp_path, b"\xff\xd8\xff\xe0fake-jpeg", meta)

    monkeypatch.setattr(
        storage,
        "delete_asset",
        lambda pr, m: (_ for _ in ()).throw(StoreError(f"fail {m.id}")),
    )
    monkeypatch.setattr(
        illus_module,
        "project_root_for",
        lambda slug: tmp_path if slug == "test-slug" else (_ for _ in ()).throw(
            LoadError(f"project {slug} not found")
        ),
    )

    client = TestClient(create_app())
    ids = ",".join(f"a-{i}" for i in range(5))
    resp = client.delete(f"/api/illustrations?slug=test-slug&ids={ids}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"] == {"total": 5, "ok": 0, "fail": 5}
    # Exactly 1 warning emission despite 5 failures (Phase 102 _warning_emitted idempotent flag)
    assert len(captured_warnings) == 1
    assert captured_warnings[0] == ("test-slug", "deletion", 3)
