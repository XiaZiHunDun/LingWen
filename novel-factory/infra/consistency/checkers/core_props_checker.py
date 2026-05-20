#!/usr/bin/env python3
"""
核心道具贯穿检查器
确保第1章出现的重要道具在后续有再现
"""
import re
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

@dataclass
class PropIssue:
    chapter: str
    prop_name: str
    severity: str
    description: str

class CorePropsChecker:
    """
    核心道具贯穿检查器

    第1章重要道具必须在全文中有再现：
    - 母亲削的木勺
    - 父亲的地窖
    - 其他核心道具

    检测逻辑：
    1. 从第1章提取所有【道具】标记
    2. 检查这些道具是否在后续章节中再现
    3. 未再现的道具标记为HIGH严重度
    """

    # 第1章必须贯穿的核心道具
    CH1_MANDATORY_PROPS = [
        '木勺',
        '地窖',
        '母亲',
        '父亲'
    ]

    def __init__(self, chapters_dir: Optional[str] = None):
        if chapters_dir is None:
            project_root = Path(__file__).parent.parent.parent
            chapters_dir = project_root / '03_内容仓库' / '04_正文'
        self.chapters_dir = Path(chapters_dir)

    def extract_ch1_props(self) -> List[str]:
        """从第1章提取道具"""
        ch1_file = self.chapters_dir / 'ch001.md'
        if not ch1_file.exists():
            return []

        content = ch1_file.read_text(encoding='utf-8')
        props = []

        # 提取【道具:名称】标记
        prop_pattern = r'【道具:(.+?)】'
        matches = re.findall(prop_pattern, content)
        props.extend(matches)

        # 检查强制性道具
        for mandatory in self.CH1_MANDATORY_PROPS:
            if mandatory in content and mandatory not in props:
                props.append(mandatory)

        return props

    def check_reappear(self, prop_name: str) -> int:
        """检查道具在后续章节的再现次数"""
        count = 0
        for ch_file in sorted(self.chapters_dir.glob('ch*.md')):
            match = re.match(r'ch(\d+)\.md', ch_file.name)
            if match:
                ch_num = int(match.group(1))
                if ch_num == 1:
                    continue  # 跳过第1章

                content = ch_file.read_text(encoding='utf-8')
                if prop_name in content:
                    count += 1

        return count

    def check_all(self) -> List[PropIssue]:
        """检查所有核心道具的贯穿情况"""
        issues = []
        ch1_props = self.extract_ch1_props()

        for prop in ch1_props:
            reappear_count = self.check_reappear(prop)

            if reappear_count == 0:
                issues.append(PropIssue(
                    chapter='ch001',
                    prop_name=prop,
                    severity='HIGH',
                    description=f"核心道具'{prop}'在360章中完全消失（0次再现）"
                ))
            elif reappear_count < 3:
                issues.append(PropIssue(
                    chapter='ch001',
                    prop_name=prop,
                    severity='MEDIUM',
                    description=f"核心道具'{prop}'再现不足（仅{reappear_count}次）"
                ))

        return issues

    def generate_report(self, issues: List[PropIssue]) -> str:
        """生成检查报告"""
        if not issues:
            return "✅ 核心道具贯穿检查通过：所有道具均有适当再现"

        high_issues = [i for i in issues if i.severity == 'HIGH']
        medium_issues = [i for i in issues if i.severity == 'MEDIUM']

        report = ["# 核心道具贯穿检查报告\n"]
        report.append(f"## 汇总\n")
        report.append(f"- HIGH级问题: {len(high_issues)}")
        report.append(f"- MEDIUM级问题: {len(medium_issues)}\n")

        if high_issues:
            report.append("## 🔴 必须修复\n")
            for issue in high_issues:
                report.append(f"- {issue.description}")

        return "\n".join(report)

def main():
    import sys
    checker = CorePropsChecker()
    issues = checker.check_all()

    if issues:
        print(checker.generate_report(issues))
        high_count = len([i for i in issues if i.severity == 'HIGH'])
        if high_count > 0:
            sys.exit(1)
    else:
        print("✅ 核心道具贯穿检查通过：所有道具均有适当再现")
        sys.exit(0)

if __name__ == '__main__':
    main()