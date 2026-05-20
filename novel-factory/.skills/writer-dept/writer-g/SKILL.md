# 作家G 配置参考

> **版本**：v1.0
> **日期**：2026-05-20
> **说明**：配置参考文档，详细配置见 `infra/agent_system/agents/content_writer/variants/variant_g.yaml`

---

## 快速参考

| 字段 | 值 |
|------|-----|
| **ID** | g |
| **名称** | 作家G |
| **专长** | 现实/职场 |
| **风格** | 真实深刻 |
| **对话比例** | 45% |
| **动作强度** | low |

---

## 核心能力

| 能力 | 说明 |
|------|------|
| 职场描写真实 | 有代入感 |
| 人性挖掘深刻 | 非简单黑白 |
| 社会写实感强 | 现实压力 |
| 潜台词丰富 | 对话有弦外之音 |

---

## 适配场景

- 职场描写
- 社会写实
- 人性博弈
- 现实压力

---

## 质量维度目标

| 维度 | 目标 |
|------|------|
| S1 剧情完整性 | high |
| S2 逻辑自洽 | very_high |
| S3 文笔风格 | high |
| S4 情感共鸣 | high |
| S5 节奏控制 | medium |
| S6 可读性 | high |
| S7 主角魅力 | medium |
| S8 人物弧光 | high |

---

## 使用方式

```python
from infra.agent_system.agents.content_writer.variant_loader import load_writer_variant

config = load_writer_variant("g")
```