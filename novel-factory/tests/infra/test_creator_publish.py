"""Tests for creator_publish."""
from __future__ import annotations

from pathlib import Path

from infra.creator_publish import list_creator_publish_history, submit_creator_publish
from infra.studio_registry import StudioProject


def test_submit_and_list_publish(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    project = StudioProject(
        slug="pub-test",
        name="发布测试",
        role="production",
        root=root,
        location="projects",
    )
    entry = submit_creator_publish(
        project,
        platform="fanqie",
        include_outline=True,
        intro="简介",
    )
    assert entry["platform"] == "fanqie"
    assert entry["status"] in {"queued", "adapter_stub"}
    assert entry.get("adapter_id") == "fanqie"
    history = list_creator_publish_history(project)
    assert len(history["entries"]) == 1
    assert history["entries"][0]["id"] == entry["id"]
