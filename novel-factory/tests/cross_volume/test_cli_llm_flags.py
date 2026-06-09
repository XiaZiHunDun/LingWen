"""Phase 9.12 Task 7: CLI 4 新 flag 集 (--use-llm/--apply/--cache-path/--llm-confidence-threshold).

8 tests:
1. default_no_use_llm_runs_rule_based           # default 无新 flag → rule path
2. use_llm_flag_parses_correctly                # --use-llm 解析正确
3. apply_without_use_llm_errors                # --apply requires --use-llm (exit 1)
4. apply_with_use_llm_triggers_llm_path        # --use-llm --apply → LLM 路径
5. dry_run_default_no_write_in_llm_path        # --use-llm 0 --apply → dry-run, 0 写
6. cache_path_passed_to_llm_cache              # --cache-path 传 LLMCache
7. help_output_mentions_new_flags              # --help 提 4 新 flag
8. backward_compat_no_new_flags_still_works     # Phase 9.11 default 0 break
"""
from pathlib import Path
from unittest.mock import patch

import pytest

from infra.cli.commands.backfill import BackfillCommand
from infra.cli.parsers import create_parser


def parse_args(argv: list[str]):
    """Helper: parse argv through the full lingwen.py parser."""
    parser = create_parser()
    return parser.parse_args(argv)


def make_options(**overrides):
    """Helper: construct BackfillOptions for testing.

    Default = Phase 9.11 (no LLM flag) + Phase 9.12 LLM defaults.
    """
    from infra.cli.options import BackfillOptions

    defaults = dict(
        range=[],
        parallel=1,
        verbose=False,
        dry_run=True,
        output=None,
        vol=None,
        rules=None,
        # Phase 9.12 additive:
        use_llm=False,
        apply=False,
        cache_path=None,
        llm_confidence_threshold=3,
    )
    defaults.update(overrides)
    return BackfillOptions(**defaults)


class TestCLINewFlags:
    def test_default_no_use_llm_runs_rule_based(self):
        """No --use-llm → existing Phase 9.11 rule path (Backfiller called)."""
        args = parse_args(["backfill", "--vol", "1"])
        assert args.command == "backfill"
        # Default 0 LLM
        assert getattr(args, "use_llm", False) is False
        # Phase 9.11 default: dry_run=True (因为 0 --execute)
        assert args.dry_run is True
        # 0 --apply
        assert getattr(args, "apply", False) is False

    def test_use_llm_flag_parses_correctly(self):
        """--use-llm flag is parsed and stored (dry_run still default True)."""
        args = parse_args(["backfill", "--use-llm", "--vol", "1"])
        assert args.use_llm is True
        # dry_run default 仍 True (--use-llm 不动 dry_run, 需 --apply 写)
        assert args.dry_run is True
        # 0 --apply
        assert args.apply is False

    def test_apply_without_use_llm_errors(self, capsys):
        """--apply without --use-llm → exit code 1 with stderr error message."""
        options = make_options(use_llm=False, apply=True, vol=1, dry_run=True)
        cmd = BackfillCommand()
        with patch("infra.cross_volume.backfill.Backfiller") as mock_backfiller:
            result = cmd.execute(options)
        # Per spec: 友好错误 → exit 1, 0 调 Backfiller
        assert result == 1
        assert mock_backfiller.call_count == 0
        captured = capsys.readouterr()
        # Error goes to stderr
        assert "--apply requires --use-llm" in captured.err

    def test_apply_with_use_llm_triggers_llm_path(self):
        """--use-llm --apply → LLM path, scanner + storage instantiated."""
        # Per spec: 真实 LLM scan-and-write 是 Task 9 的活; Task 7 仅验证
        # LLM 路径被触发, components 实例化成功.
        with patch("infra.cross_volume.llm_scanner.LLMScanner") as mock_scanner, \
             patch("infra.cross_volume.llm_cache.LLMCache"), \
             patch("infra.ai_service.cost_tracker.CostTracker"):
            options = make_options(use_llm=True, apply=True, vol=1, dry_run=False)
            cmd = BackfillCommand()
            result = cmd.execute(options)
            # LLM path 走通, 返 0
            assert result == 0
            # LLMScanner 实例化 (constructor 被调)
            assert mock_scanner.called

    def test_dry_run_default_no_write_in_llm_path(self, capsys):
        """--use-llm (no --apply) → LLM dry-run, no storage write.

        Phase 9.12 Task 9: dry-run 路径也走真实 scan loop (instanceate scanner
        + scan_chapter 跑过), 唯一区别是不调 storage.append_nodes_atomic.
        这跟 Task 7 时代 (dry-run 0 实例化 scanner) 的 stub 行为不同, 是 Task 9
        写真实 scan 后的 additive 行为.
        """
        with patch("infra.cross_volume.llm_scanner.LLMScanner") as mock_scanner, \
             patch("infra.cross_volume.llm_cache.LLMCache"), \
             patch("infra.ai_service.cost_tracker.CostTracker"), \
             patch("infra.ai_service.tiered_router.TieredRouter"), \
             patch("infra.cross_volume.backfill._load_chapters",
                   return_value=[], create=True), \
             patch("infra.cross_volume.storage.RippleStorage") as mock_storage:
            options = make_options(use_llm=True, apply=False, vol=1)
            cmd = BackfillCommand()
            result = cmd.execute(options)
            assert result == 0
            # Task 9: dry-run 也实例化 scanner (real scan loop)
            assert mock_scanner.call_count == 1
            # dry-run: 0 写 storage
            assert mock_storage.call_count == 0
            captured = capsys.readouterr()
            # Hint visible (dry-run marker)
            assert "DRY-RUN" in captured.out or "dry-run" in captured.out.lower()

    def test_cache_path_passed_to_llm_cache(self, tmp_path):
        """--cache-path is passed through to LLMCache constructor."""
        cache_path = tmp_path / "custom_cache.json"
        with patch("infra.cross_volume.llm_cache.LLMCache") as mock_cache, \
             patch("infra.cross_volume.llm_scanner.LLMScanner"), \
             patch("infra.ai_service.cost_tracker.CostTracker"), \
             patch("infra.cross_volume.storage.RippleStorage"):
            options = make_options(
                use_llm=True, apply=True, vol=1, cache_path=cache_path
            )
            cmd = BackfillCommand()
            result = cmd.execute(options)
            assert result == 0
            # LLMCache instantiated with cache_path
            mock_cache.assert_called_once()
            called_with = mock_cache.call_args.kwargs.get("cache_path")
            assert called_with == cache_path

    def test_help_output_mentions_new_flags(self, capsys):
        """--help output mentions all 4 new flags."""
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["backfill", "--help"])
        # SystemExit code 0 for --help
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        for flag in [
            "--use-llm",
            "--apply",
            "--cache-path",
            "--llm-confidence-threshold",
        ]:
            assert flag in captured.out, f"help missing {flag}"

    def test_backward_compat_no_new_flags_still_works(self):
        """Phase 9.11 default (no new flags) → rule path, Backfiller called, 0 break."""
        with patch("infra.cross_volume.backfill.Backfiller") as mock_backfiller, \
             patch("infra.cross_volume.storage.RippleStorage"):
            # 模拟 Phase 9.11 default: --dry-run (no --execute)
            options = make_options(vol=1, dry_run=True)
            cmd = BackfillCommand()
            result = cmd.execute(options)
            assert result == 0
            # Backfiller.run called
            assert mock_backfiller.return_value.run.called
            # dry_run flag forwarded
            run_kwargs = mock_backfiller.return_value.run.call_args.kwargs
            assert run_kwargs.get("dry_run") is True
            assert run_kwargs.get("volume_filter") == 1
