"""ripple-scan command — Phase 9.34 F19 LLM scanner confidence calibration."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

from infra.ai_service.cost_tracker import CostTracker
from infra.ai_service.model_tiers import ModelTier
from infra.cli.options import RippleScanOptions
from infra.cross_volume.llm_cache import LLMCache
from infra.cross_volume.llm_scanner import LLMScanner
from infra.cross_volume.scanner_calibration import (
    format_calibration_report,
    load_gold_labels,
    load_scanner_calibration,
    recommend_threshold,
    sweep_thresholds,
)

from .base import Command

DEFAULT_GOLD = Path("tests/cross_volume/fixtures/scanner_calibration_gold.yaml")
DEFAULT_FIXTURES = Path("tests/cross_volume/fixtures/llm_responses")
FIXTURE_NAMES = (
    "character_ch001.json",
    "foreshadow_ch001.json",
    "setting_ch001.json",
    "plot_point_ch001.json",
)


class RippleScanCommand(Command):
    name = "ripple-scan"
    description = "LLM scanner 置信度校准 (Phase 9.34)"

    def execute(self, options: RippleScanOptions) -> int:
        if not options.calibrate:
            print("Error: ripple-scan requires --calibrate (threshold sweep report)", file=sys.stderr)
            print("  Example: lingwen.py ripple-scan --calibrate", file=sys.stderr)
            return 1
        return self._run_calibrate(options)

    def _run_calibrate(self, options: RippleScanOptions) -> int:
        gold_path = options.gold_path or DEFAULT_GOLD
        fixture_dir = options.fixture_dir or DEFAULT_FIXTURES
        if not gold_path.is_file():
            print(f"Error: gold labels not found: {gold_path}", file=sys.stderr)
            return 1
        if not fixture_dir.is_dir():
            print(f"Error: fixture dir not found: {fixture_dir}", file=sys.stderr)
            return 1

        gold_by_ch = load_gold_labels(gold_path)
        gold_keys = gold_by_ch.get(options.chapter)
        if not gold_keys:
            print(
                f"Error: no gold_nodes for chapter {options.chapter} in {gold_path}",
                file=sys.stderr,
            )
            return 1

        nodes = self._scan_chapter_from_fixtures(fixture_dir, options.chapter)
        cal = load_scanner_calibration(options.calibration)
        metrics = sweep_thresholds(
            nodes,
            gold_keys,
            min_threshold=cal.calibrate_threshold_min,
            max_threshold=cal.calibrate_threshold_max,
        )
        recommended = recommend_threshold(metrics)
        print(
            format_calibration_report(metrics, recommended=recommended, current=cal)
        )
        return 0

    @staticmethod
    def _scan_chapter_from_fixtures(fixture_dir: Path, chapter_id: int) -> list:
        """Build nodes via LLMScanner + mock router (0 real LLM)."""
        suffix = f"ch{chapter_id:03d}"
        names = [n.replace("ch001", suffix) for n in FIXTURE_NAMES]
        for name in names:
            if not (fixture_dir / name).is_file():
                raise FileNotFoundError(f"missing fixture {fixture_dir / name}")

        router = MagicMock()
        router.generate_with_usage.side_effect = [
            ((fixture_dir / n).read_text(encoding="utf-8"), {"input_tokens": 10, "output_tokens": 5})
            for n in names
        ]
        fb = MagicMock()
        fb.extractors = {}
        scanner = LLMScanner(
            router=router,
            cache=LLMCache(cache_path=fixture_dir / ".calibrate_cache.json"),
            fallback_backfiller=fb,
            cost_tracker=CostTracker(),
            model_tier=ModelTier.SONNET,
        )
        return scanner.scan_chapter(chapter_id, "calibration fixture content", context="")
