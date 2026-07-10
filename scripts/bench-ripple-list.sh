#!/usr/bin/env bash
# Phase 13.0 T3 H4: ripple list perf smoke (200 rows ≤ 200ms).
#
# 跑 mini e2e: spin up TestClient, seed 200 ripples, hit /api/cvg/ripples,
# assert elapsed < 200ms。0 LLM, 0 网络, < 1s 全跑完。
#
# 用法: bash scripts/bench-ripple-list.sh
set -euo pipefail

cd "$(dirname "$0")/.." || exit 1

python3 -c "
import time
import tempfile
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage
from dashboard.app import create_app
from dashboard import app as app_module

with tempfile.TemporaryDirectory() as d:
    storage = RippleStorage(db_path=Path(d) / 'bench.db')
    storage._graph = None
    for i in range(200):
        r = CrossVolumeRipple(
            id=f'rip-bench-{i:03d}',
            trigger_volume=(i % 3) + 1,
            trigger_chapter=i,
            status='pending',
        )
        storage.append_ripple(r)
    with patch.object(app_module, '_default_storage', return_value=storage):
        app = create_app()
        client = TestClient(app)
        t0 = time.perf_counter()
        resp = client.get('/api/cvg/ripples?limit=200')
        elapsed_ms = (time.perf_counter() - t0) * 1000
    assert resp.status_code == 200, f'status={resp.status_code}'
    assert len(resp.json()) == 200, f'count={len(resp.json())}'
    assert elapsed_ms < 200, f'elapsed={elapsed_ms:.1f}ms > 200ms budget'
    print(f'PASS: 200 ripples, {elapsed_ms:.1f}ms < 200ms budget')
"
