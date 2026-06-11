"""cascade subparser (Phase 9.19 + 9.20 + 9.21).

Phase 9.21: 'cascade' 变 subparser group 容纳 'run' + 'cancel' 两 action.
Backward compat 注意: 'lingwen.py cascade rip-1' 旧用法变 'cascade run rip-1'.
"""
import argparse


def add_cascade_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """注册 'cascade' 子命令的参数解析器 (Phase 9.19+9.20+9.21).

    用法:
        lingwen.py cascade run rip-1
        lingwen.py cascade run rip-1 --max-depth 5 --persist
        lingwen.py cascade cancel 42
        lingwen.py cascade cancel 42 --reason "误触"
    """
    cascade_parent = subparsers.add_parser(
        "cascade",
        help="Cascade run (Phase 9.19+9.20) + cancel (Phase 9.21)",
        description="Re-run cascade BFS or cancel a persisted run.",
    )
    cascade_subs = cascade_parent.add_subparsers(dest="cascade_action")

    run_p = cascade_subs.add_parser(
        "run",
        help="Re-run cascade BFS (Phase 9.19) + optional persist (Phase 9.20)",
        description="Re-run cascade BFS with caller-specified max_depth.",
    )
    run_p.add_argument("ripple_id", type=str, help="Ripple id to trace (e.g. 'rip-1')")
    run_p.add_argument(
        "--max-depth", type=int, default=3, choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        help="Max BFS depth 1..10 (default 3)",
    )
    run_p.add_argument(
        "--max-nodes-cap", type=int, default=100,
        help="Max BFS nodes collected 1..1000 (default 100, Phase 9.32 F16)",
    )
    run_p.add_argument(
        "--persist", action="store_true", default=False,
        help="Persist cascade run to cascade_runs table (off by default)",
    )

    cancel_p = cascade_subs.add_parser(
        "cancel",
        help="Cancel a persisted cascade run by id",
    )
    cancel_p.add_argument("run_id", type=int, help="Cascade run id to cancel")
    cancel_p.add_argument(
        "--reason", type=str, default="",
        help="Optional cancel reason (logged + WS payload, not persisted)",
    )
    return cascade_parent
