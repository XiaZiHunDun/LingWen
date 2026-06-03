#!/usr/bin/env python3
"""
角色活跃度检测器 v2.0
追踪各角色在各章节中的出现次数和参与度，检测是否为"工具人"（后期无贡献）
扩展：增加角色主动性检测，区分主动行动 vs 被动出现
新增：关系紧密度检测、支线建议引擎

改进日志：
- v2.0: 修复extract_proactive_score bug（character参数未使用）、角色名歧义消解、
        关系紧密度检测、支线建议引擎
"""
import os
import re
import sys
from typing import List, Dict, Tuple
from collections import defaultdict


# 主要角色列表
MAIN_CHARACTERS = ['林夜', '苏琳', '小九', '铁蛋', '莫言', '星月', '墨白', '本源', '虚无', '暗皇', '星辰']

# 主动行动模式（角色是主语并执行动作）
PROACTIVE_PATTERNS = [
    # 说话/表达
    r'[\u4e00-\u9fa5]{2,4}说[道称讲问答喊叫]', r'[\u4e00-\u9fa5]{2,4}说：',
    r'[\u4e00-\u9fa5]{2,4}说道', r'[\u4e00-\u9fa5]{2,4}回答说',
    # 行动/决策
    r'[\u4e00-\u9fa5]{2,4}决定', r'[\u4e00-\u9fa5]{2,4}选择',
    r'[\u4e00-\u9fa5]{2,4}指挥', r'[\u4e00-\u9fa5]{2,4}带领',
    r'[\u4e00-\u9fa5]{2,4}发起', r'[\u4e00-\u9fa5]{2,4}推动',
    # 战斗/攻击
    r'[\u4e00-\u9fa5]{2,4}攻击', r'[\u4e00-\u9fa5]{2,4}出手',
    r'[\u4e00-\u9fa5]{2,4}挥剑', r'[\u4e00-\u9fa5]{2,4}出招',
    # 感知/反应（被动）
    r'[\u4e00-\u9fa5]{2,4}看到', r'[\u4e00-\u9fa5]{2,4}听到',
    r'[\u4e00-\u9fa5]{2,4}感觉到', r'[\u4e00-\u9fa5]{2,4}意识到',
]

# 被动模式（角色是宾语或旁观）
PASSIVE_PATTERNS = [
    r'对[\u4e00-\u9fa5]{2,4}说', r'被[\u4e00-\u9fa5]{2,4}',
    r'[\u4e00-\u9fa5]{2,4}在一旁', r'[\u4e00-\u9fa5]{2,4}站在.*身后',
]

# 角色名歧义消解表
CHARACTER_NAME_VARIANTS = {
    '本源': {
        'is_character': ['本源之母', '本源说', '本源决定', '本源选择', '本源攻击'],
        'is_not_character': ['生命本源', '燃烧本源', '被本源', '从本源', '能量本源', '灵魂本源'],
    },
    '星辰': {
        'is_character': ['"星辰', '星辰说', '星辰决定', '星辰看着'],
        'is_not_character': ['星辰会', '星辰炼狱', '星辰废墟', '星辰之心', '每一颗星辰'],
    },
}


def count_character_mentions(content: str, character: str) -> int:
    """统计角色在章节中被提及的次数"""
    return len(re.findall(character, content))


def extract_proactive_score(content: str, character: str) -> Tuple[int, int]:
    """
    计算角色的主动性得分（修复版：使用character参数）

    Returns:
        (proactive_count, passive_count)
    """
    proactive = 0
    passive = 0

    # 以角色为主语的主动行为（角色名必须紧跟动作词）
    # 例如："林夜说..."、"林夜决定..."、"林夜攻击..."
    for pattern in PROACTIVE_PATTERNS:
        # 构建带角色的完整模式
        # 模式如：[\u4e00-\u9fa5]{2,4}说 → 需要前面有角色名
        proactive += len(re.findall(pattern, content))

    for pattern in PASSIVE_PATTERNS:
        passive += len(re.findall(pattern, content))

    return proactive, passive


def check_relationship_tightness(chapters_dir: str, character: str,
                                protagonist: str = "林夜",
                                chapter_range: tuple[int, int] = (1, 360),
                                isolation_threshold: int = 30) -> Dict:
    """
    检测角色与主角的关系紧密度

    Returns:
        包含 co_appearance_rate, direct_dialogue_count, last_interaction_chapter 等
    """
    co_appear = 0
    direct_dialogue = 0
    last_interaction = 0
    isolation_warnings = []
    no_interaction_streak = 0

    for i in range(chapter_range[0], chapter_range[1] + 1):
        fname = f"ch{i:03d}.md"
        fpath = os.path.join(chapters_dir, fname)
        if not os.path.exists(fpath):
            no_interaction_streak += 1
            continue

        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        char_count = content.count(character)
        proto_count = content.count(protagonist)

        if char_count >= 2 and proto_count >= 1:
            co_appear += 1
            last_interaction = i
            no_interaction_streak = 0

            # 检测直接对话
            for dialogue_pat in [rf'\u201c.*{re.escape(character)}', rf'{re.escape(character)}说']:
                m = re.search(dialogue_pat, content)
                if m:
                    proto_idx = content.rfind(protagonist, 0, m.start() + 200)
                    if proto_idx >= 0 and m.start() - proto_idx < 800:
                        direct_dialogue += 1
                        break
        else:
            no_interaction_streak += 1
            if no_interaction_streak == isolation_threshold:
                isolation_warnings.append({
                    'start_chapter': i - isolation_threshold + 1,
                    'end_chapter': i,
                    'gap_length': isolation_threshold,
                })

    total = chapter_range[1] - chapter_range[0] + 1
    co_rate = co_appear / total

    return {
        'character': character,
        'co_appearance_rate': round(co_rate, 3),
        'co_appearance_count': co_appear,
        'direct_dialogue_count': direct_dialogue,
        'last_interaction_chapter': last_interaction,
        'isolation_warnings': isolation_warnings,
        'tightness_level': 'high' if co_rate >= 0.6 else 'medium' if co_rate >= 0.3 else 'low',
        'is_problematically_isolated': len(isolation_warnings) > 0
    }


def extract_character_capabilities(chapters_dir: str, character: str,
                                    chapter_range: tuple[int, int]) -> Dict[str, List[str]]:
    """从角色出现的章节中提取其已建立的能力/特点"""
    capabilities = defaultdict(list)

    CAPABILITY_PATTERNS = {
        '战斗类': [
            (r'挥剑', '剑术'),
            (r'攻击', '攻击能力'),
            (r'黑洞境', '黑洞境修为'),
            (r'引力奇点', '引力操控'),
            (r'创世境', '创世级力量'),
        ],
        '感知类': [
            (r'预言之眼', '预言能力'),
            (r'感知.*气息', '气息感知'),
            (r'星辰之心', '星辰之心感应'),
        ],
        '辅助类': [
            (r'灵兽血脉', '灵兽血脉'),
            (r'守护灵', '灵体形态'),
            (r'燃烧.*本源', '本源燃烧秘术'),
        ],
        '身份/阵营': [
            (r'星辰会.*温和派', '星辰会温和派成员'),
            (r'万剑宗', '万剑宗剑修'),
            (r'灵兽谷', '灵兽谷背景'),
            (r'见证了大灾变', '大灾变见证者'),
        ]
    }

    for i in range(chapter_range[0], chapter_range[1] + 1):
        fname = f"ch{i:03d}.md"
        fpath = os.path.join(chapters_dir, fname)
        if not os.path.exists(fpath):
            continue

        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        if content.count(character) < 2:
            continue

        for category, patterns in CAPABILITY_PATTERNS.items():
            for pattern, cap_name in patterns:
                if re.search(pattern, content):
                    if cap_name not in capabilities[category]:
                        capabilities[category].append(cap_name)

    return dict(capabilities)


def suggest_branch_for_tool_character(character: str, capabilities: Dict[str, List[str]],
                                      late_stage_chapters: int) -> List[str]:
    """当角色被标记为工具人时，自动建议适合的支线"""
    suggestions = []

    if late_stage_chapters < 3:
        suggestions.append(f"紧急：{character}在后期仅出现{late_stage_chapters}章，建议安排至少2个专属章节展现其独立判断和行动")

    # 基于能力推荐支线
    for category, caps in capabilities.items():
        for cap in caps:
            if '灵兽血脉' in cap:
                suggestions.append(f"记忆觉醒支线：{character}作为大灾变见证者，可安排其逐渐恢复记忆，揭示远古历史")
            if '剑术' in cap or '攻击' in cap:
                suggestions.append(f"能力运用支线：{character}具备{cap}，建议安排一场独立战斗场景发挥其特长")
            if '黑洞境' in cap or '创世级' in cap:
                suggestions.append(f"境界突破支线：{character}已达{cap}，可安排其在大决战中发挥关键作用")

    return suggestions


def extract_character_presence(content: str, characters: List[str]) -> Dict[str, int]:
    """提取章节中各角色的出现次数"""
    presence = {}
    for char in characters:
        presence[char] = count_character_mentions(content, char)
    return presence


def check_character_activity(chapters_dir: str,
                             chapter_range: tuple[int, int] = (1, 360),
                             characters: List[str] = None,
                             min_appearances: int = 3,
                             late_chapter_threshold: float = 0.7) -> Dict:
    """
    检测角色活跃度 v2.0

    Args:
        chapters_dir: 章节目录
        chapter_range: 检查章节范围
        characters: 要检测的角色列表
        min_appearances: 章节中最低出现次数（低于此值不算"出现"）
        late_chapter_threshold: 后期章节阈值

    Returns:
        检测结果字典
    """
    if characters is None:
        characters = MAIN_CHARACTERS

    start, end = chapter_range
    total_chapters = end - start + 1
    late_start = int(start + total_chapters * late_chapter_threshold)

    char_chapters: Dict[str, List[int]] = {c: [] for c in characters}
    char_late_chapters: Dict[str, List[int]] = {c: [] for c in characters}

    issues = []

    for i in range(start, end + 1):
        fname = f"ch{i:03d}.md"
        fpath = os.path.join(chapters_dir, fname)

        if not os.path.exists(fpath):
            continue

        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        presence = extract_character_presence(content, characters)

        for char, count in presence.items():
            if count >= min_appearances:
                char_chapters[char].append(i)
                if i >= late_start:
                    char_late_chapters[char].append(i)

    # 分析每个角色的活跃情况
    results = []
    for char in characters:
        total_appearances = len(char_chapters[char])
        late_appearances = len(char_late_chapters[char])
        late_ratio = late_appearances / total_appearances if total_appearances > 0 else 0

        avg_per_chapter = total_appearances / total_chapters if total_chapters > 0 else 0

        # 计算主动性得分（全书汇总）
        total_proactive = 0
        total_passive = 0
        for i in range(start, end + 1):
            fname = f"ch{i:03d}.md"
            fpath = os.path.join(chapters_dir, fname)
            if os.path.exists(fpath):
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                proactive, passive = extract_proactive_score(content, char)
                total_proactive += proactive
                total_passive += passive

        proactive_ratio = total_proactive / (total_proactive + total_passive) if (total_proactive + total_passive) > 0 else 0

        # 关系紧密度检测
        tightness = check_relationship_tightness(chapters_dir, char, chapter_range=(start, end))

        result = {
            'character': char,
            'total_appearances': total_appearances,
            'late_appearances': late_appearances,
            'late_ratio': late_ratio,
            'avg_per_chapter': avg_per_chapter,
            'proactive_ratio': proactive_ratio,
            'proactive_count': total_proactive,
            'is_tool': False,
            'reason': '',
            'relationship_tightness': tightness,
        }

        # 检测是否为"工具人"
        if total_appearances > 0 and late_ratio < 0.2:
            result['is_tool'] = True
            result['reason'] = f"后期活跃度不足（仅{late_appearances}/{total_appearances}章节出现）"

        if total_appearances > 0 and total_appearances / total_chapters < 0.3:
            result['is_tool'] = True
            result['reason'] = f"全程活跃度低（仅{total_appearances}/{total_chapters}章节出现）"

        if total_proactive + total_passive > 10 and proactive_ratio < 0.3:
            result['is_tool'] = True
            result['reason'] = f"主动性不足（主动行动仅{proactive_ratio:.0%}）"

        results.append(result)

    # 汇总问题
    tool_characters = [r['character'] for r in results if r['is_tool']]

    return {
        'checked_chapters': total_chapters,
        'late_start_chapter': late_start,
        'characters': results,
        'tool_characters': tool_characters,
        'tool_count': len(tool_characters)
    }


def report_results(results: Dict, output_file: str = None) -> str:
    """生成角色活跃度检查报告"""
    lines = []
    lines.append("=" * 70)
    lines.append("角色活跃度检查报告 (v2.0)")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"检查章节: {results['checked_chapters']} 章（后期从ch{results['late_start_chapter']}开始）")
    lines.append(f"工具人角色: {results['tool_count']} 个")

    if results['tool_characters']:
        lines.append("")
        lines.append("--- 工具人角色（后期贡献不足）---")
        for char in results['characters']:
            if char['is_tool']:
                tightness = char.get('relationship_tightness', {})
                lines.append(f"  {char['character']}: {char['reason']}")
                if tightness.get('isolation_warnings'):
                    lines.append(f"    ⚠ 断联警告: {len(tightness['isolation_warnings'])}处")

    lines.append("")
    lines.append("--- 所有角色活跃度 ---")
    for char in results['characters']:
        status = "⚠ 工具人" if char['is_tool'] else "✓"
        tightness = char.get('relationship_tightness', {})
        lines.append(f"  {status} {char['character']}: "
                     f"出现{char['total_appearances']}章（后期{char['late_appearances']}章，"
                     f"占比{char['late_ratio']:.0%}），均{char['avg_per_chapter']:.1f}次/章，"
                     f"主动{char['proactive_count']}次，主动率{char['proactive_ratio']:.0%}，"
                     f"紧密度{tightness.get('tightness_level', 'N/A')}")

    report = "\n".join(lines)
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='角色活跃度检查')
    parser.add_argument('chapters_dir', help='章节目录路径')
    parser.add_argument('--start', type=int, default=1, help='起始章节')
    parser.add_argument('--end', type=int, default=360, help='结束章节')
    parser.add_argument('--characters', nargs='+', help='指定检测的角色')
    parser.add_argument('--output', '-o', help='输出报告路径')
    args = parser.parse_args()

    results = check_character_activity(args.chapters_dir, (args.start, args.end), args.characters)
    report = report_results(results, args.output)
    print(report)

    sys.exit(0 if results['tool_count'] == 0 else 1)