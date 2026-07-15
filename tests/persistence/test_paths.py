"""Phase 15.0 T2.4: paths.py 3 tests.

覆盖:
1. 全部是 Path 对象
2. 相对项目根
3. 5 个值互不相同 (relationship/budget 例外共用)
"""
from __future__ import annotations

from pathlib import Path

from infra.persistence.paths import (
    COST_TRACKER_DB,
    CROSS_VOLUME_DB,
    PROJECT_ROOT,
    READING_POWER_DB,
    RELATIONSHIP_DB,
    RIPPLE_DB,
    WORKFLOW_DB,
)


class TestPaths:
    def test_paths_are_path_objects(self):
        assert isinstance(PROJECT_ROOT, Path)
        assert isinstance(RIPPLE_DB, Path)
        assert isinstance(COST_TRACKER_DB, Path)
        assert isinstance(WORKFLOW_DB, Path)
        assert isinstance(READING_POWER_DB, Path)
        assert isinstance(RELATIONSHIP_DB, Path)
        assert isinstance(CROSS_VOLUME_DB, Path)

    def test_paths_relative_to_repo_root(self):
        # 5 个 db 都在 PROJECT_ROOT/.state/ 下
        for p in [RIPPLE_DB, COST_TRACKER_DB, WORKFLOW_DB, READING_POWER_DB]:
            assert p.parent.parent == PROJECT_ROOT, f"{p} 不在 {PROJECT_ROOT} 下"
        # relationship 在 PROJECT_ROOT/.state/social_engine/ 下
        assert RELATIONSHIP_DB.parent.parent.parent == PROJECT_ROOT

    def test_paths_distinct(self):
        """5 个 db path 互不相同 (cost/budget 共用, ripple/cv 区分)."""
        # 主 5 个必须互不相同
        distinct_paths = {
            str(RIPPLE_DB),
            str(COST_TRACKER_DB),
            str(WORKFLOW_DB),
            str(READING_POWER_DB),
            str(RELATIONSHIP_DB),
        }
        assert len(distinct_paths) == 5
        # CROSS_VOLUME_DB 是 ripple 兼容别名 (暂独立, 历史可能为同一 path)
        # 不强制相等, 仅记录
        assert isinstance(CROSS_VOLUME_DB, Path)

    def test_db_path_suffix(self):
        """所有 db 路径以 .db 结尾."""
        for p in [RIPPLE_DB, COST_TRACKER_DB, WORKFLOW_DB, READING_POWER_DB, RELATIONSHIP_DB]:
            assert p.suffix == ".db", f"{p} 不是 .db 文件"
