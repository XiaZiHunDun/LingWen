"""Phase 90 — REQ-002 multimodal regression guards G1-G7.

Validates:
G1: 7 backend submodules exist (or as many as have been written)
G2: 4 API routes registered
G3: pyproject.toml workspace + dependencies
G4: I087 invariant in architecture.yml
G5: 9-pattern audit clean (no infra.illustrations.* refs)
G6: storage path pattern matches
G7: .meta.json sidecar has 4 required fields
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "packages" / "lingwen-illustrations"
ROUTER = REPO / "apps" / "studio_api" / "routes" / "illustrations.py"
ARCH_YML = REPO / ".lingwen" / "architecture.yml"
PYPROJECT = REPO / "pyproject.toml"


# --- G1: 7 submodules ---

SUBMODULES = [
    "metadata.py", "style_templates.py", "storage.py",
    "prompt_builder.py", "image_generator.py", "pipeline.py",
    "exceptions.py",
]


@pytest.mark.parametrize("submodule", SUBMODULES)
def test_g1_submodule_exists(submodule):
    p = PKG / "src" / "lingwen_illustrations" / submodule
    assert p.exists(), f"missing submodule: {submodule}"


# --- G2: 4 routes registered ---

def test_g2_routes_registered():
    content = ROUTER.read_text(encoding="utf-8")
    for route in [
        "@app.post(\"/api/illustrations/generate\"",
        "@app.get(\"/api/illustrations/list\"",
        "@app.delete(\"/api/illustrations/{asset_id}\"",
        "@app.get(\"/api/illustrations/{asset_id}/image\"",
    ]:
        assert route in content, f"missing route: {route}"


# --- G3: pyproject workspace + 3 deps ---

def test_g3_pyproject_workspace_and_deps():
    content = PYPROJECT.read_text(encoding="utf-8")
    assert "packages/lingwen-illustrations" in content, "workspace member missing"
    assert "lingwen-illustrations = { workspace = true }" in content, "dep entry missing"

    pkg_pyproject = (PKG / "pyproject.toml").read_text(encoding="utf-8")
    for dep in ["lingwen-llm-service", "lingwen-project-characters", "lingwen-paths"]:
        assert dep in pkg_pyproject, f"dep {dep} missing from package pyproject"


# --- G4: I087 invariant ---

def test_g4_i087_invariant():
    with ARCH_YML.open() as f:
        arch = yaml.safe_load(f)
    invariants = arch.get("invariants", [])
    ids = [inv.get("id") for inv in invariants]
    assert "I087" in ids, "I087 not in architecture.yml"

    i087 = next(inv for inv in invariants if inv.get("id") == "I087")
    rule = i087.get("rule", "")
    assert "lingwen-illustrations" in rule
    assert "infra.illustrations" in rule or "infra/illustrations" in rule


# --- G5: 9-pattern audit (no infra.illustrations.*) ---

@pytest.mark.parametrize("pattern,description", [
    (r"from infra\.illustrations", "literal dotted import"),
    (r"infra\.illustrations\.", "module reference"),
    (r"infra/illustrations", "filesystem path"),
])
def test_g5_no_infra_illustrations_refs(pattern, description):
    """Search all .py files for any reference to the old path."""
    import subprocess
    result = subprocess.run(
        ["grep", "-rn", "-E", pattern, str(REPO),
         "--include=*.py", "--exclude-dir=.venv", "--exclude-dir=__pycache__",
         "--exclude-dir=.git", "--exclude-dir=.superpowers",
         "--exclude-dir=node_modules", "--exclude-dir=.claude"],
        capture_output=True, text=True,
    )
    # Allow historical comments / docstrings mentioning migration
    lines = [l for l in result.stdout.splitlines()
             if "/test_phase90" not in l
             and "/test_phase18" not in l
             and "/test_phase89" not in l
             and "/test_phase86" not in l
             and "/test_phase85" not in l
             and "/test_phase84" not in l
             and "/test_phase83" not in l
             and "/test_phase82" not in l
             and "/test_phase81" not in l
             and "/test_phase80" not in l
             and "/test_phase79" not in l
             and "/test_phase78" not in l
             and "/test_phase77" not in l
             and "/test_phase76" not in l
             and "/test_phase73" not in l
             and "/test_phase62" not in l
             and "/test_phase60" not in l]
    assert not lines, "found infra.illustrations refs:\n" + "\n".join(lines[:5])


# --- G6: storage path pattern ---

def test_g6_storage_path_pattern():
    from lingwen_illustrations.storage import asset_path
    p1 = asset_path(Path("/tmp/proj"), type="cover", id="abc")
    assert str(p1).endswith("/assets/covers/abc.jpg"), p1
    p2 = asset_path(Path("/tmp/proj"), type="chapter", id="abc", chapter_num=17)
    assert str(p2).endswith("/assets/illustrations/chapter-017/abc.jpg"), p2


# --- G7: sidecar fields ---

def test_g7_sidecar_required_fields(tmp_path):
    from lingwen_illustrations.metadata import IllustrationMetadata
    from lingwen_illustrations.storage import save_asset

    meta = IllustrationMetadata(
        id="x", type="chapter", project_slug="p", chapter_num=1,
        style_preset="ink", custom_prompt=None, scene_json={"s": "x"},
        final_prompt="fp", prompt_hash="sha256:x", model="m",
        created_at="2026-09-15T00:00:00Z",
    )
    save_asset(tmp_path, b"data", meta)
    sidecar = tmp_path / "assets" / "illustrations" / "chapter-001" / "x.jpg.meta.json"
    assert sidecar.exists()
    payload = json.loads(sidecar.read_text())
    for field in ("prompt_hash", "style_preset", "scene_json", "created_at"):
        assert field in payload, f"missing required sidecar field: {field}"


# ─── G8: v1 dead path <root>/config/characters.json not in src/ ──
# Phase 91 P2-ILLUSTRATIONS-BIBLE-CANONICAL closure: v1 path physically
# removed. Strip docstrings before regex (N.14 lesson 1 v21 — module
# docstring legitimately mentioned v1 path in narrative before deletion).
def test_v1_path_not_referenced_in_src() -> None:
    """G8: v1 <root>/config/characters.json must be gone from src/."""
    illus_src = PKG / "src"
    violations: list[str] = []
    for py_file in illus_src.rglob("*.py"):
        if py_file.name.startswith("test_"):
            continue
        text = py_file.read_text(encoding="utf-8")
        # strip module/class/function docstrings (N.14 v21)
        stripped = re.sub(r'"""[\s\S]*?"""', "", text)
        stripped = re.sub(r"'''[\s\S]*?'''", "", stripped)
        if re.search(r"config/characters\.json", stripped):
            violations.append(
                str(py_file.relative_to(REPO))
            )
    assert not violations, f"v1 path still referenced in: {violations}"


# ─── G9: bible_loader.load_character_bible is public ────────────
def test_bible_loader_public() -> None:
    """G9: bible_loader submodule + load_character_bible public symbol."""
    import lingwen_illustrations.bible_loader as bl

    assert hasattr(bl, "load_character_bible")
    assert "load_character_bible" in bl.__all__


# ─── G10: STRUCTURED_EXTRACTION enum + illustrations use it (Phase 92) ──
def test_structured_extraction_enum_exists() -> None:
    """G10a: TaskType.STRUCTURED_EXTRACTION must be added to lingwen-shared.

    Phase 92 P2-EXTRACT-ENUM closure: v1 used QUALITY_ANALYSIS as a
    semantic stand-in for schema-bounded JSON extraction. v55.2 adds
    the dedicated enum member so prompts can declare intent precisely.
    """
    from lingwen_shared.contracts.python.llm import TaskType

    assert hasattr(TaskType, "STRUCTURED_EXTRACTION"), (
        "TaskType.STRUCTURED_EXTRACTION missing — Phase 92 P2-EXTRACT-ENUM"
        " not closed. v55.2 should add this member."
    )
    assert TaskType.STRUCTURED_EXTRACTION.value == "structured_extraction"


def test_extract_scene_uses_structured_extraction() -> None:
    """G10b: extract_scene must pass TaskType.STRUCTURED_EXTRACTION, not the
    legacy QUALITY_ANALYSIS stand-in.

    Validates the call-site switched from the v1 fallback to the new enum.
    """
    import inspect

    from lingwen_illustrations import prompt_builder

    source = inspect.getsource(prompt_builder.extract_scene)
    assert "TaskType.STRUCTURED_EXTRACTION" in source, (
        "extract_scene still uses the v1 QUALITY_ANALYSIS fallback — "
        "should switch to STRUCTURED_EXTRACTION in Phase 92."
    )
    assert "TaskType.QUALITY_ANALYSIS" not in source, (
        "extract_scene must not reference QUALITY_ANALYSIS anymore — "
        "STRUCTURED_EXTRACTION is the dedicated replacement."
    )


def test_llm_service_task_configs_includes_structured_extraction() -> None:
    """G10c: LLMService.TASK_CONFIGS must include STRUCTURED_EXTRACTION.

    Without an entry, the dict-based config lookup silently falls back to
    LLMTask defaults (2000/0.3) — Phase 92 makes the choice explicit.
    """
    from lingwen_llm_service.service import LLMService
    from lingwen_shared.contracts.python.llm import TaskType

    assert TaskType.STRUCTURED_EXTRACTION in LLMService.TASK_CONFIGS, (
        "LLMService.TASK_CONFIGS missing STRUCTURED_EXTRACTION entry — "
        "Phase 92 should add max_tokens + temperature for deterministic JSON."
    )
    cfg = LLMService.TASK_CONFIGS[TaskType.STRUCTURED_EXTRACTION]
    assert "max_tokens" in cfg and "temperature" in cfg


# ─── G11: image_generator real b64_json decode (Phase 93) ──────────
def test_image_generator_uses_b64_json_decode_not_raw_content() -> None:
    """G11a: image_generator.generate must base64-decode b64_json from JSON envelope.

    v55.3 Phase 93 closure: the MiniMax image API returns JSON of shape
    {"data": [{"b64_json": "<base64-jpeg>"}]} when response_format=b64_json
    is requested. The implementation must call resp.json() + base64.b64decode;
    NOT return resp.content raw (which was the v1 mock-only behavior).
    """
    import inspect

    from lingwen_illustrations import image_generator

    source = inspect.getsource(image_generator.generate)
    assert "base64" in source and "b64decode" in source, (
        "image_generator.generate must base64-decode b64_json — Phase 93"
        " closure replaces v1 raw resp.content behavior."
    )
    assert "resp.json()" in source or ".json(" in source, (
        "image_generator.generate must parse JSON response — real API"
        " returns JSON envelope, not raw bytes."
    )
    # Negative: must NOT keep the v1 behavior of returning resp.content raw.
    # Strip docstrings + allow the body to be a strict subset (no stand-alone
    # `return resp.content` as the only path).
    assert not _has_raw_resp_content_return(source), (
        "image_generator.generate must NOT return resp.content raw —"
        " Phase 93 requires JSON-parse + base64-decode path."
    )


def test_image_generator_request_format_is_b64_json() -> None:
    """G11b: payload must request response_format=b64_json.

    Without this, the API returns image URLs (b64_json absent) and decode
    raises GenerateError — silent contract drift.
    """
    import inspect

    from lingwen_illustrations import image_generator

    source = inspect.getsource(image_generator.generate)
    assert '"b64_json"' in source or "'b64_json'" in source, (
        "image_generator must request response_format=b64_json — Phase 93."
    )


def _has_raw_resp_content_return(source: str) -> bool:
    """Detect v1-style `return resp.content` as a final return (defense in depth)."""
    # Strip docstrings to avoid false-positives on the v1 docstring mention.
    import re

    stripped = re.sub(r'"""[\s\S]*?""""', "", source)
    stripped = re.sub(r"'''[\s\S]*?'''", "", stripped)
    # Look for a top-level `return resp.content` that is the sole return path.
    # Tolerate presence in branches if a JSON-decode path also exists.
    return bool(re.search(r"return\s+resp\.content\s*$", stripped, re.MULTILINE))


# ─── G12: atomic regenerate via PUT (Phase 94) ───────────────────────
def test_regenerate_endpoint_uses_put_method() -> None:
    """G12a: PUT /api/illustrations/{id}/regenerate endpoint must be registered.

    v55.4 Phase 94 replaces v1 frontend pattern (DELETE then POST, non-atomic
    window where asset doesn't exist). Backend now provides single-call atomic
    swap via PUT.
    """
    import re

    content = ROUTER.read_text(encoding="utf-8")
    # Strip docstrings (N.14 v21) so the v1 narrative mention doesn't false-positive.
    stripped = re.sub(r'"""[\s\S]*?""""', "", content)
    assert (
        re.search(
            r'@app\.put\(["\']/api/illustrations/\{asset_id\}/regenerate["\']',
            stripped,
        )
        is not None
    ), "PUT /api/illustrations/{asset_id}/regenerate must be registered — Phase 94."


def test_storage_has_replace_asset_for_atomic_swap() -> None:
    """G12b: storage.replace_asset must exist (Phase 94 atomic swap helper)."""
    import inspect

    from lingwen_illustrations import storage

    assert hasattr(storage, "replace_asset"), (
        "storage.replace_asset missing — Phase 94 atomic regenerate requires"
        " temp-file + rename helper."
    )
    sig = inspect.signature(storage.replace_asset)
    # Must accept (project_root, image_bytes, meta) — Phase 94 signature contract.
    params = list(sig.parameters)
    assert "project_root" in params
    assert "image_bytes" in params
    assert "meta" in params


def test_pipeline_has_regenerate_illustration() -> None:
    """G12c: pipeline.regenerate_illustration must exist (Phase 94 stage re-run)."""
    import inspect

    from lingwen_illustrations import pipeline

    assert hasattr(pipeline, "regenerate_illustration"), (
        "pipeline.regenerate_illustration missing — Phase 94 must add a"
        " pipeline variant that re-runs stages 1-4 + atomic swap."
    )
    sig = inspect.signature(pipeline.regenerate_illustration)
    params = list(sig.parameters)
    # Must take project_root + existing_meta + api_key + api_host (Phase 94 contract).
    assert "project_root" in params
    assert "existing_meta" in params
    assert "api_key" in params
    assert "api_host" in params


def test_frontend_regenerate_uses_put_not_delete_then_post() -> None:
    """G12d: frontend regenerate() must call PUT, not the v1 DELETE+POST pattern.

    Catches regression if someone restores the v1 non-atomic pattern in the
    store after Phase 94 closes the carryover.
    """
    STORE = REPO / "apps" / "dashboard" / "src" / "stores" / "useIllustrationStore.js"
    content = STORE.read_text(encoding="utf-8")
    # Find the regenerate function body.
    import re

    m = re.search(
        r"async function regenerate\(slug, assetId\)\s*\{(.*?)\n  \}",
        content,
        re.DOTALL,
    )
    assert m is not None, "regenerate() function not found in store"
    body = m.group(1)
    # Strip docstring-ish narrative comments before assertions.
    body_stripped = re.sub(r"//[^\n]*", "", body)
    assert "method: 'PUT'" in body_stripped or 'method: "PUT"' in body_stripped, (
        "frontend regenerate() must call PUT — Phase 94 atomic swap."
    )
    # v1 pattern: deleteAsset(slug, assetId) inside regenerate function.
    # After Phase 94 this should NOT happen.
    assert "deleteAsset(slug" not in body, (
        "regenerate() still calls deleteAsset — v1 non-atomic pattern."
        " Phase 94 should have removed the DELETE step."
    )


# ─── G13: ProjectSettingsPage substitution (Phase 95) ────────────────
def test_project_settings_illustration_mounted_in_settings_page() -> None:
    """G13a: ProjectSettingsIllustration must be mounted in SettingsPage (not orphan).

    v55.5 Phase 95 closure: Phase 90 spec mentioned a dedicated
    ProjectSettingsPage.vue route. Actual implementation substituted this
    with the component nested inside the global SettingsPage.vue (avoids
    per-project URL overhead; preferences remain accessible via the global
    Settings nav entry). This guard verifies the substitution holds:
    the component is mounted in SettingsPage (not orphan, not absent).
    """
    settings_page = (
        REPO / "apps" / "dashboard" / "src" / "pages" / "SettingsPage.vue"
    )
    content = settings_page.read_text(encoding="utf-8")
    assert "ProjectSettingsIllustration" in content, (
        "ProjectSettingsIllustration must be mounted in SettingsPage.vue —"
        " Phase 95 substitution (component nested in global Settings)"
    )
    # Also verify it's rendered (not just imported).
    assert "<ProjectSettingsIllustration" in content, (
        "ProjectSettingsIllustration must be rendered in SettingsPage.vue template —"
        " Phase 95 substitution (template, not import-only)."
    )


def test_no_dedicated_project_settings_page_route() -> None:
    """G13b: No dedicated ProjectSettingsPage.vue page exists (substitution is complete).

    This guard ENFORCES the v55.5 substitution: if someone later adds a
    dedicated ProjectSettingsPage.vue route, they should ALSO move the
    ProjectSettingsIllustration component out of SettingsPage (and update
    Phase 95 docs). Until then, the substitution is the canonical pattern.
    """
    project_settings_page = (
        REPO / "apps" / "dashboard" / "src" / "pages" / "ProjectSettingsPage.vue"
    )
    assert not project_settings_page.exists(), (
        "pages/ProjectSettingsPage.vue must NOT exist — Phase 95 substitution"
        " uses SettingsPage (global) as the host. If you intentionally want"
        " a separate route, also move ProjectSettingsIllustration out of"
        " SettingsPage and update G13a."
    )


def test_project_settings_illustration_has_its_own_spec() -> None:
    """G13c: ProjectSettingsIllustration component has dedicated tests.

    The component is tested independently even though it lives in SettingsPage —
    verifies the substitution didn't drop test coverage.
    """
    spec = (
        REPO
        / "apps"
        / "dashboard"
        / "tests"
        / "unit"
        / "components"
        / "illustrations"
        / "ProjectSettingsIllustration.spec.js"
    )
    assert spec.exists(), (
        "ProjectSettingsIllustration.spec.js must exist — Phase 90 Task 17"
        " unit tests verify component behavior independent of mount location."
    )
    content = spec.read_text(encoding="utf-8")
    # Sanity: at least 4 tests (renders 3 presets + selected + emit + max_assets + confirm).
    assert content.count("it(") >= 4, (
        "ProjectSettingsIllustration.spec.js must have ≥4 tests —"
        " Phase 95 verifies test coverage was preserved during substitution."
    )
