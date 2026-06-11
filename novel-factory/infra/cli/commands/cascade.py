"""cascade command - Phase 9.19. 1:1 with ripple_audit."""
from pathlib import Path

from infra.cli.options import CascadeOptions
from infra.cross_volume.storage import RippleStorage

from .base import Command

DEFAULT_RIPPLE_DB = Path(".state/ripple.db")


def _get_storage() -> RippleStorage:
    return RippleStorage(db_path=DEFAULT_RIPPLE_DB)


class CascadeCommand(Command):
    name = "cascade"
    description = "重新运行涟漪扩散 BFS (Phase 9.19)"

    def execute(self, options: CascadeOptions) -> int:
        import sys
        ripple_id = options.ripple_id
        max_depth = options.max_depth
        if not ripple_id:
            print("Error: ripple_id is required", file=sys.stderr)
            return 1
        storage = _get_storage()
        try:
            cascaded = storage.preview_cascade(ripple_id, max_depth=max_depth)
        except KeyError:
            print(f"Error: ripple {ripple_id} not found", file=sys.stderr)
            return 1
        print(f"Cascade for {ripple_id} (max_depth={max_depth}):")
        print(f"  depth_reached: {cascaded.depth_reached}")
        print(f"  nodes: {len(cascaded.cascade_nodes)}")
        print(f"  edges: {len(cascaded.cascade_edges)}")
        print(f"  actions: {len(cascaded.cascade_actions)}")
        print(f"  algorithm: {cascaded.bfs_algorithm_version}")
        return 0
