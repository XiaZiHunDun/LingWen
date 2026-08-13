"""Phase 17.1 守卫：pnpm-workspace.yaml 覆盖 apps/*。"""
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parents[3]
WS = REPO / "pnpm-workspace.yaml"


def test_pnpm_workspace_includes_apps():
    data = yaml.safe_load(WS.read_text(encoding="utf-8"))
    packages = data.get("packages", [])
    assert "apps/*" in packages, (
        f"pnpm-workspace.yaml must include 'apps/*'; got {packages}"
    )


def test_pnpm_workspace_excludes_lingwen_storage():
    """Python 包不应被 pnpm workspace 跟踪。"""
    data = yaml.safe_load(WS.read_text(encoding="utf-8"))
    packages = data.get("packages", [])
    # 不应包含 'packages/lingwen-storage'（用路径展开；pnpm 不识别）
    assert "packages/lingwen-storage" not in packages
    assert "packages/lingwen-core" not in packages  # 未来 17.5 也不会是 pnpm 包
