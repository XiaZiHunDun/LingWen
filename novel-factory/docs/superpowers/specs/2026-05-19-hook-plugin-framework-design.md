# Hook 插件框架设计文档

> 日期：2026-05-19
> 方案：方向7（NovelScribe Hook 风格）
> 状态：已批准，等待实施

---

## 一、背景与目标

### 1.1 现状问题

当前小说工厂的工作流依赖：
- `workflow_state.json` 配置文件驱动工作流状态机
- 脚本化：`run_init.sh`、`run_verify.sh` 等脚本执行自动化
- **缺乏统一的事件机制**：每个脚本都是硬编码逻辑，流程变更需要改代码

### 1.2 优化目标

构建一个 Hook 插件框架：
- **事件驱动**：监听工作流/写作/审核等事件，触发自动化动作
- **YAML 配置**：通过 hooks.yaml 声明式配置，无需改代码
- **安全限制**：超时、重试、required/optional 语义
- **可扩展**：支持自定义 Hook 扩展功能

---

## 二、技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| 配置格式 | YAML | 声明式、人类可读、易编辑 |
| 事件系统 | Python（观察者模式） | 实现简单、与现有代码集成 |
| 安全限制 | 内置 | 超时/重试/required/optional |
| 部署环境 | Python + Docker | 与现有环境一致 |

---

## 三、整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Hook 事件系统                                │
│                                                              │
│  事件源：                                                      │
│    - 工作流事件（STEP_COMPLETED / PHASE_CHANGED）             │
│    - 写作事件（CHAPTER_WRITTEN / CHAPTER_REVISED）             │
│    - 审核事件（REVIEW_COMPLETED / REVIEW_FAILED）              │
│    - 外部事件（MANUAL_TRIGGER）                                │
│                                                              │
│  Hook 处理器：                                                  │
│    - 自动化触发（如：一键质量门禁）                             │
│    - 通知提醒（如：审核完成后通知作家）                          │
│    - 数据同步（如：状态变更时更新多处）                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 四、Hook 配置格式

### 4.1 YAML 配置示例

```yaml
# novel-factory/hooks.yaml

hooks:
  # 工作流事件
  - name: "自动质量门禁"
    trigger:
      event: "CHAPTER_WRITTEN"
      conditions:
        - "chapter_status == 'draft_completed'"
    actions:
      - type: "run_checker"
        checker: "auto_consistency_checker"
        params:
          chapter_range: "current"
      - type: "run_checker"
        checker: "quality_gate"
        params:
          threshold: "Bronze"
    required: true
    timeout: 60

  - name: "审核完成后通知作家"
    trigger:
      event: "REVIEW_COMPLETED"
      conditions:
        - "review_result in ['PASS', 'NEED_REVISION']"
    actions:
      - type: "notify"
        channel: "writer_channel"
        template: "review_complete"
    required: false

  - name: "阶段大纲完成后更新进度"
    trigger:
      event: "STEP_COMPLETED"
      conditions:
        - "step in ['STEP_10', 'STEP_11', 'STEP_12', 'STEP_13']"
    actions:
      - type: "update_state"
        target: "workflow_state.json"
        field: "current_step"
      - type: "notify"
        channel: "controller_channel"
        template: "stage_completed"
    required: false

  - name: "卡文超时自动触发突破"
    trigger:
      event: "WRITER_IDLE"
      conditions:
        - "idle_time > 300"  # 5分钟
        - "chapter_status == 'in_progress'"
    actions:
      - type: "trigger_module"
        module: "writer_block_breakthrough"
    required: false

  - name: "章节完成自动更新索引"
    trigger:
      event: "CHAPTER_FINALIZED"
    actions:
      - type: "run_script"
        script: "update_index.py"
        params:
          scope: "current_chapter"
    required: false
```

### 4.2 内置安全限制

```yaml
security:
  max_execution_time: 60  # 秒
  max_retries: 3
  required_hooks_must_pass: true  # required=true 的 Hook 失败则阻止流程
  optional_hooks_can_fail: true     # required=false 的 Hook 失败不阻止流程
  sensitive_actions_require_approval:
    - "delete_chapter"
    - "modify_workflow_state"
    - "approve_publication"
```

---

## 五、触发事件类型

```yaml
trigger_events:
  # 工作流事件
  - "PHASE_CHANGED"           # 阶段变更
  - "STEP_COMPLETED"          # 步骤完成
  - "STEP_FAILED"              # 步骤失败

  # 写作事件
  - "CHAPTER_WRITTEN"         # 章节写完
  - "CHAPTER_REVISED"          # 章节修改
  - "CHAPTER_FINALIZED"       # 章节定稿
  - "WRITER_IDLE"             # 作家卡住（超时）

  # 审核事件
  - "REVIEW_STARTED"          # 审核开始
  - "REVIEW_COMPLETED"        # 审核完成
  - "REVIEW_FAILED"           # 审核失败

  # 灵感事件
  - "INSPIRATION_GENERATED"    # 灵感生成
  - "OUTLINE_APPROVED"        # 大纲通过

  # 汇总事件
  - "STAGE_SUMMARIZED"        # 阶段汇总完成
  - "VOLUME_SUMMARIZED"       # 卷汇总完成
  - "FINAL_SUMMARY_APPROVED"  # 全文终审通过

  # 外部事件
  - "MANUAL_TRIGGER"          # 手动触发
```

---

## 六、动作类型

```yaml
action_types:
  # 检查类
  - type: "run_checker"
    description: "运行检查器（如一致性检查、质量门禁）"
    params:
      - checker: "检查器名称"
      - chapter_range: "检查范围"

  # 通知类
  - type: "notify"
    description: "发送通知"
    params:
      - channel: "通知渠道（writer/reviewer/controller）"
      - template: "通知模板"

  # 状态更新类
  - type: "update_state"
    description: "更新状态文件"
    params:
      - target: "目标文件（workflow_state.json）"
      - field: "字段路径"
      - value: "新值或表达式"

  # 脚本类
  - type: "run_script"
    description: "运行脚本"
    params:
      - script: "脚本路径"
      - params: "脚本参数"

  # 模块触发类
  - type: "trigger_module"
    description: "触发其他模块（如卡文突破）"
    params:
      - module: "模块名称"

  # 审批类
  - type: "request_approval"
    description: "请求审批"
    params:
      - approver: "审批人角色"
      - reason: "审批原因"
```

---

## 七、与现有系统集成

### 7.1 与 workflow_state.json 的关系

```
现有：workflow_state.json 硬编码驱动工作流
新增：Hook 事件系统 + hooks.yaml 配置

关系：
  - workflow_state.json 仍然是状态机核心
  - Hook 系统监听状态变更事件，触发自动化动作
  - Hook 可以读写 workflow_state.json（如更新 current_step）
```

### 7.2 与质量门禁系统的关系

```
CHAPTER_WRITTEN 事件 → Hook 触发 auto_consistency_checker + quality_gate
                       ↓
                  检查结果写入 workflow_state.json
                  ↓
                  如未达标，阻止进入下一环节
```

### 7.3 与卡文突破系统的关系

```
WRITER_IDLE 事件（>5分钟）→ Hook 触发 writer_block_breakthrough
                            ↓
                       推送卡文突破建议给作家
```

### 7.4 与作家工作室的关系

```
作家写章节 → CHAPTER_WRITTEN 事件 → Hook 自动触发质量门禁检查
                                            ↓
                                       检查结果通知作家
```

---

## 八、存储结构

```
novel-factory/
├── hooks.yaml              # Hook 配置文件
├── hooks/
│   ├── __init__.py
│   ├── event_bus.py        # 事件总线
│   ├── hook_engine.py      # Hook 引擎核心
│   ├── actions/            # 动作类型实现
│   │   ├── __init__.py
│   │   ├── run_checker.py
│   │   ├── notify.py
│   │   ├── update_state.py
│   │   ├── run_script.py
│   │   ├── trigger_module.py
│   │   └── request_approval.py
│   └── templates/           # 通知模板
│       ├── review_complete.yaml
│       └── stage_completed.yaml
└── ...
```

---

## 九、实施步骤

### 阶段1（1-2周）：Hook 引擎核心

1. 定义 Hook 配置格式（YAML）
2. 实现 Hook 事件系统（事件监听 + 条件判断）
3. 实现基本动作类型（run_checker、notify、update_state）
4. 验证：配置一个 Hook，验证触发和执行

### 阶段2（2-3周）：内置 Hook 实现

5. 实现"自动质量门禁"Hook（CHAPTER_WRITTEN → quality_gate）
6. 实现"审核完成通知作家"Hook（REVIEW_COMPLETED → notify）
7. 实现"阶段完成更新进度"Hook（STEP_COMPLETED → update_state）
8. 实现"卡文超时触发突破"Hook（WRITER_IDLE → trigger_module）

### 阶段3（1-2周）：安全与集成

9. 实现安全限制（超时、重试、required/optional）
10. 与 workflow_state.json 深度集成
11. 与作家工作室界面集成（显示 Hook 触发状态）
12. 验证：完整流程测试

---

## 十、验收标准

| 阶段 | 验收条件 |
|------|---------|
| 阶段1 | 配置一个 Hook，能正确触发和执行 |
| 阶段2 | 5 个内置 Hook 均能正常工作 |
| 阶段3 | required Hook 失败时正确阻止流程，optional Hook 失败不阻止 |

---

## 十一、关键设计决策

| 决策 | 说明 |
|------|------|
| YAML 配置 | 声明式配置，无需改代码即可修改流程 |
| 事件驱动 | Hook 系统监听事件，不主动轮询 |
| required/optional 语义 | required Hook 失败阻止流程，optional 不阻止 |
| 超时限制 | 每个 Hook 有最大执行时间，防止挂起 |
| 安全限制 | 敏感操作（如删除章节）需要审批 |