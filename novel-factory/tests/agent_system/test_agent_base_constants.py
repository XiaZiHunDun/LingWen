"""R1-011 锁定测试: AgentBase 的 default_temperature / default_max_tokens 必须来自 agent_config 注册表

防止 magic number 0.7 / 4096 再次潜入 base.py - 必须从 agent_config 读,
且值与历史一致 (行为契约)。
"""
from infra.agent_system.agent_config import AGENT_DEFAULTS
from infra.agent_system.agents.base import AgentBase


class TestR1011AgentDefaultsRegistry:
    """R1-011: temperature / max_tokens 必须从 AGENT_DEFAULTS 注册表读"""

    def test_agent_defaults_registry_exists(self):
        """agent_config 必须导出 AGENT_DEFAULTS 字典,作为 agent 默认参数中心"""
        assert isinstance(AGENT_DEFAULTS, dict)
        assert "temperature" in AGENT_DEFAULTS
        assert "max_tokens" in AGENT_DEFAULTS

    def test_temperature_value_locked(self):
        """锁定 default_temperature=0.7 (历史值,行为契约)"""
        assert AGENT_DEFAULTS["temperature"] == 0.7

    def test_max_tokens_value_locked(self):
        """锁定 default_max_tokens=4096 (历史值,行为契约)"""
        assert AGENT_DEFAULTS["max_tokens"] == 4096

    def test_agent_base_uses_registry_not_literal(self):
        """AgentBase 类属性必须从注册表读,不能是裸字面量"""
        # 通过类属性读出值(实例继承自类)
        assert AgentBase.default_temperature == AGENT_DEFAULTS["temperature"]
        assert AgentBase.default_max_tokens == AGENT_DEFAULTS["max_tokens"]

    def test_agent_base_does_not_contain_magic_number_source(self):
        """AgentBase 模块源码中不应出现 0.7 或 4096 裸字面量赋值

        这条测试是行为+源码双重检查:即使类属性值碰巧等于 0.7,
        也不能是 base.py 中直接写 = 0.7。
        """
        import inspect
        source = inspect.getsource(AgentBase)
        # 必须从注册表读 - 允许 "AGENT_DEFAULTS[" 出现
        assert "AGENT_DEFAULTS" in source, (
            "AgentBase 必须引用 AGENT_DEFAULTS 注册表,禁止裸字面量"
        )
        # 禁止裸赋值 "= 0.7" (带空格,避免误报 AGENT_DEFAULTS 里的值)
        assert "= 0.7" not in source, (
            "AgentBase 源码不应出现 '= 0.7' 裸字面量,应通过 AGENT_DEFAULTS 读"
        )
        assert "= 4096" not in source, (
            "AgentBase 源码不应出现 '= 4096' 裸字面量,应通过 AGENT_DEFAULTS 读"
        )
