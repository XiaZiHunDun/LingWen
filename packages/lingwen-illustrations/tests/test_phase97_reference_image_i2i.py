"""Phase 97 reference image i2i regression guards (G1-G12).

Source-only checks. Verifies that all Phase 97 architectural invariants
remain in place even after future edits.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def _strip_docstrings(src: str) -> str:
    import re
    return re.sub(r'""".*?""""', "", src, flags=re.DOTALL)


# G1: get_provider returns ProviderAdapter with 4 fields
def test_g1_get_provider_returns_adapter_with_4_fields():
    src = _read(
        "packages/lingwen-illustrations/src/lingwen_illustrations/providers/__init__.py"
    )
    cleaned = _strip_docstrings(src)
    assert "ProviderAdapter" in cleaned
    assert "name:" in cleaned
    assert "generate:" in cleaned
    assert "generate_with_reference:" in cleaned
    assert "supports_i2i:" in cleaned
    assert "importlib.import_module" in cleaned  # dynamic lookup for monkeypatch


# G2: provider SUPPORTS_I2I constants
@pytest.mark.parametrize("provider,expected", [
    ("minimax", "True"),
    ("openai", "False"),
    ("stability", "True"),
])
def test_g2_provider_supports_i2i_constants(provider, expected):
    src = _read(
        f"packages/lingwen-illustrations/src/lingwen_illustrations/providers/{provider}.py"
    )
    assert f"SUPPORTS_I2I = {expected}" in _strip_docstrings(src)


# G3: providers have generate_with_reference function
@pytest.mark.parametrize("provider", ["minimax", "openai", "stability"])
def test_g3_providers_have_generate_with_reference(provider):
    src = _read(
        f"packages/lingwen-illustrations/src/lingwen_illustrations/providers/{provider}.py"
    )
    assert "async def generate_with_reference" in _strip_docstrings(src)


# G4: openai.generate_with_reference raises with retryable=False
def test_g4_openai_generate_with_reference_raises():
    src = _read(
        "packages/lingwen-illustrations/src/lingwen_illustrations/providers/openai.py"
    )
    cleaned = _strip_docstrings(src)
    # The function must raise GenerateError with retryable=False
    assert "GenerateError" in cleaned
    assert "retryable=False" in cleaned
    assert "does not support" in cleaned


# G5: reference_image module exists with 4 functions
def test_g5_reference_image_module_exists_with_4_functions():
    src = _read(
        "packages/lingwen-illustrations/src/lingwen_illustrations/reference_image.py"
    )
    for fn in (
        "save_reference_image",
        "load_reference_image",
        "delete_reference_image",
        "reference_image_info",
    ):
        assert f"def {fn}" in src, f"missing {fn}"


# G6: pipeline has reference_image_bytes param + adapter call
def test_g6_pipeline_dispatches_to_generate_with_reference_when_bytes_provided():
    src = _read(
        "packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py"
    )
    cleaned = _strip_docstrings(src)
    assert "reference_image_bytes" in cleaned
    assert "generate_with_reference" in cleaned
    assert "adapter.supports_i2i" in cleaned


# G7: pipeline raises GenerateError for openai + reference
def test_g7_pipeline_raises_generate_error_for_openai_with_reference():
    src = _read(
        "packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py"
    )
    cleaned = _strip_docstrings(src)
    assert "image-to-image" in cleaned
    assert "retryable=False" in cleaned


# G8: IllustrationMetadata has used_reference_image field
def test_g8_illustration_metadata_has_used_reference_image_field():
    src = _read(
        "packages/lingwen-illustrations/src/lingwen_illustrations/metadata.py"
    )
    cleaned = _strip_docstrings(src)
    assert "used_reference_image" in cleaned
    assert "bool" in cleaned


# G9: routes/reference_image.py 3 endpoints registered
def test_g9_routes_reference_image_three_endpoints_registered():
    src = _read("apps/studio_api/routes/reference_image.py")
    cleaned = _strip_docstrings(src)
    assert "/api/projects/{slug}/reference-image" in src
    # POST, GET, DELETE all defined
    assert 'upload_reference_image' in cleaned
    assert 'get_reference_image' in cleaned
    assert 'delete_reference_image' in cleaned


# G10: illustrations route accepts multipart file field
def test_g10_generate_request_supports_multipart_file_field():
    """Verify illustrations.py has multipart parsing + reference image plumbing.

    Task 7 implementation chose Request-based parsing (await request.form())
    because FastAPI can't mix Body(...) + File(...) in one endpoint. The
    inline comment in illustrations.py documents this design choice. This
    guard checks for the actual implementation markers.
    """
    src = _read("apps/studio_api/routes/illustrations.py")
    cleaned = _strip_docstrings(src)
    # Multipart parsing markers (Request-based approach)
    assert "Request" in cleaned
    assert "multipart/form-data" in cleaned
    assert "request.form" in cleaned or "form()" in cleaned
    # Reference image plumbing
    assert "use_project_reference" in cleaned
    assert "reference_image_bytes" in cleaned


# G11: frontend ReferenceImageUpload component exists with testids
def test_g11_frontend_reference_image_upload_component_exists():
    src = _read(
        "apps/dashboard/src/components/illustrations/ReferenceImageUpload.vue"
    )
    testids = [
        "reference-image-upload",
        "reference-image-upload-input",
        "reference-image-preview",
        "reference-image-replace",
        "reference-image-remove",
        "reference-image-error",
    ]
    for testid in testids:
        assert testid in src, f"missing data-testid={testid}"


# G12: useProjectSettings store has reference image methods
def test_g12_frontend_project_settings_store_has_reference_image_methods():
    src = _read("apps/dashboard/src/stores/useProjectSettings.js")
    for method in (
        "fetchReferenceImage",
        "fetchReferenceImageBlob",
        "uploadReferenceImage",
        "deleteReferenceImage",
    ):
        assert method in src, f"missing {method}"