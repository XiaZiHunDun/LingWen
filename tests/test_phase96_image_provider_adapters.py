"""Phase 96 regression guards (image provider abstraction).

Source-only checks (no runtime / no API calls). Pattern follows
Phase 90-95 regression guards in tests/test_phase9[0-5]_*.py.

Each guard defends a specific invariant from spec
`docs/superpowers/specs/2026-09-16-phase-96-image-provider-adapters-design.md`
that future refactors might accidentally regress.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

# Source files to read (for guards that need source inspection).
REPO = Path(__file__).resolve().parents[1]
_PROVIDERS_DIR = REPO / "packages" / "lingwen-illustrations" / "src" / "lingwen_illustrations" / "providers"
_PIPELINE_PY = REPO / "packages" / "lingwen-illustrations" / "src" / "lingwen_illustrations" / "pipeline.py"
_METADATA_PY = REPO / "packages" / "lingwen-illustrations" / "src" / "lingwen_illustrations" / "metadata.py"
_EXCEPTIONS_PY = REPO / "packages" / "lingwen-illustrations" / "src" / "lingwen_illustrations" / "exceptions.py"
_IMAGE_GENERATOR_PY = REPO / "packages" / "lingwen-illustrations" / "src" / "lingwen_illustrations" / "image_generator.py"
_ILLUSTRATIONS_ROUTE = REPO / "apps" / "studio_api" / "routes" / "illustrations.py"
_PROJECT_SETTINGS_ROUTE = REPO / "apps" / "studio_api" / "routes" / "project_settings.py"
_APICONFIG_PY = REPO / "packages" / "lingwen-config" / "src" / "lingwen_config" / "api_config_loader.py"
_PROJECT_SETTINGS_VUE = REPO / "apps" / "dashboard" / "src" / "components" / "illustrations" / "ProjectSettingsIllustration.vue"
_GEN_DIALOG_VUE = REPO / "apps" / "dashboard" / "src" / "components" / "illustrations" / "GenerateIllustrationDialog.vue"


def _strip_docstrings(text: str) -> str:
    """N.14 lesson 1 v21: strip docstrings before regex search (Phase 57b pattern).

    Phase 96 docstrings may legitimately mention deleted patterns (e.g. when
    describing the v1 behavior a refactor replaces). Strip triple-quoted
    docstrings before regex matching to avoid false positives.
    """
    return re.sub(r'\"\"\"[\s\S]*?\"\"\"', "", text, flags=re.DOTALL)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------- G1: providers/ subpackage structure ----------

def test_g1_providers_subpackage_has_5_modules():
    """G1: providers/ has __init__, _b64_decode, minimax, openai, stability."""
    expected = {"__init__.py", "_b64_decode.py", "minimax.py", "openai.py", "stability.py"}
    actual = {p.name for p in _PROVIDERS_DIR.glob("*.py")}
    assert expected.issubset(actual), f"missing: {expected - actual}"


# ---------- G2: KNOWN_PROVIDERS tuple ----------

def test_g2_known_providers_tuple_is_canonical():
    """G2: providers/__init__.py defines KNOWN_PROVIDERS = ('minimax', 'openai', 'stability')."""
    text = _strip_docstrings(_read(_PROVIDERS_DIR / "__init__.py"))
    match = re.search(r"KNOWN_PROVIDERS\s*:\s*tuple\[str,\s*\.\.\.\]\s*=\s*\(([^)]+)\)", text)
    assert match, "KNOWN_PROVIDERS tuple not found"
    items = tuple(s.strip().strip('"').strip("'") for s in match.group(1).split(","))
    assert items == ("minimax", "openai", "stability")


# ---------- G3: each adapter exports async generate ----------

@pytest.mark.parametrize("module_name", ["minimax", "openai", "stability"])
def test_g3_adapter_module_exports_async_generate(module_name):
    """G3: each adapter module exports async def generate(...)."""
    module_path = _PROVIDERS_DIR / f"{module_name}.py"
    tree = ast.parse(_read(module_path))
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "generate":
            found = True
            break
    assert found, f"{module_name}.py must define `async def generate(...)`"


# ---------- G4: GenerateError accepts provider kwarg ----------

def test_g4_generate_error_accepts_provider_kwarg():
    """G4: GenerateError.__init__ has `provider: str = "unknown"` parameter."""
    tree = ast.parse(_read(_EXCEPTIONS_PY))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "GenerateError":
            init = next(
                (n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == "__init__"),
                None,
            )
            assert init is not None, "GenerateError.__init__ not found"
            kwarg_names = {a.arg for a in init.args.kwonlyargs}
            assert "provider" in kwarg_names, "GenerateError must accept `provider` kwarg"
            return
    pytest.fail("GenerateError class not found")


# ---------- G5: IllustrationMetadata has provider field ----------

def test_g5_illustration_metadata_has_provider_field():
    """G5: IllustrationMetadata dataclass has `provider: str = "minimax"` field."""
    tree = ast.parse(_read(_METADATA_PY))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "IllustrationMetadata":
            for field in node.body:
                if isinstance(field, ast.AnnAssign) and isinstance(field.target, ast.Name):
                    if field.target.id == "provider":
                        # Verify default is "minimax"
                        assert field.value is not None, "provider field must have default"
                        assert isinstance(field.value, ast.Constant), "provider default must be a constant"
                        assert field.value.value == "minimax", f"provider default must be 'minimax', got {field.value.value!r}"
                        return
    pytest.fail("provider field not found in IllustrationMetadata")


# ---------- G6: from_dict backwards compat ----------

def test_g6_from_dict_backwards_compat_injects_provider():
    """G6: IllustrationMetadata.from_dict injects 'minimax' when provider missing."""
    text = _strip_docstrings(_read(_METADATA_PY))
    assert '"provider" not in d' in text or "'provider' not in d" in text, (
        "from_dict must check 'provider' not in d"
    )
    assert '"provider": "minimax"' in text or "provider': 'minimax'" in text or 'provider": "minimax"' in text, (
        "from_dict must inject provider='minimax' default"
    )


# ---------- G7: pipeline.generate_illustration accepts provider ----------

def test_g7_pipeline_generate_illustration_signature_has_provider():
    """G7: pipeline.generate_illustration has `provider: str = 'minimax'` parameter."""
    tree = ast.parse(_read(_PIPELINE_PY))
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "generate_illustration":
            kwarg_names = {a.arg for a in node.args.kwonlyargs}
            assert "provider" in kwarg_names, "generate_illustration must accept `provider` kwarg"
            return
    pytest.fail("generate_illustration function not found")


# ---------- G8: pipeline.regenerate_illustration reads existing_meta.provider ----------

def test_g8_regenerate_uses_existing_meta_provider_as_default():
    """G8: pipeline.regenerate_illustration uses existing_meta.provider when provider is None."""
    text = _strip_docstrings(_read(_PIPELINE_PY))
    # Verify the resolution pattern: "provider is not None else existing_meta.provider"
    assert "existing_meta.provider" in text, "regenerate_illustration must reference existing_meta.provider"
    assert "provider is not None" in text, "regenerate_illustration must check `provider is not None`"


# ---------- G9: GenerateRequest has provider field ----------

def test_g9_generate_request_has_provider_field():
    """G9: apps GenerateRequest Pydantic has `provider: Optional[str] = None` field."""
    tree = ast.parse(_read(_ILLUSTRATIONS_ROUTE))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "GenerateRequest":
            for field in node.body:
                if isinstance(field, ast.AnnAssign) and isinstance(field.target, ast.Name):
                    if field.target.id == "provider":
                        return
    pytest.fail("provider field not found in GenerateRequest")


# ---------- G10: route resolves provider priority ----------

def test_g10_route_resolves_provider_priority():
    """G10: route resolver implements body > project_settings > 'minimax' priority."""
    text = _strip_docstrings(_read(_ILLUSTRATIONS_ROUTE))
    assert "_resolve_provider_for_request" in text, "route must define _resolve_provider_for_request"
    assert "KNOWN_PROVIDERS" in text, "resolver must import KNOWN_PROVIDERS"
    # Verify priority chain: body first, then settings
    assert "body_provider" in text, "resolver must accept body_provider parameter"
    assert "default_provider" in text, "resolver must read settings.default_provider"


# ---------- G11: project_settings.py route exists with PUT/GET ----------

def test_g11_project_settings_route_has_put_and_get():
    """G11: apps/studio_api/routes/project_settings.py exists with PUT + GET routes."""
    assert _PROJECT_SETTINGS_ROUTE.exists(), "project_settings.py route missing"
    text = _read(_PROJECT_SETTINGS_ROUTE)
    assert '"/api/projects/{slug}/settings"' in text, "settings route path missing"
    # Both PUT and GET handlers
    assert "@app.put" in text, "PUT handler missing"
    assert "@app.get" in text, "GET handler missing"


# ---------- G12: APIConfig has openai_api_host + stability_api_key + stability_api_host ----------

def test_g12_apiconfig_has_new_provider_hosts():
    """G12: APIConfig exposes openai_api_host, stability_api_key, stability_api_host."""
    tree = ast.parse(_read(_APICONFIG_PY))
    properties_seen = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and any(
            isinstance(d, ast.Name) and d.id == "property"
            for d in node.decorator_list
        ):
            properties_seen.add(node.name)
    expected = {"openai_api_host", "stability_api_key", "stability_api_host"}
    missing = expected - properties_seen
    assert not missing, f"missing APIConfig properties: {missing}"


# ---------- G13: ProjectSettingsIllustration has default_provider dropdown ----------

def test_g13_project_settings_illustration_has_default_provider_dropdown():
    """G13: ProjectSettingsIllustration.vue has default_provider dropdown with data-testid."""
    text = _read(_PROJECT_SETTINGS_VUE)
    assert "project-settings-illustration-default-provider" in text, (
        "data-testid for default_provider dropdown missing"
    )
    assert "<select" in text, "<select> element for default_provider missing"
    # Provider options: Vue uses :value="p.id" binding; verify provider ids are
    # declared in the providers array OR bound via :value in the template.
    assert "providers" in text, "providers array missing"
    assert (
        "'minimax'" in text
        or '"minimax"' in text
        or "'openai'" in text
        or '"openai"' in text
        or "'stability'" in text
        or '"stability"' in text
    ), "no provider id (minimax/openai/stability) declared in component"


# ---------- G14: GenerateIllustrationDialog emits provider ----------

def test_g14_generate_illustration_dialog_emits_provider():
    """G14: GenerateIllustrationDialog.vue emits `provider` in generate payload."""
    text = _read(_GEN_DIALOG_VUE)
    assert "selectedProvider" in text, "selectedProvider ref missing"
    assert "provider:" in text or "provider =" in text, (
        "submit payload must include `provider:` field"
    )
