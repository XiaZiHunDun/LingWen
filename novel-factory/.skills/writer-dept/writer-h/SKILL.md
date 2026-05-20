# 作家H 配置参考

> **版本**：v1.0
> **日期**：2026-05-20
> **说明**：配置参考文档，详细配置见 `infra/agent_system/agents/content_writer/variants/variant_h.yaml`

---

## 快速参考

| 字段 | 值 |
|------|-----|
| **ID** | h |
| **名称** | 作家H |
| **专长** | 校园/青春 |
| **风格** | 清新青春 |
| **对话比例** | 40% |
| **动作强度** | low |

---

## 核心能力

| 能力 | 说明 |
|------|------|
| 青春气息浓郁 | 有生活感 |
| 校园场景真实 | 符合当代特征 |
| 情感共鸣强 | 不狗血 |
| 成长烦恼普遍 | 有共同经历 |

---

## 适配场景

- 校园生活
- 青春回忆
- 友情/初恋
- 成长烦恼

---

## 质量维度目标

| 维度 | 目标 |
|------|------|
| S1 剧情完整性 | medium |
| S2 逻辑自洽 | high |
| S3 文笔风格 | high |
| S4 情感共鸣 | very_high |
| S5 节奏控制 | high |
| S6 可读性 | very_high |
| S7 主角魅力 | high |
| S8 人物弧光 | high |

---

## 使用方式

```python
from infra.agent_system.agents.content_writer.variant_loader import load_writer_variant

config = load_writer_variant("h")
```