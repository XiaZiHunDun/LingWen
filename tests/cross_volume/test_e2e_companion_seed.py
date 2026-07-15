"""Companion e2e project seed tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from infra.cross_volume.e2e_seed import E2E_COMPANION_SLUG, ensure_e2e_companion_project


@pytest.fixture
def isolated_factory(tmp_path, monkeypatch):
    factory = tmp_path / "factory"
    factory.mkdir()
    projects = factory / "projects"
    projects.mkdir()
    monkeypatch.setenv("LINGWEN_FACTORY_ROOT", str(factory))
    monkeypatch.chdir(factory)
    return factory


class TestE2ECompanionProjectSeed:
    def test_ensure_e2e_companion_project_idempotent(self, isolated_factory):
        root1 = ensure_e2e_companion_project()
        root2 = ensure_e2e_companion_project()
        assert root1 == root2
        assert (root1 / "config/project.yaml").exists()
        yaml_text = (root1 / "config/project.yaml").read_text(encoding="utf-8")
        assert "companion" in yaml_text
        body = root1 / "03_内容仓库/04_正文/ch001.md"
        assert body.exists()
        plan = json.loads((root1 / ".state/volume_plan.json").read_text(encoding="utf-8"))
        assert plan["volumes"][0]["label"] == "一"
        assert plan["volumes"][0]["locked"] is True
        assert E2E_COMPANION_SLUG in str(root1)
