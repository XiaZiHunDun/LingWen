"""Phase 126 v16.2.1 shim: re-export from lingwen_creator.volume.template_approvals.

Migrated to packages/lingwen-creator/src/lingwen_creator/volume/template_approvals.py.
This shim maintains backwards compat for consumers using:
    from infra.creator_template_approvals import list_template_approvals, ...

Private names are re-exported explicitly because Python's `from module import *`
skips underscore-prefixed names, but existing tests (test_creator_template_approval_sla,
test_creator_v35_features) import private names like `_load_store` from this shim path.

NOTE: Monkeypatching the shim's private attributes does NOT affect the underlying
implementation (template_approvals.py uses its own namespace). Tests that need to
monkeypatch private helpers must target `lingwen_creator.volume.template_approvals`
directly via string path.

Shim will be deleted in v16.2.7 final cleanup.
"""
import lingwen_creator.volume.template_approvals as _impl  # noqa: F401
from lingwen_creator.volume.template_approvals import *  # noqa: F403

# Re-export underscore-prefixed names used by existing tests
_approvals_path = _impl._approvals_path
_chain_config_path = _impl._chain_config_path
_current_step_assignees = _impl._current_step_assignees
_load_store = _impl._load_store
_normalize_assignee_groups = _impl._normalize_assignee_groups
_notification_event = _impl._notify_approval_event
_notify_approval_event = _impl._notify_approval_event
_now_iso = _impl._now_iso
_parse_iso = _impl._parse_iso
_public_approval_row = _impl._public_approval_row
_save_store = _impl._save_store
_sla_config_path = _impl._sla_config_path
_step_assignee_groups = _impl._step_assignee_groups
