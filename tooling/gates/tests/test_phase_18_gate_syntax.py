"""Phase 18 Gate 脚本守卫 — syntax + executable 验证。"""
from pathlib import Path
import subprocess

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "tooling" / "gates" / "phase_18.sh"


def test_phase_18_gate_exists():
    assert SCRIPT.exists(), "phase_18.sh should exist"


def test_phase_18_gate_is_executable():
    import os

    mode = SCRIPT.stat().st_mode
    assert mode & 0o111, "phase_18.sh must be executable"


def test_phase_18_gate_passes_syntax_check():
    r = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
    assert r.returncode == 0, f"phase_18.sh has syntax error: {r.stderr}"