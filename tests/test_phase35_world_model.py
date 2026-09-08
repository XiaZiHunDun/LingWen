"""Phase 35 WORLD-MODEL-PACKAGE regression guards.

Verify packages/lingwen-world-model/ is the canonical World Model (Ripple +
Subplot + Snapshot) engine location, and infra/world_model/ + infra/subplot/helpers.py
have been deleted. See
docs/superpowers/specs/2026-09-08-phase-35-world-model-package-design.md
section 6 (Validation gates).
"""
from __future__ import annotations

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


# ============ G1: Package scaffold ============


def test_lingwen_world_model_pyproject_exists():
    """packages/lingwen-world-model/pyproject.toml must exist (C1)."""
    assert (REPO_ROOT / "packages" / "lingwen-world-model" / "pyproject.toml").is_file()


def test_lingwen_world_model_init_exists():
    """packages/lingwen-world-model/src/lingwen_world_model/__init__.py must exist (C1)."""
    assert (
        REPO_ROOT
        / "packages"
        / "lingwen-world-model"
        / "src"
        / "lingwen_world_model"
        / "__init__.py"
    ).is_file()


def test_lingwen_world_model_depends_on_lingwen_core():
    """lingwen-world-model pyproject.toml must declare lingwen-core dependency."""
    pyproject = REPO_ROOT / "packages" / "lingwen-world-model" / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    deps = data["project"]["dependencies"]
    assert any("lingwen-core" in d for d in deps), (
        "lingwen-world-model must depend on lingwen-core"
    )


# ============ G2: Public API surface (37 symbols) ============


def test_lingwen_world_model_exports_37_symbols():
    """Public API surface must match pre-migration infra.world_model (37 symbols).

    Verified symbol count from infra/world_model/__init__.py pre-Phase-35
    (grep -c '^    \"' = 37). Spec v1 originally listed 41 — actual is 37.
    """
    import lingwen_world_model
    assert len(lingwen_world_model.__all__) == 37

    # Spot-check that canonical re-exports + behavior services + subplot helpers
    # are all present (mirrors Phase 34 expected-set pattern).
    expected = {
        # Canonical re-exports (from lingwen_core.domain.*)
        "KeyPoint", "MentalLine", "NodeId", "NodeType", "PhysicalLine",
        "PlotStatus", "Relation", "Ripple", "WorldSnapshot",
        "RippleState", "ResolutionMode", "MAX_OPEN_RIPPLOTS",
        # Behavior services
        "RippleEngine", "RippleRegistry", "KeyPointGraph",
        "Contradiction", "ContradictionKind",
        "SnapshotStore", "SnapshotNotFoundError", "SnapshotIntegrityError",
        "LinkAction", "RippleNotFoundError", "DuplicateRippleIdError",
        "OpenRippleLimitExceeded",
        # Functions / constants
        "detect_unresolved_ripples", "predict_collapse_risk",
        "suggest_resolution_chapter",
        "link_subplot_to_ripple", "apply_ripple_resolution",
        "subplots_count", "add_subplot", "get_active_subplots",
        "RESOLUTION_GRACE_CH", "COLLAPSE_RISK_THRESHOLD", "VALID_TRANSITIONS",
        "can_transition", "is_terminal",
    }
    assert expected.issubset(set(lingwen_world_model.__all__)), (
        f"Missing symbols: {expected - set(lingwen_world_model.__all__)}"
    )


def test_subplot_helpers_migrated():
    """lingwen_world_model.subplot_helpers must expose 3 functions (subplots_count, add_subplot, get_active_subplots)."""
    from lingwen_world_model import subplot_helpers
    for name in ("subplots_count", "add_subplot", "get_active_subplots"):
        assert hasattr(subplot_helpers, name), f"Missing subplot helper: {name}"


# ============ G3: Infra deletion (invariant #50) ============


def test_infra_world_model_directory_deleted():
    """infra/world_model/ directory must NOT exist (C2 git mv + C7 invariant #50)."""
    assert not (REPO_ROOT / "infra" / "world_model").exists(), (
        "infra/world_model/ still exists; C7 invariant #50 violation"
    )


def test_infra_subplot_helpers_deleted():
    """infra/subplot/helpers.py must NOT exist (C2 git mv to lingwen_world_model.subplot_helpers)."""
    assert not (REPO_ROOT / "infra" / "subplot" / "helpers.py").exists(), (
        "infra/subplot/helpers.py still exists; subplot_helpers must live in lingwen_world_model"
    )


# ============ G4: No remaining infra imports (4-pattern audit) ============


def _all_python_files_under(*prefixes: str) -> list[Path]:
    """Collect all .py files under the given top-level prefixes.

    Skips:
    - __pycache__/ directories
    - tests/test_phase35_world_model.py (the guards file itself; references the path
      in docstrings/assert messages and would self-trigger otherwise)
    - tests/test_phase32_shim_cleanup.py (Phase 32 historical-references list of
      deleted paths; explicitly retains 'infra/world_model/data_structures.py' as a
      documented deletion entry, not a runtime import)
    """
    skip_files = {
        REPO_ROOT / "tests" / "test_phase35_world_model.py",
        REPO_ROOT / "tests" / "test_phase32_shim_cleanup.py",
    }
    out: list[Path] = []
    for prefix in prefixes:
        root = REPO_ROOT / prefix
        if not root.exists():
            continue
        for p in root.rglob("*.py"):
            if "__pycache__" in p.parts:
                continue
            if p in skip_files:
                continue
            out.append(p)
    return out


def test_no_infra_world_model_dotted_imports():
    """Pattern 1 (Phase 34 N.14 lesson #4 audit): no 'from infra.world_model.X' imports."""
    bad: list[tuple[str, int, str]] = []
    for p in _all_python_files_under("packages", "apps", "tests", "infra"):
        if "infra/world_model/" in str(p) or "packages/lingwen-world-model/" in str(p):
            continue
        text = p.read_text()
        for lineno, line in enumerate(text.splitlines(), 1):
            if "from infra.world_model" in line or "from infra import world_model" in line:
                bad.append((str(p.relative_to(REPO_ROOT)), lineno, line.strip()))
    assert not bad, "Stale 'from infra.world_model' imports:\n" + "\n".join(
        f"  {f}:{ln}: {l}" for f, ln, l in bad
    )


def test_no_infra_subplot_helpers_dotted_imports():
    """Pattern 1 (audit): no 'from infra.subplot.helpers' imports."""
    bad: list[tuple[str, int, str]] = []
    for p in _all_python_files_under("packages", "apps", "tests", "infra"):
        if "infra/subplot/" in str(p) or "packages/lingwen-world-model/" in str(p):
            continue
        text = p.read_text()
        for lineno, line in enumerate(text.splitlines(), 1):
            if "from infra.subplot.helpers" in line:
                bad.append((str(p.relative_to(REPO_ROOT)), lineno, line.strip()))
    assert not bad, "Stale 'from infra.subplot.helpers' imports:\n" + "\n".join(
        f"  {f}:{ln}: {l}" for f, ln, l in bad
    )


def test_no_infra_world_model_filesystem_path_literals():
    """Pattern 4 (Phase 34 N.14 lesson #4, 5th occurrence): no filesystem path string literals.

    Exception: tests/test_phase32_shim_cleanup.py:30 keeps the historical
    'infra/world_model/data_structures.py' entry as documentation of what was
    deleted in Phase 32 (also excluded from _all_python_files_under).
    """
    bad: list[tuple[str, int, str]] = []
    for p in _all_python_files_under("packages", "apps", "tests", "infra"):
        if "infra/world_model/" in str(p) or "packages/lingwen-world-model/" in str(p):
            continue
        text = p.read_text()
        for lineno, line in enumerate(text.splitlines(), 1):
            # Match string literals like "infra/world_model/..." or "infra/subplot/helpers"
            if '"infra/world_model' in line or '"infra/subplot/helpers' in line:
                bad.append((str(p.relative_to(REPO_ROOT)), lineno, line.strip()))
    assert not bad, "Stale filesystem-path literals:\n" + "\n".join(
        f"  {f}:{ln}: {l}" for f, ln, l in bad
    )


def test_no_infra_world_model_dotpath_anywhere():
    """Pattern 5 (catch-all): no usage of 'infra.world_model.X' identifier anywhere.

    Skips lines that are comments (# ...) or string literals in docstrings
    (which the grep below already handles by skipping comment-prefixed lines).
    """
    bad: list[tuple[str, int, str]] = []
    for p in _all_python_files_under("packages", "apps", "tests", "infra"):
        if "infra/world_model/" in str(p) or "packages/lingwen-world-model/" in str(p):
            continue
        text = p.read_text()
        for lineno, line in enumerate(text.splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue  # pure comment line
            if "infra.world_model" in line:
                bad.append((str(p.relative_to(REPO_ROOT)), lineno, line.strip()))
    assert not bad, "Stale 'infra.world_model' dotpath usage:\n" + "\n".join(
        f"  {f}:{ln}: {l}" for f, ln, l in bad
    )


# ============ G5: Invariant #50 in architecture.yml ============


def test_invariant_50_in_architecture_yaml():
    """.lingwen/architecture.yml must declare invariant #50 for lingwen-world-model canonical."""
    import yaml
    with open(REPO_ROOT / ".lingwen" / "architecture.yml") as f:
        data = yaml.safe_load(f)
    invariants = data.get("invariants", [])
    ids = [i["id"] for i in invariants]
    assert "I050" in ids, f"Invariant #50 missing; found: {ids}"
    i050 = next(i for i in invariants if i["id"] == "I050")
    assert "lingwen-world-model" in i050["rule"]
    assert "infra.world_model" in i050["rule"]


# ============ G6: Test files migrated ============


def test_world_model_tests_in_new_package():
    """13 in-package test files must exist in packages/lingwen-world-model/tests/."""
    expected = [
        "test_character_snapshot.py", "test_integration.py",
        "test_key_point_graph.py", "test_links.py",
        "test_phase2_integration.py", "test_ripple_engine.py",
        "test_ripple_integration.py", "test_ripple_lifecycle.py",
        "test_ripple_queries.py", "test_ripple_registry.py",
        "test_snapshot_diff.py", "test_snapshot_store.py",
        "test_world_snapshot.py",
    ]
    tests_dir = REPO_ROOT / "packages" / "lingwen-world-model" / "tests"
    for name in expected:
        assert (tests_dir / name).is_file(), f"Missing {name}"


def test_old_tests_world_model_directory_empty():
    """tests/world_model/ must be empty (or contain only __pycache__/, gitignored)."""
    old_dir = REPO_ROOT / "tests" / "world_model"
    if old_dir.exists():
        # Only __pycache__ should remain (gitignored)
        non_cache = [p for p in old_dir.iterdir() if p.name != "__pycache__"]
        assert not non_cache, f"Stray files in tests/world_model/: {non_cache}"


# ============ G7: External consumers migrated ============


def test_poc_consumer_migrated():
    """infra/poc/run_volume_1.py must import from lingwen_world_model (not infra.world_model)."""
    p = REPO_ROOT / "infra" / "poc" / "run_volume_1.py"
    if not p.exists():
        return  # file may have been removed in a later phase
    text = p.read_text()
    assert "from infra.world_model" not in text, "POC still imports infra.world_model"
    assert "from lingwen_world_model" in text, "POC must import lingwen_world_model"
    # String literal also updated (Phase 34 lesson #4, 5th occurrence)
    assert "infra.world_model.WorldSnapshot" not in text, "POC has stale source string literal"


def test_subplot_test_migrated():
    """tests/subplot/test_subplot_integration.py must import subplot_helpers from lingwen_world_model."""
    p = REPO_ROOT / "tests" / "subplot" / "test_subplot_integration.py"
    if not p.exists():
        return
    text = p.read_text()
    assert "from infra.subplot.helpers" not in text, "test_subplot_integration.py still uses infra.subplot.helpers"
    assert "from lingwen_world_model.subplot_helpers" in text, "test must import lingwen_world_model.subplot_helpers"


def test_consistency_tests_migrated():
    """tests/consistency/checkers/{pacing_ripple_integration,foreshadow_ripple_alignment}.py must use lingwen_world_model."""
    files = [
        "tests/consistency/checkers/test_pacing_ripple_integration.py",
        "tests/consistency/checkers/test_foreshadow_ripple_alignment.py",
    ]
    for f in files:
        text = (REPO_ROOT / f).read_text()
        assert "from infra.world_model" not in text, f"{f} still imports infra.world_model"
        assert "from lingwen_world_model" in text, f"{f} must import lingwen_world_model"
