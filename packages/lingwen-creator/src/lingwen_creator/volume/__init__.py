"""Phase 126 v16.2.1: volume/ subdomain (creator volume plan / pulse / share / summary / templates / template_approvals).

Bounded context: per-volume planning, lock state, deviation diff, pulse summary,
share-token encode/decode, volume-level summary markdown, template CRUD + version
changelog + rollback + approval workflow.

Volume is ROOT — depended on by content (creator_dashboard → volume_plan/pulse)
+ settings (settings_docs/history → volume_plan) + onboarding (autodetect → volume_plan).
Cycles via lazy imports in volume_plan_diff_payload (`from
lingwen_creator.content.dashboard import _excerpt`, kept function-body-local)
are broken by deferring the import to call time.

Migrated from infra/creator_volume_{plan,plan_share,pulse,summary,templates}.py
+ infra/creator_template_approvals.py.
"""

from lingwen_creator.volume.plan import *  # noqa: F403
from lingwen_creator.volume.plan_share import *  # noqa: F403
from lingwen_creator.volume.pulse import *  # noqa: F403
from lingwen_creator.volume.summary import *  # noqa: F403
from lingwen_creator.volume.template_approvals import *  # noqa: F403
from lingwen_creator.volume.templates import *  # noqa: F403
