"""Shared git helpers for hygiene checkers."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def git_ls_files(repo_root: Path, *, tool: str = "check") -> list[str]:
    """Run `git ls-files -z` with error handling. Returns list of relative paths."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=repo_root,
            check=True,
        )
    except FileNotFoundError:
        sys.exit(f"{tool}: git executable not found on PATH")
    except subprocess.CalledProcessError as e:
        sys.exit(f"{tool}: git ls-files failed: {(e.stderr or '').strip()}")
    # -z returns paths separated by \x00; trailing empty string is the terminator
    return [p for p in out.stdout.split("\x00") if p]
