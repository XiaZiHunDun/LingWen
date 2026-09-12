"""Phase 53b tools/ legacy cleanup — regression guards.

These guards prevent the four classes of bugs fixed in Phase 53b:

1. Broken shim: tools/llm_quality_deep_check.py was a 34-line back-compat
   shim that tried to re-export LLMService, a symbol that no longer
   exists (renamed to LLMServiceAdapter in the Phase 5 LLM_QUALITY
   split). The shim's `from tools.llm_quality import LLMService` raised
   ImportError, breaking the shim entirely.

2. Stale test patch paths: tests/tools/test_llm_quality_deep_check.py
   used `patch("tools.llm_quality_deep_check.LLMService")` which
   referenced a non-existent symbol. Test failures (8 ERROR) cascaded
   from the broken shim.

3. Production stale import: packages/lingwen-cli/.../check.py:167 used
   `from tools.llm_quality_deep_check import LLMQualityChecker` which
   would fail at runtime once the shim is gone.

4. Missing fixture override: TestComprehensiveQualityChecker.
   test_chapter_file_parsing set project_root but not chapters_dir,
   so get_chapter_files() scanned the wrong directory and returned 0.

Each guard is a static source-level check or a smoke import.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SHIM = REPO_ROOT / "tools" / "llm_quality_deep_check.py"
SHIM_TEST = REPO_ROOT / "tests" / "tools" / "test_llm_quality_deep_check.py"
CHECK_CMD = (
    REPO_ROOT
    / "packages"
    / "lingwen-cli"
    / "src"
    / "lingwen_cli"
    / "commands"
    / "check.py"
)

# Match actual Python import of tools.llm_quality_deep_check
_STALE_SHIM_IMPORT_RE = re.compile(
    r"(?:^|\n)\s*(?:from|import)\s+tools\.llm_quality_deep_check\b"
)


# ---------------------------------------------------------------------------
# Guard 1: Shim re-exports the 3 canonical symbols and NOT LLMService
# ---------------------------------------------------------------------------
class TestShimContract:
    def test_shim_imports_canonical_symbols(self):
        """The shim must still re-export LLMQualityChecker, QualityReport, main."""
        from tools.llm_quality_deep_check import (
            LLMQualityChecker,
            QualityReport,
            main,
        )

        assert LLMQualityChecker is not None
        assert QualityReport is not None
        assert callable(main)

    def test_shim_does_not_export_llmservice(self):
        """The shim must NOT re-export LLMService (renamed in Phase 5 split)."""
        import tools.llm_quality_deep_check as shim_mod

        assert not hasattr(shim_mod, "LLMService"), (
            "shim must not re-export LLMService — it does not exist in the "
            "new subpackage. Tests should use canonical LLMServiceAdapter or "
            "constructor injection instead."
        )

    def test_shim_docstring_documents_three_symbols(self):
        """Belt-and-braces: docstring explicitly mentions the 3 symbols."""
        text = SHIM.read_text(encoding="utf-8")
        for symbol in ("LLMQualityChecker", "QualityReport", "main"):
            assert symbol in text, f"shim docstring must mention {symbol}"
        # LLMService is intentionally not mentioned anymore
        assert "LLMService" not in text or "Phase 53b" in text, (
            "shim docstring should not document LLMService as a re-exported symbol"
        )


# ---------------------------------------------------------------------------
# Guard 2: test file uses canonical paths, not shim paths
# ---------------------------------------------------------------------------
class TestShimTestFileContract:
    def test_test_file_uses_canonical_paths(self):
        """The test file should import from tools.llm_quality, not the shim.

        Using the shim would be technically valid but defeats the purpose
        of the canonical subpackage.
        """
        text = SHIM_TEST.read_text(encoding="utf-8")
        # Must have canonical imports
        assert "from tools.llm_quality import" in text, (
            "test file must use canonical tools.llm_quality imports"
        )
        # Must NOT actively call patch() on the stale LLMService symbol.
        # Match `patch("...LLMService")` as a function call (with paren),
        # not as a docstring mention. A bare docstring reference like
        # "originally patched ... .LLMService" is allowed.
        assert not re.search(
            r'\bpatch\(\s*["\']tools\.llm_quality_deep_check\.LLMService',
            text,
        ), "test must not call patch() on the stale LLMService symbol"

    def test_test_file_no_stale_imports(self):
        """Belt-and-braces: no `from tools.llm_quality_deep_check` imports."""
        text = SHIM_TEST.read_text(encoding="utf-8")
        for m in _STALE_SHIM_IMPORT_RE.finditer(text):
            line_num = text[: m.start()].count("\n") + 1
            pytest.fail(
                f"line {line_num}: stale shim import "
                f"{m.group(0).strip()!r} — use canonical tools.llm_quality"
            )

    def test_test_file_uses_constructor_injection(self):
        """The test must use `LLMQualityChecker(llm_service=mock)` pattern
        (no patching gymnastics)."""
        text = SHIM_TEST.read_text(encoding="utf-8")
        assert "LLMQualityChecker(llm_service=" in text, (
            "test must use constructor injection pattern: "
            "LLMQualityChecker(llm_service=mock)"
        )

    def test_test_file_sets_both_project_root_and_chapters_dir(self):
        """The test_chapter_file_parsing fix (C4): the comprehensive
        checker test must set both project_root AND chapters_dir so
        get_chapter_files() scans the correct directory.
        """
        text = SHIM_TEST.read_text(encoding="utf-8")
        # Find the TestComprehensiveQualityChecker class block
        cls_match = re.search(
            r"class TestComprehensiveQualityChecker.*?(?=\nclass |\Z)",
            text,
            re.DOTALL,
        )
        assert cls_match, "TestComprehensiveQualityChecker class not found"
        block = cls_match.group(0)
        # Both project_root and chapters_dir overrides must be present
        assert "project_root =" in block, "missing project_root override"
        assert "chapters_dir =" in block, (
            "missing chapters_dir override — get_chapter_files() will scan "
            "the wrong directory and return 0"
        )


# ---------------------------------------------------------------------------
# Guard 3: Production code does not import the shim (except in known sites)
# ---------------------------------------------------------------------------
class TestProductionNoShimImports:
    def test_check_command_uses_canonical_path(self):
        """packages/lingwen-cli/.../check.py must import LLMQualityChecker
        from canonical tools.llm_quality, not the shim."""
        text = CHECK_CMD.read_text(encoding="utf-8")
        # The exact change in C3: shim → canonical
        assert "from tools.llm_quality import LLMQualityChecker" in text, (
            "check.py must use canonical import"
        )
        assert "from tools.llm_quality_deep_check" not in text, (
            "check.py must not import from the shim"
        )

    def test_no_shim_imports_in_packages(self):
        """Repo-wide: no production code in packages/ uses the shim path."""
        import subprocess

        result = subprocess.run(
            [
                "grep",
                "-rln",
                "--include=*.py",
                "-E",
                r"(^|\n)\s*(from|import)\s+tools\.llm_quality_deep_check\b",
                str(REPO_ROOT / "packages"),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        files = [line for line in result.stdout.splitlines() if line.strip()]
        assert not files, (
            "stray shim imports in production code: " + ", ".join(files)
        )

    def test_no_shim_imports_in_apps(self):
        """Repo-wide: no production code in apps/ uses the shim path."""
        import subprocess

        result = subprocess.run(
            [
                "grep",
                "-rln",
                "--include=*.py",
                "-E",
                r"(^|\n)\s*(from|import)\s+tools\.llm_quality_deep_check\b",
                str(REPO_ROOT / "apps"),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        files = [line for line in result.stdout.splitlines() if line.strip()]
        assert not files, "stray shim imports in apps/: " + ", ".join(files)


# ---------------------------------------------------------------------------
# Guard 4: End-to-end smoke
# ---------------------------------------------------------------------------
def test_full_smoke():
    """Canonical symbols work end-to-end via both shim and direct paths."""
    # Direct canonical
    from tools.llm_quality import LLMQualityChecker as Direct
    from tools.llm_quality import QualityReport as DirectReport

    # Via shim (back-compat)
    from tools.llm_quality_deep_check import LLMQualityChecker as Shimmed
    from tools.llm_quality_deep_check import QualityReport as ShimReport

    # They must be the same class objects (shim is a pure re-export)
    assert Direct is Shimmed
    assert DirectReport is ShimReport
