#!/usr/bin/env python3
"""
境界体系检测器 v2.0
检测境界体系的一致性，追踪全文境界描述，建立晋升时间线，检测前后矛盾

改进日志：
- v2.0: 区分定义vs引用语句、添加创世境和子境界、精确化正则、矛盾检测增强
"""
import os
import re
import sys
from typing import List, Dict, Tuple, Optional
from collections import OrderedDict, defaultdict


# ========== 扩展后的境界体系 ==========
REALM_HIERARCHY = [
    '粒子境', '星火境', '脉冲境', '裂变境', '黑洞境',
    '星尘境', '本源境', '虚无境', '创世境',
]

# 子境界（黑洞境的三重境界）
SUB_REALMS = {
    '黑洞境': ['引力之境', '心境之境', '意志之境']
}

# ========== 精确化的境界模式 ==========

# 真正的境界定义语句（首次引入境界）
REALM_DEFINITION_PATTERNS = [
    # 标准格式：境界名 + 系动词 + 说明
    r'(粒子境|星火境|脉冲境|裂变境|黑洞境|星尘境|本源境|虚无境|创世境)(?:是|为|属于|位于)',
    # 标准格式：踏入/进入/迈入/晋升至/突破至 + 境界名
    r'(?:踏入|进入|迈入|晋升至|突破至|达到)(?:到?|了)?(粒子境|星火境|脉冲境|裂变境|黑洞境|星尘境|本源境|虚无境|创世境)',
    # 说明性格式：境界名 + · + 阶位
    r'(粒子境|星火境|脉冲境|裂变境|黑洞境|星尘境|本源境|虚无境|创世境)[·\.](?:巅峰|初期|中期|后期|感应|灵动)',
    # 修为描述
    r'修为(?:已)?(?:达到|迈入|突破至)(?:了)?(粒子境|星火境|脉冲境|裂变境|黑洞境|星尘境|本源境|虚无境|创世境)',
]

# 境界引用语句（提及但不定义）
REALM_REFERENCE_PATTERNS = [
    r'(粒子境|星火境|脉冲境|裂变境|黑洞境|星尘境本源境|虚无境|创世境)的?(?:气息|威压|力量|波动|层次)',
    r'(?:拥有|达到|触碰)(?:到)?(粒子境|星火境|脉冲境|裂变境|黑洞境|星尘境本源境|虚无境|创世境)',
    # 黑洞境子境界
    r'(引力之境|心境之境|意志之境)',
]

# 排除模式（不视为境界）
EXCLUDE_PATTERNS = [
    r'边境外',    # 地名
    r'情境',      # 无关词汇
    r'环境',      # 无关词汇
    r'境界[高低]',  # 形容而非境界名
    r'一种境界',   # 比喻用法
]

# 境界相关的关键词（用于检测文本中的境界描述）
REALM_PATTERNS = [
    # 标准境界
    r'粒子境', r'星火境', r'脉冲境', r'裂变境', r'黑洞境',
    r'星尘境', r'本源境', r'虚无境', r'创世境',
    # 变体
    r'星尘境[·\.]\w+阶',
    r'(?:境界|修为|层次)等[一二三四五六七八九十百千万]+',
    # 常见搭配
    r'突破.*境', r'晋升.*境', r'踏入.*境',
    r'巅峰', r'大成', r'圆满',
]

# 需要检测的境界变化模式
REALM_CHANGE_PATTERNS = [
    r'从.*境.*突破', r'从.*境.*晋升',
    r'踏入.*境', r'进入.*境',
    r'晋升为.*境', r'提升至.*境',
    r'达到.*境', r'迈入.*境',
]


def extract_realms(content: str) -> Tuple[List[str], List[str]]:
    """
    从内容中提取境界描述（区分定义和引用）

    Returns:
        (definitions, references) - 境界定义语句列表和引用语句列表
    """
    definitions = []
    references = []

    # 检查排除模式
    for ex_pat in EXCLUDE_PATTERNS:
        if re.search(ex_pat, content):
            continue

    # 提取定义语句
    for pattern in REALM_DEFINITION_PATTERNS:
        matches = re.findall(pattern, content)
        definitions.extend(matches)

    # 提取引用语句
    for pattern in REALM_REFERENCE_PATTERNS:
        matches = re.findall(pattern, content)
        references.extend(matches)

    return list(set(definitions)), list(set(references))


def get_realm_level(realm_name: str) -> int:
    """获取境界在体系中的层级（用于排序）"""
    for i, known_realm in enumerate(REALM_HIERARCHY):
        if known_realm in realm_name:
            return i
    # 检查子境界
    for parent, sub_realms in SUB_REALMS.items():
        if realm_name in sub_realms:
            parent_idx = get_realm_level(parent)
            if parent_idx >= 0:
                return parent_idx  # 子境界等同于父境界层级
    return -1  # 未知境界


def is_realm_definition_sentence(sentence: str) -> bool:
    """判断是否为境界定义语句"""
    definition_verbs = ['是', '为', '属于', '踏入', '进入', '迈入', '晋升至', '突破至', '达到']
    for realm in REALM_HIERARCHY + ['创世境', '引力之境', '心境之境', '意志之境']:
        for verb in definition_verbs:
            if f'{realm}{verb}' in sentence or f'{verb}{realm}' in sentence:
                return True
    return False


def extract_realm_promotions(content: str) -> List[Dict]:
    """
    从内容中提取境界晋升描述

    Returns:
        list of {from_realm, to_realm, chapter} 晋升事件
    """
    promotions = []

    # 检测晋升语句 - 匹配"从X境突破到Y境"或"突破至Y境"等模式
    promotion_patterns = [
        # 从X境突破后，[...]向Y境发起冲击 - 非贪婪匹配中间内容
        r'从([\u4e00-\u9fa5]+境)突破后[，]?.*向([\u4e00-\u9fa5]+境)发起',
        # 突破至/进入 Y境
        r'(?:突破至|进入|晋升至|迈入)(?:了)?([\u4e00-\u9fa5]+境)',
        # 从X境 晋升/突破 为/到 Y境
        r'从([\u4e00-\u9fa5]+境)[的]?(?:晋升|突破)(?:为|至|到)?([\u4e00-\u9fa5]+境)',
        # X境突破，晋升为Y境
        r'([\u4e00-\u9fa5]+境)突破[，]?(?:晋升|为)([\u4e00-\u9fa5]+境)',
    ]

    for pattern in promotion_patterns:
        matches = re.finditer(pattern, content)
        for m in matches:
            from_realm = m.group(1) if m.lastindex >= 1 else None
            to_realm = m.group(2) if m.lastindex >= 2 else None

            if from_realm and to_realm:
                from_level = get_realm_level(from_realm)
                to_level = get_realm_level(to_realm)
                if from_level >= 0 and to_level >= 0:
                    promotions.append({
                        'from_realm': from_realm,
                        'to_realm': to_realm,
                        'from_level': from_level,
                        'to_level': to_level,
                    })

    return promotions


def check_realm_consistency(chapters_dir: str,
                            chapter_range: tuple[int, int] = (1, 360)) -> Dict:
    """
    检测境界体系一致性 v2.0

    Args:
        chapters_dir: 章节目录
        chapter_range: 检查章节范围

    Returns:
        检测结果字典
    """
    start, end = chapter_range

    # 记录每个境界首次出现的位置
    first_appearance: Dict[str, int] = {}
    # 记录每个角色的境界晋升时间线
    realm_history: Dict[str, List[Dict]] = defaultdict(list)

    # 检测到的矛盾
    contradictions = []

    # 按章节追踪
    for i in range(start, end + 1):
        fname = f"ch{i:03d}.md"
        fpath = os.path.join(chapters_dir, fname)

        if not os.path.exists(fpath):
            continue

        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取境界描述
        definitions, references = extract_realms(content)
        all_realms = definitions + references

        # 记录首次出现（仅定义语句才算"首次定义"）
        for realm in definitions:
            if realm not in first_appearance:
                first_appearance[realm] = i

        # 使用extract_realm_promotions获取真正的境界变化
        promotions = extract_realm_promotions(content)
        for promo in promotions:
            from_realm = promo['from_realm']
            to_realm = promo['to_realm']
            from_level = promo['from_level']
            to_level = promo['to_level']

            if from_level >= 0 and to_level >= 0:
                if to_level - from_level > 1:
                    contradictions.append({
                        'chapter': i,
                        'type': 'SKIP_REALM',
                        'desc': f'境界跳跃：{from_realm}→{to_realm}（跳过中间境界）',
                        'from': from_realm,
                        'to': to_realm
                    })
                elif to_level < from_level:
                    contradictions.append({
                        'chapter': i,
                        'type': 'REALM_REGRESSION',
                        'desc': f'境界倒退：{from_realm}→{to_realm}',
                        'from': from_realm,
                        'to': to_realm
                    })

    # 检测未知境界（在REALM_HIERARCHY之外但类似境界的词）
    unknown_realms = [r for r in first_appearance.keys()
                      if get_realm_level(r) == -1 and '境' in r and r not in ['引力之境', '心境之境', '意志之境']]

    # 检测未定义的境界（首次出现时全文没有铺垫）
    undefined_realms = []
    for realm in first_appearance.keys():
        ch = first_appearance[realm]
        if get_realm_level(realm) == -1:
            continue
        defined = False
        for check_ch in range(start, ch):
            if check_ch == ch:
                continue
            fname = f"ch{check_ch:03d}.md"
            fpath = os.path.join(chapters_dir, fname)
            if os.path.exists(fpath):
                with open(fpath, 'r', encoding='utf-8') as f:
                    prev_content = f.read()
                if re.search(rf'{re.escape(realm)}.*(?:定义|体系|属于|是.*境)', prev_content):
                    defined = True
                    break
                realm_list = '|'.join(REALM_HIERARCHY + ['创世境'])
                if re.search(rf'(?:粒子境|星火境|脉冲境|裂变境|黑洞境).*{re.escape(realm)}', prev_content):
                    defined = True
                    break
        if not defined and ch > 10:
            undefined_realms.append((realm, ch))

    return {
        'checked_chapters': end - start + 1,
        'realms_found': list(first_appearance.keys()),
        'first_appearance': first_appearance,
        'unknown_realms': unknown_realms,
        'undefined_realms': undefined_realms,
        'contradictions': contradictions,
        'contradiction_count': len(contradictions),
        'sub_realms': SUB_REALMS,
    }


def report_results(results: Dict, output_file: str = None) -> str:
    """生成境界体系检测报告"""
    lines = []
    lines.append("=" * 70)
    lines.append("境界体系检测报告 (v2.0)")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"检查章节: {results['checked_chapters']} 章")
    lines.append(f"发现境界: {len(results['realms_found'])} 个")
    lines.append(f"矛盾数量: {results['contradiction_count']} 处")

    # 子境界
    if results.get('sub_realms'):
        lines.append("")
        lines.append("--- 子境界体系 ---")
        for parent, subs in results['sub_realms'].items():
            lines.append(f"  {parent} → {', '.join(subs)}")

    if results['contradictions']:
        lines.append("")
        lines.append("--- 境界矛盾 ---")
        for c in results['contradictions'][:10]:
            lines.append(f"  ch{c['chapter']:03d}: {c['desc']}")

    if results['undefined_realms']:
        lines.append("")
        lines.append("--- 可能未定义的境界 ---")
        for realm, ch in results['undefined_realms'][:5]:
            lines.append(f"  {realm}: 首次出现在ch{ch:03d}，但全文未找到定义")

    if results['unknown_realms']:
        lines.append("")
        lines.append("--- 未知境界 ---")
        for realm in results['unknown_realms'][:5]:
            lines.append(f"  {realm}")

    report = "\n".join(lines)
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='境界体系检测')
    parser.add_argument('chapters_dir', help='章节目录路径')
    parser.add_argument('--start', type=int, default=1, help='起始章节')
    parser.add_argument('--end', type=int, default=360, help='结束章节')
    parser.add_argument('--output', '-o', help='输出报告路径')
    args = parser.parse_args()

    results = check_realm_consistency(args.chapters_dir, (args.start, args.end))
    report = report_results(results, args.output)
    print(report)

    sys.exit(0 if results['contradiction_count'] == 0 else 1)