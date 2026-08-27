"""Phase 126 v16.2.1: tests for volume/ subdomain (3 modules).

Volume is ROOT — depended on by content (creator_dashboard → volume_plan/pulse)
+ settings (settings_docs/history → volume_plan) + onboarding (autodetect → volume_plan).

Migrated from infra/creator_volume_{plan,plan_share,pulse}.py.
"""
from __future__ import annotations


def test_volume_package_imports() -> None:
    """lingwen_creator.volume package is importable."""
    import lingwen_creator.volume

    assert lingwen_creator.volume.__name__ == "lingwen_creator.volume"


def test_plan_module_exports() -> None:
    """lingwen_creator.volume.plan exports load_volume_plan + save_volume_plan."""
    from lingwen_creator.volume.plan import load_volume_plan, save_volume_plan

    assert callable(load_volume_plan)
    assert callable(save_volume_plan)


def test_plan_share_module_exports() -> None:
    """lingwen_creator.volume.plan_share exports encode/decode_share_token."""
    from lingwen_creator.volume.plan_share import decode_share_token, encode_share_token

    assert callable(encode_share_token)
    assert callable(decode_share_token)


def test_pulse_module_exports() -> None:
    """lingwen_creator.volume.pulse exports build_volume_pulse."""
    from lingwen_creator.volume.pulse import build_volume_pulse

    assert callable(build_volume_pulse)


def test_plan_uses_shared_revision_import() -> None:
    """volume/plan.py imports from lingwen_creator.shared.revision (NOT infra.creator_revision).

    Per v16.2.0 shared migration, infra.creator_revision is a shim — new code must use the
    shared package path.
    """
    import lingwen_creator.volume.plan as plan_mod

    # Verify the names come from the shared package
    from lingwen_creator.shared.revision import (
        CreatorDocConflictError,
        content_revision,
    )

    assert plan_mod.CreatorDocConflictError is CreatorDocConflictError
    assert plan_mod.content_revision is content_revision


def test_plan_share_round_trip() -> None:
    """encode_share_token → decode_share_token round-trips data."""
    from lingwen_creator.volume.plan_share import decode_share_token, encode_share_token

    changes = [
        {"type": "added", "label": "卷一", "message": "新增卷「卷一」", "details": []},
    ]
    token = encode_share_token(changes=changes, global_outline_path="test/outline.md")
    decoded = decode_share_token(token)
    assert decoded["valid"] is True
    assert decoded["changes"] == changes


def test_legacy_import_paths_still_work() -> None:
    """Backwards compat: old `from infra.creator_volume_X import ...` works via shim."""
    from lingwen_creator.volume.plan import load_volume_plan
    from lingwen_creator.volume.plan_share import encode_share_token
    from lingwen_creator.volume.pulse import build_volume_pulse

    from infra.creator_volume_plan import load_volume_plan as LegacyLoad
    from infra.creator_volume_plan_share import encode_share_token as LegacyEncode
    from infra.creator_volume_pulse import build_volume_pulse as LegacyPulse

    assert LegacyLoad is load_volume_plan
    assert LegacyEncode is encode_share_token
    assert LegacyPulse is build_volume_pulse
