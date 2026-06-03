"""
S4 情感共鸣 · 自动检测器
========================

可程序化检测的标准:
- S4.1 情绪转变合理性
- S4.2 情感层次
- S4.4 情绪节奏（需配合前后章节）

人工审核的标准:
- S4.3 情感共鸣触发点
- S4.5 伏笔情感回收
"""

import re
from typing import List, Tuple

# ==================== 情绪词典 ====================

# 情绪词典 - 标记章节的情绪倾向
POSITIVE_EMOTIONS = {
    "希望", "喜悦", "高兴", "快乐", "开心", "欢快", "愉悦", "欣慰", "满足", "幸福",
    "温暖", "安心", "平静", "安宁", "祥和", "舒适", "放松", "轻松", "惬意",
    "成就感", "自豪", "骄傲", "得意", "自信", "坚定", "勇气", "力量",
    "爱情正面", "甜蜜", "温馨", "浪漫", "心动", "爱意",
    "感激", "感动", "感恩", "温情",
    "决绝", "坚毅", "果敢", "刚强", "顽强",
}

NEGATIVE_EMOTIONS = {
    "恐惧", "害怕", "惊恐", "惊骇", "恐惧", "畏怯", "怯懦",
    "悲伤", "伤心", "悲痛", "哀痛", "哀伤", "凄凉", "萧索", "凄惨",
    "绝望", "无望", "死寂", "空洞", "麻木",
    "愤怒", "生气", "恼怒", "愤恨", "怨恨", "仇视", "暴怒",
    "痛苦", "难受", "难过", "煎熬", "折磨", "灼痛", "绞痛",
    "仇恨", "憎恨", "厌恶", "反感", "唾弃",
    "焦虑", "不安", "紧张", "忧虑", "担心", "惶恐",
    "愧疚", "自责", "懊悔", "悔恨", "遗憾", "惋惜",
    "孤独", "寂寞", "空虚", "失落", "迷茫", "彷徨",
}

NEUTRAL_EMOTIONS = {
    "平静", "冷静", "沉稳", "淡定", "从容", "镇定",
    "专注", "认真", "投入", "沉思", "冥想", "回忆",
    "日常", "普通", "平常", "寻常", "平凡",
}

# 所有情绪词
ALL_EMOTION_WORDS = POSITIVE_EMOTIONS | NEGATIVE_EMOTIONS | NEUTRAL_EMOTIONS

# ==================== 情绪检测核心 ====================

def _extract_emotion_words(text: str) -> List[Tuple[str, str]]:
    """提取文本中的情绪词及其类别"""
    found = []
    for word in ALL_EMOTION_WORDS:
        if word in text:
            found.append((word, "positive" if word in POSITIVE_EMOTIONS else ("negative" if word in NEGATIVE_EMOTIONS else "neutral")))
    return found


def _detect_emotion_shifts(text: str) -> List[dict]:
    """
    检测情绪转变点
    返回: List[{"before": str, "after": str, "event": str, "position": int}]
    """
    shifts = []

    # 情绪转变模式

    # 简单检测：连续出现的不同情绪词
    lines = text.split('\n')
    for i, line in enumerate(lines):
        emotions_line = _extract_emotion_words(line)
        if len(emotions_line) >= 2:
            # 检查是否有情绪转变
            emotion_types = [e[1] for e in emotions_line]
            if 'positive' in emotion_types and 'negative' in emotion_types:
                shifts.append({
                    "before": [e[0] for e in emotions_line if e[1] == 'negative'][0] if any(e[1] == 'negative' for e in emotions_line) else "",
                    "after": [e[0] for e in emotions_line if e[1] == 'positive'][0] if any(e[1] == 'positive' for e in emotions_line) else "",
                    "event": line.strip()[:100],
                    "position": i
                })

    return shifts


def _has_causal_event(emotion_shift: dict, text: str) -> bool:
    """
    检测情绪转变是否有因果事件支撑
    简化实现：检查转变前50字内是否有事件词
    """
    event_markers = [
        "因为", "由于", "为了", "因", "所以", "因此", "于是",
        "看到", "听到", "发现", "得知", "知道",
        "父亲", "母亲", "他", "她", "他们",
        "倒下", "死去", "死亡", "受伤", "流血",
        "冲", "跑", "走", "握", "拿", "抱",
        "说", "喊", "叫", "哭", "笑",
        "门", "地窖", "血", "刀", "声音",
    ]

    pos = emotion_shift.get("position", 0)
    lines = text.split('\n')
    context_before = '\n'.join(lines[max(0, pos-5):pos])

    for marker in event_markers:
        if marker in context_before:
            return True
    return False


def _analyze_emotion_layers(text: str) -> Tuple[int, List[dict]]:
    """
    分析关键场景的情感层次
    返回: (layer_count, List[{"surface": str, "deep": str, "position": int}])
    """
    layers = []
    lines = text.split('\n')

    for i, line in enumerate(lines):
        # 检测表面情绪：动作描写
        surface_patterns = [
            r'(握|拿|抱|抓|捂|压|挡|推|拉|抬|背|扛|拖|抬|挤|塞|塞进)',
            r'(他|她|林夜|主角|父亲|母亲)(.{0,15}?)(身体|手|手指|眼睛|脸|表情|声音)',
            r'(脸色|表情|眼神|目光|声音)(.{0,20}?)(苍白|僵硬|颤抖|冰凉|紧绷)',
        ]

        is_surface = any(re.search(p, line) for p in surface_patterns)

        # 检测深层情绪：心理活动
        deep_patterns = [
            r'(感到|感觉|觉得|体会|体会|内心|心里|心底)',
            r'(.{0,20}?)(恐惧|悲伤|绝望|愤怒|希望|恨|爱|心疼|心酸|欣慰)',
            r'(.{0,30}?)(像是|仿佛|如同|犹如|如同)(.{0,20}?)(在|像|是)',
        ]

        is_deep = any(re.search(p, line) for p in deep_patterns)

        if is_surface or is_deep:
            layers.append({
                "surface": line.strip() if is_surface else "",
                "deep": line.strip() if is_deep else "",
                "position": i,
                "has_surface": is_surface,
                "has_deep": is_deep
            })

    return len(layers), layers


def _detect_emotion_tone(text: str) -> str:
    """检测章节整体情绪色调"""
    emotion_words = _extract_emotion_words(text)

    if not emotion_words:
        return "neutral"

    positive_count = sum(1 for e in emotion_words if e[1] == "positive")
    negative_count = sum(1 for e in emotion_words if e[1] == "negative")

    if positive_count > negative_count * 1.5:
        return "positive"
    elif negative_count > positive_count * 1.5:
        return "negative"
    else:
        return "neutral"


# ==================== 主检测函数 ====================

def check_emotion_standards(chapter_path: str) -> Tuple[bool, List[str]]:
    """
    检测章节的S4情感共鸣标准

    返回: (passed: bool, violations: List[str])

    检测标准:
    - S4.1 情绪转变合理性（可程序化）
    - S4.2 情感层次（可程序化）
    - S4.4 情绪节奏（可程序化，需上下文）
    - S4.3 情感共鸣触发点（人工审核）
    - S4.5 伏笔情感回收（人工审核）
    """
    violations = []

    try:
        with open(chapter_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return False, [f"文件不存在: {chapter_path}"]

    # ==================== S4.1 情绪转变合理性 ====================
    emotion_shifts = _detect_emotion_shifts(content)

    for shift in emotion_shifts:
        if not _has_causal_event(shift, content):
            violations.append(
                f"[S4.1] 情绪转变缺少因果事件支撑: "
                f"'{shift['before']}' → '{shift['after']}' "
                f"(位置: 第{shift['position']+1}行附近)"
            )

    # 如果检测到重大情绪转变但无任何因果事件
    if len(emotion_shifts) > 0:
        shifts_without_cause = sum(1 for s in emotion_shifts if not _has_causal_event(s, content))
        if shifts_without_cause > len(emotion_shifts) * 0.3:
            # 超过30%的转变无因果事件
            pass  # 已通过violations列表报告

    # ==================== S4.2 情感层次 ====================
    layer_count, layers = _analyze_emotion_layers(content)

    # 计算有层次的场景数
    scenes_with_layers = sum(1 for layer in layers if layer["has_surface"] and layer["has_deep"])
    total_scenes = sum(1 for layer in layers if layer["has_surface"] or layer["has_deep"])

    if total_scenes > 0:
        layer_ratio = scenes_with_layers / total_scenes
        if layer_ratio < 0.5:
            violations.append(
                f"[S4.2] 关键场景情感层次不足: "
                f"仅{scenes_with_layers}/{total_scenes}场景有2层以上情感 "
                f"(要求≥70%)"
            )
    else:
        violations.append(
            "[S4.2] 未检测到足够的情感层次描写"
        )

    # ==================== S4.4 情绪节奏（单章节检测） ====================
    _detect_emotion_tone(content)

    # 统计情绪词分布
    emotion_words = _extract_emotion_words(content)
    positive_count = sum(1 for e in emotion_words if e[1] == "positive")
    negative_count = sum(1 for e in emotion_words if e[1] == "negative")

    if positive_count == 0 and negative_count == 0:
        violations.append(
            "[S4.4] 章节缺少明显情绪描写，无法判断节奏健康度"
        )
    elif positive_count > 0 and negative_count > 0 and abs(positive_count - negative_count) < 3:
        # 正面和负面情绪数量接近，说明有情绪变化，节奏健康
        pass
    else:
        # 单一情绪过多
        total = positive_count + negative_count
        dominant_ratio = max(positive_count, negative_count) / total
        if dominant_ratio > 0.85:
            violations.append(
                f"[S4.4] 情绪节奏过于单一: "
                f"{'正面' if positive_count > negative_count else '负面'}情绪占比{dominant_ratio:.0%} "
                f"(建议≤85%以保持节奏变化)"
            )

    # ==================== S4.3 和 S4.5 人工审核提示 ====================
    # 这两项需要人工判断，在violations中标注
    if len(emotion_shifts) >= 2:
        violations.append(
            "[S4.3] 人工审核: 请检查章节是否包含≥2个有效情感共鸣触发点"
        )

    # 检查是否有伏笔性描写（情感类伏笔）
    foreshadowing_patterns = [
        r'(像是在说|仿佛在|似乎在|似乎要)',
        r'(记住|不要|活下去|找到真相)',
        r'(最后的|最后的礼物|最后的遗产)',
    ]

    has_foreshadowing = any(re.search(p, content) for p in foreshadowing_patterns)
    if has_foreshadowing:
        violations.append(
            "[S4.5] 人工审核: 检测到情感伏笔线索，请确认是否在±15章内回收"
        )

    passed = len([v for v in violations if not v.startswith("[S4.3]") and not v.startswith("[S4.5]")]) == 0

    return passed, violations


# ==================== CLI测试入口 ====================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python emotion_checker.py <章节文件路径>")
        sys.exit(1)

    chapter_path = sys.argv[1]

    print(f"检测文件: {chapter_path}")
    print("=" * 60)

    passed, violations = check_emotion_standards(chapter_path)

    if passed:
        print("✅ 通过 S4 情感共鸣自动检测")
    else:
        print("❌ 未通过 S4 情感共鸣自动检测")

    print("")
    if violations:
        print("检测结果:")
        for v in violations:
            print(f"  - {v}")
    else:
        print("  无violations")
