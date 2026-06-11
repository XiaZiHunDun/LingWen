"""Phase 9.34 F19: scanner calibration yaml + ripple-scan --calibrate tests."""
from pathlib import Path

import pytest

from infra.cli.commands.ripple_scan import RippleScanCommand
from infra.cli.options import RippleScanOptions
from infra.cli.parsers import create_parser
from infra.cross_volume.reference_graph import ReferenceNode
from infra.cross_volume.scanner_calibration import (
    compute_threshold_metrics,
    filter_nodes_by_threshold,
    load_gold_labels,
    load_scanner_calibration,
    recommend_threshold,
    sweep_thresholds,
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
    ]


class TestScannerCalibrationLoad:
    def test_load_default_yaml_matches_phase_912(self):
        cal = load_scanner_calibration()
        assert cal.node_write_threshold == 3
        assert cal.edge_infer_threshold == 3

    def test_load_custom_yaml(self, tmp_path):
        p = tmp_path / "cal.yaml"
        p.write_text(
            "node_write_threshold: 4\nedge_infer_threshold: 5\n",
            encoding="utf-8",
        )
        cal = load_scanner_calibration(p)
        assert cal.node_write_threshold == 4
        assert cal.edge_infer_threshold == 5

    def test_invalid_threshold_raises(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text("node_write_threshold: 9\n", encoding="utf-8")
        with pytest.raises(ValueError, match="node_write_threshold"):
            load_scanner_calibration(p)


class TestScannerCalibrationMetrics:
    def test_filter_by_threshold(self, sample_nodes):
        assert len(filter_nodes_by_threshold(sample_nodes, 3)) == 2
        assert len(filter_nodes_by_threshold(sample_nodes, 4)) == 1

    def test_compute_metrics_precision_recall(self, sample_nodes):
        gold = {"character:林轩", "foreshadow:九转玄功"}
        m = compute_threshold_metrics(sample_nodes, gold, threshold=3)
        assert m.true_positive == 2
        assert m.precision == 1.0
        assert m.recall == 1.0

    def test_threshold_4_drops_low_confidence_fp(self, sample_nodes):
        gold = {"character:林轩"}
        m3 = compute_threshold_metrics(sample_nodes, gold, threshold=3)
        m4 = compute_threshold_metrics(sample_nodes, gold, threshold=4)
        assert m3.precision < m4.precision

    def test_recommend_threshold_picks_best_f1(self, sample_nodes):
        gold = {"character:林轩", "foreshadow:九转玄功"}
        metrics = sweep_thresholds(sample_nodes, gold, min_threshold=1, max_threshold=5)
        rec = recommend_threshold(metrics)
        assert rec.threshold >= 3


class TestRippleScanCalibrateCLI:
    def test_parser_calibrate_flag(self):
        args = create_parser().parse_args(["ripple-scan", "--calibrate"])
        assert args.command == "ripple-scan"
        assert args.calibrate is True

    def test_calibrate_fixture_report(self, capsys):
        opts = RippleScanOptions(
            range=[],
            parallel=1,
            verbose=False,
            dry_run=False,
            calibrate=True,
            gold_path=Path("tests/cross_volume/fixtures/scanner_calibration_gold.yaml"),
            fixture_dir=Path("tests/cross_volume/fixtures/llm_responses"),
            calibration=None,
            chapter=1,
        )
        rc = RippleScanCommand().execute(opts)
        assert rc == 0
        out = capsys.readouterr().out
        assert "[CALIBRATE]" in out
        assert "recommended node_write_threshold=" in out
        assert "precision" in out

    def test_load_gold_labels_fixture(self):
        gold = load_gold_labels(Path("tests/cross_volume/fixtures/scanner_calibration_gold.yaml"))
        assert "character:林轩" in gold[1]
        assert len(gold[1]) >= 8
