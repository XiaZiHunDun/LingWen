#!/usr/bin/env python3
"""
LLM逻辑一致性审核脚本

逐章调用LLM审核小说内容的逻辑矛盾问题
并发限制: 最多10个并发API调用
"""

import asyncio
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.ai_service import MiniMaxProvider, ProviderConfig


@dataclass
class LogicIssue:
    """逻辑问题"""
    chapter: int
    issue_type: str  # death_contradiction, state_contradiction, etc.
    severity: str  # P0, P1, P2
    description: str
    evidence: str
    suggestion: str


class LogicConsistencyAuditor:
    """逻辑一致性审核器"""

    def __init__(self, max_concurrency: int = 10, api_key: Optional[str] = None):
        self.max_concurrency = max_concurrency
        self.api_key = api_key
        self.chapters_dir = PROJECT_ROOT / "03_内容仓库" / "04_正文"
        self.output_dir = PROJECT_ROOT / "06_意见仓库" / "08_逻辑审核"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化AI Provider (使用MiniMax)
        self.provider = None
        if self.api_key:
            config = ProviderConfig(
                api_key=self.api_key,
                model="MiniMax-M2.7",
                timeout=120,
                max_retries=3
            )
            self.provider = MiniMaxProvider(config)
        self.audit_prompt_template = """你是一个严格但合理的小说审核员。请审核以下小说章节，检查真正的逻辑矛盾问题。

【重要】请区分以下两种情况：

A. 真正的逻辑矛盾（需要修复）：
   - 死亡/状态矛盾：人物明确死亡后又出现/说话（如"已经死了"但下一段能思考）
   - 位置矛盾：同一时间点人物出现在两个互斥位置
   - 时间线矛盾：事件顺序明显错误（如"第二天"出现在"当天"之前）
   - 能力矛盾：人物使用一个从未被描述、也无法解释的能力
   - 物品矛盾：关键物品消失后无法解释地再次出现

B. 设定合理内容（不需要修复）：
   - 超自然设定：化为星光、意识连接、预知能力等奇幻设定
   - 伏笔悬念：模糊的威胁描述、神秘的观察者
   - 叙事视角：内心独白、全知视角的描述
   - 情感描写：角色的情绪反应和内心变化
   - 模糊表述：未明确说"死了"就不算死亡矛盾

请仔细阅读以下章节内容：

---
{content}
---

对于每个发现的真正逻辑问题，请用以下JSON格式返回（如果没有发现问题，返回空数组）：
[
  {{
    "issue_type": "death_contradiction",
    "severity": "P0",
    "description": "问题描述",
    "evidence": "具体证据（原文摘录）",
    "suggestion": "修复建议"
  }}
]

只返回JSON数组，不要有其他内容。"""

    def get_chapter_files(self) -> List[tuple]:
        """获取所有章节文件"""
        chapter_files = []
        for f in sorted(self.chapters_dir.glob("ch*.md")):
            # 提取章节号
            match = re.search(r'ch(\d+)', f.name)
            if match:
                chapter_num = int(match.group(1))
                chapter_files.append((chapter_num, f))
        return chapter_files

    def read_chapter(self, chapter_num: int) -> Optional[str]:
        """读取章节内容"""
        chapter_file = self.chapters_dir / f"ch{chapter_num:03d}.md"
        if not chapter_file.exists():
            return None
        with open(chapter_file, 'r', encoding='utf-8') as f:
            return f.read()

    async def audit_chapter_llm(self, chapter_num: int, semaphore: asyncio.Semaphore) -> List[LogicIssue]:
        """使用LLM审核单个章节"""
        async with semaphore:
            content = self.read_chapter(chapter_num)
            if not content:
                return []

            # 如果没有provider（dry-run模式），跳过API调用
            if not self.provider:
                print(f"[SKIP] ch{chapter_num:03d} - 无API Key，跳过")
                return []

            try:
                prompt = self.audit_prompt_template.format(content=content)
                response = await asyncio.to_thread(
                    self.provider.generate,
                    prompt
                )

                # 解析JSON响应
                issues = []
                try:
                    # 提取JSON数组
                    json_match = re.search(r'\[.*\]', response, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group())
                        for item in data:
                            issues.append(LogicIssue(
                                chapter=chapter_num,
                                issue_type=item.get('issue_type', 'unknown'),
                                severity=item.get('severity', 'P2'),
                                description=item.get('description', ''),
                                evidence=item.get('evidence', ''),
                                suggestion=item.get('suggestion', '')
                            ))
                except json.JSONDecodeError:
                    print(f"[PARSE ERROR] ch{chapter_num:03d}: 无法解析LLM响应")

                status = "✓" if issues else "✓无问题"
                print(f"[AUDIT] ch{chapter_num:03d} - {status}")
                return issues

            except Exception as e:
                print(f"[ERROR] ch{chapter_num:03d}: {e}")
                return []

    async def audit_all_chapters(self) -> List[LogicIssue]:
        """审核所有章节"""
        chapter_files = self.get_chapter_files()
        print(f"开始审核 {len(chapter_files)} 个章节...")
        print(f"并发限制: {self.max_concurrency}")

        semaphore = asyncio.Semaphore(self.max_concurrency)
        tasks = [
            self.audit_chapter_llm(chapter_num, semaphore)
            for chapter_num, _ in chapter_files
        ]

        results = await asyncio.gather(*tasks)

        # 合并所有问题
        all_issues = []
        for issues in results:
            all_issues.extend(issues)

        return all_issues

    def generate_report(self, issues: List[LogicIssue]) -> Dict[str, Any]:
        """生成审核报告"""
        # 按章节分组
        by_chapter = {}
        for issue in issues:
            if issue.chapter not in by_chapter:
                by_chapter[issue.chapter] = []
            by_chapter[issue.chapter].append(issue)

        # 按严重程度分组
        by_severity = {'P0': [], 'P1': [], 'P2': [], 'P3': []}
        for issue in issues:
            by_severity[issue.severity].append(issue)

        report = {
            'audit_date': datetime.now().isoformat(),
            'total_chapters': len(self.get_chapter_files()),
            'total_issues': len(issues),
            'by_severity': {
                'P0': len(by_severity['P0']),
                'P1': len(by_severity['P1']),
                'P2': len(by_severity['P2'])
            },
            'chapters_with_issues': len(by_chapter),
            'issues': [
                {
                    'chapter': issue.chapter,
                    'issue_type': issue.issue_type,
                    'severity': issue.severity,
                    'description': issue.description,
                    'evidence': issue.evidence,
                    'suggestion': issue.suggestion
                }
                for issue in sorted(issues, key=lambda x: (x.chapter, x.severity))
            ]
        }
        return report

    def save_report(self, report: Dict[str, Any]) -> None:
        """保存报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.output_dir / f"logic_audit_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 同时保存一个latest.json方便查阅
        latest_file = self.output_dir / "logic_audit_latest.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n报告已保存: {report_file}")
        print(f"最新报告: {latest_file}")

    def print_summary(self, report: Dict[str, Any]) -> None:
        """打印摘要"""
        print("\n" + "="*60)
        print("逻辑一致性审核报告")
        print("="*60)
        print(f"审核章节: {report['total_chapters']}")
        print(f"发现问题: {report['total_issues']}")
        print(f"有问题的章节: {report['chapters_with_issues']}")
        print(f"\n按严重程度:")
        print(f"  P0 (致命): {report['by_severity'].get('P0', 0)}")
        print(f"  P1 (严重): {report['by_severity'].get('P1', 0)}")
        print(f"  P2 (轻微): {report['by_severity'].get('P2', 0)}")
        print(f"  P3 (提示): {report['by_severity'].get('P3', 0)}")

        if report['issues']:
            print(f"\n前10个P0/P1问题:")
            count = 0
            for issue in report['issues']:
                if issue['severity'] in ['P0', 'P1'] and count < 10:
                    print(f"\n  ch{issue['chapter']:03d} [{issue['severity']}] {issue['issue_type']}")
                    print(f"    描述: {issue['description'][:80]}...")
                    print(f"    证据: {issue['evidence'][:80]}...")
                    count += 1

        print("\n" + "="*60)


async def main():
    import argparse

    parser = argparse.ArgumentParser(description='LLM逻辑一致性审核')
    parser.add_argument('--concurrency', '-c', type=int, default=10,
                        help='最大并发数 (默认10)')
    parser.add_argument('--api-key', '-k', type=str, default=None,
                        help='Anthropic API Key (或设置ANTHROPIC_API_KEY环境变量)')
    parser.add_argument('--dry-run', action='store_true',
                        help='仅测试前3章，不调用API')
    parser.add_argument('--chapters', type=str, default=None,
                        help='审核指定章节，如 "1-10" 或 "5,10,15"')
    args = parser.parse_args()

    # 支持环境变量
    api_key = args.api_key or os.environ.get('ANTHROPIC_API_KEY')

    auditor = LogicConsistencyAuditor(
        max_concurrency=args.concurrency,
        api_key=api_key
    )

    print("开始LLM逻辑审核...")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if api_key:
        print("[OK] API Key loaded")
    else:
        print("[WARN] 未设置API Key，将使用占位符")

    if args.dry_run:
        # 仅测试前3章
        print("\n[DRY RUN 模式 - 仅测试前3章]")
        chapter_files = auditor.get_chapter_files()[:3]
        semaphore = asyncio.Semaphore(args.concurrency)
        tasks = [
            auditor.audit_chapter_llm(chapter_num, semaphore)
            for chapter_num, _ in chapter_files
        ]
        results = await asyncio.gather(*tasks)
        all_issues = []
        for issues in results:
            all_issues.extend(issues)
        report = auditor.generate_report(all_issues)
        auditor.print_summary(report)
    else:
        issues = await auditor.audit_all_chapters()
        report = auditor.generate_report(issues)
        auditor.save_report(report)
        auditor.print_summary(report)


if __name__ == '__main__':
    asyncio.run(main())