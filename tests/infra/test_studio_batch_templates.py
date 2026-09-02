"""Unit tests for infra.studio_batch_templates persistence + operations."""

import pytest

from infra import studio_batch_templates as tpl


@pytest.fixture(autouse=True)
def _tmp_templates_dir(tmp_path, monkeypatch):
    """Redirect template storage to a temp dir so tests never touch the repo."""
    monkeypatch.setattr(tpl, "templates_dir", lambda: tmp_path)


def test_create_and_get_roundtrip():
    template = tpl.create_batch_template(
        slug="my-project",
        name="Daily Pilot",
        start_chapter=1,
        end_chapter=5,
        budget_usd=0.15,
        mode="pilot",
        event_types=["job_state", "chapter_completed"],
    )
    assert template.template_id
    loaded = tpl.get_batch_template(template.template_id)
    assert loaded is not None
    assert loaded["name"] == "Daily Pilot"
    assert loaded["slug"] == "my-project"
    assert loaded["event_types"] == ["job_state", "chapter_completed"]


def test_create_validates_range_and_budget():
    with pytest.raises(ValueError, match="end_chapter"):
        tpl.create_batch_template(
            slug="x",
            name="Bad",
            start_chapter=5,
            end_chapter=1,
        )
    with pytest.raises(ValueError, match="budget"):
        tpl.create_batch_template(
            slug="x",
            name="Bad",
            start_chapter=1,
            end_chapter=2,
            budget_usd=200,
        )
    with pytest.raises(ValueError, match="name"):
        tpl.create_batch_template(slug="x", name="  ", start_chapter=1, end_chapter=2)


def test_list_filters_by_slug():
    tpl.create_batch_template(slug="a", name="A", start_chapter=1, end_chapter=2)
    tpl.create_batch_template(slug="b", name="B", start_chapter=1, end_chapter=2)
    assert len(tpl.list_batch_templates()) == 2
    all_a = tpl.list_batch_templates(slug="a")
    assert len(all_a) == 1 and all_a[0]["slug"] == "a"


def test_list_skips_malformed_file():
    tpl.create_batch_template(slug="a", name="A", start_chapter=1, end_chapter=2)
    # Write a malformed template file directly; listing must not crash.
    bad = tpl.templates_dir() / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    rows = tpl.list_batch_templates()
    assert len(rows) == 1


def test_update_preserves_unspecified_fields():
    template = tpl.create_batch_template(
        slug="a",
        name="A",
        start_chapter=1,
        end_chapter=2,
        budget_usd=0.1,
    )
    updated = tpl.update_batch_template(
        template.template_id,
        start_chapter=3,
        end_chapter=4,
        description="updated",
    )
    assert updated.start_chapter == 3
    assert updated.name == "A"  # not passed → unchanged
    assert updated.end_chapter == 4
    assert updated.budget_usd == 0.1  # not passed → unchanged
    assert updated.description == "updated"
    assert updated.updated_at >= template.created_at


def test_update_validation():
    template = tpl.create_batch_template(
        slug="a",
        name="A",
        start_chapter=1,
        end_chapter=2,
    )
    with pytest.raises(ValueError, match="end_chapter"):
        tpl.update_batch_template(template.template_id, end_chapter=0)
    with pytest.raises(ValueError, match="name"):
        tpl.update_batch_template(template.template_id, name=" ")


def test_update_unknown_raises():
    with pytest.raises(LookupError):
        tpl.update_batch_template("nope", name="X")


def test_delete_removes_file():
    template = tpl.create_batch_template(slug="a", name="A", start_chapter=1, end_chapter=2)
    deleted = tpl.delete_batch_template(template.template_id)
    assert deleted.template_id == template.template_id
    assert tpl.get_batch_template(template.template_id) is None


def test_delete_unknown_raises():
    with pytest.raises(LookupError):
        tpl.delete_batch_template("nope")
