"""Phase 9.33 F18: production backfill --execute idempotency + pre/post counts + CLI."""
from pathlib import Path
from unittest.mock import patch

import pytest

from infra.cli.commands.backfill import BackfillCommand
from infra.cli.options import BackfillOptions
from infra.cli.parsers import create_parser
from infra.cross_volume.backfill import Backfiller
from infra.cross_volume.reference_graph import CrossVolumeReferenceGraph
from infra.cross_volume.storage import RippleStorage


RULES_YAML = """
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


@pytest.fixture
def rules_yaml(tmp_path):
    p = tmp_path / "rules.yaml"
    p.write_text(RULES_YAML, encoding="utf-8")
    return p


@pytest.fixture
def corpus(tmp_path):
    root = tmp_path / "corpus"
    root.mkdir()
    (root / "ch001.md").write_text("李青云拜入凌霄宗, 林凡登场.", encoding="utf-8")
    (root / "ch001_大纲.md").write_text(
        "# 章节一\n## 青云觉醒获得古剑碎片\n", encoding="utf-8"
    )
    (root / "ch002.md").write_text("李青云与林凡激战.", encoding="utf-8")
    return root


def _make_backfiller(rules_yaml, corpus, db_path):
    storage = RippleStorage(db_path=db_path)
    graph = CrossVolumeReferenceGraph(storage=storage)
    return Backfiller(rules_path=rules_yaml, corpus_root=corpus, graph=graph)


class TestBackfillProductionExecute:
    def test_execute_reports_pre_post_node_counts(self, rules_yaml, corpus, tmp_path):
        backfiller = _make_backfiller(rules_yaml, corpus, tmp_path / "ripple.db")
        stats = backfiller.run(dry_run=False)
        assert stats.dry_run is False
        assert stats.pre_node_count == 0
        assert stats.post_node_count == stats.pre_node_count + stats.nodes_written
        assert stats.nodes_written == stats.total_count
        assert stats.nodes_skipped == 0
        assert "written=" in stats.summary()
        assert "pre_nodes=0" in stats.summary()

    def test_execute_idempotent_second_run_writes_zero(self, rules_yaml, corpus, tmp_path):
        backfiller = _make_backfiller(rules_yaml, corpus, tmp_path / "ripple.db")
        first = backfiller.run(dry_run=False)
        assert first.nodes_written >= 1

        second = backfiller.run(dry_run=False)
        assert second.nodes_written == 0
        assert second.nodes_skipped == first.total_count
        assert second.pre_node_count == first.post_node_count
        assert second.post_node_count == second.pre_node_count

    def test_execute_partial_existing_only_writes_new_nodes(self, rules_yaml, corpus, tmp_path):
        backfiller = _make_backfiller(rules_yaml, corpus, tmp_path / "ripple.db")
        first_exec = backfiller.run(dry_run=False)
        pre_after_first = first_exec.post_node_count
        assert pre_after_first >= 1

        (corpus / "ch003.md").write_text("李青云造访天机学院.", encoding="utf-8")
        second_exec = backfiller.run(dry_run=False)
        assert second_exec.pre_node_count == pre_after_first
        assert second_exec.nodes_written >= 1
        assert second_exec.post_node_count > second_exec.pre_node_count
        loaded = backfiller._graph._storage.load_all_nodes()
        assert any(n.payload.get("name") == "天机学院" for n in loaded)

    def test_cli_execute_flag_sets_dry_run_false(self):
        args = create_parser().parse_args(["backfill", "--execute", "--vol", "1"])
        assert args.command == "backfill"
        assert args.dry_run is False

    def test_cli_execute_integration_prints_executed_summary(self, rules_yaml, corpus, tmp_path, capsys):
        opts = BackfillOptions(
            range=[],
            parallel=1,
            verbose=False,
            dry_run=False,
            vol=None,
            rules=str(rules_yaml),
            corpus_root=str(corpus),
            use_llm=False,
            apply=False,
            cache_path=None,
            llm_confidence_threshold=3,
        )
        cmd = BackfillCommand()
        rc = cmd.execute(opts)
        assert rc == 0
        out = capsys.readouterr().out
        assert "[EXECUTED]" in out
        assert "written=" in out
        assert "pre_nodes=" in out

    def test_cli_default_dry_run_hint_mentions_execute(self, rules_yaml, corpus, tmp_path, capsys):
        opts = BackfillOptions(
            range=[],
            parallel=1,
            verbose=False,
            dry_run=True,
            vol=None,
            rules=str(rules_yaml),
            corpus_root=str(corpus),
            use_llm=False,
            apply=False,
            cache_path=None,
            llm_confidence_threshold=3,
        )
        with patch("infra.cross_volume.backfill.Backfiller") as mock_cls:
            mock_cls.return_value.run.return_value.summary.return_value = "[DRY-RUN] total=1"
            mock_cls.return_value.run.return_value = mock_cls.return_value.run.return_value
            from infra.cross_volume.backfill import BackfillStats

            mock_cls.return_value.run.return_value = BackfillStats(
                character_count=1,
                foreshadow_count=0,
                setting_count=0,
                plot_point_count=0,
                total_count=1,
                elapsed_s=0.01,
                dry_run=True,
            )
            rc = BackfillCommand().execute(opts)
        assert rc == 0
        assert "加 --execute" in capsys.readouterr().out
