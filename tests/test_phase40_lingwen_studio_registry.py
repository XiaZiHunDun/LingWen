"""Phase 40a P3-ARCHDEBT (studio_registry) regression guards.

Verifies the canonical migration of `infra.studio_registry` → `packages/lingwen-studio-registry/`:
- Package importable + 18 public symbols in __all__
- 5-sub-module structure (models + discovery + state + summary + reports)
- Source file converted to thin shim (infra.studio_registry still works)
- New package is canonical (workspace deps, NOT-LEAF — 3 deps)
- I055 invariant present in .lingwen/architecture.yml
- 5-pattern audit clean (no production consumer still references infra.studio_registry)

Phase 40b (planned, post-40a) will:
- Migrate 24 remaining `tests/`-root references to `lingwen_studio_registry`
- Delete the `infra/studio_registry.py` shim
- Add ~33 test-side migration regression guards

Phase 40a commits: C0 (6ba28672) / C1 (76d3ed03) / C1.5 (b937a4ad) /
                  C2a (74c268a4) / C2b (53562912) / C3 (4d26cc1b) / C4 (1c473405)
"""
from __future__ import annotations

import dataclasses
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


# === Test 1: package importable ===
def test_lingwen_studio_registry_importable() -> None:
    import lingwen_studio_registry
    assert lingwen_studio_registry is not None


# === Test 2: 18 public symbols in __all__ (1 class + 17 public funcs) ===
def test_lingwen_studio_registry_exposes_18_public_symbols() -> None:
    import lingwen_studio_registry
    assert hasattr(lingwen_studio_registry, "__all__")
    assert len(lingwen_studio_registry.__all__) == 18, (
        f"Expected 18 public symbols, got {len(lingwen_studio_registry.__all__)}"
    )
    expected = {
        "StudioProject",
        "factory_root",
        "list_projects",
        "get_project_by_slug",
        "active_state_path",
        "read_active_slug",
        "activate_project",
        "active_project",
        "pilot_records_dir_for",
        "project_summary",
        "quality_summary",
        "production_preflight",
        "find_calibration_batch",
        "suggest_batch_budget_usd",
        "batch_command",
        "quality_report_summary",
        "prose_diff_summary",
        "prose_judge_summary",
    }
    assert set(lingwen_studio_registry.__all__) == expected


# === Test 3: StudioProject is frozen dataclass with 5 fields ===
def test_lingwen_studio_registry_models_studio_project() -> None:
    from lingwen_studio_registry import StudioProject
    assert dataclasses.is_dataclass(StudioProject)
    assert StudioProject.__dataclass_params__.frozen
    field_names = {f.name for f in dataclasses.fields(StudioProject)}
    assert field_names == {"slug", "name", "role", "root", "location"}
    assert len(dataclasses.fields(StudioProject)) == 5


# === Test 4: 5 sub-modules exist ===
def test_lingwen_studio_registry_5_sub_modules() -> None:
    from lingwen_studio_registry import discovery, models, reports, state, summary
    for module in [models, discovery, state, summary, reports]:
        assert module is not None
    # Each sub-module should be importable and not a stub
    for module in [models, discovery, state, summary, reports]:
        assert hasattr(module, "__file__"), f"{module.__name__} has no __file__"


# === Test 5: infra/studio_registry.py exists as SHIM (NOT deleted in Phase 40a) ===
def test_infra_studio_registry_exists_as_shim() -> None:
    shim_path = REPO_ROOT / "infra" / "studio_registry.py"
    assert shim_path.exists(), (
        "infra/studio_registry.py should exist as a shim in Phase 40a "
        "(deleted in Phase 40b after tests/ migration)"
    )
    # Shim should be small (~20 lines)
    line_count = sum(1 for _ in shim_path.read_text(encoding="utf-8").splitlines())
    assert line_count < 50, f"Shim has {line_count} lines; expected <50"


# === Test 6: infra/studio/__init__.py uses lingwen_studio_registry ===
def test_infra_studio_init_uses_lingwen_studio_registry() -> None:
    init_path = REPO_ROOT / "infra" / "studio" / "__init__.py"
    content = init_path.read_text(encoding="utf-8")
    assert "from lingwen_studio_registry import *" in content, (
        "infra/studio/__init__.py should re-export from lingwen_studio_registry"
    )
    assert "from infra.studio_registry" not in content, (
        "infra/studio/__init__.py should no longer reference infra.studio_registry"
    )


# === Test 7: production code has no consumer imports of infra.studio_registry ===
def test_no_production_consumer_imports_infra_studio_registry() -> None:
    """No `from infra.studio_registry import` or `import infra.studio_registry`
    in production code (infra/, apps/, packages/).

    Excludes:
    - infra/studio_registry.py itself (the shim — C3)
    - infra/studio/__init__.py (the wildcard re-exporter)
    - tests/ root (Phase 40b will migrate; should still have refs until then)
    """
    result = subprocess.run(
        [
            "grep",
            "-rln",
            "--include=*.py",
            "from infra\\.studio_registry\\|import infra\\.studio_registry",
            "infra/",
            "apps/",
            "packages/",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    matches = [line for line in result.stdout.splitlines() if line.strip()]
    # Filter allowed exceptions (the shim itself + the wildcard re-exporter)
    ALLOWED = {
        "infra/studio_registry.py",  # the shim (C3)
        "infra/studio/__init__.py",  # the wildcard re-exporter
    }
    production_refs = [m for m in matches if m not in ALLOWED]
    assert not production_refs, (
        f"Production code still references infra.studio_registry: {production_refs}"
    )


# === Test 8: workspace member declares lingwen-studio-registry ===
def test_workspace_member_declares_lingwen_studio_registry() -> None:
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "packages/lingwen-studio-registry" in pyproject, (
        "pyproject.toml should declare packages/lingwen-studio-registry in workspace members"
    )
    assert "lingwen-studio-registry = { workspace = true }" in pyproject, (
        "pyproject.toml should declare lingwen-studio-registry as workspace source"
    )


# === Test 9: pyproject declares 3 workspace deps (NOT-LEAF package) ===
def test_lingwen_studio_registry_pyproject_dependencies() -> None:
    pkg_pyproject = (
        REPO_ROOT / "packages" / "lingwen-studio-registry" / "pyproject.toml"
    ).read_text(encoding="utf-8")
    # Verify all 3 deps — first non-LEAF P3-ARCHDEBT package (lesson 1)
    for dep in ["lingwen-paths", "lingwen-project-config", "lingwen-core"]:
        assert f'"{dep}"' in pkg_pyproject, (
            f"lingwen-studio-registry pyproject.toml missing workspace dep: {dep}"
        )


# === Test 10: invariant I055 in architecture.yml ===
def test_inv_55_in_architecture_yml() -> None:
    arch_yml = (REPO_ROOT / ".lingwen" / "architecture.yml").read_text(encoding="utf-8")
    assert "I055" in arch_yml, ".lingwen/architecture.yml should declare invariant I055"
    assert "lingwen-studio-registry" in arch_yml, (
        ".lingwen/architecture.yml should reference lingwen-studio-registry"
    )
    assert "infra.studio_registry" in arch_yml, (
        ".lingwen/architecture.yml should forbid infra.studio_registry"
    )


# === Test 11: factory_root() returns correct path (C1.5 fixup validation) ===
def test_factory_root_returns_lingwen_root() -> None:
    from lingwen_studio_registry import factory_root
    fr = factory_root()
    assert (fr / "projects").is_dir(), f"projects/ not found at factory_root: {fr}"
    assert (fr / "config" / "project.yaml").is_file(), (
        f"config/project.yaml not found at factory_root: {fr}"
    )
