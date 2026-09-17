"""Shared project helpers (Phase 96).

Extracted from apps/studio_api/routes/illustrations.py for reuse across
project_settings.py and other future per-project routes.
"""
from __future__ import annotations

from pathlib import Path

from lingwen_illustrations.exceptions import LoadError


def project_root_for(slug: str) -> Path:
    """Resolve project root from slug.

    v1: scan `projects/` for the slug. Uses cwd-relative resolution so
    tests can `monkeypatch.chdir(tmp_path)` to isolate per-test.

    Phase 96: extracted from illustrations.py for reuse by project_settings.py.
    """
    candidate = Path("projects") / slug
    if not candidate.exists():
        raise LoadError(f"project '{slug}' not found at {candidate}")
    # Note: lingwen-paths.ProjectPaths / resolve_project_root reserved
    # for future canonical integration (see BACKLOG P2-ILLUSTRATIONS-BIBLE-CANONICAL).
    return candidate


__all__ = ["project_root_for"]
