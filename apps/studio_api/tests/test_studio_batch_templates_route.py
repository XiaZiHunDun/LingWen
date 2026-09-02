"""Integration tests for /api/studio/batch/templates (Track B batch templates)."""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.studio_api.routes.studio import register_studio
from infra.studio_batch_templates import BatchTemplate


@pytest.fixture
def app():
    a = FastAPI()
    register_studio(a, ctx=None)
    return a


@pytest.fixture
def client(app):
    return TestClient(app)


def _template(template_id: str = "t1", **overrides) -> BatchTemplate:
    base = dict(
        template_id=template_id,
        slug="my-project",
        name="Daily Pilot",
        start_chapter=1,
        end_chapter=5,
        budget_usd=0.15,
        mode="pilot",
        skip_preflight=False,
        event_types=["job_state", "chapter_completed"],
        description="Pilot the first five chapters",
        created_at="2026-09-02T00:00:00+00:00",
        updated_at="2026-09-02T00:00:00+00:00",
    )
    base.update(overrides)
    return BatchTemplate(**base)


def test_create_template_returns_201(client):
    with (
        patch("infra.studio_registry.get_project_by_slug", return_value=object()),
        patch("infra.studio_batch_templates.create_batch_template", return_value=_template()),
    ):
        resp = client.post(
            "/api/studio/batch/templates",
            json={
                "name": "Daily Pilot",
                "slug": "my-project",
                "start_chapter": 1,
                "end_chapter": 5,
                "mode": "pilot",
                "event_types": ["job_state", "chapter_completed"],
            },
        )
    assert resp.status_code == 201
    payload = resp.json()
    assert payload["template_id"] == "t1"
    assert payload["name"] == "Daily Pilot"
    assert payload["slug"] == "my-project"
    assert payload["event_types"] == ["job_state", "chapter_completed"]


def test_create_template_404_for_unknown_slug(client):
    with (
        patch("infra.studio_registry.get_project_by_slug", return_value=None),
        patch("infra.studio_batch_templates.create_batch_template"),
    ):
        resp = client.post(
            "/api/studio/batch/templates",
            json={"name": "X", "slug": "nope", "start_chapter": 1, "end_chapter": 2},
        )
    assert resp.status_code == 404
    assert "nope" in resp.json()["detail"]


def test_create_template_400_for_unknown_event_type(client):
    with (
        patch("infra.studio_registry.get_project_by_slug", return_value=object()),
        patch("infra.studio_batch_templates.create_batch_template"),
    ):
        resp = client.post(
            "/api/studio/batch/templates",
            json={
                "name": "X",
                "slug": "my-project",
                "start_chapter": 1,
                "end_chapter": 2,
                "event_types": ["bogus"],
            },
        )
    assert resp.status_code == 400
    assert "bogus" in resp.json()["detail"]


def test_create_template_400_for_invalid_preset(client):
    with (
        patch("infra.studio_registry.get_project_by_slug", return_value=object()),
        patch(
            "infra.studio_batch_templates.create_batch_template",
            side_effect=ValueError("end_chapter must be >= start_chapter"),
        ),
    ):
        resp = client.post(
            "/api/studio/batch/templates",
            json={"name": "X", "slug": "my-project", "start_chapter": 5, "end_chapter": 1},
        )
    assert resp.status_code == 400
    assert "end_chapter" in resp.json()["detail"]


def test_create_template_404_when_slug_missing_and_no_active_project(client):
    # No active project; _require_project raises 404 rather than crashing.
    with (
        patch("infra.studio_registry.active_project", return_value=None),
        patch("infra.studio_batch_templates.create_batch_template"),
    ):
        resp = client.post(
            "/api/studio/batch/templates",
            json={"name": "X", "start_chapter": 1, "end_chapter": 2},
        )
    assert resp.status_code == 404


def test_get_template_returns_200(client):
    with patch(
        "infra.studio_batch_templates.get_batch_template",
        return_value=_template().to_dict(),
    ):
        resp = client.get("/api/studio/batch/templates/t1")
    assert resp.status_code == 200
    assert resp.json()["template_id"] == "t1"


def test_get_template_404_for_missing(client):
    with patch("infra.studio_batch_templates.get_batch_template", return_value=None):
        resp = client.get("/api/studio/batch/templates/nope")
    assert resp.status_code == 404
    assert "nope" in resp.json()["detail"]


def test_list_templates_returns_200(client):
    rows = [_template("t1").to_dict(), _template("t2", name="Weekly").to_dict()]
    with patch("infra.studio_batch_templates.list_batch_templates", return_value=rows):
        resp = client.get("/api/studio/batch/templates", params={"slug": "my-project"})
    assert resp.status_code == 200
    payload = resp.json()
    assert len(payload["templates"]) == 2
    assert payload["templates"][0]["template_id"] == "t1"
    assert payload["templates"][1]["name"] == "Weekly"


def test_update_template_returns_200(client):
    with patch(
        "infra.studio_batch_templates.update_batch_template",
        return_value=_template("t1", name="Renamed"),
    ):
        resp = client.put(
            "/api/studio/batch/templates/t1",
            json={"name": "Renamed"},
        )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"


def test_update_template_404_for_missing(client):
    with patch(
        "infra.studio_batch_templates.update_batch_template",
        side_effect=LookupError("batch template not found: nope"),
    ):
        resp = client.put("/api/studio/batch/templates/nope", json={"name": "X"})
    assert resp.status_code == 404


def test_update_template_400_for_unknown_event_type(client):
    with patch("infra.studio_batch_templates.update_batch_template"):
        resp = client.put(
            "/api/studio/batch/templates/t1",
            json={"event_types": ["bad"]},
        )
    assert resp.status_code == 400


def test_delete_template_returns_deleted(client):
    with patch(
        "infra.studio_batch_templates.delete_batch_template",
        return_value=_template("t1"),
    ):
        resp = client.delete("/api/studio/batch/templates/t1")
    assert resp.status_code == 200
    assert resp.json()["template_id"] == "t1"


def test_delete_template_404_for_missing(client):
    with patch(
        "infra.studio_batch_templates.delete_batch_template",
        side_effect=LookupError("batch template not found: nope"),
    ):
        resp = client.delete("/api/studio/batch/templates/nope")
    assert resp.status_code == 404
