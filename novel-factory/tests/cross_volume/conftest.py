"""Phase 9.11: shared fixtures for cross_volume tests.

`rules_yaml` and `corpus` fixtures are defined here at module level so they
are visible to all test classes in this directory (TestBackfiller,
TestBackfillIntegration, TestBackfillE2E, etc.).
"""
from pathlib import Path

import pytest


@pytest.fixture
def rules_yaml(tmp_path: Path) -> Path:
    yaml_content = """
character:
  name_pattern: "[李青云林凡]{2,3}"
  alias_map: {"凡": "林凡"}
  blacklist: []
  occurrence_threshold: 1
foreshadow:
  keywords: ["伏笔", "暗示"]
  pattern: "(?P<content>[\\u4e00-\\u9fff]{6,30}?(?:伏笔|暗示))"
  chapter_window: 5
setting:
  name_pattern: "[\\u4e00-\\u9fff]{2,6}(?:学院|山门|大陆|帝国|秘境|宗)"
  blacklist: []
  occurrence_threshold: 1
plot_point:
  pattern: "^##\\s+(.+)$"
  min_length: 8
  max_length: 50
  blacklist: []
"""
    rules_path = tmp_path / "rules.yaml"
    rules_path.write_text(yaml_content, encoding="utf-8")
    return rules_path


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    # ch001: character + setting
    (corpus_root / "ch001.md").write_text("李青云拜入凌霄宗, 林凡登场.", encoding="utf-8")
    (corpus_root / "ch001_大纲.md").write_text(
        "# 章节一\n## 青云觉醒获得古剑碎片\n## 林凡登场\n", encoding="utf-8"
    )
    # ch002: character (跨章聚合 ch001)
    (corpus_root / "ch002.md").write_text("李青云与林凡激战.", encoding="utf-8")
    (corpus_root / "ch002_大纲.md").write_text(
        "# 章节二\n## 凌霄宗大战林凡\n", encoding="utf-8"
    )
    return corpus_root
