"""Phase 9.34 F19 + Phase 9.43 F32: externalized LLM scanner thresholds + calibration feedback."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal

import yaml

from infra.cross_volume.reference_graph import ReferenceNode

DEFAULT_CALIBRATION_PATH = Path(__file__).parent / "scanner_calibration.yaml"

DimensionT = Literal["character", "foreshadow", "setting", "plot_point"]
CALIBRATION_DIMENSIONS: tuple[DimensionT, ...] = (
    "character",
    "foreshadow",
    "setting",
    "plot_point",
)


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


@dataclass(frozen=True)
class DimensionThresholdReport:
    """Phase 9.43 F32: per-dimension threshold sweep summary."""

    dimension: DimensionT
    gold_count: int
    node_count: int
    metrics: tuple[ThresholdMetrics, ...]
    recommended: ThresholdMetrics
    delta: int  # recommended.threshold - current node_write_threshold


@dataclass(frozen=True)
class CalibrationFeedback:
    """Structured output for ripple-scan --calibrate (F32 feedback loop)."""

    global_metrics: tuple[ThresholdMetrics, ...]
    global_recommended: ThresholdMetrics
    global_delta: int
    dimension_reports: tuple[DimensionThresholdReport, ...]
    current: ScannerCalibration


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


def threshold_delta(current: int, recommended: ThresholdMetrics) -> int:
    return recommended.threshold - current


def gold_keys_for_dimension(gold_keys: set[str], dimension: str) -> set[str]:
    prefix = f"{dimension}:"
    return {k for k in gold_keys if k.startswith(prefix)}


def nodes_for_dimension(nodes: Iterable[ReferenceNode], dimension: str) -> list[ReferenceNode]:
    return [n for n in nodes if n.dimension == dimension]


def build_dimension_reports(
    nodes: Iterable[ReferenceNode],
    gold_keys: set[str],
    current: ScannerCalibration,
    *,
    min_threshold: int | None = None,
    max_threshold: int | None = None,
) -> list[DimensionThresholdReport]:
    """Per-dimension threshold sweep; skip dims with zero gold labels."""
    lo = min_threshold if min_threshold is not None else current.calibrate_threshold_min
    hi = max_threshold if max_threshold is not None else current.calibrate_threshold_max
    reports: list[DimensionThresholdReport] = []
    for dim in CALIBRATION_DIMENSIONS:
        dim_gold = gold_keys_for_dimension(gold_keys, dim)
        if not dim_gold:
            continue
        dim_nodes = nodes_for_dimension(nodes, dim)
        metrics = sweep_thresholds(dim_nodes, dim_gold, min_threshold=lo, max_threshold=hi)
        recommended = recommend_threshold(metrics)
        reports.append(
            DimensionThresholdReport(
                dimension=dim,
                gold_count=len(dim_gold),
                node_count=len(dim_nodes),
                metrics=tuple(metrics),
                recommended=recommended,
                delta=threshold_delta(current.node_write_threshold, recommended),
            )
        )
    return reports


def build_calibration_feedback(
    nodes: Iterable[ReferenceNode],
    gold_keys: set[str],
    current: ScannerCalibration,
) -> CalibrationFeedback:
    global_metrics = sweep_thresholds(
        nodes,
        gold_keys,
        min_threshold=current.calibrate_threshold_min,
        max_threshold=current.calibrate_threshold_max,
    )
    global_recommended = recommend_threshold(global_metrics)
    return CalibrationFeedback(
        global_metrics=tuple(global_metrics),
        global_recommended=global_recommended,
        global_delta=threshold_delta(current.node_write_threshold, global_recommended),
        dimension_reports=tuple(
            build_dimension_reports(nodes, gold_keys, current)
        ),
        current=current,
    )


def format_per_dimension_section(reports: Iterable[DimensionThresholdReport]) -> str:
    lines = [
        "",
        "  [per-dimension] precision / recall @ recommended threshold",
        "  dimension      gold  nodes  T*  precision  recall     f1  delta",
    ]
    for report in reports:
        m = report.recommended
        delta_s = f"{report.delta:+d}" if report.delta else "0"
        lines.append(
            f"  {report.dimension:13s}  {report.gold_count:4d}  {report.node_count:5d}  "
            f"{m.threshold:2d}  {m.precision:8.3f}  {m.recall:6.3f}  "
            f"{m.f1:6.3f}  {delta_s}"
        )
    return "\n".join(lines)


def format_calibration_yaml_example(feedback: CalibrationFeedback) -> str:
    """Human-in-the-loop YAML snippet (0 auto-apply)."""
    rec = feedback.global_recommended
    cur = feedback.current
    delta = feedback.global_delta
    delta_note = "unchanged" if delta == 0 else f"delta {delta:+d} (F1={rec.f1:.3f})"
    weak_dims = [
        r.dimension
        for r in feedback.dimension_reports
        if r.recommended.recall < 0.999 and r.delta > 0
    ]
    weak_note = (
        f"review dims: {', '.join(weak_dims)}"
        if weak_dims
        else "all dims OK at recommended threshold"
    )
    return "\n".join(
        [
            "# Suggested edit — copy into scanner_calibration.yaml manually (F32, 0 auto-apply)",
            f"node_write_threshold: {rec.threshold}  # was {cur.node_write_threshold}, {delta_note}",
            f"edge_infer_threshold: {cur.edge_infer_threshold}  # unchanged; {weak_note}",
            "calibrate_threshold_min: 1",
            "calibrate_threshold_max: 5",
        ]
    )


def format_calibration_report(
    feedback: CalibrationFeedback,
) -> str:
    metrics = list(feedback.global_metrics)
    recommended = feedback.global_recommended
    current = feedback.current
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
    delta_s = f"{feedback.global_delta:+d}" if feedback.global_delta else "0"
    lines.extend(
        [
            "",
            f"  recommended node_write_threshold={recommended.threshold} "
            f"(F1={recommended.f1:.3f}, precision={recommended.precision:.3f}, "
            f"recall={recommended.recall:.3f}, delta={delta_s})",
            "  (update infra/cross_volume/scanner_calibration.yaml to apply)",
        ]
    )
    if feedback.dimension_reports:
        lines.append(format_per_dimension_section(feedback.dimension_reports))
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
