"""Phase 126 v16.2.4 shim: re-export from lingwen_creator.content.dashboard.

Migrated to packages/lingwen-creator/src/lingwen_creator/content/dashboard.py.
Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.content.dashboard import *  # noqa: F401,F403
from lingwen_creator.content.dashboard import (
    _build_volume_summaries,  # noqa: F401  # test compat (test_creator_v42_features imports private symbol)
    _excerpt,  # noqa: F401  # volume/plan.py lazy import via infra shim (documented cycle in volume/__init__.py)
)
