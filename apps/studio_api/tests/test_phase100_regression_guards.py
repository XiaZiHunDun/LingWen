"""Phase 100: Multi-Model Per Provider regression guards.

G1-G9 verify spec invariants that should never regress:
- 11 models declared across 3 providers
- ProviderAdapter has new fields
- UnknownModelError exists
- pipeline.resolve_model function exists
- settings yaml accepts default_models
- illustration route accepts model
- GET /providers/{name}/models endpoint registered
- IllustrationMetadata.model records resolved value
- I092 invariant recorded in architecture.yml
"""
from __future__ import annotations

import inspect
from pathlib import Path

import pytest
import yaml


def test_g1_known_models_count():
    """11 total: OpenAI 4 + Stability 5 + MiniMax 2."""
    from lingwen_illustrations.providers import minimax, openai, stability

    assert len(minimax.KNOWN_MODELS) == 2
    assert len(openai.KNOWN_MODELS) == 4
    assert len(stability.KNOWN_MODELS) == 5
    total = len(minimax.KNOWN_MODELS) + len(openai.KNOWN_MODELS) + len(stability.KNOWN_MODELS)
    assert total == 11


def test_g2_provider_adapter_has_models_and_default_model():
    """ProviderAdapter dataclass extended with models + default_model."""
    from lingwen_illustrations.providers import ProviderAdapter, get_provider

    fields = {f.name for f in ProviderAdapter.__dataclass_fields__.values()}
    assert "models" in fields
    assert "default_model" in fields

    adapter = get_provider("minimax")
    assert isinstance(adapter.models, tuple)
    assert isinstance(adapter.default_model, str)


def test_g3_unknown_model_error_class_exists():
    """UnknownModelError class exists in exceptions module."""
    from lingwen_illustrations.exceptions import UnknownModelError

    err = UnknownModelError("openai", "m-bad", ("m1",))
    assert err.provider == "openai"
    assert err.model == "m-bad"


def test_g4_pipeline_resolve_model_function_exists():
    """pipeline.resolve_model helper is publicly exported."""
    from lingwen_illustrations import pipeline

    assert hasattr(pipeline, "resolve_model")
    assert callable(pipeline.resolve_model)


def test_g5_settings_yaml_accepts_default_models(tmp_path: Path):
    """Settings loader accepts default_models dict (backwards compat)."""
    from lingwen_illustrations.pipeline import _load_illustration_settings

    settings_dir = tmp_path / ".lingwen"
    settings_dir.mkdir()
    (settings_dir / "illustration_settings.yaml").write_text(
        "default_provider: openai\n"
        "default_models:\n"
        "  openai: gpt-image-1\n",
        encoding="utf-8",
    )
    settings = _load_illustration_settings(tmp_path)
    assert "default_models" in settings
    assert settings["default_models"]["openai"] == "gpt-image-1"


def test_g6_illustration_route_accepts_model_field():
    """POST /generate schema has optional model field."""
    from apps.studio_api.routes.illustrations import GenerateRequest

    fields = GenerateRequest.model_fields
    assert "model" in fields
    assert fields["model"].default is None  # optional


def test_g7_get_provider_models_endpoint_registered():
    """GET /api/illustrations/providers/{name}/models is registered."""
    from apps.studio_api.app import create_app

    app = create_app()
    paths = {route.path for route in app.routes if hasattr(route, "path")}
    assert "/api/illustrations/providers/{name}/models" in paths


def test_g8_illustration_metadata_model_field_present():
    """IllustrationMetadata.model field already exists (Phase 96+); Phase 100 uses it."""
    from lingwen_illustrations.metadata import IllustrationMetadata

    fields = {f.name for f in IllustrationMetadata.__dataclass_fields__.values()}
    assert "model" in fields
    assert "provider" in fields


def test_g9_i092_invariant_in_architecture_yml():
    """I092 invariant is recorded in .lingwen/architecture.yml."""
    arch_path = Path("/home/ailearn/projects/LingWen/.lingwen/architecture.yml")
    data = yaml.safe_load(arch_path.read_text(encoding="utf-8"))
    invariants = data.get("invariants", [])
    i092 = [inv for inv in invariants if inv.get("id") == "I092"]
    assert i092, "I092 invariant not found in architecture.yml"
    rule_text = str(i092[0])
    assert "providers" in rule_text.lower() or "KNOWN_MODELS" in rule_text
