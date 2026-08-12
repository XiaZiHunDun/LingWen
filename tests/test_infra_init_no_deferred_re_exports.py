"""Phase 17.0 guard test: ensure `infra/__init__.py` does not re-export
deletion targets that 16.7 deferred to Phase 17.

This test enforces that the umbrella `infra` package has been decoupled from
the modules that Phase 16.7 deferred (creator, studio, prose, project, core,
di, event_sourcing, exports). Phase 17 will rebuild the package layout from
scratch; until then, the umbrella must NOT silently re-export them.

If this test fails:
- The deferred re-exports are still present in `infra/__init__.py`.
- Run Task 17.0 Step 4-5 (edit infra/__init__.py) to remove them.

Patterns asserted (all MUST be absent from infra/__init__.py):
    - ``from infra.creator import``
    - ``from infra.studio import``
    - ``from infra.prose import``
    - ``from infra.project import``
    - ``from infra.core import``
    - ``from infra.di.layer import``
    - ``from infra.event_sourcing.(models|store) import``

Each pattern is checked separately so the assertion message names the
specific pattern that slipped back in.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


INFRA_INIT = Path(__file__).resolve().parents[1] / "infra" / "__init__.py"


# (human-readable pattern name, regex anchored at line start)
FORBIDDEN_PATTERNS: tuple[tuple[str, str], ...] = (
    ("infra.creator re-export",     r"^\s*from\s+infra\.creator\s+import"),
    ("infra.studio re-export",      r"^\s*from\s+infra\.studio\s+import"),
    ("infra.prose re-export",       r"^\s*from\s+infra\.prose\s+import"),
    ("infra.project re-export",     r"^\s*from\s+infra\.project\s+import"),
    ("infra.core re-export",        r"^\s*from\s+infra\.core\s+import"),
    ("infra.di.layer re-export",    r"^\s*from\s+infra\.di\.layer\s+import"),
    (
        "infra.event_sourcing.{models,store} re-export",
        r"^\s*from\s+infra\.event_sourcing\.(models|store)\s+import",
    ),
)


def _read_infra_init() -> str:
    assert INFRA_INIT.exists(), f"infra/__init__.py missing at {INFRA_INIT}"
    return INFRA_INIT.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("label", "pattern"),
    [(label, pattern) for (label, pattern) in FORBIDDEN_PATTERNS],
    ids=[label for (label, _) in FORBIDDEN_PATTERNS],
)
def test_infra_init_does_not_re_export_deferred_targets(label: str, pattern: str) -> None:
    """Each deferred re-export pattern must be absent from infra/__init__.py."""
    source = _read_infra_init()
    matches = re.findall(pattern, source, flags=re.MULTILINE)
    assert not matches, (
        f"infra/__init__.py still contains the deferred re-export '{label}' "
        f"(pattern: {pattern!r}). Found {len(matches)} match(es): {matches!r}. "
        "Phase 17.0 Step 4-5 must delete this re-export."
    )


def test_infra_init_does_not_import_exports_submodule() -> None:
    """``import infra.exports as exports`` was also deferred — must be gone."""
    source = _read_infra_init()
    assert not re.search(
        r"^\s*import\s+infra\.exports\s+as\s+exports",
        source,
        flags=re.MULTILINE,
    ), (
        "infra/__init__.py still has 'import infra.exports as exports'. "
        "Phase 17.0 Step 4-5 must delete this line."
    )

