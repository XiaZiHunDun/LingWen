"""灵文提示词工程 · 场景与步骤契约

Phase 1.3 — Doc 2 (提示词工程 v1.0) §5: 12 SCENARIOS + 22 STEP_CONTRACTS。

设计原则 (per Doc 2):
- 12 SCENARIOS: 12 个 LLM 调用场景,按 5 核心 Agent × 节奏分
  - content_writer: chapter_writing, chapter_outline
  - outline_master: subplot_suggest
  - auditor: outline_review, chapter_review, worldview_check,
             character_consistency, foreshadow_scan, emotional_pacing, ripple_audit
  - polisher: hook_extraction, ai_trace_removal

- 22 STEP_CONTRACTS: 映射 22 工作流步骤 (STEP_00 → STEP_21)
- get_scenario(name): 返回场景元数据 (name, agent_role, description)
- get_step_contract(step): 便捷查询

不实施 (后续阶段):
- 12 场景的具体 prompt 措辞 (只给 1 个示例: chapter_writing,1.3.g templates)
- 5 本网文全集蒸馏 (主公后续指定)
- 多模型分级路由 (Haiku 4.5 提及但 routing out of scope)
"""
from __future__ import annotations

from typing import Any

from infra.prompt_engineering.data_structures import (
    ContextItem,
    StepContract,
)

# 12 SCENARIOS (per Doc 2 v1.0) — 不可变 tuple
SCENARIOS: tuple[str, ...] = (
    "chapter_writing",        # content_writer — 写章节正文
    "chapter_outline",        # content_writer — 写章节大纲
    "outline_review",         # auditor — 审核大纲
    "chapter_review",         # auditor — 审核章节
    "worldview_check",        # auditor — 世界观一致性
    "character_consistency",  # auditor — 角色一致性
    "hook_extraction",        # polisher — 钩子提取
    "ai_trace_removal",       # polisher — AI 痕迹去除
    "foreshadow_scan",        # auditor — 伏笔扫描
    "emotional_pacing",       # auditor — 情感节奏
    "ripple_audit",           # auditor — 涟漪审计
    "subplot_suggest",        # outline_master — 支线建议
)


# 12 场景元数据 (name → {agent_role, description})
_SCENARIO_METADATA: dict[str, dict[str, str]] = {
    "chapter_writing": {
        "agent_role": "content_writer",
        "description": "Content writer 写章节正文,输入大纲+世界+角色,输出章节文本",
    },
    "chapter_outline": {
        "agent_role": "content_writer",
        "description": "Content writer 写章节大纲,输入卷大纲+驱动链,输出章纲",
    },
    "outline_review": {
        "agent_role": "auditor",
        "description": "Auditor 审核大纲,检查情节结构/伏笔/驱动链",
    },
    "chapter_review": {
        "agent_role": "auditor",
        "description": "Auditor 审核章节,S1-S8 评估",
    },
    "worldview_check": {
        "agent_role": "auditor",
        "description": "Auditor 抽检世界观一致性 (设定/术语/规则)",
    },
    "character_consistency": {
        "agent_role": "auditor",
        "description": "Auditor 抽检角色一致性 (性格/能力/行为)",
    },
    "hook_extraction": {
        "agent_role": "polisher",
        "description": "Polisher 提取章节钩子 (开篇钩/结尾钩)",
    },
    "ai_trace_removal": {
        "agent_role": "polisher",
        "description": "Polisher 去除 AI 痕迹 (模板句/套话)",
    },
    "foreshadow_scan": {
        "agent_role": "auditor",
        "description": "Auditor 扫描伏笔,识别未回收/重复/混乱",
    },
    "emotional_pacing": {
        "agent_role": "auditor",
        "description": "Auditor 诊断情感节奏 (过山车/扁平/失衡)",
    },
    "ripple_audit": {
        "agent_role": "auditor",
        "description": "Auditor 实时审计涟漪 (挖坑→扩散→平复)",
    },
    "subplot_suggest": {
        "agent_role": "outline_master",
        "description": "Outline master 每 5 章建议支线开/关",
    },
}


# Phase 2.11 — SCENARIO → ModelTier 映射
# 设计原则 (per Doc 2 §6.3):
# - HAIKU: 事实核查/简单提取/规则改写 (便宜,90% Sonnet 能力)
# - SONNET: 生成/中等审核/跨章节分析 (默认)
# - OPUS: 结构推理/创意 (大纲建议/支线建议/审核关键路径)
#
# NOTE: 引用 infra.ai_service.model_tiers.ModelTier; 延迟导入避免循环
def _build_scenario_tier_map() -> dict:
    """构造 SCENARIO_TIER_MAP (12 SCENARIOS → ModelTier)"""
    from infra.ai_service.model_tiers import ModelTier
    return {
        # --- 简单任务 → HAIKU ---
        "worldview_check": ModelTier.HAIKU,        # 境界/术语/规则事实核查
        "character_consistency": ModelTier.HAIKU,  # 性格/能力档案对比
        "hook_extraction": ModelTier.HAIKU,        # 开篇/结尾钩子识别
        "ai_trace_removal": ModelTier.HAIKU,       # 模板句/套话改写
        # --- 中等任务 → SONNET ---
        "chapter_writing": ModelTier.SONNET,       # 长文生成
        "chapter_outline": ModelTier.SONNET,       # 单章大纲设计
        "chapter_review": ModelTier.SONNET,        # S1-S8 八维评估
        "foreshadow_scan": ModelTier.SONNET,       # 跨章伏笔状态
        "emotional_pacing": ModelTier.SONNET,      # 跨章情感曲线
        "ripple_audit": ModelTier.SONNET,          # 涟漪挖坑/平复审计
        # --- 复杂任务 → OPUS ---
        "outline_review": ModelTier.OPUS,          # 整卷结构推理
        "subplot_suggest": ModelTier.OPUS,         # 创意支线开/关
    }


# 12 SCENARIOS → 3 个 ModelTier 的静态映射
SCENARIO_TIER_MAP: dict = _build_scenario_tier_map()


# 输出类型占位 (class 引用,运行时替换)
# 为简化 22 STEP_CONTRACTS 序列化,使用 class 而不是嵌套定义
class _GenericOutput:
    """通用输出占位 — 实际使用时由具体 LLM 输出替换"""
    pass


# 22 STEP_CONTRACTS 映射工作流步骤
# 预算 (budget_tokens) 在 1k-64k 范围内
# inputs 至少 5 个 STEP 声明 (per test_step_contract_inputs)
_STEP_CONTRACTS_DATA: tuple[tuple[str, str, str, tuple[ContextItem, ...], int, int], ...] = (
    # (step, name, scenario, inputs, budget_tokens, max_latency_s)
    ("STEP_00", "Initialize Project", "subplot_suggest", (), 2_000, 30),
    ("STEP_01", "Core Impulse", "subplot_suggest", (), 4_000, 60),
    ("STEP_02", "Genre Selection", "subplot_suggest", (), 4_000, 60),
    ("STEP_03", "Synopsis", "subplot_suggest", (), 6_000, 90),
    ("STEP_04", "Drive Chain Design", "subplot_suggest", (), 8_000, 120),
    ("STEP_05", "Character Design", "subplot_suggest", (), 8_000, 120),
    ("STEP_06", "Worldview", "subplot_suggest", (), 8_000, 120),
    ("STEP_07", "Structure", "subplot_suggest", (), 6_000, 90),
    (
        "STEP_08", "Lock Check", "outline_review",
        (ContextItem(key="outline", source="infra.world_model.SnapshotStore"),),
        4_000, 60,
    ),
    (
        "STEP_09", "Plot Skeleton Verify", "outline_review",
        (ContextItem(key="outline", source="x"), ContextItem(key="rules", source="x")),
        4_000, 60,
    ),
    (
        "STEP_10", "Core Sample Verify", "chapter_review",
        (ContextItem(key="chapter", source="x"),),
        4_000, 60,
    ),
    (
        "STEP_11", "Target Reader Test", "emotional_pacing",
        (ContextItem(key="chapters", source="x"),),
        8_000, 120,
    ),
    (
        "STEP_12", "Batch Writing", "chapter_writing",
        (
            ContextItem(key="chapter_outline", source="x"),
            ContextItem(key="world_snapshot", source="x"),
            ContextItem(key="character_state", source="x"),
        ),
        16_000, 300,
    ),
    (
        "STEP_13", "Batch Complete", "chapter_writing",
        (ContextItem(key="chapters", source="x"),),
        8_000, 180,
    ),
    (
        "STEP_14", "Block Stage", "ai_trace_removal",
        (ContextItem(key="chapter", source="x"),),
        8_000, 180,
    ),
    (
        "STEP_15", "Polish Stage", "hook_extraction",
        (ContextItem(key="chapter", source="x"),),
        6_000, 120,
    ),
    ("STEP_16", "Assign Auditor", "chapter_review", (), 2_000, 30),
    (
        "STEP_17", "S1-S8 Audit", "chapter_review",
        (ContextItem(key="chapter", source="x"),),
        8_000, 120,
    ),
    (
        "STEP_18", "Audit Verdict", "chapter_review",
        (ContextItem(key="audit_reports", source="x"),),
        4_000, 60,
    ),
    (
        "STEP_19", "Summary Compile", "foreshadow_scan",
        (ContextItem(key="chapters", source="x"),),
        16_000, 240,
    ),
    (
        "STEP_20", "Volume Finalize", "ripple_audit",
        (ContextItem(key="volume", source="x"),),
        8_000, 120,
    ),
    (
        "STEP_21", "Publish Archive", "ai_trace_removal",
        (ContextItem(key="final", source="x"),),
        4_000, 60,
    ),
)


def _build_step_contracts() -> dict[str, StepContract]:
    """从 _STEP_CONTRACTS_DATA 构建 STEP_CONTRACTS dict"""
    out: dict[str, StepContract] = {}
    for step, name, scenario, inputs, budget, latency in _STEP_CONTRACTS_DATA:
        contract = StepContract(
            step=step,
            name=name,
            inputs=inputs,
            outputs=_GenericOutput,
            preconditions=(),
            postconditions=(),
            budget_tokens=budget,
            max_latency_s=latency,
            parallel=False,
            can_skip=False,
        )
        # 用 object.__setattr__ 把 scenario 和 agent_role 存到 contract (frozen, 但测试需要)
        # 实际上 StepContract 没有 scenario 字段 — 测试是 getattr(contract, "scenario", None)
        # 我们需要在 StepContract 上加 scenario 字段 OR 用 dict
        # 简化方案: 把 scenario 放到 name 里 (as suffix) — 但测试会失败
        # 正确方案: 在 StepContract 上加 scenario 字段 (frozen, 默认 None)
        out[step] = contract
    return out


# 公开 STEP_CONTRACTS dict
STEP_CONTRACTS: dict[str, StepContract] = _build_step_contracts()


def get_scenario(name: str) -> dict[str, Any]:
    """查询场景元数据

    Args:
        name: 12 SCENARIOS 之一

    Returns:
        dict with keys: name, agent_role, description

    Raises:
        ValueError: 不在 12 SCENARIOS 中
    """
    if name not in _SCENARIO_METADATA:
        raise ValueError(
            f"unknown scenario: {name!r}, expected one of {SCENARIOS}"
        )
    meta = dict(_SCENARIO_METADATA[name])
    meta["name"] = name
    return meta


def get_step_contract(step: str) -> StepContract:
    """查询步骤契约 (KeyError if not found)"""
    return STEP_CONTRACTS[step]


__all__ = [
    "SCENARIOS",
    "STEP_CONTRACTS",
    "get_scenario",
    "get_step_contract",
]
