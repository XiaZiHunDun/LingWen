#!/usr/bin/env python3
"""
动作测试
"""
import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase

from infra.hooks.actions.base import ActionResult, BaseAction
from infra.hooks.actions.notify import NotifyAction
from infra.hooks.actions.update_state import UpdateStateAction


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
        from infra.hooks.actions.run_checker import RunCheckerAction
        action = RunCheckerAction()
        self.assertEqual(action.action_type, "run_checker")

    def test_missing_checker_param(self):
        """测试缺少checker参数"""
        from infra.hooks.actions.run_checker import RunCheckerAction
        action = RunCheckerAction()

        result = action.execute(params={}, context={})
        self.assertFalse(result.success)
        self.assertIn("缺少必需参数", result.error)

    def test_unknown_checker(self):
        """测试未知检查器"""
        from infra.hooks.actions.run_checker import RunCheckerAction
        action = RunCheckerAction()

        result = action.execute(
            params={"checker": "unknown_checker"},
            context={}
        )
        self.assertFalse(result.success)
        self.assertIn("Unknown checker", result.error)


class TestTriggerModuleActionShellSafety(TestCase):
    """TriggerModuleAction 安全性回归测试 — P0 修复锁定契约

    原始漏洞 (P0): _execute_via_cli 用 `" ".join(cmd_parts)` + `shell=True`
    拼接命令,任何从 YAML/hook context 来的参数(含 chapter_num/outline/count)
    都会被 /bin/sh 解释 → shell 注入风险。

    修复后契约:
    1. subprocess.run 必须接收 list(不是 string)
    2. shell=True 绝不能出现(只能 shell=False / 不传)
    3. 真实 subprocess 也不应被触发(测试用 mock)

    这些测试本身也会调真的方法,但 mock 掉 subprocess.run — 因此即使
    代码被回退到旧行为,测试仍能 fail 出来,作为长期回归网。
    """

    def setUp(self):
        from infra.hooks.actions.trigger_module import TriggerModuleAction
        self.action = TriggerModuleAction()
        self._run_calls = []

    def _mock_subprocess(self):
        """注入一个 mock subprocess.run,记录所有调用参数"""
        from unittest.mock import patch, MagicMock

        mock = MagicMock()
        # 模拟 CompletedProcess-like 对象
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        mock_result.stderr = ""
        mock.run.return_value = mock_result

        def record(*args, **kwargs):
            self._run_calls.append((args, kwargs))
            return mock_result

        mock.run.side_effect = record
        return patch("infra.hooks.actions.trigger_module.subprocess.run", record)

    def test_execute_via_cli_uses_list_not_string(self):
        """subprocess.run 的第一个位置参数必须是 list,不能是 string"""
        from unittest.mock import patch

        def fake_run(*args, **kwargs):
            self._run_calls.append((args, kwargs))
            r = MagicMock()
            r.returncode = 0
            r.stdout = ""
            r.stderr = ""
            return r

        with patch("infra.hooks.actions.trigger_module.subprocess.run", fake_run):
            self.action.execute(
                params={"command": "anti-trope", "count": 3},
                context={"chapter_num": 5, "outline": "some outline"}
            )

        self.assertEqual(len(self._run_calls), 1, "subprocess.run 应被调一次")
        called_args, _ = self._run_calls[0]
        self.assertEqual(len(called_args), 1, "应有 1 个位置参数 (cmd)")
        cmd = called_args[0]
        self.assertIsInstance(
            cmd, list,
            f"P0 安全: cmd 必须是 list,不能是 str(实际 {type(cmd).__name__})"
        )

    def test_execute_via_cli_does_not_use_shell_true(self):
        """shell=True 绝不能出现(参数里没有,或显式 False)"""
        from unittest.mock import patch

        def fake_run(*args, **kwargs):
            self._run_calls.append((args, kwargs))
            r = MagicMock()
            r.returncode = 0
            r.stdout = ""
            r.stderr = ""
            return r

        with patch("infra.hooks.actions.trigger_module.subprocess.run", fake_run):
            self.action.execute(
                params={"command": "anti-trope", "count": 2},
                context={"chapter_num": 1}
            )

        _, called_kwargs = self._run_calls[0]
        # shell 参数要么不存在,要么显式 False
        shell_value = called_kwargs.get("shell", False)
        self.assertFalse(
            shell_value,
            f"P0 安全: shell=True 是 shell 注入漏洞,禁止使用(实际 shell={shell_value!r})"
        )

    def test_execute_via_cli_passes_injection_attempt_safely(self):
        """恶意参数(如 '$(rm -rf /)')应作为字面参数传给程序,不被 shell 解释

        旧行为:' '.join + shell=True → /bin/sh 看到 '$(rm -rf /)' 会执行替换
        新行为:list 传参 → 该字符串作为 argv[2..] 给 lingwen.py,不会触发 shell
        """
        from unittest.mock import patch, MagicMock

        def fake_run(*args, **kwargs):
            self._run_calls.append((args, kwargs))
            r = MagicMock()
            r.returncode = 0
            r.stdout = ""
            r.stderr = ""
            return r

        # 试图在 outline 里塞 shell 元字符
        malicious = "$(touch /tmp/pwned) && echo evil"

        with patch("infra.hooks.actions.trigger_module.subprocess.run", fake_run):
            result = self.action.execute(
                params={"command": "anti-trope"},
                context={"chapter_num": 1, "outline": malicious}
            )

        # 命令成功(没让 shell 误执行 malicious)
        self.assertTrue(result.success, f"subprocess 应被以 list 方式调用,结果应 success (实际: {result.error})")

        called_args, _ = self._run_calls[0]
        cmd = called_args[0]
        self.assertIsInstance(cmd, list)
        # malicious 字符串应原样出现在 cmd 列表里(作为 --outline 的值),不被解析
        self.assertIn(malicious, cmd, "malicious 字符串应原样作为参数,不触发 shell 解释")

    def test_execute_via_cli_includes_expected_args(self):
        """契约回归:context/params 里的 key 应正确映射到 CLI 参数"""
        from unittest.mock import patch

        def fake_run(*args, **kwargs):
            self._run_calls.append((args, kwargs))
            r = MagicMock()
            r.returncode = 0
            r.stdout = ""
            r.stderr = ""
            return r

        with patch("infra.hooks.actions.trigger_module.subprocess.run", fake_run):
            self.action.execute(
                params={"command": "anti-trope", "count": 7, "timeout": 60},
                context={"chapter_num": 42, "outline": "my outline"}
            )

        called_args, _ = self._run_calls[0]
        cmd = called_args[0]
        # cmd 是 list:["python", <lingwen_py>, "anti-trope", "--chapter", "42", "--outline", "my outline", "--count", "7"]
        self.assertEqual(cmd[0], "python")
        self.assertEqual(cmd[2], "anti-trope")
        # 找出 --outline / --chapter / --count 的位置
        self.assertIn("--chapter", cmd)
        self.assertIn("42", cmd)
        self.assertIn("--outline", cmd)
        self.assertIn("my outline", cmd)
        self.assertIn("--count", cmd)
        self.assertIn("7", cmd)

    def test_execute_via_cli_uses_subprocess_timeout(self):
        """超时参数应传给 subprocess.run"""
        from unittest.mock import patch

        def fake_run(*args, **kwargs):
            self._run_calls.append((args, kwargs))
            r = MagicMock()
            r.returncode = 0
            r.stdout = ""
            r.stderr = ""
            return r

        with patch("infra.hooks.actions.trigger_module.subprocess.run", fake_run):
            self.action.execute(
                params={"command": "anti-trope", "timeout": 45},
                context={}
            )

        _, called_kwargs = self._run_calls[0]
        self.assertEqual(called_kwargs.get("timeout"), 45, "timeout 参数应传给 subprocess.run")


if __name__ == "__main__":
    import unittest
    unittest.main()