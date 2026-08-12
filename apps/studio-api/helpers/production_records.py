"""
Phase 15.0 T1.4: production records root helper.

Hoisted out of dashboard/app.py closure so route files can call it without
capturing closure state.

Lifted verbatim from dashboard/app.py lines 218-230.
"""
from __future__ import annotations

import os
from pathlib import Path


def production_records_root() -> Path:
    """Resolve the root directory for production records.

    Order:
    1. LINGWEN_PILOT_RECORDS_DIR env override
    2. Active project's pilot_records dir (studio registry)
    3. Legacy infra/.state/default_pilot_records_dir
    """
    from infra.agent_system.production_records import default_pilot_records_dir
    from infra.studio_registry import active_project, pilot_records_dir_for

    env = os.environ.get("LINGWEN_PILOT_RECORDS_DIR", "").strip()
    if env:
        return Path(env)

    project = active_project()
    if project is not None:
        return pilot_records_dir_for(project)
    return default_pilot_records_dir()
