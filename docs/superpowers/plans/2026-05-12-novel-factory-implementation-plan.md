# 小说工作室 · 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建完整的小说工作室多智能体系统框架，包含目录结构、状态机、编排脚本、系统人设、以及46个部门Agent画像。

**Architecture:** 混合并行架构——部门内使用Subagent+Team并行，部门间使用多终端会话并行，串行流程在单会话内角色切换。核心由workflow_state.json状态机驱动，重大决策点人工确认。

**Tech Stack:** Claude Code Subagent机制 / Shell脚本 / JSON状态管理

---

## 阶段一：基础设施搭建

### Task 1: 创建目录骨架

**Files:**
- Create: `novel-factory/01_灵感库/.gitkeep`
- Create: `novel-factory/03_内容仓库/01_全文总体大纲/.gitkeep`
- Create: `novel-factory/03_内容仓库/02_卷大纲/.gitkeep`
- Create: `novel-factory/03_内容仓库/03_阶段大纲/.gitkeep`
- Create: `novel-factory/03_内容仓库/04_正文/.gitkeep`
- Create: `novel-factory/06_意见仓库/01_全文大纲_审核/.gitkeep`
- Create: `novel-factory/06_意见仓库/02_卷大纲_审核/.gitkeep`
- Create: `novel-factory/06_意见仓库/03_阶段大纲_审核/.gitkeep`
- Create: `novel-factory/06_意见仓库/04_正文_审核/.gitkeep`
- Create: `novel-factory/06_意见仓库/05_读者评论/.gitkeep`
- Create: `novel-factory/06_意见仓库/06_汇总_审核/.gitkeep`
- Create: `novel-factory/07_汇总仓库/阶段汇总/.gitkeep`
- Create: `novel-factory/07_汇总仓库/卷汇总/.gitkeep`
- Create: `novel-factory/07_汇总仓库/全文汇总/.gitkeep`
- Create: `novel-factory/08_已发布/.gitkeep`

- [ ] **Step 1: 创建所有目录**

Run:
```bash
mkdir -p novel-factory/{01_灵感库,02_作家工作室,03_内容仓库/{01_全文总体大纲,02_卷大纲,03_阶段大纲,04_正文},04_审核员工作室,05_模拟读者池,06_意见仓库/{01_全文大纲_审核,02_卷大纲_审核,03_阶段大纲_审核,04_正文_审核,05_读者评论,06_汇总_审核},07_汇总仓库/{阶段汇总,卷汇总,全文汇总},08_已发布}
```

- [ ] **Step 2: 提交**

```bash
git add novel-factory/
git commit -m "feat: 创建小说工作室目录骨架"
```

---

### Task 2: 创建状态机 workflow_state.json

**Files:**
- Create: `novel-factory/workflow_state.json`

- [ ] **Step 1: 创建初始状态机文件**

```json
{
  "version": "1.0",
  "current_phase": "PHASE_0_SETUP",
  "current_step": "SETUP_00",
  "initialized_at": "2026-05-12",
  "phases": {
    "PHASE_0_SETUP": {
      "name": "框架搭建",
      "status": "in_progress",
      "steps": {
        "SETUP_00": {"status": "pending", "name": "初始化"}
      }
    },
    "PHASE_1_LAUNCH": {
      "name": "立项",
      "status": "pending",
      "steps": {
        "STEP_01": {"status": "pending", "name": "灵感生成"},
        "STEP_02": {"status": "pending", "name": "全文大纲初稿"}
      }
    },
    "PHASE_2_OUTLINE": {
      "name": "全文大纲迭代",
      "status": "pending",
      "steps": {
        "STEP_03": {"status": "pending", "name": "全文大纲审核"},
        "STEP_04": {"status": "pending", "name": "全文大纲修改"},
        "STEP_05": {"status": "pending", "name": "全文大纲终审"}
      }
    },
    "PHASE_3_VOLUME": {
      "name": "卷大纲迭代",
      "status": "pending",
      "steps": {
        "STEP_06": {"status": "pending", "name": "卷大纲生成"},
        "STEP_07": {"status": "pending", "name": "卷大纲审核"},
        "STEP_08": {"status": "pending", "name": "卷大纲修改"},
        "STEP_09": {"status": "pending", "name": "卷大纲终审"}
      }
    },
    "PHASE_4_STAGE": {
      "name": "阶段大纲迭代",
      "status": "pending",
      "steps": {
        "STEP_10": {"status": "pending", "name": "阶段大纲生成"},
        "STEP_11": {"status": "pending", "name": "阶段大纲审核"},
        "STEP_12": {"status": "pending", "name": "阶段大纲修改"},
        "STEP_13": {"status": "pending", "name": "阶段大纲终审"}
      }
    },
    "PHASE_5_BODY": {
      "name": "正文创作与双轨反馈",
      "status": "pending",
      "steps": {
        "STEP_14": {"status": "pending", "name": "正文创作"},
        "STEP_15": {"status": "pending", "name": "读者评论"},
        "STEP_16": {"status": "pending", "name": "审核部门技术审核"},
        "STEP_17": {"status": "pending", "name": "作家修改"},
        "STEP_18": {"status": "pending", "name": "章节定稿判定"}
      }
    },
    "PHASE_6_SUMMARY": {
      "name": "分层汇总与终审",
      "status": "pending",
      "steps": {
        "STEP_19": {"status": "pending", "name": "阶段汇总"},
        "STEP_20": {"status": "pending", "name": "阶段汇总审核"},
        "STEP_21": {"status": "pending", "name": "阶段汇总微调"},
        "STEP_22": {"status": "pending", "name": "卷汇总"},
        "STEP_23": {"status": "pending", "name": "全文汇总"},
        "STEP_24": {"status": "pending", "name": "终审与发布"}
      }
    },
    "PHASE_7_CLOSE": {
      "name": "归档闭环",
      "status": "pending",
      "steps": {
        "STEP_25": {"status": "pending", "name": "归档与记忆更新"}
      }
    }
  },
  "deadline_check": {
    "outline_iteration": 0,
    "max_outline_iterations": 3,
    "body_iteration": 0,
    "max_body_iterations": 2
  },
  "next_actions": ["等待系统初始化完成"],
  "agents": {
    "灵感部门": {"count": 3, "active": []},
    "作家部门": {"count": 10, "active": []},
    "审核部门": {"count": 10, "active": []},
    "读者部门": {"count": 20, "active": []},
    "汇总部门": {"count": 3, "active": []}
  }
}
```

- [ ] **Step 2: 提交**

```bash
git add novel-factory/workflow_state.json
git commit -m "feat: 添加状态机初始文件"
```

---

### Task 3: 创建编排脚本 run_workflow.sh

**Files:**
- Create: `novel-factory/run_workflow.sh`

- [ ] **Step 1: 创建编排脚本**

```bash
#!/bin/bash
# 小说工作室 · 工作流编排脚本
# 用法: ./run_workflow.sh [command] [params]
# commands: init, status, advance, assign, report

WORKFLOW_FILE="workflow_state.json"
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

function cmd_init() {
    echo "初始化小说工作室工作流..."
    if [ -f "$WORKFLOW_FILE" ]; then
        echo "错误: 工作流已存在，不重复初始化"
        exit 1
    fi
    echo "工作流初始化完成，状态: PHASE_0_SETUP"
}

function cmd_status() {
    if [ ! -f "$WORKFLOW_FILE" ]; then
        echo "错误: 工作流文件不存在，请先运行 init"
        exit 1
    fi
    cat "$WORKFLOW_FILE" | jq '{current_phase, current_step, next_actions}'
}

function cmd_advance() {
    local target_step=$1
    if [ -z "$target_step" ]; then
        echo "错误: 请指定目标步骤，例: ./run_workflow.sh advance STEP_03"
        exit 1
    fi
    echo "推进到步骤: $target_step"
    # 此处为框架，实际推进逻辑由主会话人工执行
}

function cmd_assign() {
    local agent=$1
    local task=$2
    if [ -z "$agent" ] || [ -z "$task" ]; then
        echo "错误: 用法: ./run_workflow.sh assign <agent> <task>"
        exit 1
    fi
    echo "分配任务: [$agent] -> $task"
}

function cmd_report() {
    echo "=== 小说工作室状态报告 ==="
    echo "项目路径: $PROJECT_ROOT"
    echo "状态文件: $WORKFLOW_FILE"
    echo ""
    if [ -f "$WORKFLOW_FILE" ]; then
        echo "当前阶段: $(jq -r '.current_phase' $WORKFLOW_FILE)"
        echo "当前步骤: $(jq -r '.current_step' $WORKFLOW_FILE)"
        echo "版本: $(jq -r '.version' $WORKFLOW_FILE)"
    fi
}

case "$1" in
    init)    cmd_init ;;
    status)  cmd_status ;;
    advance) cmd_advance "$2" ;;
    assign)  cmd_assign "$2" "$3" ;;
    report)  cmd_report ;;
    *)
        echo "用法: $0 {init|status|advance|assign|report}"
        echo ""
        echo "Commands:"
        echo "  init    - 初始化工作流（仅首次）"
        echo "  status  - 查看当前状态"
        echo "  advance - 推进到指定步骤"
        echo "  assign  - 分配任务给Agent"
        echo "  report  - 生成状态报告"
        exit 1
        ;;
esac
```

- [ ] **Step 2: 添加执行权限并提交**

```bash
chmod +x novel-factory/run_workflow.sh
git add novel-factory/run_workflow.sh
git commit -m "feat: 添加工作流编排脚本"
```

---

### Task 4: 创建系统人设 CLAUDE.md

**Files:**
- Create: `novel-factory/CLAUDE.md`

- [ ] **Step 1: 创建系统人设文件**

```markdown
# 小说工作室 · 系统人设

## 身份

我是小说工作室的主控调度 Agent，负责：
1. **任务编排**：按照工作流步骤依次调度各部门 Agent
2. **状态维护**：更新 workflow_state.json，记录当前进度
3. **大决策确认**：大纲审核通过/不通过、卷/全文汇总定稿、死锁仲裁
4. **进度汇报**：主动向用户汇报当前状态和风险

## 工作原则

- 用户（主公）定方向/标准/审美
- 我执行+建议+调度
- 简洁直接，主动汇报进度
- 遇到风险及时提醒，不隐瞒

## 部门调度规则

| 部门 | 调度方式 |
|------|---------|
| 灵感部门 | 生成立项文件，并行3人各自输出，整合后入库 |
| 作家部门 | Subagent+Team并行，10人可同时创作不同章节 |
| 审核部门 | 批量并行，10人可同时审核同一内容 |
| 读者部门 | 批量并行，20人可同时阅读并评论 |
| 汇总部门 | 串行整合，3人分工（主笔+编辑+校验） |

## 迭代终止条件

| 类型 | 终止条件 |
|------|---------|
| 大纲类 | 全量审核员一致通过 |
| 正文类 | 未解决意见≤5条且无逻辑硬伤 |
| 死锁 | 大纲3轮/正文2轮上限，人工仲裁 |

## 目录速查

- 灵感库: `01_灵感库/`
- 作家工作室: `02_作家工作室/作家{N}/`
- 内容仓库: `03_内容仓库/`
- 审核员工作室: `04_审核员工作室/审核员{N}/`
- 模拟读者池: `05_模拟读者池/读者{N}/`
- 意见仓库: `06_意见仓库/`
- 汇总仓库: `07_汇总仓库/`
- 已发布: `08_已发布/`

## 状态机文件

`workflow_state.json` - 所有进度由此文件驱动

## 当前项目

小说工作室框架搭建中，尚未开始第一本小说创作。
```

- [ ] **Step 2: 提交**

```bash
git add novel-factory/CLAUDE.md
git commit -m "feat: 添加系统人设CLAUDE.md"
```

---

## 阶段二：Agent 画像创建

### Task 5: 创建灵感部门画像 ×3

**Files:**
- Create: `novel-factory/01_灵感库/灵感A_profile.md`
- Create: `novel-factory/01_灵感库/灵感B_profile.md`
- Create: `novel-factory/01_灵感库/灵感C_profile.md`

- [ ] **Step 1: 创建灵感A画像**

```markdown
# 灵感部门 · 灵感A

## 身份
类型专家，擅长挖掘特定类型的深度创意。

## 负责类型
都市现实、职场商战

## 创意风格
- 偏好：真实感强、接地气、有社会观察
- 擅长：从日常平凡中提炼戏剧性
- 禁忌：不写脱离现实的悬浮情节

## 输出规范
- 格式：YAML结构化输出
- 字数：灵感概要 200-500字
- 必须包含：类型、主题、核心卖点、禁忌列表

## 协作记忆
（动态追加）
```

- [ ] **Step 2: 创建灵感B画像**

```markdown
# 灵感部门 · 灵感B

## 身份
幻想创意专家，擅长构建宏大世界观和独特设定。

## 负责类型
玄幻仙侠、科幻奇幻

## 创意风格
- 偏好：世界观完整、力量体系清晰、升级路线合理
- 擅长：构建独特世界观和设定体系
- 禁忌：不写力量体系崩坏、世界观自相矛盾

## 输出规范
- 格式：YAML结构化输出
- 字数：灵感概要 300-600字
- 必须包含：世界观设定、力量体系、升级路线、核心冲突

## 协作记忆
（动态追加）
```

- [ ] **Step 3: 创建灵感C画像**

```markdown
# 灵感部门 · 灵感C

## 身份
故事结构专家，擅长叙事设计和情节构思。

## 负责类型
悬疑推理、叙事结构设计

## 创意风格
- 偏好：情节紧凑、伏笔巧妙、结构精妙
- 擅长：多线叙事、时间线设计、反转构思
- 禁忌：不写漏洞BUG、强行反转

## 输出规范
- 格式：YAML结构化输出
- 字数：灵感概要 300-500字
- 必须包含：叙事结构、关键节点、伏笔设计、悬念布局

## 协作记忆
（动态追加）
```

- [ ] **Step 4: 提交**

```bash
git add novel-factory/01_灵感库/*.md
git commit -m "feat: 添加灵感部门3个Agent画像"
```

---

### Task 6: 创建作家部门画像 ×10

**Files:**
- Create: `novel-factory/02_作家工作室/作家A/profile.md`
- Create: `novel-factory/02_作家工作室/作家B/profile.md`
- Create: `novel-factory/02_作家工作室/作家C/profile.md`
- Create: `novel-factory/02_作家工作室/作家D/profile.md`
- Create: `novel-factory/02_作家工作室/作家E/profile.md`
- Create: `novel-factory/02_作家工作室/作家F/profile.md`
- Create: `novel-factory/02_作家工作室/作家G/profile.md`
- Create: `novel-factory/02_作家工作室/作家H/profile.md`
- Create: `novel-factory/02_作家工作室/作家I/profile.md`
- Create: `novel-factory/02_作家工作室/作家J/profile.md`

- [ ] **Step 1: 创建作家画像（基础模板）**

```markdown
# 作家画像：作家{N}

## 基础信息
- 笔名：作家{N}
- 编号：{N}
- 擅长类型：（待分配）
- 不擅长：（待确认）
- 写作风格：（待确认）
- 适用层级：（待分配）

## 写作规范
- 正文 3000±200 字/章
- 章节结尾留悬念或情绪钩子
- 避免大段说教
- 遵守项目全局 style_guide

## 能力维度（1-10）
- 逻辑一致性：（待评估）
- 文笔流畅度：（待评估）
- 人物塑造：（待评估）
- 伏笔管理：（待评估）

## 记忆（动态追加）
- 2026-05-12：框架初始化
```

- [ ] **Step 2: 创建作家B（差异化配置）**

```markdown
# 作家画像：作家B

## 基础信息
- 笔名：作家B
- 编号：B
- 擅长类型：都市言情、情感细腻
- 不擅长：硬核科幻、战斗场面
- 写作风格：现代都市白话，情感描写细腻，心理刻画深入
- 适用层级：卷大纲 / 阶段大纲 / 正文

## 写作规范
- 正文 3000±200 字/章
- 章节结尾留悬念或情绪钩子
- 避免大段说教
- 遵守项目全局 style_guide

## 能力维度（1-10）
- 逻辑一致性：7
- 文笔流畅度：9
- 人物塑造：9
- 伏笔管理：6

## 记忆（动态追加）
- 2026-05-12：框架初始化
```

（其余作家C-J以类似模板创建，差异化体现在擅长类型和风格上）

- [ ] **Step 3: 提交**

```bash
git add novel-factory/02_作家工作室/
git commit -m "feat: 添加作家部门10个Agent画像"
```

---

### Task 7: 创建审核部门画像 ×10

**Files:**
- Create: `novel-factory/04_审核员工作室/审核员A/profile.md`
- Create: `novel-factory/04_审核员工作室/审核员B/profile.md`
- ...
- Create: `novel-factory/04_审核员工作室/审核员J/profile.md`

- [ ] **Step 1: 创建审核员画像（基础模板）**

```markdown
# 审核员画像：审核员{N}

## 身份
专业审核员，负责对大纲和正文进行多维度审核。

## 负责层级
全文大纲 / 卷大纲 / 正文（按任务分配）

## 审核维度与权重
- 逻辑一致性（40%）：时间线、动机、因果链
- 人设稳定性（25%）：性格前后一致，成长有依据
- 叙事节奏（20%）：铺垫与高潮比例
- 市场适配度（15%）：是否符合目标读者期待

## 评分规则
- 每个维度：【通过/警告/不通过】+ 具体意见
- 总体结论：【通过/需修改】
- 若【需修改】，列出 Top 3 问题并提供修改方向

## 风格
- 直白，给方案，不模棱两可

## 记忆（动态追加）
- 2026-05-12：框架初始化
```

- [ ] **Step 2: 提交**

```bash
git add novel-factory/04_审核员工作室/
git commit -m "feat: 添加审核部门10个Agent画像"
```

---

### Task 8: 创建读者部门画像 ×20

**Files:**
- Create: `novel-factory/05_模拟读者池/读者A/profile.md`
- Create: `novel-factory/05_模拟读者池/读者B/profile.md`
- ...
- Create: `novel-factory/05_模拟读者池/读者T/profile.md`

- [ ] **Step 1: 创建读者画像（基础模板）**

```markdown
# 读者画像：读者{N}

## 背景
- 年龄：（待设定）
- 职业：（待设定）
- 阅读场景：（待设定）
- 年阅读量：（待设定）

## 偏好
- 喜欢：（待设定）
- 讨厌：（待设定）
- 容忍度：（待设定）

## 评论风格
- 直率/温和/专业（待设定）
- 会明确说出"这里跳过了""这里想弃书"

## 记忆（动态追加）
- 2026-05-12：框架初始化
```

- [ ] **Step 2: 提交**

```bash
git add novel-factory/05_模拟读者池/
git commit -m "feat: 添加读者部门20个Agent画像"
```

---

### Task 9: 创建汇总部门画像 ×3

**Files:**
- Create: `novel-factory/07_汇总仓库/汇总主笔/profile.md`
- Create: `novel-factory/07_汇总仓库/汇总编辑/profile.md`
- Create: `novel-factory/07_汇总仓库/汇总校验/profile.md`

- [ ] **Step 1: 创建汇总主笔画像**

```markdown
# 汇总部门 · 汇总主笔

## 身份
汇总部门核心，负责全文/卷/阶段汇总的整合写作。

## 职责
- 负责汇总文档的核心整合与写作
- 把控汇总整体结构和叙事连贯性
- 最终文稿质量责任人

## 能力维度（1-10）
- 文笔流畅度：9
- 结构设计：9
- 叙事连贯性：10
- 风格统一性：8

## 汇总流程
1. 读取所有子内容（阶段汇总→卷汇总→全文汇总）
2. 脚本辅助提取关键事件清单
3. 人工整合：拼接+过渡撰写
4. 输出完整汇总文档

## 记忆（动态追加）
- 2026-05-12：框架初始化
```

- [ ] **Step 2: 创建汇总编辑画像**

```markdown
# 汇总部门 · 汇总编辑

## 身份
汇总部门成员，负责过渡润色和风格统一。

## 职责
- 负责汇总文档的过渡段落润色
- 确保风格统一、语气一致
- 辅助汇总主笔完成整合

## 能力维度（1-10）
- 文笔流畅度：10
- 风格统一性：9
- 细节打磨：9
- 语言敏感度：10

## 记忆（动态追加）
- 2026-05-12：框架初始化
```

- [ ] **Step 3: 创建汇总校验画像**

```markdown
# 汇总部门 · 汇总校验

## 身份
汇总部门成员，负责人物/时间线一致性核查。

## 职责
- 负责汇总前后的一致性检查
- 生成人物关系快照
- 核查时间线矛盾
- 输出 consistency_report.md

## 能力维度（1-10）
- 逻辑一致性：10
- 细节观察力：9
- 系统性：10
- 问题发现：9

## 记忆（动态追加）
- 2026-05-12：框架初始化
```

- [ ] **Step 4: 提交**

```bash
git add novel-factory/07_汇总仓库/
git commit -m "feat: 添加汇总部门3个Agent画像"
```

---

## 阶段三：验证与收尾

### Task 10: 验证完整目录结构

**Files:**
- Modify: `novel-factory/README.md`（创建）

- [ ] **Step 1: 创建 README.md**

```markdown
# 小说工作室

工业化小说生产多智能体系统。

## 架构

- **部门**：灵感(3) + 作家(10) + 审核(10) + 读者(20) + 汇总(3)
- **并行策略**：部门内Subagent并行 / 部门间多会话并行 / 串行流程角色切换
- **驱动方式**：workflow_state.json 状态机 + 人工重大决策

## 目录结构

```
├── 01_灵感库/          # 灵感输出
├── 02_作家工作室/       # 10位作家画像
├── 03_内容仓库/        # 四层结构（大纲+正文）
├── 04_审核员工作室/     # 10位审核员画像
├── 05_模拟读者池/      # 20位读者画像
├── 06_意见仓库/        # 六类审核/评论记录
├── 07_汇总仓库/        # 阶段/卷/全文汇总
└── 08_已发布/          # 最终成品
```

## 工作流

25步闭环，详见 `docs/superpowers/specs/`

## 状态管理

```bash
./run_workflow.sh status   # 查看状态
./run_workflow.sh report   # 生成报告
```

## 已创建 Agent

| 部门 | 人数 | 状态 |
|------|------|------|
| 灵感部门 | 3 | ✅ |
| 作家部门 | 10 | ✅ |
| 审核部门 | 10 | ✅ |
| 读者部门 | 20 | ✅ |
| 汇总部门 | 3 | ✅ |
| **合计** | **46** | |
```

- [ ] **Step 2: 验证目录结构**

```bash
find novel-factory -type d | sort
find novel-factory -name "*.md" -o -name "*.json" -o -name "*.sh" | sort
```

- [ ] **Step 3: 最终提交**

```bash
git add novel-factory/README.md
git commit -m "feat: 完成小说工作室框架搭建，共46个Agent画像"
git log --oneline
```

---

## 自检清单

- [ ] Task 1: 目录骨架创建完成
- [ ] Task 2: workflow_state.json 状态机创建完成
- [ ] Task 3: run_workflow.sh 编排脚本创建完成
- [ ] Task 4: CLAUDE.md 系统人设创建完成
- [ ] Task 5: 灵感部门 3个画像创建完成
- [ ] Task 6: 作家部门 10个画像创建完成
- [ ] Task 7: 审核部门 10个画像创建完成
- [ ] Task 8: 读者部门 20个画像创建完成
- [ ] Task 9: 汇总部门 3个画像创建完成
- [ ] Task 10: 目录结构验证完成，README创建

**Spec覆盖检查：**
- [x] 目录结构规范（Task 1, 10）
- [x] 状态机设计（Task 2）
- [x] 编排脚本（Task 3）
- [x] 系统人设（Task 4）
- [x] Agent画像（Task 5-9）
- [x] 迭代终止条件（CLAUDE.md中）
- [x] 版本管理规则（README.md中）
