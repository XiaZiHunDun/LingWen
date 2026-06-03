import subprocess
import sys
from pathlib import Path


def test_lingwen_help():
    result = subprocess.run(
        [sys.executable, "lingwen.py", "--help"],
        capture_output=True, text=True
    )
    assert result.returncode == 0

def test_lingwen_doctor():
    result = subprocess.run(
        [sys.executable, "lingwen.py", "doctor"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "系统诊断" in result.stdout

def test_lingwen_status():
    result = subprocess.run(
        [sys.executable, "lingwen.py", "status", "1-3"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
