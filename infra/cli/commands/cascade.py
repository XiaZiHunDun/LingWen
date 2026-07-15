"""cascade command - Phase 9.19 (run) + 9.20 (--persist) + 9.21 (cancel subcommand)."""
from pathlib import Path

from infra.cli.options import CascadeOptions
from infra.cli.path_utils import resolve_project_db_path
from infra.cross_volume.storage import RippleStorage

from .base import Command


def _get_storage() -> RippleStorage:
    # Phase 13.0 T4 M4: resolve via $LINGWEN_PROJECT_ROOT (preferred) or CWD fallback
    return RippleStorage(db_path=resolve_project_db_path())


class CascadeCommand(Command):
    name = "cascade"
    description = "Re-run cascade BFS / cancel persisted run (Phase 9.19+9.20+9.21)"

    def execute(self, options: CascadeOptions) -> int:
        if options.action == "cancel":
            return self._execute_cancel(options)
        if options.action == "migrate":
            return self._execute_migrate(options)
        if options.action == "purge":
            return self._execute_purge(options)
        return self._execute_run(options)

    def _execute_purge(self, options: CascadeOptions) -> int:
        """Phase 9.45 F34: retention cleanup for cascade_runs."""
        import sys

        from infra.cross_volume.cascade_retention import (
            parse_older_than,
            purge_cascade_runs_older_than,
        )

        try:
            delta = parse_older_than(options.older_than)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        storage = _get_storage()
        mode = "execute" if options.execute else "dry-run"
        result = purge_cascade_runs_older_than(
            storage, delta, execute=options.execute
        )
        print(
            f"[PURGE] mode={mode} older_than={options.older_than}"
            f" cutoff={result.cutoff_iso}"
        )
        print(f"  matched={result.matched} deleted={result.deleted}")
        if not options.execute and result.matched:
            print("  (re-run with --execute to delete)")
        return 0

    def _execute_migrate(self, options: CascadeOptions) -> int:
        """Phase 9.36 F21: v1 → v2_weighted cascade_runs migration (opt-in)."""
        from infra.cross_volume.cascade_migration import migrate_v1_cascade_runs

        storage = _get_storage()
        if storage._graph is None:
            print("Error: reference graph not loaded (cannot recompute BFS)", file=__import__("sys").stderr)
            return 1
        mode = "execute" if options.execute else "dry-run"
        print(f"[MIGRATE] mode={mode} ripple_filter={options.migrate_ripple_id or '*'}")
        stats = migrate_v1_cascade_runs(
            storage,
            execute=options.execute,
            ripple_id=options.migrate_ripple_id,
        )
        print(
            f"  scanned={stats.scanned} migrated={stats.migrated}"
            f" skipped={stats.skipped} failed={stats.failed}"
        )
        for err in stats.errors:
            print(f"  error: {err}")
        if stats.failed and not options.execute:
            pass
        return 1 if stats.failed else 0

    def _execute_run(self, options: CascadeOptions) -> int:
        """Phase 9.19+9.20: re-run cascade BFS (原 body, 0 改)."""
        import sys
        ripple_id = options.ripple_id
        max_depth = options.max_depth
        max_nodes_cap = options.max_nodes_cap
        if not ripple_id:
            print("Error: ripple_id is required", file=sys.stderr)
            return 1
        if max_nodes_cap < 1 or max_nodes_cap > 1000:
            print("Error: max_nodes_cap must be 1..1000", file=sys.stderr)
            return 1
        storage = _get_storage()
        try:
            cascaded = storage.preview_cascade(
                ripple_id, max_depth=max_depth, max_nodes_cap=max_nodes_cap,
            )
        except KeyError:
            print(f"Error: ripple {ripple_id} not found", file=sys.stderr)
            return 1
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        if options.persist:  # Phase 9.20 NEW
            run_id = storage.record_cascade_run(
                options.ripple_id, cascaded, max_depth=options.max_depth,
            )
            print(f"persisted as cascade run id={run_id}")
        print(f"Cascade for {ripple_id} (max_depth={max_depth}, max_nodes_cap={max_nodes_cap}):")
        print(f"  depth_reached: {cascaded.depth_reached}")
        print(f"  nodes: {len(cascaded.cascade_nodes)}")
        print(f"  edges: {len(cascaded.cascade_edges)}")
        print(f"  actions: {len(cascaded.cascade_actions)}")
        print(f"  algorithm: {cascaded.bfs_algorithm_version}")
        return 0

    def _execute_cancel(self, options: CascadeOptions) -> int:
        """Phase 9.21: cancel persisted cascade run by id."""
        import sys
        storage = _get_storage()
        try:
            flipped = storage.cancel_cascade_run(options.run_id, reason=options.reason)
        except KeyError:
            print(f"Error: cascade run {options.run_id} not found", file=sys.stderr)
            return 1
        if flipped:
            print(f"cancelled cascade run id={options.run_id}")
        else:
            print(f"cascade run id={options.run_id} already cancelled (no-op)")
        return 0
