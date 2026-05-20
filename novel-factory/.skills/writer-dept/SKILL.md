# 作家部门配置说明文档

> **版本**：v1.0
> **日期**：2026-05-20
> **依据**：docs/优化方案-v8.1.md Phase 3.2
> **说明**：本文档为配置说明，不再是独立Agent定义

---

## 角色池架构

作家部门采用**5核心Agent+角色池**模式中的角色池部分：

```
content_writer (核心Agent)
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    作家角色池 (A-J)                           │
├─────────────────────────────────────────────────────────────┤
│  作家A - variant_a.yaml │ 玄幻/战斗 · 热血激昂              │
│  作家B - variant_b.yaml │ 都市/情感 · 细腻真实              │
│  作家C - variant_c.yaml │ 科幻/设定 · 理性严谨              │
│  作家D - variant_d.yaml │ 悬疑/节奏 · 紧张压迫              │
│  作家E - variant_e.yaml │ 古言/文笔 · 优雅古典              │
│  作家F - variant_f.yaml │ 奇幻/魔法 · 神秘奇幻              │
│  作家G - variant_g.yaml │ 现实/职场 · 真实深刻              │
│  作家H - variant_h.yaml │ 校园/青春 · 清新青春              │
│  作家I - variant_i.yaml │ 悬疑/推理 · 冷静理性              │
│  作家J - variant_j.yaml │ 历史/战争 · 史诗厚重              │
└─────────────────────────────────────────────────────────────┘
```

---

## 配置加载机制

### 加载方式

```python
from infra.agent_system.agents.content_writer.variant_loader import load_writer_variant

# 加载单个配置
config = load_writer_variant("a")      # 单字母
config = load_writer_variant("writer_b") # 全名
config = load_writer_variant(2)        # 数字索引
```

### 配置结构

每个 `variant_*.yaml` 包含：

| 字段 | 说明 |
|------|------|
| `writer_id` | 标准化ID |
| `name` | 作家名称 |
| `specialization` | 专长领域（primary/secondary/adapted_scenes） |
| `writing_style` | 写作风格（tone/dialogue_ratio/action_intensity） |
| `sentence_preferences` | 句式偏好 |
| `system_prompt_additions` | 作家特定系统提示补充 |
| `historical_performance` | 历史表现评分 |
| `quality_targets` | S1-S8各维度质量目标 |

---

## 调度接口

### ContentWriterTools 支持 writer_id 参数

```python
from infra.agent_system.agents.content_writer import ContentWriterTools

writer = ContentWriterTools()

# 方式1：每次调用指定writer_id
result = writer.generate_chapter(
    chapter_num=1,
    context=context,
    writer_id="a"  # 使用作家A
)

# 方式2：切换默认writer
writer.switch_writer("b")  # 切换到作家B
result = writer.generate_chapter(chapter_num=2, context=context)  # 使用作家B
```

---

## 专长对照表

| 作家 | 专长类型 | 擅长场景 |
|------|---------|---------|
| 作家A | 玄幻/战斗 | 武大/宗门冲突/生死对决/升级突破 |
| 作家B | 都市/情感 | 情感纠葛/人物关系/职场博弈/家庭冲突 |
| 作家C | 科幻/设定 | 世界观构建/设定展开/科技描写/文明冲突 |
| 作家D | 悬疑/节奏 | 悬念铺设/惊悚氛围/高潮反转/节奏把控 |
| 作家E | 古言/文笔 | 意境描写/古风场景/诗词引用/情感抒发 |
| 作家F | 奇幻/魔法 | 魔法系统/异世界冒险/种族冲突/神器描写 |
| 作家G | 现实/职场 | 职场描写/社会写实/人性博弈/现实压力 |
| 作家H | 校园/青春 | 校园生活/青春回忆/友情初恋/成长烦恼 |
| 作家I | 悬疑/推理 | 逻辑推理/谜题设计/犯罪心理/真相追寻 |
| 作家J | 历史/战争 | 历史背景/战争场面/军事描写/权谋斗争 |

---

## 场景推荐

```python
from infra.agent_system.agents.content_writer.variant_loader import get_variant_for_scene

# 根据场景类型自动推荐最适合的作家
writer_id = get_variant_for_scene("战斗")   # 返回 "a"
writer_id = get_variant_for_scene("情感")   # 返回 "b"
writer_id = get_variant_for_scene("推理")   # 返回 "i"
writer_id = get_variant_for_scene("历史")   # 返回 "j"
```

---

## 历史表现（评分参考）

| 作家 | 字数均值 | 核心评分 | 一致性 |
|------|---------|---------|--------|
| 作家A | 2800 | 战斗A+/升级A/情感B+ | 95% |
| 作家B | 2600 | 情感A+/对话A/关系A | 93% |
| 作家C | 3000 | 世界A+/逻辑A+/设定A | 97% |
| 作家D | 2500 | 悬疑A+/节奏A+/钩子A | 94% |
| 作家E | 2700 | 文笔A+/意境A+/情感A | 91% |
| 作家F | 2900 | 魔法A+/世界A/冒险A | 92% |
| 作家G | 2600 | 写实A+/对话A/洞察A+ | 94% |
| 作家H | 2400 | 青春A+/情感A/共鸣A+ | 93% |
| 作家I | 2700 | 逻辑A+/谜题A+/揭示A | 95% |
| 作家J | 3000 | 历史A+/战争A+/权谋A | 96% |

---

## 关联文档

| 文档 | 说明 |
|------|------|
| `infra/agent_system/agents/content_writer/variants/` | 10个作家YAML配置 |
| `infra/agent_system/agents/content_writer/variant_loader.py` | 配置加载器 |
| `infra/agent_system/agents/content_writer/tools.py` | ContentWriterTools实现 |
| `docs/S1-S8量化标准.md` | 审核维度量化标准 |
| `workflow_state.json` | 工作流状态 |