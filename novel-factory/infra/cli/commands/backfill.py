"""backfill command - Phase 9.11 CVG (Cross-Volume Graph) 4-dim rule-based backfill.

Runs Backfiller against 359-chapter corpus to extract character / foreshadow /
setting / plot_point ReferenceNodes. --dry-run is default (per 主公 Q4).
"""
from pathlib import Path

from infra.cli.options import BackfillOptions

from .base import Command

DEFAULT_RULES_PATH = Path("infra/cross_volume/extraction_rules.yaml")


class BackfillCommand(Command):
    """CVG backfill command (Phase 9.11)"""

    name = "backfill"
    description = "跨卷涟漪 4 维规则回填 (Phase 9.11)"

    def execute(self, options: BackfillOptions) -> int:
        """
        Execute backfill command.

        Args:
            options: BackfillOptions

        Returns:
            Exit code (0 success, 1 error)
        """
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
