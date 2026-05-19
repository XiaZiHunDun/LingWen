# SPEC: 整合AI服务抽象层

> **版本**: v1.0
> **日期**: 2026-05-19
> **状态**: 已整合（原3个方案合并）
> **优先级**: P2
> **预计工作量**: 8-10周

---

## 1. 概述与目标

### 1.1 问题陈述

当前小说工厂的AI调用存在以下问题：

| 问题 | 说明 |
|------|------|
| 模型选择僵化 | hardcoded单一模型，无法灵活切换 |
| 无熔断降级 | 单点故障风险高，无自动恢复 |
| 成本不透明 | 无法追踪优化AI调用成本 |
| 提示词与模型耦合 | 模型变更影响提示词效果 |
| 无缓存复用 | 相同请求重复调用 |

### 1.2 解决方案

构建**整合AI服务抽象层**，统一以下原有方案：
- ~~AI服务抽象层~~（核心架构）
- ~~模型分级策略~~（路由策略）
- ~~温度参数指导~~（已合并到提示词体系）

**核心能力**：
- 统一接口：支持多Provider无缝切换
- 智能路由：根据场景自动选择最优模型
- 熔断降级：故障自动切换，保障可用性
- 成本优化：用量统计与优化建议

### 1.3 目标

| 目标 | 指标 |
|------|------|
| 模型切换时间 | < 1分钟（配置变更而非代码变更） |
| 服务可用性 | ≥ 99.9% |
| 熔断响应时间 | < 100ms |
| AI调用成本 | 优化后降低20% |
| 缓存命中率 | ≥ 30% |

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        调用方                               │
│   记忆系统    Agent系统    提示词系统    一致性检查          │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                     AI服务网关 (AIGateway)                    │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    统一接口层                           │ │
│  │  generate() / batch_generate() / switch_model()         │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │    路由策略       │  │    熔断管理器     │                │
│  │  场景路由/成本路由 │  │  延迟熔断/错误熔断 │                │
│  └──────────────────┘  └──────────────────┘                │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                    模型适配器层 (Model Adapters)              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │DeepSeek │ │ Claude  │ │  千问   │ │ Minimax │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
novel-factory/
├── ai_gateway/
│   ├── __init__.py
│   ├── gateway.py                    # AI服务网关主类
│   ├── interfaces/
│   │   ├── base_adapter.py           # 适配器基类
│   │   ├── deepseek_adapter.py
│   │   ├── claude_adapter.py
│   │   ├── qwen_adapter.py
│   │   └── minimax_adapter.py
│   ├── router/
│   │   ├── scene_router.py           # 场景路由
│   │   └── cost_optimizer.py         # 成本优化器
│   ├── circuit_breaker/
│   │   ├── circuit_breaker.py        # 熔断器
│   │   └── fallback_manager.py       # 降级管理器
│   ├── cache/
│   │   ├── cache_manager.py
│   │   └── response_cache.py
│   └── config/
│       ├── model_config.yaml          # 模型配置
│       ├── scene_mapping.yaml         # 场景-模型映射
│       └── circuit_breaker.yaml        # 熔断配置
```

---

## 3. 核心接口

### 3.1 AIGateway

```python
class AIGateway:
    """AI服务网关"""

    def generate(
        self,
        prompt: str,
        model: Optional[ModelType] = None,
        parameters: Optional[GenerationParams] = None,
        context: Optional[Dict] = None,
        scene: Optional[str] = None
    ) -> AIResponse:
        """统一生成接口"""

    def batch_generate(
        self,
        prompts: List[str],
        model: Optional[ModelType] = None
    ) -> List[AIResponse]:
        """批量生成"""

    def get_model_status(self) -> List[ModelStatus]:
        """获取各模型健康状态"""

    def get_cost_report(self, period_days: int = 30) -> CostReport:
        """生成成本报告"""
```

### 3.2 场景-模型映射

```yaml
scene_model_mapping:
  outline_generation:
    primary: [qwen, deepseek]
    secondary: [claude]
    fallback: [minimax]

  content_continuation:
    primary: [deepseek, claude]
    secondary: [qwen]
    fallback: [minimax]

  review_analysis:
    primary: [claude, deepseek]
    secondary: [qwen]

  polish:
    primary: [qwen, deepseek]
    secondary: [claude]
```

---

## 4. 熔断降级机制

### 4.1 熔断器状态

```
CLOSED → (连续失败≥阈值) → OPEN
OPEN → (超时后) → HALF_OPEN
HALF_OPEN → (连续成功≥阈值) → CLOSED
HALF_OPEN → (失败) → OPEN
```

### 4.2 降级策略

```yaml
fallback_strategy:
  primary_model: deepseek
  fallback_chain:
    - deepseek
    - qwen
    - minimax
  ultimate_fallback: cache_or_error
```

---

## 5. 归档的原始文档

| 原文档 | 整合内容 |
|--------|---------|
| `2026-05-19-ai-service-abstraction-layer-design.md` | 核心架构 |
| `2026-05-19-model-tier-strategy.md` | 模型分级路由 |