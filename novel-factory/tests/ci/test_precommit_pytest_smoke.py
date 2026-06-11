"""Phase 9.58 F49: pre-commit backend pytest smoke contract tests."""
from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT / "novel-factory"
PRE_COMMIT_HOOK = (
    NOVEL_FACTORY / "dashboard" / "frontend" / ".husky" / "pre-commit"
)

# Keep in sync with .husky/pre-commit smoke subset (~30s budget).
SMOKE_PYTEST_ARGS = [
    "tests/ci/",
    "--ignore=tests/ci/test_precommit_pytest_smoke.py",
    "tests/dashboard/test_api.py::TestHealthEndpoint",
    "-q",
    "--timeout=30",
]


class TestPrecommitPytestSmokeContract:
    def test_precommit_hook_exists_and_is_opt_in(self):
        assert PRE_COMMIT_HOOK.is_file(), PRE_COMMIT_HOOK
        text = PRE_COMMIT_HOOK.read_text(encoding="utf-8")
        assert "LINGWEN_PRECOMMIT_PYTEST" in text
        assert "tests/ci/" in text
        assert "lint-staged" in text

    def test_smoke_subset_passes(self):
        result = subprocess.run(
            ["pytest", *SMOKE_PYTEST_ARGS],
            cwd=NOVEL_FACTORY,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
