# 灵文 · 提示词工程白皮书 v1.0

> 日期：2026-06-03
> 状态：待批准
> 配套：Doc 1 (理论框架) / Doc 3 (支线) / Doc 4 (GoT)
> 输入：用户 29 条想法 #2, #5, #8, #17, #20, #21, #26

---

## 一、为什么需要提示词工程

当前痛点：

1. **Prompt 散落**：5 核心 Agent × 10+ 角色池 = 50+ 不同 prompt，没人系统管
2. **上下文爆炸**：写一章时塞了 5 万字前文，但只用得上 200 字
3. **效果难测**：换一个 prompt 措辞，效果差异巨大，但没有 A/B 流程
4. **新人难上手**：写新 Agent 的 prompt 不知道"该写什么字段"

**目标**：把 prompt 从"代码里的字符串"提升到"一等公民资产"。

## 二、PromptContext 统一模型

### 2.1 核心理念

**每个 Agent 调用前，先声明"我需要什么"，再由 ContextBuilder 拼装。**

```python
@dataclass
class PromptContext:
    """Prompt 上下文声明 (声明式)"""
    scenario: str                       # "chapter_writing" / "outline_review" / ...
    agent_role: str                     # "writer_a" / "reviewer_c"
    inputs: list[ContextItem]           # 我需要什么
    output_schema: type[BaseModel]      # 我输出什么
    temperature: float = 0.7
    max_tokens: int = 4096
    budget_tokens: int = 16000          # 输入预算

@dataclass
class ContextItem:
    key: str                            # "world_snapshot" / "prev_chapter_summary" / ...
    source: str                         # "snapshot.ch0050" / "key_points.lin_chen" / ...
    required: bool = True
    token_estimate: int = 0             # 自动估算
    transform: Optional[str] = None     # "summary_500" / "diff_only" / "raw"
```

### 2.2 ContextBuilder 流程

```
[Agent declares PromptContext]
        ↓
[ContextBuilder reads sources]
        ↓
[Token budget allocation: 大块先按优先级,小块按需]
        ↓
[Auto-summarize if overflow]
        ↓
[Render to system_prompt + user_prompt]
        ↓
[Call LLM]
        ↓
[Validate output_schema]
```

## 三、场景化模板库

### 3.1 已识别 12 个核心场景

| 场景 | Agent | 输入 | 输出 | 频率 |
|------|-------|------|------|------|
| chapter_writing | content_writer | snapshot+outline+constrain | 章节正文 | 每章 |
| chapter_outline | content_writer | snapshot+key_points | 章节大纲 | 每章 |
| outline_review | auditor | outline+constraints | pass/fail+reasons | 批次前 |
| chapter_review | auditor | chapter+snapshot | S1-S8 评分 | 每章 |
| worldview_check | auditor | snapshot+rules | 矛盾列表 | 抽查 |
| character_consistency | auditor | snapshot+profile | 一致性问题 | 抽查 |
| hook_extraction | polisher | chapter | 钩子列表 | 每章 |
| ai_trace_removal | polisher | chapter | 改写后章节 | 每章 |
| foreshadow_scan | auditor | snapshot+ripple | 回收率 | 批后 |
| emotional_pacing | auditor | mental_lines | 情感曲线 | 批后 |
| ripple_audit | auditor | ripple list | 崩塌风险 | 实时 |
| subplot_suggest | outline_master | main_plot+subplots | 支线建议 | 5 章 1 次 |

### 3.2 模板结构 (统一格式)

```yaml
scenario: chapter_writing
version: 1.2  # 模板版本,效果回滚用
agent_role: writer_a

system_prompt: |
  你是作家 A，擅长 [燃向战斗 / 升级流节奏]。
  当前小说：[novel_name]
  题材：[genre]
  主角：[main_char]

  你的任务: 写第 {ch} 章, 遵循以下约束:
  {constraints_block}

  写作要求:
  {requirements_block}

user_prompt: |
  ## 当前世界快照 (v{version})
  {world_snapshot}

  ## 本章大纲
  {chapter_outline}

  ## 上一章总结
  {prev_chapter_summary}

  ## 上一章对当前章的限制
  {prev_constraints}

  ## 主角当前状态
  {protagonist_state}

  ## 输出
  请写第 {ch} 章, 3500-4500 字, 严格遵循大纲, 必须包含:
  - [ ] 至少 1 个爽点 (升级/打脸/揭秘)
  - [ ] 至少 1 个钩子 (章末悬念)
  - [ ] 推进至少 1 条 Ripple

constraints_block: |
  - 物理线/心理线比例: 7:3 (玄幻)
  - 对话占比: 35-40%
  - 主角性格: 隐忍/机智 (避免: 暴怒/幼稚)
  - 已知 {X} 禁词
  - 不能破坏已确立的 {Y} 设定

requirements_block: |
  - 字数: 3500-4500
  - 视角: 第三人称限知
  - 风格: 网文爽感 + 文学质感
  - 节奏: 4 段式 (起/承/转/合)

output_schema: ChapterContent  # Pydantic 模型
```

### 3.3 模板版本化

- 每个场景模板独立版本号
- 改 prompt 词必须升 minor
- 改 prompt 结构必须升 major
- 效果回滚 = 切到旧 version

```bash
prompts/
├── chapter_writing/
│   ├── v1.0.yaml
│   ├── v1.1.yaml  # 微调措辞
│   └── v1.2.yaml  # 当前在用
├── chapter_outline/
│   └── ...
```

## 四、StepContract 步骤契约

### 4.1 理念

**22 步工作流中,每步必须明确: 输入是什么 / 输出是什么 / token 预算多少。**

```python
@dataclass
class StepContract:
    step: str                    # "STEP_12"
    name: str                    # "批量写作"
    inputs: list[ContextItem]    # 必填
    outputs: type[BaseModel]     # 必填
    preconditions: list[str]     # 状态前置条件
    postconditions: list[str]    # 状态后置条件
    budget_tokens: int           # 输入预算
    max_latency_s: int           # 超时
    parallel: bool = False       # 是否可并行
    can_skip: bool = False       # 是否可跳过
```

### 4.2 22 步的 StepContract 草案

| Step | 输入 | 输出 | 预算 | 关键约束 |
|------|------|------|------|---------|
| STEP_01 核心冲动 | 灵感库 | CoreImpulse | 8K | 必填 5 字段 |
| STEP_02 类型 | CoreImpulse | GenreDecision | 8K | - |
| STEP_03 梗概 | CoreImpulse+Genre | Synopsis | 16K | - |
| STEP_04 驱动链 | Synopsis | DriveChain | 16K | - |
| STEP_05 人物 | Synopsis+Drive | CharacterCards | 16K | ≤10 主角 |
| STEP_06 世界观 | 全部前置 | Worldview | 32K | 关键点 ≤100 |
| STEP_07 结构 | 全部前置 | Structure | 32K | 3 卷架构 |
| STEP_08 锁定门 | Structure | LockCheck | 8K | 必须 P0=0 |
| STEP_09 情节骨架 | Structure | PlotSkeleton | 16K | - |
| STEP_10 核心样章 | PlotSkeleton | SampleChapter | 16K | 1-3 章 |
| STEP_11 目标读者 | SampleChapter | ReaderFeedback | 16K | - |
| STEP_12 批量写作 | Snapshot+Outline | ChapterContent[] | 64K/章 | 3500-4500 字 |
| STEP_13 批次完成 | ChapterContent[] | BatchReport | 8K | - |
| STEP_14 Block | BatchReport | IssueList | 16K | - |
| STEP_15 Polish | IssueList+Chapter | PolishedChapter | 32K/章 | - |
| STEP_16 分配审核员 | PolishedChapter | ReviewerAssign | 8K | - |
| STEP_17 S1-S8 | Chapter | QualityReport | 16K/章 | - |
| STEP_18 审核判定 | QualityReport | Judgment | 8K | P0=0 通过 |
| STEP_19 汇总整理 | Judgment[] | SummaryDoc | 32K | - |
| STEP_20 卷/阶段定稿 | SummaryDoc | FinalVersion | 32K | - |
| STEP_21 发布归档 | FinalVersion | PublishArtifact | 8K | - |

### 4.3 预算执行

- 实际 token > 预算 → 触发 AutoSummarizer
- AutoSummarizer 优先级: 砍时间序列中间段 > 砍非关键角色细节 > 砍场景描述
- 关键事件/对话/决定 永不砍

## 五、上下文分配表

### 5.1 chapter_writing 场景的输入清单

| 字段 | 必填 | 来源 | 估算 token | 备注 |
|------|------|------|----------|------|
| world_snapshot | 是 | snapshot | 800 | Doc 1 模型 |
| chapter_outline | 是 | outline | 500 | |
| prev_chapter_summary | 是 | 上章输出 | 600 | 上一章自动产出 |
| prev_constraints | 是 | 上章审计 | 400 | 显式"下一章必须..." |
| protagonist_state | 是 | mental_line | 300 | |
| active_ripples | 是 | ripple list | 400 | |
| key_points_relevant | 是 | graph query | 600 | 与本章相关 ≤30 |
| style_guide | 否 | asset | 200 | |
| writer_role_config | 是 | role | 200 | |
| **小计** | | | **~4000** | |
| **冗余 30%** | | | **~5200** | |
| **总预算** | | | **8000** | |

**不传**：前 5 章原文 (只传 summary), 不相关配角细节, 不相关伏笔

### 5.2 上下文来源标签

每个 ContextItem 有 source 标签，便于审计和回放：
- `snapshot.ch0050` - 来自第 50 章的 snapshot
- `outline.batch_001` - 来自第 1 批大纲
- `review.judgment_001` - 来自第 1 次审核
- `asset.style_xuanhuan` - 来自素材库

**审计日志** = 每个 LLM 调用的所有 ContextItem 列表，便于：
- 回放 (重跑同 context, 比对输出)
- 优化 (发现某些 item 永远没被 LLM 用到 → 砍)
- 解释 (LLM 输出的某句话, 来自哪个 context)

## 六、A/B 测试与提示词工程

### 6.1 测出"比较好的 prompt"

**流程**：
1. 准备 3-5 个 prompt 变体 (措辞/结构/示例 不同)
2. 准备 10 个统一测试输入 (不同章节, 不同难度)
3. 跑 50 次生成 (10 输入 × 5 变体)
4. 评估 (自动评分 + 人工抽检 20%)
5. 选最优 → 升 minor 版本
6. 入模板库

### 6.2 自动评分维度

| 维度 | 评分器 | 阈值 |
|------|--------|------|
| 字数合规 | 字数检查 | 95% 达标 |
| 大纲符合度 | 大纲对比 | 80% 关键点命中 |
| 爽点密度 | pacing_checker | ≥1/章 |
| 钩子存在 | hook_extraction | 100% |
| 一致性 | worldview_check | P0=0 |
| 风格契合 | style_matcher | >0.7 |

### 6.3 蒸馏头部网文 (用户 #4)

拿《吞噬星空》前 50 章做蒸馏：

1. **结构蒸馏**：每章起承转合的文本量比例
2. **节奏蒸馏**：爽点间隔的统计分布 (N 章 1 爽点)
3. **对话蒸馏**：对话/描写/心理的比例
4. **钩子蒸馏**：章末钩子的常见模板 (50 类)
5. **冲突蒸馏**：冲突升级的常见模式 (人→人→势→命)

输出物：`assets/genre_knowledge/xuanhuan_burning.yaml`，喂给 writer_role_config。

## 七、LLM 定位重塑 (用户 #26)

**用户原话**：模拟人来写小说（比如我），然后 LLM 相当于缓存，挤牙膏。

**重新定位**：

| 角色 | 旧定位 | 新定位 |
|------|--------|--------|
| 用户 | 主控+决策 | **编辑/导演**：定大纲, 把方向, 不写正文 |
| LLM | 主角写手 | **加速器**：填充大纲, 提供 3 选 1, 人类选 |
| 检测器 | 质量门 | **校对员**：标红问题, 给修改建议 |

**操作变化**：
- LLM 不再"自由发挥" → 必须严格按大纲
- LLM 输出 3 个候选 → 用户/Agent 选 1
- 关键决策(支线启动/角色死亡) 永远人类拍板

**对应实现**：
- `MultiStyleDrafter` 已存在, 升级为"3 选 1"模式
- 加 `HumanDecisionQueue` (类似 inbox, 排序决策点)

## 八、与现有模块映射

| 现有 | 升级方向 |
|------|---------|
| `infra/agent_system/agents/*/prompts/` | 迁到 `prompts/{scenario}/v{N}.yaml` |
| 各 agent 的 `system_prompt` 字面量 | 改为 `PromptContext` 声明 |
| `infra/ai_service/router.py` | 接收 `PromptContext`, 调 ContextBuilder |
| `lingwen.py` 22 步 | 改为 StepContract 声明 |
| `infra/quality/llm/scorers/` | A/B 评估用 |

## 九、实施路径

### Phase 0 (本文) ✅
### Phase 1: 基础 (2 周)
- 实现 `PromptContext` + `ContextBuilder` + `StepContract`
- 把 5 核心 Agent 的 prompt 迁到模板库
- 把 22 步改造为 StepContract 驱动

### Phase 2: A/B 流程 (2 周)
- 实现 prompt 变体生成器
- 实现自动评估 pipeline
- 跑 50 章回归, 选最优 prompt

### Phase 3: 素材蒸馏 (2 周)
- 拿 5 本头部网文, 蒸馏 genre_knowledge
- 入库 style_guide, 喂给 writer_role

### Phase 4: 用户角色重塑 (1 周)
- 实现 HumanDecisionQueue
- 实现 MultiStyleDrafter 3 选 1 模式
- 编辑指南 (用户只编辑不写)

## 十、风险与缓解

| 风险 | 缓解 |
|------|------|
| 模板爆炸 | 强制合并相似场景,12 个上限 |
| A/B 测成本 | 用小模型 (Haiku 4.5) 跑初筛, 大模型精评 |
| 蒸馏质量 | 选头部 5 本, 人工审核后再入库 |
| 用户决策疲劳 | 决策去重, 相似决策合并 |
| 模板锁定效应 | 每版本保留 1 个月的"旧版回切"能力 |

## 十一、与其他文档关系

- **Doc 1 理论框架**：StepContract 的输入字段直接对应 Snapshot 子结构
- **Doc 3 支线模型**：chapter_writing 必传 active_ripples
- **Doc 4 GoT 适配**：StepContract 是 GoT 节点的元数据
