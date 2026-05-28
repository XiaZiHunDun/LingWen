#!/usr/bin/env python3
"""
套路句式检测器
检测"那一刻"等50+种套路句式的过度使用
评分标准（基于S3文笔风格扩展）：
- 优秀: 无套路句式或占比<10%
- 合格: 套路句式占比10-20%
- 触发重写: 套路句式占比>20%

注：这是SentenceDiversityChecker的补充，
专注于检测过度使用的固定句式模式
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field

from .base_checker import BaseChecker
from infra.consistency.engine.data_structures import Issue, IssueLocation, CheckerType, IssueSeverity


@dataclass
class RepetitivePhraseIssue:
    """套路句式问题"""
    chapter: int
    phrase_type: str
    count: int
    percentage: float
    examples: List[str] = field(default_factory=list)
    severity: str = "MEDIUM"


class RepetitivePhraseChecker(BaseChecker):
    """
    套路句式检测器
    检测"那一刻"等50+种套路句式的过度使用
    """

    # 套路句式模式定义（按评审意见新增）
    # 格式: (正则模式, 句式名称, 替换建议列表)
    REPETITIVE_PATTERNS = [
        # === 时间标记类（评审一致指出）===
        (r'那一刻[^\n。！？]{0,30}[。！？]?', '那一刻', [
            '替换为具体动作：他的手停住了',
            '替换为感官描写：一阵寒意窜上脊背',
            '替换为短句：刀锋入肉。'
        ]),
        (r'下一秒[^\n。！？]{0,30}[。！？]?', '下一秒', [
            '替换：刀光一闪、利刃破空、话音未落',
            '替换：话音未落，他已消失在原地'
        ]),
        (r'就在这时[^\n。！？]{0,30}[。！？]?', '就在这时', [
            '替换：恰在此时、偏在这刻、正此际',
            '替换：话音刚落，异变突生'
        ]),
        (r'与此同时[^\n。！？]{0,30}[。！？]?', '与此同时', [
            '删除此过渡句，或用具体场景描述替代',
            '替换：视线转向另一处、镜头拉远'
        ]),
        (r'不一会儿[^\n。！？]{0,30}[。！？]?', '不一会儿', [
            '替换：片刻后、少顷、须臾之间'
        ]),
        (r'很快[^\n。！？]{0,30}[。！？]?', '很快', [
            '替换：不多时、半炷香后、片刻'
        ]),
        (r'很快地[^\n。！？]{0,30}[。！？]?', '很快地', [
            '替换：不多时、片刻之后'
        ]),
        (r'不多时[^\n。！？]{0,30}[。！？]?', '不多时', [
            '保留或替换：片刻后、少顷'
        ]),

        # === 心理描写类（评审2/3/4指出）===
        (r'他[的]?心想[^\n。！？]{0,30}[。！？]?', '他心想', [
            '删除"他心想"，用动作/表情暗示',
            '改为：他的手微微收紧，面上却不显'
        ]),
        (r'她[的]?心想[^\n。！？]{0,30}[。！？]?', '她心想', [
            '删除"她心想"，用动作/表情暗示',
            '改为：她的睫毛颤了颤，没有回答'
        ]),
        (r'他知道[^\n。！？]{0,30}[。！？]?', '他知道', [
            '删除"他知道"，用行为证明',
            '改为：林夜没有回答，只是收刀入鞘'
        ]),
        (r'她知道[^\n。！？]{0,30}[。！？]?', '她知道', [
            '删除"她知道"，用行动展示',
            '改为：苏琳垂下眼，指尖摩挲着衣角'
        ]),
        (r'他[感觉得到领悟到明白]?[^\n。！？]{0,30}[。！？]?', '他感到', [
            '用身体反应替代心理陈述',
            '改为：他的喉咙像被什么堵住'
        ]),
        (r'她[感觉得到领悟到明白]?[^\n。！？]{0,30}[。！？]?', '她感到', [
            '用身体反应替代心理陈述',
            '改为：她的眼眶发酸，却没让泪落下'
        ]),
        (r'心头一沉[^\n。！？]{0,30}[。！？]?', '心头一沉', [
            '替换：胸口像被攥紧、一种不祥的预感'
        ]),
        (r'心头一热[^\n。！？]{0,30}[。！？]?', '心头一热', [
            '替换：胸口涌起暖意、鼻尖微酸'
        ]),
        (r'心脏被攥住[^\n。！？]{0,30}[。！？]?', '心脏被攥住', [
            '替换：胸口发闷、喘不上气（评审4指出重复）',
            '替换：像有什么东西压在心口'
        ]),
        (r'心脏像是被什么攥住[^\n。！？]{0,30}[。！？]?', '心脏像是被攥住', [
            '同心脏被攥住变体，需统一替换'
        ]),

        # === 情感描写模板（评审3/4指出）===
        (r'感到前所未有的[^\n。！？]{0,20}[。！？]?', '前所未有的', [
            '"前所未有的"过于夸张',
            '直接描写当下感受：胸口发紧、喉咙发涩'
        ]),
        (r'他[的]?眼眶[发红湿润泛红]?[^\n。！？]{0,20}[。！？]?', '眼眶发红', [
            '减少直接眼部描写',
            '替换：用别的方式暗示情感——握拳、别过脸'
        ]),
        (r'她[的]?眼眶[发红湿润泛红]?[^\n。！？]{0,20}[。！？]?', '眼眶发红', [
            '减少直接眼部描写',
            '替换：她的声音微微发颤'
        ]),

        # === 动作引导类（评审4指出）===
        (r'看到这一幕[^\n。！？]{0,30}[。！？]?', '看到这一幕', [
            '替换：目击此景、见状、这一幕映入眼帘',
            '删除，改为直接场景描写'
        ]),
        (r'听到这话[^\n。！？]{0,30}[。！？]?', '听到这话', [
            '替换：话音入耳、闻及此言',
            '删除，让对话自然承接'
        ]),
        (r'只见[^\n。！？]{0,30}[。！？]?', '只见', [
            '"只见"过于套路化（评审1/4指出）',
            '替换：视野中突现、眼前浮现、一道身影落下',
            '示例：视野中突现一道身影'
        ]),

        # === 转折类（评审2/4指出）===
        (r'然而[^\n。！？]{0,30}[。！？]?', '然而', [
            '过多"然而"削弱转折力度（评审2）',
            '替换：但、只是、可惜、无奈、却、偏',
            '示例：可惜天不遂人愿'
        ]),
        (r'但是[^\n。！？]{0,30}[。！？]?', '但是', [
            '过多"但是"削弱转折力度（评审2）',
            '替换：只是、可、可惜、无奈、却',
            '示例：只是这代价太过沉重'
        ]),
        (r'不过[^\n。！？]{0,30}[。！？]?', '不过', [
            '替换：只是、可、可惜'
        ]),

        # === 因果类（评审4指出）===
        (r'因此[^\n。！？]{0,30}[。！？]?', '因此', [
            '"因此"过于书面化（评审4）',
            '替换：于是、这就、这就样'
        ]),
        (r'于是[^\n。！？]{0,30}[。！？]?', '于是', [
            '"于是"使用过度（评审2/4）',
            '替换：接着、随后、然后、此时',
            '示例：下一秒，他消失在原地'
        ]),

        # === 过渡类 ===
        (r'随着[^\n。！？]{0,30}[。！？]?', '随着', [
            '"随着"过于套路化（评审4）',
            '替换：此后、此后不久、就在此时'
        ]),
        (r'然后[^\n。！？]{0,30}[。！？]?', '然后', [
            '减少"然后"使用',
            '替换：接着、随后、之后'
        ]),
        (r'接着[^\n。！？]{0,30}[。！？]?', '接着', [
            '减少"接着"使用',
            '替换：随后、之后、下一秒'
        ]),
        (r'随后[^\n。！？]{0,30}[。！？]?', '随后', [
            '减少"随后"使用',
            '替换：片刻后、少顷'
        ]),

        # === 场景描写模板 ===
        (r'废土的?天空[永远是]?[^\n。！？]{0,20}[。！？]?', '废土天空', [
            '"废土的天空永远是暗红色的"过于套路（评审2）',
            '变化描写：天空呈暗褐色、有黄尘扬起',
            '减少环境描写的重复'
        ]),
        (r'风带着铁锈味[^\n。！？]{0,20}[。！？]?', '铁锈味', [
            '减少"铁锈味"重复使用（评审2）',
            '变化：腐败气息、尘土味、焦糊味'
        ]),

        # === 守护主题类（评审2指出重复最多）===
        (r'守护[不是保护]?[^\n。！？]{0,30}[。！？]?', '守护主题', [
            '"守护"主题讨论过多（评审2统计≥26次）',
            '保留3次关键场景，其余用行动替代',
            '删除宣言式表达，用具体行为展示'
        ]),
        (r'黑暗不是用来消灭的[^\n。！？]{0,30}[。！？]?', '黑暗守护', [
            '这是核心金句，全文保留≤3次',
            '删除其他变体重复表达'
        ]),
        (r'同伴是用命来守护的[^\n。！？]{0,30}[。！？]?', '同伴守护', [
            '删除，用具体行动替代',
            '示例：林夜挡在苏琳面前、拔刀'
        ]),
        (r'值得吗[^\n。！？]{0,30}[。！？]?', '值得吗', [
            '"值得吗"讨论过多（评审2指出）',
            '保留1-2次关键场景即可'
        ]),

        # === 复仇主题类 ===
        (r'用[他们]?的血[^\n。！？]{0,20}[。！？]?', '复仇宣言', [
            '减少复仇宣言出现次数',
            '保留1-2处作为情感锚点'
        ]),
        (r'变强[^\n。！？]{0,20}[。！？]?', '变强主题', [
            '减少"变强"独白',
            '用行动证明：苦修、战斗、突破'
        ]),
        (r'活下去[^\n。！？]{0,20}[。！？]?', '活下去', [
            '"活下去"出现次数过多',
            '保留开头和关键转折处即可'
        ]),

        # === 状态描写 ===
        (r'他的(?!手|脚|眼|脸|身)[^\n。！？]{0,20}[^\n。！？]{0,15}[。！？]', '他的状态', [
            '减少"他的..."开头',
            '用动作/对话替代'
        ]),

        # === 比喻过度使用（评审4指出）===
        (r'像[风中的枯叶枯叶]?[^\n。！？]{0,20}[。！？]?', '像枯叶', [
            '"像风中的枯叶"重复使用（评审4）',
            '变化：像秋日落叶、像被抽走力气'
        ]),
        (r'像[沉睡的]?星辰[^\n。！？]{0,20}[。！？]?', '像星辰', [
            '"像沉睡的星辰"重复（评审4）',
            '变化：像碎钻、像渔火'
        ]),
    ]

    # 评分阈值
    THRESHOLDS = {
        'excellent': 10.0,   # 套路句式占比<10%
        'pass': 20.0,        # 10-20%
        'fail': 20.0,        # >20%
    }

    def __init__(self, chapters_dir: Optional[str] = None):
        super().__init__(CheckerType.REPETITIVE_PHRASE)
        if chapters_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            chapters_dir = project_root / '03_内容仓库' / '04_正文'
        self.chapters_dir = Path(chapters_dir)

    def _count_sentences(self, content: str) -> int:
        return len(re.findall(r'[。！？]', content))

    def check_chapter(self, chapter_num: int) -> List[RepetitivePhraseIssue]:
        ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
        if not ch_file.exists():
            return []
        content = ch_file.read_text(encoding='utf-8')
        return self.check_content(content, chapter_num)

    def check_content(self, content: str, chapter_num: int = 0) -> List[RepetitivePhraseIssue]:
        total_sentences = self._count_sentences(content)
        if total_sentences == 0:
            return []

        issues = []
        for pattern, phrase_type, suggestions in self.REPETITIVE_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                count = len(matches)
                pct = (count / total_sentences) * 100
                if pct > 0:  # 只要出现就算问题
                    severity = 'HIGH' if pct > self.THRESHOLDS['fail'] else \
                               'MEDIUM' if pct > self.THRESHOLDS['excellent'] else 'LOW'
                    examples = [m[:50] for m in matches[:3]]
                    issues.append(RepetitivePhraseIssue(
                        chapter=chapter_num,
                        phrase_type=phrase_type,
                        count=count,
                        percentage=round(pct, 2),
                        examples=examples,
                        severity=severity
                    ))

        return sorted(issues, key=lambda x: x.percentage, reverse=True)

    def check_all(self, limit: Optional[int] = None) -> List[RepetitivePhraseIssue]:
        issues = []
        chapter_files = sorted(self.chapters_dir.glob('ch*.md'))
        if limit:
            chapter_files = chapter_files[:limit]

        for ch_file in chapter_files:
            match = re.match(r'ch(\d+)\.md', ch_file.name)
            if match:
                ch_num = int(match.group(1))
                ch_issues = self.check_chapter(ch_num)
                issues.extend(ch_issues)

        return issues

    def check(self, chapter_content: str, chapter_num: int, context: Optional[Dict[str, Any]] = None) -> List[Issue]:
        """执行检查，返回Issue列表

        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
            context: 上下文信息

        Returns:
            Issue列表
        """
        # 使用check_content检测当前章节
        repetitive_issues = self.check_content(chapter_content, chapter_num)

        # 转换为标准Issue格式
        result = []
        for issue in repetitive_issues:
            if issue.severity in ('HIGH', 'MEDIUM'):
                suggestion = self._get_suggestion(issue.phrase_type, issue.examples)
                result.append(Issue(
                    id=f"RP_{chapter_num:03d}_{issue.phrase_type}",
                    severity=IssueSeverity.P2 if issue.severity == 'MEDIUM' else IssueSeverity.P1,
                    checker_type=CheckerType.REPETITIVE_PHRASE,
                    issue_type="repetitive_phrase",
                    title=f"套路句式过度使用: {issue.phrase_type}",
                    description=f"'{issue.phrase_type}'出现{issue.count}次，占比{issue.percentage}%，高于阈值",
                    location=IssueLocation(chapter=chapter_num),
                    evidence='; '.join(issue.examples[:2]),
                    suggestion=suggestion
                ))
        return result

    def generate_issue_for_chapter(self, chapter_num: int) -> List[Issue]:
        """生成符合一致性引擎格式的Issue列表"""
        issues = self.check_chapter(chapter_num)
        result = []
        for issue in issues:
            if issue.severity in ('HIGH', 'MEDIUM'):
                ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
                content = ch_file.read_text(encoding='utf-8') if ch_file.exists() else ''

                # 生成修改建议
                suggestion = self._get_suggestion(issue.phrase_type, issue.examples)

                result.append(Issue(
                    id=f"RP_{chapter_num:03d}_{issue.phrase_type}",
                    severity=IssueSeverity.P2 if issue.severity == 'MEDIUM' else IssueSeverity.P1,
                    checker_type=CheckerType.REPETITIVE_PHRASE,
                    issue_type="repetitive_phrase",
                    title=f"套路句式过度使用: {issue.phrase_type}",
                    description=f"'{issue.phrase_type}'出现{issue.count}次，占比{issue.percentage}%，高于阈值",
                    location=IssueLocation(chapter=chapter_num),
                    evidence='; '.join(issue.examples[:2]),
                    suggestion=suggestion
                ))
        return result

    def _get_suggestion(self, phrase_type: str, examples: List[str]) -> str:
        """获取修改建议"""
        suggestions_map = {
            '那一刻': '用具体动作或感官描写替代，如"他的手停住了"或"一阵寒意窜上脊背"',
            '下一秒': '替换为"刀光一闪"或"话音未落"',
            '他心想': '删除，用动作/表情暗示内心',
            '她心想': '删除，用动作/表情暗示内心',
            '他知道': '删除，用行为证明',
            '她知道': '删除，用行动展示',
            '只见': '替换为"视野中突现"或"眼前浮现"',
            '然而': '替换为"但、只是、可惜"',
            '但是': '替换为"只是、可、可惜"',
            '于是': '替换为"接着、随后、下一秒"',
            '守护主题': '减少讨论，用行动替代宣言',
            '黑暗守护': '核心金句，全文保留≤3次',
            '心脏被攥住': '替换为"胸口发闷"或"像有什么东西压在心口"',
        }
        return suggestions_map.get(phrase_type, f'减少"{phrase_type}"的使用，用更具体的描写替代')

    def generate_report(self, issues: List[RepetitivePhraseIssue]) -> str:
        if not issues:
            return "✅ 套路句式检查通过：未检测到过度使用的套路句式"

        high_issues = [i for i in issues if i.severity == 'HIGH']
        medium_issues = [i for i in issues if i.severity == 'MEDIUM']

        report = ["# 套路句式检查报告\n"]
        report.append(f"## 汇总\n")
        report.append(f"- HIGH级问题: {len(high_issues)}处\n")
        report.append(f"- MEDIUM级问题: {len(medium_issues)}处\n")

        # 按句式类型汇总
        phrase_stats = {}
        for issue in issues:
            if issue.phrase_type not in phrase_stats:
                phrase_stats[issue.phrase_type] = {'count': 0, 'total_pct': 0, 'chapters': []}
            phrase_stats[issue.phrase_type]['count'] += issue.count
            phrase_stats[issue.phrase_type]['total_pct'] += issue.percentage
            phrase_stats[issue.phrase_type]['chapters'].append(issue.chapter)

        if phrase_stats:
            report.append("\n## 句式类型统计（按出现次数排序）\n")
            for phrase, stats in sorted(phrase_stats.items(), key=lambda x: x[1]['count'], reverse=True)[:15]:
                ch_list = ', '.join([f"ch{c:03d}" for c in stats['chapters'][:5]])
                report.append(f"- **{phrase}**: {stats['count']}次 (ch{ch_list})")

        return "\n".join(report)


if __name__ == '__main__':
    import sys
    checker = RepetitivePhraseChecker()

    limit = None
    if len(sys.argv) > 1 and sys.argv[1] == '--limit':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    issues = checker.check_all(limit=limit)
    if issues:
        print(checker.generate_report(issues))
    else:
        print("✅ 套路句式检查通过")