"""backfill subparser (Phase 9.11 CVG backfill CLI integration)."""
import argparse


def add_backfill_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """注册 'backfill' 子命令的参数解析器。

    用法:
        lingwen.py backfill --vol 1
        lingwen.py backfill --vol 3 --execute
        lingwen.py backfill --rules infra/cross_volume/extraction_rules.yaml
    """
    parser = subparsers.add_parser(
        "backfill",
        help="跨卷涟漪 4 维规则回填 (Phase 9.11)",
        description="Backfill CVG 4-dim ReferenceNodes (character / foreshadow / setting / plot_point) from chapter corpus.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="[默认] 0 写库, 仅 print 统计 (per 主公 Q4)",
    )
    parser.add_argument(
        "--execute",
        dest="dry_run",
        action="store_false",
        help="真正写入 storage (调 Backfiller.run dry_run=False)",
    )
    parser.add_argument(
        "--vol",
        type=int,
        default=None,
        choices=[1, 2, 3],
        help="Volume filter: 1/2/3 抽样式, 缺省全 359 章",
    )
    parser.add_argument(
        "--rules",
        type=str,
        default=None,
        help="Extraction rules YAML path (default: infra/cross_volume/extraction_rules.yaml)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    return parser
