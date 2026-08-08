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

    Default args are captured at function definition; updating only the module
    attribute is not enough. Patch __defaults__ so find_oversized() sees the
    tmp_path (git_ls_files receives repo_root as a positional arg, no patching
    needed there).
    """
    from tooling.hygiene import check_file_size as mod

    importlib.reload(mod)
    mod.REPO_ROOT = repo_root
    mod.find_oversized.__defaults__ = (repo_root,)
    return mod


def test_no_oversized_files_clean_repo(tmp_path: Path):
    """A repo with only small files should produce no violations."""
    _git_init(tmp_path)
    (tmp_path / "small.py").write_text("x = 1\n")
    (tmp_path / "small.vue").write_text("<template></template>\n")
    _git_commit(tmp_path)

    mod = _run_against(tmp_path)
    assert mod.find_oversized() == []


def test_oversized_py_file_detected(tmp_path: Path):
    """A .py file > 500 lines should be flagged."""
    _git_init(tmp_path)
    (tmp_path / "big.py").write_text("\n".join(["x = 1"] * 600) + "\n")
    _git_commit(tmp_path)

    mod = _run_against(tmp_path)
    violations = mod.find_oversized()
    assert any(v[0] == "big.py" and v[1] == 600 for v in violations), violations


def test_allowlist_skips_file(tmp_path: Path):
    """Files in ALLOWLIST should not be flagged."""
    _git_init(tmp_path)
    (tmp_path / "huge.py").write_text("\n".join(["x = 1"] * 1000) + "\n")
    _git_commit(tmp_path)

    mod = _run_against(tmp_path)
    mod.ALLOWLIST.add("huge.py")
    violations = mod.find_oversized()
    assert all(v[0] != "huge.py" for v in violations), violations


def test_oversized_vue_at_351_detected(tmp_path: Path):
    """A .vue file at 351 lines should be flagged (limit is 350)."""
    _git_init(tmp_path)
    (tmp_path / "Big.vue").write_text("\n".join(["<div/>"] * 351) + "\n")
    _git_commit(tmp_path)

    mod = _run_against(tmp_path)
    violations = mod.find_oversized()
    assert any(v[0] == "Big.vue" and v[1] == 351 for v in violations), violations


def test_main_returns_1_on_violations(tmp_path: Path, capsys):
    """main() should return 1 when violations exist."""
    _git_init(tmp_path)
    (tmp_path / "huge.py").write_text("\n".join(["x = 1"] * 600) + "\n")
    _git_commit(tmp_path)

    mod = _run_against(tmp_path)
    rc = mod.main()
    captured = capsys.readouterr()
    assert rc == 1
    assert "huge.py" in captured.out


def test_main_returns_0_clean(tmp_path: Path, capsys):
    """main() should return 0 when no violations."""
    _git_init(tmp_path)
    (tmp_path / "ok.py").write_text("x = 1\n")
    _git_commit(tmp_path)

    mod = _run_against(tmp_path)
    rc = mod.main()
    captured = capsys.readouterr()
    assert rc == 0
    assert "OK" in captured.out