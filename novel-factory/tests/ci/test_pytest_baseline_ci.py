"""Phase 12.09: pytest baseline >= 3000 collected."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

NOVEL_FACTORY = Path(__file__).resolve().parents[2]


class TestPytestBaseline1209:
    def test_collected_at_least_3000(self):
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            "--ignore=tests/agent_system/test_e2e_workflow.py",
            "--ignore=tests/tools/test_enhancement_tools.py",
            "--collect-only",
            "-q",
        ]
        proc = subprocess.run(
            cmd,
            cwd=NOVEL_FACTORY,
            capture_output=True,
            text=True,
            check=True,
        )
        out = proc.stdout + proc.stderr
        import re

        match = re.search(r"(\d+)\s+tests collected", out)
        assert match, f"could not parse collect-only output:\n{out}"
        count = int(match.group(1))
        assert count >= 3000, f"expected >=3000 collected, got {count}"
