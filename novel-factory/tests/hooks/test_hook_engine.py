#!/usr/bin/env python3
"""
Hook引擎测试
"""
import os
import tempfile
import time
from pathlib import Path
from unittest import TestCase

from infra.hooks import Event, EventBus, EventTypes
from infra.hooks.config_loader import HookConfig, HookConfigLoader, ConditionEvaluator
from infra.hooks.hook_engine import HookEngine, HookStatus, HookExecutionError
from infra.hooks.actions.base import ActionResult, BaseAction
from infra.hooks.actions.run_checker import RunCheckerAction
from infra.hooks.actions.notify import NotifyAction
from infra.hooks.actions.update_state import UpdateStateAction


class _SlowAction(BaseAction):
    """R3-004: 慢动作 - 用于验证 timeout 强制

    sleep_time 由 params 控制,默认 2.0s。
    """
    action_type = "slow"

    def execute(self, params, context):
        sleep_time = params.get("sleep", 2.0)
        time.sleep(sleep_time)
        return ActionResult(success=True, output=f"slept {sleep_time}s")


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


class TestHookEngineTimeout(TestCase):
    """R3-004: required hook 同步等待 + action 超时强制

    HookEngine._execute_action 用 ThreadPoolExecutor + future.result
    带 timeout 跑 action.execute()。required hook 超时/失败会
    抛 HookExecutionError,调用方据此回滚。
    """

    def setUp(self):
        self.event_bus = EventBus()
        self.config_loader = HookConfigLoader()
        self.engine = HookEngine(self.event_bus, self.config_loader)
        # 注册慢动作
        self.engine.register_action("slow", _SlowAction)

    def _create_config(self, content: str) -> str:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(content)
            return f.name

    def test_required_hook_timeout_raises(self):
        """required hook 慢动作超时 → 抛 HookExecutionError"""
        config_content = """
hooks:
  - name: "慢动作必需Hook"
    trigger:
      event: "CHAPTER_WRITTEN"
    actions:
      - type: "slow"
        params:
          sleep: 3.0
    required: true
    timeout: 1
"""
        config_path = self._create_config(config_content)
        try:
            self.engine.load_hooks(config_path)
            event = Event(name="CHAPTER_WRITTEN", source="test")
            t0 = time.time()
            with self.assertRaises(HookExecutionError) as ctx:
                self.engine.trigger(event)
            elapsed = time.time() - t0
            # 超时应该约 1s,绝不超过 sleep 时间 3s(节省测试时间)
            self.assertLess(elapsed, 2.5, f"超时未生效,实际耗时 {elapsed:.2f}s")
            self.assertIn("timed out", str(ctx.exception).lower())
        finally:
            os.unlink(config_path)

    def test_required_hook_timeout_status_recorded(self):
        """required hook 超时 → 状态为 TIMEOUT,失败为 FAILED (区分二者)"""
        config_content = """
hooks:
  - name: "超时Hook"
    trigger:
      event: "CHAPTER_WRITTEN"
    actions:
      - type: "slow"
        params:
          sleep: 2.0
    required: true
    timeout: 1
"""
        config_path = self._create_config(config_content)
        try:
            self.engine.load_hooks(config_path)
            event = Event(name="CHAPTER_WRITTEN", source="test")
            try:
                self.engine.trigger(event)
            except HookExecutionError:
                pass
            last = self.engine.get_last_result("超时Hook")
            self.assertIsNotNone(last)
            self.assertEqual(last.status, HookStatus.TIMEOUT)
        finally:
            os.unlink(config_path)

    def test_optional_hook_timeout_does_not_raise(self):
        """optional hook 超时 → 不抛异常,继续执行"""
        config_content = """
hooks:
  - name: "可选慢Hook"
    trigger:
      event: "CHAPTER_WRITTEN"
    actions:
      - type: "slow"
        params:
          sleep: 2.0
    required: false
    timeout: 1
"""
        config_path = self._create_config(config_content)
        try:
            self.engine.load_hooks(config_path)
            event = Event(name="CHAPTER_WRITTEN", source="test")
            t0 = time.time()
            # optional hook 超时不应抛异常
            results = self.engine.trigger(event)
            elapsed = time.time() - t0
            self.assertLess(elapsed, 2.5, f"超时未生效,实际耗时 {elapsed:.2f}s")
            self.assertEqual(len(results), 1)
            # 状态应是 TIMEOUT 但不抛异常
            self.assertEqual(results[0].status, HookStatus.TIMEOUT)
        finally:
            os.unlink(config_path)

    def test_action_completes_within_timeout_succeeds(self):
        """action 在 timeout 内完成 → 正常返回 SUCCESS"""
        config_content = """
hooks:
  - name: "快速Hook"
    trigger:
      event: "CHAPTER_WRITTEN"
    actions:
      - type: "slow"
        params:
          sleep: 0.2
    required: true
    timeout: 5
"""
        config_path = self._create_config(config_content)
        try:
            self.engine.load_hooks(config_path)
            event = Event(name="CHAPTER_WRITTEN", source="test")
            results = self.engine.trigger(event)
            self.assertEqual(results[0].status, HookStatus.SUCCESS)
        finally:
            os.unlink(config_path)


class TestHookEngineDefaultActions(TestCase):
    """R3-014: 默认应注册所有 actions/ 下的 action,不只是 2 个"""

    def test_all_action_classes_auto_registered(self):
        """新 HookEngine 实例应自动注册 actions/ 下的全部 7 个 action"""
        from infra.hooks.actions import ACTION_REGISTRY

        engine = HookEngine()
        registered = set(engine.get_registered_action_types())

        # 1) 7 个内置 action 必须全部就位
        expected = set(ACTION_REGISTRY.keys())
        self.assertEqual(
            registered, expected,
            f"缺少默认注册: {expected - registered};"
            f"多余注册: {registered - expected}",
        )

    def test_action_type_matches_registry_class(self):
        """每个注册的 action_class().action_type 必须等于 registry key"""
        from infra.hooks.actions import ACTION_REGISTRY

        engine = HookEngine()
        for type_name, action_cls in ACTION_REGISTRY.items():
            # 校验:engine 里注册的类就是 registry 里的类
            self.assertIs(engine._action_registry[type_name], action_cls)
            # 校验:每个 action 实例自报的 type_name == registry key
            self.assertEqual(action_cls().action_type, type_name)

    def test_legacy_two_actions_still_present(self):
        """回归保护:之前已注册的两个(trigger_module, log_state_change)仍在"""
        engine = HookEngine()
        registered = set(engine.get_registered_action_types())
        self.assertIn("trigger_module", registered)
        self.assertIn("log_state_change", registered)

    def test_unknown_action_type_rejected_at_load(self):
        """未注册的 action_type 必须在 load_hooks 时被 validator 拒绝,不能等到 trigger"""
        config_content = """
hooks:
  - name: "未知动作Hook"
    trigger:
      event: "CHAPTER_WRITTEN"
    actions:
      - type: "nonexistent_action_xyz"
    required: false
    timeout: 5
"""
        engine = HookEngine()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            config_path = f.name
        try:
            # 7 个 action 全部默认注册后,任何 actions: 列表里的 type
            # 若不在 ACTION_REGISTRY 里,load_hooks 就会抛 ValueError
            with self.assertRaises(ValueError) as ctx:
                engine.load_hooks(config_path)
            self.assertIn("无效类型", str(ctx.exception))
            self.assertIn("nonexistent_action_xyz", str(ctx.exception))
        finally:
            os.unlink(config_path)

    def test_can_still_register_custom_action(self):
        """修复后:用户仍可在默认注册之上添加自定义 action (不冲突)"""
        engine = HookEngine()
        # 默认就有 7 个,再注册一个 'slow'
        before = len(engine.get_registered_action_types())
        engine.register_action("slow", _SlowAction)
        after = len(engine.get_registered_action_types())
        self.assertEqual(after, before + 1)
        self.assertIn("slow", engine.get_registered_action_types())


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