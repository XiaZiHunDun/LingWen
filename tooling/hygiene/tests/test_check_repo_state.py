import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tooling.hygiene.check_repo_state import find_hygiene_violations


@pytest.fixture
def stub_ls_files(monkeypatch):
    """Stub git_ls_files to return an arbitrary file list."""
    def _stub(files):
        monkeypatch.setattr(
            "tooling.hygiene.check_repo_state.git_ls_files",
            lambda *args, **kwargs: files,
        )
    return _stub


def test_forbidden_path_detected(stub_ls_files):
    """__pycache__ path component must be flagged."""
    stub_ls_files(["src/foo.py", "a/__pycache__/x.pyc"])
    violations = find_hygiene_violations()
    assert any("FORBIDDEN_PATH: a/__pycache__/x.pyc" in v for v in violations)


def test_state_subdir_detected(stub_ls_files):
    """.state path component must be flagged."""
    stub_ls_files(["infra/.state/workflow.db"])
    violations = find_hygiene_violations()
    assert any("FORBIDDEN_PATH: infra/.state/workflow.db" in v for v in violations)


def test_substring_not_matched(stub_ls_files):
    """Substring-only matches must NOT be flagged (path-component rule)."""
    stub_ls_files([
        "docs/state_machine/manager.py",
        "docs/pycache_intro.md",
        "tools/mypy_cache_helper.py",
        "src/lingwen_novel_factory.egg-info.md",
    ])
    violations = find_hygiene_violations()
    assert violations == []


def test_placeholder_detected(stub_ls_files, tmp_path):
    """TEMPLATE.md tracked file must be flagged."""
    (tmp_path / "TEMPLATE.md").write_text("")
    stub_ls_files(["TEMPLATE.md"])
    violations = find_hygiene_violations(tmp_path)
    assert any("PLACEHOLDER_FILE: TEMPLATE.md" in v for v in violations)


def test_clean_tracked_files(stub_ls_files):
    """No violations on a clean file list."""
    stub_ls_files(["src/foo.py", "tests/test_x.py", "docs/readme.md"])
    violations = find_hygiene_violations()
    assert violations == []
