"""Pyproject layout regression test for v16.0 uv workspace migration.

Verifies:
- Root pyproject.toml declares [tool.uv.workspace] with members
- Each member directory exists with its own pyproject.toml
- Each member declares a Python package name
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest  # noqa: F401 — pytest test module

REPO_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_MEMBERS = [
    "packages/lingwen-core",
    "packages/lingwen-storage",
    "packages/lingwen-llm",
    "packages/lingwen-memory",
    "packages/lingwen-prompt",
    "packages/lingwen-pipeline",
    "packages/lingwen-quality",
    "packages/lingwen-cli",
    "apps/studio_api",
]


def _read_toml(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_section(text: str, header: str) -> str | None:
    """Return the body of a TOML ``[header]`` section, or None if missing."""
    pattern = re.compile(rf"^\[{re.escape(header)}\]\s*(.*?)(?=^\[|\Z)", re.MULTILINE | re.DOTALL)
    m = pattern.search(text)
    return m.group(1).strip() if m else None


def test_root_pyproject_declares_uv_workspace() -> None:
    """Root pyproject.toml must declare a [tool.uv.workspace] section."""
    text = _read_toml(REPO_ROOT / "pyproject.toml")
    section = _extract_section(text, "tool.uv.workspace")
    assert section is not None, (
        "root pyproject.toml missing [tool.uv.workspace] section — v16.0 plan §6.2 T2 requires uv workspaces"
    )


def test_root_pyproject_members_includes_all_expected() -> None:
    """Workspace members must list every expected package directory."""
    text = _read_toml(REPO_ROOT / "pyproject.toml")
    section = _extract_section(text, "tool.uv.workspace")
    assert section is not None
    for member in EXPECTED_MEMBERS:
        member_glob = member.split("/")[-1]  # e.g. 'lingwen-core'
        assert member in section or member_glob in section, (
            f"workspace missing member {member!r} — found section:\n{section}"
        )


def test_root_pyproject_declares_uv_sources() -> None:
    """Workspace sources must list internal package aliases."""
    text = _read_toml(REPO_ROOT / "pyproject.toml")
    section = _extract_section(text, "tool.uv.sources")
    assert section is not None, "root pyproject.toml missing [tool.uv.sources]"


def test_each_member_has_pyproject_toml() -> None:
    """Each workspace member directory must contain its own pyproject.toml."""
    missing: list[str] = []
    for member in EXPECTED_MEMBERS:
        pyproject = REPO_ROOT / member / "pyproject.toml"
        if not pyproject.exists():
            missing.append(str(pyproject.relative_to(REPO_ROOT)))
    assert not missing, f"members missing pyproject.toml: {missing}"


def test_each_member_declares_project_section() -> None:
    """Each member must have a [project] section declaring a package name."""
    bad: list[str] = []
    for member in EXPECTED_MEMBERS:
        pyproject = REPO_ROOT / member / "pyproject.toml"
        if not pyproject.exists():
            continue  # covered by previous test
        text = _read_toml(pyproject)
        section = _extract_section(text, "project")
        if not section or "name" not in section:
            bad.append(str(pyproject.relative_to(REPO_ROOT)))
    assert not bad, f"members missing [project] section or name: {bad}"
