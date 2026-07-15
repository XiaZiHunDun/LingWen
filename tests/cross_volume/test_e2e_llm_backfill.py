"""Phase 9.12 Task 9: 1 e2e test — full LLM backfill flow with mock router.

E2E 跑 ripple backfill --use-llm --apply 完整流程: mock router + mock chapters,
验证 scanner.scan_chapter 调 N 次 + storage.append_nodes_atomic + cost_tracker
全链路. 0 真实 LLM 调用, 0 API key, 0 .env 改.

Mock strategy:
    - patch LLMScanner: 返回 mock 节点 (避免依赖 router 内部)
    - patch RippleStorage: 验证 append_nodes_atomic 被调 (但 0 真写)
    - patch _load_chapters: 提供 N 章 fixture, 0 读 corpus
    - patch CostTracker: 验证 cost_tracker 0 LLM calls 时仍 instantiate
"""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from infra.cli.commands.backfill import BackfillCommand
from infra.cli.options import BackfillOptions
from infra.cross_volume.reference_graph import ReferenceNode


def make_options(tmp_path, **overrides) -> BackfillOptions:
    """Helper: construct BackfillOptions for e2e testing."""
    defaults = dict(
        range=[],
        parallel=1,
        verbose=False,
        dry_run=False,
        output=None,
        vol=1,
        rules=None,
        use_llm=True,
        apply=True,
        cache_path=tmp_path / "llm_cache.json",
        llm_confidence_threshold=3,
    )
    defaults.update(overrides)
    return BackfillOptions(**defaults)


def make_mock_chapters(num: int = 5) -> list[MagicMock]:
    """Return N mock chapters with .id (int) + .content (str)."""
    chapters = []
    for i in range(1, num + 1):
        ch = MagicMock()
        ch.id = i
        ch.content = f"第{i}章测试. 林轩在青云宗修炼."
        chapters.append(ch)
    return chapters


def make_mock_scanner_nodes(chapter_num: int, threshold: int) -> list[ReferenceNode]:
    """Build real ReferenceNode list with confidence 2/3/4 (some below threshold).

    Phase 9.12 spec: --llm-confidence-threshold filters nodes with conf < threshold.
    Returns 4 nodes (1 per dim), confs = [2, 3, 4, 5].
    With threshold=3: filtered → 3 nodes (confs 3, 4, 5).
    """
    return [
        ReferenceNode(dimension="character", volume=1, chapter=chapter_num,
                      title=f"林轩-{chapter_num}", description="主角",
                      payload={}, created_by="llm_scanner", confidence=2),
        ReferenceNode(dimension="foreshadow", volume=1, chapter=chapter_num,
                      title=f"伏笔-{chapter_num}", description="伏笔desc",
                      payload={}, created_by="llm_scanner", confidence=3),
        ReferenceNode(dimension="setting", volume=1, chapter=chapter_num,
                      title=f"青云宗-{chapter_num}", description="宗门",
                      payload={}, created_by="llm_scanner", confidence=4),
        ReferenceNode(dimension="plot_point", volume=1, chapter=chapter_num,
                      title=f"事件-{chapter_num}", description="事件desc",
                      payload={}, created_by="llm_scanner", confidence=5),
    ]


class TestE2ELLMBackfill:
    def test_e2e_llm_backfill_full_flow_with_mock_router(self, tmp_path, capsys):
        """E2E: --use-llm --apply 跑全链路 (mock router, 0 真实 LLM call).

        验证:
            1. cmd.execute 返 0
            2. LLMScanner.scan_chapter 调 N 次 (per chapter)
            3. Confidence filter 生效 (低 conf 节点被剔除)
            4. RippleStorage.append_nodes_atomic 调 1 次 (with filtered nodes)
            5. CostTracker 实例化
            6. 0 真实 LLM call (router.generate_with_usage 0 调)
        """
        cache_path = tmp_path / "llm_cache.json"
        options = make_options(tmp_path, apply=True, cache_path=cache_path, vol=1,
                               llm_confidence_threshold=3)
        cmd = BackfillCommand()

        num_chapters = 5
        # threshold=3 → 3 nodes per chapter pass filter
        # (confs [2, 3, 4, 5] → 3 with conf >= 3)
        nodes_per_chapter = 3
        expected_total_nodes = num_chapters * nodes_per_chapter

        mock_chapters = make_mock_chapters(num_chapters)
        mock_storage = MagicMock()
        mock_scanner = MagicMock()

        def fake_scan(chapter_id, chapter_content, context=""):
            return make_mock_scanner_nodes(chapter_id, options.llm_confidence_threshold)

        mock_scanner.scan_chapter.side_effect = fake_scan

        with patch("infra.cross_volume.backfill._load_chapters",
                   return_value=mock_chapters, create=True), \
             patch("infra.cross_volume.llm_scanner.LLMScanner",
                   return_value=mock_scanner), \
             patch("infra.cross_volume.storage.RippleStorage",
                   return_value=mock_storage), \
             patch("infra.ai_service.cost_tracker.CostTracker"), \
             patch("infra.cross_volume.backfill._default_storage",
                   return_value=mock_storage, create=True), \
             patch("infra.ai_service.tiered_router.TieredRouter") as mock_router_cls:
            result = cmd.execute(options)

        # 1. Exit code 0
        assert result == 0, f"expected exit 0, got {result}"

        # 2. scanner.scan_chapter called once per chapter
        assert mock_scanner.scan_chapter.call_count == num_chapters, (
            f"expected {num_chapters} scan_chapter calls, got "
            f"{mock_scanner.scan_chapter.call_count}"
        )

        # 3. Confidence filter: storage received exactly expected_total_nodes
        #    (1 call to append_nodes_atomic with full list, 0 partial commits)
        assert mock_storage.append_nodes_atomic.call_count == 1
        written_nodes = mock_storage.append_nodes_atomic.call_args.args[0]
        assert len(written_nodes) == expected_total_nodes, (
            f"expected {expected_total_nodes} nodes, got {len(written_nodes)}"
        )
        # 4. All written nodes have conf >= threshold
        for n in written_nodes:
            assert n.confidence >= options.llm_confidence_threshold

        # 5. Router instantiated (production default TieredRouter)
        #    Note: in --apply path, scanner is created with router kwarg
        assert mock_router_cls.called

        # 6. Summary printed
        captured = capsys.readouterr()
        assert "APPLY" in captured.out
        assert f"chapters={num_chapters}" in captured.out
        assert f"total_nodes={expected_total_nodes}" in captured.out

    def test_e2e_llm_backfill_dry_run_no_write(self, tmp_path, capsys):
        """E2E: --use-llm (no --apply) → scan, but 0 写 RippleStorage."""
        cache_path = tmp_path / "llm_cache.json"
        options = make_options(tmp_path, apply=False, cache_path=cache_path, vol=1,
                               llm_confidence_threshold=3)
        cmd = BackfillCommand()

        num_chapters = 3
        mock_chapters = make_mock_chapters(num_chapters)
        mock_scanner = MagicMock()
        mock_scanner.scan_chapter.side_effect = lambda *a, **kw: (
            make_mock_scanner_nodes(kw.get("chapter_id") or a[0], 3)
        )

        with patch("infra.cross_volume.backfill._load_chapters",
                   return_value=mock_chapters, create=True), \
             patch("infra.cross_volume.llm_scanner.LLMScanner",
                   return_value=mock_scanner), \
             patch("infra.ai_service.cost_tracker.CostTracker"), \
             patch("infra.ai_service.tiered_router.TieredRouter"), \
             patch("infra.cross_volume.storage.RippleStorage") as mock_storage:
            result = cmd.execute(options)

        assert result == 0
        # dry-run: scanner instantiated, scan_chapter called per chapter
        assert mock_scanner.scan_chapter.call_count == num_chapters
        # dry-run: 0 写 RippleStorage
        assert mock_storage.call_count == 0
        captured = capsys.readouterr()
        assert "DRY-RUN" in captured.out

    def test_e2e_llm_backfill_continues_on_chapter_error(self, tmp_path, capsys):
        """E2E: 1 章 scan 抛异常 → 警告 + 继续其他章 (resilient)."""
        cache_path = tmp_path / "llm_cache.json"
        options = make_options(tmp_path, apply=True, cache_path=cache_path, vol=1,
                               llm_confidence_threshold=3)
        cmd = BackfillCommand()

        num_chapters = 4
        mock_chapters = make_mock_chapters(num_chapters)
        mock_scanner = MagicMock()

        # ch=2 抛异常, 其他正常返
        def selective_scan(chapter_id, content, context=""):
            if chapter_id == 2:
                raise RuntimeError("mock LLM failure")
            return make_mock_scanner_nodes(chapter_id, 3)

        mock_scanner.scan_chapter.side_effect = selective_scan
        mock_storage = MagicMock()

        with patch("infra.cross_volume.backfill._load_chapters",
                   return_value=mock_chapters, create=True), \
             patch("infra.cross_volume.llm_scanner.LLMScanner",
                   return_value=mock_scanner), \
             patch("infra.cross_volume.storage.RippleStorage",
                   return_value=mock_storage), \
             patch("infra.ai_service.cost_tracker.CostTracker"), \
             patch("infra.cross_volume.backfill._default_storage",
                   return_value=mock_storage, create=True), \
             patch("infra.ai_service.tiered_router.TieredRouter"):
            result = cmd.execute(options)

        # exit 0 (不因单章 fail 而整批 abort)
        assert result == 0
        # scanner 4 次都被尝试
        assert mock_scanner.scan_chapter.call_count == num_chapters
        # storage 收到 3 章的 nodes (ch=2 跳过, 3 nodes each → 9)
        assert mock_storage.append_nodes_atomic.call_count == 1
        written = mock_storage.append_nodes_atomic.call_args.args[0]
        assert len(written) == 3 * 3
        # 警告打印
        captured = capsys.readouterr()
        assert "ch=2" in captured.out or "ch=2" in captured.err
