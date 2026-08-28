"""Phase 126 v16.2.5 shim: re-export from lingwen_creator.export.docx.

Migrated to packages/lingwen-creator/src/lingwen_creator/export/docx.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_export_docx import build_creator_docx_bytes, ...

Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.export.docx import *  # noqa: F403
