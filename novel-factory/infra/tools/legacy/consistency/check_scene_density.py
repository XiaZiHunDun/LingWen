#!/usr/bin/env python3
"""
场景密度检测器 v2.0
检测章节中对话/谈心段落占比，识别重复场景模式，场景类型分类+子维度检测

改进日志：
- v2.0: 新增场景类型分类（战斗/感情/信息/纯叙事）、子维度检测（环境/动作/心理）、
        差异化阈值
"""
import os
import re
import sys
from typing import List, Dict, Tuple
from collections import Counter


# ========== 场景类型定义 ==========

# 1. 战斗/动作场景特征
COMBAT_ACTION_PATTERNS = {
    'action_verbs': [
        r'攻击|闪避|爆发|冲|跑|追|挥|砍|挡|拆|破|裂',
        r'脚步|身影|速度|纵身|翻身|扑向|逼近',
        r'雷光|剑气|拳风|掌风|纳米|机甲|武器',
    ],
}

# 2. 感情对手戏特征
EMOTIONAL_CONFRONTATION_PATTERNS = {
    'psychological_words': [
        r'想|觉得|似乎|仿佛|感到|体会|明白|知道',
        r'心头|心底|心中|意识|直觉|本能',
        r'泪水|眼眶|声音.*颤|轻声',
    ],
    'intimate_gestures': [
        r'看着.*眼睛|握.*手|靠在.*肩|依偎|并肩',
        r'轻声|微微一笑|目光中带着',
    ],
}

# 3. 信息交代场景特征
INFO_EXPOSITION_PATTERNS = {
    'quotative_verbs': [
        r'说|告诉|解释|问道|答道|叹道',
        r'介绍|说明|讲述|提到|指出',
    ],
    'time_span_words': [
        r'年来|年间|之前|之后|从此|那段|那些日子',
        r'从.*到.*|每|总是|经常|通常',
    ],
}

# 环境描写关键词
ENVIRONMENT_WORDS = [
    r'月光|星光|阳光|夜幕|天空|云层|大地|荒野|废墟|建筑|树木',
    r'风.*吹|雾.*弥漫|颜色|光辉|昏暗|明亮|阴影|轮廓',
    r'远处|近处|四周|夜色|晨光|夕阳|黄昏',
]

# 动作描写关键词
ACTION_WORDS = [
    r'走|跑|跳|跃|飞|攀|爬|躺|卧|坐|站|蹲|弯|伸|转|扭|推|拉|按|握|拿',
    r'攻击|防守|闪避|格挡|挥砍|冲刺|爆发|凝聚|释放',
    r'呼吸|心跳|脉搏|血流|肌肉|身体',
]

# 心理描写关键词
PSYCHOLOGICAL_WORDS = [
    r'想|觉得|感到|体会|明白|知道|以为|相信|记得|想起|仿佛',
    r'心头|心中|心底|意识|直觉|本能|灵魂|精神',
    r'恐惧|愤怒|悲伤|喜悦|惊讶|期待|绝望|希望',
]


# 对话密集场景的标记
DIALOGUE_PATTERNS = [
    r'"[^"]{10,}"',
    r'\u201c[^\u201d]{10,}\u201d',
]

# 谈心场景标记（情感交流类）
HEARTHEART_PATTERNS = [
    r'看着.*眼睛',
    r'轻声.*说',
    r'目光中带着',
    r'微微一笑',
    r'握住了.*手',
    r'靠在.*肩',
    r'依偎在',
    r'并肩.*站',
    r'星光.*映',
    r'眼中.*泪光',
]

# 重复场景模式
REPEAT_SCENE_PATTERNS = [
    (r'守夜', r'醒来', r'对话'),
    (r'篝火', r'看星星', r'谈论守护'),
    (r'遇到敌人', r'分析', r'战斗'),
    (r'三寸',),
]


def _count_pattern_matches(content: str, patterns: List[str]) -> int:
    """统计内容中匹配的模式数量"""
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, content))
    return count


def _count_chars_by_patterns(content: str, patterns: List[str]) -> int:
    """统计匹配到的字符总数（避免重复计算同一段文字）"""
    matched_spans = set()
    for pattern in patterns:
        for m in re.finditer(pattern, content):
            matched_spans.add((m.start(), m.end()))
    total_chars = sum(end - start for start, end in matched_spans)
    return total_chars


def _calc_psychological_ratio(content: str) -> float:
    """计算心理描写占比"""
    total_chars = len(content)
    if total_chars == 0:
        return 0.0
    psych_chars = _count_chars_by_patterns(content, PSYCHOLOGICAL_WORDS)
    return psych_chars / total_chars


def classify_scene_type(content: str) -> Tuple[str, float]:
    """
    纯规则场景分类（优先级从高到低）

    Returns:
        (scene_type, confidence)
        scene_type: 'combat_action' | 'emotional_confrontation' | 'info_exposition' | 'pure_narrative' | 'mixed'
        confidence: 0.0-1.0
    """
    combat_score = _count_pattern_matches(content, COMBAT_ACTION_PATTERNS['action_verbs'])
    emotional_score = _count_pattern_matches(content, EMOTIONAL_CONFRONTATION_PATTERNS['psychological_words'])
    info_score = _count_pattern_matches(content, INFO_EXPOSITION_PATTERNS['quotative_verbs'])

    # 计算对话占比
    total_dialogue = 0
    for m in re.finditer(r'\u201c([^\u201d]{10,})\u201d', content):
        total_dialogue += len(m.group(1))
    for m in re.finditer(r'"([^"]{10,})"', content):
        total_dialogue += len(m.group(1))
    dialogue_ratio = total_dialogue / len(content) if len(content) > 0 else 0

    # 计算心理描写占比
    psychological_ratio = _calc_psychological_ratio(content)

    # 决策树分类
    if combat_score > 5 and dialogue_ratio < 0.25:
        return ("combat_action", 0.8)

    if emotional_score > 10 and psychological_ratio > 0.15:
        return ("emotional_confrontation", 0.7)

    time_span_count = _count_pattern_matches(content, INFO_EXPOSITION_PATTERNS['time_span_words'])
    if (info_score > 8 and dialogue_ratio > 0.35 and
            psychological_ratio < 0.15 and time_span_count > 3):
        return ("info_exposition", 0.7)

    if dialogue_ratio < 0.08 and combat_score < 3:
        return ("pure_narrative", 0.6)

    # 计算综合得分判断混合类型
    total_score = combat_score + emotional_score + info_score
    if total_score > 15 and dialogue_ratio > 0.3:
        return ("mixed", 0.5)

    # 默认返回基于主要特征的类型
    if combat_score > emotional_score and combat_score > info_score:
        return ("combat_action", 0.4)
    elif emotional_score > info_score:
        return ("emotional_confrontation", 0.4)
    else:
        return ("info_exposition", 0.4)


def extract_subdimension_ratios(content: str) -> Dict[str, float]:
    """提取场景密度子维度"""
    total_chars = len(content)
    if total_chars == 0:
        return {'env_ratio': 0.0, 'action_ratio': 0.0, 'psych_ratio': 0.0, 'dialogue_ratio': 0.0}

    env_chars = _count_chars_by_patterns(content, ENVIRONMENT_WORDS)
    action_chars = _count_chars_by_patterns(content, ACTION_WORDS)
    psych_chars = _count_chars_by_patterns(content, PSYCHOLOGICAL_WORDS)

    total_dialogue = 0
    for m in re.finditer(r'\u201c([^\u201d]{10,})\u201d', content):
        total_dialogue += len(m.group(1))
    for m in re.finditer(r'"([^"]{10,})"', content):
        total_dialogue += len(m.group(1))
    for m in re.finditer(r'《([^》]{10,})》', content):
        total_dialogue += len(m.group(1))

    return {
        'env_ratio': env_chars / total_chars,
        'action_ratio': action_chars / total_chars,
        'psych_ratio': psych_chars / total_chars,
        'dialogue_ratio': total_dialogue / total_chars,
    }


# 各场景类型的期望范围
SCENE_TYPE_THRESHOLDS = {
    'combat_action': {
        'dialogue_max': 0.30,  # 战斗场景对话应少
        'action_min': 0.15,
        'psych_max': 0.15,
    },
    'emotional_confrontation': {
        'dialogue_max': 0.60,  # 感情戏对话可以高
        'psych_min': 0.12,
        'action_max': 0.15,
    },
    'info_exposition': {
        'dialogue_max': 0.70,  # 信息交代对话偏高正常
        'env_min': 0.08,
        'psych_max': 0.15,
    },
    'pure_narrative': {
        'dialogue_max': 0.10,
        'env_min': 0.10,
    },
    'mixed': {
        'dialogue_max': 0.50,
        'action_min': 0.05,
    },
}

DEFAULT_THRESHOLDS = {
    'dialogue_max': 0.65,
    'action_min': 0.03,
    'psych_min': 0.02,
}


def check_subdimension_health(subdims: dict, scene_type: str) -> List[str]:
    """根据场景类型检测子维度异常"""
    issues = []
    ranges = SCENE_TYPE_THRESHOLDS.get(scene_type, DEFAULT_THRESHOLDS)

    d = subdims

    # 对话占比检查
    if d['dialogue_ratio'] > ranges.get('dialogue_max', 0.65):
        issues.append(f"对话占比{d['dialogue_ratio']:.1%}过高")

    # 动作占比检查
    if 'action_min' in ranges and d['action_ratio'] < ranges['action_min']:
        issues.append(f"动作占比{d['action_ratio']:.1%}过低")

    # 心理占比检查
    if 'psych_min' in ranges and d['psych_ratio'] < ranges['psych_min']:
        issues.append(f"心理描写{d['psych_ratio']:.1%}过低")
    if 'psych_max' in ranges and d['psych_ratio'] > ranges['psych_max']:
        issues.append(f"心理描写{d['psych_ratio']:.1%}过高")

    # 环境占比检查
    if 'env_min' in ranges and d['env_ratio'] < ranges['env_min']:
        issues.append(f"环境描写{d['env_ratio']:.1%}过低")

    return issues


def extract_dialogue_ratio(content: str) -> float:
    """计算对话内容占总字数的比例"""
    total_dialogue = 0
    for m in re.finditer(r'\u201c([^\u201d]{10,})\u201d', content):
        total_dialogue += len(m.group(1))
    for m in re.finditer(r'"([^"]{10,})"', content):
        total_dialogue += len(m.group(1))
    for m in re.finditer(r'《([^》]{10,})》', content):
        total_dialogue += len(m.group(1))

    total_chars = len(content)
    if total_chars == 0:
        return 0.0

    return total_dialogue / total_chars


def extract_heartheart_ratio(content: str) -> float:
    """计算谈心/情感交流场景占总字数的比例"""
    hearttext = 0
    for pattern in HEARTHEART_PATTERNS:
        hearttext += len(re.findall(pattern, content)) * 30

    total_chars = len(content)
    if total_chars == 0:
        return 0.0

    return min(hearttext / total_chars, 1.0)


def detect_repeat_scene_patterns(content: str) -> List[str]:
    """检测是否存在重复场景模式"""
    found = []
    if len(re.findall(r'三寸', content)) >= 2:
        found.append('莫言剑指咽喉闪回（多次出现"三寸"）')

    star_talk_count = len(re.findall(r'星星|星光|星空', content))
    guard_talk_count = len(re.findall(r'守护', content))
    if star_talk_count >= 3 and guard_talk_count >= 3:
        found.append(f"星空谈守护模式（星星{star_talk_count}次、守护{guard_talk_count}次）")

    night_count = len(re.findall(r'守夜|守在|值班', content))
    wake_count = len(re.findall(r'醒来|清晨|天亮', content))
    if night_count >= 2 and wake_count >= 2:
        found.append("守夜-醒来循环模式")

    return found


def check_scene_density(chapters_dir: str,
                        chapter_range: tuple[int, int] = (1, 360),
                        dialogue_threshold: float = 0.65,
                        heartheart_threshold: float = 0.25) -> Dict:
    """
    检测场景密度 v2.0

    Args:
        chapters_dir: 章节目录
        chapter_range: 检查章节范围
        dialogue_threshold: 对话占比阈值（向后兼容）
        heartheart_threshold: 谈心场景占比阈值（向后兼容）

    Returns:
        检测结果字典
    """
    start, end = chapter_range
    results = []
    total_dialogue_ratio = 0
    total_heartheart_ratio = 0
    chapter_count = 0
    scene_type_counts = Counter()

    for i in range(start, end + 1):
        fname = f"ch{i:03d}.md"
        fpath = os.path.join(chapters_dir, fname)

        if not os.path.exists(fpath):
            continue

        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 场景类型分类
        scene_type, confidence = classify_scene_type(content)
        scene_type_counts[scene_type] += 1

        # 子维度提取
        subdims = extract_subdimension_ratios(content)

        dialogue_ratio = subdims['dialogue_ratio']
        heartheart_ratio = extract_heartheart_ratio(content)
        repeat_patterns = detect_repeat_scene_patterns(content)

        total_dialogue_ratio += dialogue_ratio
        total_heartheart_ratio += heartheart_ratio
        chapter_count += 1

        # 获取该场景类型的阈值
        thresholds = SCENE_TYPE_THRESHOLDS.get(scene_type, DEFAULT_THRESHOLDS)

        # 检测问题
        issues = []

        # 对话占比检查（使用场景类型差异化阈值）
        if dialogue_ratio > thresholds.get('dialogue_max', dialogue_threshold):
            issues.append(f"[{scene_type}]对话占比{dialogue_ratio:.1%}过高")

        # 子维度健康检查
        sub_issues = check_subdimension_health(subdims, scene_type)
        issues.extend(sub_issues)

        # 谈心阈值（向后兼容）
        if heartheart_ratio > heartheart_threshold:
            issues.append(f"谈心场景{heartheart_ratio:.1%}过高")

        for pat in repeat_patterns:
            issues.append(pat)

        results.append({
            'chapter': i,
            'scene_type': scene_type,
            'scene_type_confidence': confidence,
            'dialogue_ratio': dialogue_ratio,
            'heartheart_ratio': heartheart_ratio,
            'subdimensions': subdims,
            'issues': issues,
            'passed': len(issues) == 0
        })

    avg_dialogue = total_dialogue_ratio / chapter_count if chapter_count > 0 else 0
    avg_heartheart = total_heartheart_ratio / chapter_count if chapter_count > 0 else 0

    failed_chapters = [r['chapter'] for r in results if not r['passed']]

    return {
        'checked_chapters': chapter_count,
        'avg_dialogue_ratio': avg_dialogue,
        'avg_heartheart_ratio': avg_heartheart,
        'failed_chapters': failed_chapters,
        'failed_count': len(failed_chapters),
        'pass_rate': f"{(chapter_count - len(failed_chapters)) / chapter_count * 100:.1f}%" if chapter_count > 0 else "0%",
        'scene_type_distribution': dict(scene_type_counts),
        'results': results
    }


def report_results(results: Dict, output_file: str = None) -> str:
    """生成场景密度检查报告"""
    lines = []
    lines.append("=" * 70)
    lines.append("场景密度检查报告 (v2.0)")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"检查章节: {results['checked_chapters']} 章")
    lines.append(f"平均对话占比: {results['avg_dialogue_ratio']:.1%}")
    lines.append(f"平均谈心场景占比: {results['avg_heartheart_ratio']:.1%}")
    lines.append(f"未通过章节: {results['failed_count']} 个")
    lines.append(f"通过率: {results['pass_rate']}")

    # 场景类型分布
    if results.get('scene_type_distribution'):
        lines.append("")
        lines.append("--- 场景类型分布 ---")
        for stype, count in sorted(results['scene_type_distribution'].items()):
            pct = count / results['checked_chapters'] * 100
            lines.append(f"  {stype}: {count}章 ({pct:.1%})")

    if results['failed_chapters']:
        lines.append("")
        lines.append("--- 未通过章节（前10）---")
        for ch in results['failed_chapters'][:10]:
            for r in results['results']:
                if r['chapter'] == ch:
                    lines.append(f"  ch{ch:03d}: [{r['scene_type']}] {', '.join(r['issues'])}")
                    break

    report = "\n".join(lines)
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='场景密度检查')
    parser.add_argument('chapters_dir', help='章节目录路径')
    parser.add_argument('--start', type=int, default=1, help='起始章节')
    parser.add_argument('--end', type=int, default=360, help='结束章节')
    parser.add_argument('--dialogue-threshold', type=float, default=0.35, help='对话占比阈值')
    parser.add_argument('--heartheart-threshold', type=float, default=0.20, help='谈心场景占比阈值')
    parser.add_argument('--output', '-o', help='输出报告路径')
    args = parser.parse_args()

    results = check_scene_density(args.chapters_dir, (args.start, args.end),
                                  args.dialogue_threshold, args.heartheart_threshold)
    report = report_results(results, args.output)
    print(report)

    sys.exit(0 if results['failed_count'] == 0 else 1)