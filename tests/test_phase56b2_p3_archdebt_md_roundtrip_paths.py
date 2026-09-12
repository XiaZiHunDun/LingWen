"""Phase 56b2 P3-ARCHDEBT — test_markdown_roundtrip.py cwd-independent paths guard.

Phase 56b C2 restored `packages/lingwen-world-db/tests/test_markdown_roundtrip.py`
from Phase 58 commit `0f3239f4^`. The restored file used cwd-relative paths
like `Path("docs/character-bible")`, which only resolved correctly when pytest
was invoked from the repo root. Phase 56b2 closed this gap by replacing cwd-
relative paths with `Path(__file__).resolve().parents[3] / "docs"`.

This guard prevents regression:
  - G6 (1): test_markdown_roundtrip.py MUST NOT use cwd-relative Path("docs/...")
  - G7 (1): test_markdown_roundtrip.py MUST resolve DOCS_DIR via
             Path(__file__).resolve().parents[N] pattern (cwd-independent)
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

TARGET_FILE = (
    REPO_ROOT / "packages" / "lingwen-world-db" / "tests" / "test_markdown_roundtrip.py"
)


# ---------------------------------------------------------------------------
# G6: no cwd-relative Path("docs/...") literals in test_markdown_roundtrip.py
# ---------------------------------------------------------------------------


def test_no_cwd_relative_path_literals_in_md_roundtrip() -> None:
    """test_markdown_roundtrip.py must not use cwd-relative Path("docs/...").

    Phase 56b2 replaced these with `Path(__file__).resolve().parents[3] / "docs"`
    so the tests pass regardless of pytest invocation cwd (repo root, package
    dir, or tests/ dir).
    """
    assert TARGET_FILE.exists(), (
        f"{TARGET_FILE} must exist (Phase 56b C2 restoration)."
    )
    offenders: list[tuple[int, str]] = []
    for lineno, line in enumerate(
        TARGET_FILE.read_text(encoding="utf-8").splitlines(), start=1
    ):
        stripped = line.lstrip()
        # Only flag actual Path() construction calls, not docstrings/comments.
        # Allow "Path(__file__)" and "Path(repo_root)" but forbid
        # `Path("docs/...")` literals.
        if 'Path("docs/' in stripped or "Path('docs/" in stripped:
            offenders.append((lineno, line.strip()))

    assert not offenders, (
        "Found cwd-relative Path('docs/...') literals in "
        "test_markdown_roundtrip.py. Use Path(__file__).resolve().parents[3] "
        "/ 'docs' (or DOCS_DIR constant) instead:\n"
        + "\n".join(f"  line {ln}: {line}" for ln, line in offenders)
    )


# ---------------------------------------------------------------------------
# G7: test_markdown_roundtrip.py uses Path(__file__).resolve().parents[N] pattern
# ---------------------------------------------------------------------------


def test_md_roundtrip_uses_file_relative_path_pattern() -> None:
    """test_markdown_roundtrip.py must resolve paths via
    `Path(__file__).resolve().parents[N]` so tests are cwd-independent.

    The pattern is the standard idiom for cwd-independent test fixtures when
    no shared conftest.py / pyproject `[tool.pytest.ini_options]` testpaths
    is available.
    """
    assert TARGET_FILE.exists(), (
        f"{TARGET_FILE} must exist (Phase 56b C2 restoration)."
    )
    content = TARGET_FILE.read_text(encoding="utf-8")
    assert "Path(__file__).resolve().parents[" in content, (
        "test_markdown_roundtrip.py must use "
        "`Path(__file__).resolve().parents[N]` to anchor DOCS_DIR "
        "relative to the test file (cwd-independent). "
        "Phase 56b2 added this pattern; if it was reverted, restore it."
    )
    # Sanity: must construct DOCS_DIR (or equivalent) from REPO_ROOT.
    assert "DOCS_DIR" in content, (
        "test_markdown_roundtrip.py must define a module-level DOCS_DIR "
        "constant anchored at REPO_ROOT / 'docs' (Phase 56b2)."
    )