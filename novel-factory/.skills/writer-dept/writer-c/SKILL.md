# 作家C 配置参考

> **版本**：v1.0
> **日期**：2026-05-20
> **说明**：配置参考文档，详细配置见 `infra/agent_system/agents/content_writer/variants/variant_c.yaml`

---

## 快速参考

| 字段 | 值 |
|------|-----|
| **ID** | c |
| **名称** | 作家C |
| **专长** | 科幻/设定 |
| **风格** | 理性严谨 |
| **对话比例** | 30% |
| **动作强度** | medium |

---

## 核心能力

| 能力 | 说明 |
|------|------|
| 世界观构建 | 自洽完整，细节丰富 |
| 设定展开 | 信息量大但节奏可控 |
| 科技描写 | 有逻辑基础或合理解释 |
| 文明冲突 | 深层矛盾 |

---

## 适配场景

- 世界观构建
- 设定展开
- 科技描写
- 文明冲突

---

## 质量维度目标

| 维度 | 目标 |
|------|------|
| S1 剧情完整性 | high |
| S2 逻辑自洽 | very_high |
| S3 文笔风格 | medium |
| S4 情感共鸣 | medium |
| S5 节奏控制 | medium |
| S6 可读性 | medium |
| S7 主角魅力 | medium |
| S8 人物弧光 | medium |

---

## 使用方式

```python
from infra.agent_system.agents.content_writer.variant_loader import load_writer_variant

config = load_writer_variant("c")
```