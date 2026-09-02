"""Phase 126 v16.2.0: verify lingwen-creator package layout (5 tests).

仿 v16.1 T1 (`tests/test_lingwen_shared_layout.py`) — uv sync 不验证 member 目录,
需要显式 gate 测试 package layout 与 import path 正确性。
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]  # .../LingWen (test file is at root tests/)
PACKAGE_PYPROJECT = REPO_ROOT / "packages" / "lingwen-creator" / "pyproject.toml"
PACKAGE_SRC = REPO_ROOT / "packages" / "lingwen-creator" / "src" / "lingwen_creator"


def test_package_pyproject_exists() -> None:
    assert PACKAGE_PYPROJECT.exists(), f"missing {PACKAGE_PYPROJECT}"


def test_package_pyproject_has_hyphen_name() -> None:
    """Packaging name 必须是 hyphen ('lingwen-creator'),不是 underscore."""
    content = PACKAGE_PYPROJECT.read_text(encoding="utf-8")
    assert 'name = "lingwen-creator"' in content, "packaging name must be 'lingwen-creator' (hyphen)"


def test_module_imports_with_underscore_name() -> None:
    """Python module name 必须是 underscore ('lingwen_creator'),不是 hyphen."""
    import lingwen_creator  # noqa: F401

    assert lingwen_creator.__name__ == "lingwen_creator"


def test_shared_subpackage_exists() -> None:
    assert (PACKAGE_SRC / "shared" / "__init__.py").exists()


def test_uv_workspace_member_declared() -> None:
    root_pyproject = REPO_ROOT / "pyproject.toml"
    content = root_pyproject.read_text(encoding="utf-8")
    assert '"packages/lingwen-creator"' in content or "'packages/lingwen-creator'" in content, (
        "lingwen-creator not declared as uv workspace member in root pyproject.toml"
    )
