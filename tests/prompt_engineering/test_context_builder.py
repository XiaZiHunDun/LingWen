"""Tests for prompt_engineering.context_builder.

Phase 1.3.e — RED tests for ContextBuilder + AutoSummarizer.

设计约束 (per Doc 2 v1.0):
- ContextBuilder: 声明式 I/O pipeline
  - add_source(key, data): 注入数据源
  - build(): 组装 + 预算裁剪 + AutoSummarize → BuiltContext
- AutoSummarizer: 智能摘要
  - 永不删除关键事件、对话、决策
  - 优先级: 时间序列中段 > 非关键角色细节 > 场景描述
- BuiltContext: data dict + total_tokens + transforms_applied list

不实施 (后续阶段):
- LLM 调用的真实实现 (Phase 1.4+ GoT)
- 复杂 transform (e.g. "truncate_2000" — Phase 1.5+)
"""
from __future__ import annotations

import pytest


class _DummyOutput:
    pass


def _ctx(inputs=(), budget_tokens=16000):
    from infra.prompt_engineering.data_structures import PromptContext

    return PromptContext(
        scenario="chapter_writing",
        agent_role="content_writer",
        inputs=inputs,
        output_schema=_DummyOutput,
        budget_tokens=budget_tokens,
    )


class TestContextBuilderBasics:
    def test_build_empty_returns_empty_context(self):
        """无 input 的 ctx → build 后为空 BuiltContext"""
        from infra.prompt_engineering.context_builder import ContextBuilder

        cb = ContextBuilder(_ctx())
        result = cb.build()
        assert result.data == {}
        assert result.total_tokens == 0
        assert result.transforms_applied == []

    def test_add_source_returns_self(self):
        """add_source 返回 self (链式 API)"""
        from infra.prompt_engineering.context_builder import ContextBuilder

        cb = ContextBuilder(_ctx())
        result = cb.add_source("x", "data")
        assert result is cb

    def test_add_source_stores_data(self):
        """add_source 后 build 拿得到"""
        from infra.prompt_engineering.context_builder import ContextBuilder

        ctx = _ctx(inputs=(
            _make_item("a", "src_a", 100),
        ))
        cb = ContextBuilder(ctx).add_source("a", "hello")
        result = cb.build()
        assert result.data["a"] == "hello"
        assert result.total_tokens == 100

    def test_add_multiple_sources(self):
        from infra.prompt_engineering.context_builder import ContextBuilder

        ctx = _ctx(inputs=(
            _make_item("a", "src_a", 50),
            _make_item("b", "src_b", 80),
        ))
        cb = (ContextBuilder(ctx)
              .add_source("a", "alpha")
              .add_source("b", "beta"))
        result = cb.build()
        assert result.data == {"a": "alpha", "b": "beta"}
        assert result.total_tokens == 130


class TestContextBuilderMissingRequired:
    def test_missing_required_raises(self):
        """required=True 但未 add_source → raise"""
        from infra.prompt_engineering.context_builder import ContextBuilder, MissingContextError

        ctx = _ctx(inputs=(
            _make_item("a", "src_a", 100, required=True),
        ))
        cb = ContextBuilder(ctx)
        with pytest.raises(MissingContextError, match="(?i)a"):
            cb.build()

    def test_optional_missing_ok(self):
        """required=False 缺失不 raise,只记 missing_optionals"""
        from infra.prompt_engineering.context_builder import ContextBuilder

        ctx = _ctx(inputs=(
            _make_item("a", "src_a", 100, required=False),
        ))
        cb = ContextBuilder(ctx)
        result = cb.build()
        assert "a" not in result.data
        assert "a" in result.missing_optionals


class TestContextBuilderBudgetOverflow:
    def test_budget_overflow_raises(self):
        """total > budget_tokens → raise"""
        from infra.prompt_engineering.context_builder import BudgetOverflowError, ContextBuilder

        ctx = _ctx(inputs=(
            _make_item("a", "src", 800),
            _make_item("b", "src", 500),
        ), budget_tokens=1000)
        cb = (ContextBuilder(ctx)
              .add_source("a", "x")
              .add_source("b", "y"))
        with pytest.raises(BudgetOverflowError, match="(?i)budget"):
            cb.build()

    def test_budget_within_limit_ok(self):
        from infra.prompt_engineering.context_builder import ContextBuilder

        ctx = _ctx(inputs=(
            _make_item("a", "src", 400),
            _make_item("b", "src", 500),
        ), budget_tokens=1000)
        cb = (ContextBuilder(ctx)
              .add_source("a", "x")
              .add_source("b", "y"))
        result = cb.build()
        assert result.total_tokens == 900


class TestContextBuilderTransforms:
    def test_summary_transform_truncates(self):
        """transform="summary_500" → 数据被 AutoSummarizer 处理"""
        from infra.prompt_engineering.context_builder import ContextBuilder

        long_text = "X" * 5000  # 5000 chars
        ctx = _ctx(inputs=(
            _make_item("a", "src", 5000, transform="summary_500"),
        ), budget_tokens=16000)
        cb = ContextBuilder(ctx).add_source("a", long_text)
        result = cb.build()
        # summary_500 should be <= 500 chars
        assert len(result.data["a"]) <= 500
        assert "summary_500" in result.transforms_applied

    def test_truncate_transform(self):
        """transform="truncate_200" → 截断到 200 chars"""
        from infra.prompt_engineering.context_builder import ContextBuilder

        long_text = "Y" * 2000
        ctx = _ctx(inputs=(
            _make_item("a", "src", 2000, transform="truncate_200"),
        ), budget_tokens=16000)
        cb = ContextBuilder(ctx).add_source("a", long_text)
        result = cb.build()
        assert len(result.data["a"]) <= 200
        assert "truncate_200" in result.transforms_applied

    def test_no_transform_passthrough(self):
        """无 transform → 原样"""
        from infra.prompt_engineering.context_builder import ContextBuilder

        ctx = _ctx(inputs=(
            _make_item("a", "src", 100, transform=None),
        ), budget_tokens=16000)
        cb = ContextBuilder(ctx).add_source("a", "data")
        result = cb.build()
        assert result.data["a"] == "data"

    def test_unknown_transform_passthrough(self):
        """未知 transform → 不报错,原样输出,记入 transforms_applied"""
        from infra.prompt_engineering.context_builder import ContextBuilder

        ctx = _ctx(inputs=(
            _make_item("a", "src", 100, transform="unknown_strategy"),
        ), budget_tokens=16000)
        cb = ContextBuilder(ctx).add_source("a", "data")
        result = cb.build()
        assert result.data["a"] == "data"
        assert "unknown_strategy" in result.transforms_applied


class TestAutoSummarizer:
    def test_summarize_keeps_key_events(self):
        """关键事件标记的段落必须保留"""
        from infra.prompt_engineering.context_builder import AutoSummarizer

        text = (
            "[KEY_EVENT] 林尘突破到筑基期\n"
            "这是中间一些填充文字..." * 20 + "\n"
            "[KEY_DIALOGUE] 林尘: 我一定要报仇!"
        )
        s = AutoSummarizer()
        result = s.summarize(text, target_chars=50)
        assert "[KEY_EVENT]" in result
        assert "[KEY_DIALOGUE]" in result

    def test_summarize_pure_length(self):
        """无 key 标记 → 简单截断"""
        from infra.prompt_engineering.context_builder import AutoSummarizer

        text = "X" * 1000
        s = AutoSummarizer()
        result = s.summarize(text, target_chars=100)
        # 100 chars + 关键标记 → 接近 100
        assert len(result) <= 100 + 50  # 加 buffer

    def test_summarize_short_text_unchanged(self):
        """短文本不应被截断"""
        from infra.prompt_engineering.context_builder import AutoSummarizer

        text = "短文本"
        s = AutoSummarizer()
        result = s.summarize(text, target_chars=1000)
        assert result == text


class TestBuiltContext:
    def test_built_context_fields(self):
        """BuiltContext 字段: data, total_tokens, transforms_applied, missing_optionals"""
        from infra.prompt_engineering.context_builder import ContextBuilder

        ctx = _ctx(inputs=(
            _make_item("a", "src", 50, transform="truncate_100"),
        ), budget_tokens=1000)
        cb = (ContextBuilder(ctx)
              .add_source("a", "data"))
        result = cb.build()
        assert isinstance(result.data, dict)
        assert isinstance(result.total_tokens, int)
        assert isinstance(result.transforms_applied, list)
        assert isinstance(result.missing_optionals, list)


def _make_item(key: str, source: str, tokens: int, **kwargs):
    from infra.prompt_engineering.data_structures import ContextItem

    defaults = dict(key=key, source=source, token_estimate=tokens)
    defaults.update(kwargs)
    return ContextItem(**defaults)
