"""Phase 40b P3-ARCHDEBT (studio_registry) regression guards.

Verifies the canonical migration of `infra.studio_registry` → `packages/lingwen-studio-registry/`:
- Package importable + 18 public symbols in __all__
- 5-sub-module structure (models + discovery + state + summary + reports)
- Legacy shim deleted after all test consumers migrated
- `infra/studio/__init__.py` no longer re-exports the deleted shim
- New package is canonical (workspace deps, NOT-LEAF — 3 deps)
- I055 invariant present in .lingwen/architecture.yml
- Production and test audits contain no legacy registry path references

Phase 40a migrated all production consumers. Phase 40b completes the migration by
moving the remaining test consumers and deleting the compatibility shim.

Phase 40a commits: C0 (6ba28672) / C1 (76d3ed03) / C1.5 (b937a4ad) /
                  C2a (74c268a4) / C2b (53562912) / C3 (4d26cc1b) / C4 (1c473405)
"""
from __future__ import annotations

import dataclasses
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


# === Test 5: infra/studio_registry.py shim deleted in Phase 40b ===
def test_infra_studio_registry_shim_deleted() -> None:
    shim_path = REPO_ROOT / "infra" / "studio_registry.py"
    assert not shim_path.exists(), (
        "infra/studio_registry.py must be deleted after the tests/ migration"
    )


# === Test 6: infra/studio/__init__.py has no registry wildcard ===
def test_infra_studio_init_has_no_registry_wildcard() -> None:
    init_path = REPO_ROOT / "infra" / "studio" / "__init__.py"
    content = init_path.read_text(encoding="utf-8")
    assert "from lingwen_studio_registry import *" not in content, (
        "infra/studio/__init__.py must not re-export the deleted registry shim"
    )
    assert "from infra.studio_registry" not in content, (
        "infra/studio/__init__.py must not reference infra.studio_registry"
    )


# === Test 7: production code has no legacy registry path ===
def test_no_production_references_infra_studio_registry() -> None:
    """No legacy dotted or filesystem registry path remains in production code."""
    production_refs: list[str] = []
    for directory_name in ["infra", "apps", "packages"]:
        directory = REPO_ROOT / directory_name
        for path in sorted(directory.rglob("*.py")):
            content = path.read_text(encoding="utf-8")
            if "infra.studio_registry" in content or "infra/studio_registry" in content:
                production_refs.append(str(path.relative_to(REPO_ROOT)))
    assert production_refs == [], (
        f"Production code still references the legacy registry path: {production_refs}"
    )


# === Test 8: test code has no legacy registry path ===
def test_no_test_references_infra_studio_registry() -> None:
    """All test consumers use the canonical lingwen_studio_registry package."""
    guard_path = Path(__file__).resolve()
    test_refs: list[str] = []
    for directory_name in ["tests", "apps", "packages"]:
        directory = REPO_ROOT / directory_name
        for path in sorted(directory.rglob("*.py")):
            if path == guard_path or "tests" not in path.parts:
                continue
            content = path.read_text(encoding="utf-8")
            if "infra.studio_registry" in content or "infra/studio_registry" in content:
                test_refs.append(str(path.relative_to(REPO_ROOT)))
    assert test_refs == [], f"Tests still reference the legacy registry path: {test_refs}"


# === Test 9: workspace member declares lingwen-studio-registry ===
def test_workspace_member_declares_lingwen_studio_registry() -> None:
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "packages/lingwen-studio-registry" in pyproject, (
        "pyproject.toml should declare packages/lingwen-studio-registry in workspace members"
    )
    assert "lingwen-studio-registry = { workspace = true }" in pyproject, (
        "pyproject.toml should declare lingwen-studio-registry as workspace source"
    )


# === Test 10: pyproject declares 3 workspace deps (NOT-LEAF package) ===
def test_lingwen_studio_registry_pyproject_dependencies() -> None:
    pkg_pyproject = (
        REPO_ROOT / "packages" / "lingwen-studio-registry" / "pyproject.toml"
    ).read_text(encoding="utf-8")
    # Verify all 3 deps — first non-LEAF P3-ARCHDEBT package (lesson 1)
    for dep in ["lingwen-paths", "lingwen-project-config", "lingwen-core"]:
        assert f'"{dep}"' in pkg_pyproject, (
            f"lingwen-studio-registry pyproject.toml missing workspace dep: {dep}"
        )


# === Test 11: invariant I055 in architecture.yml ===
def test_inv_55_in_architecture_yml() -> None:
    arch_yml = (REPO_ROOT / ".lingwen" / "architecture.yml").read_text(encoding="utf-8")
    assert "I055" in arch_yml, ".lingwen/architecture.yml should declare invariant I055"
    assert "lingwen-studio-registry" in arch_yml, (
        ".lingwen/architecture.yml should reference lingwen-studio-registry"
    )
    assert "infra.studio_registry" in arch_yml, (
        ".lingwen/architecture.yml should forbid infra.studio_registry"
    )


# === Test 12: factory_root() returns correct path (C1.5 fixup validation) ===
def test_factory_root_returns_lingwen_root() -> None:
    from lingwen_studio_registry import factory_root
    fr = factory_root()
    assert (fr / "projects").is_dir(), f"projects/ not found at factory_root: {fr}"
    assert (fr / "config" / "project.yaml").is_file(), (
        f"config/project.yaml not found at factory_root: {fr}"
    )
