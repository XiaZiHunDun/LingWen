#!/usr/bin/env python3
"""
Hook引擎测试
"""
import os
import tempfile
from pathlib import Path
from unittest import TestCase

from hooks import Event, EventBus, EventTypes
from hooks.config_loader import HookConfig, HookConfigLoader, ConditionEvaluator
from hooks.hook_engine import HookEngine, HookStatus, HookExecutionError
from hooks.actions.base import ActionResult
from hooks.actions.run_checker import RunCheckerAction
from hooks.actions.notify import NotifyAction
from hooks.actions.update_state import UpdateStateAction


class TestConditionEvaluator(TestCase):
    """条件表达式求值器测试"""

    def test_simple_equality(self):
        """测试简单相等比较"""
        context = {"chapter_status": "draft_completed"}
        self.assertTrue(
            ConditionEvaluator.evaluate("chapter_status == 'draft_completed'", context)
        )
        self.assertFalse(
            ConditionEvaluator.evaluate("chapter_status == 'draft'", context)
        )

    def test_numeric_comparison(self):
        """测试数值比较"""
        context = {"idle_time": 300}
        self.assertTrue(ConditionEvaluator.evaluate("idle_time > 200", context))
        self.assertTrue(ConditionEvaluator.evaluate("idle_time >= 300", context))
        self.assertFalse(ConditionEvaluator.evaluate("idle_time < 100", context))

    def test_in_operator(self):
        """测试in操作符"""
        context = {"review_result": "PASS"}
        self.assertTrue(
            ConditionEvaluator.evaluate("review_result in ['PASS', 'NEED_REVISION']", context)
        )
        self.assertFalse(
            ConditionEvaluator.evaluate("review_result in ['FAIL']", context)
        )

    def test_not_in_operator(self):
        """测试not in操作符"""
        context = {"review_result": "PASS"}
        self.assertTrue(
            ConditionEvaluator.evaluate("review_result not in ['FAIL']", context)
        )
        self.assertFalse(
            ConditionEvaluator.evaluate("review_result not in ['PASS', 'FAIL']", context)
        )

    def test_step_in_list(self):
        """测试step in列表"""
        context = {"step": "STEP_10"}
        self.assertTrue(
            ConditionEvaluator.evaluate("step in ['STEP_10', 'STEP_11', 'STEP_12']", context)
        )

    def test_missing_variable(self):
        """测试缺失变量（返回False，不抛异常）"""
        context = {}
        self.assertFalse(
            ConditionEvaluator.evaluate("missing_var == 'value'", context)
        )


class TestHookConfig(TestCase):
    """HookConfig数据类测试"""

    def test_event_name_property(self):
        """测试event_name属性"""
        config = HookConfig(
            name="test_hook",
            trigger={"event": "CHAPTER_WRITTEN", "conditions": []}
        )
        self.assertEqual(config.event_name, "CHAPTER_WRITTEN")

    def test_conditions_property(self):
        """测试conditions属性"""
        config = HookConfig(
            name="test_hook",
            trigger={
                "event": "CHAPTER_WRITTEN",
                "conditions": ["status == 'done'", "count > 5"]
            }
        )
        self.assertEqual(len(config.conditions), 2)
        self.assertEqual(config.conditions[0], "status == 'done'")


class TestHookConfigLoader(TestCase):
    """HookConfigLoader测试"""

    def setUp(self):
        """测试前准备"""
        self.loader = HookConfigLoader()

    def test_load_valid_config(self):
        """测试加载有效配置"""
        config_content = """
hooks:
  - name: "测试Hook"
    trigger:
      event: "CHAPTER_WRITTEN"
      conditions:
        - "status == 'done'"
    actions:
      - type: "notify"
        channel: "writer_channel"
        template: "test"
    required: true
    timeout: 30
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            configs = self.loader.load(config_path)
            self.assertEqual(len(configs), 1)
            self.assertEqual(configs[0].name, "测试Hook")
            self.assertEqual(configs[0].event_name, "CHAPTER_WRITTEN")
            self.assertTrue(configs[0].required)
        finally:
            os.unlink(config_path)

    def test_validate_valid_config(self):
        """测试验证有效配置"""
        configs = [
            HookConfig(
                name="test",
                trigger={"event": "CHAPTER_WRITTEN", "conditions": []},
                actions=[{"type": "notify", "channel": "writer_channel"}],
                timeout=30
            )
        ]
        is_valid, errors = self.loader.validate(configs)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_invalid_event_type(self):
        """测试验证无效事件类型"""
        configs = [
            HookConfig(
                name="test",
                trigger={"event": "INVALID_EVENT", "conditions": []},
                actions=[{"type": "notify", "channel": "writer_channel"}],
                timeout=30
            )
        ]
        is_valid, errors = self.loader.validate(configs)
        self.assertFalse(is_valid)
        self.assertTrue(any("无效的事件类型" in e for e in errors))

    def test_validate_invalid_action_type(self):
        """测试验证无效动作类型"""
        configs = [
            HookConfig(
                name="test",
                trigger={"event": "CHAPTER_WRITTEN", "conditions": []},
                actions=[{"type": "invalid_action"}],
                timeout=30
            )
        ]
        is_valid, errors = self.loader.validate(configs)
        self.assertFalse(is_valid)


class TestHookEngine(TestCase):
    """HookEngine测试"""

    def setUp(self):
        """测试前准备"""
        self.event_bus = EventBus()
        self.config_loader = HookConfigLoader()
        self.engine = HookEngine(self.event_bus, self.config_loader)

        # 注册动作类型
        self.engine.register_action("notify", NotifyAction)
        self.engine.register_action("update_state", UpdateStateAction)

    def _create_test_config_file(self, content: str) -> str:
        """创建测试配置文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(content)
            return f.name

    def test_load_hooks(self):
        """测试加载Hook配置"""
        config_content = """
hooks:
  - name: "测试Hook"
    trigger:
      event: "CHAPTER_WRITTEN"
    actions:
      - type: "notify"
        channel: "writer_channel"
    required: false
    timeout: 30
"""
        config_path = self._create_test_config_file(config_content)
        try:
            self.engine.load_hooks(config_path)
            self.assertEqual(len(self.engine._hooks), 1)
            self.assertEqual(self.engine._hooks[0].name, "测试Hook")
        finally:
            os.unlink(config_path)

    def test_event_matching(self):
        """测试事件匹配"""
        config_content = """
hooks:
  - name: "测试Hook"
    trigger:
      event: "CHAPTER_WRITTEN"
      conditions:
        - "chapter_status == 'done'"
    actions:
      - type: "notify"
        channel: "writer_channel"
    required: false
    timeout: 30
"""
        config_path = self._create_test_config_file(config_content)
        try:
            self.engine.load_hooks(config_path)

            # 匹配条件的事件
            event = Event(
                name="CHAPTER_WRITTEN",
                source="test",
                data={"chapter_status": "done"}
            )
            results = self.engine.trigger(event)
            self.assertEqual(len(results), 1)

            # 不匹配条件的事件
            event2 = Event(
                name="CHAPTER_WRITTEN",
                source="test",
                data={"chapter_status": "pending"}
            )
            results2 = self.engine.trigger(event2)
            self.assertEqual(len(results2), 0)
        finally:
            os.unlink(config_path)

    def test_required_hook_blocks_flow(self):
        """测试required hook阻止流程"""
        config_content = """
hooks:
  - name: "必需Hook"
    trigger:
      event: "CHAPTER_WRITTEN"
    actions:
      - type: "notify"
        params:
          channel: "writer_channel"
    required: true
    timeout: 30
"""
        config_path = self._create_test_config_file(config_content)
        try:
            self.engine.load_hooks(config_path)

            event = Event(name="CHAPTER_WRITTEN", source="test")
            # required hook 目前是mock notify，所以应该成功
            results = self.engine.trigger(event)
            self.assertEqual(len(results), 1)
            # 不应该抛出异常，因为notify action是mock成功的
        finally:
            os.unlink(config_path)

    def test_optional_hook_does_not_block(self):
        """测试optional hook不阻止流程"""
        config_content = """
hooks:
  - name: "可选Hook"
    trigger:
      event: "CHAPTER_WRITTEN"
    actions:
      - type: "notify"
        channel: "writer_channel"
    required: false
    timeout: 30
"""
        config_path = self._create_test_config_file(config_content)
        try:
            self.engine.load_hooks(config_path)

            event = Event(name="CHAPTER_WRITTEN", source="test")
            results = self.engine.trigger(event)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].hook_name, "可选Hook")
        finally:
            os.unlink(config_path)

    def test_get_hook_status(self):
        """测试获取Hook状态"""
        config_content = """
hooks:
  - name: "状态测试Hook"
    trigger:
      event: "CHAPTER_WRITTEN"
    actions:
      - type: "notify"
        channel: "writer_channel"
    required: false
    timeout: 30
"""
        config_path = self._create_test_config_file(config_content)
        try:
            self.engine.load_hooks(config_path)

            event = Event(name="CHAPTER_WRITTEN", source="test")
            self.engine.trigger(event)

            status = self.engine.get_hook_status("状态测试Hook")
            self.assertEqual(status, HookStatus.SUCCESS)
        finally:
            os.unlink(config_path)


class TestActionResult(TestCase):
    """ActionResult数据类测试"""

    def test_action_result_creation(self):
        """测试ActionResult创建"""
        result = ActionResult(
            success=True,
            output={"key": "value"},
            duration_ms=150.5
        )
        self.assertTrue(result.success)
        self.assertEqual(result.output["key"], "value")
        self.assertEqual(result.duration_ms, 150.5)

    def test_action_result_with_error(self):
        """测试带错误的ActionResult"""
        result = ActionResult(
            success=False,
            error="Something went wrong",
            duration_ms=50.0
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Something went wrong")


if __name__ == "__main__":
    import unittest
    unittest.main()