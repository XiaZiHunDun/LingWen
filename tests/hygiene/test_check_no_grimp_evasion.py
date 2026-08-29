"""Unit tests for the grimp-evasion hygiene check."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "tooling"
    / "hygiene"
    / "check_no_grimp_evasion.py"
)


def test_check_passes_on_clean_port_adapter() -> None:
    """Current port_adapter.py (v16.5) must pass the check."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        cwd=str(SCRIPT.parent.parent.parent),
    )
    assert result.returncode == 0, (
        f"Hygiene check failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    assert "grimp-evasion-free" in result.stdout


def test_check_script_importable() -> None:
    """The check module must be importable for direct unit testing."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("check_no_grimp_evasion", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Verify the three check functions exist
    assert callable(module.check_static_import)
    assert callable(module.check_string_concat_evasion)
    assert callable(module.check_pep562_re_export)
    # Run them on the actual port_adapter.py — all should return empty
    assert module.check_static_import() == []
    assert module.check_string_concat_evasion() == []
    assert module.check_pep562_re_export() == []
