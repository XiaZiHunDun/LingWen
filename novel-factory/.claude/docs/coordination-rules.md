# 协调规则

本文档定义小说工厂各部门Agent之间的协调机制。

## 1. 垂直委派

**原则**：领导层Agent委派给部门主管，部门主管再委派给专家。对于复杂决策，不得跳过层级。

```
用户 → 主控调度 → 部门主管 → 专家Agent
```

| 层级 | 角色 | 职责 |
|------|------|------|
| 领导层 | 主控调度（灵文） | 战略决策、大方向把控 |
| 部门层 | 部门主编/主管 | 任务分配、进度跟踪、跨域协调 |
| 专家层 | 具体执行Agent | 按时按质完成分配任务 |

## 2. 横向协商

**原则**：同一层级的Agent可以相互协商，但不得在其领域之外做出约束性决策。

**允许**：
- 作家A询问作家B关于某角色的理解
- 审核员A与审核员B讨论同一章节的问题

**禁止**：
- 作家A直接修改作家B负责的章节（除非通过主编分配）
- 审核员A单方面决定修改大纲（需通过主控调度）

## 3. 冲突解决

当两个Agent意见不一致时：

| 冲突类型 | 上报对象 |
|---------|---------|
| 设计冲突（大纲/结构） | 主控调度（灵文） |
| 技术冲突（质量检查标准） | 审核部门主编 |
| 进度冲突（交付时间） | 主控调度（灵文） |

**解决流程**：
1. 当事Agent尝试协商解决
2. 无法解决时，上报共同上级
3. 上级做出裁决并记录

## 4. 变更传播

当设计变更影响多个领域时，由相应的部门主编协调传播。

**示例**：
- 卷1大纲修改 → 需通知作家部门（影响正文创作）、审核部门（重新审核）
- 角色设定变更 → 需通知相关作家、审核员、汇总部门

**传播原则**：
- 变更发起方负责通知受影响方
- 重大变更需主控调度确认
- 所有变更需记录到意见仓库

## 5. 禁止单方面跨域变更

**原则**：Agent未经明确委派，不得修改其指定目录之外的文件。

| Agent | 可修改目录 |
|-------|-----------|
| 灵感部门 | `01_灵感库/` |
| 作家部门 | `02_作家工作室/`, `03_内容仓库/04_正文/`（修改时） |
| 审核部门 | `04_审核员工作室/`, `06_意见仓库/04_正文_审核/` |
| 读者部门 | `05_模拟读者池/`, `06_意见仓库/05_读者评论/` |
| 汇总部门 | `07_汇总仓库/` |

**例外**：经主控调度明确授权的跨域修改。

## 6. 会话状态更新

每次完成重要里程碑后，Agent必须更新 `production/session-state/active.md`：

```
## [时间戳] 完成事项
- 部门：[部门名]
- 任务：[任务描述]
- 结果：[成功/失败/部分完成]
- 下一步：[待处理事项]
```

## 7. Agent调度记录

每次启动Agent后，必须记录到 `workflow_state.json` 的 `agent_tasks` 字段：

```json
"agent_tasks": {
  "ch164_fix": {
    "task_id": "a1234567890",
    "agent": "作家A",
    "status": "running",
    "chapter": "ch164",
    "dispatched_at": "2026-05-18T10:00:00"
  }
}
```

## 8. 验证闭环

Agent返回后必须使用 `TaskOutput` 验证状态，才能改变 workflow_state 中的 step_status。

```
启动Agent → 获得task_id → TaskOutput验证
                              ↓
                       status=failed → 重新启动（最多3次）
                       status=completed → 确认修复内容
                       → 才能改step_status为completed
```

## 9. 紧急情况处理

| 情况 | 处理方式 |
|------|---------|
| P0问题发现 | 立即停止当前任务，优先处理P0 |
| Agent无响应 | 等待5秒后 TaskOutput 重试，最多3次 |
| 死锁（超迭代上限） | 上报主控调度，启动人工仲裁 |

## State Ownership Registry

The state ownership registry (`docs/registry/state-ownership.yaml`) defines which agent owns each state field and file. All coordination rules reference this registry.

Key ownership rules:
- `workflow_state.json` top-level fields → `main_controller` only
- `phases.*.status` → respective department agents
- `review_queue.*` → `reviewer_dept`
- Chapter files → `writer_dept` (write), `reviewer_dept` (read)

For full registry details, see `docs/registry/state-ownership.yaml`.

## Forbidden Patterns

See `docs/registry/forbidden-patterns.yaml` for patterns that are never allowed.

## Collaborative Decision Workflow (CCGS Pattern)

> Adapted from CCGS's COLLABORATIVE-DESIGN-PRINCIPLE.md

For all major decision points, agents MUST follow this workflow:

### Step 1: Question
The agent asks clarifying questions before proposing anything.

```
❓ "Before I generate the outline, I need to confirm:
   1. What's the target chapter count for Volume 1? (recommended: 100-120)
   2. Should the climactic battle in ch060 be character-death or near-death?
   3. Is the romance subplot a slow-burn or fast-track?"
```

### Step 2: Options
The agent presents 2-4 options with pros/cons and theoretical grounding.

```
📋 Options for Volume 1 Arc:
   A) Classic 3-Act Structure
      - Pros: Familiar, reliable pacing
      - Cons: Predictable for genre-savvy readers
   B) Nested Loop (30-sec micro / 5-min meso / session macro)
      - Pros: High engagement, good for serialization
      - Cons: Complex outline management
   C) Cliffhanger-Driven (end every 3 chapters)
      - Pros: Page-turner effect, viral potential
      - Cons: Hard to sustain for 120 chapters
```

### Step 3: Decision
The user or main controller makes the final decision.

```
✅ Decision: Option B (Nested Loop) with cliffhanger endpoints at ch030, ch060, ch090, ch120
```

### Step 4: Draft
The agent shows the draft before writing files.

```
📝 Draft outline for Volume 1:
   - Volume Arc: Rising → Crisis → Cliff-climax
   - Chapter breakdown:
     * ch001-ch030: Micro-loop 1 (establish world + character)
     * ch031-ch060: Meso-loop 1 (first crisis)
     * ch061-ch090: Meso-loop 2 (rising action)
     * ch091-ch120: Macro-climax (volume finale)

   Before I write the full outline, should I proceed?
```

### Step 5: Approval
Only after explicit approval does the agent write files.

```
✅ "May I write the Volume 1 outline to 03_内容仓库/02_卷大纲/卷1_大纲_v1.0.md?"
```

## Decision Points Map

| Decision Point | Who Decides | Options Format | Approval Required |
|---------------|-------------|----------------|------------------|
| 灵感生成类型 | 用户/主控 | 2-4类型方案 | Yes |
| 大纲审核通过 | 审核部门主编 | 通过/修改/打回 | Yes |
| 卷汇总定稿 | 汇总部门主编 | 通过/修改/打回 | Yes |
| 作家修改分配 | 作家主编 | 并行方案 | No (routine) |
| 审核员轮值 | 审核部门主编 | 轮值表选择 | No (routine) |
| 情感审核专项 | 审核部门 | 启用/跳过 | Yes |
| 模式切换 (full/lean/solo) | 用户/主控 | 3个模式 | Yes |

---

*文档版本: v1.0*
*创建时间: 2026-05-18*
*适用范围: 灵文 · 工业化小说生产系统*
*Last updated: 2026-05-19*
*Collaborative workflow added per CCGS reference*