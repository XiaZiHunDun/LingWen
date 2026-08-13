"""ripple-scan subparser (Phase 9.34 F19 LLM scanner calibration CLI)."""
import argparse
from pathlib import Path


def add_ripple_scan_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "ripple-scan",
        help="LLM scanner 校准 / 阈值报告 (Phase 9.34)",
        description="Calibrate LLM scanner confidence thresholds against fixture gold labels.",
    )
    parser.add_argument(
        "--calibrate",
        action="store_true",
        help="Run threshold sweep + precision/recall report (default fixture, 0 真 LLM)",
    )
    parser.add_argument(
        "--yaml-example",
        action="store_true",
        help="After --calibrate report, print suggested scanner_calibration.yaml snippet (0 auto-apply)",
    )
    parser.add_argument(
        "--gold-path",
        type=Path,
        default=None,
        help="Gold labels YAML (default: tests/cross_volume/fixtures/scanner_calibration_gold.yaml)",
    )
    parser.add_argument(
        "--fixture-dir",
        type=Path,
        default=None,
        help="LLM response fixtures dir (default: tests/cross_volume/fixtures/llm_responses)",
    )
    parser.add_argument(
        "--calibration",
        type=Path,
        default=None,
        help="scanner_calibration.yaml path (default: infra/cross_volume/scanner_calibration.yaml)",
    )
    parser.add_argument(
        "--chapter",
        type=int,
        default=1,
        help="Chapter id for fixture calibration (default: 1)",
    )
    return parser
