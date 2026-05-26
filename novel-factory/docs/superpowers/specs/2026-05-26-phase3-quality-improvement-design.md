# Phase 3 质量提升设计文档

> **版本**: v1.0
> **日期**: 2026-05-26
> **阶段**: Phase 3 - 质量提升

## 1. 概述

### 1.1 目标

提升质量检查系统的覆盖范围和准确性，通过新增检测器、完善修复方法、优化误报分类来提升整体质量。

### 1.2 现状

- 22个一致性检测器
- 7个LLM修复方法
- ProblemClassifier可过滤约40%误报

### 1.3 优化收益

| 方向 | 收益 |
|------|------|
| 新增检测器 | 覆盖更多质量问题维度 |
| 完善修复方法 | 提高自动修复准确率 |
| 优化误报分类 | 减少无效检测和LLM调用 |

## 2. 设计方案

### 2.1 新增检测器

#### PacingChecker - 节奏检测器

检测章节节奏问题：
- 高潮后是否有缓冲
- 铺垫是否充分
- 战斗/冲突是否过于密集

```python
class PacingChecker(BaseChecker):
    """节奏检测器"""

    def check(self, content, chapter_num, context=None):
        issues = []

        # 检测高潮密度
        action_count = self._count_action_segments(content)
        if action_count > 10:  # 超过10个动作段
            issues.append(Issue(
                chapter=chapter_num,
                issue_type="节奏过密",
                severity="P2",
                description="章节中动作/冲突段过于密集"
            ))

        # 检测是否有缓冲
        if self._has_climax_without_cooldown(content):
            issues.append(...)

        return issues
```

#### SceneTransitionChecker - 场景转换检测器

检测场景转换问题：
- 场景转换是否突兀
- 是否缺少过渡
- 时间/空间跳跃是否合理

```python
class SceneTransitionChecker(BaseChecker):
    """场景转换检测器"""

    def check(self, content, chapter_num, context=None):
        issues = []

        # 检测场景转换标记词
        transition_markers = ["忽然", "突然", "下一秒", "就在这时"]
        transitions = self._find_transitions(content)

        if len(transitions) > 5 and not self._has_transitional_content(content):
            issues.append(Issue(
                chapter=chapter_num,
                issue_type="场景转换突兀",
                severity="P2",
                description="章节中场景转换过于频繁且缺少过渡"
            ))

        return issues
```

#### DialogueAuthenticityChecker - 对话真实性检测器

检测对话质量问题：
- 对话是否过于正式
- 是否符合角色性格
- 是否缺少口语化表达

```python
class DialogueAuthenticityChecker(BaseChecker):
    """对话真实性检测器"""

    # AI对话特征词
    AI_DIALOGUE_PATTERNS = [
        r'我相信', r'毫无疑问', r'必须承认',
        r'从某种意义上', r'事实上', r'总的来说'
    ]

    def check(self, content, chapter_num, context=None):
        issues = []

        for pattern in self.AI_DIALOGUE_PATTERNS:
            matches = re.findall(pattern, content)
            if len(matches) > 3:
                issues.append(Issue(
                    chapter=chapter_num,
                    issue_type="对话不真实",
                    severity="P2",
                    description=f"检测到{len(matches)}处AI化表达"
                ))

        return issues
```

### 2.2 完善修复方法

#### 新增修复方法

```python
# llm_quality_deep_check.py

def repair_pacing_issue(self, issue, chapter_content):
    """修复节奏问题"""
    # 分析节奏密度
    # 在高潮后插入缓冲段
    # 调整冲突间隔

def repair_scene_transition(self, issue, chapter_content):
    """修复场景转换问题"""
    # 添加过渡句
    # 使用时间/空间标记词

def repair_dialogue_authenticity(self, issue, chapter_content):
    """修复对话真实感问题"""
    # 替换AI表达为口语化表达
    # 添加角色口癖
```

### 2.3 优化误报分类

#### ProblemClassifier 改进

```python
# 新增检测器局限案例
DETECTOR_LIMITATIONS = {
    # ... 现有案例 ...

    # 新增：节奏检测器宇宙场景局限
    "节奏过密": {
        "patterns": ["宇宙级", "星际战争", "跨维度"],
        "description": "宇宙级战斗场景节奏密集是正常的"
    },

    # 新增：场景转换宇宙场景局限
    "场景转换突兀": {
        "patterns": ["维度裂缝", "空间跳跃", "传送"],
        "description": "科幻/奇幻场景中突兀转换可能是设定需要"
    }
}
```

## 3. 文件清单

### 3.1 新增文件

| 文件 | 行数 | 说明 |
|------|------|------|
| `infra/consistency/checkers/pacing_checker.py` | ~150 | 节奏检测器 |
| `infra/consistency/checkers/scene_transition_checker.py` | ~120 | 场景转换检测器 |
| `infra/consistency/checkers/dialogue_authenticity_checker.py` | ~100 | 对话真实性检测器 |

### 3.2 修改文件

| 文件 | 修改 | 说明 |
|------|------|------|
| `tools/problem_classifier.py` | 扩展局限案例 | 添加新检测器局限 |
| `tools/llm_quality_deep_check.py` | 添加修复方法 | 3个新修复方法 |

## 4. 实现顺序

1. **节奏检测器** - 最实用
2. **场景转换检测器** - 通用性强
3. **对话真实性检测器** - 补充AI痕迹检测
4. **修复方法** - 配套修复
5. **ProblemClassifier优化** - 减少新检测器误报

## 5. 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 新检测器引入误报 | 产生新的误报 | 添加足够的局限案例 |
| 修复方法不准确 | 修复引入新问题 | 保守策略：仅建议不自动修复 |

## 6. 成功标准

- [ ] PacingChecker节奏检测器正常工作
- [ ] SceneTransitionChecker场景转换检测器正常工作
- [ ] DialogueAuthenticityChecker对话真实性检测器正常工作
- [ ] 3个新修复方法可用
- [ ] ProblemClassifier覆盖新检测器局限
- [ ] 所有现有测试继续通过
