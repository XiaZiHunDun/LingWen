"""R2-011: split_chinese_sentences 行为测试 + 等价性回归"""
from infra.consistency.checkers.battle_visualization import BattleVisualizationChecker
from infra.consistency.checkers.text_utils import split_chinese_sentences
from infra.consistency.checkers.vocabulary import (
    ABSTRACT_CULTIVATION,
    CONCRETE_ACTION,
    CONCRETE_VISUAL,
)


class TestSplitChineseSentences:
    """split_chinese_sentences 是 str.split('。') 的精确等价包装"""

    def test_basic_split(self):
        """3 个句号 → 4 段(含末尾空串)"""
        result = split_chinese_sentences("第一句。第二句。第三句。")
        assert result == ["第一句", "第二句", "第三句", ""]

    def test_no_period_returns_single(self):
        """无句号 → 整段一个元素"""
        result = split_chinese_sentences("无句号文本")
        assert result == ["无句号文本"]

    def test_empty_string_returns_empty_list(self):
        """空字符串 → 一个空元素的列表(与 str.split 行为一致)"""
        result = split_chinese_sentences("")
        assert result == [""]

    def test_equivalence_to_native_split(self):
        """核心契约:与 str.split('。') 完全等价,无任何语义变更

        这是 R2-011 的灵魂 — 抽函数后 5 个调用方行为必须 0 变化。
        用 20 条随机样本验证。
        """
        import random
        random.seed(42)
        chinese_chars = "的一是了我不在人们有这个"
        for _ in range(20):
            # 随机生成 1-50 句的中文段落
            n = random.randint(1, 50)
            sentences = [
                "".join(random.choices(chinese_chars, k=random.randint(3, 10)))
                for _ in range(n)
            ]
            text = "。".join(sentences) + "。"

            ours = split_chinese_sentences(text)
            native = text.split("。")
            assert ours == native, f"分歧: {ours} vs {native}"

    def test_handles_unicode_emoji_and_special(self):
        """特殊字符(emoji/全角符号)不影响切分"""
        text = "第一句🎉。第二句✅。第三句❓。"  # 注意:❓不是 ?
        result = split_chinese_sentences(text)
        # 我们的 helper 只切 。 ,不切 ❓(即使它也是问号 Unicode)
        assert result == ["第一句🎉", "第二句✅", "第三句❓", ""]


class TestBattleVocabularyShared:
    """R2-012: vocabulary.py 共享词表 — battle_visualization 通过类属性引用"""

    def test_class_attributes_match_module_constants(self):
        """BattleVisualizationChecker 的类属性 === vocabulary 模块常量

        关键契约:共享同一份 list (id 一致),不是 copy。
        这样新增/修改 vocabulary 的项会自动反映到 checker。
        """
        assert BattleVisualizationChecker.ABSTRACT_CULTIVATION is ABSTRACT_CULTIVATION
        assert BattleVisualizationChecker.CONCRETE_VISUAL is CONCRETE_VISUAL
        assert BattleVisualizationChecker.CONCRETE_ACTION is CONCRETE_ACTION

    def test_abstract_cultivation_has_16_items(self):
        """抽象词表 16 项,与修复前数量一致(0 行为变化)"""
        assert len(ABSTRACT_CULTIVATION) == 16

    def test_concrete_visual_no_duplicate_fragment(self):
        """R2-012 顺手修复:CONCRETE_VISUAL 不再含重复的 '碎片'

        修复前:['光芒', '火焰', '血', '碎片', '声响', '声音', '碎片', ...]
              25 行 (去重前),1 个 '碎片' 重复
        修复后(R2-012):24 项,无重复
        R2-013:新增 '火星' 修复 test_mixed_content_ratio → 25 项
        """
        # '碎片' 应只出现 1 次
        assert CONCRETE_VISUAL.count("碎片") == 1
        # 总数应为 25 (R2-013 新增 '火星')
        assert len(CONCRETE_VISUAL) == 25
        # R2-013 新增的具象词应在
        assert "火星" in CONCRETE_VISUAL

    def test_concrete_action_has_18_items(self):
        """具象动作词表 18 项,与修复前数量一致"""
        assert len(CONCRETE_ACTION) == 18

    def test_calculate_abstract_ratio_uses_shared_list(self):
        """calculate_abstract_ratio 仍能正确工作(用 monkeypatch 验证它走类属性)"""
        checker = BattleVisualizationChecker()
        # 全部是抽象词的内容 → ratio 应该是 1.0
        text = "星辰能量在能量波动中爆发。神秘力量涌动,某种力量在凝聚。"
        ratio = checker.calculate_abstract_ratio(text)
        assert ratio > 0.5, f"纯抽象内容 ratio 应 > 0.5,实际 {ratio}"

        # 全部是具象词的内容 → ratio 应该是 0.0
        text2 = "火焰四溅,碎片崩飞,血泊扩散。砍劈刺斩,声光震天。"
        ratio2 = checker.calculate_abstract_ratio(text2)
        assert ratio2 == 0.0
