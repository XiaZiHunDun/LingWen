# 作家B 配置参考

> **版本**：v1.0
> **日期**：2026-05-20
> **说明**：配置参考文档，详细配置见 `infra/agent_system/agents/content_writer/variants/variant_b.yaml`

---

## 快速参考

| 字段 | 值 |
|------|-----|
| **ID** | b |
| **名称** | 作家B |
| **专长** | 都市/情感 |
| **风格** | 细腻真实 |
| **对话比例** | 40% |
| **动作强度** | low |

---

## 核心能力

| 能力 | 说明 |
|------|------|
| 情感描写 | 细腻真实，不矫揉造作 |
| 人物关系 | 关系变化有铺垫，逻辑清晰 |
| 对话自然 | 符合角色身份和性格 |
| 场景接地气 | 家庭/职场场景真实 |

---

## 适配场景

- 情感纠葛
- 人物关系
- 职场博弈
- 家庭冲突

---

## 质量维度目标

| 维度 | 目标 |
|------|------|
| S1 剧情完整性 | medium |
| S2 逻辑自洽 | high |
| S3 文笔风格 | high |
| S4 情感共鸣 | very_high |
| S5 节奏控制 | medium |
| S6 可读性 | high |
| S7 主角魅力 | high |
| S8 人物弧光 | high |

---

## 使用方式

```python
from infra.agent_system.agents.content_writer.variant_loader import load_writer_variant

config = load_writer_variant("b")
```