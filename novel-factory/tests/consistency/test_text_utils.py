"""R2-011: split_chinese_sentences 行为测试 + 等价性回归"""
from infra.consistency.checkers.text_utils import split_chinese_sentences


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
