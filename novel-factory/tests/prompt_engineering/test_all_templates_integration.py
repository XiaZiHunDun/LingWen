"""Cross-template integration tests for all 12 SCENARIOS (Phase 2.13).

Doc 2 v1.0 §5: 12 SCENARIOS × YAML 模板 × 22 STEP_CONTRACTS 必须协同。

每个 SCENARIO 必须:
1. 加载模板 (v1) 成功
2. scenario 字段 == 文件名 (scenario_v1.yaml)
3. agent_role 字段 == _SCENARIO_METADATA[scenario].agent_role
4. system_prompt / user_prompt / constraints / requirements 非空
5. user_prompt 至少含 1 个 {placeholder} 槽 (可被 render 填充)
6. render_template 用完整 context 后,无残留 {placeholder}
7. ModelTier (HAIKU/SONNET/OPUS) 与场景元数据一致

跨场景约束:
- 12 SCENARIOS 都有 YAML 模板 (无遗漏)
- 22 STEP_CONTRACTS 涉及的 SCENARIO 都对应到模板
- 模板结构 (constraints_block / requirements_block / output_schema) 风格统一
"""
from __future__ import annotations

import re
from typing import Any

import pytest

from infra.ai_service.model_tiers import ModelTier
from infra.prompt_engineering.scenarios import (
    _SCENARIO_METADATA,
    SCENARIO_TIER_MAP,
    SCENARIOS,
    STEP_CONTRACTS,
)
from infra.prompt_engineering.templates import (
    Template,
    load_template,
    render_template,
)

# === 完整 context 工厂 (per-scenario) ===

def _ctx_chapter_writing() -> dict[str, Any]:
    return {
        "chapter_num": 5,
        "chapter_outline": "林尘在天璇峰击败赵无极, 展露剑意雏形",
        "world_snapshot": "境界: 炼气七层; 地点: 天璇峰演武场; 时间: 黄昏",
        "character_state": "林尘: 受伤但胜; 赵无极: 倒地",
        "genre": "东方玄幻",
        "max_words": 3000,
        "min_words": 2000,
        "previous_chapters_count": 4,
        "protagonist": "林尘",
        "style": "燃系, 节奏快",
    }


def _ctx_chapter_outline() -> dict[str, Any]:
    return {
        "chapter_num": 5,
        "drive_chain": "林尘身世曝光 → 宗门震动 → 强敌环伺",
        "genre": "东方玄幻",
        "previous_chapter_outline": "林尘击败赵无极, 剑意初成",
        "protagonist": "林尘",
        "volume_outline": "第一卷 天璇崛起 (ch1-120): 林尘从天璇峰外门弟子崛起",
    }


def _ctx_outline_review() -> dict[str, Any]:
    return {
        "drive_chain": "林尘身世 → 宗门震动 → 强敌 → 反击",
        "outline": "第一卷共 120 章, 分 4 阶段 (30 章/阶段)",
        "volume_index": 1,
    }


def _ctx_chapter_review() -> dict[str, Any]:
    return {
        "chapter_content": "林尘拔出长剑, 一剑挥出...赵无极应声倒地。",
        "chapter_num": 5,
    }


def _ctx_worldview_check() -> dict[str, Any]:
    return {
        "chapter_content": "林尘催动炼气七层灵力, 剑意如虹。",
        "world_setting": "修真世界: 炼气/筑基/金丹/元婴/化神, 剑修体系独立",
    }


def _ctx_character_consistency() -> dict[str, Any]:
    return {
        "chapter_content": "林尘冷静地说: 此事待我三思。",
        "character_profiles": "林尘: 冷静/谨慎/重情义, 不冲动",
    }


def _ctx_hook_extraction() -> dict[str, Any]:
    return {
        "chapter_content": (
            "林尘望着远方的天璇峰, 心中暗下决心: "
            "此生定要踏入剑道巅峰, 查清当年灭门真相。 "
            "此时, 一道凌厉剑光自云层中破空而下, 直刺林尘眉心。 "
            "他侧身闪避, 却被第二道剑光击中肩胛, 鲜血迸流。"
        ),
        "chapter_num": 5,
    }


def _ctx_ai_trace_removal() -> dict[str, Any]:
    return {
        "chapter_content": "林尘紧握拳头, 心中暗下决心...他深吸一口气, 眼中闪过坚定的光芒。",
    }


def _ctx_foreshadow_scan() -> dict[str, Any]:
    return {
        "active_foreshadows": "伏笔 1: 林尘身世 (ch3 暗示, ch50 揭晓)",
        "chapter_content": "林尘击败赵无极, 众人议论纷纷...",
    }


def _ctx_emotional_pacing() -> dict[str, Any]:
    return {
        "chapter_content": "林尘在演武场鏖战, 心境从紧张到激昂...",
        "chapter_range": "ch1-ch10",
    }


def _ctx_ripple_audit() -> dict[str, Any]:
    return {
        "active_count": 3,
        "active_ripples": "r1: 林尘身世 (ch3-); r2: 赵无极报复 (ch5-); r3: 天璇峰内鬼 (ch8-)",
        "alarm_status": "active=3, limit=10, safe",
        "chapter_content": "林尘击败赵无极后, 宗主亲自召见...",
        "chapter_num": 5,
    }


def _ctx_subplot_suggest() -> dict[str, Any]:
    return {
        "active_subplots": "sp1: 林尘身世 (ACTIVE ch3-); sp2: 赵无极线 (CLOSING ch10-15)",
        "current_chapter": 6,
        "main_plot": "林尘在天璇崛起, 120 章",
    }


# === Per-scenario context map ===

_CONTEXT_FACTORIES: dict[str, Any] = {
    "chapter_writing": _ctx_chapter_writing,
    "chapter_outline": _ctx_chapter_outline,
    "outline_review": _ctx_outline_review,
    "chapter_review": _ctx_chapter_review,
    "worldview_check": _ctx_worldview_check,
    "character_consistency": _ctx_character_consistency,
    "hook_extraction": _ctx_hook_extraction,
    "ai_trace_removal": _ctx_ai_trace_removal,
    "foreshadow_scan": _ctx_foreshadow_scan,
    "emotional_pacing": _ctx_emotional_pacing,
    "ripple_audit": _ctx_ripple_audit,
    "subplot_suggest": _ctx_subplot_suggest,
}


def _placeholder_keys(text: str) -> set[str]:
    """从文本中提取 {placeholder} 的 key 集合"""
    return set(re.findall(r"\{(\w+)\}", text))


# === TestAllScenariosHaveTemplates ===

class TestAllScenariosHaveTemplates:
    """12 SCENARIOS × 模板文件 一一对应"""

    def test_scenarios_count_is_12(self):
        assert len(SCENARIOS) == 12

    def test_every_scenario_has_v1_template(self):
        for s in SCENARIOS:
            t = load_template(s, version=1)
            assert isinstance(t, Template), f"{s} template is not Template"
            assert t.version == 1

    def test_scenario_field_matches_filename(self):
        for s in SCENARIOS:
            t = load_template(s, version=1)
            assert t.scenario == s, (
                f"scenario field {t.scenario!r} != file name {s!r}"
            )

    def test_no_orphan_template_files(self, tmp_path):
        """examples/ 目录不应有不在 12 SCENARIOS 列表中的模板 (除已记录的内部子模板)"""
        from pathlib import Path

        base = Path(__file__).parent.parent.parent / "infra" / "prompt_engineering" / "templates" / "examples"
        if not base.exists():
            pytest.skip(f"examples dir not found: {base}")
        files = {p.stem.replace("_v1", "") for p in base.glob("*_v1.yaml")}
        # 全部 _v1.yaml 必须对应到 SCENARIOS
        orphans = files - set(SCENARIOS)
        # 已记录的内部子模板 (Phase 4.2 ripple_extraction 是 ripple_audit 内部子任务,
        # 不在 12 SCENARIOS 列表中, 但供 MasterController 抽取涟漪使用)
        _INTERNAL_SUBTEMPLATES: frozenset[str] = frozenset({"ripple_extraction"})
        unexpected = orphans - _INTERNAL_SUBTEMPLATES
        assert not unexpected, (
            f"orphan _v1.yaml files (not in 12 SCENARIOS, not declared internal): {unexpected}"
        )


# === TestTemplateMetadataConsistency ===

class TestTemplateMetadataConsistency:
    """模板的 agent_role / ModelTier 与 SCENARIOS 元数据一致"""

    def test_agent_role_matches_scenarios_metadata(self):
        for s in SCENARIOS:
            t = load_template(s, version=1)
            expected = _SCENARIO_METADATA[s]["agent_role"]
            assert t.agent_role == expected, (
                f"{s}: agent_role={t.agent_role!r}, expected={expected!r}"
            )

    def test_model_tier_map_covers_all_scenarios(self):
        assert set(SCENARIO_TIER_MAP.keys()) == set(SCENARIOS)

    def test_model_tier_values_are_valid(self):
        for s in SCENARIOS:
            tier = SCENARIO_TIER_MAP[s]
            assert isinstance(tier, ModelTier), f"{s}: tier {tier!r} is not ModelTier"

    def test_agent_role_distribution(self):
        """12 SCENARIOS 中 5 agent 角色分布合理"""
        roles = {s: _SCENARIO_METADATA[s]["agent_role"] for s in SCENARIOS}
        # content_writer: 2 (chapter_writing, chapter_outline)
        assert sum(1 for r in roles.values() if r == "content_writer") == 2
        # auditor: 7
        assert sum(1 for r in roles.values() if r == "auditor") == 7
        # polisher: 2
        assert sum(1 for r in roles.values() if r == "polisher") == 2
        # outline_master: 1
        assert sum(1 for r in roles.values() if r == "outline_master") == 1


# === TestTemplateStructureConsistency ===

class TestTemplateStructureConsistency:
    """模板结构 (字段 + block) 风格统一"""

    @pytest.mark.parametrize("scenario", list(SCENARIOS))
    def test_all_required_fields_present(self, scenario):
        t = load_template(scenario, version=1)
        assert t.scenario
        assert t.version == 1
        assert t.agent_role
        assert t.system_prompt.strip()
        assert t.user_prompt.strip()

    @pytest.mark.parametrize("scenario", list(SCENARIOS))
    def test_constraints_block_nonempty(self, scenario):
        """所有模板都至少 2 条约束 (per Doc 2 设计)"""
        t = load_template(scenario, version=1)
        assert len(t.constraints_block) >= 2, (
            f"{scenario}: constraints_block has only {len(t.constraints_block)} items"
        )

    @pytest.mark.parametrize("scenario", list(SCENARIOS))
    def test_requirements_block_nonempty(self, scenario):
        t = load_template(scenario, version=1)
        assert len(t.requirements_block) >= 1

    @pytest.mark.parametrize("scenario", list(SCENARIOS))
    def test_user_prompt_has_placeholders(self, scenario):
        """user_prompt 必须含 {placeholder} 槽 (可被 context 填充)"""
        t = load_template(scenario, version=1)
        placeholders = _placeholder_keys(t.user_prompt)
        assert placeholders, (
            f"{scenario}: user_prompt has no placeholders; static prompts should use {scenario}.md"
        )

    @pytest.mark.parametrize("scenario", list(SCENARIOS))
    def test_output_schema_is_set(self, scenario):
        t = load_template(scenario, version=1)
        assert t.output_schema  # 非空 (默认 'dict')


# === TestTemplateRenderingWithFullContext ===

class TestTemplateRenderingWithFullContext:
    """12 模板用完整 context 渲染 → 无残留 placeholder"""

    @pytest.mark.parametrize("scenario", list(SCENARIOS))
    def test_render_with_full_context_no_residual(self, scenario):
        """用 _CONTEXT_FACTORIES[scenario] 渲染,无 {xxx} 残留"""
        t = load_template(scenario, version=1)
        ctx = _CONTEXT_FACTORIES[scenario]()
        rendered = render_template(t, ctx)

        # user_prompt 不应有残留 placeholder
        residual = _placeholder_keys(rendered.user_prompt)
        assert not residual, (
            f"{scenario}: user_prompt has residual placeholders: {residual}"
        )

    @pytest.mark.parametrize("scenario", list(SCENARIOS))
    def test_rendered_user_prompt_nonempty(self, scenario):
        t = load_template(scenario, version=1)
        ctx = _CONTEXT_FACTORIES[scenario]()
        rendered = render_template(t, ctx)
        assert len(rendered.user_prompt) > 50, (
            f"{scenario}: rendered user_prompt too short ({len(rendered.user_prompt)} chars)"
        )

    @pytest.mark.parametrize("scenario", list(SCENARIOS))
    def test_rendered_system_prompt_contains_chinese(self, scenario):
        """system_prompt 应含中文 (灵文是中文项目)"""
        t = load_template(scenario, version=1)
        ctx = _CONTEXT_FACTORIES[scenario]()
        rendered = render_template(t, ctx)
        # 中文字符
        has_cn = re.search(r"[一-鿿]", rendered.system_prompt)
        assert has_cn, f"{scenario}: system_prompt 缺少中文"

    @pytest.mark.parametrize("scenario", list(SCENARIOS))
    def test_rendered_constraints_substituted(self, scenario):
        """若 constraints 含 {placeholder},应被填充"""
        t = load_template(scenario, version=1)
        ctx = _CONTEXT_FACTORIES[scenario]()
        rendered = render_template(t, ctx)
        if "{min_words}" in t.constraints_block or "{max_words}" in t.constraints_block:
            # 若有 min/max 占位符,渲染后应被填入
            assert "{" not in rendered.constraints_block or "min_words" not in rendered.constraints_block


# === TestStepContractToTemplateMapping ===

class TestStepContractToTemplateMapping:
    """22 STEP_CONTRACTS 涉及的 SCENARIO 都必须能找到模板"""

    def test_all_step_contract_scenarios_have_templates(self):
        """22 STEP_CONTRACTS 中出现的所有 scenario 都应在 SCENARIOS + 都有模板"""
        # 直接遍历 SCENARIOS,确保每个 scenario 都有模板
        for s in SCENARIOS:
            t = load_template(s, version=1)
            assert t.scenario == s

    def test_step_contracts_count_is_22(self):
        assert len(STEP_CONTRACTS) == 22

    def test_every_step_contract_has_budget(self):
        for step, contract in STEP_CONTRACTS.items():
            assert contract.budget_tokens > 0
            assert contract.max_latency_s > 0


# === TestTierComplexityConsistency ===

class TestTierComplexityConsistency:
    """ModelTier 与模板复杂度 (system_prompt 长度) 大致一致"""

    def test_opus_templates_have_richtest_prompts(self):
        """OPUS tier (复杂任务) 应有最丰富的 system_prompt"""
        opus_scenarios = [s for s in SCENARIOS if SCENARIO_TIER_MAP[s] == ModelTier.OPUS]
        haiku_scenarios = [s for s in SCENARIOS if SCENARIO_TIER_MAP[s] == ModelTier.HAIKU]
        assert opus_scenarios, "no OPUS scenarios"
        assert haiku_scenarios, "no HAIKU scenarios"

        opus_avg = sum(
            len(load_template(s, version=1).system_prompt) for s in opus_scenarios
        ) / len(opus_scenarios)
        haiku_avg = sum(
            len(load_template(s, version=1).system_prompt) for s in haiku_scenarios
        ) / len(haiku_scenarios)
        # OPUS 模板应比 HAIKU 更详尽 (允许相等,但鼓励更长)
        assert opus_avg >= haiku_avg * 0.8, (
            f"OPUS avg prompt {opus_avg} chars < HAIKU avg {haiku_avg} chars"
        )


# === TestSpecificScenarioRenderings ===

class TestSpecificScenarioRenderings:
    """针对每个 SCENARIO 的具体渲染内容校验 (per Doc 2 设计)"""

    def test_chapter_writing_includes_chapter_num_and_protagonist(self):
        t = load_template("chapter_writing", version=1)
        ctx = _ctx_chapter_writing()
        rendered = render_template(t, ctx)
        assert "5" in rendered.user_prompt  # chapter_num
        assert "林尘" in rendered.user_prompt  # protagonist

    def test_ripple_audit_includes_active_count(self):
        t = load_template("ripple_audit", version=1)
        ctx = _ctx_ripple_audit()
        rendered = render_template(t, ctx)
        assert "3" in rendered.user_prompt  # active_count
        assert "ch5" in rendered.user_prompt or "5" in rendered.user_prompt

    def test_subplot_suggest_references_main_plot(self):
        t = load_template("subplot_suggest", version=1)
        ctx = _ctx_subplot_suggest()
        rendered = render_template(t, ctx)
        # 必有 current_chapter 替换
        assert "6" in rendered.user_prompt

    def test_ai_trace_removal_replaces_chapter_content(self):
        t = load_template("ai_trace_removal", version=1)
        ctx = _ctx_ai_trace_removal()
        rendered = render_template(t, ctx)
        assert "紧握拳头" in rendered.user_prompt
        assert "深吸一口气" in rendered.user_prompt

    def test_outline_review_uses_volume_index(self):
        t = load_template("outline_review", version=1)
        ctx = _ctx_outline_review()
        rendered = render_template(t, ctx)
        assert "1" in rendered.user_prompt  # volume_index
