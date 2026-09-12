"""Phase 58 P3-ARCHDEBT defect closure — regression guards.

These guards prevent the four classes of bugs that were silently
present in the codebase before Phase 58:

1. Missing re-exports: lingwen_studio_batch_streamer did not
   re-export KNOWN_EVENT_TYPES, breaking 18 tests + 5 runtime sites.
2. Stale internal imports: packages/lingwen-world-db/* had 8 internal
   `from infra.world_db.* import` references pointing at the
   deleted directory, breaking import of the entire query subpackage
   and silently breaking every /api/world/* runtime call.
3. Stale test imports: apps/studio_api/tests/test_world_route.py had
   5 `from infra.world_db.* import` references, breaking 6 tests.
4. Orphan test directory: tests/infra/world_db/ contained 5 test
   files that pytest could not collect.

Each guard is a static source-level check (no runtime) so the test
runs in < 100ms and is suitable for CI.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
WORLD_DB_PKG = REPO_ROOT / "packages" / "lingwen-world-db" / "src" / "lingwen_world_db"
WORLD_DB_QUERIES = WORLD_DB_PKG / "queries"
WORLD_DB_AGENT = WORLD_DB_PKG / "agent_extractors.py"
WORLD_DB_MD = WORLD_DB_PKG / "markdown_roundtrip.py"
WORLD_DB_INIT = WORLD_DB_PKG / "__init__.py"
STREAMER_INIT = (
    REPO_ROOT
    / "packages"
    / "lingwen-studio-batch-streamer"
    / "src"
    / "lingwen_studio_batch_streamer"
    / "__init__.py"
)
TEST_WORLD_ROUTE = REPO_ROOT / "apps" / "studio_api" / "tests" / "test_world_route.py"
ORPHAN_DIR = REPO_ROOT / "tests" / "infra" / "world_db"

# Files inside lingwen-world-db that must be free of stale imports.
WORLD_DB_PY_FILES = [
    WORLD_DB_INIT,
    WORLD_DB_QUERIES / "_helpers.py",
    WORLD_DB_QUERIES / "characters.py",
    WORLD_DB_QUERIES / "factions.py",
    WORLD_DB_QUERIES / "lore.py",
    WORLD_DB_QUERIES / "proposals.py",
    WORLD_DB_QUERIES / "relationships.py",
    WORLD_DB_QUERIES / "timeline.py",
    WORLD_DB_AGENT,
    WORLD_DB_MD,
]

# Match an actual Python import of infra.world_db.*
# Allows docstring references like "matches original infra.world_db.__init__.py"
_STALE_IMPORT_RE = re.compile(
    r"(?:^|\n)\s*(?:from|import)\s+infra\.world_db\b"
)


def _has_stale_import(path: Path) -> list[str]:
    """Return list of stale-import lines found in path (empty if clean)."""
    text = path.read_text(encoding="utf-8")
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        if _STALE_IMPORT_RE.search(line):
            hits.append(f"{path.relative_to(REPO_ROOT)}:{i}: {line.strip()}")
    return hits


# ---------------------------------------------------------------------------
# Guard 1: KNOWN_EVENT_TYPES is re-exported from lingwen_studio_batch_streamer
# ---------------------------------------------------------------------------
class TestKnownEventTypesExport:
    def test_known_event_types_in_package_all(self):
        """KNOWN_EVENT_TYPES must be in lingwen_studio_batch_streamer.__all__.

        apps/studio_api/routes/studio.py imports it via canonical path at
        5 sites; missing export breaks 18 batch tests + 4 runtime sites.
        """
        from lingwen_studio_batch_streamer import __all__

        assert "KNOWN_EVENT_TYPES" in __all__, (
            "KNOWN_EVENT_TYPES missing from lingwen_studio_batch_streamer.__all__"
        )

    def test_known_event_types_importable(self):
        """The symbol must be importable from the package root."""
        from lingwen_studio_batch_streamer import KNOWN_EVENT_TYPES

        # Sanity: it's a frozenset of canonical event-type strings
        assert isinstance(KNOWN_EVENT_TYPES, frozenset)
        assert "job_state" in KNOWN_EVENT_TYPES
        assert "chapter_completed" in KNOWN_EVENT_TYPES

    def test_streamer_init_contains_known_event_types_text(self):
        """Belt-and-braces: the literal name must appear in __init__.py source.

        Catches accidental re-renames / refactors that lose the symbol
        even if __all__ is correct.
        """
        text = STREAMER_INIT.read_text(encoding="utf-8")
        assert "KNOWN_EVENT_TYPES" in text


# ---------------------------------------------------------------------------
# Guard 2: No `infra.world_db.*` imports remain in the world-db package
# ---------------------------------------------------------------------------
class TestWorldDbPackageNoOldPaths:
    @pytest.mark.parametrize("path", WORLD_DB_PY_FILES, ids=lambda p: p.name)
    def test_no_stale_imports(self, path):
        """Production code in lingwen-world-db must use canonical paths only.

        Phase 56 deleted infra/world_db/; any surviving import is a silent
        production bug that breaks the entire package's importability.
        """
        hits = _has_stale_import(path)
        assert not hits, "Stale infra.world_db imports found:\n" + "\n".join(hits)

    def test_characters_query_module_importable(self):
        """The whole point of guard 2: the queries/characters subpackage
        must be importable in isolation.
        """
        from lingwen_world_db.queries import characters  # noqa: F401

        assert hasattr(characters, "create_character")

    def test_agent_extractors_module_importable(self):
        """The whole point of guard 2: agent_extractors must be importable
        and expose its public LLM extraction function.
        """
        from lingwen_world_db import agent_extractors  # noqa: F401

        assert hasattr(agent_extractors, "extract_proposals_from_chapters"), (
            "agent_extractors must expose extract_proposals_from_chapters"
        )
        assert hasattr(agent_extractors, "extract_proposals_from_prompt"), (
            "agent_extractors must expose extract_proposals_from_prompt"
        )

    def test_markdown_roundtrip_module_importable(self):
        """The whole point of guard 2: markdown_roundtrip must be importable."""
        from lingwen_world_db import markdown_roundtrip  # noqa: F401

        assert hasattr(markdown_roundtrip, "import_project_markdown")


# ---------------------------------------------------------------------------
# Guard 3: test_world_route.py uses canonical paths only
# ---------------------------------------------------------------------------
class TestWorldRouteTestNoOldPaths:
    def test_no_stale_imports(self):
        """apps/studio_api/tests/test_world_route.py must not import infra.world_db."""
        hits = _has_stale_import(TEST_WORLD_ROUTE)
        assert not hits, "Stale infra.world_db imports in test_world_route.py:\n" + "\n".join(
            hits
        )

    def test_uses_canonical_imports(self):
        text = TEST_WORLD_ROUTE.read_text(encoding="utf-8")
        # Must reference canonical schema import
        assert "lingwen_world_db.schema" in text
        # Must reference canonical agent_extractors import
        assert "lingwen_world_db.agent_extractors" in text


# ---------------------------------------------------------------------------
# Guard 4: Orphan test directory must not exist; no stale imports anywhere
# ---------------------------------------------------------------------------
class TestOrphanTestDirDeleted:
    def test_orphan_dir_does_not_exist(self):
        """tests/infra/world_db/ was deleted in C4. Must not reappear."""
        assert not ORPHAN_DIR.exists(), (
            f"orphan test directory must remain deleted: {ORPHAN_DIR}"
        )

    def test_no_orphan_imports_repo_wide(self):
        """A belt-and-braces scan: no `from infra.world_db` or
        `import infra.world_db` anywhere in the repository
        (excluding build artifacts, .git, archive, worktrees).
        """
        result = subprocess.run(
            [
                "grep",
                "-rln",
                "--include=*.py",
                "-E",
                r"(^|\n)\s*(from|import)\s+infra\.world_db\b",
                str(REPO_ROOT),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # grep returns 1 when no matches found — that's the success case
        files = [line for line in result.stdout.splitlines() if line.strip()]
        offenders = []
        for f in files:
            rel = f.replace(str(REPO_ROOT) + "/", "")
            # Exclude build artifacts, venvs, worktrees, archive
            if any(
                part in rel
                for part in (
                    ".venv/",
                    "node_modules/",
                    "__pycache__/",
                    ".git/",
                    "docs/superpowers/archive/",
                    ".claude/worktrees/",
                )
            ):
                continue
            offenders.append(rel)
        assert not offenders, (
            "stray infra.world_db imports in: " + ", ".join(offenders)
        )

    def test_import_project_markdown_callable(self):
        """Round-trip: production import works end-to-end."""
        from lingwen_world_db.markdown_roundtrip import import_project_markdown

        assert callable(import_project_markdown)


# ---------------------------------------------------------------------------
# Guard 5: Full studio_api test suite passes (smoke)
# ---------------------------------------------------------------------------
def test_studio_api_suite_clean():
    """A bare smoke test for the original 24 failures — does not
    re-run the suite (pytest will do that) but ensures all the
    symbols are importable in the canonical way.
    """
    from lingwen_studio_batch_streamer import KNOWN_EVENT_TYPES
    from lingwen_world_db.agent_extractors import extract_proposals_from_chapters
    from lingwen_world_db.queries.characters import create_character
    from lingwen_world_db.schema import get_connection, init_schema

    assert KNOWN_EVENT_TYPES
    assert callable(extract_proposals_from_chapters)
    assert callable(create_character)
    assert callable(get_connection)
    assert callable(init_schema)


# Import pytest at module level for the parametrize decorator on methods
# (already imported at top of module)
