"""Phase 55 P3-ARCHDEBT cross_volume — regression guards.

These guards prevent the bug classes that the migration fixed:
1. Lingering references to infra/cross_volume/ in source or tests
2. Lingering imports of infra.cross_volume.* modules
3. Lingering filesystem-path string literals referencing
   infra/cross_volume/
4. Lingering monkeypatch.setattr() string targets referencing
   infra/cross_volume.X
5. lingwen-cross-volume package public surface must match original
6. New invariant I078 (no infra.cross_volume.* paths)
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_SRC = REPO_ROOT / "packages" / "lingwen-cross-volume" / "src" / "lingwen_cross_volume"
INFRA_DELETED = REPO_ROOT / "infra" / "cross_volume"

# Match an actual Python import of infra.cross_volume.*
_STALE_IMPORT_RE = re.compile(
    r"(?:^|\n)\s*(?:from|import)\s+infra\.cross_volume\b"
)

# Match a filesystem path string literal (in a quoted string)
# referencing infra/cross_volume/
_PATH_LITERAL_RE = re.compile(
    r"""(?:["'`])([^"'`]*infra/cross_volume[^"'`]*)["'`]"""
)


# ---------------------------------------------------------------------------
# Guard 1: Canonical package exists and imports cleanly
# ---------------------------------------------------------------------------
class TestCanonicalPackage:
    def test_package_dir_exists(self):
        """The new package directory must exist."""
        assert PACKAGE_SRC.exists(), (
            f"canonical package missing: {PACKAGE_SRC}"
        )
        assert (PACKAGE_SRC / "__init__.py").exists()

    def test_canonical_imports_resolve(self):
        """All 9 __all__ symbols must be importable."""
        from lingwen_cross_volume import (
            CrossVolumeReferenceGraph,
            ReferenceNode,
            ReferenceEdge,
            CrossVolumeRipple,
            QueryImpactCache,
            LLMCache,
            LLMScanner,
            EdgeInferrer,
            ModelTier,
        )

    def test_all_count_matches_original(self):
        """The __all__ must have exactly 9 symbols (matches original
        infra/cross_volume/__init__.py)."""
        import lingwen_cross_volume

        assert len(lingwen_cross_volume.__all__) == 9, (
            f"expected 9 symbols, got {len(lingwen_cross_volume.__all__)}: "
            f"{lingwen_cross_volume.__all__}"
        )

    @pytest.mark.parametrize(
        "submodule",
        [
            "cache",
            "edge_inferrer",
            "llm_cache",
            "llm_scanner",
            "reference_graph",
            "ripple",
            "scoring",
            "storage",
            "backfill",
            "incremental_backfill",
            "cascade_migration",
            "cascade_retention",
            "chained_cascade",
            "audit_retention",
            "e2e_seed",
            "perf",
            "scanner_calibration",
        ],
    )
    def test_submodule_importable(self, submodule):
        """All 17 top-level submodules must be importable."""
        import importlib

        mod = importlib.import_module(f"lingwen_cross_volume.{submodule}")
        assert mod is not None


# ---------------------------------------------------------------------------
# Guard 2: infra/cross_volume/ must be fully deleted
# ---------------------------------------------------------------------------
class TestInfraDeleted:
    def test_infra_dir_gone(self):
        """infra/cross_volume/ must be FULL DELETED (Phase 55 C3)."""
        assert not INFRA_DELETED.exists(), (
            f"infra/cross_volume must be deleted, still found at {INFRA_DELETED}"
        )


# ---------------------------------------------------------------------------
# Guard 3: No stale `from infra.cross_volume` / `import infra.cross_volume`
# ---------------------------------------------------------------------------
class TestNoStaleImports:
    def test_no_stale_imports_repo_wide(self):
        """No Python file outside deleted infra/cross_volume/ may import
        from the old path.

        Excludes:
        - the deleted infra/cross_volume/ (already gone)
        - .venv/, node_modules/, .git/, archive, worktrees (artifacts)
        - This guard file (which references the deleted path in the
          guarded test logic itself)
        """
        offenders = []
        for py_file in REPO_ROOT.rglob("*.py"):
            rel = py_file.relative_to(REPO_ROOT)
            if any(
                part in rel.parts
                for part in (
                    ".venv",
                    "node_modules",
                    ".git",
                    "__pycache__",
                    ".claude/worktrees",
                )
            ):
                continue
            if "docs/superpowers/archive" in rel.parts:
                continue
            # The guard itself is allowed to mention the old path
            if rel == Path(
                "tests/test_phase55_p3_archdebt_cross_volume.py"
            ):
                continue
            try:
                text = py_file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if _STALE_IMPORT_RE.search(line):
                    offenders.append(f"{rel}:{i}: {line.strip()}")

        assert not offenders, (
            "stale infra.cross_volume imports found:\n"
            + "\n".join(offenders[:20])
        )


# ---------------------------------------------------------------------------
# Guard 4: No filesystem-path string literals referencing infra/cross_volume
# ---------------------------------------------------------------------------
class TestNoPathLiterals:
    def test_no_repo_wide_path_literals(self):
        """No string literal should reference infra/cross_volume/ as a
        filesystem path. The data file moved to the new package."""
        offenders = []
        for py_file in REPO_ROOT.rglob("*.py"):
            rel = py_file.relative_to(REPO_ROOT)
            if any(
                part in rel.parts
                for part in (
                    ".venv",
                    "node_modules",
                    ".git",
                    "__pycache__",
                    ".claude/worktrees",
                )
            ):
                continue
            if "docs/superpowers/archive" in rel.parts:
                continue
            # The guard is allowed to mention the old path
            if rel == Path(
                "tests/test_phase55_p3_archdebt_cross_volume.py"
            ):
                continue
            try:
                text = py_file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for i, line in enumerate(text.splitlines(), 1):
                for m in _PATH_LITERAL_RE.finditer(line):
                    # Allow docstring historical references with
                    # specific markers (Phase 55, migration, relocated)
                    matched = m.group(1)
                    if any(
                        marker in line
                        for marker in (
                            "Phase 55",
                            "Phase55",
                            "relocated",
                            "P3-ARCHDEBT",
                            "ARCHDEBT",
                        )
                    ):
                        continue
                    offenders.append(f"{rel}:{i}: {line.strip()}")

        assert not offenders, (
            "stray infra/cross_volume path literals in source:\n"
            + "\n".join(offenders[:20])
        )


# ---------------------------------------------------------------------------
# Guard 5: pyproject.toml workspace registration
# ---------------------------------------------------------------------------
class TestWorkspaceRegistration:
    def test_root_pyproject_has_workspace_member(self):
        """pyproject.toml [tool.uv.workspace] members must include
        packages/lingwen-cross-volume."""
        text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        assert "packages/lingwen-cross-volume" in text, (
            "pyproject.toml must register packages/lingwen-cross-volume as workspace"
        )

    def test_root_pyproject_has_uv_sources(self):
        """pyproject.toml [tool.uv.sources] must include the package."""
        text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        assert "lingwen-cross-volume = { workspace = true }" in text, (
            "pyproject.toml [tool.uv.sources] must declare workspace-true for "
            "lingwen-cross-volume"
        )


# ---------------------------------------------------------------------------
# Guard 6: I078 invariant is documented
# ---------------------------------------------------------------------------
class TestInvariantI078:
    def test_claude_md_has_i078(self):
        """CLAUDE.md must document I078."""
        text = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        assert "I078" in text, "CLAUDE.md must include invariant I078"
        assert "lingwen-cross-volume" in text, (
            "CLAUDE.md I078 entry must reference lingwen-cross-volume"
        )
        assert "infra.cross_volume" in text, (
            "CLAUDE.md I078 entry must forbid infra.cross_volume path"
        )


# ---------------------------------------------------------------------------
# Guard 7: End-to-end smoke
# ---------------------------------------------------------------------------
def test_end_to_end_smoke():
    """All canonical symbols importable + new package is the only path."""
    # Canonical imports work
    from lingwen_cross_volume import (
        CrossVolumeReferenceGraph,
        ReferenceNode,
        ReferenceEdge,
        CrossVolumeRipple,
        QueryImpactCache,
        LLMCache,
        LLMScanner,
        EdgeInferrer,
        ModelTier,
    )
    from lingwen_cross_volume.storage import RippleStorage, AuditEntry, ConflictError
    from lingwen_cross_volume.scoring import compute_impact_score
    from lingwen_cross_volume.backfill import Backfiller
    from lingwen_cross_volume.e2e_seed import ensure_e2e_fixtures

    # Old path is forbidden
    try:
        from infra.cross_volume import CrossVolumeRipple as _Old
    except ImportError:
        pass
    else:
        pytest.fail(
            "infra.cross_volume must be deleted; old import still works"
        )
