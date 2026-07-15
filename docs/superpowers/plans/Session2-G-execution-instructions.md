# Session 2 执行指令：方向G（插件框架/Hook系统）

> **项目路径**: `/home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory`
> **参考文档**: `docs/superpowers/specs/2026-05-19-hook-plugin-framework-design.md`

---

## 方向G：插件框架（Hook系统）

### G-Step1: 创建事件总线
**Task ID**: #30
**文件**: `hooks/event_bus.py`

**实现要点**:
1. 定义 `Event` 数据类:
   ```python
   @dataclass
   class Event:
       name: str                           # 事件名称（PHASE_CHANGED等）
       source: str                         # 事件源
       data: Dict[str, Any]               # 事件数据
       timestamp: datetime = field(default_factory=datetime.now)
   ```

2. 定义 `EventBus` 类:
   ```python
   class EventBus:
       def subscribe(self, event_name: str, handler: Callable[[Event], None]) -> None: ...
       def unsubscribe(self, event_name: str, handler: Callable[[Event], None]) -> None: ...
       def publish(self, event: Event) -> None: ...
       def publish_async(self, event: Event) -> None: ...  # 异步发布
   ```

3. 支持事件过滤（条件判断）
4. 支持优先级（多个handler按优先级执行）

**验收标准**:
- `event_bus.subscribe("CHAPTER_WRITTEN", handler)` 能注册handler
- `event_bus.publish(event)` 时handler被正确调用
- 支持异步发布

---

### G-Step2: 创建配置加载器
**Task ID**: #32
**文件**: `hooks/config_loader.py`

**参考**: `hooks.yaml` 规范（第4节配置格式）

**实现要点**:
1. 定义 `HookConfig` 数据类:
   ```python
   @dataclass
   class HookConfig:
       name: str
       trigger: Dict[str, Any]            # event + conditions
       actions: List[Dict[str, Any]]     # action列表
       required: bool = False
       timeout: int = 60
   ```

2. 定义 `HookConfigLoader` 类:
   ```python
   class HookConfigLoader:
       def load(self, config_path: str) -> List[HookConfig]: ...
       def validate(self, config: List[HookConfig]) -> bool: ...  # 验证合法性
   ```

3. 支持条件表达式解析（如 `"chapter_status == 'draft_completed'"`）

**验收标准**:
- 能解析 `hooks.yaml` 文件
- 验证配置合法性（事件类型、动作类型）

---

### G-Step3: 创建Hook引擎核心
**Task ID**: #31
**文件**: `hooks/hook_engine.py`

**实现要点**:
1. 定义 `HookEngine` 类:
   ```python
   class HookEngine:
       def __init__(self, event_bus: EventBus, config_loader: HookConfigLoader): ...
       def load_hooks(self, config_path: str) -> None: ...
       def trigger(self, event: Event) -> List[ActionResult]: ...  # 触发Hook
       def get_hook_status(self, hook_name: str) -> HookStatus: ...  # 获取Hook状态
   ```

2. 事件匹配逻辑:
   - 匹配 `trigger.event` 与 `event.name`
   - 评估 `trigger.conditions` 条件表达式

3. 执行动作链:
   - 按顺序执行 `actions` 列表
   - 实现超时控制（`timeout` 参数）
   - 实现 `required/optional` 语义

**验收标准**:
- 事件匹配正确（CHAPTER_WRITTEN只匹配 `event: "CHAPTER_WRITTEN"` 的Hook）
- required Hook失败时抛出异常
- optional Hook失败时不阻止流程

---

### G-Step4: 创建动作基类
**Task ID**: #35
**文件**: `hooks/actions/base.py`

**实现要点**:
1. 定义 `ActionResult` 数据类:
   ```python
   @dataclass
   class ActionResult:
       success: bool
       output: Any = None
       error: Optional[str] = None
       duration_ms: float = 0
   ```

2. 定义 `BaseAction` 抽象基类:
   ```python
   class BaseAction(ABC):
       @abstractmethod
       def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ActionResult: ...

       @property
       @abstractmethod
       def action_type(self) -> str: ...  # "run_checker", "notify"等
   ```

**验收标准**:
- `BaseAction` 不能直接实例化
- 子类必须实现 `execute()` 和 `action_type`

---

### G-Step5: 实现核心动作类型
**Task ID**: #34
**文件**: `hooks/actions/run_checker.py`, `hooks/actions/notify.py`, `hooks/actions/update_state.py`

**实现要点**:

#### run_checker.py - 运行检查器
```python
class RunCheckerAction(BaseAction):
    def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        # params: {"checker": "auto_consistency_checker", "chapter_range": "current"}
        # 调用 ConsistencyEngine 执行检查
        # 返回检查结果
```

#### notify.py - 发送通知
```python
class NotifyAction(BaseAction):
    def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        # params: {"channel": "writer_channel", "template": "review_complete"}
        # 发送通知到指定渠道
        # 支持模板渲染
```

#### update_state.py - 更新状态
```python
class UpdateStateAction(BaseAction):
    def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        # params: {"target": "workflow_state.json", "field": "current_step", "value": "STEP_13"}
        # 更新workflow_state.json中的字段
```

**验收标准**:
- RunCheckerAction 能调用 ConsistencyEngine
- NotifyAction 能发送通知（可mock）
- UpdateStateAction 能更新状态文件

---

### G-Step6: 创建Hook配置示例
**Task ID**: #33
**文件**: `hooks.yaml`

**实现要点**:
按照规范创建 `hooks.yaml`，实现两个示例Hook：

```yaml
hooks:
  - name: "自动质量门禁"
    trigger:
      event: "CHAPTER_WRITTEN"
      conditions:
        - "chapter_status == 'draft_completed'"
    actions:
      - type: "run_checker"
        checker: "consistency_engine"
        params:
          chapter_range: "current"
    required: true
    timeout: 60

  - name: "审核完成通知作家"
    trigger:
      event: "REVIEW_COMPLETED"
      conditions:
        - "review_result in ['PASS', 'NEED_REVISION']"
    actions:
      - type: "notify"
        channel: "writer_channel"
        template: "review_complete"
    required: false
```

**验收标准**:
- `hooks.yaml` 语法正确，能被 `HookConfigLoader` 解析
- 至少包含2个Hook示例

---

### G-Step7: 编写Hook系统测试
**Task ID**: #36
**文件**: `tests/hooks/test_event_bus.py`, `tests/hooks/test_hook_engine.py`, `tests/hooks/test_actions.py`

**实现要点**:

#### test_event_bus.py
- `TestEventBus::test_subscribe_and_publish` - 订阅/发布测试
- `TestEventBus::test_unsubscribe` - 取消订阅测试
- `TestEventBus::test_async_publish` - 异步发布测试

#### test_hook_engine.py
- `TestHookEngine::test_load_hooks` - 加载配置测试
- `TestHookEngine::test_event_matching` - 事件匹配测试
- `TestHookEngine::test_required_hook_blocks_flow` - required语义测试
- `TestHookEngine::test_optional_hook_does_not_block` - optional语义测试

#### test_actions.py
- `TestRunCheckerAction::test_execute` - 执行检查器测试
- `TestNotifyAction::test_execute` - 发送通知测试
- `TestUpdateStateAction::test_execute` - 更新状态测试

**验收标准**: 所有测试通过

---

## 执行顺序建议

```
Session 2:
├── G-Step1: 创建事件总线
├── G-Step2: 创建配置加载器
├── G-Step3: 创建Hook引擎核心
├── G-Step4: 创建动作基类
├── G-Step5: 实现核心动作类型
├── G-Step6: 创建Hook配置示例
└── G-Step7: 编写Hook系统测试
```

**完成后请更新Task状态为completed**