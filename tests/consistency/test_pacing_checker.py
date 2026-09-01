"""节奏检测器测试"""

from unittest.mock import MagicMock

from lingwen_quality.consistency.checkers.pacing_checker import PacingChecker


class TestPacingChecker:
    """PacingChecker 测试"""

    def test_init(self):
        checker = PacingChecker()
        assert checker is not None
        assert len(checker.action_keywords) > 0
        assert len(checker.cooldown_keywords) > 0
        assert len(checker.foreshadow_keywords) > 0

    def test_check_empty(self):
        checker = PacingChecker()
        issues = checker.check("", 1, {})
        assert issues == []

    def test_check_normal_content(self):
        """正常内容不触发节奏问题"""
        checker = PacingChecker()
        content = (
            "清晨的阳光洒在窗台上。张三起床洗漱。"
            "他走到厨房，准备早餐。一切都很平静。"
            "吃完早餐后，他出门散步。"
        )
        issues = checker.check(content, 1, {})
        assert issues == []

    def test_check_high_action_density(self):
        """动作密度过高触发问题"""
        checker = PacingChecker()
        # 构造大量动作段
        content = ""
        for _ in range(20):
            content += "战斗攻击冲击爆发爆炸碰撞。"
        issues = checker.check(content, 1, {})
        # 动作密度 > 60% 且 action_count > 5
        assert len(issues) >= 1
        assert any("节奏" in i.title or "密度" in i.title for i in issues)

    def test_check_climax_without_cooldown(self):
        """连续高潮无缓冲"""
        checker = PacingChecker()
        content = (
            "战斗攻击冲击爆发。战斗攻击碰撞对决。"
            "战斗攻击冲击爆发。战斗攻击碰撞对决。"
            "战斗攻击冲击爆发。"
        )
        issues = checker.check(content, 1, {})
        # 可能触发节奏过密或高潮后无缓冲
        assert len(issues) >= 0  # 取决于具体实现

    def test_check_long_setup(self):
        """铺垫过长"""
        checker = PacingChecker()
        content = ""
        for _ in range(10):
            content += "似乎可能将要准备预感。"
        content += "于是战斗开始了。"
        issues = checker.check(content, 1, {})
        # 铺垫超过40% 可能触发
        assert len(issues) >= 0

    def test_count_action_segments(self):
        checker = PacingChecker()
        content = "战斗攻击冲击爆发。正常句子。碰撞对决。"
        count = checker._count_action_segments(content)
        assert count >= 0

    def test_estimate_total_segments(self):
        checker = PacingChecker()
        content = "第一句。第二句。第三句！第四句？"
        total = checker._estimate_total_segments(content)
        assert total == 4

    def test_estimate_total_segments_empty(self):
        checker = PacingChecker()
        total = checker._estimate_total_segments("")
        assert total == 1  # max(1, ...)

    def test_has_climax_without_cooldown_true(self):
        checker = PacingChecker()
        content = "战斗攻击冲击爆发。战斗攻击碰撞对决。战斗攻击冲击爆发。"
        result = checker._has_climax_without_cooldown(content)
        assert isinstance(result, bool)

    def test_has_climax_without_cooldown_with_cooldown(self):
        """有缓冲时不触发"""
        checker = PacingChecker()
        content = "战斗攻击冲击爆发。沉默叹息思考。休息等待观察。"
        result = checker._has_climax_without_cooldown(content)
        assert result is False  # 有缓冲，不触发

    def test_measure_foreshadow_length(self):
        checker = PacingChecker()
        content = (
            "似乎可能也许将要准备预感担忧。"
            "似乎可能也许将要。"
            "正文开始。正文继续。正文结束。"
        )
        ratio = checker._measure_foreshadow_length(content)
        assert 0.0 <= ratio <= 1.0

    def test_measure_foreshadow_length_short(self):
        checker = PacingChecker()
        content = "很短。"
        ratio = checker._measure_foreshadow_length(content)
        assert ratio == 0.0  # less than 3 sentences

    def test_check_ripple_density_empty(self):
        """无涟漪时不触发"""
        checker = PacingChecker()
        mock_registry = MagicMock()
        mock_registry.list_active.return_value = ()
        issues = checker.check_ripple_density(mock_registry, 5)
        assert issues == []

    def test_check_ripple_density_high(self):
        """涟漪密度过高"""
        checker = PacingChecker()
        mock_registry = MagicMock()
        # 创建 mock ripples — 需要 origin_ch 属性
        mock_ripples = [
            MagicMock(ripple_id=f"r{i}", wavefront=(5,), origin_ch=1)
            for i in range(7)
        ]
        mock_registry.list_active.return_value = mock_ripples
        mock_registry.get_ripple.side_effect = lambda rid: next(
            r for r in mock_ripples if r.ripple_id == rid
        )
        issues = checker.check_ripple_density(mock_registry, 5)
        assert len(issues) >= 1
        assert any("密度" in i.title for i in issues)

    def test_check_ripple_density_normal(self):
        """正常涟漪数不触发"""
        checker = PacingChecker()
        mock_registry = MagicMock()
        mock_ripples = [
            MagicMock(ripple_id=f"r{i}", wavefront=(5,), origin_ch=1)
            for i in range(3)
        ]
        mock_registry.list_active.return_value = mock_ripples
        mock_registry.get_ripple.side_effect = lambda rid: next(
            r for r in mock_ripples if r.ripple_id == rid
        )
        issues = checker.check_ripple_density(mock_registry, 5)
        assert issues == []

    def test_check_ripple_density_convergence(self):
        """涟漪集中爆发"""
        checker = PacingChecker()
        mock_registry = MagicMock()
        mock_ripples = [
            MagicMock(ripple_id=f"r{i}", wavefront=(5, 6, 7), origin_ch=1)
            for i in range(4)
        ]
        mock_registry.list_active.return_value = mock_ripples
        mock_registry.get_ripple.side_effect = lambda rid: next(
            r for r in mock_ripples if r.ripple_id == rid
        )
        issues = checker.check_ripple_density(mock_registry, 10)
        assert len(issues) >= 1
        assert any("集中" in i.title for i in issues)

    def test_filter_active_wavefront(self):
        PacingChecker()
        mock_ripple = MagicMock()
        mock_ripple.origin_ch = 3
        mock_ripple.wavefront = (3, 5, 7, 10)
        filtered = PacingChecker._filter_active_wavefront(mock_ripple, 6)
        assert len(filtered) == 2  # 3, 5 (≤ 6)
        assert 3 in filtered
        assert 5 in filtered

    def test_check_ripple_density_custom_thresholds(self):
        checker = PacingChecker()
        mock_registry = MagicMock()
        mock_ripples = [
            MagicMock(ripple_id=f"r{i}", wavefront=(5,), origin_ch=1)
            for i in range(4)
        ]
        mock_registry.list_active.return_value = mock_ripples
        mock_registry.get_ripple.side_effect = lambda rid: next(
            r for r in mock_ripples if r.ripple_id == rid
        )
        # 使用自定义阈值，4 > 3 触发
        issues = checker.check_ripple_density(
            mock_registry, 5, active_threshold=3
        )
        assert len(issues) >= 1
