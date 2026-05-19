# AI服务抽象层实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立统一的AI服务抽象层，封装不同模型提供商的API调用，对上层提供一致接口，支持模型灵活切换和熔断降级

**Architecture:** 采用适配器模式，每种模型（DeepSeek/Claude/Qwen/MiniMax）实现统一接口，网关层负责路由、熔断、缓存

**Tech Stack:** Python + httpx + pydantic

---

## 文件结构

```
novel-factory/
├── ai_gateway/
│   ├── __init__.py
│   ├── gateway.py                    # AI服务网关主类
│   ├── interfaces/
│   │   ├── __init__.py
│   │   ├── base_adapter.py           # 适配器基类
│   │   ├── deepseek_adapter.py       # DeepSeek适配器
│   │   ├── claude_adapter.py         # Claude适配器
│   │   ├── qwen_adapter.py           # 千问适配器
│   │   └── minimax_adapter.py        # Minimax适配器
│   ├── router/
│   │   ├── __init__.py
│   │   ├── router.py                 # 路由策略
│   │   └── cost_optimizer.py         # 成本优化器
│   ├── circuit_breaker/
│   │   ├── __init__.py
│   │   ├── circuit_breaker.py        # 熔断器
│   │   └── fallback_manager.py       # 降级管理器
│   ├── cache/
│   │   ├── __init__.py
│   │   ├── cache_manager.py          # 缓存管理器
│   │   └── response_cache.py         # 响应缓存
│   └── config/
│       ├── __init__.py
│       ├── model_config.yaml          # 模型配置
│       ├── scene_mapping.yaml        # 场景-模型映射
│       └── circuit_breaker.yaml      # 熔断配置
├── config/
│   └── ai_models.yaml                # AI模型总配置
└── tests/
    └── test_ai_gateway.py
```

---

### Task 1: 创建基础适配器接口

**Files:**
- Create: `novel-factory/ai_gateway/__init__.py`
- Create: `novel-factory/ai_gateway/interfaces/__init__.py`
- Create: `novel-factory/ai_gateway/interfaces/base_adapter.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_ai_gateway.py

import pytest
from ai_gateway.interfaces.base_adapter import (
    BaseModelAdapter,
    ModelConfig,
    GenerationParameters,
    AIResponse
)

def test_model_config_creation():
    """测试模型配置创建"""
    config = ModelConfig(
        model_id="deepseek-chat",
        api_key="test_key",
        base_url="https://api.deepseek.com"
    )
    assert config.model_id == "deepseek-chat"

def test_generation_parameters_defaults():
    """测试生成参数默认值"""
    params = GenerationParameters()
    assert params.temperature == 0.7
    assert params.max_tokens == 2000
    assert params.top_p == 0.9

def test_ai_response_structure():
    """测试响应结构"""
    response = AIResponse(
        success=True,
        content="测试输出",
        model="deepseek-chat",
        tokens_used=100,
        latency_ms=500,
        cost=0.002
    )
    assert response.success is True
    assert response.cached is False
    assert response.fallback_used is False

def test_base_adapter_abstract():
    """测试适配器基类是抽象的"""
    with pytest.raises(TypeError):
        BaseModelAdapter()
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory && python -m pytest tests/test_ai_gateway.py::test_model_config_creation -v`
Expected: FAIL with "cannot import"

- [ ] **Step 3: 实现基础接口**

```python
# ai_gateway/interfaces/base_adapter.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum

class ModelType(Enum):
    DEEPSEEK = "deepseek"
    CLAUDE = "claude"
    QWEN = "qwen"
    MINIMAX = "minimax"

@dataclass
class ModelConfig:
    """模型配置"""
    model_id: str
    api_key: str
    base_url: str
    timeout: int = 60
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GenerationParameters:
    """生成参数"""
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 0.9
    top_k: int = 50
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[List[str]] = None

@dataclass
class AIResponse:
    """统一响应格式"""
    success: bool
    content: str
    model: str
    tokens_used: int
    latency_ms: int
    cost: float
    error: Optional[str] = None
    fallback_used: bool = False
    cached: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseModelAdapter(ABC):
    """模型适配器基类"""

    def __init__(self, config: ModelConfig):
        self.config = config
        self._initialized = False

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        parameters: Optional[GenerationParameters] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AIResponse:
        """
        生成内容

        Args:
            prompt: 提示词
            parameters: 生成参数
            context: 上下文信息

        Returns:
            AIResponse: 统一响应格式
        """
        pass

    @abstractmethod
    async def batch_generate(
        self,
        prompts: List[str],
        parameters: Optional[GenerationParameters] = None
    ) -> List[AIResponse]:
        """批量生成"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass

    @property
    @abstractmethod
    def model_type(self) -> ModelType:
        """返回模型类型"""
        pass

    @property
    def is_initialized(self) -> bool:
        return self._initialized
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/test_ai_gateway.py::test_model_config_creation tests/test_ai_gateway.py::test_generation_parameters_defaults tests/test_ai_gateway.py::test_ai_response_structure -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add ai_gateway/interfaces/base_adapter.py ai_gateway/__init__.py ai_gateway/interfaces/__init__.py
git commit -m "feat(ai-gateway): 添加基础适配器接口"
```

---

### Task 2: 实现DeepSeek适配器

**Files:**
- Create: `novel-factory/ai_gateway/interfaces/deepseek_adapter.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_deepseek_adapter.py

import pytest
from ai_gateway.interfaces.deepseek_adapter import DeepSeekAdapter
from ai_gateway.interfaces.base_adapter import ModelConfig, GenerationParameters, ModelType

@pytest.fixture
def deepseek_config():
    return ModelConfig(
        model_id="deepseek-chat",
        api_key="test_key",
        base_url="https://api.deepseek.com/v1"
    )

def test_deepseek_adapter_model_type(deepseek_config):
    """测试DeepSeek适配器模型类型"""
    adapter = DeepSeekAdapter(deepseek_config)
    assert adapter.model_type == ModelType.DEEPSEEK

def test_deepseek_adapter_initialization(deepseek_config):
    """测试DeepSeek适配器初始化"""
    adapter = DeepSeekAdapter(deepseek_config)
    assert adapter.is_initialized is True
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/test_deepseek_adapter.py -v`
Expected: FAIL with "cannot import"

- [ ] **Step 3: 实现DeepSeek适配器**

```python
# ai_gateway/interfaces/deepseek_adapter.py

import httpx
import time
from typing import Optional, Dict, Any, List

from .base_adapter import (
    BaseModelAdapter,
    ModelConfig,
    GenerationParameters,
    AIResponse,
    ModelType
)

class DeepSeekAdapter(BaseModelAdapter):
    """DeepSeek模型适配器"""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def model_type(self) -> ModelType:
        return ModelType.DEEPSEEK

    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=self.config.timeout
            )
        return self._client

    async def generate(
        self,
        prompt: str,
        parameters: Optional[GenerationParameters] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AIResponse:
        """生成内容"""
        params = parameters or GenerationParameters()

        start_time = time.time()

        try:
            client = await self._get_client()

            # 构建请求
            request_data = {
                "model": self.config.model_id,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": params.temperature,
                "max_tokens": params.max_tokens,
                "top_p": params.top_p
            }

            if params.stop:
                request_data["stop"] = params.stop

            # 发送请求
            response = await client.post("/chat/completions", json=request_data)
            response.raise_for_status()

            result = response.json()

            # 计算延迟和成本
            latency_ms = int((time.time() - start_time) * 1000)
            tokens_used = result.get("usage", {}).get("total_tokens", 0)
            cost = tokens_used * 0.0001  # DeepSeek价格

            return AIResponse(
                success=True,
                content=result["choices"][0]["message"]["content"],
                model=self.config.model_id,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                cost=cost
            )

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return AIResponse(
                success=False,
                content="",
                model=self.config.model_id,
                tokens_used=0,
                latency_ms=latency_ms,
                cost=0,
                error=str(e)
            )

    async def batch_generate(
        self,
        prompts: List[str],
        parameters: Optional[GenerationParameters] = None
    ) -> List[AIResponse]:
        """批量生成"""
        tasks = [self.generate(p, parameters) for p in prompts]
        return await asyncio.gather(*tasks)

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            client = await self._get_client()
            response = await client.get("/models")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/test_deepseek_adapter.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add ai_gateway/interfaces/deepseek_adapter.py
git commit -m "feat(ai-gateway): 实现DeepSeek适配器"
```

---

### Task 3: 实现AI服务网关

**Files:**
- Create: `novel-factory/ai_gateway/gateway.py`
- Create: `novel-factory/ai_gateway/config/model_config.yaml`
- Create: `novel-factory/config/ai_models.yaml`

- [ ] **Step 1: 编写测试**

```python
# tests/test_gateway.py

import pytest
from ai_gateway.gateway import AIGateway, ModelType

def test_gateway_initialization():
    """测试网关初始化"""
    gateway = AIGateway()
    assert gateway is not None

def test_gateway_default_model():
    """测试默认模型"""
    gateway = AIGateway()
    # 应该有默认模型配置
    assert gateway.default_model is not None
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/test_gateway.py -v`
Expected: FAIL with "cannot import"

- [ ] **Step 3: 实现AI服务网关**

```python
# ai_gateway/gateway.py

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import asyncio

from .interfaces.base_adapter import (
    BaseModelAdapter,
    GenerationParameters,
    AIResponse,
    ModelType
)
from .interfaces.deepseek_adapter import DeepSeekAdapter
from .interfaces.claude_adapter import ClaudeAdapter
from .interfaces.qwen_adapter import QwenAdapter
from .interfaces.minimax_adapter import MiniMaxAdapter
from .interfaces.base_adapter import ModelConfig

@dataclass
class GatewayConfig:
    """网关配置"""
    default_model: ModelType = ModelType.DEEPSEEK
    enable_fallback: bool = True
    enable_cache: bool = True
    cache_ttl: int = 3600

class AIGateway:
    """AI服务网关"""

    def __init__(self, config: Optional[GatewayConfig] = None):
        self.config = config or GatewayConfig()
        self._adapters: Dict[ModelType, BaseModelAdapter] = {}
        self._initialize_adapters()

    def _initialize_adapters(self):
        """初始化适配器"""
        # DeepSeek适配器
        deepseek_config = ModelConfig(
            model_id="deepseek-chat",
            api_key=self._get_api_key("deepseek"),
            base_url="https://api.deepseek.com/v1"
        )
        self._adapters[ModelType.DEEPSEEK] = DeepSeekAdapter(deepseek_config)

        # Claude适配器
        claude_config = ModelConfig(
            model_id="claude-3-sonnet",
            api_key=self._get_api_key("claude"),
            base_url="https://api.anthropic.com/v1"
        )
        self._adapters[ModelType.CLAUDE] = ClaudeAdapter(claude_config)

        # Qwen适配器
        qwen_config = ModelConfig(
            model_id="qwen-turbo",
            api_key=self._get_api_key("qwen"),
            base_url="https://dashscope.aliyuncs.com/api/v1"
        )
        self._adapters[ModelType.QWEN] = QwenAdapter(qwen_config)

        # MiniMax适配器
        minimax_config = ModelConfig(
            model_id="abab6-chat",
            api_key=self._get_api_key("minimax"),
            base_url="https://api.minimax.chat/v1"
        )
        self._adapters[ModelType.MINIMAX] = MiniMaxAdapter(minimax_config)

    def _get_api_key(self, provider: str) -> str:
        """从环境变量获取API密钥"""
        import os
        key = os.environ.get(f"{provider.upper()}_API_KEY", "dummy_key")
        return key

    @property
    def default_model(self) -> ModelType:
        return self.config.default_model

    async def generate(
        self,
        prompt: str,
        model: Optional[ModelType] = None,
        parameters: Optional[GenerationParameters] = None,
        context: Optional[Dict[str, Any]] = None,
        scene: Optional[str] = None
    ) -> AIResponse:
        """
        统一生成接口

        Args:
            prompt: CARE格式提示词
            model: 指定模型（可选，自动路由）
            parameters: 生成参数（可选，使用默认）
            context: 上下文信息（用于缓存键生成）
            scene: 场景类型（用于自动路由）

        Returns:
            AIResponse: 统一响应格式
        """
        model = model or self.default_model

        adapter = self._adapters.get(model)
        if not adapter:
            return AIResponse(
                success=False,
                content="",
                model=str(model),
                tokens_used=0,
                latency_ms=0,
                cost=0,
                error=f"Model {model} not available"
            )

        return await adapter.generate(prompt, parameters, context)

    async def batch_generate(
        self,
        prompts: List[str],
        model: Optional[ModelType] = None,
        parallel: bool = True
    ) -> List[AIResponse]:
        """批量生成接口"""
        model = model or self.default_model
        adapter = self._adapters.get(model)

        if not adapter:
            return [
                AIResponse(
                    success=False,
                    content="",
                    model=str(model),
                    tokens_used=0,
                    latency_ms=0,
                    cost=0,
                    error=f"Model {model} not available"
                )
                for _ in prompts
            ]

        if parallel:
            tasks = [adapter.generate(p) for p in prompts]
            return await asyncio.gather(*tasks)
        else:
            results = []
            for p in prompts:
                results.append(await adapter.generate(p))
            return results

    async def switch_model(self, from_model: ModelType, to_model: ModelType) -> bool:
        """运行时切换默认模型"""
        if to_model not in self._adapters:
            return False
        self.config.default_model = to_model
        return True

    async def get_model_status(self) -> List[Dict[str, Any]]:
        """获取各模型状态"""
        status = []
        for model_type, adapter in self._adapters.items():
            is_healthy = await adapter.health_check()
            status.append({
                "model": model_type.value,
                "available": is_healthy,
                "is_default": model_type == self.default_model
            })
        return status

    async def close(self):
        """关闭所有适配器"""
        for adapter in self._adapters.values():
            if hasattr(adapter, 'close'):
                await adapter.close()
```

- [ ] **Step 4: 创建配置文件**

```yaml
# ai_gateway/config/model_config.yaml

models:
  deepseek:
    model_id: deepseek-chat
    enabled: true
    cost_per_token: 0.0001
    capabilities:
      - chat
      - function_calling

  claude:
    model_id: claude-3-sonnet-20240229
    enabled: true
    cost_per_token: 0.0003
    capabilities:
      - chat
      - vision

  qwen:
    model_id: qwen-turbo
    enabled: true
    cost_per_token: 0.00005
    capabilities:
      - chat

  minimax:
    model_id: abab6-chat
    enabled: true
    cost_per_token: 0.00003
    capabilities:
      - chat
```

```yaml
# config/ai_models.yaml

# AI模型总配置
# 最后更新：2026-05-19

default_model: deepseek

model_preferences:
  # 场景-模型偏好
  outline_generation: deepseek
  content_continuation: deepseek
  dialogue_generation: qwen
  description_enhancement: qwen
  review_analysis: claude
  polish: deepseek

# 成本优化配置
cost_optimization:
  enabled: true
  monthly_budget: 1000
  alert_threshold: 0.8
```

- [ ] **Step 5: 运行测试验证通过**

Run: `python -m pytest tests/test_gateway.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add ai_gateway/gateway.py ai_gateway/config/model_config.yaml config/ai_models.yaml
git commit -m "feat(ai-gateway): 实现AI服务网关核心"
```

---

### Task 4: 实现熔断器

**Files:**
- Create: `novel-factory/ai_gateway/circuit_breaker/circuit_breaker.py`
- Create: `novel-factory/ai_gateway/circuit_breaker/fallback_manager.py`
- Create: `novel-factory/ai_gateway/config/circuit_breaker.yaml`

- [ ] **Step 1: 编写测试**

```python
# tests/test_circuit_breaker.py

import pytest
import asyncio
from ai_gateway.circuit_breaker.circuit_breaker import CircuitBreaker, CircuitState

def test_circuit_breaker_initial_state():
    """测试熔断器初始状态"""
    cb = CircuitBreaker(failure_threshold=3)
    assert cb.state == CircuitState.CLOSED

def test_circuit_breaker_opens_on_failures():
    """测试失败达到阈值时熔断器打开"""
    cb = CircuitBreaker(failure_threshold=2)

    # 模拟失败
    asyncio.run(cb.record_failure())
    assert cb.state == CircuitState.CLOSED

    asyncio.run(cb.record_failure())
    assert cb.state == CircuitState.OPEN

def test_circuit_breaker_half_open_after_timeout():
    """测试超时后半开状态"""
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)

    asyncio.run(cb.record_failure())
    assert cb.state == CircuitState.OPEN

    # 等待恢复超时
    import time
    time.sleep(0.15)

    asyncio.run(cb.record_success())  # 尝试请求
    # 在half-open状态下，如果请求成功则关闭
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/test_circuit_breaker.py -v`
Expected: FAIL with "cannot import"

- [ ] **Step 3: 实现熔断器**

```python
# ai_gateway/circuit_breaker/circuit_breaker.py

import time
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Any, Optional
import asyncio

class CircuitState(Enum):
    CLOSED = "closed"      # 正常状态
    OPEN = "open"          # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态

@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5      # 失败次数阈值
    success_threshold: int = 2      # 恢复需要的成功次数
    recovery_timeout: float = 60.0 # 恢复超时（秒）
    half_open_max_calls: int = 3   # 半开状态最大尝试次数

class CircuitBreaker:
    """熔断器"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout
        )
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0

    @property
    def state(self) -> CircuitState:
        """获取当前状态"""
        if self._state == CircuitState.OPEN:
            # 检查是否应该转换到半开
            if self._last_failure_time and \
               time.time() - self._last_failure_time >= self.config.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
        return self._state

    async def record_failure(self):
        """记录失败"""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._failure_count >= self.config.failure_threshold:
            self._state = CircuitState.OPEN

    async def record_success(self):
        """记录成功"""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.success_threshold:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
        elif self._state == CircuitState.CLOSED:
            # 成功时重置失败计数
            self._failure_count = max(0, self._failure_count - 1)

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """执行函数，带熔断保护"""
        if self.state == CircuitState.OPEN:
            raise CircuitOpenError("Circuit breaker is OPEN")

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            await self.record_success()
            return result

        except Exception as e:
            await self.record_failure()
            raise

class CircuitOpenError(Exception):
    """熔断器打开异常"""
    pass
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/test_circuit_breaker.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add ai_gateway/circuit_breaker/circuit_breaker.py ai_gateway/circuit_breaker/__init__.py ai_gateway/config/circuit_breaker.yaml
git commit -m "feat(ai-gateway): 实现熔断器"
```

---

## 实现完成检查

- [ ] 基础适配器接口已创建
- [ ] DeepSeek适配器已实现
- [ ] AI服务网关已实现
- [ ] 熔断器已实现
- [ ] 配置文件已创建
- [ ] 测试通过