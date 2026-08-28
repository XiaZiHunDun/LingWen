"""Phase 126 v16.2.1: tests for volume/ subdomain (6 modules).

Volume is ROOT — depended on by content (creator_dashboard → volume_plan/pulse)
+ settings (settings_docs/history → volume_plan) + onboarding (autodetect → volume_plan).

Migrated from infra/creator_volume_{plan,plan_share,pulse,summary,templates}.py
+ infra/creator_template_approvals.py.
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


def test_summary_module_exports() -> None:
    """lingwen_creator.volume.summary exports build_volume_summary + write_volume_summary."""
    from lingwen_creator.volume.summary import (
        build_volume_summary,
        format_volume_summary_markdown,
        write_volume_summary,
    )

    assert callable(build_volume_summary)
    assert callable(format_volume_summary_markdown)
    assert callable(write_volume_summary)


def test_templates_module_exports() -> None:
    """lingwen_creator.volume.templates exports list_volume_templates + build_volume_template."""
    from lingwen_creator.volume.templates import (
        build_volume_template,
        list_volume_templates,
        save_custom_volume_template,
        validate_version_label,
    )

    assert callable(list_volume_templates)
    assert callable(build_volume_template)
    assert callable(save_custom_volume_template)
    assert callable(validate_version_label)


def test_template_approvals_module_exports() -> None:
    """lingwen_creator.volume.template_approvals exports list_template_approvals + approve."""
    from lingwen_creator.volume.template_approvals import (
        approve_template_approval,
        list_template_approvals,
        submit_template_version_approval,
    )

    assert callable(list_template_approvals)
    assert callable(approve_template_approval)
    assert callable(submit_template_version_approval)


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


def test_template_approvals_uses_intra_package_templates_import() -> None:
    """volume/template_approvals.py imports from lingwen_creator.volume.templates (intra-package).

    Per plan §12.2, intra-package imports avoid shim circular imports — the new package
    uses lingwen_creator.volume.templates, not infra.creator_volume_templates.
    """
    import lingwen_creator.volume.template_approvals as ta_mod

    # Verify the names come from the intra-package templates module
    from lingwen_creator.volume.templates import (
        _load_custom_store,
        _normalize_version_label,
        _save_custom_store,
        _snapshot_volumes,
        set_custom_template_version_label,
        set_factory_template_version_label,
    )

    assert ta_mod._load_custom_store is _load_custom_store
    assert ta_mod._normalize_version_label is _normalize_version_label
    assert ta_mod._save_custom_store is _save_custom_store
    assert ta_mod._snapshot_volumes is _snapshot_volumes
    assert ta_mod.set_custom_template_version_label is set_custom_template_version_label
    assert ta_mod.set_factory_template_version_label is set_factory_template_version_label


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


def test_summary_format_volume_summary_markdown() -> None:
    """format_volume_summary_markdown produces a structured markdown doc."""
    from lingwen_creator.volume.summary import format_volume_summary_markdown

    summary = {
        "start_chapter": 1,
        "end_chapter": 3,
        "chapter_count": 2,
        "missing_count": 1,
        "total_words": 1234,
        "chapters": [
            {"chapter": 1, "missing": False, "word_count": 600, "head": "开篇", "tail": ""},
            {"chapter": 2, "missing": True, "word_count": 0},
            {"chapter": 3, "missing": False, "word_count": 634, "head": "发展", "tail": ""},
        ],
    }
    md = format_volume_summary_markdown(title="测试", summary=summary)
    assert "《测试》" in md
    assert "ch001–ch003" in md
    assert "ch001" in md
    assert "ch002 — 缺失" in md
    assert "1234" in md


def test_templates_validate_version_label_smoke() -> None:
    """validate_version_label canonicalizes semver strings."""
    from lingwen_creator.volume.templates import validate_version_label

    assert validate_version_label("1.2.3") == "v1.2.3"
    assert validate_version_label("v1.2.3-beta") == "v1.2.3-beta"


def test_template_approvals_load_approval_sla_config_default() -> None:
    """load_approval_sla_config returns default config when file missing."""
    import json
    from pathlib import Path

    from lingwen_creator.volume.template_approvals import load_approval_sla_config

    # tmp_path is an empty dir — no SLA config file present
    cfg = load_approval_sla_config(Path("/tmp/lingwen-test-nonexistent-sla-config-path"))
    assert cfg["timeout_hours"] == 72
    assert cfg["email_on_submit"] is True


def test_legacy_shims_deleted() -> None:
    """v16.2.7 T4.5+T4.6: all 6 volume shims deleted, must raise ModuleNotFoundError.

    T4.5: creator_volume_plan_share/pulse/summary/template_approvals.
    T4.6: creator_volume_plan + creator_volume_templates.
    """
    import pytest

    with pytest.raises(ModuleNotFoundError):
        from infra.creator_volume_plan_share import encode_share_token  # noqa: F401
    with pytest.raises(ModuleNotFoundError):
        from infra.creator_volume_pulse import build_volume_pulse  # noqa: F401
    with pytest.raises(ModuleNotFoundError):
        from infra.creator_volume_summary import build_volume_summary  # noqa: F401
    with pytest.raises(ModuleNotFoundError):
        from infra.creator_template_approvals import list_template_approvals  # noqa: F401
    with pytest.raises(ModuleNotFoundError):
        from infra.creator_volume_plan import load_volume_plan  # noqa: F401
    with pytest.raises(ModuleNotFoundError):
        from infra.creator_volume_templates import list_volume_templates  # noqa: F401
