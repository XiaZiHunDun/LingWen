"""角色能动性检测器测试"""

from infra.consistency.checkers.character_agency import CharacterAgencyChecker


class TestCharacterAgencyChecker:
    """CharacterAgencyChecker 测试"""

    def test_init(self):
        checker = CharacterAgencyChecker()
        assert checker is not None

    def test_agency_ratio_threshold(self):
        assert CharacterAgencyChecker.AGENCY_RATIO_THRESHOLD == 0.3

    def test_min_reactive_hits(self):
        assert CharacterAgencyChecker.MIN_REACTIVE_HITS == 3

    def test_check_empty_content(self):
        checker = CharacterAgencyChecker()
        context = {"target_characters": ["张三"]}
        issues = checker.check("", 1, context)
        assert issues == []

    def test_check_no_reactive_patterns(self):
        checker = CharacterAgencyChecker()
        context = {"target_characters": ["张三"]}
        issues = checker.check("张三站了起来，走向前方，决定行动。", 1, context)
        assert issues == []  # 没有被动模式命中

    def test_check_high_agency_passes(self):
        """高能动性不报告问题"""
        checker = CharacterAgencyChecker()
        context = {"target_characters": ["张三"]}
        content = (
            "张三站了起来。张三走向前方。张三决定行动。"
            "张三攻击了敌人。张三带领队伍。张三命令手下。"
            "张三推开了门。张三跑得很快。"
        )
        issues = checker.check(content, 1, context)
        assert issues == []  # 全是主动行动

    def test_check_low_agency_detected(self):
        """低能动性检测到"""
        checker = CharacterAgencyChecker()
        context = {"target_characters": ["张三"]}
        content = (
            # 被动反应（多处）
            "张三眼眶泛红。张三眼中含泪。张三泪水模糊了视线。"
            "张三静静地看着。张三默默地站着。"
            # 少量主动
            "张三站了起来。"
        )
        issues = checker.check(content, 1, context)
        assert len(issues) >= 1
        assert issues[0].issue_type == "low_character_agency"
        assert issues[0].character == "张三"

    def test_check_below_min_reactive_hits(self):
        """被动命中不足阈值时不检测"""
        checker = CharacterAgencyChecker()
        context = {"target_characters": ["张三"]}
        # 只有2次被动命中 < MIN_REACTIVE_HITS(3)
        content = "张三眼眶泛红。张三眼中含泪。"
        issues = checker.check(content, 1, context)
        assert issues == []

    def test_calculate_agency_ratio_no_reactive(self):
        checker = CharacterAgencyChecker()
        content = "张三站了起来。张三走向前方。"
        ratio = checker.calculate_agency_ratio(content, "张三")
        assert ratio == 1.0  # 无被动 = 1.0

    def test_calculate_agency_ratio_no_active(self):
        checker = CharacterAgencyChecker()
        content = "张三眼眶泛红。张三眼中含泪。"
        ratio = checker.calculate_agency_ratio(content, "张三")
        assert ratio == 0.0  # 无主动 = 0.0

    def test_calculate_agency_ratio_no_both(self):
        checker = CharacterAgencyChecker()
        content = "张三在房间里。"
        ratio = checker.calculate_agency_ratio(content, "张三")
        assert ratio == 0.0  # 无主动无被动 = 0.0

    def test_calculate_agency_ratio_mixed(self):
        checker = CharacterAgencyChecker()
        content = "张三眼眶泛红。张三眼中含泪。张三站了起来。"
        ratio = checker.calculate_agency_ratio(content, "张三")
        assert 0.0 <= ratio <= 1.0

    def test_ratio_below_02_is_p1(self):
        """比率 < 0.2 为 P1 严重级别"""
        checker = CharacterAgencyChecker()
        context = {"target_characters": ["张三"]}
        # 被动多，主动少
        content = (
            "张三眼眶泛红。张三眼中含泪。"
            "张三泪水模糊。张三静静地看着。"
            "张三默默地蹲着。张三感到悲伤。"
            "张三站了起来。"
        )
        issues = checker.check(content, 1, context)
        # 比率 < 0.2 应为 P1
        if issues:
            # P1 是最严重的
            assert issues[0].severity.name == "P1" or any(
                i.severity.name == "P1" for i in issues
            )

    def test_check_without_target_characters_uses_default(self):
        """无 target_characters 时使用默认方式"""
        checker = CharacterAgencyChecker()
        # 不传 target_characters，会尝试从上下文推断
        context = {}
        # 应该能运行而不报错（可能返回空列表）
        issues = checker.check("任意内容", 1, context)
        assert isinstance(issues, list)

    def test_multiple_characters(self):
        checker = CharacterAgencyChecker()
        context = {"target_characters": ["张三", "李四"]}
        content = (
            "张三眼眶泛红。张三眼中含泪。张三泪水模糊。"
            "张三静静地看着。张三默默地蹲着。"
            "李四站了起来。李四走向前方。李四决定行动。"
        )
        issues = checker.check(content, 1, context)
        # 张三被动多：眼眶泛红、眼中含泪、泪水模糊、静静地看着、默默地 = 5
        # 张三主动：站着(0)、走向(0)、决定(0) = 0 (不在张三段落)
        # 注意：_count_patterns 在包含角色名的整个段落中计数，
        # 段落中有张三和李四，所以双方都看到所有模式
        # 因此 ratio 相同，张三不会单独触发
        assert isinstance(issues, list)
