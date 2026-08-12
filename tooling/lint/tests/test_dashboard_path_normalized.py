"""Phase 17.2/17.3 守卫：dashboard/frontend 路径应已迁移到 apps/dashboard；
dashboard/ 剩余部分应已迁移到 apps/studio-api。
"""
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


def test_dashboard_root_removed():
    """Phase 17.3: dashboard/ root should be moved to apps/studio-api."""
    dashboard_path = REPO / "dashboard"
    # dashboard/ root must be gone (no longer a directory); symlinks are tolerated
    assert not (dashboard_path.exists() and dashboard_path.is_dir()), (
        "dashboard/ root should be moved to apps/studio-api "
        "(frontend already in apps/dashboard)"
    )


def test_apps_studio_api_exists():
    assert (REPO / "apps" / "studio-api").exists(), (
        "apps/studio-api should exist after 17.3"
    )
