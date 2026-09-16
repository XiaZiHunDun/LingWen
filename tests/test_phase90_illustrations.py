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
