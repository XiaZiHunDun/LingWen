#!/usr/bin/env python3
"""
动作测试
"""
import json
import os
import tempfile
from pathlib import Path
from subprocess import TimeoutExpired
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

    def test_auto_consistency_checker_is_removed(self):
        """auto_consistency_checker 已在 P4-2 删除,RunCheckerAction 不应再支持

        P4-2 删除了 tools/consistency/auto_consistency_checker.py;
        原 _run_auto_consistency_check 方法变成死代码(P0 broken import)。
        契约:任何 "auto_consistency_checker" 请求都应返回 Unknown。
        """
        from infra.hooks.actions.run_checker import RunCheckerAction
        action = RunCheckerAction()

        result = action.execute(
            params={"checker": "auto_consistency_checker", "chapter_id": "ch001"},
            context={}
        )
        self.assertFalse(result.success)
        self.assertIn("Unknown checker", result.error)

    def test_run_quality_gate_uses_correct_import_path(self):
        """质量门禁应走正确的 import path: infra.tools.consistency.run_quality_checks

        原代码用 `from tools.consistency.run_quality_checks` — 但实际目录是
        `infra/tools/consistency/`,旧路径从来 import 不通。这是 P4-2 删
        auto_consistency_checker 留下的潜在 bug,P5-1 修复 + 锁定。
        """
        from unittest.mock import MagicMock, patch

        from infra.hooks.actions.run_checker import RunCheckerAction

        fake_result = {"passed": True, "score": 0.95}
        with patch(
            "infra.tools.consistency.run_quality_checks.run_quality_checks",
            return_value=fake_result,
            create=True,
        ) as mock_run:
            # 还需要让 import 走通 — patch 掉整个模块
            with patch.dict("sys.modules", {
                "infra.tools.consistency.run_quality_checks": MagicMock(
                    run_quality_checks=mock_run
                )
            }):
                action = RunCheckerAction()
                result = action.execute(
                    params={
                        "checker": "quality_gate",
                        "chapter_range": "1-10",
                        "threshold": "Silver"
                    },
                    context={}
                )

        # 修复后契约:成功返回,score / threshold / range 正确
        self.assertTrue(result.success, f"应成功 (error={result.error})")
        self.assertEqual(result.output["checker"], "quality_gate")
        self.assertEqual(result.output["score"], 0.95)
        self.assertEqual(result.output["threshold"], "Silver")
        self.assertEqual(result.output["chapter_range"], "1-10")
        # run_quality_checks 必须被以正确参数调用
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args.kwargs
        self.assertEqual(call_kwargs.get("chapter_range"), "1-10")
        self.assertEqual(call_kwargs.get("threshold"), "Silver")


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
        from unittest.mock import MagicMock, patch

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
        from unittest.mock import MagicMock, patch

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
        from unittest.mock import MagicMock, patch

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
        from unittest.mock import MagicMock, patch

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
        from unittest.mock import MagicMock, patch

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
        from unittest.mock import MagicMock, patch

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


class TestBlockProceedAction(TestCase):
    """BlockProceedAction — 三条铁律强制验证闭环"""

    def setUp(self):
        from infra.hooks.actions.block_proceed import BlockProceedAction
        self.action = BlockProceedAction()

    def test_action_type(self):
        self.assertEqual(self.action.action_type, "block_proceed")

    def test_blocks_when_verify_result_is_null_and_block_on_null_default(self):
        """核心契约:verify_result 为 None + block_on_null 默认 True → 阻止"""
        result = self.action.execute(
            params={"reason": "审核未通过"},
            context={"event_name": "post_verify", "hook_name": "verify_check", "verify_result": None}
        )
        self.assertFalse(result.success)
        self.assertIn("审核未通过", result.error)

    def test_blocks_when_verify_result_is_string_null(self):
        """verify_result='null'(字符串) + block_on_null=True → 同样阻止

        上游 hook 可能把缺失值序列化成字符串 'null',需要兼容。
        """
        result = self.action.execute(
            params={"reason": "结果为空"},
            context={"verify_result": "null"}
        )
        self.assertFalse(result.success)

    def test_does_not_block_when_verify_result_exists(self):
        """verify_result 存在(非 None / 非 'null') → 不阻止"""
        result = self.action.execute(
            params={"reason": "x"},
            context={"verify_result": {"score": 0.9, "passed": True}}
        )
        self.assertTrue(result.success)
        self.assertFalse(result.output["blocked"])

    def test_does_not_block_when_block_on_null_false(self):
        """即使 verify_result 是 None,只要 block_on_null=False 也不阻止"""
        result = self.action.execute(
            params={"reason": "test", "block_on_null_result": False},
            context={"verify_result": None}
        )
        self.assertTrue(result.success)
        self.assertFalse(result.output["blocked"])

    def test_records_block_reason_to_state(self):
        """阻止时应把 blocked_reason / blocked_at / blocked_at_hook 写入状态

        这是"强制验证闭环"的核心 — 阻止记录要可被后续 step 查询到。
        """
        recorded = {}

        def fake_set_state(key, value):
            recorded[key] = value

        from unittest.mock import patch
        with patch("infra.tools.workflow.lib.set_state", fake_set_state, create=True):
            result = self.action.execute(
                params={"reason": "数据不达标"},
                context={"event_name": "post_verify", "hook_name": "verify_check", "verify_result": None}
            )

        self.assertFalse(result.success)
        self.assertEqual(recorded.get("blocked_reason"), "数据不达标")
        self.assertEqual(recorded.get("blocked_at"), "post_verify")
        self.assertEqual(recorded.get("blocked_at_hook"), "verify_check")

    def test_set_state_failure_is_tolerated(self):
        """set_state 抛异常不能整个 action 失败 — 阻止本身已经发生,日志记录是 best-effort"""
        from unittest.mock import patch

        def broken_set_state(*args, **kwargs):
            raise RuntimeError("db locked")

        with patch("infra.tools.workflow.lib.set_state", broken_set_state, create=True):
            result = self.action.execute(
                params={"reason": "test"},
                context={"verify_result": None}
            )

        # 即使 state 写入失败,仍然返回阻止结果
        self.assertFalse(result.success)
        self.assertIn("test", result.error)

    def test_default_reason_when_not_provided(self):
        """params 缺 reason 时,error 应包含默认提示而不是空字符串"""
        result = self.action.execute(
            params={},
            context={"verify_result": None}
        )
        self.assertFalse(result.success)
        self.assertIn("未指定原因", result.error)


class TestLogStateChangeAction(TestCase):
    """LogStateChangeAction — 状态变更日志记录"""

    def setUp(self):
        from infra.hooks.actions.log_state_change import LogStateChangeAction
        self.action = LogStateChangeAction()
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_action_type(self):
        self.assertEqual(self.action.action_type, "log_state_change")

    def test_writes_json_line_with_expected_keys(self):
        """日志条目应包含 timestamp / event / data / source 四个键"""
        log_path = self.temp_dir / "history.log"
        result = self.action.execute(
            params={"log_path": str(log_path)},
            context={
                "event_name": "STEP_TRANSITION",
                "data": {"from": "STEP_14", "to": "STEP_15"},
                "source": "lib.py"
            }
        )

        self.assertTrue(result.success, f"应成功 (error={result.error})")
        self.assertTrue(result.output["logged"])
        self.assertEqual(result.output["path"], str(log_path))

        # 验证文件内容
        content = log_path.read_text(encoding="utf-8").strip()
        entry = json.loads(content)
        self.assertIn("timestamp", entry)
        self.assertEqual(entry["event"], "STEP_TRANSITION")
        self.assertEqual(entry["data"], {"from": "STEP_14", "to": "STEP_15"})
        self.assertEqual(entry["source"], "lib.py")

    def test_appends_multiple_entries(self):
        """多次 execute 应追加(append)而不是覆盖"""
        log_path = self.temp_dir / "history.log"

        for i in range(3):
            self.action.execute(
                params={"log_path": str(log_path)},
                context={"event_name": f"E{i}", "data": {"i": i}, "source": "test"}
            )

        lines = log_path.read_text(encoding="utf-8").strip().split("\n")
        self.assertEqual(len(lines), 3)
        events = [json.loads(line)["event"] for line in lines]
        self.assertEqual(events, ["E0", "E1", "E2"])

    def test_creates_parent_directories(self):
        """log_path 父目录不存在时应自动创建"""
        nested_log = self.temp_dir / "a" / "b" / "c" / "history.log"
        self.assertFalse(nested_log.parent.exists())

        result = self.action.execute(
            params={"log_path": str(nested_log)},
            context={"event_name": "X", "data": {}, "source": "test"}
        )

        self.assertTrue(result.success)
        self.assertTrue(nested_log.exists())

    def test_uses_defaults_when_log_path_missing(self):
        """params 缺 log_path 时,使用默认路径 (相对项目根)"""
        result = self.action.execute(
            params={},
            context={"event_name": "DEFAULT_TEST", "data": {"k": "v"}, "source": "test"}
        )

        # 默认路径会成功创建 / 追加,即使 .state/ 之前没建过
        self.assertTrue(result.success, f"error={result.error}")
        # output 里返回的 path 应该是绝对路径
        self.assertTrue(Path(result.output["path"]).is_absolute())

    def test_handles_missing_context_keys(self):
        """context 缺 event_name / data / source 时不报错(用默认值)"""
        log_path = self.temp_dir / "history.log"
        result = self.action.execute(
            params={"log_path": str(log_path)},
            context={}
        )
        self.assertTrue(result.success)

        entry = json.loads(log_path.read_text(encoding="utf-8").strip())
        # 缺省值应兜底
        self.assertEqual(entry["event"], "UNKNOWN")
        self.assertEqual(entry["data"], {})
        self.assertEqual(entry["source"], "lib.py")


class TestRunScriptAction(TestCase):
    """RunScriptAction — hooks.yaml 触发任意脚本执行

    关键安全契约(与 trigger_module 同源):
    - subprocess.run 必须接收 list,禁止 shell=True
    - missing script param → 拒绝执行
    - 不存在的 script → 拒绝执行
    """

    def setUp(self):
        from infra.hooks.actions.run_script import RunScriptAction
        self.action = RunScriptAction()
        self.temp_dir = Path(tempfile.mkdtemp())
        self._run_calls = []

    def tearDown(self):
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _mock_subprocess(self, returncode=0, stdout="ok", stderr=""):
        """返回 patcher + record 函数,让 fake_run 录入所有调用"""
        from unittest.mock import MagicMock

        def fake_run(*args, **kwargs):
            self._run_calls.append((args, kwargs))
            r = MagicMock()
            r.returncode = returncode
            r.stdout = stdout
            r.stderr = stderr
            return r

        return fake_run

    def test_action_type(self):
        self.assertEqual(self.action.action_type, "run_script")

    def test_missing_script_param_returns_error(self):
        """缺 'script' 必需参数 → 不调 subprocess,直接返回错误"""
        from unittest.mock import patch

        with patch("infra.hooks.actions.run_script.subprocess.run", self._mock_subprocess()):
            result = self.action.execute(params={}, context={})

        self.assertFalse(result.success)
        self.assertIn("script", result.error)
        self.assertEqual(len(self._run_calls), 0, "缺参数时不应调 subprocess")

    def test_nonexistent_script_returns_error(self):
        """script 路径不存在 → 提前返回错误,不调 subprocess"""
        from unittest.mock import patch

        with patch("infra.hooks.actions.run_script.subprocess.run", self._mock_subprocess()):
            result = self.action.execute(
                params={"script": "/nonexistent/path/fake_script.sh"},
                context={}
            )

        self.assertFalse(result.success)
        self.assertIn("不存在", result.error)
        self.assertEqual(len(self._run_calls), 0)

    def test_successful_execution_returns_stdout(self):
        """成功执行:output 包含 stdout / stderr / returncode / script"""
        from unittest.mock import patch

        real_script = self.temp_dir / "hello.sh"
        real_script.write_text("#!/bin/sh\necho hi\n", encoding="utf-8")
        real_script.chmod(0o755)

        with patch("infra.hooks.actions.run_script.subprocess.run", self._mock_subprocess(
            returncode=0, stdout="hi\n", stderr=""
        )):
            result = self.action.execute(
                params={"script": str(real_script)},
                context={}
            )

        self.assertTrue(result.success, f"error={result.error}")
        self.assertEqual(result.output["stdout"], "hi\n")
        self.assertEqual(result.output["returncode"], 0)
        self.assertEqual(result.output["script"], str(real_script))

    def test_non_zero_returncode_returns_failure(self):
        """非零退出码 → success=False,error 用 stderr 兜底"""
        from unittest.mock import patch

        real_script = self.temp_dir / "fail.sh"
        real_script.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        real_script.chmod(0o755)

        with patch("infra.hooks.actions.run_script.subprocess.run", self._mock_subprocess(
            returncode=2, stdout="", stderr="something went wrong"
        )):
            result = self.action.execute(
                params={"script": str(real_script)},
                context={}
            )

        self.assertFalse(result.success)
        self.assertIn("something went wrong", result.error)
        self.assertEqual(result.output["returncode"], 2)

    def test_non_zero_with_empty_stderr_falls_back_to_code(self):
        """非零退出码但 stderr 为空 → error 兜底为 '非零退出码 N'"""
        from unittest.mock import patch

        real_script = self.temp_dir / "fail2.sh"
        real_script.write_text("#!/bin/sh\nexit 3\n", encoding="utf-8")
        real_script.chmod(0o755)

        with patch("infra.hooks.actions.run_script.subprocess.run", self._mock_subprocess(
            returncode=3, stdout="", stderr=""
        )):
            result = self.action.execute(params={"script": str(real_script)}, context={})

        self.assertFalse(result.success)
        self.assertIn("3", result.error)

    def test_uses_python_for_py_extension_by_default(self):
        """脚本后缀 .py → use_python 默认 True,cmd 第一个是 'python'"""
        from unittest.mock import patch

        real_script = self.temp_dir / "my_script.py"
        real_script.write_text("print('hi')\n", encoding="utf-8")

        with patch("infra.hooks.actions.run_script.subprocess.run", self._mock_subprocess()):
            self.action.execute(params={"script": str(real_script)}, context={})

        called_args, _ = self._run_calls[0]
        cmd = called_args[0]
        self.assertEqual(cmd[0], "python")
        self.assertIn(str(real_script), cmd)

    def test_explicit_python_true(self):
        """显式 python=True 时也用 python 解释器"""
        from unittest.mock import patch

        real_script = self.temp_dir / "no_ext_file"
        real_script.write_text("hi\n", encoding="utf-8")
        real_script.chmod(0o755)

        with patch("infra.hooks.actions.run_script.subprocess.run", self._mock_subprocess()):
            self.action.execute(
                params={"script": str(real_script), "python": True},
                context={}
            )

        called_args, _ = self._run_calls[0]
        cmd = called_args[0]
        self.assertEqual(cmd[0], "python")

    def test_explicit_python_false_skips_interpreter(self):
        """显式 python=False 时直接 exec,不加 python 前缀"""
        from unittest.mock import patch

        real_script = self.temp_dir / "shell_script.sh"
        real_script.write_text("echo hi\n", encoding="utf-8")
        real_script.chmod(0o755)

        with patch("infra.hooks.actions.run_script.subprocess.run", self._mock_subprocess()):
            self.action.execute(
                params={"script": str(real_script), "python": False},
                context={}
            )

        called_args, _ = self._run_calls[0]
        cmd = called_args[0]
        # 不应以 python 开头(直接是脚本绝对路径)
        self.assertNotEqual(cmd[0], "python")

    def test_args_appended_to_command(self):
        """params['args'] 应作为 cmd 后续元素追加"""
        from unittest.mock import patch

        real_script = self.temp_dir / "a.sh"
        real_script.write_text("#!/bin/sh\necho $@\n", encoding="utf-8")
        real_script.chmod(0o755)

        with patch("infra.hooks.actions.run_script.subprocess.run", self._mock_subprocess()):
            self.action.execute(
                params={"script": str(real_script), "args": ["--foo", "bar", "--baz", "qux"]},
                context={}
            )

        called_args, _ = self._run_calls[0]
        cmd = called_args[0]
        # args 列表应原样追加
        for a in ["--foo", "bar", "--baz", "qux"]:
            self.assertIn(a, cmd)

    def test_subprocess_uses_list_not_shell(self):
        """P0 安全契约:subprocess.run 必须接收 list,禁止 shell=True

        与 trigger_module 的安全契约同源 — 一旦回退到 ' '.join + shell=True,
        从 YAML 来的 args(含钩子事件数据)会被 /bin/sh 解释。
        """
        from unittest.mock import patch

        real_script = self.temp_dir / "x.sh"
        real_script.write_text("echo\n", encoding="utf-8")
        real_script.chmod(0o755)

        with patch("infra.hooks.actions.run_script.subprocess.run", self._mock_subprocess()):
            self.action.execute(params={"script": str(real_script), "python": False}, context={})

        called_args, called_kwargs = self._run_calls[0]
        cmd = called_args[0]
        # 必须是 list,不能是 string(避免 shell 注入)
        self.assertIsInstance(
            cmd, list,
            f"P0 安全: cmd 必须是 list,不是 str(实际 {type(cmd).__name__})"
        )
        # shell=True 绝不能出现
        shell_value = called_kwargs.get("shell", False)
        self.assertFalse(
            shell_value,
            f"P0 安全: shell=True 禁止使用(实际 shell={shell_value!r})"
        )

    def test_injection_attempt_passed_as_literal(self):
        """恶意参数应作为字面字符串传给程序,不被 shell 解释"""
        from unittest.mock import patch

        real_script = self.temp_dir / "a.sh"
        real_script.write_text("echo\n", encoding="utf-8")
        real_script.chmod(0o755)

        malicious = "$(touch /tmp/pwned) && echo evil"

        with patch("infra.hooks.actions.run_script.subprocess.run", self._mock_subprocess()):
            result = self.action.execute(
                params={
                    "script": str(real_script),
                    "python": False,
                    "args": ["--input", malicious]
                },
                context={}
            )

        # 命令应能成功(mock 总是返回 0)
        self.assertTrue(result.success, f"应成功,实际 error={result.error}")

        called_args, _ = self._run_calls[0]
        cmd = called_args[0]
        # malicious 字符串应原样在 cmd 列表中(作为 argv 元素,不触发 shell)
        self.assertIn(malicious, cmd)

    def test_timeout_propagates_to_subprocess(self):
        """timeout 参数应传给 subprocess.run"""
        from unittest.mock import patch

        real_script = self.temp_dir / "t.sh"
        real_script.write_text("sleep 999\n", encoding="utf-8")
        real_script.chmod(0o755)

        with patch("infra.hooks.actions.run_script.subprocess.run", self._mock_subprocess()):
            self.action.execute(
                params={"script": str(real_script), "python": False, "timeout": 30},
                context={}
            )

        _, called_kwargs = self._run_calls[0]
        self.assertEqual(called_kwargs.get("timeout"), 30)

    def test_timeout_expired_returns_error(self):
        """subprocess.TimeoutExpired → success=False, error 含超时信息"""
        from unittest.mock import patch

        real_script = self.temp_dir / "slow.sh"
        real_script.write_text("sleep 999\n", encoding="utf-8")
        real_script.chmod(0o755)

        def fake_run(*args, **kwargs):
            raise TimeoutExpired(cmd=args[0] if args else [], timeout=5)

        with patch("infra.hooks.actions.run_script.subprocess.run", fake_run):
            result = self.action.execute(
                params={"script": str(real_script), "python": False, "timeout": 5},
                context={}
            )

        self.assertFalse(result.success)
        self.assertIn("超时", result.error)

    def test_custom_cwd_propagated(self):
        """params['cwd'] 应作为 subprocess.run 的 cwd"""
        from unittest.mock import patch

        real_script = self.temp_dir / "cwd.sh"
        real_script.write_text("pwd\n", encoding="utf-8")
        real_script.chmod(0o755)

        with patch("infra.hooks.actions.run_script.subprocess.run", self._mock_subprocess()):
            self.action.execute(
                params={"script": str(real_script), "python": False, "cwd": str(self.temp_dir)},
                context={}
            )

        _, called_kwargs = self._run_calls[0]
        self.assertEqual(called_kwargs.get("cwd"), str(self.temp_dir))

    def test_extra_env_merged_with_os_environ(self):
        """params['env'] 应合并到 os.environ.copy() 之上"""
        from unittest.mock import patch

        real_script = self.temp_dir / "env.sh"
        real_script.write_text("env\n", encoding="utf-8")
        real_script.chmod(0o755)

        with patch("infra.hooks.actions.run_script.subprocess.run", self._mock_subprocess()):
            self.action.execute(
                params={
                    "script": str(real_script),
                    "python": False,
                    "env": {"MY_VAR": "hello"}
                },
                context={}
            )

        _, called_kwargs = self._run_calls[0]
        env = called_kwargs.get("env", {})
        # 合并的 env 应包含 MY_VAR
        self.assertEqual(env.get("MY_VAR"), "hello")
        # 也应保留 os.environ 里的关键变量(证明是 copy + update,不是 replace)
        self.assertIn("PATH", env)


if __name__ == "__main__":
    import unittest
    unittest.main()
