"""Phase 126 v16.2.5: tests for export/ subdomain (5 modules)."""
from __future__ import annotations


def test_export_package_imports() -> None:
    """lingwen_creator.export package is importable."""
    import lingwen_creator.export

    assert lingwen_creator.export.__name__ == "lingwen_creator.export"


def test_common_module_exports() -> None:
    """lingwen_creator.export.common exports export_metadata + load_export_chapters."""
    from lingwen_creator.export.common import (
        export_metadata,
        load_export_chapters,
        resolve_export_chapter_nums,
        split_paragraphs,
        utc_modified_iso,
        written_chapter_nums,
    )

    assert callable(export_metadata)
    assert callable(load_export_chapters)
    assert callable(resolve_export_chapter_nums)
    assert callable(split_paragraphs)
    assert callable(written_chapter_nums)
    assert callable(utc_modified_iso)


def test_docx_module_exports() -> None:
    """lingwen_creator.export.docx exports build_creator_docx_bytes."""
    from lingwen_creator.export.docx import build_creator_docx_bytes

    assert callable(build_creator_docx_bytes)


def test_epub_module_exports() -> None:
    """lingwen_creator.export.epub exports build_creator_epub_bytes."""
    from lingwen_creator.export.epub import build_creator_epub_bytes

    assert callable(build_creator_epub_bytes)


def test_publish_module_exports() -> None:
    """lingwen_creator.export.publish exports submit + list_history + list_platforms."""
    from lingwen_creator.export.publish import (
        list_creator_publish_history,
        submit_creator_publish,
    )

    assert callable(submit_creator_publish)
    assert callable(list_creator_publish_history)


def test_publish_adapters_module_exports() -> None:
    """lingwen_creator.export.publish_adapters exports Protocol + 4 stubs + get_publish_adapter."""
    from lingwen_creator.export.publish_adapters import (
        CustomPublishAdapter,
        FanqiePublishAdapter,
        JjwxcPublishAdapter,
        PublishAdapter,
        PublishCapabilities,
        PublishSubmitResult,
        QidianPublishAdapter,
        get_publish_adapter,
        list_publish_platforms,
    )

    assert callable(get_publish_adapter)
    assert callable(list_publish_platforms)
    assert FanqiePublishAdapter.platform_id == "fanqie"
    assert QidianPublishAdapter.platform_id == "qidian"
    assert JjwxcPublishAdapter.platform_id == "jjwxc"
    assert CustomPublishAdapter.platform_id == "custom"


def test_legacy_import_paths_still_work() -> None:
    """Backwards compat: `from infra.creator_export_X import ...` and `from infra.creator_publish_X import ...`."""
    # Shim equivalence checks
    from lingwen_creator.export.common import export_metadata, load_export_chapters
    from lingwen_creator.export.docx import build_creator_docx_bytes
    from lingwen_creator.export.epub import build_creator_epub_bytes
    from lingwen_creator.export.publish import submit_creator_publish
    from lingwen_creator.export.publish_adapters import (
        FanqiePublishAdapter,
        get_publish_adapter,
    )

    from infra.creator_export_common import (
        export_metadata as LegacyExportMeta,
    )
    from infra.creator_export_common import (
        load_export_chapters as LegacyLoadChapters,
    )
    from infra.creator_export_docx import build_creator_docx_bytes as LegacyDocx
    from infra.creator_export_epub import build_creator_epub_bytes as LegacyEpub
    from infra.creator_publish import submit_creator_publish as LegacyPublish
    from infra.creator_publish_adapters import (
        FanqiePublishAdapter as LegacyFanqie,
    )
    from infra.creator_publish_adapters import (
        get_publish_adapter as LegacyGetAdapter,
    )

    assert LegacyExportMeta is export_metadata
    assert LegacyLoadChapters is load_export_chapters
    assert LegacyDocx is build_creator_docx_bytes
    assert LegacyEpub is build_creator_epub_bytes
    assert LegacyPublish is submit_creator_publish
    assert LegacyGetAdapter is get_publish_adapter
    assert LegacyFanqie is FanqiePublishAdapter


def test_intra_package_imports_no_cycle() -> None:
    """Intra-package imports (export.common + export.publish_adapters) work without shim detour.

    Per v16.2.4 §5.1 lesson 1: intra-package imports must use new path,
    not infra shim, to avoid cycle via shim proxy.
    """
    from lingwen_creator.export.docx import build_creator_docx_bytes
    from lingwen_creator.export.epub import build_creator_epub_bytes
    from lingwen_creator.export.publish import submit_creator_publish

    # All callable, no ImportError
    assert callable(build_creator_docx_bytes)
    assert callable(build_creator_epub_bytes)
    assert callable(submit_creator_publish)
