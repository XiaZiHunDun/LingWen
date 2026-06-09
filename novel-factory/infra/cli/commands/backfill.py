"""backfill command - Phase 9.11 CVG (Cross-Volume Graph) 4-dim rule-based backfill.

Runs Backfiller against 359-chapter corpus to extract character / foreshadow /
setting / plot_point ReferenceNodes. --dry-run is default (per 主公 Q4).

Phase 9.12 additive: LLM opt-in 4 flag (--use-llm/--apply/--cache-path/--llm-confidence-threshold).
LLM path 走 LLMScanner + LLMCache + CostTracker; 真实 LLM scan-and-write 是 Task 9,
本 Task 7 仅完成 CLI 接线 + 组件实例化 dry-run/apply 开关.
"""
import sys
from pathlib import Path

from infra.cli.options import BackfillOptions

from .base import Command

DEFAULT_RULES_PATH = Path("infra/cross_volume/extraction_rules.yaml")


class BackfillCommand(Command):
    """CVG backfill command (Phase 9.11 rule + Phase 9.12 LLM opt-in)"""

    name = "backfill"
    description = "跨卷涟漪 4 维回填 (Phase 9.11 规则 + Phase 9.12 LLM opt-in)"

    def execute(self, options: BackfillOptions) -> int:
        """
        Execute backfill command.

        Phase 9.12 LLM opt-in routing:
            --use-llm=False (default) → Phase 9.11 rule path (Backfiller)
            --use-llm=True, --apply=False → LLM dry-run (instantiate components, 0 写)
            --use-llm=True, --apply=True  → LLM apply (instantiate + 写 RippleStorage)
        --apply without --use-llm is a hard error (exit 1, friendly stderr msg).

        Args:
            options: BackfillOptions

        Returns:
            Exit code (0 success, 1 error)
        """
        # Phase 9.12: --apply requires --use-llm (强校验, 防误用)
        if options.apply and not options.use_llm:
            print(
                "Error: --apply requires --use-llm (rule-based backfill 用 --execute)",
                file=sys.stderr,
            )
            return 1

        # Phase 9.12: LLM opt-in 路径
        if options.use_llm:
            return self._execute_llm_path(options)

        # Phase 9.11: rule-based 路径 (backward compat 100% 保)
        from infra.cross_volume.backfill import Backfiller  # lazy import

        rules_path = Path(options.rules) if options.rules else DEFAULT_RULES_PATH
        try:
            backfiller = Backfiller(rules_path=rules_path)
        except (FileNotFoundError, ValueError) as e:
            print(f"[错误] Backfiller 初始化失败: {e}")
            return 1

        stats = backfiller.run(dry_run=options.dry_run, volume_filter=options.vol)
        print(stats.summary())
        if options.dry_run:
            print("(hint: 加 --execute 走真写)")
        return 0

    def _execute_llm_path(self, options: BackfillOptions) -> int:
        """Phase 9.12 LLM opt-in 路径: instantiate LLMScanner + LLMCache + CostTracker.

        TODO Task 9: replace dry-run scaffold with real scan-and-write loop:
            for ch in chapters(vol=options.vol):
                nodes = scanner.scan_chapter(ch.id, ch.content, context=...)
                nodes = [n for n in nodes if n.confidence >= options.llm_confidence_threshold]
                if options.apply: storage.append_nodes_atomic(nodes)
        """
        # Lazy import: LLM 路径 0 LLM 默认 0 调用, 仅在 --use-llm 时引入
        from infra.ai_service.cost_tracker import CostTracker
        from infra.cross_volume.llm_cache import LLMCache
        from infra.cross_volume.llm_scanner import LLMScanner

        cache = LLMCache(cache_path=options.cache_path)
        cost_tracker = CostTracker()  # 0 LLM calls yet; CostTracker records 0 0 cost
        # NOTE: scanner 必填 router (Task 9 will wire real LLM router).
        # 本 Task 7 仅完成 component 接线, 真实 LLM 调用留 Task 9.
        # dry-run 路径 0 实例化 scanner (per spec: 0 写 + 0 调 LLM).
        if not options.apply:
            print(
                f"[DRY-RUN] LLM scan vol={options.vol} (cache={cache._path}, "
                f"threshold={options.llm_confidence_threshold}) — 0 写, 0 LLM call"
            )
            return 0

        # --apply: instantiate scanner + storage (Task 9 写真实 scan-and-write)
        from infra.cross_volume.storage import RippleStorage  # lazy
        from infra.cross_volume.backfill import _default_storage  # reuse Phase 9.11 helper

        _scanner = LLMScanner(
            router=None,  # Task 9 will wire real LLM router
            cache=cache,
            fallback_backfiller=None,  # Task 9 will wire real fallback
            cost_tracker=cost_tracker,
        )
        _storage = _default_storage()  # infra/.state/ripple.db (Phase 9.10 default)
        print(
            f"[APPLY] LLM scan vol={options.vol} (cache={cache._path}, "
            f"threshold={options.llm_confidence_threshold}) — TODO Task 9 写真实"
        )
        return 0
