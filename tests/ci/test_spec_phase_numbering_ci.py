"""F28: spec phase numbering annotation contract tests (doc-only closure)."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SPEC_845 = (
    REPO_ROOT
    / "docs"
    / "superpowers"
    / "specs"
    / "2026-06-09-phase8.45-ui-completeness-design.md"
)
PHASE_NUMBERING_NOTE = "Phase 编号以 c32015d 为准"


class TestSpecPhaseNumberingAnnotation:
    def test_phase845_spec_has_c32015d_numbering_note(self):
        text = SPEC_845.read_text(encoding="utf-8")
        assert PHASE_NUMBERING_NOTE in text

    def test_note_is_in_header_block_before_section_one(self):
        text = SPEC_845.read_text(encoding="utf-8")
        header, _rest = text.split("\n---\n", 1)
        assert PHASE_NUMBERING_NOTE in header
