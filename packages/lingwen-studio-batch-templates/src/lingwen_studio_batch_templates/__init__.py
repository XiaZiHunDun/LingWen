"""lingwen-studio-batch-templates — canonical studio batch templates package.

Phase 47 P3-ARCHDEBT: relocated from infra/studio_batch_templates.py (234 LOC).
NOT-LEAF (depends on lingwen-studio-registry).
"""

from __future__ import annotations

from lingwen_studio_batch_templates.service import (
    BatchTemplate,
    create_batch_template,
    delete_batch_template,
    get_batch_template,
    list_batch_templates,
    update_batch_template,
)

__all__ = [
    "BatchTemplate",
    "create_batch_template",
    "list_batch_templates",
    "get_batch_template",
    "update_batch_template",
    "delete_batch_template",
]