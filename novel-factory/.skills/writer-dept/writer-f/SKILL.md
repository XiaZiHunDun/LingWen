# 作家F 配置参考

> **版本**：v1.0
> **日期**：2026-05-20
> **说明**：配置参考文档，详细配置见 `infra/agent_system/agents/content_writer/variants/variant_f.yaml`

---

## 快速参考

| 字段 | 值 |
|------|-----|
| **ID** | f |
| **名称** | 作家F |
| **专长** | 奇幻/魔法 |
| **风格** | 神秘奇幻 |
| **对话比例** | 30% |
| **动作强度** | high |

---

## 核心能力

| 能力 | 说明 |
|------|------|
| 魔法系统设计 | 自洽完整，有独特规则和代价 |
| 异世界设定 | 新鲜感强，有创意 |
| 视觉效果 | 魔法仪式感强 |
| 种族文化 | 独特文化设定 |

---

## 适配场景

- 魔法系统
- 异世界冒险
- 种族冲突
- 神器/魔法描写

---

## 质量维度目标

| 维度 | 目标 |
|------|------|
| S1 剧情完整性 | high |
| S2 逻辑自洽 | high |
| S3 文笔风格 | high |
| S4 情感共鸣 | medium |
| S5 节奏控制 | high |
| S6 可读性 | medium |
| S7 主角魅力 | medium |
| S8 人物弧光 | medium |

---

## 使用方式

```python
from infra.agent_system.agents.content_writer.variant_loader import load_writer_variant

config = load_writer_variant("f")
```