# 作家E 配置参考

> **版本**：v1.0
> **日期**：2026-05-20
> **说明**：配置参考文档，详细配置见 `infra/agent_system/agents/content_writer/variants/variant_e.yaml`

---

## 快速参考

| 字段 | 值 |
|------|-----|
| **ID** | e |
| **名称** | 作家E |
| **专长** | 古言/文笔 |
| **风格** | 优雅古典 |
| **对话比例** | 20% |
| **动作强度** | low |

---

## 核心能力

| 能力 | 说明 |
|------|------|
| 文笔优美 | 古典韵味，有诗词典故 |
| 意境描写 | 留白多，不要说太满 |
| 古风对话 | 符合礼仪感 |
| 情感抒发 | 含蓄，不可直白 |

---

## 适配场景

- 意境描写
- 古风场景
- 诗词引用
- 情感抒发

---

## 质量维度目标

| 维度 | 目标 |
|------|------|
| S1 剧情完整性 | medium |
| S2 逻辑自洽 | high |
| S3 文笔风格 | very_high |
| S4 情感共鸣 | high |
| S5 节奏控制 | medium |
| S6 可读性 | medium |
| S7 主角魅力 | high |
| S8 人物弧光 | high |

---

## 使用方式

```python
from infra.agent_system.agents.content_writer.variant_loader import load_writer_variant

config = load_writer_variant("e")
```