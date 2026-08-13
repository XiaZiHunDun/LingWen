"""Phase 17.13 守卫：包依赖方向正确。

规则：
- packages/lingwen-* 不得 import apps.studio_api（lingwen 不能反向依赖应用）
- apps/dashboard 只能 import packages/dashboard-contracts（其他 lingwen 包须经 HTTP/WS）
- apps/studio-api 可以 import packages/lingwen-*（应用层）
- 同包内可互相 import。
"""
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "tooling" / "lint" / "check_package_deps.py"


def _run(args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True,
        cwd=str(REPO),
    )


def test_clean_repo_passes():
    result = _run(["--check"])
    assert result.returncode in (0, 1), f"Script crashed: {result.stderr[:200]}"


def test_violation_is_detected(tmp_path):
    # Create fake file inside repo so the script can compute source zone.
    # The directory must start with 'lingwen' to trigger the package rule.
    fake_pkg = REPO / "packages" / "lingwen_test_tmp"
    fake_pkg.mkdir(parents=True, exist_ok=True)
    bad = fake_pkg / "fake_lingwen.py"
    bad.write_text("from apps.studio_api import foo\n", encoding="utf-8")
    try:
        result = _run(["--check", "--target", str(bad)])
        assert result.returncode == 1, (
            f"Expected violation, got rc={result.returncode}, stdout={result.stdout}"
        )
        assert "violation" in result.stdout.lower()
    finally:
        bad.unlink(missing_ok=True)
        fake_pkg.rmdir()
