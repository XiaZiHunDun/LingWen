"""Phase 126 v16.2.6: tests for memory/ subdomain (3 modules)."""

from __future__ import annotations

from pathlib import Path


def test_memory_package_imports() -> None:
    """lingwen_creator.memory package is importable."""
    import lingwen_creator.memory

    assert lingwen_creator.memory.__name__ == "lingwen_creator.memory"


def test_annotations_module_exports() -> None:
    """lingwen_creator.memory.annotations exports load/apply/upsert."""
    from lingwen_creator.memory.annotations import (
        apply_memory_annotations,
        load_memory_annotations,
        upsert_memory_annotation,
    )

    assert callable(load_memory_annotations)
    assert callable(apply_memory_annotations)
    assert callable(upsert_memory_annotation)


def test_assets_module_exports() -> None:
    """lingwen_creator.memory.assets exports creator_memory_assets_payload."""
    from lingwen_creator.memory.assets import creator_memory_assets_payload

    assert callable(creator_memory_assets_payload)


def test_query_module_exports() -> None:
    """lingwen_creator.memory.query exports creator_memory_query."""
    from lingwen_creator.memory.query import creator_memory_query

    assert callable(creator_memory_query)


def test_package_star_reexports() -> None:
    """__init__.py star-imports expose all 3 submodules' public names."""
    import lingwen_creator.memory as memory

    assert callable(memory.upsert_memory_annotation)
    assert callable(memory.creator_memory_assets_payload)
    assert callable(memory.creator_memory_query)


def test_legacy_shims_deleted() -> None:
    """v16.2.7 T4.1: shim files were deleted; back-compat `from infra.creator_memory_X` must now raise.

    Replaces test_legacy_import_paths_still_work from v16.2.6 cycle (shim existence test).
    """
    import pytest

    with pytest.raises(ModuleNotFoundError):
        from infra.creator_memory_annotations import apply_memory_annotations  # noqa: F401
    with pytest.raises(ModuleNotFoundError):
        from infra.creator_memory_assets import creator_memory_assets_payload  # noqa: F401
    with pytest.raises(ModuleNotFoundError):
        from infra.creator_memory_query import creator_memory_query  # noqa: F401


def test_intra_package_imports_use_new_path() -> None:
    """No `from infra.creator_*` left in memory/*.py (per v16.2.4 §5.1 lesson 1).

    infra.studio_registry / infra.memory_service are NOT creator subdomain modules
    and legitimately stay on the infra path.
    """
    pkg_dir = Path(__file__).resolve().parents[1] / "src" / "lingwen_creator" / "memory"
    offenders: list[str] = []
    for path in sorted(pkg_dir.glob("*.py")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "infra.creator_" in line:
                offenders.append(f"{path.name}:{lineno}: {line.strip()}")
    assert offenders == []


def test_annotations_round_trip(tmp_path: Path) -> None:
    """upsert -> load -> apply keeps note/pinned on the matching asset."""
    from lingwen_creator.memory.annotations import (
        apply_memory_annotations,
        load_memory_annotations,
        upsert_memory_annotation,
    )

    upsert_memory_annotation(tmp_path, "memory-ch-1", note="主角线索", pinned=True)
    data = load_memory_annotations(tmp_path)
    assert data["memory-ch-1"]["note"] == "主角线索"
    assert data["memory-ch-1"]["pinned"] is True

    items = apply_memory_annotations(
        [{"id": "memory-ch-1", "kind": "memory"}, {"id": "memory-ch-2", "kind": "memory"}],
        data,
    )
    annotated = next(i for i in items if i["id"] == "memory-ch-1")
    plain = next(i for i in items if i["id"] == "memory-ch-2")
    assert annotated["note"] == "主角线索"
    assert annotated["pinned"] is True
    assert not plain.get("pinned")
