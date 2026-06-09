"""Phase 9.11: 10-chapter fixture exports for E2E test.

供 tests/cross_volume/test_backfill.py::TestBackfillE2E 引用:
- SAMPLE_CORPUS_ROOT: 10 章 .md (5 正文 + 5 大纲) sample corpus
- SAMPLE_RULES_YAML: 跟 corpus 匹配的最小 rules (含 character / setting / plot_point 各 ≥ 1)
"""
from pathlib import Path

SAMPLE_CORPUS_ROOT = Path(__file__).parent  # fixtures/ 目录含 5 章 .md

# 规则调小让 E2E test 容易过 (threshold=1, blacklist 空)
SAMPLE_RULES_YAML = """
character:
  name_pattern: "[李青云林凡]{2,3}"
  alias_map: {"凡": "林凡"}
  blacklist: []
  occurrence_threshold: 1
foreshadow:
  keywords: ["伏笔"]
  pattern: "(?P<content>[\\u4e00-\\u9fff]{6,30}?(?:伏笔))"
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
