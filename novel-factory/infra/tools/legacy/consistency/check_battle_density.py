#!/usr/bin/env python3
"""
战斗描写密度检测器 v2.0
检测章节中动作/战术描写的占比，标记纯对话推进而战斗被口头带过的章节

改进日志：
- v2.0: 新增战时/平时章节分类、扩展战术关键词库（3层）、分级阈值
"""
import os
import re
import sys
from typing import List, Dict, Tuple


# ========== 基础战斗动作词（原有）==========
BATTLE_ACTION_WORDS = [
    '攻击', '防守', '防御', '进攻', '出击', '反击',
    '挥剑', '劈砍', '刺出', '格挡', '闪避', '躲闪',
    '爆发', '释放', '凝聚', '发动', '施展',
    '飞跃', '冲刺', '后退', '撤退', '追击',
    '碰撞', '冲击', '爆炸', '粉碎', '撕裂',
    '倒下', '翻滚', '跃起',
    '燃烧', '闪烁', '轰鸣',
]

# ========== 战术对抗词汇（新增第二层）==========
TACTICAL_COMBAT_WORDS = [
    # 阵法/布阵
    '布阵', '破阵', '结阵', '阵眼', '阵法', '阵旗',
    # 试探/僵持
    '试探', '试探性', '僵持', '对峙', '拉扯',
    # 压制/缠斗
    '压制', '碾压', '缠斗', '纠缠', '纠缠不清',
    # 追击/撤退
    '穷追', '围堵', '包抄', '合围', '突围',
    # 回合/交锋
    '回合', '交锋', '交错', '冲击波',
    # 武器特效
    '剑气纵横', '刀光剑影', '拳风呼啸', '能量波动', '气浪',
    # 致命/伤亡
    '一击必杀', '致命伤', '鲜血迸溅', '血雾', '倒飞出去',
]

# ========== 战时心理/意图（新增第三层）==========
WARTIME_INTENT_WORDS = [
    '杀意', '战意', '杀气', '煞气', '威胁',
    '必杀', '绝招', '底牌', '拼死', '奋力',
    '阻击', '拦截', '掩护', '断后',
]

# ========== 战时场景关键词 ==========
WARTIME_SCENE_KEYWORDS = [
    '战场', '敌人', '来袭', '追杀', '伏击', '遭遇战',
    '剑气', '刀光', '拳风', '暗域', '爪牙', '堕落者',
    '兽潮', '异变', '异族', '妖兽', '怪物',
]

# ========== 战时意图/行动关键词 ==========
WARTIME_ACTION_KEYWORDS = [
    '攻击', '进攻', '出击', '迎战', '迎敌',
    '格挡', '闪避', '躲闪', '撤退', '逃跑',
    '剑出鞘', '刀出鞘', '拔剑', '抽刀',
    '释放', '爆发', '轰击', '斩杀', '劈砍',
    '飞跃', '冲刺', '扑向', '射向',
]

# ========== 平时场景关键词 ==========
PEACETIME_SCENE_KEYWORDS = [
    '夜晚', '休息', '睡眠', '沉睡', '午睡',
    '修炼', '打坐', '闭关', '吸收', '凝聚',
    '交谈', '对话', '聊天', '商议', '讨论',
    '回忆', '思念', '想起', '记得',
    '交易', '买卖', '商定', '契约',
]


# 战斗场景关键词
BATTLE_SCENE_KEYWORDS = [
    '战斗', '交战', '厮杀', '对决', '对抗',
    '战场上', '战局', '战况',
    '剑气', '刀光', '拳风',
]

# 纯对话推进模式（战斗被口头描述，跳过）
TALKED_ABOUT_BATTLE = [
    r'说.*已经.*战斗', r'说.*结束了',
    r'说.*打败了', r'说.*击败了',
    r'战斗.*已经.*结束', r'战争.*已经.*结束',
]


def classify_chapter_type(content: str) -> str:
    """
    章节类型分类: 'wartime' | 'peaceful' | 'mixed'

    战时章节: 战时关键词 ≥ 3 处 OR 战时场景≥1 + 战时行动≥2
    平时章节: 无战时关键词，战时关键词 < 3 处
    混合章节: 战时关键词 ≥ 3 处，但对话/内心独白也占大量篇幅
    """
    wartime_count = 0

    for kw in WARTIME_SCENE_KEYWORDS + WARTIME_ACTION_KEYWORDS:
        wartime_count += len(re.findall(kw, content))

    if wartime_count >= 3:
        # 检查是否主要是对话（混合型）
        dialogue_patterns = [r'\u201c[^\u201d]{10,}\u201d', r'"[^"]{10,}"', r'说[道问曰]']
        dialogue_count = sum(len(re.findall(p, content)) for p in dialogue_patterns)
        total_paragraphs = content.count('\n\n')

        if dialogue_count > wartime_count * 3 and total_paragraphs > 10:
            return 'mixed'
        return 'wartime'

    return 'peaceful'


def get_threshold(chapter_type: str) -> float:
    """根据章节类型获取战斗密度阈值"""
    thresholds = {
        'wartime': 0.10,   # 战时章节：战斗描写密度 ≥ 10% 才合格
        'mixed': 0.06,     # 混合章节：≥ 6% 才合格
        'peaceful': 0.03,  # 平时章节：≥ 3% 即合格
    }
    return thresholds.get(chapter_type, 0.05)


def calculate_battle_density(content: str, chapter_type: str = 'peaceful') -> float:
    """
    计算战斗描写密度（战斗相关字数/总字数）

    Args:
        content: 章节内容
        chapter_type: 'wartime' | 'mixed' | 'peaceful'

    Returns:
        0.0 ~ 1.0 的密度值
    """
    battle_chars = 0

    # 基础动作词
    for word in BATTLE_ACTION_WORDS:
        battle_chars += len(word) * len(re.findall(word, content))

    # 战术词汇（战时/mixed章节权重更高）
    weight = 1.5 if chapter_type in ('wartime', 'mixed') else 1.0
    for word in TACTICAL_COMBAT_WORDS + WARTIME_INTENT_WORDS:
        battle_chars += len(word) * len(re.findall(word, content)) * weight

    # 战斗场景关键词
    for keyword in BATTLE_SCENE_KEYWORDS:
        battle_chars += len(keyword) * len(re.findall(keyword, content))

    total_chars = len(content)
    if total_chars == 0:
        return 0.0

    # 估算战斗描写占比（假设平均每处战斗描写15字）
    estimated_battle_ratio = min(battle_chars * 15 / total_chars, 1.0)
    return estimated_battle_ratio


def detect_talked_battle(content: str) -> bool:
    """
    检测是否是"口头描述的战斗"

    有些章节声称发生了战斗，但实际的战斗描写极少，
    主要是通过对话来交代战斗结果，这会削弱战斗的冲击力。
    """
    for pattern in TALKED_ABOUT_BATTLE:
        if re.search(pattern, content):
            return True
    return False


def check_battle_density(chapters_dir: str,
                          chapter_range: tuple[int, int] = (1, 360),
                          threshold: float = None) -> Dict:
    """
    检测战斗描写密度 v2.0

    Args:
        chapters_dir: 章节目录
        chapter_range: 检查章节范围
        threshold: 战斗描写密度阈值（会覆盖自动分类的阈值，仅用于向后兼容）

    Returns:
        检测结果字典
    """
    start, end = chapter_range

    results = []
    low_battle_chapters = []
    talked_battle_chapters = []
    total_battle_density = 0.0
    chapter_count = 0
    chapter_type_counts = {'wartime': 0, 'mixed': 0, 'peaceful': 0}

    for i in range(start, end + 1):
        fname = f"ch{i:03d}.md"
        fpath = os.path.join(chapters_dir, fname)

        if not os.path.exists(fpath):
            continue

        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 自动分类章节类型
        chapter_type = classify_chapter_type(content)
        chapter_type_counts[chapter_type] += 1

        # 确定阈值
        if threshold is not None:
            effective_threshold = threshold
        else:
            effective_threshold = get_threshold(chapter_type)

        battle_density = calculate_battle_density(content, chapter_type)
        has_talked_battle = detect_talked_battle(content)

        total_battle_density += battle_density
        chapter_count += 1

        issues = []
        if battle_density < effective_threshold:
            issues.append(f"战斗描写{battle_density:.1%}过低（{chapter_type}阈值{effective_threshold:.1%}）")
            low_battle_chapters.append(i)
        if has_talked_battle:
            issues.append("口头描述的战斗（实际描写不足）")
            talked_battle_chapters.append(i)

        results.append({
            'chapter': i,
            'chapter_type': chapter_type,
            'battle_density': battle_density,
            'threshold': effective_threshold,
            'has_talked_battle': has_talked_battle,
            'issues': issues,
            'passed': len(issues) == 0
        })

    avg_battle_density = total_battle_density / chapter_count if chapter_count > 0 else 0.0

    return {
        'checked_chapters': chapter_count,
        'avg_battle_density': avg_battle_density,
        'low_battle_chapters': low_battle_chapters,
        'talked_battle_chapters': talked_battle_chapters,
        'low_battle_count': len(low_battle_chapters),
        'talked_battle_count': len(talked_battle_chapters),
        'chapter_type_distribution': chapter_type_counts,
        'results': results
    }


def report_results(results: Dict, output_file: str = None) -> str:
    """生成战斗密度检查报告"""
    lines = []
    lines.append("=" * 70)
    lines.append("战斗描写密度检查报告 (v2.0)")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"检查章节: {results['checked_chapters']} 章")
    lines.append(f"平均战斗描写密度: {results['avg_battle_density']:.1%}")
    lines.append(f"战斗描写不足章节: {results['low_battle_count']} 个")
    lines.append(f"口头描述战斗章节: {results['talked_battle_count']} 个")

    # 章节类型分布
    if results.get('chapter_type_distribution'):
        lines.append("")
        lines.append("--- 章节类型分布 ---")
        for ctype, count in results['chapter_type_distribution'].items():
            pct = count / results['checked_chapters'] * 100
            lines.append(f"  {ctype}: {count}章 ({pct:.1%})")

    if results['low_battle_chapters']:
        lines.append("")
        lines.append("--- 战斗描写不足章节（前10）---")
        for ch in results['low_battle_chapters'][:10]:
            for r in results['results']:
                if r['chapter'] == ch:
                    lines.append(f"  ch{ch:03d}: [{r['chapter_type']}] 密度{r['battle_density']:.1%}, {r['issues']}")
                    break

    report = "\n".join(lines)
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='战斗描写密度检查')
    parser.add_argument('chapters_dir', help='章节目录路径')
    parser.add_argument('--start', type=int, default=1, help='起始章节')
    parser.add_argument('--end', type=int, default=360, help='结束章节')
    parser.add_argument('--threshold', type=float, default=0.05, help='战斗描写密度阈值')
    parser.add_argument('--output', '-o', help='输出报告路径')
    args = parser.parse_args()

    results = check_battle_density(args.chapters_dir, (args.start, args.end), args.threshold)
    report = report_results(results, args.output)
    print(report)

    sys.exit(0 if results['low_battle_count'] == 0 else 1)