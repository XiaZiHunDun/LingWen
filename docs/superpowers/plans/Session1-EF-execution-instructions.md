# Session 1 执行指令：方向E（伏笔追踪系统）+ 方向F（AI网关抽象层）

> **项目路径**: `/home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory`
> **参考文档**: `docs/superpowers/specs/` 下相关设计文档
> **执行顺序**: E完成后执行F，或E+F交替进行

---

## 方向E：伏笔追踪系统

### E-Step1: 创建ForeshadowChecker
**Task ID**: #24
**文件**: `consistency/checkers/foreshadow_checker.py`

**参考已有检查器**: `consistency/checkers/character_checker.py` 或 `consistency/checkers/ai_gloss_checker.py`

**实现要点**:
1. 创建 `ForeshadowChecker` 类，继承检查器基类模式
2. `check()` 方法签名:
   ```python
   def check(self, chapter_content: str, chapter_num: int, context: Dict[str, Any]) -> List[Issue]:
   ```
3. 检查逻辑:
   - 从 `context.get("foreshadows", {})` 获取伏笔列表
   - 检查伏笔是否在引入后被正确提及/回收
   - 检测逾期未回收的伏笔（当前章节 > 预期回收章节）
4. 返回 `List[Issue]`，使用 `IssueSeverity` 标记问题等级

**验收标准**:
- 能检测到逾期未回收的伏笔（P1）
- 能检测到伏笔描述与实际内容不符（P2）
- 与一致性引擎集成后正常工作

---

### E-Step2: 扩展QueryEngine伏笔查询
**Task ID**: #23
**文件**: `memory_system/gateway/query_engine.py`

**参考**: `query_engine.py` 现有 `get_character_state()` 方法

**实现要点**:
1. 添加 `query_foreshadows()` 方法:
   ```python
   def query_foreshadows(
       self,
       query: str,
       status: Optional[str] = None,  # pending/in_progress/recycled/invalid
       chapter_range: Optional[Tuple[int, int]] = None,
       top_k: int = 5
   ) -> List[Dict[str, Any]]:
   ```
2. 支持按状态过滤（默认返回所有状态）
3. 支持按章节范围过滤
4. 返回伏笔列表，包含状态、描述、提及章节等信息

**验收标准**:
- `query_foreshadows("林夜的身世")` 返回相关伏笔
- 按状态过滤正确生效

---

### E-Step3: 扩展MemoryGateway伏笔接口
**Task ID**: #22
**文件**: `memory_system/gateway/memory_gateway.py`

**参考**: `memory_gateway.py` 现有 `update_character_state()` 方法

**实现要点**:
1. 添加 `update_foreshadow()` 方法:
   ```python
   def update_foreshadow(
       self,
       fp_id: str,
       event_type: str,  # plant/activate/recycle/invalidate
       metadata: Optional[Dict[str, Any]] = None,
       chapter: Optional[int] = None
   ) -> None:
   ```
2. 事件类型说明:
   - `plant`: 登记新伏笔，需要 `metadata`（title, description, planted_chapter, expected_recycle_chapter）
   - `activate`: 伏笔开始被提及，设置状态为 in_progress
   - `recycle`: 伏笔已回收，设置状态为 recycled
   - `invalidate`: 伏笔失效，设置状态为 invalid
3. 内部调用 `PlotThreadTracker` 的对应方法

**验收标准**:
- `update_foreshadow("fp_001", "plant", {...}, 5)` 能成功登记伏笔
- `update_foreshadow("fp_001", "recycle", chapter=25)` 能更新伏笔状态

---

### E-Step4: 编写伏笔系统测试
**Task ID**: #21
**文件**: `tests/consistency/test_foreshadow_checker.py`, `tests/memory_system/test_plot_thread_tracker.py`

**参考**: `tests/consistency/test_ai_gloss_checker.py`, `tests/memory_system/test_character_tracker.py`

**实现要点**:
1. `test_foreshadow_checker.py`:
   - `TestForeshadowChecker::test_detect_overdue_foreshadow` - 检测逾期伏笔
   - `TestForeshadowChecker::test_detect_unrecycled_foreshadow` - 检测未回收伏笔
   - `TestForeshadowChecker::test_no_issue_for_normal_foreshadow` - 正常伏笔无误报

2. `test_plot_thread_tracker.py`（如不存在）:
   - 基础CRUD测试
   - 状态转换测试
   - 持久化测试

**验收标准**: 所有测试通过（pytest运行）

---

## 方向F：AI网关抽象层

### F-Step1: 创建AI Provider抽象基类
**Task ID**: #27
**文件**: `ai_service/base.py`

**实现要点**:
1. 定义 `ProviderConfig` 数据类:
   ```python
   @dataclass
   class ProviderConfig:
       api_key: str
       endpoint: Optional[str] = None
       model: str = "gpt-4"
       timeout: int = 60
       max_retries: int = 3
   ```

2. 定义 `AIProvider` 抽象基类:
   ```python
   class AIProvider(ABC):
       @abstractmethod
       def generate(self, prompt: str, **kwargs) -> str: ...

       @abstractmethod
       def embed(self, text: str) -> List[float]: ...

       @abstractmethod
       def batch_generate(self, prompts: List[str], **kwargs) -> List[str]: ...
   ```

3. 定义统一的异常类 `AIProviderError`

**验收标准**:
- `AIProvider` 不能直接实例化（抽象类）
- 子类实现所有抽象方法才能实例化

---

### F-Step2: 实现OpenAI Provider
**Task ID**: #28
**文件**: `ai_service/openai_provider.py`

**参考**: `memory_system/vector/embedder.py` 的API调用方式

**实现要点**:
1. `OpenAIProvider` 继承 `AIProvider`
2. `__init__` 接收 `ProviderConfig`
3. `generate()`: 调用 OpenAI Chat Completions API
4. `embed()`: 调用 OpenAI Embeddings API
5. 重试机制：3次，指数退避（1s, 2s, 4s）
6. 错误处理：超时、重试耗尽、API错误

**验收标准**:
- `OpenAIProvider(config).generate("你好")` 返回文本
- `OpenAIProvider(config).embed("测试文本")` 返回向量
- 网络错误时自动重试

---

### F-Step3: 实现Anthropic Provider
**Task ID**: #29
**文件**: `ai_service/anthropic_provider.py`

**实现要点**:
1. `AnthropicProvider` 继承 `AIProvider`
2. `generate()`: 调用 Claude API（messages格式）
3. 接口设计与 OpenAIProvider 保持一致
4. 同样的重试机制和错误处理

**验收标准**:
- `AnthropicProvider(config).generate("你好")` 返回文本
- 与 OpenAIProvider 接口兼容

---

### F-Step4: 实现Provider路由选择器
**Task ID**: #25
**文件**: `ai_service/router.py`

**实现要点**:
1. 定义 `AIRouter` 类:
   ```python
   class AIRouter:
       def __init__(self, config: Dict[str, ProviderConfig]): ...
       def generate(self, prompt: str, provider: Optional[str] = None) -> str: ...
       def embed(self, text: str, provider: Optional[str] = None) -> List[float]: ...
   ```

2. 路由策略:
   - `embedding` 类型自动选择 OpenAI（embed接口）
   - `general` 类型可配置优先级
   - 支持故障转移（Provider A失败自动切换B）

3. 成本优化路由（可选）:
   - 按使用量选择最低成本Provider

**验收标准**:
- `router.generate("你好")` 正确路由到配置的Provider
- Provider故障时自动转移

---

### F-Step5: 编写AI服务测试
**Task ID**: #26
**文件**: `tests/ai_service/test_providers.py`, `tests/ai_service/test_router.py`

**实现要点**:
1. `test_providers.py`:
   - `TestOpenAIProvider::test_generate_success` - mock测试
   - `TestOpenAIProvider::test_embed_success` - mock测试
   - `TestAnthropicProvider::test_generate_success` - mock测试
   - 重试机制测试

2. `test_router.py`:
   - `TestAIRouter::test_route_to_primary_provider` - 路由测试
   - `TestAIRouter::test_failover_on_error` - 故障转移测试

**验收标准**: 所有测试通过

---

## 执行顺序建议

```
Session 1 (本会话):
├── E-Step1: 创建ForeshadowChecker
├── E-Step2: 扩展QueryEngine伏笔查询
├── E-Step3: 扩展MemoryGateway伏笔接口
├── E-Step4: 编写伏笔系统测试
├── F-Step1: 创建AI Provider抽象基类
├── F-Step2: 实现OpenAI Provider
├── F-Step3: 实现Anthropic Provider
├── F-Step4: 实现Provider路由选择器
└── F-Step5: 编写AI服务测试
```

**完成后请更新Task状态为completed**