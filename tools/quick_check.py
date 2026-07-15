#!/usr/bin/env python3
"""快速质量检查 - 简化版"""
import asyncio
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.ai_service import MiniMaxProvider, ProviderConfig


@dataclass
class CheckResult:
    chapter: int
    dimension: str
    severity: str
    issue_type: str = ""
    description: str = ""
    evidence: str = ""
    suggestion: str = ""


class QuickChecker:
    def __init__(self):
        self.api_key = os.getenv("MINIMAX_API_KEY")
        config = ProviderConfig(api_key=self.api_key, model="MiniMax-M2.7", timeout=120, max_retries=3)
        self.provider = MiniMaxProvider(config)
        self.chapters_dir = PROJECT_ROOT / "03_内容仓库" / "04_正文"
        self.output_dir = PROJECT_ROOT / "06_意见仓库" / "09_全面质量检查"
        self.results = []

    def get_chapters(self):
        chapters = []
        for f in sorted(self.chapters_dir.glob("ch*.md")):
            match = re.search(r'ch(\d+)', f.name)
            if match:
                chapters.append(int(match.group(1)))
        return chapters

    def read(self, num):
        with open(self.chapters_dir / f"ch{num:03d}.md", 'r') as f:
            return f.read()

    async def check_one(self, num):
        content = self.read(num)
        if len(content) > 6000:
            content = content[:6000]

        prompt = f"""你是小说质量审核专家。请检查以下章节的逻辑问题。

检查维度：时间线矛盾、状态矛盾、角色行为逻辑、前后矛盾

章节内容：
---
{content[:5000]}
---

返回JSON数组格式的问题列表，如无问题返回空数组：
[
  {{"issue_type": "类型", "severity": "P0/P1/P2", "description": "描述", "evidence": "证据", "suggestion": "建议"}}
]

只返回JSON，不要其他内容。"""

        try:
            response = await asyncio.to_thread(self.provider.generate, prompt)
            # 解析JSON
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                for item in data:
                    self.results.append(CheckResult(
                        chapter=num,
                        dimension="logic",
                        severity=item.get('severity', 'P2'),
                        issue_type=item.get('issue_type', ''),
                        description=item.get('description', ''),
                        evidence=item.get('evidence', ''),
                        suggestion=item.get('suggestion', '')
                    ))
            print(f"[OK] ch{num:03d} - 发现 {len([r for r in self.results if r.chapter == num])} 个问题")
        except Exception as e:
            print(f"[ERROR] ch{num:03d}: {e}")

    async def run(self, target_calls=2500):
        chapters = self.get_chapters()
        print(f"开始检查 {len(chapters)} 章，目标 {target_calls} 次调用")

        calls = 0
        for i, num in enumerate(chapters):
            if calls >= target_calls:
                break
            await self.check_one(num)
            calls += 1
            if (i + 1) % 20 == 0:
                print(f"进度: {i+1}/{len(chapters)}, API调用: {calls}")
            await asyncio.sleep(1)  # 避免rate limit

        self.save()

    def save(self):
        by_chapter = {}
        for r in self.results:
            if r.chapter not in by_chapter:
                by_chapter[r.chapter] = []
            by_chapter[r.chapter].append(r)

        by_severity = {'P0': 0, 'P1': 0, 'P2': 0, 'P3': 0}
        for r in self.results:
            if r.severity in by_severity:
                by_severity[r.severity] += 1

        report = {
            'audit_date': datetime.now().isoformat(),
            'total_issues': len(self.results),
            'by_severity': by_severity,
            'chapters_with_issues': len(by_chapter),
            'issues': [
                {'chapter': r.chapter, 'dimension': r.dimension, 'issue_type': r.issue_type,
                 'severity': r.severity, 'description': r.description, 'evidence': r.evidence, 'suggestion': r.suggestion}
                for r in sorted(self.results, key=lambda x: (x.chapter, x.severity))
            ]
        }

        datetime.now().strftime('%Y%m%d_%H%M%S')
        latest = self.output_dir / "comprehensive_quality_report_latest.json"
        with open(latest, 'w') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n完成！发现问题: {len(self.results)}")
        print(f"P0: {by_severity['P0']}, P1: {by_severity['P1']}, P2: {by_severity['P2']}")
        print(f"报告已保存: {latest}")


async def main():
    checker = QuickChecker()
    await checker.run(target_calls=2500)

if __name__ == "__main__":
    asyncio.run(main())
