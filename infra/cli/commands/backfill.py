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
        corpus_root = Path(options.corpus_root) if options.corpus_root else None
        try:
            backfiller = Backfiller(
                rules_path=rules_path,
                corpus_root=corpus_root or Path("03_内容仓库/04_正文"),
            )
        except (FileNotFoundError, ValueError) as e:
            print(f"[错误] Backfiller 初始化失败: {e}")
            return 1

        stats = backfiller.run(dry_run=options.dry_run, volume_filter=options.vol)
        print(stats.summary())
        if options.dry_run:
            print("(hint: 加 --execute 写入 ripple.db; 已存在 node 自动跳过)")
        elif stats.nodes_written == 0 and stats.nodes_skipped > 0:
            print("(hint: 全部 node 已存在, 幂等 re-run 0 新写入)")
        return 0

    def _execute_llm_path(self, options: BackfillOptions) -> int:
        """Phase 9.12 LLM opt-in 路径: real scan-and-write loop (Task 9 完成).

        流程:
            1. instantiate LLMScanner(router=real or mock, cache, cost_tracker)
            2. _load_chapters(volume_filter=options.vol)
            3. for ch in chapters:
                nodes = scanner.scan_chapter(ch.id, ch.content, context="")
                nodes = filter(conf >= options.llm_confidence_threshold)
                累积到 batch; 单章出错 log 警告 + 继续 (resilient)
            4. if --apply and batch: storage.append_nodes_atomic(batch) (1 atomic)
            5. 打印 summary

        Router instantiation 走 lazy: 优先 TieredRouter(providers={}) (test 路径不抛
        时也 OK), 真 LLM 调时才校验 missing tier.
        """
        from infra.ai_service.cost_tracker import CostTracker
        from infra.ai_service.tiered_router import TieredRouter
        from infra.cross_volume.backfill import (
            _default_storage,
            _load_chapters,
        )
        from infra.cross_volume.llm_cache import LLMCache
        from infra.cross_volume.llm_scanner import LLMScanner
        from infra.cross_volume.scanner_calibration import load_scanner_calibration

        cal = load_scanner_calibration(getattr(options, "calibration_path", None))
        write_threshold = (
            options.llm_confidence_threshold
            if options.llm_confidence_threshold is not None
            else cal.node_write_threshold
        )

        cache = LLMCache(cache_path=options.cache_path)
        cost_tracker = CostTracker()

        # Production 默认 TieredRouter; test 路径用 mock patch 替换整个 LLMScanner,
        # 不会走到 router.generate. 0 LLM call = 0 tier provider 校验, 构造轻量.
        # 走 lazy 模式: 0 走 --apply 真 LLM 路径时, provider 0 注入会 fail 真 LLM call
        # (而非构造时), 友好。
        router: object = None
        try:
            router = TieredRouter(providers={})
        except Exception:
            # 缺 provider (test env 0 patch LLMScanner 时, 真 TieredRouter 缺 tier 抛错)
            # 走 None 兜底, 0 真 LLM 调时 0 触发; 触发了再 fail
            router = None

        scanner = LLMScanner(
            router=router,
            cache=cache,
            fallback_backfiller=None,  # Phase 9.12 opt-in, 0 fallback rule
            cost_tracker=cost_tracker,
        )

        chapters = _load_chapters(volume_filter=options.vol)

        batch: list = []
        total_nodes = 0
        mode = "APPLY" if options.apply else "DRY-RUN"

        for ch in chapters:
            try:
                nodes = scanner.scan_chapter(ch.id, ch.content, context="")
                nodes = [n for n in nodes if n.confidence >= write_threshold]
                total_nodes += len(nodes)
                batch.extend(nodes)
            except Exception as e:
                print(f"[警告] ch={ch.id} 扫描失败: {e}", file=sys.stderr)
                continue

        written_nodes = 0
        if options.apply and batch:
            storage = _default_storage()
            storage.append_nodes_atomic(batch)
            written_nodes = len(batch)

        print(
            f"[{mode}] LLM scan vol={options.vol} (cache={cache._path}, "
            f"threshold={write_threshold}): "
            f"chapters={len(chapters)}, total_nodes={total_nodes}, "
            f"written_nodes={written_nodes}"
        )
        return 0
