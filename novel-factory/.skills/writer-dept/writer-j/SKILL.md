# 作家J 配置参考

> **版本**：v1.0
> **日期**：2026-05-20
> **说明**：配置参考文档，详细配置见 `infra/agent_system/agents/content_writer/variants/variant_j.yaml`

---

## 快速参考

| 字段 | 值 |
|------|-----|
| **ID** | j |
| **名称** | 作家J |
| **专长** | 历史/战争 |
| **风格** | 史诗厚重 |
| **对话比例** | 30% |
| **动作强度** | very_high |

---

## 核心能力

| 能力 | 说明 |
|------|------|
| 历史考据扎实 | 尊重史实 |
| 战争场面宏大 | 宏观+微观结合 |
| 权谋描写深刻 | 有深度和逻辑 |
| 史诗感强 | 细节堆叠 |

---

## 适配场景

- 历史背景
- 战争场面
- 军事描写
- 权谋斗争

---

## 质量维度目标

| 维度 | 目标 |
|------|------|
| S1 剧情完整性 | high |
| S2 逻辑自洽 | very_high |
| S3 文笔风格 | high |
| S4 情感共鸣 | medium |
| S5 节奏控制 | medium |
| S6 可读性 | medium |
| S7 主角魅力 | medium |
| S8 人物弧光 | medium |

---

## 使用方式

```python
from infra.agent_system.agents.content_writer.variant_loader import load_writer_variant

config = load_writer_variant("j")
```