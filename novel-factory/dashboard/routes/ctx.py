"""
Phase 15.0 T1.4: shared dependency container for route modules.

Routes previously captured closure state (db, master_controller, manager,
limiter) inside `create_app`. Extracting routes out of the closure forces us
to pass that state explicitly via this context.

Closure state → context field map:
- db (ReadingPowerDB instance)         → ctx.db
- master_controller (Optional[Protocol]) → ctx.master_controller
- manager (ConnectionManager)          → ctx.manager
- limiter (slowapi Limiter)            → ctx.limiter
- _production_records_root()           → ctx.production_records_root (callable)
- _default_storage()                   → ctx.cvg_storage (callable, returns RippleStorage)
- _validate_max_depth(...)             → ctx.validate_max_depth (callable)
- _validate_max_nodes_cap(...)         → ctx.validate_max_nodes_cap (callable)
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from fastapi import HTTPException
from slowapi import Limiter

from dashboard.helpers.reading_power_db import ReadingPowerDB
from dashboard.protocols import MasterControllerLike
from dashboard.ws import ConnectionManager

if TYPE_CHECKING:
    from infra.cross_volume.storage import RippleStorage


@dataclass
class RoutesContext:
    """Shared dependencies for route modules."""

    db: ReadingPowerDB
    master_controller: Optional[MasterControllerLike]
    manager: ConnectionManager
    limiter: Limiter

    # late-bound callables (resolved at request time to honour monkeypatch)
    production_records_root: Callable[[], Path]
    cvg_storage: Callable[[], "RippleStorage"]


def require_controller(ctx: RoutesContext) -> MasterControllerLike:
    """Hoisted out of create_app closure: require master_controller, else 503."""
    if ctx.master_controller is None:
        raise HTTPException(
            status_code=503,
            detail="master_controller not configured for this dashboard instance",
        )
    return ctx.master_controller
