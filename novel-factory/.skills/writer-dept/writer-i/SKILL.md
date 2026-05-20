# 作家I 配置参考

> **版本**：v1.0
> **日期**：2026-05-20
> **说明**：配置参考文档，详细配置见 `infra/agent_system/agents/content_writer/variants/variant_i.yaml`

---

## 快速参考

| 字段 | 值 |
|------|-----|
| **ID** | i |
| **名称** | 作家I |
| **专长** | 悬疑/推理 |
| **风格** | 冷静理性 |
| **对话比例** | 35% |
| **动作强度** | low |

---

## 核心能力

| 能力 | 说明 |
|------|------|
| 逻辑推理强 | 证据链完整 |
| 谜题设计精巧 | 公平线索 |
| 犯罪心理刻画深 | 有深度 |
| 真相揭示有力 | 情感冲击 |

---

## 适配场景

- 逻辑推理
- 谜题设计
- 犯罪心理
- 真相追寻

---

## 质量维度目标

| 维度 | 目标 |
|------|------|
| S1 剧情完整性 | high |
| S2 逻辑自洽 | very_high |
| S3 文笔风格 | medium |
| S4 情感共鸣 | medium |
| S5 节奏控制 | high |
| S6 可读性 | high |
| S7 主角魅力 | medium |
| S8 人物弧光 | medium |

---

## 使用方式

```python
from infra.agent_system.agents.content_writer.variant_loader import load_writer_variant

config = load_writer_variant("i")
```