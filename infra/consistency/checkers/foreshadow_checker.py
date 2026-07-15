#!/usr/bin/env python3
"""
伏笔回收检查器

检查伏笔是否正确埋设和回收

检测维度：
1. 伏笔未回收：已到预期回收章节，伏笔未揭示
2. 伏笔过度揭示：一次性揭示太多伏笔
3. 伏笔逻辑矛盾：回收方式与埋设矛盾
4. Core级伏笔强制回收检测：从章节标记中提取伏笔并验证回收
5. Ripple状态机对齐检测：检测涟漪是否按时平复
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from ..engine.data_structures import CheckerType, ForeshadowAlert, Issue, IssueLocation, IssueSeverity
from .base_checker import BaseChecker


def _get_ripple_state_and_grace():
    from infra.world_model.data_structures import RippleState
    from infra.world_model.lifecycle import RESOLUTION_GRACE_CH
    return RippleState, RESOLUTION_GRACE_CH


class _RippleRegistryLike(Protocol):
    """Ripple Registry 最小接口 (Protocol 解耦)"""

    def list_all(self) -> tuple: ...


@dataclass
class ForeshadowIssue:
    chapter: str
    foreshadow_text: str
    level: str
    severity: str
    description: str


@dataclass
class PlotThread:
    """伏笔"""
    id: str
    content: str
    introduced_chapter: int
    expected_resolve_chapter: int
    actual_resolve_chapter: Optional[int] = None
    status: str = "unresolved"  # unresolved, resolved, overdue
    resolve_type: Optional[str] = None  # full, partial, wrong


class ForeshadowChecker(BaseChecker):
    """伏笔回收检查器"""
    _checker_type = CheckerType.FORESHADOW

    LEVEL_THRESHOLDS = {
        'core': 1.0,    # 100% must be recycled
        'normal': 0.8,  # 80%回收率
        'edge': 0.5    # 50%回收率
    }

    def __init__(self, rules: Optional[Dict[str, Any]] = None, chapters_dir: Optional[str] = None):
        super().__init__(self._checker_type)
        self.rules = rules or {}
        self._plot_threads: Dict[str, PlotThread] = {}
        self._pending_foreshadow: List[str] = []  # 待回收的伏笔关键词
        if chapters_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            chapters_dir = project_root / '03_内容仓库' / '04_正文'
        self.chapters_dir = Path(chapters_dir)
        self._chapter_content_cache: Dict[int, Optional[str]] = {}

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """
        检查伏笔回收

        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
            context: 上下文，包含：
                - plot_threads: List[PlotThread] 伏笔列表
                - new_foreshadow: List[str] 本章新埋的伏笔

        Returns:
            Issue列表
        """
        issues = []
        context = context or {}
        plot_threads = context.get("plot_threads", [])
        new_foreshadow = context.get("new_foreshadow", [])

        # 更新伏笔状态
        for thread in plot_threads:
            self._plot_threads[thread.id] = thread

        # 检查未回收的伏笔
        issues.extend(self._check_unresolved_foreshadow(chapter_num))

        # 检查过度揭示
        issues.extend(self._check_over_resolution(chapter_content, chapter_num))

        # 检查新埋的伏笔
        issues.extend(self._check_new_foreshadow(chapter_content, chapter_num, new_foreshadow))

        return issues

    def _check_unresolved_foreshadow(self, chapter_num: int) -> List[Issue]:
        """检查未回收的伏笔"""
        issues = []

        # 检查已到回收期的伏笔
        for thread_id, thread in self._plot_threads.items():
            if thread.status == "unresolved":
                if chapter_num >= thread.expected_resolve_chapter:
                    # 延迟回收
                    delay = chapter_num - thread.expected_resolve_chapter
                    if delay >= 3:  # 延迟3章以上
                        issues.append(Issue(
                            id=f"foreshadow_{chapter_num}_{thread_id}_延迟回收",
                            severity=IssueSeverity.P2,
                            checker_type=CheckerType.FORESHADOW,
                            issue_type="伏笔未及时回收",
                            title="伏笔回收延迟",
                            description=f"伏笔\"{thread.content}\"应在ch{thread.expected_resolve_chapter}回收，已延迟{delay}章",
                            location=IssueLocation(chapter=chapter_num),
                            evidence=f"预期回收章节：ch{thread.expected_resolve_chapter}",
                            suggestion="考虑在本章或近期章节回收该伏笔",
                            character=None
                        ))

        return issues

    def _check_over_resolution(
        self,
        content: str,
        chapter_num: int
    ) -> List[Issue]:
        """检查过度揭示"""
        issues = []

        # 统计本章中"揭示"类关键词的数量
        reveal_keywords = ["原来", "真相是", "事实证明", "揭示", "暴露"]
        reveal_count = sum(content.count(kw) for kw in reveal_keywords)

        if reveal_count > 3:
            issues.append(Issue(
                id=f"foreshadow_{chapter_num}_过度揭示",
                severity=IssueSeverity.P2,
                checker_type=CheckerType.FORESHADOW,
                issue_type="伏笔过度揭示",
                title="一次性揭示太多",
                description=f"本章有{reveal_count}处揭示/揭示类表达，可能过于密集",
                location=IssueLocation(chapter=chapter_num),
                evidence=f"揭示关键词出现次数：{reveal_count}",
                suggestion="考虑分散揭示，或将部分揭示留到后续章节",
                character=None
            ))

        return issues

    def _check_new_foreshadow(
        self,
        content: str,
        chapter_num: int,
        new_foreshadow: List[str]
    ) -> List[Issue]:
        """检查新埋的伏笔"""
        issues = []

        if not new_foreshadow:
            return issues

        # 检查新伏笔是否有足够的回收预期
        for foreshadow in new_foreshadow:
            # 简化：检查伏笔是否明确
            if len(foreshadow) < 10:  # 太短的伏笔可能不明确
                issues.append(Issue(
                    id=f"foreshadow_{chapter_num}_伏笔不明确",
                    severity=IssueSeverity.P3,
                    checker_type=CheckerType.FORESHADOW,
                    issue_type="伏笔不明确",
                    title="伏笔描述不够明确",
                    description=f"伏笔\"{foreshadow}\"可能不够明确，读者可能无法识别",
                    location=IssueLocation(chapter=chapter_num),
                    evidence=f"伏笔长度：{len(foreshadow)}字符",
                    suggestion="增强伏笔的明确性或添加更多线索",
                    character=None
                ))

        return issues

    def add_foreshadow(
        self,
        thread_id: str,
        content: str,
        introduced_chapter: int,
        expected_resolve_chapter: int
    ):
        """添加伏笔"""
        self._plot_threads[thread_id] = PlotThread(
            id=thread_id,
            content=content,
            introduced_chapter=introduced_chapter,
            expected_resolve_chapter=expected_resolve_chapter
        )

    def resolve_foreshadow(self, thread_id: str, chapter_num: int):
        """标记伏笔已回收"""
        if thread_id in self._plot_threads:
            self._plot_threads[thread_id].status = "resolved"
            self._plot_threads[thread_id].actual_resolve_chapter = chapter_num

    def get_unresolved_count(self) -> int:
        """获取未回收伏笔数量"""
        return sum(1 for t in self._plot_threads.values() if t.status == "unresolved")

    def _detect_overdue_foreshadow(self, current_chapter: int) -> List[ForeshadowAlert]:
        """检测超期未回收的伏笔"""
        alerts = []
        for thread_id, thread in self._plot_threads.items():
            if thread.status == "unresolved" and current_chapter > thread.expected_resolve_chapter:
                delay = current_chapter - thread.expected_resolve_chapter
                severity = IssueSeverity.P1 if delay >= 3 else IssueSeverity.P2
                message = f"伏笔\"{thread.content}\"应在ch{thread.expected_resolve_chapter}回收，已延迟{delay}章仍未回收"
                alerts.append(ForeshadowAlert(
                    alert_type="overdue",
                    thread_id=thread_id,
                    content=thread.content,
                    introduced_chapter=thread.introduced_chapter,
                    expected_resolve_chapter=thread.expected_resolve_chapter,
                    current_chapter=current_chapter,
                    delay_chapters=delay,
                    severity=severity,
                    message=message
                ))
        return alerts

    def _detect_approaching_deadline(self, current_chapter: int) -> List[ForeshadowAlert]:
        """检测即将到期的伏笔（2章以内）"""
        alerts = []
        for thread_id, thread in self._plot_threads.items():
            if thread.status == "unresolved":
                distance = thread.expected_resolve_chapter - current_chapter
                if 0 < distance <= 2:
                    message = f"伏笔\"{thread.content}\"还剩{distance}章即将到期（ch{thread.expected_resolve_chapter}），请注意回收"
                    alerts.append(ForeshadowAlert(
                        alert_type="approaching",
                        thread_id=thread_id,
                        content=thread.content,
                        introduced_chapter=thread.introduced_chapter,
                        expected_resolve_chapter=thread.expected_resolve_chapter,
                        current_chapter=current_chapter,
                        delay_chapters=0,
                        severity=IssueSeverity.P3,
                        message=message
                    ))
        return alerts

    def get_foreshadow_alerts(self, current_chapter: int) -> List[ForeshadowAlert]:
        """获取当前章节的所有伏笔预警"""
        alerts = []
        alerts.extend(self._detect_overdue_foreshadow(current_chapter))
        alerts.extend(self._detect_approaching_deadline(current_chapter))
        return alerts

    def get_overdue_count(self) -> int:
        """获取超期伏笔数量"""
        current_chapter = self._get_current_chapter()
        return self.get_overdue_count_at(current_chapter)

    def _get_current_chapter(self) -> int:
        """获取当前章节号（目录中最高章节号）"""
        chapter_files = list(self.chapters_dir.glob('ch*.md'))
        if not chapter_files:
            return 0
        max_chapter = 0
        for ch_file in chapter_files:
            import re
            match = re.match(r'ch(\d+)\.md', ch_file.name)
            if match:
                ch_num = int(match.group(1))
                if ch_num > max_chapter:
                    max_chapter = ch_num
        return max_chapter

    def get_overdue_count_at(self, current_chapter: int) -> int:
        """获取当前超期伏笔数量"""
        return len(self._detect_overdue_foreshadow(current_chapter))

    def check_realtime(self, text: str, **kwargs) -> List[Issue]:
        """实时检查（简化版）"""
        return []

    def _get_chapter_content(self, ch_num: int) -> Optional[str]:
        """缓存章节内容,避免 _is_recycled 在循环中重复 read_text

        返回 None 表示文件不存在 (与 read_text 抛 FileNotFoundError 区分)。
        """
        if ch_num not in self._chapter_content_cache:
            ch_file = self.chapters_dir / f'ch{ch_num:03d}.md'
            if ch_file.exists():
                self._chapter_content_cache[ch_num] = ch_file.read_text(encoding='utf-8')
            else:
                self._chapter_content_cache[ch_num] = None
        return self._chapter_content_cache[ch_num]

    def clear_chapter_cache(self) -> None:
        """清空章节缓存 (测试隔离用)

        正常业务代码不需要调,check_all 跨章节会自然填充新缓存。
        仅当磁盘文件被外部修改 (e.g. 修复 pipeline 写入新内容)
        时需要主动清空,否则会读到旧内容。
        """
        self._chapter_content_cache.clear()

    def check_chapter(self, chapter_num: int) -> list[ForeshadowIssue]:
        """检查单章的伏笔记录"""
        ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
        if not ch_file.exists():
            return []

        content = ch_file.read_text(encoding='utf-8')
        issues = []

        foreshadow_pattern = r'【伏笔:(\w+):(.+?):([\w-]+)】'
        matches = re.findall(foreshadow_pattern, content)

        for level, foreshadow_text, expect_range in matches:
            if self._is_recycled(foreshadow_text, chapter_num, expect_range):
                continue

            severity = 'HIGH' if level == 'core' else 'MEDIUM'
            issues.append(ForeshadowIssue(
                chapter=f'ch{chapter_num:03d}',
                foreshadow_text=foreshadow_text,
                level=level,
                severity=severity,
                description=f"Core级伏笔'{foreshadow_text}'未在{expect_range}内回收"
            ))

        return issues

    def _is_recycled(self, foreshadow_text: str, start_chapter: int, expect_range: str) -> bool:
        """检查伏笔是否被回收"""
        match = re.match(r'ch(\d+)-ch(\d+)', expect_range)
        if not match:
            return False

        start = int(match.group(1))
        end = int(match.group(2))
        keywords = foreshadow_text.split('/')

        for ch_num in range(start, end + 1):
            if ch_num <= start_chapter:
                continue
            content = self._get_chapter_content(ch_num)
            if content is None:
                continue
            if any(kw.strip() in content for kw in keywords):
                return True

        return False

    def check_ripple_alignment(
        self,
        ripple_registry: _RippleRegistryLike,
        current_ch: int,
    ) -> List[Issue]:
        """涟漪状态机对齐检测

        检测 3 类问题:
        1. 超期未平复 (P1): OPEN/PROPAGATING/RESOLVING + planned_resolve_ch < current_ch - 5
        2. 计划缺失 (P3): OPEN/PROPAGATING + planned_resolve_ch is None
        3. RESOLVED 状态 + resolved_ch 在合理范围 (current_ch - 5..current_ch) → 无 issue

        Args:
            ripple_registry: 实现 list_all 的对象
            current_ch: 当前章节号

        Returns:
            Issue 列表 (空 = 无问题)
        """
        RippleState, RESOLUTION_GRACE_CH = _get_ripple_state_and_grace()
        issues: List[Issue] = []

        for ripple in ripple_registry.list_all():
            state = ripple.state

            if state == RippleState.RESOLVED:
                if ripple.resolved_ch is not None:
                    if current_ch - ripple.resolved_ch <= RESOLUTION_GRACE_CH:
                        continue
                continue

            if ripple.planned_resolve_ch is None:
                issues.append(Issue(
                    id=f"ripple_alignment_no_plan_{ripple.ripple_id}",
                    severity=IssueSeverity.P3,
                    checker_type=CheckerType.FORESHADOW,
                    issue_type="ripple_no_planned_resolve",
                    title=f"涟漪 {ripple.ripple_id} 缺少平复计划",
                    description=(
                        f"状态 {state.value} 的涟漪未设置 planned_resolve_ch,"
                        f"无法评估是否超期"
                    ),
                    location=IssueLocation(chapter=current_ch),
                    evidence=f"ripple_id={ripple.ripple_id}, state={state.value}",
                    suggestion="设置 planned_resolve_ch (预估章节号)",
                ))
                continue

            overdue_chs = current_ch - ripple.planned_resolve_ch
            if overdue_chs > RESOLUTION_GRACE_CH:
                issues.append(Issue(
                    id=f"ripple_alignment_overdue_{ripple.ripple_id}",
                    severity=IssueSeverity.P1,
                    checker_type=CheckerType.FORESHADOW,
                    issue_type="ripple_overdue",
                    title=f"涟漪 {ripple.ripple_id} 超期未平复",
                    description=(
                        f"状态 {state.value} 的涟漪 planned_resolve_ch={ripple.planned_resolve_ch},"
                        f"当前章节 {current_ch},已超 {overdue_chs} 章 (> grace {RESOLUTION_GRACE_CH})"
                    ),
                    location=IssueLocation(chapter=current_ch),
                    evidence=(
                        f"ripple_id={ripple.ripple_id}, planned={ripple.planned_resolve_ch},"
                        f" current={current_ch}, overdue={overdue_chs}"
                    ),
                    suggestion="立即调用 resolve 平复,或调整 planned_resolve_ch",
                ))

        return issues

    def check_all(self) -> list[ForeshadowIssue]:
        """检查所有章节的伏笔"""
        all_issues = []

        for ch_file in sorted(self.chapters_dir.glob('ch*.md')):
            match = re.match(r'ch(\d+)\.md', ch_file.name)
            if match:
                ch_num = int(match.group(1))
                issues = self.check_chapter(ch_num)
                all_issues.extend(issues)

        return all_issues

    def generate_report(self, issues: list[ForeshadowIssue]) -> str:
        """生成检查报告"""
        if not issues:
            return "✅ 伏笔回收检查通过：无core级伏笔遗漏"

        core_issues = [i for i in issues if i.level == 'core']
        normal_issues = [i for i in issues if i.level == 'normal']
        edge_issues = [i for i in issues if i.level == 'edge']

        report = ["# 伏笔回收检查报告\n"]
        report.append("## 汇总\n")
        report.append(f"- Core级未回收: {len(core_issues)}")
        report.append(f"- Normal级未回收: {len(normal_issues)}")
        report.append(f"- Edge级未回收: {len(edge_issues)}\n")

        if core_issues:
            report.append("## 🔴 Core级未回收（必须修复）\n")
            for issue in core_issues:
                report.append(f"- [{issue.chapter}] {issue.description}")

        return "\n".join(report)


def main():
    import sys
    checker = ForeshadowChecker()
    issues = checker.check_all()

    if issues:
        print(checker.generate_report(issues))
        sys.exit(1)
    else:
        print("✅ 伏笔回收检查通过：无core级伏笔遗漏")
        sys.exit(0)


if __name__ == '__main__':
    main()
