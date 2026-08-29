"""Regression test — DP-03 enforcement: no concrete sqlite3 in business code.

DP-03 (Phase 126 v16.5 #2): business code (`apps/` + `lingwen_creator/`)
must go through the StoragePort abstraction instead of importing the
sqlite3 stdlib driver directly. This test enforces the architectural
invariant via two complementary gates:

1. **import-linter contract gate** (`test_lint_imports_reports_dp03_kept`):
   the `no_concrete_sqlite3_in_business_code` contract declared in
   `pyproject.toml [tool.importlinter.contracts]` must report KEPT.
   This catches contract removal/rename in pyproject.toml and ensures
   import-linter itself runs cleanly.

2. **grep gate** (`test_no_sqlite3_imports_in_business_code`): scans
   every `.py` file under `apps/` and `packages/lingwen-creator/src/`
   for direct `import sqlite3` or `from sqlite3` statements. This is
   the primary enforcement because import-linter's `forbidden` contract
   only checks `lingwen_creator` (see pyproject.toml comment about
   transitive imports via `apps → infra → sqlite3`).

Why both gates:
- import-linter is the documented architectural intent (visible in CI logs)
- grep is the actual enforcement (catches direct imports even if the
  contract is bypassed, e.g., via dynamic imports or string-concat
  workarounds discovered in v16.4 DP-02 grimp-evasion lessons)

History:
- v16.5 #1 closed the grimp-evasion hack for LLMServicePort (v16.4
  string-concat + PEP 562 workaround).
- v16.5 #2 (this task) extends the pattern to StoragePort.

Carryover:
- Future storage backends (Postgres, in-memory test backend) must
  implement `lingwen_shared.ports.storage.StoragePort` rather than
  introducing a new stdlib driver import in business code.
"""
from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = PROJECT_ROOT / "pyproject.toml"


def test_pyproject_has_dp03_forbidden_contract() -> None:
    """DP-03 forbidden contract must be declared in pyproject.toml."""
    config = tomllib.loads(PYPROJECT.read_text())
    contracts = config["tool"]["importlinter"]["contracts"]
    contract_names = {c["name"] for c in contracts}

    assert "no_concrete_sqlite3_in_business_code" in contract_names, (
        f"DP-03 forbidden contract missing. Found: {sorted(contract_names)}"
    )


def test_dp03_contract_targets_sqlite3() -> None:
    """DP-03 contract must forbid sqlite3 in lingwen_creator (business code)."""
    config = tomllib.loads(PYPROJECT.read_text())
    contracts = config["tool"]["importlinter"]["contracts"]
    dp03 = next(
        c for c in contracts if c["name"] == "no_concrete_sqlite3_in_business_code"
    )

    assert dp03["type"] == "forbidden", (
        f"DP-03 contract must be of type 'forbidden', got {dp03['type']!r}"
    )
    assert dp03["forbidden_modules"] == ["sqlite3"], (
        f"DP-03 must forbid exactly ['sqlite3'], got {dp03['forbidden_modules']!r}"
    )
    assert "lingwen_creator" in dp03["source_modules"], (
        f"DP-03 source_modules must include lingwen_creator, got {dp03['source_modules']!r}"
    )


def test_lint_imports_reports_dp03_kept() -> None:
    """lint-imports must report the DP-03 contract as KEPT.

    This is the integration smoke test — ensures the contract not only
    exists in pyproject.toml but is also syntactically valid and the
    current codebase satisfies it.
    """
    result = subprocess.run(
        ["lint-imports"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    output = (result.stdout or "") + (result.stderr or "")

    assert "no_concrete_sqlite3_in_business_code KEPT" in output, (
        f"DP-03 contract not reported as KEPT.\n"
        f"lint-imports exit={result.returncode}\noutput:\n{output}"
    )


def test_no_sqlite3_imports_in_business_code() -> None:
    """No file under apps/ or lingwen_creator/ should have a direct sqlite3 import.

    This is the defense-in-depth grep gate. import-linter only checks
    `lingwen_creator` (see pyproject.toml rationale), but a bare
    `import sqlite3` anywhere in business code violates the StoragePort
    abstraction. Catches direct violations regardless of import-linter's
    transitive limitations.
    """
    sources = [
        PROJECT_ROOT / "apps",
        PROJECT_ROOT / "packages" / "lingwen-creator" / "src",
    ]
    # Match `import sqlite3` or `from sqlite3 import ...` at module level.
    # Word boundary prevents false matches like `import sqlite3_utils`.
    pattern = re.compile(r"^\s*(?:from\s+sqlite3\b|import\s+sqlite3\b)", re.MULTILINE)

    violations: list[str] = []
    for src_root in sources:
        if not src_root.exists():
            continue
        for py_file in src_root.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for match in pattern.finditer(content):
                rel_path = py_file.relative_to(PROJECT_ROOT)
                violations.append(f"{rel_path}:{match.start()}")

    assert not violations, (
        "DP-03 violations found (sqlite3 imported directly in business code):\n  "
        + "\n  ".join(violations)
        + "\nBusiness code must go through StoragePort "
        + "(lingwen_shared.ports.storage) instead of importing sqlite3 directly."
    )
