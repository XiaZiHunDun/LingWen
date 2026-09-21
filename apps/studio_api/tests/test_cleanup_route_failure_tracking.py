"""Phase 105 — cleanup_route failure tracking tests.

6 NEW tests (T1-T6) covering:
- T1: LoadError (404) -> record_failure called with event_type="cleanup", project_root=None
- T2: StoreError on lru_cleanup -> record_failure called with event_type="cleanup", project_root=real
- T3: Successful cleanup -> record_success called (reset counter)
- T4: 422 validation (chapter_num missing) -> NO record_failure called
- T5: dry_run path -> NO record_failure / record_success called
- T6: Threshold crossing after N consecutive StoreErrors -> 1 severity=warning notification

These tests verify Phase 105 wiring without modifying behavior.
Each test uses a unique slug to avoid in-memory counter bleed.

Monkeypatch note: cleanup_route uses `from ... import X` for project_root_for
and lru_cleanup (local bindings). Patching the source module attribute does
NOT affect cleanup_route's local binding. Tests patch cleanup_route.X directly.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.studio_api.app import create_app
from apps.studio_api.routes import cleanup_route


def _setup_project(slug: str, tmp_path: Path, max_assets: int = 2) -> Path:
    """Create minimal project; return project_root path."""
    project_root = tmp_path / "projects" / slug
    (project_root / ".lingwen").mkdir(parents=True)
    (project_root / ".lingwen" / "illustration_settings.yaml").write_text(
        f"max_assets: {max_assets}\n", encoding="utf-8"
    )
    return project_root


def _setup_project_with_settings(slug: str, tmp_path: Path, settings_yaml: str) -> Path:
    """Create project with custom settings yaml."""
    project_root = tmp_path / "projects" / slug
    (project_root / ".lingwen").mkdir(parents=True)
    (project_root / ".lingwen" / "illustration_settings.yaml").write_text(
        settings_yaml, encoding="utf-8"
    )
    return project_root


def test_t1_load_error_triggers_record_failure_with_none_root(
    tmp_path, monkeypatch
):
    """404 LoadError path: record_failure called with event_type='cleanup', project_root=None."""
    from lingwen_illustrations import notifications
    from lingwen_illustrations.exceptions import LoadError

    calls: list[dict] = []
    real_record_failure = notifications.record_failure

    def spy_record_failure(slug, error, *, project_root, threshold, event_type):
        calls.append({
            "slug": slug, "error": error,
            "project_root": project_root, "threshold": threshold,
            "event_type": event_type,
        })
        return real_record_failure(
            slug, error,
            project_root=project_root, threshold=threshold,
            event_type=event_type,
        )

    def fake_root(slug):
        raise LoadError(f"project not found: {slug}")

    # Patch cleanup_route's local binding (not _project_helpers)
    monkeypatch.setattr(cleanup_route, "project_root_for", fake_root)
    monkeypatch.setattr(notifications, "record_failure", spy_record_failure)

    app = create_app()
    client = TestClient(app)
    response = client.post(
        "/api/projects/phase105-t1/illustrations/cleanup",
        json={"type": "cover"},
    )
    assert response.status_code == 404

    assert len(calls) == 1
    call = calls[0]
    assert call["slug"] == "phase105-t1"
    assert call["event_type"] == "cleanup"
    assert call["project_root"] is None  # No real project context for LoadError
    import math
    assert call["threshold"] == math.inf


def test_t2_store_error_triggers_record_failure_with_real_root(
    tmp_path, monkeypatch
):
    """StoreError on lru_cleanup: record_failure called with event_type='cleanup', project_root=real root."""
    from lingwen_illustrations import notifications
    from lingwen_illustrations.exceptions import StoreError

    slug = "phase105-t2"
    project_root = _setup_project(slug, tmp_path)

    calls: list[dict] = []
    real_record_failure = notifications.record_failure

    def spy_record_failure(slug, error, *, project_root, threshold, event_type):
        calls.append({
            "slug": slug, "error": error,
            "project_root": project_root, "threshold": threshold,
            "event_type": event_type,
        })
        return real_record_failure(
            slug, error,
            project_root=project_root, threshold=threshold,
            event_type=event_type,
        )

    def fake_lru_cleanup(*args, **kwargs):
        raise StoreError("simulated store failure")

    # Patch cleanup_route's local bindings (not source module)
    monkeypatch.setattr(cleanup_route, "project_root_for", lambda s: project_root)
    monkeypatch.setattr(cleanup_route, "lru_cleanup", fake_lru_cleanup)
    monkeypatch.setattr(notifications, "record_failure", spy_record_failure)

    app = create_app()
    client = TestClient(app)
    response = client.post(
        f"/api/projects/{slug}/illustrations/cleanup",
        json={"type": "cover"},
    )
    assert response.status_code == 422

    assert len(calls) == 1
    call = calls[0]
    assert call["slug"] == slug
    assert call["event_type"] == "cleanup"
    assert call["project_root"] == project_root  # Real root, not None
    # Threshold may be int (configured) or float (INFINITY for missing key)
    assert isinstance(call["threshold"], (int, float))


def test_t3_successful_cleanup_resets_counter(tmp_path, monkeypatch):
    """Successful lru_cleanup: record_success called for event_type='cleanup'."""
    from lingwen_illustrations import notifications
    from lingwen_illustrations.metadata import IllustrationMetadata
    from lingwen_illustrations.storage import save_asset

    slug = "phase105-t3"
    project_root = _setup_project(slug, tmp_path)

    for i, dt in enumerate([
        "2026-09-01T00:00:00+00:00",
        "2026-09-02T00:00:00+00:00",
        "2026-09-03T00:00:00+00:00",
    ]):
        meta = IllustrationMetadata(
            id=f"cover-{i}",
            type="cover",
            project_slug=slug,
            chapter_num=None,
            style_preset="ink",
            custom_prompt=None,
            scene_json={"scene": f"scene-{i}"},
            final_prompt=f"final-prompt-{i}",
            prompt_hash=f"hash-{i}",
            model="minimax-multimodal",
            created_at=dt,
            provider="minimax",
        )
        save_asset(project_root, b"jpg-bytes", meta)

    success_calls: list[dict] = []
    real_record_success = notifications.record_success

    def spy_record_success(slug, event_type):
        success_calls.append({"slug": slug, "event_type": event_type})
        return real_record_success(slug, event_type=event_type)

    monkeypatch.setattr(cleanup_route, "project_root_for", lambda s: project_root)
    monkeypatch.setattr(notifications, "record_success", spy_record_success)

    app = create_app()
    client = TestClient(app)
    response = client.post(
        f"/api/projects/{slug}/illustrations/cleanup",
        json={"type": "cover"},
    )
    assert response.status_code == 200

    assert len(success_calls) == 1
    assert success_calls[0]["slug"] == slug
    assert success_calls[0]["event_type"] == "cleanup"


def test_t4_validation_422_does_not_track_failure(tmp_path, monkeypatch):
    """422 validation (chapter_num missing): NO record_failure called."""
    from lingwen_illustrations import notifications

    slug = "phase105-t4"
    project_root = _setup_project(slug, tmp_path)

    failure_calls: list[dict] = []

    def spy_record_failure(slug, error, *, project_root, threshold, event_type):
        failure_calls.append({"event_type": event_type})
        return None

    monkeypatch.setattr(cleanup_route, "project_root_for", lambda s: project_root)
    monkeypatch.setattr(notifications, "record_failure", spy_record_failure)

    app = create_app()
    client = TestClient(app)
    response = client.post(
        f"/api/projects/{slug}/illustrations/cleanup",
        json={"type": "chapter"},
    )
    assert response.status_code == 422
    assert len(failure_calls) == 0


def test_t5_dry_run_does_not_track_failure_or_success(tmp_path, monkeypatch):
    """dry_run path: NO record_failure / record_success called."""
    from lingwen_illustrations import notifications
    from lingwen_illustrations.metadata import IllustrationMetadata
    from lingwen_illustrations.storage import save_asset

    slug = "phase105-t5"
    project_root = _setup_project(slug, tmp_path)

    for i, dt in enumerate([
        "2026-09-01T00:00:00+00:00",
        "2026-09-02T00:00:00+00:00",
        "2026-09-03T00:00:00+00:00",
    ]):
        meta = IllustrationMetadata(
            id=f"cover-{i}",
            type="cover",
            project_slug=slug,
            chapter_num=None,
            style_preset="ink",
            custom_prompt=None,
            scene_json={"scene": f"scene-{i}"},
            final_prompt=f"final-prompt-{i}",
            prompt_hash=f"hash-{i}",
            model="minimax-multimodal",
            created_at=dt,
            provider="minimax",
        )
        save_asset(project_root, b"jpg-bytes", meta)

    failure_calls: list[dict] = []
    success_calls: list[dict] = []

    def spy_record_failure(slug, error, *, project_root, threshold, event_type):
        failure_calls.append({"event_type": event_type})
        return None

    def spy_record_success(slug, event_type):
        success_calls.append({"event_type": event_type})
        return None

    monkeypatch.setattr(cleanup_route, "project_root_for", lambda s: project_root)
    monkeypatch.setattr(notifications, "record_failure", spy_record_failure)
    monkeypatch.setattr(notifications, "record_success", spy_record_success)

    app = create_app()
    client = TestClient(app)
    response = client.post(
        f"/api/projects/{slug}/illustrations/cleanup",
        json={"type": "cover", "dry_run": True},
    )
    assert response.status_code == 200
    assert len(failure_calls) == 0
    assert len(success_calls) == 0


def test_t6_threshold_crossing_emits_warning_notification(tmp_path, monkeypatch):
    """Threshold crossing after N consecutive StoreErrors -> 1 severity=warning notification."""
    from lingwen_illustrations import notifications
    from lingwen_illustrations.exceptions import StoreError

    slug = "phase105-t6"
    project_root = _setup_project_with_settings(
        slug, tmp_path,
        "max_assets: 5\nnotify_threshold:\n  cleanup: 2\n",
    )

    warnings_published: list[dict] = []
    real_publish = notifications.publish

    def spy_publish(event):
        if event.severity == "warning":
            warnings_published.append({
                "event_type": event.event_type,
                "severity": event.severity,
                "extra": event.extra,
            })
        return real_publish(event)

    def fake_lru_cleanup(*args, **kwargs):
        raise StoreError("simulated failure for t6")

    monkeypatch.setattr(cleanup_route, "project_root_for", lambda s: project_root)
    monkeypatch.setattr(cleanup_route, "lru_cleanup", fake_lru_cleanup)
    monkeypatch.setattr(notifications, "publish", spy_publish)

    app = create_app()
    client = TestClient(app)

    for _ in range(2):
        response = client.post(
            f"/api/projects/{slug}/illustrations/cleanup",
            json={"type": "cover"},
        )
        assert response.status_code == 422

    assert len(warnings_published) == 1
    warning = warnings_published[0]
    assert warning["event_type"] == "cleanup"
    assert warning["severity"] == "warning"
    assert warning["extra"]["consecutive_failures"] >= 2
