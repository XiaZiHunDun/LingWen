#!/usr/bin/env python3
"""
动作测试
"""
import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase

from hooks.actions.base import ActionResult, BaseAction
from hooks.actions.notify import NotifyAction
from hooks.actions.update_state import UpdateStateAction


class TestBaseAction(TestCase):
    """BaseAction抽象基类测试"""

    def test_cannot_instantiate_directly(self):
        """测试不能直接实例化BaseAction"""
        with self.assertRaises(TypeError):
            BaseAction()

    def test_must_implement_execute(self):
        """测试子类必须实现execute方法"""

        class IncompleteAction(BaseAction):
            @property
            def action_type(self) -> str:
                return "incomplete"

        # 实例化时就会报错（抽象方法未实现）
        with self.assertRaises(TypeError):
            IncompleteAction()

    def test_validate_params(self):
        """测试参数验证"""

        class TestAction(BaseAction):
            @property
            def action_type(self) -> str:
                return "test"

            def execute(self, params, context):
                return ActionResult(success=True)

        action = TestAction()
        valid, error = action.validate_params({"key": "value"}, ["key"])
        self.assertTrue(valid)

        valid, error = action.validate_params({}, ["key"])
        self.assertFalse(valid)
        self.assertIn("key", error)


class TestNotifyAction(TestCase):
    """NotifyAction测试"""

    def setUp(self):
        """测试前准备"""
        self.action = NotifyAction()

    def test_action_type(self):
        """测试动作类型"""
        self.assertEqual(self.action.action_type, "notify")

    def test_execute_with_valid_channel(self):
        """测试有效渠道的通知"""
        result = self.action.execute(
            params={"channel": "writer_channel", "message": "Test message"},
            context={"event_name": "TEST_EVENT"}
        )
        self.assertTrue(result.success)
        self.assertEqual(result.output["channel"], "writer_channel")

    def test_execute_with_template(self):
        """测试模板渲染"""
        result = self.action.execute(
            params={"channel": "writer_channel", "template": "review_complete"},
            context={"chapter_id": "ch001", "review_result": "PASS"}
        )
        self.assertTrue(result.success)

    def test_execute_with_invalid_channel(self):
        """测试无效渠道"""
        result = self.action.execute(
            params={"channel": "invalid_channel"},
            context={}
        )
        self.assertFalse(result.success)
        self.assertIn("Invalid channel", result.error)

    def test_execute_missing_channel(self):
        """测试缺少必需参数"""
        result = self.action.execute(params={}, context={})
        self.assertFalse(result.success)
        self.assertIn("缺少必需参数", result.error)


class TestUpdateStateAction(TestCase):
    """UpdateStateAction测试"""

    def setUp(self):
        """测试前准备"""
        self.action = UpdateStateAction()
        # 创建临时状态文件
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = Path(self.temp_dir) / "test_state.json"
        self.initial_state = {
            "current_step": "STEP_01",
            "project_status": {"phase": "PHASE_1"},
            "nested": {"field": "original"}
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.initial_state, f)

    def tearDown(self):
        """测试后清理"""
        if self.state_file.exists():
            os.unlink(self.state_file)
        os.rmdir(self.temp_dir)

    def test_action_type(self):
        """测试动作类型"""
        self.assertEqual(self.action.action_type, "update_state")

    def test_update_simple_field(self):
        """测试更新简单字段"""
        result = self.action.execute(
            params={
                "target": str(self.state_file),
                "field": "current_step",
                "value": "STEP_02"
            },
            context={}
        )
        self.assertTrue(result.success)

        # 验证更新
        with open(self.state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
        self.assertEqual(state["current_step"], "STEP_02")

    def test_update_nested_field(self):
        """测试更新嵌套字段"""
        result = self.action.execute(
            params={
                "target": str(self.state_file),
                "field": "project_status.phase",
                "value": "PHASE_2"
            },
            context={}
        )
        self.assertTrue(result.success)

        with open(self.state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
        self.assertEqual(state["project_status"]["phase"], "PHASE_2")

    def test_update_with_context_variable(self):
        """测试使用context变量"""
        result = self.action.execute(
            params={
                "target": str(self.state_file),
                "field": "current_step",
                "value": "$step"
            },
            context={"step": "STEP_05"}
        )
        self.assertTrue(result.success)

        with open(self.state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
        self.assertEqual(state["current_step"], "STEP_05")

    def test_update_missing_field_param(self):
        """测试缺少field参数"""
        result = self.action.execute(
            params={"value": "some_value"},
            context={}
        )
        self.assertFalse(result.success)
        self.assertIn("缺少必需参数", result.error)

    def test_update_missing_value_param(self):
        """测试缺少value参数"""
        result = self.action.execute(
            params={"field": "current_step"},
            context={}
        )
        self.assertFalse(result.success)


class TestRunCheckerAction(TestCase):
    """RunCheckerAction测试"""

    def test_action_type(self):
        """测试动作类型"""
        from hooks.actions.run_checker import RunCheckerAction
        action = RunCheckerAction()
        self.assertEqual(action.action_type, "run_checker")

    def test_missing_checker_param(self):
        """测试缺少checker参数"""
        from hooks.actions.run_checker import RunCheckerAction
        action = RunCheckerAction()

        result = action.execute(params={}, context={})
        self.assertFalse(result.success)
        self.assertIn("缺少必需参数", result.error)

    def test_unknown_checker(self):
        """测试未知检查器"""
        from hooks.actions.run_checker import RunCheckerAction
        action = RunCheckerAction()

        result = action.execute(
            params={"checker": "unknown_checker"},
            context={}
        )
        self.assertFalse(result.success)
        self.assertIn("Unknown checker", result.error)


if __name__ == "__main__":
    import unittest
    unittest.main()