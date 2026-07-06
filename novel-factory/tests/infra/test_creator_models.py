"""Tests for creator_models."""
from __future__ import annotations

from infra.creator_models import list_creator_models, list_creator_models_payload


def test_list_creator_models_includes_mock() -> None:
    models = list_creator_models()
    ids = {m["id"] for m in models}
    assert "local-mock" in ids
    assert all("available" in m for m in models)


def test_list_creator_models_payload_shape() -> None:
    payload = list_creator_models_payload()
    assert "models" in payload
    assert "default_model" in payload
