"""Pyproject layout regression test for v16.1 lingwen-shared package.

Verifies:
- Root pyproject.toml [tool.uv.workspace] members includes packages/lingwen-shared
- packages/lingwen-shared/ exists with its own pyproject.toml
- packages/lingwen-shared/pyproject.toml declares [project] section
- lingwen-shared has hyphen name (packaging) but underscore module (importable)
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_toml(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_section(text: str, header: str) -> str | None:
    pattern = re.compile(rf"^\[{re.escape(header)}\]\s*(.*?)(?=^\[|\Z)", re.MULTILINE | re.DOTALL)
    m = pattern.search(text)
    return m.group(1).strip() if m else None


def test_lingwen_shared_in_workspace_members() -> None:
    """Root pyproject.toml must list packages/lingwen-shared as a workspace member."""
    text = _read_toml(REPO_ROOT / "pyproject.toml")
    section = _extract_section(text, "tool.uv.workspace")
    assert section is not None, "root pyproject.toml missing [tool.uv.workspace]"
    assert "packages/lingwen-shared" in section, (
        f"workspace missing packages/lingwen-shared — found section:\n{section}"
    )


def test_lingwen_shared_directory_exists() -> None:
    """packages/lingwen-shared/ directory must exist."""
    assert (REPO_ROOT / "packages" / "lingwen-shared").is_dir(), "packages/lingwen-shared/ directory missing"


def test_lingwen_shared_pyproject_exists() -> None:
    """packages/lingwen-shared/pyproject.toml must exist."""
    path = REPO_ROOT / "packages" / "lingwen-shared" / "pyproject.toml"
    assert path.is_file(), f"{path} missing"


def test_lingwen_shared_pyproject_declares_project_section() -> None:
    """packages/lingwen-shared/pyproject.toml must declare a [project] section."""
    text = _read_toml(REPO_ROOT / "packages" / "lingwen-shared" / "pyproject.toml")
    section = _extract_section(text, "project")
    assert section is not None, "lingwen-shared/pyproject.toml missing [project]"
    assert 'name = "lingwen-shared"' in section, (
        f"lingwen-shared/pyproject.toml must have name = 'lingwen-shared' — got:\n{section}"
    )


def test_lingwen_shared_module_importable() -> None:
    """import lingwen_shared must work (underscore module name from hyphen package)."""
    import lingwen_shared  # noqa: F401
