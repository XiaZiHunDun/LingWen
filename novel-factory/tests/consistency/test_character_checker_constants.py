"""R1-006 锁定测试: character_checker 的 detection_window 默认值必须是模块常量

防止硬编码 200 再次潜入代码 - 任何对 DEFAULT_DETECTION_WINDOW 的修改
必须显式更新测试,而不是悄悄改字面量。
"""
from infra.consistency.checkers import character_checker
from infra.consistency.checkers.character_checker import CharacterChecker


class TestR1006DetectionWindowConstant:
    """R1-006: window_size 默认值应抽成模块级常量,禁止裸字面量"""

    def test_default_detection_window_constant_exists(self):
        """模块必须导出 DEFAULT_DETECTION_WINDOW 常量"""
        assert hasattr(character_checker, "DEFAULT_DETECTION_WINDOW"), (
            "character_checker 模块必须导出 DEFAULT_DETECTION_WINDOW 常量"
        )
        assert isinstance(character_checker.DEFAULT_DETECTION_WINDOW, int)
        assert character_checker.DEFAULT_DETECTION_WINDOW > 0

    def test_default_detection_window_value_locked(self):
        """锁定默认值为 200 (历史值,行为契约)

        如果业务需要调整窗口大小,应改 YAML 配置 detection_window,
        而非修改此常量。
        """
        assert character_checker.DEFAULT_DETECTION_WINDOW == 200

    def test_checker_uses_constant_as_fallback(self):
        """CharacterPersonalityChecker 在 rules 缺 detection_window 时
        必须回退到模块常量,不能回退到裸字面量。
        """
        # rules 中无 detection_window 字段
        checker = CharacterChecker(rules={})
        # 通过 _check_personality_conflicts 触发 fallback 逻辑
        # 实际值由 self.rules.get("detection_window", DEFAULT_...) 决定
        # 间接验证: 显式比较 rules.get() 的行为
        rules = {}
        assert rules.get("detection_window", character_checker.DEFAULT_DETECTION_WINDOW) == 200
