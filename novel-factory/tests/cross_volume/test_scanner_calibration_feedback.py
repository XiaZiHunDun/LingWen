"""Phase 9.43 F32: scanner calibration feedback loop tests."""
from pathlib import Path

import pytest

from infra.cli.commands.ripple_scan import RippleScanCommand
from infra.cli.options import RippleScanOptions
from infra.cli.parsers import create_parser
from infra.cross_volume.reference_graph import ReferenceNode
from infra.cross_volume.scanner_calibration import (
    ScannerCalibration,
    build_calibration_feedback,
    build_dimension_reports,
    format_calibration_yaml_example,
    gold_keys_for_dimension,
    threshold_delta,
)


@pytest.fixture
def sample_nodes():
    return [
        ReferenceNode(
            dimension="character", volume=1, chapter=1, title="林轩",
            description="", confidence=4,
        ),
        ReferenceNode(
            dimension="character", volume=1, chapter=1, title="路人甲",
            description="", confidence=2,
        ),
        ReferenceNode(
            dimension="foreshadow", volume=1, chapter=1, title="九转玄功",
            description="", confidence=3,
        ),
        ReferenceNode(
            dimension="setting", volume=1, chapter=1, title="青云宗",
            description="", confidence=5,
        ),
    ]


class TestCalibrationFeedback:
    def test_gold_keys_for_dimension(self):
        gold = {"character:林轩", "foreshadow:玉佩", "setting:青云宗"}
        assert gold_keys_for_dimension(gold, "character") == {"character:林轩"}
        assert gold_keys_for_dimension(gold, "plot_point") == set()

    def test_build_dimension_reports_skips_empty_gold(self, sample_nodes):
        gold = {"character:林轩", "foreshadow:九转玄功"}
        cal = ScannerCalibration()
        reports = build_dimension_reports(sample_nodes, gold, cal)
        dims = {r.dimension for r in reports}
        assert dims == {"character", "foreshadow"}
        assert all(r.gold_count > 0 for r in reports)

    def test_threshold_delta_sign(self):
        cal = ScannerCalibration(node_write_threshold=3)
        gold = {"character:林轩", "foreshadow:九转玄功"}
        feedback = build_calibration_feedback([], gold, cal)
        assert isinstance(feedback.global_delta, int)

    def test_format_yaml_example_human_in_loop(self, sample_nodes):
        gold = {"character:林轩", "foreshadow:九转玄功", "setting:青云宗"}
        cal = ScannerCalibration(node_write_threshold=3)
        feedback = build_calibration_feedback(sample_nodes, gold, cal)
        yaml_text = format_calibration_yaml_example(feedback)
        assert "0 auto-apply" in yaml_text
        assert "node_write_threshold:" in yaml_text
        assert f"was {cal.node_write_threshold}" in yaml_text

    def test_calibrate_cli_includes_per_dimension(self, capsys):
        opts = RippleScanOptions(
            range=[],
            parallel=1,
            verbose=False,
            dry_run=False,
            calibrate=True,
            yaml_example=True,
            gold_path=Path("tests/cross_volume/fixtures/scanner_calibration_gold.yaml"),
            fixture_dir=Path("tests/cross_volume/fixtures/llm_responses"),
            calibration=None,
            chapter=1,
        )
        rc = RippleScanCommand().execute(opts)
        assert rc == 0
        out = capsys.readouterr().out
        assert "[per-dimension]" in out
        assert "delta=" in out
        assert "Suggested edit" in out

    def test_parser_yaml_example_flag(self):
        args = create_parser().parse_args(["ripple-scan", "--calibrate", "--yaml-example"])
        assert args.yaml_example is True
