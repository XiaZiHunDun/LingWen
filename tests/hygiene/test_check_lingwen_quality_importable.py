"""Regression tests for tooling/hygiene/check_lingwen_quality_importable.py.

Phase 126 v16.5 #N.16 Task 1 — closes v15.7.1 debt claim "lingwen_quality module missing"
by ensuring the CI guard runs and correctly fails when symbols disappear.
"""
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "tooling"
    / "hygiene"
    / "check_lingwen_quality_importable.py"
)


def test_check_script_exists():
    """The CI guard script must exist at the expected path."""
    assert SCRIPT_PATH.exists(), f"Missing CI guard script at {SCRIPT_PATH}"


def test_check_script_returns_zero_when_all_symbols_importable():
    """Running the script in a clean environment should exit 0 and report PASSED."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(SCRIPT_PATH.parent.parent.parent),
    )
    assert result.returncode == 0, (
        f"Script failed unexpectedly: stderr={result.stderr!r}, "
        f"stdout={result.stdout!r}"
    )
    assert "PASSED" in result.stdout, (
        f"Expected PASSED in stdout, got: {result.stdout!r}"
    )


def test_check_script_fails_when_symbol_missing():
    """Verify the script exits non-zero when a required module is unimportable.

    Uses a MetaPathFinder wrapper to force ImportError for one specific module
    in a subprocess, then verifies the failure is reported.
    """
    wrapper = f"""
import sys

class BlockingFinder:
    def find_spec(self, name, path=None, target=None):
        if name == "lingwen_quality.consistency.engine.data_structures":
            raise ImportError("Forced failure for testing")
        return None

sys.meta_path.insert(0, BlockingFinder())

# Remove cached module so the blocker takes effect on re-import
sys.modules.pop("lingwen_quality.consistency.engine.data_structures", None)

exec(open(r"{SCRIPT_PATH}").read())
"""
    result = subprocess.run(
        [sys.executable, "-c", wrapper],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0, (
        f"Script should have failed: stdout={result.stdout!r}, "
        f"stderr={result.stderr!r}"
    )
    assert "FAILED" in result.stderr, (
        f"Expected FAILED in stderr, got: {result.stderr!r}"
    )
