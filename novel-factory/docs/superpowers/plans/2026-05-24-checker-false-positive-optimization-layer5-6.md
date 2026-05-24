# 检测器误报优化 Layer 5-6 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现检查器自检机制（Layer 5）和混合仲裁机制（Layer 6），完成6层误报优化体系

**Architecture:**
- Layer 5: 检查器自检机制 - 每个检查器追踪自身的误报率，自动调整灵敏度或加入白名单
- Layer 6: 混合仲裁机制 - 多检查器交叉验证，模糊问题提交LLM复核

**Tech Stack:** Python dataclass, JSON, 现有检测器架构

---

## 文件变更总览

| 文件 | 操作 |
|------|------|
| `infra/consistency/engine/checker_inspector.py` | 新增 |
| `infra/consistency/engine/consistency_arbitrator.py` | 新增 |
| `infra/consistency/engine/data_structures.py` | 修改 |
| `context/checker_performance.json` | 新增 |
| `tests/test_checker_inspector.py` | 新增 |
| `tests/test_consistency_arbitrator.py` | 新增 |

---

## Layer 5: 检查器自检机制

## Task 1: 扩展 Issue 数据结构（添加自检字段）

**Files:**
- Modify: `infra/consistency/engine/data_structures.py`

- [ ] **Step 1: 添加 CheckerPerformance 数据类**

在 `Issue` 类之后添加：

```python
@dataclass
class CheckerPerformance:
    """检查器性能统计"""
    checker_type: str
    total_detections: int = 0
    false_positive_count: int = 0
    true_positive_count: int = 0
    false_positive_rate: float = 0.0
    avg_confidence_score: float = 0.5
    last_updated: datetime = field(default_factory=datetime.now)
    is_over_threshold: bool = False  # 是否超过误报阈值

    def update(self, is_false_positive: bool, confidence_score: float = 0.5):
        """更新性能统计"""
        self.total_detections += 1
        if is_false_positive:
            self.false_positive_count += 1
        else:
            self.true_positive_count += 1
        self.false_positive_rate = self.false_positive_count / max(self.total_detections, 1)
        # 更新平均置信度分数
        self.avg_confidence_score = (
            (self.avg_confidence_score * (self.total_detections - 1) + confidence_score)
            / self.total_detections
        )
        self.last_updated = datetime.now()
```

- [ ] **Step 2: 添加 IssueFeedback 数据类**

```python
@dataclass
class IssueFeedback:
    """问题反馈（用于自检）"""
    issue_id: str
    checker_type: str
    chapter_num: int
    is_false_positive: bool
    user_confirmed: bool = False
    llm_reviewed: bool = False
    llm_verdict: Optional[str] = None  # "confirmed", "false_positive", "ambiguous"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
```

- [ ] **Step 3: 运行测试验证无语法错误**

Run: `cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory && python -c "from infra.consistency.engine.data_structures import CheckerPerformance, IssueFeedback; p = CheckerPerformance('timeline_checker'); print(f'checker_type={p.checker_type}'); f = IssueFeedback('test', 'timeline_checker', 1, True); print(f'feedback={f.is_false_positive}')"`
Expected: `checker_type=timeline_checker` and `feedback=True`

- [ ] **Step 4: 提交**

```bash
git add infra/consistency/engine/data_structures.py
git commit -m "feat: add CheckerPerformance and IssueFeedback for self-inspection"
```

---

## Task 2: 创建 CheckerInspector（检查器自检器）

**Files:**
- Create: `infra/consistency/engine/checker_inspector.py`

- [ ] **Step 1: 创建 CheckerInspector 类**

```python
#!/usr/bin/env python3
"""
检查器自检器 - Layer 5 实现
追踪每个检查器的误报率，自动调整灵敏度或建议加入白名单
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CONTEXT_DIR = PROJECT_ROOT / "context"
PERFORMANCE_PATH = CONTEXT_DIR / "checker_performance.json"

# 误报率阈值
FALSE_POSITIVE_RATE_THRESHOLD = 0.3  # 30% 误报率阈值
CONFIDENCE_WEIGHT_THRESHOLD = 0.6   # 置信度权重阈值


@dataclass
class InspectionResult:
    """自检结果"""
    checker_type: str
    false_positive_rate: float
    avg_confidence_score: float
    total_issues: int
    recommendations: List[str]  # 建议列表
    should_auto_fix: bool      # 是否应自动修复


class CheckerInspector:
    """检查器自检器（单例）"""
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
        self.performance_data = self._load_performance()

    def _load_performance(self) -> Dict[str, Any]:
        """加载性能数据"""
        if not PERFORMANCE_PATH.exists():
            return self._default_performance()
        try:
            with open(PERFORMANCE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return self._default_performance()

    def _default_performance(self) -> Dict[str, Any]:
        return {
            "checkers": {},
            "last_full_inspection": None,
            "auto_fix_enabled": True
        }

    def _save_performance(self):
        """保存性能数据"""
        PERFORMANCE_PATH.parent.mkdir(exist_ok=True)
        with open(PERFORMANCE_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.performance_data, f, ensure_ascii=False, indent=2)

    def record_issue_result(self, checker_type: str, is_false_positive: bool, confidence_score: float = 0.5):
        """记录检测结果"""
        if checker_type not in self.performance_data["checkers"]:
            self.performance_data["checkers"][checker_type] = {
                "total_detections": 0,
                "false_positive_count": 0,
                "true_positive_count": 0,
                "false_positive_rate": 0.0,
                "avg_confidence_score": 0.5,
                "last_updated": None
            }

        stats = self.performance_data["checkers"][checker_type]
        stats["total_detections"] += 1
        if is_false_positive:
            stats["false_positive_count"] += 1
        else:
            stats["true_positive_count"] += 1

        # 更新误报率
        total = stats["total_detections"]
        fp = stats["false_positive_count"]
        stats["false_positive_rate"] = fp / max(total, 1)

        # 更新平均置信度
        prev_avg = stats.get("avg_confidence_score", 0.5)
        stats["avg_confidence_score"] = (prev_avg * (total - 1) + confidence_score) / total
        stats["last_updated"] = datetime.now().isoformat()

        self._save_performance()

    def get_checker_stats(self, checker_type: str) -> Dict[str, Any]:
        """获取检查器统计"""
        return self.performance_data["checkers"].get(checker_type, {})

    def inspect_checker(self, checker_type: str) -> InspectionResult:
        """检查单个检查器的性能"""
        stats = self.get_checker_stats(checker_type)
        if not stats or stats.get("total_detections", 0) == 0:
            return InspectionResult(
                checker_type=checker_type,
                false_positive_rate=0.0,
                avg_confidence_score=0.5,
                total_issues=0,
                recommendations=["无数据"],
                should_auto_fix=False
            )

        fp_rate = stats.get("false_positive_rate", 0.0)
        avg_confidence = stats.get("avg_confidence_score", 0.5)
        total = stats.get("total_detections", 0)

        recommendations = []
        should_auto_fix = False

        # 检查误报率阈值
        if fp_rate > FALSE_POSITIVE_RATE_THRESHOLD:
            recommendations.append(f"误报率 {fp_rate:.1%} 超过阈值 {FALSE_POSITIVE_RATE_THRESHOLD:.1%}，建议加入白名单")
            should_auto_fix = True

        # 检查置信度分数
        if avg_confidence < CONFIDENCE_WEIGHT_THRESHOLD:
            recommendations.append(f"平均置信度 {avg_confidence:.2f} 低于阈值 {CONFIDENCE_WEIGHT_THRESHOLD:.2f}，降低灵敏度")

        # 检查绝对数量
        if stats.get("false_positive_count", 0) > 10:
            recommendations.append(f"误报数量 {stats['false_positive_count']} 超过10，建议人工审核")

        return InspectionResult(
            checker_type=checker_type,
            false_positive_rate=fp_rate,
            avg_confidence_score=avg_confidence,
            total_issues=total,
            recommendations=recommendations,
            should_auto_fix=should_auto_fix
        )

    def inspect_all_checkers(self) -> List[InspectionResult]:
        """检查所有检查器"""
        results = []
        for checker_type in self.performance_data["checkers"]:
            result = self.inspect_checker(checker_type)
            results.append(result)

        self.performance_data["last_full_inspection"] = datetime.now().isoformat()
        self._save_performance()
        return results

    def get_auto_fix_recommendations(self) -> List[Dict[str, Any]]:
        """获取自动修复建议（用于更新白名单）"""
        recommendations = []
        for result in self.inspect_all_checkers():
            if result.should_auto_fix:
                recommendations.append({
                    "checker_type": result.checker_type,
                    "false_positive_rate": result.false_positive_rate,
                    "recommendations": result.recommendations
                })
        return recommendations
```

- [ ] **Step 2: 创建测试文件**

```python
# tests/test_checker_inspector.py
import pytest
from infra.consistency.engine.checker_inspector import CheckerInspector, InspectionResult

class TestCheckerInspector:
    def test_singleton(self):
        i1 = CheckerInspector()
        i2 = CheckerInspector()
        assert i1 is i2

    def test_record_issue_result(self):
        inspector = CheckerInspector()
        inspector.record_issue_result("timeline_checker", is_false_positive=False, confidence_score=0.8)
        inspector.record_issue_result("timeline_checker", is_false_positive=True, confidence_score=0.3)
        stats = inspector.get_checker_stats("timeline_checker")
        assert stats["total_detections"] == 2
        assert stats["false_positive_count"] == 1

    def test_inspect_checker_no_data(self):
        inspector = CheckerInspector()
        result = inspector.inspect_checker("nonexistent_checker")
        assert result.total_issues == 0

    def test_inspect_checker_with_data(self):
        inspector = CheckerInspector()
        for _ in range(5):
            inspector.record_issue_result("character_checker", is_false_positive=False, confidence_score=0.9)
        for _ in range(3):
            inspector.record_issue_result("character_checker", is_false_positive=True, confidence_score=0.2)
        result = inspector.inspect_checker("character_checker")
        assert result.total_issues == 8
        assert result.false_positive_rate == 0.375  # 3/8 = 37.5%
        assert result.should_auto_fix == True  # > 30%
```

- [ ] **Step 3: 运行测试验证**

Run: `cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory && python -m pytest tests/test_checker_inspector.py -v`

- [ ] **Step 4: 提交**

```bash
git add infra/consistency/engine/checker_inspector.py tests/test_checker_inspector.py
git commit -m "feat: add CheckerInspector for checker self-inspection (Layer 5)"
```

---

## Layer 6: 混合仲裁机制

## Task 3: 创建 ConsistencyArbitrator（混合仲裁器）

**Files:**
- Create: `infra/consistency/engine/consistency_arbitrator.py`

- [ ] **Step 1: 创建 ConsistencyArbitrator 类**

```python
#!/usr/bin/env python3
"""
混合仲裁器 - Layer 6 实现
多检查器交叉验证，模糊问题提交LLM复核
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .data_structures import Issue, IssueSeverity, ConfidenceLevel


@dataclass
class ArbitrationResult:
    """仲裁结果"""
    original_issues: List[Issue]
    resolved_issues: List[Issue]  # 经仲裁确认的问题
    ambiguous_issues: List[Issue]  # 模糊问题，需LLM复核
    false_positive_issues: List[Issue]  # 误报问题
    arbitration_summary: str
    needs_llm_review: bool = False


@dataclass
class IssueGroup:
    """问题组（相同位置的问题）"""
    location_key: str  # "chXXX_pYY" 格式
    issues: List[Issue] = field(default_factory=list)
    checker_types: List[str] = field(default_factory=list)
    severities: List[IssueSeverity] = field(default_factory=list)
    avg_confidence: float = 0.0


class ConsistencyArbitrator:
    """
    混合仲裁器

    仲裁规则：
    1. 位置分组：相同章节/段落的问题分组
    2. 多检查器确认：≥2个检查器报告相同位置的问题 → 高置信度
    3. 置信度投票：HIGH置信度issue权重高
    4. 模糊问题：置信度差异大或多个检查器冲突 → LLM复核
    """

    def __init__(self):
        self.arbitration_log = []

    def _group_issues_by_location(self, issues: List[Issue]) -> List[IssueGroup]:
        """将问题按位置分组"""
        groups: Dict[str, IssueGroup] = {}

        for issue in issues:
            # 生成位置键
            loc = issue.location
            key = f"ch{loc.chapter}"
            if loc.paragraph is not None:
                key += f"_p{loc.paragraph}"

            if key not in groups:
                groups[key] = IssueGroup(location_key=key)
            groups[key].issues.append(issue)
            groups[key].checker_types.append(issue.checker_type.value)
            groups[key].severities.append(issue.severity)

            # 计算平均置信度
            conf_map = {"HIGH": 1.0, "MEDIUM": 0.7, "LOW": 0.4}
            conf_val = conf_map.get(issue.confidence.value, 0.5)
            avg = groups[key].avg_confidence
            n = len(groups[key].issues)
            groups[key].avg_confidence = (avg * (n - 1) + conf_val) / n

        return list(groups.values())

    def _is_same_issue(self, issue1: Issue, issue2: Issue) -> bool:
        """判断两个问题是否实质相同"""
        # 相同检查器类型
        if issue1.checker_type == issue2.checker_type:
            return True
        # 不同检查器但相同角色和相似类型
        if issue1.character and issue2.character:
            if issue1.character == issue2.character:
                return True
        return False

    def _arbitrate_group(self, group: IssueGroup) -> Tuple[List[Issue], List[Issue], List[Issue]]:
        """仲裁一个问题组"""
        resolved = []
        ambiguous = []
        false_positives = []

        # 规则1：多检查器确认（相同位置≥2个检查器报告）→ 高置信度
        unique_checkers = set(group.checker_types)
        if len(unique_checkers) >= 2:
            # 多个检查器确认，这是个真实问题
            # 取最高严重性
            max_severity = max(group.severities, default=IssueSeverity.P3)
            for issue in group.issues:
                if issue.severity == max_severity:
                    resolved.append(issue)
                    break
            return resolved, ambiguous, false_positives

        # 规则2：单检查器，查看置信度
        issue = group.issues[0]
        if issue.confidence == ConfidenceLevel.HIGH:
            resolved.append(issue)
        elif issue.confidence == ConfidenceLevel.LOW:
            # 低置信度 → 标记为模糊，需要LLM复核
            issue.needs_llm_review = True
            ambiguous.append(issue)
        else:
            # MEDIUM置信度
            if issue.confidence_score >= 0.75:
                resolved.append(issue)
            elif issue.confidence_score <= 0.4:
                issue.needs_llm_review = True
                ambiguous.append(issue)
            else:
                ambiguous.append(issue)

        return resolved, ambiguous, false_positives

    def arbitrate(self, issues: List[Issue]) -> ArbitrationResult:
        """
        仲裁一组问题

        Args:
            issues: 从多个检查器收集的问题列表

        Returns:
            ArbitrationResult: 包含已解决、模糊和误报问题
        """
        if not issues:
            return ArbitrationResult(
                original_issues=[],
                resolved_issues=[],
                ambiguous_issues=[],
                false_positive_issues=[],
                arbitration_summary="无问题可仲裁"
            )

        # 按位置分组
        groups = self._group_issues_by_location(issues)

        all_resolved = []
        all_ambiguous = []
        all_false_positives = []

        for group in groups:
            resolved, ambiguous, false_pos = self._arbitrate_group(group)
            all_resolved.extend(resolved)
            all_ambiguous.extend(ambiguous)
            all_false_positives.extend(false_pos)

        # 生成摘要
        summary = f"仲裁完成：{len(all_resolved)}个已确认，{len(all_ambiguous)}个需LLM复核，{len(all_false_positives)}个误报"

        result = ArbitrationResult(
            original_issues=issues,
            resolved_issues=all_resolved,
            ambiguous_issues=all_ambiguous,
            false_positive_issues=all_false_positives,
            arbitration_summary=summary,
            needs_llm_review=len(all_ambiguous) > 0
        )

        # 记录日志
        self.arbitration_log.append({
            "timestamp": datetime.now().isoformat(),
            "original_count": len(issues),
            "resolved_count": len(all_resolved),
            "ambiguous_count": len(all_ambiguous),
            "false_positive_count": len(all_false_positives)
        })

        return result

    def get_arbitration_log(self) -> List[Dict[str, Any]]:
        """获取仲裁日志"""
        return self.arbitration_log
```

- [ ] **Step 2: 创建测试文件**

```python
# tests/test_consistency_arbitrator.py
import pytest
from infra.consistency.engine.consistency_arbitrator import ConsistencyArbitrator, IssueGroup, ArbitrationResult
from infra.consistency.engine.data_structures import (
    Issue, IssueSeverity, IssueLocation, CheckerType, ConfidenceLevel
)

class TestConsistencyArbitrator:
    def test_arbitrate_empty(self):
        arb = ConsistencyArbitrator()
        result = arb.arbitrate([])
        assert len(result.resolved_issues) == 0
        assert result.arbitration_summary == "无问题可仲裁"

    def test_arbitrate_single_high_confidence(self):
        arb = ConsistencyArbitrator()
        issue = Issue(
            id="test1", severity=IssueSeverity.P1,
            checker_type=CheckerType.CHARACTER, issue_type="test",
            title="Test", description="Test",
            location=IssueLocation(chapter=1),
            confidence=ConfidenceLevel.HIGH
        )
        result = arb.arbitrate([issue])
        assert len(result.resolved_issues) == 1

    def test_arbitrate_multiple_checkers_same_location(self):
        arb = ConsistencyArbitrator()
        issue1 = Issue(
            id="test1", severity=IssueSeverity.P1,
            checker_type=CheckerType.CHARACTER, issue_type="test",
            title="Test1", description="Test1",
            location=IssueLocation(chapter=1, paragraph=3),
            confidence=ConfidenceLevel.MEDIUM
        )
        issue2 = Issue(
            id="test2", severity=IssueSeverity.P2,
            checker_type=CheckerType.ABILITY, issue_type="test",
            title="Test2", description="Test2",
            location=IssueLocation(chapter=1, paragraph=3),
            confidence=ConfidenceLevel.MEDIUM
        )
        result = arb.arbitrate([issue1, issue2])
        # 两个检查器报告同一位置 → 高置信度
        assert len(result.resolved_issues) >= 1
```

- [ ] **Step 3: 运行测试验证**

Run: `cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory && python -m pytest tests/test_consistency_arbitrator.py -v`

- [ ] **Step 4: 提交**

```bash
git add infra/consistency/engine/consistency_arbitrator.py tests/test_consistency_arbitrator.py
git commit -m "feat: add ConsistencyArbitrator for hybrid arbitration (Layer 6)"
```

---

## Task 4: 集成到 ConsistencyEngine

**Files:**
- Modify: `infra/consistency/engine/consistency_engine.py`

- [ ] **Step 1: 添加仲裁器初始化**

在 `ConsistencyEngine.__init__` 中添加：

```python
from .checker_inspector import CheckerInspector
from .consistency_arbitrator import ConsistencyArbitrator

# 在 __init__ 方法中添加：
self.checker_inspector = CheckerInspector()
self.arbitrator = ConsistencyArbitrator()
```

- [ ] **Step 2: 在 check_chapter 方法中集成仲裁**

在 `check_chapter` 方法返回前添加：

```python
# 在返回 ConsistencyReport 之前添加仲裁
if issues and self.use_arbitration:
    arbitration_result = self.arbitrator.arbitrate(issues)
    # 使用仲裁后的问题列表
    report = ConsistencyReport(
        chapter_num=chapter_num,
        chapter_title=chapter_title,
        issues=arbitration_result.resolved_issues,
        # ... 其他字段
    )
    # 记录模糊问题用于LLM复核
    if arbitration_result.needs_llm_review:
        # 存储 ambiguous_issues 供后续处理
        pass
else:
    report = ConsistencyReport(...)
```

- [ ] **Step 3: 运行测试验证无语法错误**

Run: `cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory && python -c "from infra.consistency.engine.consistency_engine import ConsistencyEngine; e = ConsistencyEngine(); print(f'arbitrator={e.arbitrator}, inspector={e.checker_inspector}')"`

- [ ] **Step 4: 提交**

```bash
git add infra/consistency/engine/consistency_engine.py
git commit -m "feat: integrate checker inspector and arbitrator into engine"
```

---

## Task 5: 最终验证

- [ ] **Step 1: 运行所有一致性测试**

Run: `cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory && python -m pytest tests/consistency/ -v --tb=short 2>&1 | tail -30`
Expected: 所有测试通过

- [ ] **Step 2: 验证新功能加载**

Run: `cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory && python -c "
from infra.consistency.engine.checker_inspector import CheckerInspector
from infra.consistency.engine.consistency_arbitrator import ConsistencyArbitrator

inspector = CheckerInspector()
print(f'Inspector: {inspector}')

arb = ConsistencyArbitrator()
print(f'Arbitrator: {arb}')

print('Layer 5-6 loaded OK')
"`

- [ ] **Step 3: 提交**

```bash
git add -A
git commit -m "feat: complete Layer 5-6 implementation - checker self-inspection and hybrid arbitration"
```

---

## 实施后验证

完成后，系统应能：
1. `CheckerInspector` 追踪每个检查器的误报率
2. 误报率 > 30% 时自动建议加入白名单
3. `ConsistencyArbitrator` 对多检查器问题进行仲裁
4. 模糊问题标记为 `needs_llm_review: True`
5. 引擎层集成自检和仲裁机制