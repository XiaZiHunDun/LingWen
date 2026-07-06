"""Tests for creator_publish_adapters."""
from __future__ import annotations

from pathlib import Path

from infra.creator_publish_adapters import (
    FanqiePublishAdapter,
    get_publish_adapter,
    list_publish_platforms,
)
from infra.studio_registry import StudioProject


def test_list_publish_platforms() -> None:
    project = StudioProject(
        slug="demo",
        name="演示",
        role="production",
        root=Path("/tmp/demo"),
        location="projects",
    )
    platforms = list_publish_platforms(project)
    assert len(platforms) == 4
    assert platforms[0]["id"] in {"fanqie", "qidian", "jjwxc", "custom"}


def test_fanqie_adapter_submit() -> None:
    project = StudioProject(
        slug="demo",
        name="演示",
        role="production",
        root=Path("/tmp/demo"),
        location="projects",
    )
    adapter = get_publish_adapter("fanqie")
    assert isinstance(adapter, FanqiePublishAdapter)
    result = adapter.submit(project, include_outline=True, intro="简介", mode="submission")
    assert result.status == "adapter_stub"
    assert result.adapter_id == "fanqie"
