#!/usr/bin/env python3
"""Phase 9.65 F56: FastAPI entry for Playwright live-backend e2e."""
from __future__ import annotations

import os
from pathlib import Path


def main() -> None:
    from infra.cross_volume.e2e_seed import ensure_e2e_fixtures

    ensure_e2e_fixtures()

    from dashboard.app import create_app
    from dashboard.protocols import MasterControllerAdapter
    from infra.agent_system.master_controller import MasterController

    state_dir = Path(__file__).resolve().parent.parent / "infra" / ".state"
    state_dir.mkdir(parents=True, exist_ok=True)

    controller = MasterControllerAdapter(MasterController(state_dir=str(state_dir)))
    app = create_app(master_controller=controller)

    import uvicorn

    host = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
    port = int(os.environ.get("DASHBOARD_PORT", "8765"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
