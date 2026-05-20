# 审核部门配置说明

> 版本：v2.0
> 日期：2026-05-20
> 依据：docs/优化方案-v8.1.md Session 3

---

## 架构说明

审核部门采用 **auditor Agent + variants 配置**模式：

```
auditor Agent（代码层）
    │
    ├── variants/
    │   ├── variant_a.yaml  → 审核员A（S1专长）
    │   ├── variant_b.yaml  → 审核员B（S2专长）
    │   ├── ...
    │   └── variant_j.yaml  → 审核员J（全维度综合）
    │
    └── variant_loader.py   → 配置加载器
```

**核心思想**：同一套 auditor Agent 代码，通过 YAML 配置切换为不同审核员角色。

---

## 审核员配置（A-J）

| 审核员 | 专长维度 | 核心能力 | 权重倾向 |
|--------|---------|---------|---------|
| **A** | S1 | 剧情完整性 | S1=45% |
| **B** | S2 | 逻辑自洽 | S2=45% |
| **C** | S3 | 文笔风格 | S3=45% |
| **D** | S4 | 情感共鸣 | S4=45% |
| **E** | S5 | 节奏控制 | S5=45% |
| **F** | S6 | 可读性 | S6=45% |
| **G** | S7 | 主角魅力 | S7=45% |
| **H** | S8 | 人物弧光 | S8=45% |
| **I** | 伏笔 | 伏笔追踪 | S8=35% |
| **J** | 全维度 | 综合评估 | 均衡12.5% |

---

## variant YAML 配置结构

```yaml
variant_id: "A"
name: "审核员A"
specialty_dimensions: ["S1"]
secondary_dimensions: ["S5", "S8"]

# S1-S8权重（相对比较用）
s1_weight: 0.45
s2_weight: 0.10
s3_weight: 0.05
...

# 审核风格
audit_style:
  strictness: "strict"      # strict / moderate / loose
  focus: "macro"            # macro / detail
  verbosity: "detailed"     # detailed / concise
```

---

## 使用方式

### 1. 代码中切换审核员

```python
from infra.agent_system.agents.auditor import AuditorTools

auditor = AuditorTools(router)

# 方式1：直接指定审核员
report = auditor.audit_chapter(
    chapter_num=1,
    content=content,
    characters=chars,
    context={},
    reviewer_id="C"  # 使用审核员C（S3文笔专长）
)

# 方式2：设置默认审核员
auditor.set_reviewer("B")
report = auditor.audit_chapter(...)  # 自动使用B
```

### 2. 获取配置信息

```python
from infra.agent_system.agents.auditor.variant_loader import get_variant_loader

loader = get_variant_loader()

# 获取审核员C的S3权重
weight = loader.get_weight("C", "S3")  # 0.45

# 获取审核员C的完整权重配置
weights = loader.get_weights("C")
# {'S1': 0.05, 'S2': 0.05, 'S3': 0.45, ...}

# 获取审核员C的专长维度
specialties = loader.get_specialty_dimensions("C")  # ['S3']

# 获取审核员C的审核风格
style = loader.get_audit_style("C")
# {'strictness': 'moderate', 'focus': 'detail', 'verbosity': 'detailed'}
```

---

## 配置文件清单

| 文件 | 审核员 | 专长 |
|------|--------|------|
| `variant_a.yaml` | A | S1剧情完整性 |
| `variant_b.yaml` | B | S2逻辑自洽 |
| `variant_c.yaml` | C | S3文笔风格 |
| `variant_d.yaml` | D | S4情感共鸣 |
| `variant_e.yaml` | E | S5节奏控制 |
| `variant_f.yaml` | F | S6可读性 |
| `variant_g.yaml` | G | S7主角魅力 |
| `variant_h.yaml` | H | S8人物弧光 |
| `variant_i.yaml` | I | 伏笔追踪 |
| `variant_j.yaml` | J | 全维度综合 |

---

## 关联文档

| 文档 | 说明 |
|------|------|
| `infra/agent_system/agents/auditor/tools.py` | AuditorTools 实现 |
| `infra/agent_system/agents/auditor/variant_loader.py` | 变体加载器 |
| `infra/agent_system/agents/auditor/variants/*.yaml` | 审核员A-J配置 |
| `docs/S1-S8量化标准.md` | 审核维度量化标准 |