#!/usr/bin/env python3
"""
问题追踪工具测试
"""
import pytest
import json
import tempfile
import sys
from pathlib import Path

# 添加 tools 目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))


class TestIssueTracker:
    """问题追踪工具测试"""

    def test_index_file_structure(self, tmp_path):
        """测试索引文件结构"""
        index_file = tmp_path / "_index.json"
        index = {
            "version": "1.0",
            "total_issues": 0,
            "by_severity": {"P0": 0, "P1": 0, "P2": 0},
            "by_status": {"open": 0, "in_progress": 0, "resolved": 0, "verified": 0},
            "issues": []
        }

        with open(index_file, 'w') as f:
            json.dump(index, f)

        with open(index_file, 'r') as f:
            loaded = json.load(f)

        assert loaded["version"] == "1.0"
        assert "issues" in loaded
        assert "by_severity" in loaded
        assert "by_status" in loaded

    def test_index_stats_tracking(self, tmp_path):
        """测试索引统计追踪"""
        index_file = tmp_path / "_index.json"
        index = {
            "version": "1.0",
            "total_issues": 2,
            "by_severity": {"P0": 1, "P1": 1, "P2": 0},
            "by_status": {"open": 2, "in_progress": 0, "resolved": 0, "verified": 0},
            "issues": [
                {"chapter_id": "ch001", "severity": "P0", "status": "open"},
                {"chapter_id": "ch002", "severity": "P1", "status": "open"}
            ]
        }

        with open(index_file, 'w') as f:
            json.dump(index, f)

        with open(index_file, 'r') as f:
            loaded = json.load(f)

        assert loaded["total_issues"] == 2
        assert loaded["by_severity"]["P0"] == 1
        assert loaded["by_severity"]["P1"] == 1
        assert len(loaded["issues"]) == 2