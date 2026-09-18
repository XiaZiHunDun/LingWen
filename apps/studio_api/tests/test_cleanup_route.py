"""POST /api/projects/{slug}/illustrations/cleanup tests (Phase 98)."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.studio_api.app import create_app


def _setup_project(slug: str, tmp_path: Path) -> None:
    """Create a minimal project structure with N assets."""
    project_root = tmp_path / "projects" / slug
    (project_root / ".lingwen").mkdir(parents=True)
    (project_root / ".lingwen" / "illustration_settings.yaml").write_text(
        "max_assets: 2\n", encoding="utf-8"
    )
    from lingwen_illustrations.metadata import IllustrationMetadata
    from lingwen_illustrations.storage import save_asset

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


def test_cleanup_endpoint_success(tmp_path, monkeypatch):
    """POST /cleanup with default body deletes oldest assets."""
    slug = "test-cleanup-success"
    _setup_project(slug, tmp_path)

    # Patch project_root_for to return our tmp_path structure
    def fake_root_for(s):
        return tmp_path / "projects" / s

    from apps.studio_api.routes import _project_helpers
    monkeypatch.setattr(_project_helpers, "project_root_for", fake_root_for)

    app = create_app()
    client = TestClient(app)

    response = client.post(f"/api/projects/{slug}/illustrations/cleanup", json={"type": "cover"})
    assert response.status_code == 200
    data = response.json()
    assert "deleted" in data
    assert "remaining" in data
    assert data["dry_run"] is False


def test_cleanup_endpoint_dry_run(tmp_path, monkeypatch):
    """dry_run=true returns what would be deleted without actually deleting."""
    slug = "test-cleanup-dry-run"
    _setup_project(slug, tmp_path)

    def fake_root_for(s):
        return tmp_path / "projects" / s

    from apps.studio_api.routes import _project_helpers
    monkeypatch.setattr(_project_helpers, "project_root_for", fake_root_for)

    app = create_app()
    client = TestClient(app)

    response = client.post(
        f"/api/projects/{slug}/illustrations/cleanup",
        json={"type": "cover", "dry_run": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["dry_run"] is True
    assert len(data["deleted"]) > 0

    # Verify files still exist (dry_run doesn't delete)
    from lingwen_illustrations.storage import list_assets
    remaining = list_assets(tmp_path / "projects" / slug)
    assert len(remaining) == 3  # original 3


def test_cleanup_endpoint_invalid_type(tmp_path, monkeypatch):
    """Invalid type returns 422."""
    slug = "test-cleanup-bad"
    _setup_project(slug, tmp_path)

    def fake_root_for(s):
        return tmp_path / "projects" / s

    from apps.studio_api.routes import _project_helpers
    monkeypatch.setattr(_project_helpers, "project_root_for", fake_root_for)

    app = create_app()
    client = TestClient(app)

    response = client.post(
        f"/api/projects/{slug}/illustrations/cleanup",
        json={"type": "invalid"},
    )
    assert response.status_code == 422


def test_cleanup_endpoint_chapter_requires_num(tmp_path, monkeypatch):
    """type=chapter without chapter_num returns 422."""
    slug = "test-cleanup-chapter-no-num"
    _setup_project(slug, tmp_path)

    def fake_root_for(s):
        return tmp_path / "projects" / s

    from apps.studio_api.routes import _project_helpers
    monkeypatch.setattr(_project_helpers, "project_root_for", fake_root_for)

    app = create_app()
    client = TestClient(app)

    response = client.post(
        f"/api/projects/{slug}/illustrations/cleanup",
        json={"type": "chapter"},
    )
    assert response.status_code == 422


def test_cleanup_endpoint_404_for_missing_project(monkeypatch):
    """Missing project returns 404."""
    from lingwen_illustrations.exceptions import LoadError

    def fake_root(slug):
        raise LoadError(f"project not found: {slug}")

    from apps.studio_api.routes import _project_helpers
    monkeypatch.setattr(_project_helpers, "project_root_for", fake_root)

    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/projects/missing-project/illustrations/cleanup",
        json={"type": "cover"},
    )
    assert response.status_code == 404
