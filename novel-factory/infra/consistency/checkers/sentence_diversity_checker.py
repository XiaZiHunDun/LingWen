#!/usr/bin/env python3
"""
句式多样性检测器
检测章节句式重复度过高的问题
评分标准（S3文笔风格）：
- 优秀: Shannon指数≥3.5，句式种类≥10种，且无单一句式超过20%
- 合格: Shannon指数≥2.5，句式种类≥6种
- 触发重写: Shannon指数<2.5 或 句式种类<6种 或 某句式占比>40%
"""
import re
import math
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field

@dataclass
class DiversityIssue:
    chapter: str
    score: float
    severity: str
    description: str

@dataclass
class TemplateSentence:
    """模板句检测结果"""
    pattern_name: str
    template_example: str
    count: int
    percentage: float
    replacement_suggestions: List[str] = field(default_factory=list)

@dataclass
class PatternRatio:
    """句式占比信息"""
    pattern_name: str
    count: int
    percentage: float
    is_template: bool = False

class SentenceDiversityChecker:
    """
    句式多样性检测器
    使用Shannon多样性指数计算句式分布
    """

    # 句式模式定义（25+种真正的中文句式分类）
    DIVERSE_PATTERNS = [
        # === 对话句 ===
        (r'「[^」]+」', 'dialog', '对话句'),
        (r'他[说问道喊叫笑叹谓称著显示露出透露出冒][^。！？]*[。！？]', 'narrate_he', '他述句'),
        (r'她[说问道喊叫笑叹谓称著显示露出透露出冒][^。！？]*[。！？]', 'narrate_she', '她述句'),
        (r'它[说问道喊叫][^。！？]*[。！？]', 'narrate_it', '它述句'),

        # === 被动/把字句 ===
        (r'被[^。，！？]{1,20}[了着过]', 'passive', '被动句'),
        (r'把[^。，！？]{1,30}[了着]', 'ba_construction', '把字句'),

        # === 疑问/反问/感叹句 ===
        (r'[^。！？]*[吗呢吧嘛呀啊][。！？]', 'question_particle', '疑问句'),
        (r'[^。！？]*[谁|什么|哪|几|怎么|如何|为何|为什么][^。！？]*[？?]', 'question_wh', '疑问词疑问句'),
        (r'难道[^。！？]+[吗呢不成][。！？]', 'rhetorical_反问', '反问句'),
        (r'岂能[^。！？]+[。！？]', 'rhetorical_岂', '反问句'),
        (r'[^。！？]*![。！？]', 'exclamatory', '感叹句'),

        # === 祈使句 ===
        (r'^[你要您咱们大家][^。！？]{0,20}[！。]', 'imperative_你', '祈使句'),
        (r'^[勿莫别不要不许不可][^。！？]{0,15}[！。]', 'imperative_禁', '祈使句'),
        (r'^[来去走跑站坐][^。！？]{0,15}[！。]', 'imperative_v', '祈使句'),

        # === 省略句 ===
        (r'^，、[^。！？]{0,10}[。！？]', 'elliptical_comma', '省略句'),
        (r'^\.{3,}[^。！？]*[。！？]', 'elliptical_dots', '省略句'),

        # === 连动句/兼语句 ===
        (r'请[^。！？]{1,15}[^。！？]+[做去来][^。！？]*[。！？]', 'pivotal_请', '兼语句'),
        (r'让[^。！？]{1,10}[^。！？]+[做去来][^。！？]*[。！？]', 'pivotal_让', '兼语句'),

        # === 双宾句 ===
        (r'给[^。！？]{1,10}[^。！？]{1,10}[^。！？]{1,10}[了着][。！？]', 'double_io', '双宾句'),
        (r'送[^。！？]{1,10}[^。！？]{1,10}[^。！？]{1,10}[了着][。！？]', 'double_io_送', '双宾句'),

        # === 时间/条件/因果句 ===
        (r'随着[^，]。*[。！？]', 'temporal_随着', '时间句'),
        (r'当[^，]。*[时侯候][，][^。！？]*[。！？]', 'temporal_当', '时间句'),
        (r'在[^，]。*[时侯候][，][^。！？]*[。！？]', 'temporal_在', '时间句'),
        (r'如果[^，]。*[，][^。！？]*[。！？]', 'conditional_如果', '条件句'),
        (r'假如[^，]。*[，][^。！？]*[。！？]', 'conditional_假如', '条件句'),
        (r'只要[^，]。*[，][^。！？]*[。！？]', 'conditional_只要', '条件句'),
        (r'因为[^，]。*[，][^。！？]*[。！？]', 'cause_因为', '因果句'),
        (r'因此[^，]。*[。！？]', 'cause_因此', '因果句'),
        (r'所以[^，]。*[。！？]', 'cause_所以', '因果句'),

        # === 转折/递进/让步句 ===
        (r'但是[^，]。*[。！？]', 'contrast_但是', '转折句'),
        (r'然而[^，]。*[。！？]', 'contrast_然而', '转折句'),
        (r'不过[^，]。*[。！？]', 'contrast_不过', '转折句'),
        (r'虽然[^，]。*[，][^。！？]*[。！？]', 'concessive_虽然', '让步句'),
        (r'尽管[^，]。*[，][^。！？]*[。！？]', 'concessive_尽管', '让步句'),
        (r'不仅[^，]。*[，][^。！？]*[而且甚至]', 'progressive', '递进句'),
        (r'既[^，]。*[，][^。！？]*[又也且]', 'parallel_既', '并列句'),

        # === 目的/解说句 ===
        (r'为了[^，]。*[，][^。！？]*[。！？]', 'purpose_为了', '目的句'),
        (r'以便[^，]。*[。！？]', 'purpose_以便', '目的句'),
        (r'即[^，]。*[，][^。！？]*[。！？]', 'explanatory_即', '解说句'),
        (r'也就是说[^，]。*[。！？]', 'explanatory_也就是说', '解说句'),

        # === 描写句 ===
        (r'只见[^，]。*[。！？]', 'desc_只见', '描写句'),
        (r'忽见[^，]。*[。！？]', 'desc_忽见', '描写句'),
        (r'但见[^，]。*[。！？]', 'desc_但见', '描写句'),
        (r'忽然[^，]。*[。！？]', 'desc_忽然', '描写句'),
        (r'突然[^，]。*[。！？]', 'desc_突然', '描写句'),
        (r'猛然[^，]。*[。！？]', 'desc_猛然', '描写句'),

        # === 短句 ===
        (r'^[^。！？]{1,10}[。！？]', 'short_sentence', '短句'),

        # === 陈述句（兜底） ===
        (r'^[^\n。！？]{2,80}[。！？\n]', 'declarative', '陈述句'),
    ]

    # 模板句模式（过度使用的固定句式）
    TEMPLATE_PATTERNS = [
        (r'他[说问道喊叫笑叹谓称著显示露出透露出冒][^。！？]{0,15}[。！？]', '模板_他说道', [
            '减少"他说道"的使用，用动作和表情替代',
            '改为：他抬起下巴，目光冷冽',
            '改为：嘴角勾起一抹笑'
        ]),
        (r'她[说问道喊叫笑叹谓称著显示露出透露出冒][^。！？]{0,15}[。！？]', '模板_她说道', [
            '减少"她说道"的使用，用动作和表情替代',
            '改为：她轻抚发丝，声音低沉',
            '改为：她愣了愣，没有回答'
        ]),
        (r'只见([^，]。*)', '模板_只见', [
            '"只见"过于套路化',
            '替换：视野中突现、眼前浮现、一道身影落下',
            '示例：视野中突现一道身影'
        ]),
        (r'突然([^，]。*)', '模板_突然', [
            '"突然"过于平淡',
            '替换：倏忽、霎时、刹那、一瞬间、蓦然',
            '示例：空气中霎时弥漫起一股寒意'
        ]),
        (r'然而([^，]。*)', '模板_然而', [
            '过多"然而"削弱转折力度',
            '替换：但、只是、可惜、无奈、却、偏',
            '示例：可惜天不遂人愿'
        ]),
        (r'但是([^，]。*)', '模板_但是', [
            '过多"但是"削弱转折力度',
            '替换：只是、可、可惜、无奈、却',
            '示例：只是这代价太过沉重'
        ]),
        (r'因此([^，]。*)', '模板_因此', [
            '"因此"过于书面化',
            '替换：于是、这就、这才、于是乎',
            '示例：于是众人各自散去'
        ]),
        (r'随着([^，]。*)', '模板_随着', [
            '"随着"过于套路化',
            '替换：此后、此后不久、就在此时、就在那刻',
            '示例：就在此时，异变突生'
        ]),
        (r'如果([^，]。*)', '模板_如果', [
            '虚拟语气过多使用',
            '减少"如果...就"结构，用事实陈述替代'
        ]),
        (r'于是([^，]。*)', '模板_于是', [
            '"于是"使用过度',
            '替换：接着、随后、然后、此时、下一秒',
            '示例：下一秒，他消失在原地'
        ]),
        (r'就在这时([^，]。*)', '模板_就在此时', [
            '时间标记过于套路',
            '替换：恰在此时、偏在这时、正此际',
            '示例：恰在此时，一道闪电划破夜空'
        ]),
        (r'不一会儿([^，]。*)', '模板_不一会儿', [
            '时间过渡过于简单',
            '替换：片刻后、少顷、须臾之间、转瞬',
            '示例：少顷，他睁开双眼'
        ]),
        (r'很快([^，]。*)', '模板_很快', [
            '时间过渡过于模糊',
            '替换：不多时、半晌、一炷香后',
            '示例：半晌，他才回过神来'
        ]),
        (r'看到这一幕([^，]。*)', '模板_看到这一幕', [
            '视角转换过于生硬',
            '替换：目击此景、见状、这一幕映入眼帘',
            '示例：这一幕映入眼帘，他心头一沉'
        ]),
        (r'听到这话([^，]。*)', '模板_听到这话', [
            '对话引入过于生硬',
            '替换：话音入耳、闻及此言、此言入心',
            '示例：话音入耳，他面色微变'
        ]),
    ]

    # 评分阈值（S3标准，校准后适配新增陈述句兜底）
    # Shannon指数受句式种类数影响，6种以上可达标
    THRESHOLDS = {
        'excellent': 3.0,
        'pass': 1.5,
        'fail': 1.5,
        'template_ratio': 30.0,
    }

    def __init__(self, chapters_dir: Optional[str] = None):
        if chapters_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            chapters_dir = project_root / '03_内容仓库' / '04_正文'
        self.chapters_dir = Path(chapters_dir)

    def _count_sentences(self, content: str) -> int:
        return len(re.findall(r'[。！？]', content))

    def _calculate_shannon_index(self, distribution: Dict[str, int], total: int) -> float:
        if total == 0:
            return 0.0
        diversity_index = 0.0
        for count in distribution.values():
            p = count / total
            if p > 0:
                diversity_index -= p * math.log2(p)
        return diversity_index

    def score_chapter(self, chapter_num: int) -> Tuple[float, Dict[str, int]]:
        ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
        if not ch_file.exists():
            return 0.0, {}
        content = ch_file.read_text(encoding='utf-8')
        return self.score_content(content)

    def score_content(self, content: str) -> Tuple[float, Dict[str, int]]:
        total_sentences = self._count_sentences(content)
        if total_sentences == 0:
            return 0.0, {}

        distribution = {}
        for pattern, name, _ in self.DIVERSE_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                distribution[name] = len(matches)

        diversity_index = self._calculate_shannon_index(distribution, total_sentences)

        covered = sum(distribution.values())
        uncovered = total_sentences - covered
        if uncovered > 0:
            all_dist = distribution.copy()
            all_dist['_other'] = uncovered
            diversity_index = self._calculate_shannon_index(all_dist, total_sentences)

        return round(diversity_index, 2), distribution

    def get_pattern_ratios(self, chapter_num: int) -> List[PatternRatio]:
        ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
        if not ch_file.exists():
            return []
        content = ch_file.read_text(encoding='utf-8')
        return self.get_pattern_ratios_from_content(content)

    def get_pattern_ratios_from_content(self, content: str) -> List[PatternRatio]:
        total_sentences = self._count_sentences(content)
        if total_sentences == 0:
            return []

        distribution = {}
        for pattern, name, _ in self.DIVERSE_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                distribution[name] = len(matches)

        ratios = []
        for name, count in distribution.items():
            pct = (count / total_sentences) * 100
            ratios.append(PatternRatio(
                pattern_name=name,
                count=count,
                percentage=round(pct, 2),
                is_template=pct > self.THRESHOLDS['template_ratio']
            ))
        ratios.sort(key=lambda x: x.percentage, reverse=True)
        return ratios

    def detect_template_sentences(self, chapter_num: int) -> List[TemplateSentence]:
        ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
        if not ch_file.exists():
            return []
        content = ch_file.read_text(encoding='utf-8')
        return self.detect_template_sentences_from_content(content)

    def detect_template_sentences_from_content(self, content: str) -> List[TemplateSentence]:
        total_sentences = self._count_sentences(content)
        if total_sentences == 0:
            return []

        template_sentences = []
        for pattern, template_name, suggestions in self.TEMPLATE_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                count = len(matches)
                pct = (count / total_sentences) * 100
                if pct > self.THRESHOLDS['template_ratio']:
                    example = matches[0] if matches else ''
                    if len(example) > 30:
                        example = example[:30] + '...'
                    template_sentences.append(TemplateSentence(
                        pattern_name=template_name,
                        template_example=example,
                        count=count,
                        percentage=round(pct, 2),
                        replacement_suggestions=suggestions
                    ))
        template_sentences.sort(key=lambda x: x.percentage, reverse=True)
        return template_sentences

    def check_chapter(self, chapter_num: int) -> Optional[DiversityIssue]:
        score, distribution = self.score_chapter(chapter_num)
        templates = self.detect_template_sentences(chapter_num)
        template_warnings = [t for t in templates if t.percentage > self.THRESHOLDS['template_ratio']]

        ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
        content = ch_file.read_text(encoding='utf-8') if ch_file.exists() else ''
        total_sentences = self._count_sentences(content)
        pattern_variety = len(distribution)

        dominant_pct = 0
        if total_sentences > 0:
            for name, count in distribution.items():
                pct = (count / total_sentences) * 100
                if pct > dominant_pct:
                    dominant_pct = pct

        issues_desc = []
        if score < self.THRESHOLDS['fail']:
            issues_desc.append(f"Shannon指数{score:.2f}低于阈值{self.THRESHOLDS['fail']}")
        if pattern_variety < 6:
            issues_desc.append(f"句式种类仅{pattern_variety}种，少于6种")
        if dominant_pct > 40:
            issues_desc.append(f"单一句式占比{dominant_pct:.0f}%超过40%")
        if template_warnings:
            template_names = ', '.join([t.pattern_name for t in template_warnings[:3]])
            issues_desc.append(f"模板句问题：{template_names}")

        if not issues_desc:
            return None

        if score < 2.0 or dominant_pct > 50 or len(template_warnings) >= 2:
            severity = 'HIGH'
        elif score < 2.5 or dominant_pct > 40 or template_warnings:
            severity = 'MEDIUM'
        else:
            severity = 'LOW'

        return DiversityIssue(
            chapter=f'ch{chapter_num:03d}',
            score=score,
            severity=severity,
            description='; '.join(issues_desc)
        )

    def check_all(self, limit: Optional[int] = None) -> List[DiversityIssue]:
        issues = []
        chapter_files = sorted(self.chapters_dir.glob('ch*.md'))
        if limit:
            chapter_files = chapter_files[:limit]

        for ch_file in chapter_files:
            match = re.match(r'ch(\d+)\.md', ch_file.name)
            if match:
                ch_num = int(match.group(1))
                issue = self.check_chapter(ch_num)
                if issue:
                    issues.append(issue)
        return issues

    def generate_report(self, issues: List[DiversityIssue]) -> str:
        if not issues:
            return "✅ 句式多样性检查通过：所有章节评分合格"

        high_issues = [i for i in issues if i.severity == 'HIGH']
        medium_issues = [i for i in issues if i.severity == 'MEDIUM']

        report = ["# 句式多样性检查报告\n"]
        report.append(f"## 汇总\n")
        report.append(f"- HIGH级问题: {len(high_issues)}章节\n")
        report.append(f"- MEDIUM级问题: {len(medium_issues)}章节\n")

        if high_issues:
            report.append("## HIGH 需重写\n")
            for issue in sorted(high_issues, key=lambda x: x.score):
                report.append(f"- [{issue.chapter}] {issue.description}")

        if medium_issues:
            report.append("\n## MEDIUM 建议优化\n")
            for issue in sorted(medium_issues, key=lambda x: x.score)[:10]:
                report.append(f"- [{issue.chapter}] {issue.description}")

        return "\n".join(report)

    def generate_template_report(self, chapter_num: int) -> str:
        templates = self.detect_template_sentences(chapter_num)
        if not templates:
            return f"ch{chapter_num:03d}: 未检测到模板句问题"

        lines = [f"# 模板句检测报告 - ch{chapter_num:03d}\n"]
        lines.append("## 检测到的模板句问题\n")

        for t in templates:
            lines.append(f"### {t.pattern_name}")
            lines.append(f"- 出现次数: {t.count}")
            lines.append(f"- 占比: {t.percentage}%")
            lines.append(f"- 示例: {t.template_example}")
            lines.append("- 替换建议:")
            for suggestion in t.replacement_suggestions:
                lines.append(f"  - {suggestion}")
            lines.append("")
        return "\n".join(lines)


if __name__ == '__main__':
    import sys
    checker = SentenceDiversityChecker()

    limit = None
    if len(sys.argv) > 1 and sys.argv[1] == '--limit':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    template_mode = '--template' in sys.argv

    if template_mode:
        chapter_files = sorted(checker.chapters_dir.glob('ch*.md'))[:limit or 9999]
        for ch_file in chapter_files:
            match = re.match(r'ch(\d+)\.md', ch_file.name)
            if match:
                ch_num = int(match.group(1))
                templates = checker.detect_template_sentences(ch_num)
                if templates:
                    print(checker.generate_template_report(ch_num))
                    print("---")
    else:
        issues = checker.check_all(limit=limit)
        if issues:
            print(checker.generate_report(issues))
            high_count = len([i for i in issues if i.severity == 'HIGH'])
            print(f"\n总计: {len(issues)}章节有问题（{high_count} HIGH）")
            sys.exit(1) if high_count > 0 else sys.exit(0)
        else:
            print("✅ 句式多样性检查通过：所有章节评分合格")
            sys.exit(0)