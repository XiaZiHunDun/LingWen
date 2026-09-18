"""Reference image route tests (Phase 97)."""
from __future__ import annotations

import io
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.studio_api.routes.ctx import RoutesContext
from apps.studio_api.routes.reference_image import register_reference_image


def _stub_ctx() -> RoutesContext:
    """Minimal RoutesContext — reference_image router doesn't read any field today."""
    return RoutesContext(
        db=None,  # type: ignore[arg-type]
        master_controller=None,
        manager=None,  # type: ignore[arg-type]
        limiter=None,  # type: ignore[arg-type]
        production_records_root=lambda: Path("/tmp"),
        cvg_storage=lambda: None,  # type: ignore[arg-type]
    )


@pytest.fixture
def project_root(tmp_path: Path, monkeypatch) -> Path:
    """Create projects/test-slug under tmp_path + chdir so cwd-relative lookup works."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "projects" / "test-slug").mkdir(parents=True, exist_ok=True)
    return tmp_path / "projects" / "test-slug"


@pytest.fixture
def client(project_root: Path) -> TestClient:
    app = FastAPI()
    register_reference_image(app, _stub_ctx())
    return TestClient(app)


def test_get_returns_404_when_no_reference_image(client):
    response = client.get("/api/projects/test-slug/reference-image")
    assert response.status_code == 404


def test_post_uploads_jpeg(client):
    jpeg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    response = client.post(
        "/api/projects/test-slug/reference-image",
        files={"file": ("test.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["exists"] is True
    assert body["size_bytes"] == len(jpeg_bytes)
    assert body["mime_type"] == "image/jpeg"


def test_post_uploads_png(client):
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    response = client.post(
        "/api/projects/test-slug/reference-image",
        files={"file": ("test.png", io.BytesIO(png_bytes), "image/png")},
    )
    assert response.status_code == 200
    assert response.json()["mime_type"] == "image/png"


def test_post_rejects_unsupported_mime(client):
    response = client.post(
        "/api/projects/test-slug/reference-image",
        files={"file": ("test.gif", io.BytesIO(b"GIF89a"), "image/gif")},
    )
    assert response.status_code == 415


def test_post_rejects_oversize(client):
    big = b"\xff\xd8\xff\xe0" + b"\x00" * (11 * 1024 * 1024)
    response = client.post(
        "/api/projects/test-slug/reference-image",
        files={"file": ("big.jpg", io.BytesIO(big), "image/jpeg")},
    )
    assert response.status_code == 413


def test_get_returns_info_after_upload(client):
    jpeg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    client.post(
        "/api/projects/test-slug/reference-image",
        files={"file": ("test.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")},
    )
    response = client.get("/api/projects/test-slug/reference-image")
    assert response.status_code == 200
    assert response.json()["exists"] is True


def test_delete_returns_deleted_false_when_no_image(client):
    response = client.delete("/api/projects/test-slug/reference-image")
    assert response.status_code == 200
    assert response.json()["deleted"] is False


def test_delete_returns_deleted_true_when_image_exists(client):
    jpeg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    client.post(
        "/api/projects/test-slug/reference-image",
        files={"file": ("test.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")},
    )
    response = client.delete("/api/projects/test-slug/reference-image")
    assert response.status_code == 200
    assert response.json()["deleted"] is True


def test_unknown_project_returns_404(monkeypatch):
    """When project_root_for raises LoadError, return 404."""
    from lingwen_illustrations.exceptions import LoadError

    from apps.studio_api.routes import _project_helpers

    def mock_root_for(slug):
        raise LoadError(f"project {slug} not found")

    monkeypatch.setattr(_project_helpers, "project_root_for", mock_root_for)

    app = FastAPI()
    register_reference_image(app, _stub_ctx())
    test_client = TestClient(app)
    response = test_client.get("/api/projects/missing/reference-image")
    assert response.status_code == 404
