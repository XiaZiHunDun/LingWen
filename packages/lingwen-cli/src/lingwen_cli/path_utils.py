"""Phase 13.0 T4 M4: CLI path resolution helper.

3 CLI commands (cascade / ripple-rollback / ripple-audit) resolve their
ripple.db path from $LINGWEN_PROJECT_ROOT (preferred) or CWD fallback
(1-version deprecation).

When db 不存在 (env 设 or CWD fallback), exit 2 with [ERROR] message —
silent cwd-coupling is what broke the cron job (Phase 13.0 audit R4).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

DEFAULT_RIPPLE_DB = Path(".state") / "ripple.db"
ENV_VAR = "LINGWEN_PROJECT_ROOT"


def _emit_error_and_exit(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(2)


def resolve_project_db_path() -> Path:
    """Resolve ripple.db path from $LINGWEN_PROJECT_ROOT or CWD fallback.

    Resolution order:
    1. $LINGWEN_PROJECT_ROOT/.state/ripple.db (preferred, no warning)
    2. CWD/.state/ripple.db (deprecated, prints WARNING to stderr)
    3. db 缺失 → exit 2 (any of the above)
    """
    env_value = os.environ.get(ENV_VAR, "").strip()
    if env_value:
        project_root = Path(env_value).resolve()
        db_path = project_root / DEFAULT_RIPPLE_DB
        if not db_path.exists():
            _emit_error_and_exit(
                f"{db_path} 不存在 "
                f"(LINGWEN_PROJECT_ROOT={env_value}); "
                f"set env 到有效项目根或 init 一个"
            )
        return db_path
    # CWD fallback (1-version deprecation)
    cwd_db = Path.cwd() / DEFAULT_RIPPLE_DB
    print(
        f"[WARNING] LINGWEN_PROJECT_ROOT 未设, fall back to CWD: {cwd_db}。"
        f"下版本 (Phase 13.1) 将删除此 fallback — 显式 export LINGWEN_PROJECT_ROOT=<path>",
        file=sys.stderr,
    )
    if not cwd_db.exists():
        _emit_error_and_exit(
            f"{cwd_db} 不存在 (CWD fallback) — "
            f"export LINGWEN_PROJECT_ROOT=<valid project root>"
        )
    return cwd_db.resolve()
