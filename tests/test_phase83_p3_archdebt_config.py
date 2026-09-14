"""Phase 83 regression guards — P3-ARCHDEBT infra/config → packages/lingwen-config.

Closure of ARCHDEBT-CANDIDATES.md Top 5 candidate #5 (LAST in Top 5 cluster — 77 LOC,
2 source files, 5 consumer sites [3 cross-pkg tools + 1 intra-infra + 1 intra-subdir],
TRUE LEAF + 1 third-party dep pyyaml, I084 NEW invariant). Per I079 template §A —
Phase 83 has NO test files to MIGRATE.

12 guards G1-G12 validate:
- G1  infra/config/ directory gone (no __pycache__ residue)
- G2  2 specific source files gone (parametrized)
- G3  (no test files to MIGRATE — n/a)
- G4  packages/lingwen-config/ exists
- G5  3 source files at new location (pyproject.toml + 2 modules)
- G6  (no test dir to scaffold — n/a)
- G7  0 infra.config refs in production (packages/ + tools/)
- G8  (no new tests — n/a)
- G9  I084 row in CLAUDE.md invariant table
- G10 I084 row in .lingwen/architecture.yml
- G11 prior-phase guards updated (test_phase53d + test_phase18_8)
- G12 functional import gate: lingwen_config imports + 3 tools/ consumers work
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# G1 + G2: infra/config/ fully deleted
# ---------------------------------------------------------------------------


def test_phase83_g1_infra_config_directory_gone() -> None:
    """G1: infra/config/ directory must not exist (no .py files,
    no __pycache__ residue). Phase 83 C3 FULL DELETE + C3 cleanup."""
    p = REPO_ROOT / "infra" / "config"
    assert not p.exists(), (
        "infra/config/ must be gone (Phase 83 C3 FULL DELETE). "
        "If __pycache__ residue, see Phase 79 v23 lesson."
    )


@pytest.mark.parametrize(
    "filename",
    [
        "__init__.py",
        "api_config_loader.py",
    ],
)
def test_phase83_g2_source_file_deleted(filename: str) -> None:
    """G2: each of 2 source files in infra/config/ must be gone."""
    p = REPO_ROOT / "infra" / "config" / filename
    assert not p.exists(), f"infra/config/{filename} must be gone"


# ---------------------------------------------------------------------------
# G3: (no test files to MIGRATE — n/a for Phase 83)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# G4 + G5: new package scaffolded correctly
# ---------------------------------------------------------------------------


def test_phase83_g4_package_exists() -> None:
    """G4: packages/lingwen-config/ must exist with pyproject.toml."""
    pkg = REPO_ROOT / "packages" / "lingwen-config"
    assert pkg.is_dir(), "packages/lingwen-config/ must exist"
    assert (pkg / "pyproject.toml").is_file(), "pyproject.toml must exist"


@pytest.mark.parametrize(
    "filename",
    [
        "pyproject.toml",
        "src/lingwen_config/__init__.py",
        "src/lingwen_config/api_config_loader.py",
    ],
)
def test_phase83_g5_package_file_exists(filename: str) -> None:
    """G5: 3 specific files at new location (pyproject + 2 modules)."""
    p = REPO_ROOT / "packages" / "lingwen-config" / filename
    assert p.is_file(), f"packages/lingwen-config/{filename} must exist"


# ---------------------------------------------------------------------------
# G6: (no test dir to scaffold — n/a for Phase 83)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# G7: zero infra.config refs in production
# ---------------------------------------------------------------------------


def test_phase83_g7_no_infra_refs_in_production() -> None:
    """G7: 0 infra.config refs in production code (packages/, infra/__init__.py,
    tools/). Excludes tests/ + __pycache__/."""
    result = subprocess.run(
        [
            "grep",
            "-rln",
            "--include=*.py",
            r"infra\.config",
            str(REPO_ROOT / "packages"),
            str(REPO_ROOT / "tools"),
        ],
        capture_output=True,
        text=True,
    )
    matches = [
        line for line in result.stdout.splitlines()
        if line and "/__pycache__/" not in line
    ]
    assert not matches, (
        f"infra.config refs found in production: {matches}. "
        f"Should all be lingwen_config."
    )


# ---------------------------------------------------------------------------
# G8: (no new tests — n/a for Phase 83)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# G9 + G10: I084 invariant declared in CLAUDE.md + architecture.yml
# ---------------------------------------------------------------------------


def test_phase83_g9_i084_in_claude_md() -> None:
    """G9: I084 row in CLAUDE.md invariant table."""
    claude_md = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert re.search(r"\| I084 \|", claude_md), (
        "I084 must appear in CLAUDE.md invariant table (Phase 83 NEW)"
    )


def test_phase83_g10_i084_in_architecture_yml() -> None:
    """G10: I084 entry in .lingwen/architecture.yml invariants list."""
    arch_yml = (REPO_ROOT / ".lingwen" / "architecture.yml").read_text(
        encoding="utf-8"
    )
    assert re.search(r"^\s*-\s*id:\s*I084\b", arch_yml, re.MULTILINE), (
        "I084 must appear in .lingwen/architecture.yml (Phase 83 NEW)"
    )


# ---------------------------------------------------------------------------
# G11: prior-phase guards updated (no config in remaining_subdirs list)
# ---------------------------------------------------------------------------


def test_phase83_g11_prior_phase_guards_updated() -> None:
    """G11: test_phase53d remaining_subdirs list must not include 'config'
    (would fail because config/ is now gone — Phase 83 C4 fixup)."""
    test_phase53d = (
        REPO_ROOT / "tests" / "test_phase53d_event_sourcing.py"
    ).read_text(encoding="utf-8")
    # Strip docstring + assert-not-exists block to isolate remaining_subdirs
    stripped = re.sub(r'""".*?""""', "", test_phase53d, flags=re.DOTALL)
    stripped = re.sub(
        r"# And the deleted subdirs.*$", "", stripped, flags=re.DOTALL
    )
    assert '"config"' not in stripped, (
        "test_phase53d remaining_subdirs still lists 'config' "
        "(N.14 v22 lesson — closed-list breaks on sibling deletion)"
    )


# ---------------------------------------------------------------------------
# G12: functional import gate (lingwen_config + 3 tools/ consumers + infra re-export)
# ---------------------------------------------------------------------------


def test_phase83_g12_functional_import_gate() -> None:
    """G12: lingwen_config APIConfig singleton + infra compat re-export +
    3 cross-pkg tools/ consumers work after Phase 83 C2 rewrite."""
    # Use a script file to avoid shell escaping issues with f-strings
    script_path = REPO_ROOT / "tests" / "_phase83_g12_script.py"
    script_content = '''
import importlib.util
import sys
sys.path.insert(0, ".")

# Test lingwen_config imports
from lingwen_config import APIConfig
from lingwen_config.api_config_loader import get_api_config

# Test infra compat re-export
import infra
assert infra.APIConfig is APIConfig, "infra.APIConfig must be lingwen_config.APIConfig"

# Test 3 tools/ consumers (load via importlib to avoid running main code)
tools = [
    "tools/anti_trope_enhancer.py",
    "tools/claude_key_chapter_polisher.py",
    "tools/llm_quality_analyzer.py",
]
for tool_path in tools:
    spec = importlib.util.spec_from_file_location("mod", tool_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    print(f"OK: {tool_path}")

print("ALL_OK")
'''
    script_path.write_text(script_content, encoding="utf-8")
    try:
        result = subprocess.run(
            [".venv/bin/python", str(script_path)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, (
            f"Functional import gate failed (rc={result.returncode}):\n"
            f"STDOUT: {result.stdout[-500:]}\n"
            f"STDERR: {result.stderr[-500:]}"
        )
        assert "ALL_OK" in result.stdout, (
            f"Functional import gate didn't print ALL_OK:\n{result.stdout[-500:]}"
        )
    finally:
        script_path.unlink(missing_ok=True)