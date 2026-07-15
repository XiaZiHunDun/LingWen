"""Tests for prompt_engineering.scenarios.

Phase 1.3.c — RED tests for 12 SCENARIOS + 22 STEP_CONTRACTS constants.

设计约束 (per Doc 2 v1.0):
- 12 SCENARIOS — 12 个 LLM 调用场景 (按 5 核心 Agent × 节奏分)
- 22 STEP_CONTRACTS — 映射 22 工作流步骤
- 每个 STEP 包含: step, name, scenario (引用 12 个), agent_role, inputs, outputs, pre/postconditions, budget
- SCENARIOS 是不可变 tuple[str, ...]
- STEP_CONTRACTS 是 dict[step, StepContract]
"""
from __future__ import annotations

import pytest

from infra.prompt_engineering.data_structures import (
    ContextItem,
    StepContract,
)
from infra.prompt_engineering.scenarios import (
    SCENARIOS,
    STEP_CONTRACTS,
    get_scenario,
    get_step_contract,
)


class TestScenarios:
    def test_12_scenarios_defined(self):
        """12 个 LLM 调用场景 (per Doc 2)"""
        assert len(SCENARIOS) == 12

    def test_scenarios_exact_names(self):
        """精确场景名 (per Doc 2 v1.0)"""
        assert set(SCENARIOS) == {
            "chapter_writing",
            "chapter_outline",
            "outline_review",
            "chapter_review",
            "worldview_check",
            "character_consistency",
            "hook_extraction",
            "ai_trace_removal",
            "foreshadow_scan",
            "emotional_pacing",
            "ripple_audit",
            "subplot_suggest",
        }

    def test_scenarios_is_tuple(self):
        """SCENARIOS 是不可变 tuple (防止运行时修改)"""
        assert isinstance(SCENARIOS, tuple)

    def test_no_duplicate_scenarios(self):
        assert len(SCENARIOS) == len(set(SCENARIOS))

    def test_get_scenario_valid(self):
        """get_scenario 返回标准化场景元数据"""
        meta = get_scenario("chapter_writing")
        assert meta["name"] == "chapter_writing"
        assert "agent_role" in meta
        assert "description" in meta

    def test_get_scenario_invalid_raises(self):
        with pytest.raises(ValueError, match="(?i)scenario"):
            get_scenario("nonexistent_scenario")


class TestStepContracts:
    def test_22_step_contracts_defined(self):
        """22 STEP_CONTRACTS 映射 22 工作流步骤"""
        assert len(STEP_CONTRACTS) == 22

    def test_step_contracts_keys_format(self):
        """key 是 "STEP_XX" 格式 (XX = 0-21)"""
        for key in STEP_CONTRACTS:
            assert key.startswith("STEP_"), f"key {key!r} not STEP_XX format"
            try:
                n = int(key.split("_")[1])
                assert 0 <= n <= 21
            except (IndexError, ValueError):
                pytest.fail(f"key {key!r} not parseable as STEP_NN")

    def test_all_step_contracts_are_step_contract_instance(self):
        for key, contract in STEP_CONTRACTS.items():
            assert isinstance(contract, StepContract), f"{key} is not StepContract"
            assert contract.step == key

    def test_all_step_contracts_reference_known_scenarios(self):
        """每个 STEP 引用的 scenario 必须在 12 个 SCENARIOS 中"""
        for key, contract in STEP_CONTRACTS.items():
            # contract.scenario (or description) must be in SCENARIOS
            scenario = getattr(contract, "scenario", None)
            if scenario is not None:
                assert scenario in SCENARIOS, f"{key} references unknown scenario {scenario!r}"

    def test_step_contracts_have_non_empty_names(self):
        for key, contract in STEP_CONTRACTS.items():
            assert contract.name, f"{key} has empty name"
            assert isinstance(contract.name, str)

    def test_step_contracts_have_outputs(self):
        """每个 STEP 必须指定 output 类型 (class 引用)"""
        for key, contract in STEP_CONTRACTS.items():
            assert contract.outputs is not None, f"{key} missing outputs"


class TestGetStepContract:
    def test_get_existing_contract(self):
        contract = get_step_contract("STEP_01")
        assert isinstance(contract, StepContract)
        assert contract.step == "STEP_01"

    def test_get_nonexistent_raises(self):
        with pytest.raises(KeyError):
            get_step_contract("STEP_99")


class TestScenarioMetadata:
    def test_scenario_metadata_count_matches(self):
        """get_scenario 返回的元数据应有 12 项 (与 SCENARIOS 一一对应)"""
        for s in SCENARIOS:
            meta = get_scenario(s)
            assert meta["name"] == s

    def test_scenario_metadata_has_agent_role(self):
        for s in SCENARIOS:
            meta = get_scenario(s)
            # agent_role 应该是 5 核心 Agent 之一
            assert meta["agent_role"] in {
                "content_writer", "auditor", "polisher", "outline_master",
                "character_designer",
            }, f"{s} has invalid agent_role {meta['agent_role']!r}"

    def test_scenario_metadata_has_description(self):
        for s in SCENARIOS:
            meta = get_scenario(s)
            assert "description" in meta
            assert isinstance(meta["description"], str)
            assert len(meta["description"]) > 0


class TestStepContractInputs:
    def test_some_steps_have_inputs(self):
        """至少某些 STEP 应该声明 inputs"""
        with_inputs = [k for k, c in STEP_CONTRACTS.items() if len(c.inputs) > 0]
        assert len(with_inputs) >= 5, "expected at least 5 STEPs with inputs"

    def test_step_inputs_are_context_items(self):
        for key, contract in STEP_CONTRACTS.items():
            for inp in contract.inputs:
                assert isinstance(inp, ContextItem), f"{key} input not ContextItem"
                assert inp.key, f"{key} input has empty key"


class TestStepContractBudgets:
    def test_step_budgets_are_positive(self):
        """每个 STEP 应该有合理的 token 预算 (>0)"""
        for key, contract in STEP_CONTRACTS.items():
            assert contract.budget_tokens > 0, f"{key} has zero/negative budget"

    def test_step_budgets_reasonable(self):
        """token 预算应在合理范围 (1k - 64k)"""
        for key, contract in STEP_CONTRACTS.items():
            assert 1_000 <= contract.budget_tokens <= 64_000, (
                f"{key} budget {contract.budget_tokens} outside reasonable range"
            )


class TestStepContractLatency:
    def test_step_max_latency_positive(self):
        for key, contract in STEP_CONTRACTS.items():
            assert contract.max_latency_s > 0, f"{key} has zero/negative max_latency_s"
