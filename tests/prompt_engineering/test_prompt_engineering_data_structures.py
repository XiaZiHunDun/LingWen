"""Tests for prompt_engineering.data_structures.

Phase 1.3.a — RED tests for PromptContext + ContextItem + StepContract.

设计约束 (per Doc 2 v1.0):
- ContextItem: key + source + required + token_estimate + transform
- StepContract: step + name + inputs + outputs + pre/postconditions + budget_tokens + max_latency_s + parallel + can_skip
- PromptContext: scenario + agent_role + inputs + output_schema + temperature + max_tokens + budget_tokens
- 全部 frozen (dataclass(frozen=True))
- JSON 序列化 (to_dict / from_dict) — 不含 output_schema 类的运行时引用
- token 预算字段为 int
"""
from __future__ import annotations

import dataclasses

import pytest


class TestContextItem:
    def test_minimal_context_item(self):
        """最小 ContextItem 只需 key + source"""
        from infra.prompt_engineering.data_structures import ContextItem

        item = ContextItem(key="world_snapshot", source="infra.world_model.WorldSnapshot")
        assert item.key == "world_snapshot"
        assert item.source == "infra.world_model.WorldSnapshot"
        # 默认
        assert item.required is True
        assert item.token_estimate == 0
        assert item.transform is None

    def test_context_item_with_transform(self):
        """transform 是可选的字符串 (e.g. "summary_500", "truncate_2000")"""
        from infra.prompt_engineering.data_structures import ContextItem

        item = ContextItem(
            key="chapter_history",
            source="infra.world_model.SnapshotStore",
            token_estimate=2000,
            transform="summary_500",
        )
        assert item.transform == "summary_500"
        assert item.token_estimate == 2000

    def test_context_item_is_frozen(self):
        from infra.prompt_engineering.data_structures import ContextItem

        item = ContextItem(key="x", source="y")
        with pytest.raises(dataclasses.FrozenInstanceError):
            item.key = "z"  # type: ignore[misc]

    def test_context_item_to_dict(self):
        from infra.prompt_engineering.data_structures import ContextItem

        item = ContextItem(key="x", source="y", token_estimate=100, transform="truncate_500")
        d = item.to_dict()
        assert d == {
            "key": "x",
            "source": "y",
            "required": True,
            "token_estimate": 100,
            "transform": "truncate_500",
        }

    def test_context_item_from_dict(self):
        from infra.prompt_engineering.data_structures import ContextItem

        d = {"key": "x", "source": "y", "required": False, "token_estimate": 50, "transform": None}
        item = ContextItem.from_dict(d)
        assert item.key == "x"
        assert item.required is False
        assert item.transform is None

    def test_context_item_equality(self):
        from infra.prompt_engineering.data_structures import ContextItem

        a = ContextItem(key="x", source="y")
        b = ContextItem(key="x", source="y")
        assert a == b


class TestStepContract:
    def test_minimal_step_contract(self):
        """最小 StepContract: step + name + outputs (class 引用)"""
        from infra.prompt_engineering.data_structures import StepContract

        class Output:
            pass

        contract = StepContract(
            step="STEP_01",
            name="Generate Outline",
            outputs=Output,
        )
        assert contract.step == "STEP_01"
        assert contract.name == "Generate Outline"
        assert contract.outputs is Output
        # 默认
        assert contract.inputs == ()
        assert contract.preconditions == ()
        assert contract.postconditions == ()
        assert contract.budget_tokens == 0
        assert contract.max_latency_s == 60
        assert contract.parallel is False
        assert contract.can_skip is False

    def test_step_contract_with_inputs(self):
        from infra.prompt_engineering.data_structures import ContextItem, StepContract

        class Out:
            pass

        inputs = (
            ContextItem(key="world", source="x"),
            ContextItem(key="character", source="y"),
        )
        contract = StepContract(
            step="STEP_02",
            name="Write",
            inputs=inputs,
            outputs=Out,
            preconditions=("world.ready",),
            postconditions=("chapter.emitted",),
            budget_tokens=8000,
            max_latency_s=120,
            parallel=True,
            can_skip=True,
        )
        assert len(contract.inputs) == 2
        assert contract.preconditions == ("world.ready",)
        assert contract.budget_tokens == 8000
        assert contract.parallel is True
        assert contract.can_skip is True

    def test_step_contract_is_frozen(self):
        from infra.prompt_engineering.data_structures import StepContract

        class Out:
            pass

        c = StepContract(step="S", name="n", outputs=Out)
        with pytest.raises(dataclasses.FrozenInstanceError):
            c.step = "X"  # type: ignore[misc]

    def test_step_contract_to_dict(self):
        """to_dict 不序列化 outputs (class 引用) — 留给运行时校验"""
        from infra.prompt_engineering.data_structures import ContextItem, StepContract

        class Out:
            pass

        c = StepContract(
            step="STEP_01",
            name="Test",
            inputs=(ContextItem(key="x", source="y"),),
            outputs=Out,
            budget_tokens=1000,
        )
        d = c.to_dict()
        # outputs 是 class 引用,应转为 None 或忽略
        assert d["step"] == "STEP_01"
        assert d["name"] == "Test"
        assert d["budget_tokens"] == 1000
        assert d["max_latency_s"] == 60
        assert d["parallel"] is False
        assert d["can_skip"] is False
        # outputs 字段不存在或为 None
        assert d.get("outputs", None) is None
        # inputs 列表
        assert len(d["inputs"]) == 1
        assert d["inputs"][0]["key"] == "x"


class TestPromptContext:
    def test_minimal_prompt_context(self):
        """最小 PromptContext: scenario + agent_role + output_schema"""
        from infra.prompt_engineering.data_structures import PromptContext

        class Out:
            pass

        ctx = PromptContext(
            scenario="chapter_writing",
            agent_role="content_writer",
            output_schema=Out,
        )
        assert ctx.scenario == "chapter_writing"
        assert ctx.agent_role == "content_writer"
        assert ctx.output_schema is Out
        # 默认
        assert ctx.inputs == ()
        assert ctx.temperature == 0.7
        assert ctx.max_tokens == 4096
        assert ctx.budget_tokens == 16000

    def test_prompt_context_with_inputs(self):
        from infra.prompt_engineering.data_structures import ContextItem, PromptContext

        class Out:
            pass

        ctx = PromptContext(
            scenario="chapter_writing",
            agent_role="content_writer",
            inputs=(ContextItem(key="x", source="y"),),
            output_schema=Out,
            temperature=0.9,
            max_tokens=8192,
            budget_tokens=32000,
        )
        assert len(ctx.inputs) == 1
        assert ctx.temperature == 0.9
        assert ctx.max_tokens == 8192
        assert ctx.budget_tokens == 32000

    def test_prompt_context_is_frozen(self):
        from infra.prompt_engineering.data_structures import PromptContext

        class Out:
            pass

        ctx = PromptContext(scenario="x", agent_role="y", output_schema=Out)
        with pytest.raises(dataclasses.FrozenInstanceError):
            ctx.scenario = "z"  # type: ignore[misc]

    def test_prompt_context_to_dict(self):
        from infra.prompt_engineering.data_structures import ContextItem, PromptContext

        class Out:
            pass

        ctx = PromptContext(
            scenario="chapter_writing",
            agent_role="content_writer",
            inputs=(ContextItem(key="x", source="y"),),
            output_schema=Out,
        )
        d = ctx.to_dict()
        assert d["scenario"] == "chapter_writing"
        assert d["agent_role"] == "content_writer"
        assert d["temperature"] == 0.7
        assert d["max_tokens"] == 4096
        assert d["budget_tokens"] == 16000
        # output_schema 不序列化 (class 引用)
        assert d.get("output_schema", None) is None

    def test_prompt_context_inputs_total_tokens(self):
        """辅助方法: 计算 inputs 总 token 估计"""
        from infra.prompt_engineering.data_structures import ContextItem, PromptContext

        class Out:
            pass

        ctx = PromptContext(
            scenario="x",
            agent_role="y",
            output_schema=Out,
            inputs=(
                ContextItem(key="a", source="x", token_estimate=100),
                ContextItem(key="b", source="x", token_estimate=200),
            ),
        )
        assert ctx.total_input_tokens() == 300

    def test_prompt_context_under_budget_check(self):
        """辅助方法: 检查 inputs 是否在 budget 内"""
        from infra.prompt_engineering.data_structures import ContextItem, PromptContext

        class Out:
            pass

        ctx = PromptContext(
            scenario="x",
            agent_role="y",
            output_schema=Out,
            budget_tokens=1000,
            inputs=(
                ContextItem(key="a", source="x", token_estimate=500),
                ContextItem(key="b", source="x", token_estimate=400),
            ),
        )
        # 900 < 1000 → OK
        assert ctx.fits_budget() is True

    def test_prompt_context_over_budget_check(self):
        from infra.prompt_engineering.data_structures import ContextItem, PromptContext

        class Out:
            pass

        ctx = PromptContext(
            scenario="x",
            agent_role="y",
            output_schema=Out,
            budget_tokens=500,
            inputs=(
                ContextItem(key="a", source="x", token_estimate=400),
                ContextItem(key="b", source="x", token_estimate=300),
            ),
        )
        # 700 > 500 → 超
        assert ctx.fits_budget() is False


class TestContextItemUniqueKey:
    """ContextItem 验证: key 必填,不允许空白"""

    def test_empty_key_raises(self):
        from infra.prompt_engineering.data_structures import ContextItem

        with pytest.raises(ValueError, match="key"):
            ContextItem(key="", source="y")

    def test_whitespace_key_raises(self):
        from infra.prompt_engineering.data_structures import ContextItem

        with pytest.raises(ValueError, match="key"):
            ContextItem(key="   ", source="y")

    def test_empty_source_raises(self):
        from infra.prompt_engineering.data_structures import ContextItem

        with pytest.raises(ValueError, match="source"):
            ContextItem(key="x", source="")
