import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _run_lingwen(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("LINGWEN_PROJECT_ROOT", None)
    return subprocess.run(
        [sys.executable, "lingwen.py", *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=env,
    )


def test_lingwen_help():
    result = _run_lingwen("--help")
    assert result.returncode == 0

def test_lingwen_doctor():
    result = _run_lingwen("doctor")
    assert result.returncode == 0
    assert "系统诊断" in result.stdout

def test_lingwen_status():
    result = _run_lingwen("status", "1-3")
    assert result.returncode == 0
