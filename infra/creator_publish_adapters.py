"""Phase 126 v16.2.5 shim: re-export from lingwen_creator.export.publish_adapters.

Migrated to packages/lingwen-creator/src/lingwen_creator/export/publish_adapters.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_publish_adapters import (
        PublishAdapter, PublishCapabilities, PublishSubmitResult,
        FanqiePublishAdapter, QidianPublishAdapter, JjwxcPublishAdapter, CustomPublishAdapter,
        get_publish_adapter, list_publish_platforms,
    )

Shim will be deleted in v16.2.7 final cleanup.

NOTE: publish_adapters.py is pure Python (zero infra.creator_X imports).
The actual migration to lingwen_creator.export.publish_adapters.py happens in T1.c.
This shim is created early so it can be referenced from the migrated publish.py in T1.c.
"""
from lingwen_creator.export.publish_adapters import *  # noqa: F403
