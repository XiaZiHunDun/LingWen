#!/usr/bin/env python3
"""
报告生成器

生成一致性检查报告
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from consistency.engine.data_structures import (
    ConsistencyReport, Issue, IssueSeverity, CheckerType, QualityDimension
)


class ReportGenerator:
    """一致性报告生成器"""

    def __init__(self, template_dir: Optional[str] = None):
        """
        初始化报告生成器

        Args:
            template_dir: 报告模板目录
        """
        self.template_dir = template_dir
        self._load_template()

    def _load_template(self):
        """加载报告模板"""
        # 默认模板
        self.template = """## 一致性检查报告

**章节**: ch{chapter}
**检查时间**: {check_time}
**检查范围**: {check_scope}

---

### 问题汇总

| 严重程度 | 问题数 |
|----------|--------|
| P0 致命 | {p0_count} |
| P1 严重 | {p1_count} |
| P2 中等 | {p2_count} |
| P3 提示 | {p3_count} |

### 详细问题

{issue_details}

---

### 质量评分

| 维度 | 评分 |
|------|------|
| S1 剧情完整性 | {S1} |
| S2 逻辑自洽 | {S2} |
| S3 文笔风格 | {S3} |
| S4 情感共鸣 | {S4} |
| S5 节奏控制 | {S5} |
| S6 可读性 | {S6} |
| S7 主角魅力 | {S7} |
| S8 人物弧光 | {S8} |

**总体评分**: {total_score}/100

---

### 通过判定

**结论**: [{verdict}] {verdict_comment}

---

### 修改建议

{suggestions}

---

*报告生成时间: {report_time}*
"""

    def generate(
        self,
        report: ConsistencyReport,
        format: str = "markdown"
    ) -> str:
        """
        生成报告

        Args:
            report: 一致性检查报告
            format: 输出格式 (markdown/text/html)

        Returns:
            格式化的报告字符串
        """
        if format == "markdown":
            return self._generate_markdown(report)
        elif format == "text":
            return self._generate_text(report)
        elif format == "html":
            return self._generate_html(report)
        return self._generate_markdown(report)

    def _generate_markdown(self, report: ConsistencyReport) -> str:
        """生成 Markdown 格式报告"""
        # 生成问题详情
        issue_details = self._format_issues(report.issues)

        # 生成建议
        suggestions = self._format_suggestions(report.suggestions)

        # 判定说明
        verdict_comments = {
            "pass": "通过，无P0/P1问题",
            "review": "建议审核，存在一些问题",
            "fail": "不通过，存在严重问题"
        }

        # 填充模板
        return self.template.format(
            chapter=report.chapter,
            check_time=report.check_time.strftime("%Y-%m-%d %H:%M:%S"),
            check_scope=report.check_scope.value,
            p0_count=report.p0_count,
            p1_count=report.p1_count,
            p2_count=report.p2_count,
            p3_count=report.p3_count,
            issue_details=issue_details,
            S1=f"{report.quality.s1_plot_completeness:.1f}",
            S2=f"{report.quality.s2_logic_consistency:.1f}",
            S3=f"{report.quality.s3_writing_style:.1f}",
            S4=f"{report.quality.s4_emotional_resonance:.1f}",
            S5=f"{report.quality.s5_pacing_control:.1f}",
            S6=f"{report.quality.s6_readability:.1f}",
            S7=f"{report.quality.s7_protagonist_charm:.1f}",
            S8=f"{report.quality.s8_character_arc:.1f}",
            total_score=f"{report.total_score:.1f}",
            verdict=report.verdict.upper(),
            verdict_comment=verdict_comments.get(report.verdict, ""),
            suggestions=suggestions,
            report_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    def _format_issues(self, issues: List[Issue]) -> str:
        """格式化问题列表"""
        if not issues:
            return "_暂无问题_"

        result = []
        current_severity = None

        for issue in issues:
            # 按严重程度分组
            if issue.severity != current_severity:
                if current_severity is not None:
                    result.append("")
                result.append(f"#### {issue.severity.value}: {issue.severity.name}")
                current_severity = issue.severity

            # 问题条目
            char_info = f"**角色**: {issue.character}" if issue.character else ""
            result.append(
                f"- **[{issue.checker_type.value}]** {issue.title}\n"
                f"  {issue.description} {char_info}\n"
                f"  建议: {issue.suggestion}"
            )

        return "\n".join(result)

    def _format_suggestions(self, suggestions: List[str]) -> str:
        """格式化建议列表"""
        if not suggestions:
            return "_暂无建议_"

        return "\n".join(f"- {s}" for s in suggestions)

    def _generate_text(self, report: ConsistencyReport) -> str:
        """生成纯文本格式报告"""
        lines = [
            "=" * 50,
            "一致性检查报告",
            "=" * 50,
            f"章节: ch{report.chapter}",
            f"检查时间: {report.check_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"检查范围: {report.check_scope.value}",
            "",
            "问题汇总:",
            f"  P0 致命: {report.p0_count}",
            f"  P1 严重: {report.p1_count}",
            f"  P2 中等: {report.p2_count}",
            f"  P3 提示: {report.p3_count}",
            "",
            f"总体评分: {report.total_score:.1f}/100",
            f"结论: {report.verdict.upper()}",
            "",
            "详细问题:",
        ]

        for issue in report.issues:
            lines.append(f"  [{issue.severity.value}] {issue.title}")
            lines.append(f"    {issue.description}")
            if issue.character:
                lines.append(f"    角色: {issue.character}")
            lines.append(f"    建议: {issue.suggestion}")
            lines.append("")

        if report.suggestions:
            lines.append("修改建议:")
            for i, suggestion in enumerate(report.suggestions, 1):
                lines.append(f"  {i}. {suggestion}")

        lines.append("")
        lines.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return "\n".join(lines)

    def _generate_html(self, report: ConsistencyReport) -> str:
        """生成 HTML 格式报告"""
        html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>一致性检查报告 - ch{chapter}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .p0 {{ color: #d32f2f; font-weight: bold; }}
        .p1 {{ color: #f57c00; font-weight: bold; }}
        .p2 {{ color: #fbc02d; }}
        .p3 {{ color: #757575; }}
        .score {{ font-size: 24px; font-weight: bold; }}
        .pass {{ color: #4CAF50; }}
        .fail {{ color: #d32f2f; }}
        .review {{ color: #f57c00; }}
    </style>
</head>
<body>
    <h1>一致性检查报告</h1>
    <p><strong>章节:</strong> ch{chapter}</p>
    <p><strong>检查时间:</strong> {check_time}</p>
    <p><strong>检查范围:</strong> {check_scope}</p>

    <h2>问题汇总</h2>
    <table>
        <tr><th>严重程度</th><th>问题数</th></tr>
        <tr><td class="p0">P0 致命</td><td>{p0_count}</td></tr>
        <tr><td class="p1">P1 严重</td><td>{p1_count}</td></tr>
        <tr><td class="p2">P2 中等</td><td>{p2_count}</td></tr>
        <tr><td class="p3">P3 提示</td><td>{p3_count}</td></tr>
    </table>

    <h2>总体评分</h2>
    <p class="score {verdict}">{total_score}/100</p>
    <p>结论: <span class="{verdict}">{verdict}</span></p>

    <h2>修改建议</h2>
    <ul>
{suggestions}
    </ul>

    <footer>
        <p>报告生成时间: {report_time}</p>
    </footer>
</body>
</html>"""

        suggestions_html = "\n".join(
            f"<li>{s}</li>" for s in report.suggestions
        ) if report.suggestions else "<li>暂无建议</li>"

        return html_template.format(
            chapter=report.chapter,
            check_time=report.check_time.strftime("%Y-%m-%d %H:%M:%S"),
            check_scope=report.check_scope.value,
            p0_count=report.p0_count,
            p1_count=report.p1_count,
            p2_count=report.p2_count,
            p3_count=report.p3_count,
            total_score=f"{report.total_score:.1f}",
            verdict=report.verdict,
            suggestions=suggestions_html,
            report_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    def save_report(
        self,
        report: ConsistencyReport,
        output_path: str,
        format: str = "markdown"
    ) -> str:
        """
        保存报告到文件

        Args:
            report: 一致性检查报告
            output_path: 输出文件路径
            format: 输出格式

        Returns:
            保存的文件路径
        """
        content = self.generate(report, format)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(output_path)