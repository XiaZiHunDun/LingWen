#!/usr/bin/env python3
"""
360章全方位质量检查脚本

使用MiniMax M2.7 API进行深度检查，消耗全部3000次额度
三阶段：快速扫描(900次) → 深度分析(1200次) → 精准验证(900次)
"""

import asyncio
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.ai_service import MiniMaxProvider, ProviderConfig


@dataclass
class CheckResult:
    """检查结果"""
    chapter: int
    dimension: str
    severity: str  # P0, P1, P2, P3, PASS
    issue_type: Optional[str] = None
    description: str = ""
    evidence: str = ""
    suggestion: str = ""


class ComprehensiveQualityChecker:
    """全方位质量检查器"""

    def __init__(self, api_key: Optional[str] = None, max_concurrency: int = 8):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        self.max_concurrency = max_concurrency
        self.chapters_dir = PROJECT_ROOT / "03_内容仓库" / "04_正文"
        self.output_dir = PROJECT_ROOT / "06_意见仓库" / "09_全面质量检查"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化AI Provider
        self.provider = None
        if self.api_key:
            config = ProviderConfig(
                api_key=self.api_key,
                model="MiniMax-M2.7",
                timeout=180,
                max_retries=3
            )
            self.provider = MiniMaxProvider(config)
            print("[INIT] MiniMax M2.7 Provider已初始化")

        # API调用计数
        self.api_calls_made = 0
        self.budget = 3000

        # 检查结果存储
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
            # 移除markdown标题
            lines = content.split('\n')
            if lines and lines[0].startswith('#'):
                lines = lines[1:]
            # 移除章节分隔线
            content = '\n'.join(lines)
            return content.strip()

    def get_context_chapters(self, chapter_num: int, before: int = 3, after: int = 3) -> Dict[int, str]:
        """获取前后章节内容用于上下文分析"""
        context = {}
        for cn in range(chapter_num - before, chapter_num + after + 1):
            if cn > 0 and cn != chapter_num:
                content = self.read_chapter(cn)
                if content:
                    context[cn] = content[:500]  # 只取前500字作为上下文
        return context

    # ==================== LLMr批量检查 ====================

    async def check_chapter_llm(self, chapter_num: int, check_type: str, prompt: str) -> List[CheckResult]:
        """使用LLM检查单个章节"""
        if not self.provider:
            return []
        if self.api_calls_made >= self.budget:
            print("[BUDGET] API额度已耗尽，停止调用")
            return []

        self.api_calls_made += 1
        content = self.read_chapter(chapter_num)
        if not content:
            return []

        try:
            # 截取合理长度（API限制）
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

            # 解析响应
            results = self._parse_check_response(chapter_num, check_type, response)
            return results

        except Exception as e:
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
            # 尝试解析为单对象
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
            except json.JSONDecodeError:
                logger.debug(f"JSON解析失败 (chapter {chapter_num})")
        return results

    # ==================== 检查提示词模板 ====================

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

    # ==================== 批量执行 ====================

    async def phase1_scan(self) -> int:
        """
        第一阶段：快速扫描（900次调用）
        - 逻辑一致性：360章
        - 情感节奏：360章
        - 章节钩子：180章
        """
        print("\n" + "="*60)
        print("第一阶段：快速扫描")
        print("="*60)

        chapters = [f[0] for f in self.get_chapter_files()]
        calls_used = 0

        # 1. 逻辑一致性检查 - 360章
        print("\n[Phase 1.1] 逻辑一致性检查 - 360章")
        asyncio.Semaphore(self.max_concurrency)
        tasks = []

        for chapter_num in chapters:
            task = self.check_chapter_llm(chapter_num, "logic_consistency", self.LOGIC_CONSISTENCY_PROMPT)
            tasks.append(task)

        # 分批执行，每批50章
        batch_size = 50
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i+batch_size]
            results = await asyncio.gather(*batch)
            for r in results:
                self.results.extend(r)
            calls_used += len(batch)
            print(f"  进度: {min(i+batch_size, len(tasks))}/{len(tasks)} 章, 已用API: {calls_used}")
            await asyncio.sleep(0.5)  # 避免过快

        print(f"  逻辑一致性检查完成，已调用API: {calls_used}")

        # 2. 情感节奏检查 - 180章（抽样50%）
        print("\n[Phase 1.2] 情感节奏检查 - 180章")
        emotion_chapters = chapters[:180]
        tasks = []

        for chapter_num in emotion_chapters:
            task = self.check_chapter_llm(chapter_num, "emotional_pacing", self.EMOTIONAL_PACING_PROMPT)
            tasks.append(task)

        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i+batch_size]
            results = await asyncio.gather(*batch)
            for r in results:
                self.results.extend(r)
            calls_used += len(batch)
            print(f"  进度: {min(i+batch_size, len(tasks))}/{len(tasks)} 章, 已用API: {calls_used}")
            await asyncio.sleep(0.5)

        print(f"  情感节奏检查完成，已调用API: {calls_used}")

        # 3. 章节钩子检查 - 180章
        print("\n[Phase 1.3] 章节钩子检查 - 180章")
        tasks = []

        for chapter_num in chapters[:180]:
            task = self.check_chapter_llm(chapter_num, "chapter_hook", self.CHAPTER_HOOK_PROMPT)
            tasks.append(task)

        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i+batch_size]
            results = await asyncio.gather(*batch)
            for r in results:
                self.results.extend(r)
            calls_used += len(batch)
            print(f"  进度: {min(i+batch_size, len(tasks))}/{len(tasks)} 章, 已用API: {calls_used}")
            await asyncio.sleep(0.5)

        print(f"  章节钩子检查完成，已调用API: {calls_used}")

        return calls_used

    async def phase2_deep_analysis(self, start_calls: int) -> int:
        """
        第二阶段：深度分析（1200次调用）
        - 角色一致性：360章
        - 伏笔回收验证：180章
        - 关键章节复查：660章（约220章重点章节×3次）
        """
        print("\n" + "="*60)
        print("第二阶段：深度分析")
        print("="*60)

        chapters = [f[0] for f in self.get_chapter_files()]
        calls_used = 0
        batch_size = 40

        # 1. 角色一致性检查 - 360章
        print("\n[Phase 2.1] 角色一致性检查 - 360章")
        tasks = []

        for chapter_num in chapters:
            task = self.check_chapter_llm(chapter_num, "character_consistency", self.CHARACTER_CONSISTENCY_PROMPT)
            tasks.append(task)

        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i+batch_size]
            results = await asyncio.gather(*batch)
            for r in results:
                self.results.extend(r)
            calls_used += len(batch)
            print(f"  进度: {min(i+batch_size, len(tasks))}/{len(tasks)} 章, 已用API: {calls_used}")
            await asyncio.sleep(0.5)

        print(f"  角色一致性检查完成，已调用API: {calls_used}")

        # 2. 伏笔回收验证 - 180章
        print("\n[Phase 2.2] 伏笔回收验证 - 180章")
        tasks = []

        for chapter_num in chapters[:180]:
            task = self.check_chapter_llm(chapter_num, "foreshadow_recovery", self.LOGIC_CONSISTENCY_PROMPT)
            tasks.append(task)

        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i+batch_size]
            results = await asyncio.gather(*batch)
            for r in results:
                self.results.extend(r)
            calls_used += len(batch)
            print(f"  进度: {min(i+batch_size, len(tasks))}/{len(tasks)} 章, 已用API: {calls_used}")
            await asyncio.sleep(0.5)

        print(f"  伏笔回收验证完成，已调用API: {calls_used}")

        # 3. 关键章节复查（约220章×3次 = 660次）
        print("\n[Phase 2.3] 关键章节复查 - 660次")
        # 选取关键章节：每10章选1章作为关键章节
        key_chapters = []
        for i, cn in enumerate(chapters):
            if i % 10 == 0:  # 每10章选1个
                key_chapters.append(cn)

        # 每章复查3次
        review_tasks = []
        for _ in range(3):
            for chapter_num in key_chapters:
                task = self.check_chapter_llm(chapter_num, "key_review", self.LOGIC_CONSISTENCY_PROMPT)
                review_tasks.append(task)

        # 分批执行
        for i in range(0, len(review_tasks), batch_size):
            batch = review_tasks[i:i+batch_size]
            results = await asyncio.gather(*batch)
            for r in results:
                self.results.extend(r)
            calls_used += len(batch)
            print(f"  复查进度: {min(i+batch_size, len(review_tasks))}/{len(review_tasks)}, 已用API: {calls_used}")
            await asyncio.sleep(0.5)

        print(f"  关键章节复查完成，已调用API: {calls_used}")

        return calls_used - start_calls

    async def phase3_verification(self, start_calls: int) -> int:
        """
        第三阶段：精准验证（900次调用）
        - P0问题章节复查（每章6次）
        - P1问题章节复查（每章4次）
        - 交叉验证：100章×3次
        - 机动储备：剩余额度
        """
        print("\n" + "="*60)
        print("第三阶段：精准验证")
        print("="*60)

        # 找出有问题的章节
        problem_chapters = set()
        for r in self.results:
            if r.severity in ['P0', 'P1']:
                problem_chapters.add(r.chapter)

        calls_used = 0
        batch_size = 30

        # P0问题章节复查（每章6次）
        if problem_chapters:
            p0_chapters = list(problem_chapters)[:15]  # 最多15章
            print(f"\n[Phase 3.1] P0问题章节复查 - {len(p0_chapters)}章 × 6次 = {len(p0_chapters)*6}次")

            review_tasks = []
            for _ in range(6):
                for chapter_num in p0_chapters:
                    task = self.check_chapter_llm(chapter_num, "p0_review", self.LOGIC_CONSISTENCY_PROMPT)
                    review_tasks.append(task)

            for i in range(0, len(review_tasks), batch_size):
                batch = review_tasks[i:i+batch_size]
                results = await asyncio.gather(*batch)
                for r in results:
                    self.results.extend(r)
                calls_used += len(batch)
                print(f"  P0复查: {min(i+batch_size, len(review_tasks))}/{len(review_tasks)}, 已用API: {calls_used}")
                await asyncio.sleep(0.5)

        # P1问题章节复查（每章4次）
        if len(problem_chapters) > 15:
            p1_chapters = list(problem_chapters)[15:40]  # 15-40章
            print(f"\n[Phase 3.2] P1问题章节复查 - {len(p1_chapters)}章 × 4次 = {len(p1_chapters)*4}次")

            review_tasks = []
            for _ in range(4):
                for chapter_num in p1_chapters:
                    task = self.check_chapter_llm(chapter_num, "p1_review", self.LOGIC_CONSISTENCY_PROMPT)
                    review_tasks.append(task)

            for i in range(0, len(review_tasks), batch_size):
                batch = review_tasks[i:i+batch_size]
                results = await asyncio.gather(*batch)
                for r in results:
                    self.results.extend(r)
                calls_used += len(batch)
                print(f"  P1复查: {min(i+batch_size, len(review_tasks))}/{len(review_tasks)}, 已用API: {calls_used}")
                await asyncio.sleep(0.5)

        # 交叉验证：100章×3次
        chapters = [f[0] for f in self.get_chapter_files()]
        cross_chapters = chapters[:100]
        print("\n[Phase 3.3] 交叉验证 - 100章 × 3次 = 300次")

        cross_tasks = []
        for _ in range(3):
            for chapter_num in cross_chapters:
                task = self.check_chapter_llm(chapter_num, "cross_validation", self.LOGIC_CONSISTENCY_PROMPT)
                cross_tasks.append(task)

        for i in range(0, len(cross_tasks), batch_size):
            batch = cross_tasks[i:i+batch_size]
            results = await asyncio.gather(*batch)
            for r in results:
                self.results.extend(r)
            calls_used += len(batch)
            print(f"  交叉验证: {min(i+batch_size, len(cross_tasks))}/{len(cross_tasks)}, 已用API: {calls_used}")
            await asyncio.sleep(0.5)

        return calls_used - start_calls

    async def run_full_check(self):
        """运行完整的三阶段检查"""
        print("\n" + "="*60)
        print("《星陨纪元》360章全方位质量检查")
        print(f"总API额度: {self.budget}次")
        print("MiniMax模型: MiniMax-M2.7")
        print("="*60)

        total_calls = 0

        # 第一阶段
        phase1_calls = await self.phase1_scan()
        total_calls += phase1_calls
        print(f"\n[Phase 1 完成] 已使用API: {total_calls}/{self.budget}")

        if total_calls >= self.budget:
            print("[BUDGET] 额度已耗尽，保存当前结果")
            self.save_results(total_calls)
            return

        # 第二阶段
        remaining = self.budget - total_calls
        print(f"\n剩余额度: {remaining}次")

        if remaining >= 1200:
            phase2_calls = await self.phase2_deep_analysis(total_calls)
            total_calls += phase2_calls
            print(f"\n[Phase 2 完成] 已使用API: {total_calls}/{self.budget}")

        if total_calls >= self.budget:
            print("[BUDGET] 额度已耗尽，保存当前结果")
            self.save_results(total_calls)
            return

        # 第三阶段
        remaining = self.budget - total_calls
        print(f"\n剩余额度: {remaining}次")

        if remaining >= 900:
            phase3_calls = await self.phase3_verification(total_calls)
            total_calls += phase3_calls
            print(f"\n[Phase 3 完成] 已使用API: {total_calls}/{self.budget}")

        # 保存结果
        self.save_results(total_calls)

    def save_results(self, total_calls: int):
        """保存检查结果"""
        # 按章节和严重程度组织
        by_chapter = {}
        for r in self.results:
            if r.chapter not in by_chapter:
                by_chapter[r.chapter] = []
            by_chapter[r.chapter].append(r)

        by_severity = {'P0': [], 'P1': [], 'P2': [], 'P3': [], 'PASS': []}
        for r in self.results:
            if r.severity in by_severity:
                by_severity[r.severity].append(r)

        # 生成报告
        report = {
            'audit_date': datetime.now().isoformat(),
            'total_chapters': 360,
            'api_calls_made': total_calls,
            'budget_used': f"{total_calls}/{self.budget}",
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

        # 保存
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.output_dir / f"comprehensive_quality_report_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        latest_file = self.output_dir / "comprehensive_quality_report_latest.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 打印摘要
        print("\n" + "="*60)
        print("检查完成摘要")
        print("="*60)
        print(f"API调用: {total_calls}/{self.budget}")
        print(f"发现问题: {len(self.results)}")
        print(f"有问题的章节: {len(by_chapter)}")
        print("\n按严重程度:")
        print(f"  P0 (致命): {len(by_severity['P0'])}")
        print(f"  P1 (严重): {len(by_severity['P1'])}")
        print(f"  P2 (轻微): {len(by_severity['P2'])}")
        print(f"  P3 (提示): {len(by_severity['P3'])}")
        print(f"  PASS: {len(by_severity['PASS'])}")
        print(f"\n报告已保存: {report_file}")

    def print_summary(self):
        """打印问题摘要"""
        by_chapter = {}
        for r in self.results:
            if r.chapter not in by_chapter:
                by_chapter[r.chapter] = []
            by_chapter[r.chapter].append(r)

        print("\n问题章节摘要：")
        for chapter in sorted(by_chapter.keys())[:20]:
            issues = by_chapter[chapter]
            p0 = sum(1 for i in issues if i.severity == 'P0')
            p1 = sum(1 for i in issues if i.severity == 'P1')
            p2 = sum(1 for i in issues if i.severity == 'P2')
            print(f"  ch{chapter:03d}: P0={p0}, P1={p1}, P2={p2}")


async def main():
    """主函数"""
    api_key = os.getenv("MINIMAX_API_KEY")

    if not api_key:
        print("[ERROR] 需要设置MINIMAX_API_KEY环境变量")
        return

    checker = ComprehensiveQualityChecker(api_key=api_key, max_concurrency=8)

    # 运行完整检查
    await checker.run_full_check()

    # 打印摘要
    checker.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
