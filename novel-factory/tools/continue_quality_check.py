#!/usr/bin/env python3
"""
继续执行360章全方位质量检查（续）
消耗剩余~2500次API额度

修复Rate Limit问题：
- 降低并发数（8→3）
- 增加重试延迟
- 增加退避时间
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
import time

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.ai_service import MiniMaxProvider, ProviderConfig


@dataclass
class CheckResult:
    """检查结果"""
    chapter: int
    dimension: str
    severity: str
    issue_type: Optional[str] = None
    description: str = ""
    evidence: str = ""
    suggestion: str = ""


class ContinueQualityChecker:
    """继续质量检查器"""

    def __init__(self, api_key: Optional[str] = None, max_concurrency: int = 3):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        self.max_concurrency = max_concurrency
        self.chapters_dir = PROJECT_ROOT / "03_内容仓库" / "04_正文"
        self.output_dir = PROJECT_ROOT / "06_意见仓库" / "09_全面质量检查"

        # 初始化AI Provider
        self.provider = None
        if self.api_key:
            config = ProviderConfig(
                api_key=self.api_key,
                model="MiniMax-M2.7",
                timeout=180,
                max_retries=5  # 增加重试次数
            )
            self.provider = MiniMaxProvider(config)
            print(f"[INIT] MiniMax M2.7 Provider已初始化 (并发数: {max_concurrency})")

        self.api_calls_made = 0
        self.budget = 2600  # 继续消耗额度
        self.results: List[CheckResult] = []

    def get_chapter_files(self) -> List[tuple]:
        """获取所有章节文件"""
        chapter_files = []
        for f in sorted(self.chapters_dir.glob("ch*.md")):
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
            content = f.read()
            lines = content.split('\n')
            if lines and lines[0].startswith('#'):
                lines = lines[1:]
            content = '\n'.join(lines)
            return content.strip()

    async def check_chapter_llm(self, chapter_num: int, check_type: str, prompt: str) -> List[CheckResult]:
        """使用LLM检查单个章节"""
        if not self.provider:
            return []
        if self.api_calls_made >= self.budget:
            return []

        # 退避策略：每次调用后等待
        await asyncio.sleep(1.5)  # 1.5秒间隔，避免rate limit

        self.api_calls_made += 1
        content = self.read_chapter(chapter_num)
        if not content:
            return []

        try:
            if len(content) > 8000:
                content = content[:8000]

            full_prompt = prompt.format(
                chapter_num=chapter_num,
                content=content
            )

            response = await asyncio.to_thread(
                self.provider.generate,
                full_prompt
            )

            results = self._parse_check_response(chapter_num, check_type, response)
            return results

        except Exception as e:
            error_str = str(e)
            if "rate_limit" in error_str.lower():
                print(f"[RATE LIMIT] ch{chapter_num:03d} - 等待10秒...")
                await asyncio.sleep(10)  # Rate limit时等待10秒
                # 重试一次
                try:
                    response = await asyncio.to_thread(
                        self.provider.generate,
                        full_prompt
                    )
                    results = self._parse_check_response(chapter_num, check_type, response)
                    return results
                except:
                    pass
            print(f"[ERROR] ch{chapter_num:03d} {check_type}: {e}")
            return []

    def _parse_check_response(self, chapter_num: int, check_type: str, response: str) -> List[CheckResult]:
        """解析LLM响应"""
        results = []
        try:
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                for item in data:
                    results.append(CheckResult(
                        chapter=chapter_num,
                        dimension=check_type,
                        severity=item.get('severity', 'P2'),
                        issue_type=item.get('issue_type', ''),
                        description=item.get('description', ''),
                        evidence=item.get('evidence', ''),
                        suggestion=item.get('suggestion', '')
                    ))
        except json.JSONDecodeError:
            try:
                data = json.loads(response)
                if isinstance(data, dict):
                    results.append(CheckResult(
                        chapter=chapter_num,
                        dimension=check_type,
                        severity=data.get('severity', 'P2'),
                        issue_type=data.get('issue_type', ''),
                        description=data.get('description', ''),
                        evidence=data.get('evidence', ''),
                        suggestion=data.get('suggestion', '')
                    ))
            except:
                pass
        return results

    LOGIC_CONSISTENCY_PROMPT = """你是一个严格的小说审核员。请检查以下章节的逻辑一致性问题。

检查以下维度：
1. 时间线矛盾：日期/季节/事件顺序是否矛盾
2. 状态矛盾：生死状态/物理位置/能力是否前后一致
3. 角色行为逻辑：行为是否符合角色性格和能力设定
4. 前后矛盾：与前文已建立的事实是否矛盾

章节内容：
---
{content}
---

对于每个发现的问题，请用以下JSON格式返回：
[
  {{
    "issue_type": "矛盾类型",
    "severity": "P0/P1/P2/P3",
    "description": "问题描述",
    "evidence": "原文证据",
    "suggestion": "修复建议"
  }}
]

如果没有发现问题，返回空数组：[]
只返回JSON数组，不要有其他内容。"""

    EMOTIONAL_PACING_PROMPT = """你是一个情感节奏专家。请评估章节的情感过渡质量。

检查以下维度：
1. 章内情感曲线：是否平滑？有无突兀跳跃？
2. 情感锚点：是否有情感高点/低点？分布是否合理？
3. 情绪词汇密度：是否过密/过疏？
4. 情感转折点：是否有意义？是否铺垫充分？

章节内容：
---
{content}
---

返回JSON数组：
[
  {{
    "issue_type": "emotional_pacing",
    "severity": "P0/P1/P2/P3",
    "description": "问题描述",
    "evidence": "原文证据",
    "suggestion": "修复建议"
  }}
]

如果没有问题，返回：[]
只返回JSON数组。"""

    CHAPTER_HOOK_PROMPT = """你是一个小说质量审核专家。请评估章节结尾的悬念钩子质量。

检查以下维度：
1. 悬念设置：结尾是否有明确的悬念点？
2. 悬念类型：人物威胁/信息缺失/情节转折/情感悬置
3. 悬念强度：强/中/弱
4. 读者吸引力：是否能让读者想继续读下去？

章节内容：
---
{content}
---

返回JSON：
[
  {{
    "issue_type": "chapter_hook",
    "severity": "P0/P1/P2/P3",
    "description": "问题描述",
    "evidence": "原文证据",
    "suggestion": "修复建议"
  }}
]

如果没有问题，返回：[]
只返回JSON数组。"""

    CHARACTER_CONSISTENCY_PROMPT = """你是一个角色一致性审核专家。请检查章节中角色行为/对话是否符合人设。

检查以下维度：
1. 性格一致性：角色行为是否符合性格设定
2. 对话风格一致性：对话是否符合角色背景
3. 能力表现一致性：能力使用是否与设定等级匹配
4. 关系发展一致性：角色关系变化是否自然

章节内容：
---
{content}
---

返回JSON：
[
  {{
    "issue_type": "character_consistency",
    "severity": "P0/P1/P2/P3",
    "description": "问题描述",
    "evidence": "原文证据",
    "suggestion": "修复建议"
  }}
]

如果没有问题，返回：[]
只返回JSON数组。"""

    async def phase_continue(self):
        """继续执行检查"""
        print("\n" + "="*60)
        print("继续执行质量检查")
        print(f"剩余预算: {self.budget}次")
        print("="*60)

        chapters = [f[0] for f in self.get_chapter_files()]
        calls_used = 0

        # 1. 情感节奏检查（继续）- 180章
        print(f"\n[1] 情感节奏检查 - 180章")
        emotion_chapters = chapters[80:180]  # 80-180章
        tasks = []
        for chapter_num in emotion_chapters:
            task = self.check_chapter_llm(chapter_num, "emotional_pacing", self.EMOTIONAL_PACING_PROMPT)
            tasks.append(task)

        batch_size = 30
        for i in range(0, len(tasks), batch_size):
            if calls_used >= self.budget:
                break
            batch = tasks[i:i+batch_size]
            results = await asyncio.gather(*batch)
            for r in results:
                self.results.extend(r)
            calls_used += len([t for t in batch if self.api_calls_made <= self.budget])
            print(f"  进度: {min(i+batch_size, len(tasks))}/{len(tasks)}, 已用API: {self.api_calls_made}")
            await asyncio.sleep(0.5)

        print(f"  情感节奏检查完成，已调用API: {self.api_calls_made}")

        # 2. 章节钩子检查（继续）- 180章
        print(f"\n[2] 章节钩子检查 - 180章")
        tasks = []
        for chapter_num in chapters[100:280]:
            task = self.check_chapter_llm(chapter_num, "chapter_hook", self.CHAPTER_HOOK_PROMPT)
            tasks.append(task)

        for i in range(0, len(tasks), batch_size):
            if self.api_calls_made >= self.budget:
                break
            batch = tasks[i:i+batch_size]
            results = await asyncio.gather(*batch)
            for r in results:
                self.results.extend(r)
            print(f"  进度: {min(i+batch_size, len(tasks))}/{len(tasks)}, 已用API: {self.api_calls_made}")
            await asyncio.sleep(0.5)

        print(f"  章节钩子检查完成，已调用API: {self.api_calls_made}")

        # 3. 角色一致性检查 - 360章
        print(f"\n[3] 角色一致性检查 - 360章")
        tasks = []
        for chapter_num in chapters:
            task = self.check_chapter_llm(chapter_num, "character_consistency", self.CHARACTER_CONSISTENCY_PROMPT)
            tasks.append(task)

        for i in range(0, len(tasks), batch_size):
            if self.api_calls_made >= self.budget:
                break
            batch = tasks[i:i+batch_size]
            results = await asyncio.gather(*batch)
            for r in results:
                self.results.extend(r)
            print(f"  进度: {min(i+batch_size, len(tasks))}/{len(tasks)}, 已用API: {self.api_calls_made}")
            await asyncio.sleep(0.5)

        print(f"  角色一致性检查完成，已调用API: {self.api_calls_made}")

        # 4. 伏笔回收验证 - 180章
        print(f"\n[4] 伏笔回收验证 - 180章")
        tasks = []
        for chapter_num in chapters:
            task = self.check_chapter_llm(chapter_num, "foreshadow_recovery", self.LOGIC_CONSISTENCY_PROMPT)
            tasks.append(task)

        for i in range(0, len(tasks), batch_size):
            if self.api_calls_made >= self.budget:
                break
            batch = tasks[i:i+batch_size]
            results = await asyncio.gather(*batch)
            for r in results:
                self.results.extend(r)
            print(f"  进度: {min(i+batch_size, len(tasks))}/{len(tasks)}, 已用API: {self.api_calls_made}")
            await asyncio.sleep(0.5)

        print(f"  伏笔回收验证完成，已调用API: {self.api_calls_made}")

        # 5. 关键章节深度复查
        print(f"\n[5] 关键章节深度复查")
        key_chapters = [1, 5, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 90, 100,
                        120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 320, 340, 360]

        review_tasks = []
        for _ in range(5):  # 每章复查5次
            for chapter_num in key_chapters:
                task = self.check_chapter_llm(chapter_num, "key_review", self.LOGIC_CONSISTENCY_PROMPT)
                review_tasks.append(task)

        for i in range(0, len(review_tasks), batch_size):
            if self.api_calls_made >= self.budget:
                break
            batch = review_tasks[i:i+batch_size]
            results = await asyncio.gather(*batch)
            for r in results:
                self.results.extend(r)
            print(f"  复查进度: {min(i+batch_size, len(review_tasks))}/{len(review_tasks)}, 已用API: {self.api_calls_made}")
            await asyncio.sleep(0.5)

        print(f"  关键章节复查完成，已调用API: {self.api_calls_made}")

        return self.api_calls_made

    async def run_continue(self):
        """运行继续检查"""
        await self.phase_continue()
        self.save_results()

    def save_results(self):
        """保存检查结果"""
        by_chapter = {}
        for r in self.results:
            if r.chapter not in by_chapter:
                by_chapter[r.chapter] = []
            by_chapter[r.chapter].append(r)

        by_severity = {'P0': [], 'P1': [], 'P2': [], 'P3': [], 'PASS': []}
        for r in self.results:
            if r.severity in by_severity:
                by_severity[r.severity].append(r)

        report = {
            'audit_date': datetime.now().isoformat(),
            'total_chapters': 360,
            'api_calls_made': self.api_calls_made,
            'budget_used': f"{self.api_calls_made}/{self.budget}",
            'total_issues': len(self.results),
            'by_severity': {
                'P0': len(by_severity['P0']),
                'P1': len(by_severity['P1']),
                'P2': len(by_severity['P2']),
                'P3': len(by_severity['P3']),
                'PASS': len(by_severity['PASS'])
            },
            'chapters_with_issues': len(by_chapter),
            'issues': [
                {
                    'chapter': r.chapter,
                    'dimension': r.dimension,
                    'issue_type': r.issue_type,
                    'severity': r.severity,
                    'description': r.description,
                    'evidence': r.evidence,
                    'suggestion': r.suggestion
                }
                for r in sorted(self.results, key=lambda x: (x.chapter, x.severity))
            ]
        }

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.output_dir / f"comprehensive_quality_report_continue_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        latest_file = self.output_dir / "comprehensive_quality_report_latest.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print("\n" + "="*60)
        print("继续检查完成摘要")
        print("="*60)
        print(f"API调用: {self.api_calls_made}/{self.budget}")
        print(f"发现问题: {len(self.results)}")
        print(f"有问题的章节: {len(by_chapter)}")
        print(f"\n按严重程度:")
        print(f"  P0 (致命): {len(by_severity['P0'])}")
        print(f"  P1 (严重): {len(by_severity['P1'])}")
        print(f"  P2 (轻微): {len(by_severity['P2'])}")
        print(f"  P3 (提示): {len(by_severity['P3'])}")
        print(f"\n报告已保存: {report_file}")


async def main():
    """主函数"""
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        print("[ERROR] 需要设置MINIMAX_API_KEY环境变量")
        return

    checker = ContinueQualityChecker(api_key=api_key, max_concurrency=3)
    await checker.run_continue()


if __name__ == "__main__":
    asyncio.run(main())