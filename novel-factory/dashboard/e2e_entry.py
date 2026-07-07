#!/usr/bin/env python3
"""Phase 9.65 F56: FastAPI entry for Playwright live-backend e2e."""
from __future__ import annotations

import os
from pathlib import Path


def main() -> None:
    from infra.cross_volume.e2e_seed import ensure_e2e_fixtures

    ensure_e2e_fixtures()

    from dashboard.app import create_app
    from dashboard.e2e_stub_controller import E2EStubController

    state_dir = Path(__file__).resolve().parent.parent / "infra" / ".state"
    state_dir.mkdir(parents=True, exist_ok=True)

    app = create_app(master_controller=E2EStubController(state_dir=str(state_dir)))

    from dashboard import app as app_module
    from infra.cross_volume.reference_graph import CrossVolumeReferenceGraph

    storage = app_module._default_storage()
    if storage._graph is None:
        storage._graph = CrossVolumeReferenceGraph(storage)

    import uvicorn

    host = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
    port = int(os.environ.get("DASHBOARD_PORT", "8765"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
