# Phase 3 质量提升实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended)

**Goal:** 提升质量检测覆盖范围和准确性

**Architecture:**
- 3个新检测器：PacingChecker, SceneTransitionChecker, DialogueAuthenticityChecker
- 3个新修复方法：repair_pacing_issue, repair_scene_transition, repair_dialogue_authenticity
- ProblemClassifier扩展新检测器局限案例

**Tech Stack:** Python 3.13, re, dataclasses

---

## Task 1: 创建 PacingChecker 节奏检测器

**Files:**
- Create: `infra/consistency/checkers/pacing_checker.py`

- [ ] **Step 1: 创建 pacing_checker.py**

```python
#!/usr/bin/env python3
"""
节奏检测器 - 检测章节节奏问题

评估标准：
- 高潮/动作段不应过于密集
- 应有合理的缓冲和铺垫
- 战斗节奏应有张弛
"""

import re
from typing import List, Dict, Optional
from .base_checker import BaseChecker
from ..engine.data_structures import Issue, CheckerType


class PacingChecker(BaseChecker):
    """节奏检测器"""

    def __init__(self):
        super().__init__(CheckerType.CONSISTENCY)

        # 高潮/动作关键词
        self.action_keywords = [
            "战斗", "攻击", "冲击", "爆发", "爆炸", "碰撞",
            "厮杀", "搏斗", "对决", "交锋", "对抗"
        ]

        # 缓冲/过渡关键词
        self.cooldown_keywords = [
            "沉默", "叹息", "思考", "回忆", "休息", "等待",
            "观察", "警惕", "戒备", "喘息", "平静"
        ]

        # 铺垫关键词
        self.foreshadow_keywords = [
            "预感", "觉得", "似乎", "可能", "也许", "将要",
            "即将", "准备", "预感", "担忧"
        ]

    def check(self, chapter_content: str, chapter_num: int, context: Optional[Dict] = None) -> List[Issue]:
        issues = []

        # 检测高潮密度
        action_count = self._count_action_segments(chapter_content)
        total_segments = self._estimate_total_segments(chapter_content)

        if total_segments > 0:
            action_ratio = action_count / total_segments

            # 动作段超过60%认为节奏过密
            if action_ratio > 0.6 and action_count > 5:
                issues.append(Issue(
                    chapter=chapter_num,
                    dimension="节奏",
                    issue_type="节奏过密",
                    severity="P2",
                    description=f"章节中动作/冲突段过于密集（{action_count}处，占比{action_ratio:.0%}）",
                    evidence=f"动作段: {action_count}, 总段: {total_segments}"
                ))

        # 检测高潮后是否有缓冲
        if self._has_climax_without_cooldown(chapter_content):
            issues.append(Issue(
                chapter=chapter_num,
                dimension="节奏",
                issue_type="高潮后缺少缓冲",
                severity="P2",
                description="连续高潮后缺少缓冲段读者会疲劳"
            ))

        # 检测是否有过长铺垫
        setup_length = self._measure_foreshadow_length(chapter_content)
        if setup_length > 0.4:  # 铺垫超过40%
            issues.append(Issue(
                chapter=chapter_num,
                dimension="节奏",
                issue_type="铺垫过长",
                severity="P3",
                description="章节前期铺垫过长可能让读者失去耐心"
            ))

        return issues

    def _count_action_segments(self, content: str) -> int:
        """统计动作段数量"""
        count = 0
        sentences = content.split('。')

        for sentence in sentences:
            action_count = sum(1 for kw in self.action_keywords if kw in sentence)
            if action_count >= 2:  # 一句中有2个以上动作词
                count += 1

        return count

    def _estimate_total_segments(self, content: str) -> int:
        """估算总段数（简单按句号计数）"""
        return max(1, content.count('。') + content.count('！') + content.count('？'))

    def _has_climax_without_cooldown(self, content: str) -> bool:
        """检测高潮后是否有缓冲"""
        sentences = content.split('。')
        recent_actions = 0
        recent_cooldowns = 0

        # 从后向前检测最近10句
        for sentence in reversed(sentences[-10:]):
            action_count = sum(1 for kw in self.action_keywords if kw in sentence)
            cooldown_count = sum(1 for kw in self.cooldown_keywords if kw in sentence)

            if action_count >= 2:
                recent_actions += 1
            if cooldown_count >= 1:
                recent_cooldowns += 1

        # 连续3个以上动作段但没有缓冲
        return recent_actions >= 3 and recent_cooldowns == 0

    def _measure_foreshadow_length(self, content: str) -> float:
        """测量铺垫长度占比"""
        sentences = content.split('。')

        if len(sentences) < 3:
            return 0.0

        # 前1/3为铺垫区
        setup_sentences = sentences[:len(sentences) // 3]
        foreshadow_count = sum(
            1 for s in setup_sentences
            if any(kw in s for kw in self.foreshadow_keywords)
        )

        return foreshadow_count / max(1, len(setup_sentences))
```

- [ ] **Step 2: 测试检测器**

```bash
python -c "
from infra.consistency.checkers.pacing_checker import PacingChecker
from infra.paths import ProjectPaths

paths = ProjectPaths.get()
content = paths.read_chapter(1)

checker = PacingChecker()
issues = checker.check(content, 1)
print(f'ch001: 发现 {len(issues)} 个节奏问题')
for issue in issues:
    print(f'  - {issue.issue_type}: {issue.description}')
"
```

- [ ] **Step 3: 提交**

```bash
git add infra/consistency/checkers/pacing_checker.py
git commit -m "feat: add PacingChecker for rhythm detection"
```

---

## Task 2: 创建 SceneTransitionChecker 场景转换检测器

**Files:**
- Create: `infra/consistency/checkers/scene_transition_checker.py`

- [ ] **Step 1: 创建 scene_transition_checker.py**

```python
#!/usr/bin/env python3
"""
场景转换检测器 - 检测场景转换问题

评估标准：
- 场景转换应有过渡
- 时间/空间跳跃应合理
- 不应有突兀的视角切换
"""

import re
from typing import List, Dict, Optional
from .base_checker import BaseChecker
from ..engine.data_structures import Issue, CheckerType


class SceneTransitionChecker(BaseChecker):
    """场景转换检测器"""

    def __init__(self):
        super().__init__(CheckerType.CONSISTENCY)

        # 突兀转换标记词
        self.abrupt_markers = [
            "忽然", "突然", "下一秒", "就在这时",
            "刹那间", "一瞬", "瞬间", "眨眼间"
        ]

        # 过渡标记词
        self.transitional_markers = [
            "片刻后", "过了一会儿", "不多时",
            "与此同时", "与此同时", "在这期间",
            "时间流逝", "随着"
        ]

        # 场景变换关键词
        self.scene_change_keywords = [
            "来到", "到达", "前往", "进入",
            "离开", "穿越", "传送", "跳跃"
        ]

    def check(self, chapter_content: str, chapter_num: int, context: Optional[Dict] = None) -> List[Issue]:
        issues = []

        # 检测突兀转换
        abrupt_transitions = self._find_abrupt_transitions(chapter_content)
        transitional_content = self._has_transitional_content(chapter_content)

        if len(abrupt_transitions) > 5 and not transitional_content:
            issues.append(Issue(
                chapter=chapter_num,
                dimension="一致性",
                issue_type="场景转换突兀",
                severity="P2",
                description=f"章节中{len(abrupt_transitions)}处场景转换缺少过渡",
                evidence="频繁使用突然/忽然等词但无过渡描写"
            ))

        # 检测连续空间跳跃
        if self._has_consecutive_space_jumps(chapter_content):
            issues.append(Issue(
                chapter=chapter_num,
                dimension="一致性",
                issue_type="空间跳跃过频",
                severity="P2",
                description="短时间内多次空间跳跃缺乏合理性"
            ))

        return issues

    def _find_abrupt_transitions(self, content: str) -> List[str]:
        """找出所有突兀转换"""
        transitions = []
        for marker in self.abrupt_markers:
            if marker in content:
                transitions.append(marker)
        return transitions

    def _has_transitional_content(self, content: str) -> bool:
        """检测是否有过渡内容"""
        for marker in self.transitional_markers:
            if marker in content:
                return True
        return False

    def _has_consecutive_space_jumps(self, content: str) -> bool:
        """检测是否在短距离内有多次空间跳跃"""
        sentences = content.split('。')
        jump_count = 0

        for sentence in sentences[-15:]:  # 检查最近15句
            if any(kw in sentence for kw in self.scene_change_keywords):
                jump_count += 1

        return jump_count >= 3
```

- [ ] **Step 2: 测试检测器**

```bash
python -c "
from infra.consistency.checkers.scene_transition_checker import SceneTransitionChecker
from infra.paths import ProjectPaths

paths = ProjectPaths.get()
content = paths.read_chapter(1)

checker = SceneTransitionChecker()
issues = checker.check(content, 1)
print(f'ch001: 发现 {len(issues)} 个场景转换问题')
"
```

- [ ] **Step 3: 提交**

```bash
git add infra/consistency/checkers/scene_transition_checker.py
git commit -m "feat: add SceneTransitionChecker"
```

---

## Task 3: 创建 DialogueAuthenticityChecker 对话真实性检测器

**Files:**
- Create: `infra/consistency/checkers/dialogue_authenticity_checker.py`

- [ ] **Step 1: 创建 dialogue_authenticity_checker.py**

```python
#!/usr/bin/env python3
"""
对话真实性检测器 - 检测AI化对话

评估标准：
- 对话应符合角色性格
- 不应有过多正式/书面化表达
- 应有口语化/角色特色表达
"""

import re
from typing import List, Dict, Optional
from .base_checker import BaseChecker
from ..engine.data_structures import Issue, CheckerType


class DialogueAuthenticityChecker(BaseChecker):
    """对话真实性检测器"""

    def __init__(self):
        super().__init__(CheckerType.AI_TRACE)

        # AI对话特征词
        self.ai_patterns = [
            r'我相信',
            r'毫无疑问',
            r'必须承认',
            r'从某种意义上',
            r'事实上',
            r'总的来说',
            r'毫无疑问',
            r'不言而喻',
            r'显而易见',
            r'众所周知'
        ]

        # 正式/书面化表达
        self.formal_patterns = [
            r'因此', r'然而', r'但是', r'所以',
            r'由于', r'既然', r'倘若', r'虽然'
        ]

    def check(self, chapter_content: str, chapter_num: int, context: Optional[Dict] = None) -> List[Issue]:
        issues = []

        # 检测AI特征词
        ai_matches = self._find_ai_patterns(chapter_content)
        if len(ai_matches) > 3:
            issues.append(Issue(
                chapter=chapter_num,
                dimension="AI痕迹",
                issue_type="对话AI化",
                severity="P2",
                description=f"检测到{len(ai_matches)}处AI化对话表达",
                evidence=f"特征词: {', '.join(set(ai_matches))}"
            ))

        # 检测连续正式表达
        formal_count = self._count_formal_expressions(chapter_content)
        total_dialogue = self._estimate_dialogue_ratio(chapter_content)

        if total_dialogue > 0 and formal_count / total_dialogue > 0.5:
            issues.append(Issue(
                chapter=chapter_num,
                dimension="AI痕迹",
                issue_type="对话过于正式",
                severity="P3",
                description="对话中正式表达占比过高，不够口语化"
            ))

        return issues

    def _find_ai_patterns(self, content: str) -> List[str]:
        """找出所有AI特征词"""
        matches = []
        for pattern in self.ai_patterns:
            found = re.findall(pattern, content)
            matches.extend(found)
        return matches

    def _count_formal_expressions(self, content: str) -> int:
        """统计正式表达数量"""
        count = 0
        for pattern in self.formal_patterns:
            count += len(re.findall(pattern, content))
        return count

    def _estimate_dialogue_ratio(self, content: str) -> float:
        """估算对话占比"""
        dialogue_marks = content.count('「') + content.count('"')
        return dialogue_marks / 2  # 每段对话有开始和结束
```

- [ ] **Step 2: 测试检测器**

```bash
python -c "
from infra.consistency.checkers.dialogue_authenticity_checker import DialogueAuthenticityChecker
from infra.paths import ProjectPaths

paths = ProjectPaths.get()
content = paths.read_chapter(1)

checker = DialogueAuthenticityChecker()
issues = checker.check(content, 1)
print(f'ch001: 发现 {len(issues)} 个对话真实感问题')
"
```

- [ ] **Step 3: 提交**

```bash
git add infra/consistency/checkers/dialogue_authenticity_checker.py
git commit -m "feat: add DialogueAuthenticityChecker"
```

---

## Task 4: 添加修复方法

**Files:**
- Modify: `tools/llm_quality_deep_check.py`

- [ ] **Step 1: 添加3个新修复方法**

在 `LLMQualityChecker` 类中添加：

```python
def repair_pacing_issue(self, issue: Issue, chapter_content: str) -> str:
    """修复节奏问题"""
    prompt = f"""修复以下小说章节中的节奏问题：

{chapter_content[:3000]}

问题：{issue.description}

请在高潮段落后添加适当的缓冲描写（如：角色的内心活动、短暂的平静等），
使节奏更加合理。不要改变剧情内容。
"""
    result = self.llm.generate(prompt)
    return result

def repair_scene_transition(self, issue: Issue, chapter_content: str) -> str:
    """修复场景转换问题"""
    prompt = f"""修复以下小说章节中的场景转换问题：

{chapter_content[:3000]}

问题：{issue.description}

请在突兀的场景转换处添加过渡描写（如：时间流逝、空间转移等），
使场景转换更加自然流畅。
"""
    result = self.llm.generate(prompt)
    return result

def repair_dialogue_authenticity(self, issue: Issue, chapter_content: str) -> str:
    """修复对话真实感问题"""
    prompt = f"""修复以下小说章节中的AI化对话：

{chapter_content[:3000]}

问题：{issue.description}

请将过于正式/书面化的AI对话替换为更口语化、符合角色性格的表达。
"""
    result = self.llm.generate(prompt)
    return result
```

- [ ] **Step 2: 提交**

```bash
git add tools/llm_quality_deep_check.py
git commit -m "feat: add repair methods for pacing, scene transition, and dialogue"
```

---

## Task 5: 优化 ProblemClassifier

**Files:**
- Modify: `tools/problem_classifier.py`

- [ ] **Step 1: 扩展检测器局限案例**

在 `DETECTOR_LIMITATIONS` 中添加：

```python
# 新增：节奏检测器宇宙场景局限
"节奏过密": {
    "patterns": ["宇宙级", "星际战争", "跨维度", "亿万年"],
    "description": "宇宙级战斗场景节奏密集是正常的"
},

# 新增：场景转换宇宙场景局限
"场景转换突兀": {
    "patterns": ["维度裂缝", "空间跳跃", "传送", "虫洞"],
    "description": "科幻/奇幻场景中突兀转换可能是设定需要"
},
```

- [ ] **Step 2: 提交**

```bash
git add tools/problem_classifier.py
git commit -m "feat: extend ProblemClassifier with new detector limitations"
```

---

## Task 6: 完整测试

- [ ] **Step 1: 运行测试套件**

```bash
pytest tests/ -x -q --tb=short
```

- [ ] **Step 2: 测试新检测器**

```bash
python -c "
from infra.consistency.checkers.pacing_checker import PacingChecker
from infra.consistency.checkers.scene_transition_checker import SceneTransitionChecker
from infra.consistency.checkers.dialogue_authenticity_checker import DialogueAuthenticityChecker
from infra.paths import ProjectPaths

paths = ProjectPaths.get()
content = paths.read_chapter(1)

for Checker, name in [(PacingChecker, 'Pacing'), (SceneTransitionChecker, 'Scene'), (DialogueAuthenticityChecker, 'Dialogue')]:
    checker = Checker()
    issues = checker.check(content, 1)
    print(f'{name}Checker: {len(issues)} issues')
"
```

- [ ] **Step 3: 提交**

```bash
git add -A
git commit -m "test: verify Phase 3 quality improvements"
```

---

## 验证清单

- [ ] PacingChecker节奏检测器正常工作
- [ ] SceneTransitionChecker场景转换检测器正常工作
- [ ] DialogueAuthenticityChecker对话真实性检测器正常工作
- [ ] 3个新修复方法可用
- [ ] ProblemClassifier覆盖新检测器局限
- [ ] 所有测试继续通过
