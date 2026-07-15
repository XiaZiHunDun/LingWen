"""Phase 13.0 T4 M4: CLI path resolution from $LINGWEN_PROJECT_ROOT.

Goal: 3 CLI commands (cascade / ripple-rollback / ripple-audit) resolve
db path via $LINGWEN_PROJECT_ROOT, CWD fallback with WARNING (1-version
deprecation), exit 2 when db 不存在。

RED: import `infra.cli.path_utils.resolve_project_db_path` — helper
不存 → ImportError → RED。
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from infra.cli import path_utils


class TestResolveProjectDbPath:
    def test_env_set_db_exists_returns_path(self, tmp_path, monkeypatch):
        """env 设了 + db 存在 → 返回 resolved db path."""
        project_root = tmp_path / "proj"
        state_dir = project_root / ".state"
        state_dir.mkdir(parents=True)
        (state_dir / "ripple.db").touch()
        monkeypatch.setenv("LINGWEN_PROJECT_ROOT", str(project_root))
        result = path_utils.resolve_project_db_path()
        assert result == (state_dir / "ripple.db").resolve()
        assert result.exists()

    def test_env_set_db_missing_exits_2(self, tmp_path, monkeypatch):
        """env 设了 + db 缺失 → SystemExit(2)."""
        project_root = tmp_path / "empty_proj"
        project_root.mkdir()
        # no .state/ripple.db created
        monkeypatch.setenv("LINGWEN_PROJECT_ROOT", str(project_root))
        with pytest.raises(SystemExit) as exc_info:
            path_utils.resolve_project_db_path()
        assert exc_info.value.code == 2

    def test_env_unset_cwd_fallback_with_warning(
        self, tmp_path, monkeypatch, capsys
    ):
        """env 未设 + CWD 有 .state/ripple.db → fallback + WARNING."""
        monkeypatch.delenv("LINGWEN_PROJECT_ROOT", raising=False)
        state_dir = tmp_path / ".state"
        state_dir.mkdir(parents=True)
        (state_dir / "ripple.db").touch()
        monkeypatch.chdir(tmp_path)
        result = path_utils.resolve_project_db_path()
        assert result == (state_dir / "ripple.db").resolve()
        # WARNING in stderr (1-version deprecation notice)
        captured = capsys.readouterr()
        assert "WARNING" in captured.err
        assert "LINGWEN_PROJECT_ROOT" in captured.err

    def test_env_unset_no_fallback_exits_2(
        self, tmp_path, monkeypatch, capsys
    ):
        """env 未设 + CWD 无 .state/ripple.db → exit 2."""
        monkeypatch.delenv("LINGWEN_PROJECT_ROOT", raising=False)
        # tmp_path 存在 but no .state/ripple.db inside
        monkeypatch.chdir(tmp_path)
        with pytest.raises(SystemExit) as exc_info:
            path_utils.resolve_project_db_path()
        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "ERROR" in captured.err
