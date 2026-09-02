"""Phase 126 v16.2.0: tests for shared/revision.py migrated utilities."""

from __future__ import annotations

import pytest
from lingwen_creator.shared.revision import CreatorDocConflictError, content_revision


def test_creator_doc_conflict_error_is_exception() -> None:
    with pytest.raises(CreatorDocConflictError):
        raise CreatorDocConflictError("test conflict")


def test_content_revision_deterministic() -> None:
    rev1 = content_revision("hello world")
    rev2 = content_revision("hello world")
    assert rev1 == rev2


def test_content_revision_differs_on_content_change() -> None:
    rev1 = content_revision("hello world")
    rev2 = content_revision("hello WORLD")
    assert rev1 != rev2


def test_legacy_shim_deleted() -> None:
    """v16.2.7 T4.12: infra.creator_revision shim deleted, must raise ModuleNotFoundError."""
    import pytest

    with pytest.raises(ModuleNotFoundError):
        from infra.creator_revision import CreatorDocConflictError  # noqa: F401
