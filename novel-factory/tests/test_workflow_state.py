#!/usr/bin/env python3
"""
workflow_state.json 处理测试
"""
import json
import pytest
from pathlib import Path


class TestWorkflowState:
    """workflow_state 处理测试"""

    def test_workflow_state_exists(self, project_root):
        """测试 workflow_state.json 存在"""
        state_file = project_root / "workflow_state.json"
        assert state_file.exists(), "workflow_state.json 应该存在"

    def test_workflow_state_valid_json(self, project_root):
        """测试 workflow_state.json 是有效 JSON"""
        state_file = project_root / "workflow_state.json"
        with open(state_file, 'r') as f:
            state = json.load(f)
        assert isinstance(state, dict), "workflow_state 应该是 dict"

    def test_workflow_state_has_required_keys(self, project_root):
        """测试 workflow_state 包含必需字段"""
        state_file = project_root / "workflow_state.json"
        with open(state_file, 'r') as f:
            state = json.load(f)

        required_keys = ["version", "current_phase", "current_step", "phases"]
        for key in required_keys:
            assert key in state, f"workflow_state 应该有 {key} 字段"

    def test_current_phase_valid(self, project_root):
        """测试当前阶段有效"""
        state_file = project_root / "workflow_state.json"
        with open(state_file, 'r') as f:
            state = json.load(f)

        valid_phases = ["PHASE_1_LAUNCH", "PHASE_2_OUTLINE", "PHASE_3_VOLUME",
                       "PHASE_4_STAGE", "PHASE_5_BODY", "PHASE_6_SUMMARY", "PHASE_7_CLOSE"]

        current = state.get("current_phase", "")
        assert current in valid_phases, f"current_phase 应该合法，当前值: {current}"