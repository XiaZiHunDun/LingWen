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
- v16.5 #N.3 closes the remaining-packages carryover from v16.5 #4:
  the 8-file whitelist (Phase 15.0 T2.8 deprecated) was emptied — all
  8 files now use SqliteStorageAdapter from lingwen_storage.

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


# v16.5 #N.3: defense-in-depth gate for remaining packages
# (lingwen_core/pipeline/cli). The 8-file whitelist from v16.5 #4
# (Phase 15.0 T2.8 deprecated files) has been retired — all 8 files
# now use SqliteStorageAdapter from lingwen_storage. The simpler
# "no sqlite3 in remaining packages" grep gate enforces the
# architectural invariant going forward.


def test_no_sqlite3_imports_in_remaining_packages() -> None:
    """lingwen_core/pipeline/cli MUST NOT have direct sqlite3 imports.

    v16.5 #N.3: 8 whitelisted files migrated to SqliteStorageAdapter.
    No whitelist remains — any new direct sqlite3 import is a regression.

    Lingwen_storage.SqliteStorageAdapter is the canonical SQLite backend
    implementation. Business code in these packages should:
    - Use SqliteStorageAdapter for SQLite operations
    - Or implement lingwen_shared.ports.storage.StoragePort for alternate
      backends (in-memory test, future Postgres, etc.)
    """
    sources = [
        PROJECT_ROOT / "packages" / "lingwen-core" / "src",
        PROJECT_ROOT / "packages" / "lingwen-pipeline" / "src",
        PROJECT_ROOT / "packages" / "lingwen-cli" / "src",
    ]
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
                rel_path = str(py_file.relative_to(PROJECT_ROOT))
                violations.append(f"{rel_path}:{match.start()}")
    assert not violations, (
        "Direct sqlite3 imports found in remaining packages:\n  "
        + "\n  ".join(violations)
        + "\n\nDirect sqlite3 imports are forbidden in lingwen_core/pipeline/cli. "
        + "Use SqliteStorageAdapter from lingwen_storage.sqlite_storage_adapter "
        + "instead of importing sqlite3 directly.\n\n"
        + "Migration guide: see v16.5 #N.3 handoff "
        + "(docs/superpowers/handoffs/2026-08-30-phase-126-v16-5-n3-whitelisted-files-migration-handoff.md)."
    )
