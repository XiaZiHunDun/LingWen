"""Phase 58: 5 regression guards for cross_volume 16 failures fix.

RC1 (4 fails): tests use legacy dashboard.X import paths; production uses
canonical apps.studio_api.X.
RC2 (12 fails): Command.__init__ eagerly validates ProjectPaths.get().

Run from any cwd:
    .venv/bin/python -m pytest tests/test_phase58_cross_volume_failures.py -v
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_PY = REPO_ROOT / "packages/lingwen-cli/src/lingwen_cli/commands/base.py"

CROSS_VOLUME_TESTS_DIR = REPO_ROOT / "packages/lingwen-cross-volume/tests"


class TestLazyCommandInit:
    """G1+G2: Command.__init__ must NOT eagerly resolve ProjectPaths."""

    def test_g1_no_eager_project_paths_get_in_init(self):
        """base.py Command.__init__ body must not call ProjectPaths.get() directly."""
        content = BASE_PY.read_text(encoding="utf-8")
        match = re.search(r"def __init__\(self\):\n((?:    .*\n)*)", content)
        assert match, "Command.__init__ not found"
        init_body = match.group(1)
        assert "ProjectPaths.get()" not in init_body, (
            "Phase 58 G1: Command.__init__ must lazily init paths "
            "(eager ProjectPaths.get() breaks 12 test constructions)"
        )

    def test_g2_no_eager_project_max_chapter_in_init(self):
        """base.py Command.__init__ body must not call project_max_chapter."""
        content = BASE_PY.read_text(encoding="utf-8")
        match = re.search(r"def __init__\(self\):\n((?:    .*\n)*)", content)
        assert match, "Command.__init__ not found"
        init_body = match.group(1)
        assert "project_max_chapter(" not in init_body, (
            "Phase 58 G2: Command.__init__ must not call project_max_chapter "
            "(depends on paths which is lazy)"
        )


class TestCanonicalPathsInCrossVolumeTests:
    """G3: No 'dashboard.X' import paths in cross_volume test files."""

    def test_g3_no_dashboard_imports_in_cross_volume_tests(self):
        """Cross-volume tests must NOT use legacy dashboard.X import paths.

        Legacy path never existed as a Python module (dashboard/ is Vue frontend).
        Canonical: apps.studio_api.X (matches lingwen_cross_volume/storage.py).
        """
        offenders: list[tuple[str, int, str]] = []
        pattern = re.compile(r'dashboard\.(cvg_ws|cascade_notifier|app)\b')
        for test_file in CROSS_VOLUME_TESTS_DIR.glob("test_*.py"):
            for i, line in enumerate(test_file.read_text(encoding="utf-8").splitlines(), 1):
                if pattern.search(line):
                    offenders.append((str(test_file.relative_to(REPO_ROOT)), i, line.strip()))
        assert not offenders, (
            "Phase 58 G3: cross_volume tests use legacy dashboard.X paths.\n"
            "Canonical is apps.studio_api.X (Phase 56c).\n"
            f"Offenders: {offenders}"
        )


class TestCrossVolumeSuiteGreen:
    """G4+G5: 220/220 cross_volume tests pass after fix."""

    def test_g4_all_cross_volume_tests_pass(self):
        """220/220 cross_volume tests pass (Phase 58 baseline)."""
        result = subprocess.run(
            [
                sys.executable, "-m", "pytest",
                str(CROSS_VOLUME_TESTS_DIR),
                "--tb=no", "-q", "--no-header",
            ],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        output = result.stdout + result.stderr
        # Look for "N failed" in tail
        last_lines = output.splitlines()[-10:]
        failed_match = re.search(r"(\d+)\s+failed", "\n".join(last_lines))
        if failed_match:
            fail_count = int(failed_match.group(1))
            assert fail_count == 0, (
                f"Phase 58 G4: {fail_count} cross_volume tests still failing.\n"
                f"Last 10 lines: {last_lines}"
            )
        # Also check exit code
        assert result.returncode == 0, (
            f"Phase 58 G4: cross_volume pytest exit {result.returncode}\n"
            f"Last 10 lines: {last_lines}"
        )

    def test_g5_lazy_command_construction_succeeds_without_chapters_dir(self):
        """BackfillCommand() can be instantiated without a valid chapters dir.

        After RC2 fix, Command.__init__ no longer calls ProjectPaths.get().
        Tests construct BackfillCommand/RippleScanCommand with full mocking;
        they should never hit ProjectPaths validation.
        """
        result = subprocess.run(
            [
                sys.executable, "-c",
                "from lingwen_cli.commands.backfill import BackfillCommand; "
                "from lingwen_cli.commands.ripple_scan import RippleScanCommand; "
                "b = BackfillCommand(); "
                "r = RippleScanCommand(); "
                "print('OK')",
            ],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, (
            f"Phase 58 G5: Command construction still requires chapters dir.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert "OK" in result.stdout
