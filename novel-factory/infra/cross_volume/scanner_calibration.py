"""Phase 9.34 F19: externalized LLM scanner confidence thresholds + calibration metrics."""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

from infra.cross_volume.reference_graph import ReferenceNode

DEFAULT_CALIBRATION_PATH = Path(__file__).parent / "scanner_calibration.yaml"


@dataclass(frozen=True)
class ScannerCalibration:
    node_write_threshold: int = 3
    edge_infer_threshold: int = 3
    calibrate_threshold_min: int = 1
    calibrate_threshold_max: int = 5

    def validate(self) -> None:
        for name in (
            "node_write_threshold",
            "edge_infer_threshold",
            "calibrate_threshold_min",
            "calibrate_threshold_max",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or value < 1 or value > 5:
                raise ValueError(f"scanner calibration {name} must be int 1..5, got {value!r}")
        if self.calibrate_threshold_min > self.calibrate_threshold_max:
            raise ValueError("calibrate_threshold_min must be <= calibrate_threshold_max")


@dataclass(frozen=True)
class ThresholdMetrics:
    threshold: int
    precision: float
    recall: float
    f1: float
    predicted: int
    gold: int
    true_positive: int


def load_scanner_calibration(path: Path | str | None = None) -> ScannerCalibration:
    """Load thresholds from YAML; missing file → built-in defaults (3/3)."""
    cal_path = Path(path) if path is not None else DEFAULT_CALIBRATION_PATH
    if not cal_path.is_file():
        return ScannerCalibration()
    raw = yaml.safe_load(cal_path.read_text(encoding="utf-8")) or {}
    cal = ScannerCalibration(
        node_write_threshold=int(raw.get("node_write_threshold", 3)),
        edge_infer_threshold=int(raw.get("edge_infer_threshold", 3)),
        calibrate_threshold_min=int(raw.get("calibrate_threshold_min", 1)),
        calibrate_threshold_max=int(raw.get("calibrate_threshold_max", 5)),
    )
    cal.validate()
    return cal


def node_key(node: ReferenceNode) -> str:
    return f"{node.dimension}:{node.title}"


def filter_nodes_by_threshold(
    nodes: Iterable[ReferenceNode],
    threshold: int,
) -> list[ReferenceNode]:
    return [n for n in nodes if n.confidence >= threshold]


def compute_threshold_metrics(
    nodes: Iterable[ReferenceNode],
    gold_keys: set[str],
    threshold: int,
) -> ThresholdMetrics:
    predicted = {node_key(n) for n in filter_nodes_by_threshold(nodes, threshold)}
    gold = set(gold_keys)
    tp = len(predicted & gold)
    precision = tp / len(predicted) if predicted else 0.0
    recall = tp / len(gold) if gold else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return ThresholdMetrics(
        threshold=threshold,
        precision=precision,
        recall=recall,
        f1=f1,
        predicted=len(predicted),
        gold=len(gold),
        true_positive=tp,
    )


def sweep_thresholds(
    nodes: Iterable[ReferenceNode],
    gold_keys: set[str],
    *,
    min_threshold: int = 1,
    max_threshold: int = 5,
) -> list[ThresholdMetrics]:
    return [
        compute_threshold_metrics(nodes, gold_keys, t)
        for t in range(min_threshold, max_threshold + 1)
    ]


def recommend_threshold(metrics: list[ThresholdMetrics]) -> ThresholdMetrics:
    """Pick highest F1; tie-break → higher threshold (fewer false positives)."""
    if not metrics:
        raise ValueError("metrics must not be empty")
    return max(metrics, key=lambda m: (m.f1, m.threshold))


def format_calibration_report(
    metrics: list[ThresholdMetrics],
    *,
    recommended: ThresholdMetrics,
    current: ScannerCalibration,
) -> str:
    lines = [
        "[CALIBRATE] threshold sweep (fixture gold labels)",
        f"  current node_write_threshold={current.node_write_threshold} "
        f"edge_infer_threshold={current.edge_infer_threshold}",
        "",
        "  T  precision  recall     f1  pred  gold   tp",
    ]
    for m in metrics:
        star = " *" if m.threshold == recommended.threshold else ""
        lines.append(
            f"  {m.threshold}  {m.precision:8.3f}  {m.recall:6.3f}  "
            f"{m.f1:6.3f}  {m.predicted:4d}  {m.gold:4d}  {m.true_positive:3d}{star}"
        )
    lines.extend(
        [
            "",
            f"  recommended node_write_threshold={recommended.threshold} "
            f"(F1={recommended.f1:.3f}, precision={recommended.precision:.3f}, "
            f"recall={recommended.recall:.3f})",
            "  (update infra/cross_volume/scanner_calibration.yaml to apply)",
        ]
    )
    return "\n".join(lines)


def load_gold_labels(path: Path) -> dict[int, set[str]]:
    """Load chapter_id → gold node keys from YAML."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    chapters = raw.get("chapters") or {}
    out: dict[int, set[str]] = {}
    for ch_id, body in chapters.items():
        keys = body.get("gold_nodes") if isinstance(body, dict) else None
        if not keys:
            continue
        out[int(ch_id)] = {str(k) for k in keys}
    return out
