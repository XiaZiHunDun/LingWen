#!/usr/bin/env python3
"""
运行检查器动作 - 在Hook中触发一致性检查或质量门禁
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

# 添加项目根目录到路径，以便导入检查器模块
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from hooks.actions.base import ActionResult, BaseAction


class RunCheckerAction(BaseAction):
    """
    运行检查器动作

    在Hook上下文中触发一致性检查或质量门禁

    params:
        checker: 检查器名称（如 "consistency_engine", "quality_gate"）
        chapter_range: 检查范围（如 "current", "all", "1-10"）
        threshold: 质量阈值（可选，如 "Bronze", "Silver", "Gold"）
    """

    @property
    def action_type(self) -> str:
        return "run_checker"

    def execute(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ActionResult:
        """
        执行检查器

        Args:
            params: 包含 checker, chapter_range 等
            context: 执行上下文

        Returns:
            ActionResult with checker output
        """
        # 验证参数
        valid, error = self.validate_params(params, ["checker"])
        if not valid:
            return ActionResult(success=False, error=error)

        checker_name = params["checker"]
        chapter_range = params.get("chapter_range", "current")
        threshold = params.get("threshold")

        try:
            # 根据checker名称加载对应的检查器
            if checker_name == "consistency_engine":
                result = self._run_consistency_check(chapter_range, context)
            elif checker_name == "quality_gate":
                result = self._run_quality_gate(chapter_range, threshold, context)
            elif checker_name == "auto_consistency_checker":
                result = self._run_auto_consistency_check(chapter_range, context)
            else:
                return ActionResult(
                    success=False,
                    error=f"Unknown checker: {checker_name}"
                )

            return ActionResult(success=True, output=result)

        except Exception as e:
            return ActionResult(success=False, error=str(e))

    def _run_consistency_check(
        self,
        chapter_range: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """运行一致性检查引擎"""
        # 动态导入避免循环依赖
        import re
        from consistency.engine.consistency_engine import ConsistencyEngine
        from consistency.engine.data_structures import CheckScope

        # 从context获取chapters_dir，如果没有则从项目根目录推导
        if "chapters_dir" in context:
            chapters_dir = context["chapters_dir"]
        else:
            # 从项目根目录推导章节目录
            from pathlib import Path
            project_root = Path(__file__).resolve().parents[2]
            chapters_dir = str(project_root / "03_内容仓库" / "04_正文")

        engine = ConsistencyEngine()
        # Register all checkers
        engine.checkers = engine._init_checkers()

        # Run checks for the chapter range
        if chapter_range == "all":
            range_start, range_end = 1, 360
        elif chapter_range == "current":
            chapter_id = context.get("chapter_id", "ch001")
            match = re.search(r'ch(\d+)', chapter_id)
            range_start = int(match.group(1)) if match else 1
            range_end = range_start
        elif "-" in str(chapter_range):
            parts = str(chapter_range).split("-")
            range_start, range_end = int(parts[0]), int(parts[1])
        else:
            range_start = range_end = int(chapter_range)

        chapter_results = []
        for ch_num in range(range_start, range_end + 1):
            chapter_content = context.get("chapter_content", "")
            if "chapters_dir" in context:
                ch_path = Path(context["chapters_dir"]) / f"ch{ch_num:03d}.md"
                if ch_path.exists():
                    with open(ch_path, 'r', encoding='utf-8') as f:
                        chapter_content = f.read()
            report = engine.check_chapter(ch_num, chapter_content, scope=CheckScope.ALL)
            chapter_results.append(report.to_dict())

        # Summarize
        total_issues = sum(len(r.get('issues', [])) for r in chapter_results)
        summary = {
            "checked_chapters": len(chapter_results),
            "total_issues": total_issues,
            "chapter_range": f"{range_start}-{range_end}"
        }
        return {
            "checker": "consistency_engine",
            "results": chapter_results,
            "summary": summary,
            "chapter_range": chapter_range
        }

    def _get_chapters_dir(self, context: Dict[str, Any]) -> str:
        """获取章节目录路径"""
        if "chapters_dir" in context:
            return context["chapters_dir"]
        # 从项目根目录推导章节目录
        project_root = Path(__file__).resolve().parents[2]
        return str(project_root / "03_内容仓库" / "04_正文")

    def _run_quality_gate(
        self,
        chapter_range: str,
        threshold: str | None,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """运行质量门禁检查"""
        from tools.consistency.run_quality_checks import run_quality_checks

        chapters_dir = self._get_chapters_dir(context)

        # 调用质量检查
        results = run_quality_checks(
            chapters_dir=chapters_dir,
            chapter_range=chapter_range,
            threshold=threshold
        )

        return {
            "checker": "quality_gate",
            "passed": results.get("passed", False),
            "score": results.get("score", 0),
            "threshold": threshold,
            "chapter_range": chapter_range
        }

    def _run_auto_consistency_check(
        self,
        chapter_range: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """运行自动一致性检查器"""
        from tools.consistency.auto_consistency_checker import check_chapter

        chapter_id = context.get("chapter_id", "")
        if not chapter_id:
            return {
                "checker": "auto_consistency_checker",
                "error": "No chapter_id in context"
            }

        chapters_dir = self._get_chapters_dir(context)

        issues = check_chapter(chapter_id, chapters_dir)

        return {
            "checker": "auto_consistency_checker",
            "chapter_id": chapter_id,
            "issues_found": len(issues),
            "issues": issues,
            "chapter_range": chapter_range
        }