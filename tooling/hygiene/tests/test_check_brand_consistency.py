import importlib
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def _git_init(repo: Path) -> None:
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@test"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)


def _git_commit(repo: Path) -> None:
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "init", "-q"], check=True)


def _run_against(repo_root: Path):
    """Re-import the module under a fresh REPO_ROOT (via reload).

    Patches REPO_ROOT and find_violations.__defaults__ so the function reads
    from the tmp_path repo (same trick as test_check_file_size.py).
    """
    from tooling.hygiene import check_brand_consistency as mod

    importlib.reload(mod)
    mod.REPO_ROOT = repo_root
    mod.find_violations.__defaults__ = (repo_root,)
    return mod


def test_clean_file_passes(tmp_path: Path):
    """A frontend src/ file with only the new product/framework strings is clean."""
    _git_init(tmp_path)
    src_dir = tmp_path / "apps" / "dashboard" / "src"
    src_dir.mkdir(parents=True)
    (src_dir / "Page.vue").write_text(
        "<template><h1>墨灵</h1><p>欢迎使用 MoLing</p></template>\n<script>const name = '灵文';</script>\n"
    )
    # brand.js source-of-truth (must not be flagged itself)
    config_dir = src_dir / "config"
    config_dir.mkdir()
    (config_dir / "brand.js").write_text(
        "export const BRAND = { productShortZh: '墨灵', frameworkShortZh: '灵文' };\n"
    )
    _git_commit(tmp_path)

    mod = _run_against(tmp_path)
    assert mod.find_violations() == []


def test_lingwen_studio_in_src_is_flagged(tmp_path: Path):
    """LingWen Studio literal inside apps/dashboard/src/ must be flagged."""
    _git_init(tmp_path)
    src_dir = tmp_path / "apps" / "dashboard" / "src"
    src_dir.mkdir(parents=True)
    (src_dir / "bad.vue").write_text("<h1>LingWen Studio</h1>\n")
    _git_commit(tmp_path)

    mod = _run_against(tmp_path)
    violations = mod.find_violations()
    assert any(
        v[0] == "apps/dashboard/src/bad.vue" and v[1] == "forbidden_LingWen Studio" for v in violations
    ), violations


def test_brand_js_is_ignored(tmp_path: Path):
    """The brand source-of-truth file is exempt from the LingWen / 墨灵 / 灵文 checks."""
    _git_init(tmp_path)
    config_dir = tmp_path / "apps" / "dashboard" / "src" / "config"
    config_dir.mkdir(parents=True)
    # The real brand.js contains LingWen / 墨灵 / 灵文 — those should not be flagged.
    (config_dir / "brand.js").write_text(
        "/** 品牌字符串真源 */\n"
        "export const BRAND = Object.freeze({\n"
        "  productShortZh: '墨灵',\n"
        "  productNameZh: '墨灵 Studio',\n"
        "  frameworkShortZh: '灵文',\n"
        "  frameworkNameEn: 'LingWen Engine',\n"
        "});\n"
    )
    _git_commit(tmp_path)

    mod = _run_against(tmp_path)
    violations = mod.find_violations()
    assert violations == [], f"brand.js must be exempt; got {violations}"


def test_historical_doc_is_ignored(tmp_path: Path):
    """docs/superpowers/plans/** mentioning LingWen Studio is allowed (historical)."""
    _git_init(tmp_path)
    plans_dir = tmp_path / "docs" / "superpowers" / "plans"
    plans_dir.mkdir(parents=True)
    (plans_dir / "2026-05-12-legacy.md").write_text(
        "# Phase X plan\nThis plan references LingWen Studio and MoLing Studio.\n"
    )
    _git_commit(tmp_path)

    mod = _run_against(tmp_path)
    violations = mod.find_violations()
    assert violations == [], f"Historical plan files must be exempt; got {violations}"


def test_packages_readme_with_lingwen_studio_is_flagged(tmp_path: Path):
    """packages/*/README.md mentioning LingWen Studio must be flagged."""
    _git_init(tmp_path)
    pkg_dir = tmp_path / "packages" / "foo"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "README.md").write_text("# foo\nThis package belongs to LingWen Studio.\n")
    _git_commit(tmp_path)

    mod = _run_against(tmp_path)
    violations = mod.find_violations()
    assert any(v[0] == "packages/foo/README.md" and v[1] == "forbidden_LingWen Studio" for v in violations), (
        violations
    )


def test_standalone_lingwen_in_src_is_flagged(tmp_path: Path, capsys):
    """A standalone 'LingWen' token in frontend src/ must be flagged (rule: lingwen_standalone)."""
    _git_init(tmp_path)
    src_dir = tmp_path / "apps" / "dashboard" / "src"
    src_dir.mkdir(parents=True)
    (src_dir / "api.js").write_text("// LingWen Dashboard API client\nexport const foo = 1;\n")
    _git_commit(tmp_path)

    mod = _run_against(tmp_path)
    violations = mod.find_violations()
    assert any(v[0] == "apps/dashboard/src/api.js" and v[1] == "lingwen_standalone" for v in violations), (
        violations
    )


def test_main_returns_0_on_clean_repo(tmp_path: Path, capsys):
    """main() returns 0 when no violations exist."""
    _git_init(tmp_path)
    src_dir = tmp_path / "apps" / "dashboard" / "src"
    src_dir.mkdir(parents=True)
    (src_dir / "Page.vue").write_text("<h1>墨灵</h1>\n")
    _git_commit(tmp_path)

    mod = _run_against(tmp_path)
    rc = mod.main()
    captured = capsys.readouterr()
    assert rc == 0
    assert "OK" in captured.out


def test_main_returns_1_on_violations(tmp_path: Path, capsys):
    """main() returns 1 and prints the violation when LingWen Studio is found."""
    _git_init(tmp_path)
    src_dir = tmp_path / "apps" / "dashboard" / "src"
    src_dir.mkdir(parents=True)
    (src_dir / "bad.vue").write_text("<h1>LingWen Studio</h1>\n")
    _git_commit(tmp_path)

    mod = _run_against(tmp_path)
    rc = mod.main()
    captured = capsys.readouterr()
    assert rc == 1
    assert "LingWen Studio" in captured.out


def test_binary_file_is_skipped(tmp_path: Path):
    """A non-UTF-8 binary file in apps/dashboard/src/ must be skipped (no crash, no flag)."""
    _git_init(tmp_path)
    src_dir = tmp_path / "apps" / "dashboard" / "src"
    src_dir.mkdir(parents=True)
    # Write raw non-UTF-8 bytes (e.g. simulated font/image header).
    (src_dir / "asset.bin").write_bytes(b"\xff\xfe\x00\x01\x80\x90binary")
    _git_commit(tmp_path)

    mod = _run_against(tmp_path)
    # Must not crash. Binary file is skipped, so no violations from it.
    violations = mod.find_violations()
    assert violations == [], f"binary file must be skipped silently; got {violations}"


def test_lingwen_standalone_in_packages_readme_is_flagged(tmp_path: Path):
    """A standalone 'LingWen' token in a package README (non-JSDoc) must be flagged."""
    _git_init(tmp_path)
    pkg_dir = tmp_path / "packages" / "foo"
    pkg_dir.mkdir(parents=True)
    # Non-JSDoc context (plain prose): the standalone 'LingWen' rule only fires
    # in apps/dashboard/src/, but a forbidden product-string like 'LingWen Studio'
    # must still be flagged here.
    (pkg_dir / "README.md").write_text("# foo\nLingWen Studio is the product name.\n")
    _git_commit(tmp_path)

    mod = _run_against(tmp_path)
    violations = mod.find_violations()
    assert any(v[0] == "packages/foo/README.md" and v[1] == "forbidden_LingWen Studio" for v in violations), (
        violations
    )
