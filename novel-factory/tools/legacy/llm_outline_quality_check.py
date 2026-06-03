#!/usr/bin/env python3
"""
大纲层级LLM质检工具 - PHASE_X_LLM_OUTLINE_QUALITY
对全文大纲、卷大纲、阶段大纲进行基于LLM的深度质量检测

使用方法:
    # 全文大纲质检
    python tools/llm_outline_quality_check.py --check full --level volume

    # 卷大纲质检（3卷）
    python tools/llm_outline_quality_check.py --check volume --volume 1
    python tools/llm_outline_quality_check.py --check volume --volume all

    # 阶段大纲质检（可指定卷和阶段）
    python tools/llm_outline_quality_check.py --check stage --volume 1
    python tools/llm_outline_quality_check.py --check stage --volume all --stage all

    # 全量质检
    python tools/llm_outline_quality_check.py --check all

    # 输出报告
    python tools/llm_outline_quality_check.py --check full --output logs/outline_quality_report.json
"""

import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.llm_service import LLMService


@dataclass
class OutlineIssue:
    """大纲问题"""
    level: str  # 'full', 'volume', 'stage', 'chapter'
    chapter_range: str
    issue_type: str
    severity: str  # P0, P1, P2
    description: str
    location: str
    suggestion: str = ""


@dataclass
class OutlineQualityReport:
    """大纲质检报告"""
    level: str
    target: str  # e.g., "全文大纲", "卷1", "阶段1-4"
    issues: List[OutlineIssue] = field(default_factory=list)
    score: float = 0.0
    llm_calls: int = 0
    timestamp: str = ""
    recommendations: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "target": self.target,
            "issues": [asdict(i) for i in self.issues],
            "score": self.score,
            "llm_calls": self.llm_calls,
            "timestamp": self.timestamp,
            "recommendations": self.recommendations
        }


class OutlinePathManager:
    """大纲路径管理器（单例）"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.project_root = PROJECT_ROOT
        self.outline_root = self.project_root / "03_内容仓库"
        # 各层目录
        self.full_outline_dir = self.outline_root / "01_全文总体大纲"
        self.volume_outline_dir = self.outline_root / "02_卷大纲"
        self.stage_outline_dir = self.outline_root / "03_阶段大纲"
        self.body_dir = self.outline_root / "04_正文"

    def get_full_outline_path(self) -> Optional[Path]:
        """获取全文大纲路径"""
        candidates = list(self.full_outline_dir.glob("*.md"))
        if not candidates:
            return None
        # 返回最新的或最大的
        return max(candidates, key=lambda p: p.stat().st_size)

    def get_volume_outline_paths(self, volume: int = None) -> List[Path]:
        """获取卷大纲路径"""
        if volume:
            path = self.volume_outline_dir / f"卷{volume}_大纲.md"
            return [path] if path.exists() else []
        return list(self.volume_outline_dir.glob("卷*_大纲.md"))

    def get_stage_outline_paths(self, volume: int = None, stage: int = None) -> List[Path]:
        """获取阶段大纲路径"""
        if volume and stage:
            path = self.stage_outline_dir / f"卷{volume}_阶段{stage}_大纲.md"
            return [path] if path.exists() else []
        if volume:
            return list(self.stage_outline_dir.glob(f"卷{volume}_阶段*_大纲.md"))
        return list(self.stage_outline_dir.glob("卷*_阶段*_大纲.md"))

    def get_chapter_outline_paths(self, chapters: List[int] = None) -> List[Path]:
        """获取章节大纲路径

        Args:
            chapters: 指定章节号列表，如 [1, 2, 3] 或 None（全部）
        Returns:
            章节大纲文件路径列表
        """
        if chapters:
            return [self.body_dir / f"ch{ch:03d}_大纲.md" for ch in chapters
                    if (self.body_dir / f"ch{ch:03d}_大纲.md").exists()]
        return list(self.body_dir.glob("ch*_大纲.md"))

    def load_outline_content(self, path: Path) -> Optional[str]:
        """加载大纲内容"""
        if not path or not path.exists():
            return None
        return path.read_text(encoding='utf-8')


class LLMOutlineChecker:
    """基于LLM的大纲质量检测器"""

    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm = llm_service or LLMService()
        self.path_mgr = OutlinePathManager()

    def check_full_outline(self, outline_path: Path = None) -> OutlineQualityReport:
        """
        全文大纲LLM质检
        检查：360章全貌一致性、主线逻辑链、伏笔全局布局
        """
        report = OutlineQualityReport(level="full", target="全文大纲")

        if not outline_path:
            outline_path = self.path_mgr.get_full_outline_path()
        if not outline_path:
            report.issues.append(OutlineIssue(
                level="full", chapter_range="N/A", issue_type="file_not_found",
                severity="P0", description="未找到全文大纲文件",
                location="01_全文总体大纲/"
            ))
            return report

        content = self.path_mgr.load_outline_content(outline_path)
        if not content:
            return report

        # 加载正文样例（用于交叉验证）
        sample_chapters = {}
        for ch_num in [1, 50, 100, 150, 200, 250, 300, 350, 360]:
            ch_path = self.path_mgr.body_dir / f"ch{ch_num:03d}.md"
            if ch_path.exists():
                sample_chapters[ch_num] = ch_path.read_text(encoding='utf-8')[:500]

        prompt = f"""你是小说大纲审核专家，负责全文大纲的深度质检。

全文大纲内容:
{content[:8000]}

正文样例（用于交叉验证大纲与实际内容的一致性）:
{json.dumps(sample_chapters, ensure_ascii=False)[:3000]}

请进行以下维度的检测：

1. 逻辑一致性（P0）
   - 360章整体逻辑链是否通顺
   - 起承转合是否合理
   - 高潮与结局的铺垫是否充分

2. 结构完整性（P1）
   - 三卷划分是否合理
   - 各卷占比是否均衡
   - 阶段划分是否清晰

3. 伏笔全局布局（P1）
   - 伏笔是否分布均匀
   - 重要伏笔是否有对应回收节点
   - 伏笔密度是否合理

4. 角色弧光一致性（P2）
   - 主要角色成长轨迹是否清晰
   - 角色弧光是否与大纲设定一致

5. 设定统一性（P2）
   - 力量体系是否前后一致
   - 世界观设定是否有矛盾

返回JSON格式：
{{"issues": [{{"level": "full", "chapter_range": "ch1-ch360", "issue_type": "...", "severity": "P0/P1/P2", "description": "...", "location": "...", "suggestion": "..."}}], "score": 0.0-1.0, "recommendations": ["..."]}}
"""

        response = self.llm.generate(
            prompt=prompt,
            system="你是一个专业的小说大纲审核专家，擅长发现全局性问题。",
            model="default"
        )
        report.llm_calls = 1

        try:
            data = json.loads(response)
            issues = data.get("issues", [])
            report.issues = [OutlineIssue(**i) for i in issues]
            report.score = data.get("score", 0.5)
            report.recommendations = data.get("recommendations", [])
        except json.JSONDecodeError:
            report.score = 0.5
            report.issues.append(OutlineIssue(
                level="full", chapter_range="ch1-ch360", issue_type="parse_error",
                severity="P2", description="LLM返回格式解析失败",
                location="全文大纲", suggestion="请检查LLM输出格式"
            ))

        return report

    def check_volume_outline(self, volume: int = None) -> List[OutlineQualityReport]:
        """
        卷大纲LLM质检
        检查：卷内阶段衔接、卷主题一致性、跨卷角色状态
        """
        reports = []
        paths = self.path_mgr.get_volume_outline_paths(volume)

        for path in paths:
            report = OutlineQualityReport(
                level="volume",
                target=path.stem.replace("_大纲", "").replace("卷", "卷")
            )

            content = self.path_mgr.load_outline_content(path)
            if not content:
                report.issues.append(OutlineIssue(
                    level="volume", chapter_range="N/A", issue_type="file_not_found",
                    severity="P0", description=f"未找到卷大纲: {path.name}",
                    location=str(path)
                ))
                reports.append(report)
                continue

            # 提取卷号
            import re
            vol_match = re.search(r'卷(\d+)', path.name)
            vol_num = int(vol_match.group(1)) if vol_match else 0

            # 获取其他卷大纲（用于跨卷一致性检查）
            other_volumes = []
            for other_path in paths:
                if other_path != path:
                    other_content = self.path_mgr.load_outline_content(other_path)
                    if other_content:
                        other_volumes.append(other_content[:2000])

            prompt = f"""你是卷大纲审核专家，负责检测卷内和跨卷的一致性问题。

当前卷大纲（第{vol_num}卷）:
{content[:5000]}

其他卷大纲摘要（用于跨卷一致性检查）:
{chr(10).join(other_volumes[:2000]) if other_volumes else '无'}

请进行以下维度的检测：

1. 卷内阶段衔接（P0）
   - 阶段之间过渡是否自然
   - 阶段起止是否与卷大纲匹配

2. 卷主题一致性（P1）
   - 各阶段是否服务同一主题
   - 阶段之间逻辑是否连贯

3. 跨卷角色状态（P1）
   - 角色状态在不同卷间是否连贯
   - 角色在当前卷的出入是否合理

4. 卷内伏笔一致性（P2）
   - 本卷伏笔是否与全文大纲一致
   - 伏笔回收是否在本卷内完成或跨卷延续

返回JSON格式：
{{"issues": [{{"level": "volume", "chapter_range": "ch{start}-ch{end}", "issue_type": "...", "severity": "P0/P1/P2", "description": "...", "location": "...", "suggestion": "..."}}], "score": 0.0-1.0, "recommendations": ["..."]}}
"""

            response = self.llm.generate(
                prompt=prompt,
                system="你是一个专业的卷大纲审核专家，擅长阶段衔接和跨卷一致性分析。",
                model="default"
            )
            report.llm_calls = 1

            try:
                data = json.loads(response)
                issues = data.get("issues", [])
                report.issues = [OutlineIssue(**i) for i in issues]
                report.score = data.get("score", 0.5)
                report.recommendations = data.get("recommendations", [])
            except json.JSONDecodeError:
                report.score = 0.5

            reports.append(report)

        return reports

    def check_stage_outline(self, volume: int = None, stage: int = None) -> List[OutlineQualityReport]:
        """
        阶段大纲LLM质检
        检查：阶段内逻辑自洽、人物弧光连贯性、与卷大纲对齐
        """
        reports = []
        paths = self.path_mgr.get_stage_outline_paths(volume, stage)

        for path in paths:
            report = OutlineQualityReport(level="stage", target=path.stem)

            content = self.path_mgr.load_outline_content(path)
            if not content:
                report.issues.append(OutlineIssue(
                    level="stage", chapter_range="N/A", issue_type="file_not_found",
                    severity="P0", description=f"未找到阶段大纲: {path.name}",
                    location=str(path)
                ))
                reports.append(report)
                continue

            # 提取卷号和阶段号
            import re
            vol_match = re.search(r'卷(\d+)', path.name)
            stage_match = re.search(r'阶段(\d+)', path.name)
            vol_num = int(vol_match.group(1)) if vol_match else 0
            stage_num = int(stage_match.group(1)) if stage_match else 0

            # 获取对应卷大纲（用于对齐检查）
            vol_paths = self.path_mgr.get_volume_outline_paths(vol_num)
            vol_content = ""
            if vol_paths:
                vol_content = self.path_mgr.load_outline_content(vol_paths[0])[:2000]

            prompt = f"""你是阶段大纲审核专家，负责检测阶段大纲的内部一致性和对齐问题。

阶段大纲（卷{vol_num} 阶段{stage_num}）:
{content[:4000]}

对应卷大纲摘要（用于对齐检查）:
{vol_content if vol_content else '无'}

请进行以下维度的检测：

1. 阶段内逻辑自洽（P0）
   - 核心事件是否自相矛盾
   - 时间线是否有冲突

2. 人物弧光连贯性（P1）
   - 本阶段人物变化是否有铺垫
   - 人物决策是否与其性格一致

3. 与卷大纲对齐（P1）
   - 阶段主题是否服务卷主题
   - 阶段范围是否与卷大纲匹配

4. 章节分布合理性（P2）
   - 章节数量与阶段时长是否匹配
   - 章节划分是否合理

返回JSON格式：
{{"issues": [{{"level": "stage", "chapter_range": "ch{start}-ch{end}", "issue_type": "...", "severity": "P0/P1/P2", "description": "...", "location": "...", "suggestion": "..."}}], "score": 0.0-1.0, "recommendations": ["..."]}}
"""

            response = self.llm.generate(
                prompt=prompt,
                system="你是一个专业的阶段大纲审核专家，擅长逻辑和一致性分析。",
                model="default"
            )
            report.llm_calls = 1

            try:
                data = json.loads(response)
                issues = data.get("issues", [])
                report.issues = [OutlineIssue(**i) for i in issues]
                report.score = data.get("score", 0.5)
                report.recommendations = data.get("recommendations", [])
            except json.JSONDecodeError:
                report.score = 0.5

            reports.append(report)

        return reports

    def check_chapter_outline(self, chapters: List[int] = None) -> List[OutlineQualityReport]:
        """
        章节大纲LLM质检
        检查：章节大纲与正文章节的一致性、核心事件提取准确性、伏笔铺设质量

        Args:
            chapters: 指定章节号列表，None表示全部章节大纲
        """
        reports = []
        paths = self.path_mgr.get_chapter_outline_paths(chapters)

        # 按卷分组处理，每卷一章发一次LLM调用
        volume_chapters = {}
        for path in paths:
            # 从文件名提取章节号：ch001_大纲.md
            import re
            ch_match = re.search(r'ch(\d+)_大纲', path.name)
            if not ch_match:
                continue
            ch_num = int(ch_match.group(1))

            # 确定所在卷（每120章一卷）
            vol_num = (ch_num - 1) // 120 + 1

            if vol_num not in volume_chapters:
                volume_chapters[vol_num] = []
            volume_chapters[vol_num].append((ch_num, path))

        # 对每卷批次处理
        for vol_num, ch_list in sorted(volume_chapters.items()):
            # 加载章节正文（每卷抽样5章）
            body_samples = {}
            sample_indices = [1, 60, 120]  # 每卷开头、中间、结尾
            for ch_num, _ in ch_list[:5]:
                ch_path = self.path_mgr.body_dir / f"ch{ch_num:03d}.md"
                if ch_path.exists():
                    body_samples[ch_num] = ch_path.read_text(encoding='utf-8')[:300]

            # 加载章节大纲
            outline_samples = {}
            for ch_num, path in ch_list[:5]:
                content = self.path_mgr.load_outline_content(path)
                if content:
                    outline_samples[ch_num] = content[:500]

            prompt = f"""你是章节大纲审核专家，负责检测章节大纲的质量问题。

当前批次：第{vol_num}卷（共{len(ch_list)}个章节大纲）

章节大纲样例:
{json.dumps({str(k): v for k, v in outline_samples.items()}, ensure_ascii=False, indent=2)[:4000]}

章节正文样例（用于交叉验证）:
{json.dumps({str(k): v for k, v in body_samples.items()}, ensure_ascii=False, indent=2)[:2000]}

请进行以下维度的检测：

1. 大纲与正文一致性（P0）
   - 大纲描述的事件是否与正文一致
   - 大纲标注的人物是否出现在正文中
   - 伏笔铺设是否在正文中有体现

2. 核心事件提取准确性（P1）
   - 核心事件是否准确反映本章重点
   - 事件排序是否合理
   - 是否遗漏重要事件

3. 伏笔铺设质量（P1）
   - 伏笔标注是否准确
   - 伏笔暗示是否与正文情节契合

4. 信息完整性（P2）
   - 字数估算是否合理
   - 紧张度评级是否准确

返回JSON格式：
{{"issues": [{{"level": "chapter", "chapter": {ch_num}, "issue_type": "...", "severity": "P0/P1/P2", "description": "...", "location": "ch{{编号}}", "suggestion": "..."}}], "score": 0.0-1.0, "recommendations": ["..."]}}
"""

            response = self.llm.generate(
                prompt=prompt,
                system="你是一个专业的章节大纲审核专家，擅长发现大纲与正文的不一致问题。",
                model="default"
            )

            # 为每个章节大纲生成报告
            for ch_num, path in ch_list:
                report = OutlineQualityReport(
                    level="chapter",
                    target=f"ch{ch_num:03d}_大纲"
                )
                report.llm_calls = 1  # 每卷共享一次LLM调用
                reports.append(report)

            # 尝试解析LLM响应并分配问题到各报告
            try:
                data = json.loads(response)
                issues = data.get("issues", [])
                score = data.get("score", 0.5)
                recommendations = data.get("recommendations", [])

                # 将问题分配到对应报告
                for issue_data in issues:
                    ch_num = issue_data.get("chapter")
                    if ch_num:
                        for r in reports:
                            if r.target == f"ch{ch_num:03d}_大纲":
                                r.issues.append(OutlineIssue(**issue_data))
                                r.score = score
                                r.recommendations = recommendations
                                break
            except json.JSONDecodeError:
                for r in reports:
                    r.score = 0.5

        return reports


class LLMOutlineRepairer:
    """基于LLM的大纲问题修复器"""

    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm = llm_service or LLMService()
        self.path_mgr = OutlinePathManager()

    def repair_full_outline_issue(self, issue: OutlineIssue, content: str) -> str:
        """修复全文大纲问题"""
        prompt = f"""你是大纲修复专家，负责修复全文大纲中的问题。

原文大纲内容:
{content[:6000]}

问题描述:
- 类型: {issue.issue_type}
- 严重度: {issue.severity}
- 问题: {issue.description}
- 位置: {issue.location}
- 修复建议: {issue.suggestion}

请直接输出修复后的大纲内容（保持原有结构，只修改问题部分）。"""

        response = self.llm.generate(
            prompt=prompt,
            system="你是一个专业的大纲修复专家，能够保持原有结构进行修改。",
            model="default"
        )
        return response

    def repair_volume_outline_issue(self, issue: OutlineIssue, content: str) -> str:
        """修复卷大纲问题"""
        prompt = f"""你是大纲修复专家，负责修复卷大纲中的问题。

原文大纲内容:
{content[:4000]}

问题描述:
- 类型: {issue.issue_type}
- 严重度: {issue.severity}
- 问题: {issue.description}
- 位置: {issue.location}
- 修复建议: {issue.suggestion}

请直接输出修复后的大纲内容（保持原有结构，只修改问题部分）。"""

        response = self.llm.generate(
            prompt=prompt,
            system="你是一个专业的大纲修复专家，能够保持原有结构进行修改。",
            model="default"
        )
        return response

    def repair_stage_outline_issue(self, issue: OutlineIssue, content: str) -> str:
        """修复阶段大纲问题"""
        prompt = f"""你是大纲修复专家，负责修复阶段大纲中的问题。

原文大纲内容:
{content[:4000]}

问题描述:
- 类型: {issue.issue_type}
- 严重度: {issue.severity}
- 问题: {issue.description}
- 位置: {issue.location}
- 修复建议: {issue.suggestion}

请直接输出修复后的大纲内容（保持原有结构，只修改问题部分）。"""

        response = self.llm.generate(
            prompt=prompt,
            system="你是一个专业的大纲修复专家，能够保持原有结构进行修改。",
            model="default"
        )
        return response


def save_reports(reports: List[OutlineQualityReport], output_file: Path):
    """保存质检报告"""
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "total_reports": len(reports),
        "total_issues": sum(len(r.issues) for r in reports),
        "reports": [r.to_dict() for r in reports],
        "summary": {
            "by_level": {},
            "by_severity": {"P0": 0, "P1": 0, "P2": 0},
            "average_score": sum(r.score for r in reports) / len(reports) if reports else 0,
            "total_llm_calls": sum(r.llm_calls for r in reports)
        }
    }

    for r in reports:
        report_data["summary"]["by_level"][r.level] = report_data["summary"]["by_level"].get(r.level, 0) + len(r.issues)
        for issue in r.issues:
            report_data["summary"]["by_severity"][issue.severity] = report_data["summary"]["by_severity"].get(issue.severity, 0) + 1

    output_file.parent.mkdir(exist_ok=True)
    output_file.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"报告已保存: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='大纲层级LLM质检工具')
    parser.add_argument('--check', type=str, choices=['full', 'volume', 'stage', 'chapter', 'all'],
                        default='all', help='检测层级')
    parser.add_argument('--volume', type=int, help='指定卷号（1-3）')
    parser.add_argument('--stage', type=int, help='指定阶段号')
    parser.add_argument('--chapters', type=str, default='1-360', help='章节范围，如 "1-30" 或 "1,5,10"')
    parser.add_argument('--repair', action='store_true', help='是否修复发现的问题')
    parser.add_argument('--dry-run', action='store_true', help='预览模式（不实际写入）')
    parser.add_argument('--output', type=str, help='报告输出路径')

    args = parser.parse_args()

    print("=" * 60)
    print(f"大纲层级LLM质检工具 v9.2 - LLM_OUTLINE_QUALITY")
    print(f"检测层级: {args.check}")
    if args.volume:
        print(f"指定卷: {args.volume}")
    if args.stage:
        print(f"指定阶段: {args.stage}")
    if args.check == 'chapter':
        print(f"章节范围: {args.chapters}")
    print(f"修复模式: {'开启' if args.repair else '关闭'}")
    print("=" * 60)

    checker = LLMOutlineChecker()
    all_reports = []

    # 全文大纲质检
    if args.check in ['full', 'all']:
        print("\n[全文大纲LLM质检]")
        report = checker.check_full_outline()
        all_reports.append(report)
        print(f"  问题数: {len(report.issues)}")
        print(f"  质量分: {report.score:.2f}")
        print(f"  LLM调用: {report.llm_calls}")
        for issue in report.issues:
            print(f"    [{issue.severity}] {issue.description[:50]}...")

    # 卷大纲质检
    if args.check in ['volume', 'all']:
        print("\n[卷大纲LLM质检]")
        reports = checker.check_volume_outline(args.volume)
        all_reports.extend(reports)
        for r in reports:
            print(f"  {r.target}: {len(r.issues)}问题, score={r.score:.2f}, {r.llm_calls}次LLM调用")

    # 阶段大纲质检
    if args.check in ['stage', 'all']:
        print("\n[阶段大纲LLM质检]")
        reports = checker.check_stage_outline(args.volume, args.stage)
        all_reports.extend(reports)
        for r in reports:
            print(f"  {r.target}: {len(r.issues)}问题, score={r.score:.2f}, {r.llm_calls}次LLM调用")

    # 章节大纲质检
    if args.check in ['chapter', 'all']:
        print("\n[章节大纲LLM质检]")
        # 解析章节范围
        chapters = []
        for part in args.chapters.split(','):
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                chapters.extend(range(start, end + 1))
            else:
                chapters.append(int(part))

        reports = checker.check_chapter_outline(chapters)
        all_reports.extend(reports)

        # 按卷汇总显示
        vol_summary = {}
        for r in reports:
            vol_match = r.target[2:5]  # ch001
            vol_num = (int(vol_match) - 1) // 120 + 1
            if vol_num not in vol_summary:
                vol_summary[vol_num] = {"count": 0, "issues": 0, "score_sum": 0}
            vol_summary[vol_num]["count"] += 1
            vol_summary[vol_num]["issues"] += len(r.issues)
            vol_summary[vol_num]["score_sum"] += r.score

        for vol_num in sorted(vol_summary.keys()):
            s = vol_summary[vol_num]
            avg = s["score_sum"] / s["count"] if s["count"] > 0 else 0
            print(f"  卷{vol_num}: {s['count']}章节大纲, {s['issues']}问题, avg_score={avg:.2f}")
        print(f"  LLM调用: {sum(r.llm_calls for r in reports)}")

    # 保存报告
    if all_reports:
        output_file = Path(args.output) if args.output else PROJECT_ROOT / "logs" / "outline_quality_report.json"
        save_reports(all_reports, output_file)

    # 修复问题
    if args.repair and all_reports:
        print("\n[开始修复]")
        repairer = LLMOutlineRepairer()
        p0_p1_issues = []
        for r in all_reports:
            for issue in r.issues:
                if issue.severity in ['P0', 'P1']:
                    p0_p1_issues.append((r, issue))

        print(f"  P0/P1问题数: {len(p0_p1_issues)}")

        if p0_p1_issues and not args.dry_run:
            for report, issue in p0_p1_issues:
                if report.level == "full":
                    path = checker.path_mgr.get_full_outline_path()
                elif report.level == "volume":
                    path = checker.path_mgr.get_volume_outline_paths()[0]  # 需要更精确的路径
                else:
                    continue

                if not path or not path.exists():
                    continue

                content = checker.path_mgr.load_outline_content(path)
                if not content:
                    continue

                try:
                    if report.level == "full":
                        fixed = repairer.repair_full_outline_issue(issue, content)
                    elif report.level == "volume":
                        fixed = repairer.repair_volume_outline_issue(issue, content)
                    else:
                        continue

                    path.write_text(fixed, encoding='utf-8')
                    print(f"  ✓ 已修复: {report.target} - {issue.issue_type}")
                except Exception as e:
                    print(f"  ✗ 修复失败: {report.target} - {e}")

    # 汇总
    print("\n" + "=" * 60)
    print("大纲层级LLM质检完成")
    total_issues = sum(len(r.issues) for r in all_reports)
    total_calls = sum(r.llm_calls for r in all_reports)
    avg_score = sum(r.score for r in all_reports) / len(all_reports) if all_reports else 0
    print(f"检测报告: {len(all_reports)}")
    print(f"发现问题: {total_issues}")
    print(f"LLM调用: {total_calls}")
    print(f"平均质量分: {avg_score:.2f}")
    print("=" * 60)


if __name__ == '__main__':
    main()