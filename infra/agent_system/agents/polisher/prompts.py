# novel-factory/agent_system/agents/polisher/prompts.py
"""润色师提示词模板 (Phase 7.2)

3 组模板, 每组 1 个 builder + 1 个 system prompt:
- polish: 主入口 (聚合视角) — 暂未使用, 保留供后续 phase
- dialogue: 对话自然化
- pacing: 节奏调整

每个 builder 接受 content + reader_id, 返回组装好的 prompt 字符串。
reader_id 用于个性化 (默认 'A' = 悬念铺设专长读者)。
"""
from typing import Optional

try:
    from .variant_loader import get_variant_loader
    VARIANT_LOADER_AVAILABLE = True
except ImportError:
    VARIANT_LOADER_AVAILABLE = False


def _load_variant_enhancement(reader_id: str, max_enhancements: int = 3) -> str:
    """从 reader 变体配置加载 prompt 增强片段

    防御性: variant_loader 失败时返回空字符串, 不阻塞主流程。
    """
    if not VARIANT_LOADER_AVAILABLE:
        return ""
    try:
        loader = get_variant_loader()
        variant = loader.get_variant(reader_id)
    except Exception:
        return ""

    if not variant:
        return ""

    parts: list[str] = []
    enhancements = variant.get("feedback_preference", {}).get("focus_areas", [])
    if enhancements:
        parts.append(
            f"读者 {reader_id} 关注领域: {', '.join(enhancements[:max_enhancements])}"
        )
    style = variant.get("style_expertise", {})
    if style:
        primary = style.get("primary", "")
        if primary:
            parts.append(f"读者 {reader_id} 专长: {primary}")
    return "\n".join(parts)


# ==================== Dialogue ====================

def build_dialogue_prompt(content: str, reader_id: str = "A") -> str:
    """构建对话优化提示"""
    enhancement = _load_variant_enhancement(reader_id)
    enhancement_block = f"\n{enhancement}\n" if enhancement else ""
    return f"""请优化以下章节中的对话, 使其更自然、更符合角色性格。

{enhancement_block}
## 原文
{content[:3000]}

## 要求
1. 保持原意和情节不变
2. 让对话更口语化、自然
3. 角色性格保持一致
4. 去除机械/AI 感

请直接返回优化后的全文 (不要解释)。"""


def get_dialogue_system_prompt(reader_id: str = "A") -> str:
    """对话优化系统提示"""
    return f"""你是一位资深网文编辑 (读者 {reader_id} 号视角), 擅长对话润色。
你的工作: 让对话更自然、更有"人味", 去除 AI 痕迹, 保持原作意图。
不要改变情节或角色行为, 只调整语言风格。直接返回润色后全文。"""


# ==================== Pacing ====================

def build_pacing_prompt(content: str, reader_id: str = "A") -> str:
    """构建节奏调整提示"""
    enhancement = _load_variant_enhancement(reader_id)
    enhancement_block = f"\n{enhancement}\n" if enhancement else ""
    return f"""请调整以下章节的节奏, 使其更有张力。

{enhancement_block}
## 原文
{content[:3000]}

## 要求
1. 保持原意和情节不变
2. 调整段落长度 (高潮紧凑 / 过渡舒缓)
3. 加强关键场景的冲击
4. 减少拖沓的过渡段

请直接返回调整后的全文 (不要解释)。"""


def get_pacing_system_prompt(reader_id: str = "A") -> str:
    """节奏调整系统提示"""
    return f"""你是一位资深网文编辑 (读者 {reader_id} 号视角), 擅长节奏控制。
你的工作: 调整章节节奏, 让高潮有力、过渡自然、张弛有度。
保持情节不变, 只调整段落长度和叙述密度。直接返回调整后全文。"""


# ==================== Merge Synthesis (Phase 7.5) ====================

_S1_S8_NAMES = {
    "S1": "剧情完整性 (Plot Completeness)",
    "S2": "逻辑自洽 (Logic Consistency)",
    "S3": "文笔风格 (Writing Style)",
    "S4": "情感共鸣 (Emotional Resonance)",
    "S5": "节奏控制 (Pacing Control)",
    "S6": "可读性 (Readability)",
    "S7": "主角魅力 (Protagonist Appeal)",
    "S8": "人物弧光 (Character Arc)",
}

_MERGE_SYNTHESIS_TRUNCATE = 6000  # Phase 8.1: 3000→6000 chars (~3000-4000 tokens), HAIKU 4.5 上下文 200k 足够


def build_merge_synthesis_prompt(content_a: str, content_b: str, labels: tuple[str, str] = ("A", "B")) -> str:
    """Phase 7.5 + 8.1: 构建 polish_merge S1-S8 多维评分 prompt

    把 2 个润色 variant 给 LLM, 按 S1-S8 8 维打分 (0-10), 选总平均分高者。
    label 参数允许上游节点用 input id (e.g. "polish_emotional_pacing") 当 label,
    JSON key 用 sanitized label (Phase 8.1: 防御性 normalize 非 [a-zA-Z0-9_] 字符).
    """
    from infra.agent_system.master_controller import _safe_label  # Phase 8.1

    label_a, label_b = labels
    safe_a, safe_b = _safe_label(label_a), _safe_label(label_b)
    s1_s8_list = "\n".join(f"- {k}: {v}" for k, v in _S1_S8_NAMES.items())
    return f"""你是资深网文质量审核官, 需要对比 2 个章节润色 variant, 按 S1-S8 8 维评分 (0-10 分, 越高越好), 并选出优胜者。

## 评分维度
{s1_s8_list}

## Variant {label_a}
{content_a[:_MERGE_SYNTHESIS_TRUNCATE]}

## Variant {label_b}
{content_b[:_MERGE_SYNTHESIS_TRUNCATE]}

## 输出格式 (严格 JSON)
{{
  "scores_{safe_a}": {{"S1": <int>, "S2": <int>, "S3": <int>, "S4": <int>, "S5": <int>, "S6": <int>, "S7": <int>, "S8": <int>}},
  "scores_{safe_b}": {{"S1": <int>, "S2": <int>, "S3": <int>, "S4": <int>, "S5": <int>, "S6": <int>, "S7": <int>, "S8": <int>}},
  "reason": "<50 字以内, 解释为什么选 {label_a} 或 {label_b}>"
}}

只返 JSON, 不要其他文字。"""


def get_merge_synthesis_system_prompt() -> str:
    """Phase 7.5: polish_merge S1-S8 评分系统提示"""
    return """你是一位资深网文质量审核官, 擅长多维度对比 2 个润色版本。
你的工作: 客观评分 S1-S8 8 维, 选总平均分高者。
不要因为 variant 长度或风格偏好而偏袒, 严格按 8 维定义评估。"""
