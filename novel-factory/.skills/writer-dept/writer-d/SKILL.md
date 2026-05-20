# 作家D 配置参考

> **版本**：v1.0
> **日期**：2026-05-20
> **说明**：配置参考文档，详细配置见 `infra/agent_system/agents/content_writer/variants/variant_d.yaml`

---

## 快速参考

| 字段 | 值 |
|------|-----|
| **ID** | d |
| **名称** | 作家D |
| **专长** | 悬疑/节奏 |
| **风格** | 紧张压迫 |
| **对话比例** | 25% |
| **动作强度** | medium |

---

## 核心能力

| 能力 | 说明 |
|------|------|
| 悬念铺设 | 信息释放节奏控制 |
| 惊悚氛围 | 环境/感官描写 |
| 高潮反转 | 有逻辑铺垫，不可突兀 |
| 节奏把控 | 一张一弛，张弛有度 |

---

## 适配场景

- 悬念铺设
- 惊悚氛围
- 高潮反转
- 节奏把控

---

## 质量维度目标

| 维度 | 目标 |
|------|------|
| S1 剧情完整性 | high |
| S2 逻辑自洽 | high |
| S3 文笔风格 | medium |
| S4 情感共鸣 | medium |
| S5 节奏控制 | very_high |
| S6 可读性 | high |
| S7 主角魅力 | medium |
| S8 人物弧光 | medium |

---

## 使用方式

```python
from infra.agent_system.agents.content_writer.variant_loader import load_writer_variant

config = load_writer_variant("d")
```