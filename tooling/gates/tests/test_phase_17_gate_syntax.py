"""Phase 17 Gate 脚本语法与可执行性守卫。

确保 tooling/gates/phase_17.sh 存在、可执行、bash 语法正确。
"""
from pathlib import Path
import subprocess

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "tooling" / "gates" / "phase_17.sh"


def test_phase_17_gate_exists() -> None:
    assert SCRIPT.exists(), "phase_17.sh should exist"


def test_phase_17_gate_is_executable() -> None:
    mode = SCRIPT.stat().st_mode
    assert mode & 0o111, "phase_17.sh must be executable"


def test_phase_17_gate_passes_syntax_check() -> None:
    result = subprocess.run(
        ["bash", "-n", str(SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"phase_17.sh has syntax error: {result.stderr}"
    )
