# ReAct架构升级实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将主控调度Agent升级为智能写作助手，用户通过自然语言指令完成从构思到创作的完整流程

**Architecture:** 采用ReAct架构（主专家+子专家+ReAct循环），主专家理解意图并规划任务，子专家执行具体任务，循环迭代直到完成

**Tech Stack:** Python + asyncio + fsm (有限状态机)

---

## 文件结构

```
novel-factory/
├── react_system/
│   ├── __init__.py
│   ├── main_expert/
│   │   ├── __init__.py
│   │   ├── intent_classifier.py      # 意图分类
│   │   ├── task_planner.py           # 任务规划
│   │   ├── coordinator.py            # 子专家协调
│   │   └── response_formatter.py      # 响应格式化
│   ├── sub_experts/
│   │   ├── __init__.py
│   │   ├── outline_expert.py         # 大纲专家
│   │   ├── writing_expert.py          # 写作专家
│   │   ├── review_expert.py           # 审核专家
│   │   ├── character_expert.py        # 角色专家
│   │   └── world_expert.py            # 世界观专家
│   ├── react_loop/
│   │   ├── __init__.py
│   │   ├── thought_engine.py          # 思考引擎
│   │   ├── action_executor.py         # 行动执行器
│   │   ├── observer.py                # 观察器
│   │   └── loop_manager.py            # 循环管理器
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── conversation_memory.py    # 对话记忆
│   │   └── context_store.py          # 上下文存储
│   └── config/
│       ├── experts_config.yaml        # 专家配置
│       └── react_config.yaml          # ReAct配置
└── config/
    └── react_settings.yaml            # 总配置
```

---

### Task 1: 创建ReAct循环核心

**Files:**
- Create: `novel-factory/react_system/__init__.py`
- Create: `novel-factory/react_system/react_loop/__init__.py`
- Create: `novel-factory/react_system/react_loop/loop_manager.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_react_loop.py

import pytest
from react_system.react_loop.loop_manager import ReActLoopManager, ReActStep

def test_react_step_creation():
    """测试ReAct步骤创建"""
    step = ReActStep(
        thought="用户想要创建新小说",
        action="classify_intent",
        observation="意图分类为create_novel"
    )
    assert step.thought == "用户想要创建新小说"
    assert step.action == "classify_intent"

def test_loop_manager_initialization():
    """测试循环管理器初始化"""
    manager = ReActLoopManager(max_iterations=10)
    assert manager.max_iterations == 10
    assert manager.current_iteration == 0

def test_loop_termination():
    """测试循环终止条件"""
    manager = ReActLoopManager(max_iterations=2)
    manager.current_iteration = 2
    assert manager.should_terminate() is True
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory && python -m pytest tests/test_react_loop.py -v`
Expected: FAIL with "cannot import"

- [ ] **Step 3: 实现循环管理器**

```python
# react_system/react_loop/loop_manager.py

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class StepType(Enum):
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    RESPONSE = "response"

@dataclass
class ReActStep:
    """ReAct循环中的单步"""
    step_type: StepType
    thought: Optional[str] = None
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None
    response: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            'type': self.step_type.value,
            'thought': self.thought,
            'action': self.action,
            'action_input': self.action_input,
            'observation': self.observation,
            'response': self.response,
            'timestamp': self.timestamp.isoformat()
        }

class ReActLoopManager:
    """ReAct循环管理器"""

    def __init__(self, max_iterations: int = 10):
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.steps: List[ReActStep] = []
        self.context: Dict[str, Any] = {}

    def add_thought(self, thought: str) -> ReActStep:
        """添加思考步骤"""
        step = ReActStep(step_type=StepType.THOUGHT, thought=thought)
        self.steps.append(step)
        return step

    def add_action(
        self,
        action: str,
        action_input: Optional[Dict[str, Any]] = None
    ) -> ReActStep:
        """添加行动步骤"""
        step = ReActStep(
            step_type=StepType.ACTION,
            action=action,
            action_input=action_input
        )
        self.steps.append(step)
        return step

    def add_observation(self, observation: str) -> ReActStep:
        """添加观察步骤"""
        step = ReActStep(step_type=StepType.OBSERVATION, observation=observation)
        self.steps.append(step)
        return step

    def add_response(self, response: str) -> ReActStep:
        """添加响应步骤"""
        step = ReActStep(step_type=StepType.RESPONSE, response=response)
        self.steps.append(step)
        return step

    def should_terminate(self) -> bool:
        """检查是否应该终止循环"""
        # 达到最大迭代
        if self.current_iteration >= self.max_iterations:
            return True

        # 检查最后一个响应是否完整
        for step in reversed(self.steps):
            if step.step_type == StepType.RESPONSE:
                return step.response is not None

        return False

    def get_last_step(self) -> Optional[ReActStep]:
        """获取最后一步"""
        return self.steps[-1] if self.steps else None

    def get_full_trace(self) -> List[Dict]:
        """获取完整追踪"""
        return [step.to_dict() for step in self.steps]

    def increment_iteration(self):
        """增加迭代计数"""
        self.current_iteration += 1

    def reset(self):
        """重置循环"""
        self.current_iteration = 0
        self.steps = []
        self.context = {}
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/test_react_loop.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
mkdir -p react_system/react_loop
git add react_system/__init__.py react_system/react_loop/__init__.py react_system/react_loop/loop_manager.py
git commit -m "feat(react): 添加ReAct循环管理器"
```

---

### Task 2: 实现意图分类器

**Files:**
- Create: `novel-factory/react_system/main_expert/__init__.py`
- Create: `novel-factory/react_system/main_expert/intent_classifier.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_intent_classifier.py

import pytest
from react_system.main_expert.intent_classifier import IntentClassifier, Intent

def test_classify_create_novel():
    """测试创建小说意图分类"""
    classifier = IntentClassifier()
    intent = classifier.classify("帮我写一个关于星际探险的小说")
    assert intent.type == "create_novel"
    assert intent.confidence > 0.5

def test_classify_continue_writing():
    """测试续写意图分类"""
    classifier = IntentClassifier()
    intent = classifier.classify("继续写下一章")
    assert intent.type == "continue_writing"

def test_classify_review():
    """测试审核意图分类"""
    classifier = IntentClassifier()
    intent = classifier.classify("帮我审核一下这几章")
    assert intent.type == "review"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/test_intent_classifier.py -v`
Expected: FAIL with "cannot import"

- [ ] **Step 3: 实现意图分类器**

```python
# react_system/main_expert/intent_classifier.py

from dataclasses import dataclass
from typing import List, Dict, Optional
import re

@dataclass
class Intent:
    """意图"""
    type: str
    confidence: float
    entities: Dict[str, any]
    raw_input: str

class IntentClassifier:
    """意图分类器"""

    INTENT_PATTERNS = {
        'create_novel': {
            'patterns': [
                r'创建小说', r'写小说', r'新小说', r'开始创作',
                r'写个.*小说', r'想写.*小说'
            ],
            'confidence_threshold': 0.7
        },
        'continue_writing': {
            'patterns': [
                r'续写', r'继续写', r'往下写', r'接着写',
                r'写下一', r'后面的内容'
            ],
            'confidence_threshold': 0.7
        },
        'outline_generation': {
            'patterns': [
                r'写大纲', r'生成大纲', r'帮我规划',
                r'设计大纲', r'梳理情节'
            ],
            'confidence_threshold': 0.7
        },
        'revision': {
            'patterns': [
                r'修改', r'润色', r'调整', r'优化',
                r'改一下', r'修订'
            ],
            'confidence_threshold': 0.7
        },
        'review': {
            'patterns': [
                r'审核', r'检查', r'看看怎么样',
                r'评审', r'质量怎么样'
            ],
            'confidence_threshold': 0.7
        },
        'brainstorm': {
            'patterns': [
                r'头脑风暴', r'给我点灵感', r'想想看',
                r'有什么想法', r'创意'
            ],
            'confidence_threshold': 0.7
        },
        'character_design': {
            'patterns': [
                r'设计角色', r'角色设定', r'人物塑造',
                r'角色.*怎么样'
            ],
            'confidence_threshold': 0.7
        },
        'world_design': {
            'patterns': [
                r'世界观', r'设定', r'世界.*构建',
                r'背景设定'
            ],
            'confidence_threshold': 0.7
        }
    }

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """预编译正则表达式"""
        for intent_type, config in self.INTENT_PATTERNS.items():
            config['compiled_patterns'] = [
                re.compile(p, re.IGNORECASE)
                for p in config['patterns']
            ]

    def classify(self, user_input: str) -> Intent:
        """分类用户输入"""
        best_intent = None
        best_confidence = 0.0
        entities = {}

        for intent_type, config in self.INTENT_PATTERNS.items():
            confidence = self._calculate_confidence(
                user_input,
                config['compiled_patterns']
            )

            if confidence > best_confidence:
                best_confidence = confidence
                best_intent = intent_type

                # 提取实体
                entities = self._extract_entities(user_input, intent_type)

        # 如果最高置信度低于阈值，返回未知
        if best_confidence < 0.3:
            return Intent(
                type="unknown",
                confidence=0.0,
                entities={},
                raw_input=user_input
            )

        return Intent(
            type=best_intent,
            confidence=best_confidence,
            entities=entities,
            raw_input=user_input
        )

    def _calculate_confidence(self, text: str, patterns: List) -> float:
        """计算匹配置信度"""
        matches = sum(1 for p in patterns if p.search(text))
        if not patterns:
            return 0.0
        return min(1.0, matches / len(patterns) * 1.5)

    def _extract_entities(self, text: str, intent_type: str) -> Dict:
        """提取实体"""
        entities = {}

        # 提取章节号
        chapter_match = re.search(r'ch(\d+)', text, re.IGNORECASE)
        if chapter_match:
            entities['chapter'] = f"ch{chapter_match.group(1)}"

        # 提取角色名（简单实现）
        known_characters = ['林夜', '苏琳', '暗皇']
        for char in known_characters:
            if char in text:
                entities.setdefault('characters', []).append(char)

        return entities
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/test_intent_classifier.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add react_system/main_expert/__init__.py react_system/main_expert/intent_classifier.py
git commit -m "feat(react): 实现意图分类器"
```

---

### Task 3: 实现主专家协调器

**Files:**
- Create: `novel-factory/react_system/main_expert/coordinator.py`
- Create: `novel-factory/react_system/main_expert/task_planner.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_coordinator.py

import pytest
from react_system.main_expert.coordinator import MainExpertCoordinator
from react_system.main_expert.intent_classifier import Intent

@pytest.fixture
def coordinator():
    return MainExpertCoordinator()

def test_coordinator_initialization(coordinator):
    """测试协调器初始化"""
    assert coordinator is not None
    assert coordinator.loop_manager is not None

def test_process_create_novel_intent(coordinator):
    """测试处理创建小说意图"""
    intent = Intent(
        type="create_novel",
        confidence=0.9,
        entities={},
        raw_input="帮我写一个科幻小说"
    )

    # 由于是异步，需要用event loop
    import asyncio
    result = asyncio.get_event_loop().run_until_complete(
        coordinator.process_intent(intent)
    )

    assert result is not None
    assert 'plan' in result or 'response' in result
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/test_coordinator.py -v`
Expected: FAIL with "cannot import"

- [ ] **Step 3: 实现任务规划器**

```python
# react_system/main_expert/task_planner.py

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class Task:
    """任务"""
    task_id: str
    task_type: str
    description: str
    sub_tasks: List['Task']
    status: str = "pending"
    result: Any = None

class TaskPlanner:
    """任务规划器"""

    def create_plan(self, intent_type: str, entities: Dict) -> List[Task]:
        """根据意图类型创建任务计划"""

        if intent_type == "create_novel":
            return self._plan_create_novel(entities)
        elif intent_type == "continue_writing":
            return self._plan_continue_writing(entities)
        elif intent_type == "outline_generation":
            return self._plan_outline_generation(entities)
        elif intent_type == "revision":
            return self._plan_revision(entities)
        elif intent_type == "review":
            return self._plan_review(entities)
        elif intent_type == "brainstorm":
            return self._plan_brainstorm(entities)
        else:
            return [self._create_unknown_task(intent_type)]

    def _plan_create_novel(self, entities: Dict) -> List[Task]:
        """创建小说计划"""
        return [
            Task(
                task_id="novel_type",
                task_type="outline",
                description="确定小说类型和基调",
                sub_tasks=[]
            ),
            Task(
                task_id="novel_outline",
                task_type="outline",
                description="生成小说大纲",
                sub_tasks=[
                    Task(
                        task_id="world_outline",
                        task_type="world_design",
                        description="设计世界观",
                        sub_tasks=[]
                    ),
                    Task(
                        task_id="character_outline",
                        task_type="character_design",
                        description="设计主要角色",
                        sub_tasks=[]
                    ),
                    Task(
                        task_id="plot_outline",
                        task_type="plot_design",
                        description="设计情节主线",
                        sub_tasks=[]
                    )
                ]
            ),
            Task(
                task_id="novel_sample",
                task_type="writing",
                description="生成核心样章",
                sub_tasks=[]
            )
        ]

    def _plan_continue_writing(self, entities: Dict) -> List[Task]:
        """续写计划"""
        chapter = entities.get('chapter', 'ch001')

        return [
            Task(
                task_id="check_context",
                task_type="review",
                description=f"检查{chapter}上下文",
                sub_tasks=[]
            ),
            Task(
                task_id="generate_continuation",
                task_type="writing",
                description=f"续写{chapter}后续内容",
                sub_tasks=[]
            ),
            Task(
                task_id="review_continuation",
                task_type="review",
                description="审核续写内容",
                sub_tasks=[]
            )
        ]

    def _plan_outline_generation(self, entities: Dict) -> List[Task]:
        """大纲生成计划"""
        return [
            Task(
                task_id="collect_ideas",
                task_type="brainstorm",
                description="收集创作思路",
                sub_tasks=[]
            ),
            Task(
                task_id="generate_global_outline",
                task_type="outline",
                description="生成全局大纲",
                sub_tasks=[]
            ),
            Task(
                task_id="generate_volume_outline",
                task_type="outline",
                description="生成卷大纲",
                sub_tasks=[]
            )
        ]

    def _plan_revision(self, entities: Dict) -> List[Task]:
        """修改计划"""
        return [
            Task(
                task_id="identify_issues",
                task_type="review",
                description="识别需要修改的问题",
                sub_tasks=[]
            ),
            Task(
                task_id="execute_revision",
                task_type="revision",
                description="执行修改",
                sub_tasks=[]
            ),
            Task(
                task_id="review_revision",
                task_type="review",
                description="审核修改结果",
                sub_tasks=[]
            )
        ]

    def _plan_review(self, entities: Dict) -> List[Task]:
        """审核计划"""
        return [
            Task(
                task_id="review_content",
                task_type="review",
                description="进行内容审核",
                sub_tasks=[]
            ),
            Task(
                task_id="generate_report",
                task_type="report",
                description="生成审核报告",
                sub_tasks=[]
            )
        ]

    def _plan_brainstorm(self, entities: Dict) -> List[Task]:
        """头脑风暴计划"""
        return [
            Task(
                task_id="collect_ideas",
                task_type="brainstorm",
                description="收集创意想法",
                sub_tasks=[]
            ),
            Task(
                task_id="organize_ideas",
                task_type="analysis",
                description="整理并归类想法",
                sub_tasks=[]
            )
        ]

    def _create_unknown_task(self, intent_type: str) -> Task:
        """未知意图任务"""
        return Task(
            task_id="unknown",
            task_type="unknown",
            description=f"无法识别的意图类型: {intent_type}",
            sub_tasks=[]
        )
```

- [ ] **Step 4: 实现协调器**

```python
# react_system/main_expert/coordinator.py

from typing import Dict, Any, Optional
from .intent_classifier import Intent, IntentClassifier
from .task_planner import TaskPlanner, Task
from .response_formatter import ResponseFormatter
from react_system.react_loop.loop_manager import ReActLoopManager

class MainExpertCoordinator:
    """主专家协调器"""

    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.task_planner = TaskPlanner()
        self.response_formatter = ResponseFormatter()
        self.loop_manager = ReActLoopManager(max_iterations=10)

    async def process_intent(self, intent: Intent) -> Dict[str, Any]:
        """处理用户意图"""

        # 思考：理解用户需求
        self.loop_manager.add_thought(
            f"用户意图是{intent.type}，置信度{intent.confidence}。"
            f"提取到实体：{intent.entities}"
        )

        # 创建任务计划
        plan = self.task_planner.create_plan(intent.type, intent.entities)

        # 添加行动
        self.loop_manager.add_action(
            action="create_plan",
            action_input={'intent': intent.type, 'task_count': len(plan)}
        )

        # 观察
        self.loop_manager.add_observation(
            f"已创建包含{len(plan)}个任务的建设计划"
        )

        # 执行任务（这里简化处理，实际需要调用子专家）
        results = await self._execute_plan(plan)

        # 整合响应
        response = self.response_formatter.format(
            intent_type=intent.type,
            plan=plan,
            results=results
        )

        # 添加响应
        self.loop_manager.add_response(response)

        return {
            'intent': intent.type,
            'plan': [self._task_to_dict(t) for t in plan],
            'results': results,
            'response': response,
            'trace': self.loop_manager.get_full_trace()
        }

    async def _execute_plan(self, plan: list) -> Dict[str, Any]:
        """执行任务计划"""
        results = {}

        for task in plan:
            # 模拟任务执行
            results[task.task_id] = {
                'status': 'completed',
                'description': task.description
            }

            # 执行子任务
            for sub_task in task.sub_tasks:
                results[sub_task.task_id] = {
                    'status': 'completed',
                    'description': sub_task.description
                }

        return results

    def _task_to_dict(self, task: Task) -> Dict:
        """任务转字典"""
        return {
            'task_id': task.task_id,
            'task_type': task.task_type,
            'description': task.description,
            'sub_tasks': [self._task_to_dict(t) for t in task.sub_tasks]
        }

    async def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """处理用户输入的便捷方法"""
        intent = self.intent_classifier.classify(user_input)
        return await self.process_intent(intent)
```

- [ ] **Step 5: 创建响应格式化器**

```python
# react_system/main_expert/response_formatter.py

from typing import Dict, Any, List

class ResponseFormatter:
    """响应格式化器"""

    def format(
        self,
        intent_type: str,
        plan: List,
        results: Dict[str, Any]
    ) -> str:
        """格式化响应"""

        if intent_type == "create_novel":
            return self._format_create_novel(plan, results)
        elif intent_type == "continue_writing":
            return self._format_continue_writing(plan, results)
        elif intent_type == "review":
            return self._format_review(plan, results)
        else:
            return self._format_general(plan, results)

    def _format_create_novel(self, plan: List, results: Dict) -> str:
        """创建小说响应"""
        response = "好的，我来帮你创建小说。\n\n"
        response += "**计划步骤：**\n"

        for i, task in enumerate(plan, 1):
            response += f"{i}. {task.description}\n"
            for j, sub_task in enumerate(task.sub_tasks, 1):
                response += f"   {i}.{j} {sub_task.description}\n"

        response += "\n我将按照这个计划开始工作。有什么需要调整的吗？"
        return response

    def _format_continue_writing(self, plan: List, results: Dict) -> str:
        """续写响应"""
        response = "好的，我来帮你续写内容。\n\n"
        response += "**续写计划：**\n"

        for i, task in enumerate(plan, 1):
            response += f"{i}. {task.description}\n"

        response += "\n正在开始续写..."
        return response

    def _format_review(self, plan: List, results: Dict) -> str:
        """审核响应"""
        response = "好的，我来帮你审核内容。\n\n"
        response += "**审核计划：**\n"

        for i, task in enumerate(plan, 1):
            response += f"{i}. {task.description}\n"

        return response

    def _format_general(self, plan: List, results: Dict) -> str:
        """通用响应"""
        response = "好的，我来帮你处理。\n\n"
        response += "**执行计划：**\n"

        for i, task in enumerate(plan, 1):
            response += f"{i}. {task.description}\n"

        return response
```

- [ ] **Step 6: 运行测试验证通过**

Run: `python -m pytest tests/test_coordinator.py -v`
Expected: PASS (部分测试可能需要异步支持)

- [ ] **Step 7: 提交**

```bash
git add react_system/main_expert/coordinator.py react_system/main_expert/task_planner.py react_system/main_expert/response_formatter.py
git commit -m "feat(react): 实现主专家协调器"
```

---

### Task 4: 创建子专家基类

**Files:**
- Create: `novel-factory/react_system/sub_experts/__init__.py`
- Create: `novel-factory/react_system/sub_experts/base_expert.py`

- [ ] **Step 1: 创建子专家基类**

```python
# react_system/sub_experts/base_expert.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class ExpertResponse:
    """专家响应"""
    success: bool
    content: Any
    expert_name: str
    metadata: Dict[str, Any]
    error: Optional[str] = None

class BaseExpert(ABC):
    """子专家基类"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> ExpertResponse:
        """
        执行任务

        Args:
            task: 任务描述，包含task_type和参数

        Returns:
            ExpertResponse: 执行结果
        """
        pass

    async def health_check(self) -> bool:
        """健康检查"""
        return True

    @property
    @abstractmethod
    def supported_tasks(self) -> list:
        """支持的任务类型"""
        pass
```

- [ ] **Step 2: 创建大纲专家**

```python
# react_system/sub_experts/outline_expert.py

from typing import Dict, Any
from .base_expert import BaseExpert, ExpertResponse

class OutlineExpert(BaseExpert):
    """大纲专家"""

    def __init__(self):
        super().__init__("outline_expert")

    @property
    def supported_tasks(self) -> list:
        return ["outline_generation", "plot_design", "world_design"]

    async def execute(self, task: Dict[str, Any]) -> ExpertResponse:
        """执行大纲生成任务"""
        try:
            task_type = task.get('task_type')

            if task_type == 'outline_generation':
                content = await self._generate_outline(task)
            elif task_type == 'plot_design':
                content = await self._design_plot(task)
            elif task_type == 'world_design':
                content = await self._design_world(task)
            else:
                return ExpertResponse(
                    success=False,
                    content=None,
                    expert_name=self.name,
                    metadata={},
                    error=f"Unknown task type: {task_type}"
                )

            return ExpertResponse(
                success=True,
                content=content,
                expert_name=self.name,
                metadata={'task_type': task_type}
            )

        except Exception as e:
            return ExpertResponse(
                success=False,
                content=None,
                expert_name=self.name,
                metadata={},
                error=str(e)
            )

    async def _generate_outline(self, task: Dict) -> Dict:
        """生成大纲"""
        return {
            'outline_type': 'global',
            'sections': []
        }

    async def _design_plot(self, task: Dict) -> Dict:
        """设计情节"""
        return {
            'plot_type': 'main',
            'key_events': []
        }

    async def _design_world(self, task: Dict) -> Dict:
        """设计世界观"""
        return {
            'world_name': '',
            'rules': []
        }
```

- [ ] **Step 3: 提交**

```bash
git add react_system/sub_experts/__init__.py react_system/sub_experts/base_expert.py react_system/sub_experts/outline_expert.py
git commit -m "feat(react): 实现子专家基类和大纲专家"
```

---

## 实现完成检查

- [ ] ReAct循环核心已实现
- [ ] 意图分类器已实现
- [ ] 主专家协调器已实现
- [ ] 子专家基类已实现
- [ ] 大纲专家已实现
- [ ] 配置文件已创建
- [ ] 测试通过