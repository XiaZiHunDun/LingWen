"""Phase 42 P3-ARCHDEBT (project_init) regression guards.

Verifies lingwen-project-init package canonicalization (v40.0, invariant #56).
Pattern: Phase 40a test_phase40a_lingwen_studio_registry.py + Phase 41+ test_phase42 patterns.

Skip files (N.14 lesson 6 — guard self-trigger):
- tests/test_phase42_lingwen_project_init.py (this file)
- tests/test_phase18_10_stale_imports.py (potential stale-list)
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

SKIP_FILES = {
    REPO_ROOT / "tests" / "test_phase42_lingwen_project_init.py",
    REPO_ROOT / "tests" / "test_phase18_10_stale_imports.py",
}


def _is_skipped(path: Path) -> bool:
    return path in SKIP_FILES


# ---------------------------------------------------------------------------
# G1: lingwen-project-init package scaffolding exists
# ---------------------------------------------------------------------------


def test_lingwen_project_init_importable():
    """Verify package importable."""
    import lingwen_project_init

    assert lingwen_project_init is not None


def test_lingwen_project_init_exposes_4_public_symbols():
    """Verify __all__ lists 4 public symbols (1 class + 3 funcs)."""
    import lingwen_project_init

    assert hasattr(lingwen_project_init, "__all__")
    assert len(lingwen_project_init.__all__) == 4
    assert "InitProjectResult" in lingwen_project_init.__all__
    assert "validate_slug" in lingwen_project_init.__all__
    assert "default_project_parent" in lingwen_project_init.__all__
    assert "init_minimal_short_project" in lingwen_project_init.__all__


def test_lingwen_project_init_init_project_result():
    """Verify InitProjectResult is frozen dataclass with 6 fields."""
    from lingwen_project_init import InitProjectResult

    fields = list(InitProjectResult.__dataclass_fields__.keys())
    assert fields == ["slug", "title", "root", "chapter_count", "creation_mode", "files_written"]
    # Frozen check
    assert InitProjectResult.__dataclass_params__.frozen is True


def test_lingwen_project_init_3_sub_modules():
    """Verify all 3 sub-module files exist."""
    package_src = REPO_ROOT / "packages" / "lingwen-project-init" / "src" / "lingwen_project_init"
    assert (package_src / "models.py").exists()
    assert (package_src / "slug.py").exists()
    assert (package_src / "beats.py").exists()
    assert (package_src / "__init__.py").exists()


# ---------------------------------------------------------------------------
# G2: infra/project_init.py deleted (FULL DELETE in C3, NOT shim)
# ---------------------------------------------------------------------------


def test_infra_project_init_path_forbidden():
    """Verify infra/project_init.py removed (Phase 42 C3 FULL DELETE)."""
    infra_project_init = REPO_ROOT / "infra" / "project_init.py"
    assert not infra_project_init.exists(), (
        f"{infra_project_init} should not exist after Phase 42 (full delete, NOT shim)"
    )


def test_no_consumer_imports_infra_project_init():
    """Verify no Python file imports from infra.project_init (excluding skip files + other worktrees)."""
    result = subprocess.run(
        [
            "grep",
            "-rln",
            "--include=*.py",
            ".",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        # Exclude worktree pollution from other locked worktrees (Phase 41 mini lesson 1)
        # The grep runs in cwd=REPO_ROOT; manually filter results below
    )
    files = [f for f in result.stdout.splitlines() if f]

    offenders = []
    pattern = re.compile(r"\b(infra\.project_init|from\s+infra\.project_init|import\s+infra\.project_init)\b")

    for rel_path in files:
        # Skip other worktrees (pollution from locked worktree)
        if rel_path.startswith(".claude/worktrees/"):
            continue
        # Skip excluded dirs
        if any(part in rel_path for part in ["/.venv/", "/__pycache__/", "/build/", "/dist/"]):
            continue
        path = REPO_ROOT / rel_path
        if _is_skipped(path):
            continue
        if path.suffix != ".py":
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if pattern.search(content):
            offenders.append(rel_path)

    assert not offenders, (
        "Found infra.project_init references (forbidden by invariant #56):\n"
        + "\n".join(f"  - {p}" for p in offenders)
    )


# ---------------------------------------------------------------------------
# G3: Workspace + invariant + pyproject
# ---------------------------------------------------------------------------


def test_workspace_member_declares_lingwen_project_init():
    """Verify root pyproject.toml declares packages/lingwen-project-init."""
    pyproject = REPO_ROOT / "pyproject.toml"
    content = pyproject.read_text(encoding="utf-8")
    assert '"packages/lingwen-project-init"' in content, (
        "pyproject.toml [tool.uv.workspace] members must include 'packages/lingwen-project-init'"
    )
    assert 'lingwen-project-init = { workspace = true }' in content, (
        "pyproject.toml [tool.uv.sources] must declare lingwen-project-init workspace source"
    )


def test_pyproject_dependencies_lists_2_packages():
    """Verify lingwen-project-init pyproject.toml has 2 workspace deps."""
    pyproject = REPO_ROOT / "packages" / "lingwen-project-init" / "pyproject.toml"
    content = pyproject.read_text(encoding="utf-8")
    assert '"lingwen-paths"' in content
    assert '"lingwen-shared"' in content
    # Ensure NO other workspace deps (Phase 42 scope = 2 deps)
    deps_section = content.split("dependencies = [")[1].split("]")[0]
    dep_count = len([line for line in deps_section.split("\n") if '"lingwen-' in line])
    assert dep_count == 2, f"Expected 2 deps, found {dep_count}"


def test_inv_56_in_architecture_yml():
    """Verify invariant I056 in architecture.yml."""
    arch_yml = REPO_ROOT / ".lingwen" / "architecture.yml"
    content = arch_yml.read_text(encoding="utf-8")
    assert "id: I056" in content, "invariant I056 not found in architecture.yml"
    assert "lingwen-project-init" in content, "invariant I056 must reference lingwen-project-init"
    assert "infra.project_init" in content, "invariant I056 must forbid infra.project_init.*"


# ---------------------------------------------------------------------------
# G4: Functional smoke test
# ---------------------------------------------------------------------------


def test_init_minimal_short_project_smoke():
    """Smoke test: invoke init_minimal_short_project with valid params."""
    import tempfile
    from lingwen_project_init import init_minimal_short_project

    with tempfile.TemporaryDirectory() as tmp:
        from pathlib import Path
        factory_root = Path(tmp) / "factory"
        factory_root.mkdir()
        result = init_minimal_short_project(
            slug="smoke",
            title="冒烟测试",
            factory_root=factory_root,
        )
        assert result.slug == "smoke"
        assert result.title == "冒烟测试"
        assert result.chapter_count == 10
        assert result.creation_mode == "companion"
        assert len(result.files_written) > 0  # At least config + pillars + readme + outlines
        # Files actually written
        for rel in result.files_written:
            assert (result.root / rel).exists(), f"file {rel} not written"
