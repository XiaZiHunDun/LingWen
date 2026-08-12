"""Phase 17.2 守卫：dashboard/frontend 路径应已迁移到 apps/dashboard。"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def test_dashboard_frontend_path_removed():
    assert not (REPO / "dashboard" / "frontend").exists(), (
        "dashboard/frontend should have been moved to apps/dashboard in 17.2"
    )


def test_apps_dashboard_exists():
    assert (REPO / "apps" / "dashboard").exists(), (
        "apps/dashboard should exist after 17.2"
    )
