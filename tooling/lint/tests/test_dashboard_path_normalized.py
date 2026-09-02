"""Phase 17.2/17.3 守卫:dashboard/frontend 路径应已迁移到 apps/dashboard;
dashboard/ 剩余部分应已迁移到 apps/studio_api。

注: 17.3 fix 把目录从 apps/studio-api 重命名为 apps/studio_api(下划线),
因 hyphen 不是合法 Python 标识符 — see commit message。
"""

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def test_dashboard_frontend_path_removed():
    assert not (REPO / "dashboard" / "frontend").exists(), (
        "dashboard/frontend should have been moved to apps/dashboard in 17.2"
    )


def test_apps_dashboard_exists():
    assert (REPO / "apps" / "dashboard").exists(), "apps/dashboard should exist after 17.2"


def test_dashboard_root_removed():
    """Phase 17.3: dashboard/ root should be moved to apps/studio_api."""
    dashboard_path = REPO / "dashboard"
    # dashboard/ root must be gone (no longer a directory); symlinks are tolerated
    assert not (dashboard_path.exists() and dashboard_path.is_dir()), (
        "dashboard/ root should be moved to apps/studio_api (frontend already in apps/dashboard)"
    )


def test_apps_studio_api_exists():
    """Phase 17.3: apps/studio_api/ (underscore for Python imports) should exist."""
    assert (REPO / "apps" / "studio_api").exists(), (
        "apps/studio_api should exist after 17.3 (renamed from apps/studio-api for Python import compatibility)"
    )


def test_no_legacy_studio_api_hyphen_path():
    """Phase 17.3 fix: ensure no apps/studio-api (hyphenated) lingers."""
    legacy = REPO / "apps" / "studio-api"
    assert not legacy.exists(), (
        f"Legacy apps/studio-api should have been renamed to apps/studio_api: {legacy}"
    )
