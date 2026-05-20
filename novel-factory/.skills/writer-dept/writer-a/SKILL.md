# 作家A 配置参考

> **版本**：v1.0
> **日期**：2026-05-20
> **说明**：配置参考文档，详细配置见 `infra/agent_system/agents/content_writer/variants/variant_a.yaml`

---

## 快速参考

| 字段 | 值 |
|------|-----|
| **ID** | a |
| **名称** | 作家A |
| **专长** | 玄幻/战斗 |
| **风格** | 热血激昂 |
| **对话比例** | 25% |
| **动作强度** | very_high |

---

## 核心能力

| 能力 | 说明 |
|------|------|
| 战斗场面描写 | 热血激昂、画面感强、法术对轰 |
| 升级爽感营造 | 境界突破、实力碾压、成就感 |
| 热血台词 | 燃系对话、战意激发 |
| 高能情节设计 | 越阶战斗、绝境逆转 |

---

## 适配场景

- 武大/宗门冲突
- 生死对决
- 境界突破
- 越阶战斗

---

## 质量维度目标

| 维度 | 目标 |
|------|------|
| S1 剧情完整性 | medium |
| S2 逻辑自洽 | high |
| S3 文笔风格 | high |
| S4 情感共鸣 | medium |
| S5 节奏控制 | very_high |
| S6 可读性 | high |
| S7 主角魅力 | high |
| S8 人物弧光 | medium |

---

## 使用方式

```python
from infra.agent_system.agents.content_writer.variant_loader import load_writer_variant

config = load_writer_variant("a")
```