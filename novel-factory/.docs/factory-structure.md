# 灵文 · 工业化小说生产系统 - 完整结构文档

---

## 一、项目概览

| 项目 | 内容 |
|------|------|
| **项目名称** | 星陨纪元 |
| **总章节数** | 360章 |
| **项目状态** | v3.0 已完成 |
| **核心流程** | 6大阶段，25个步骤 |
| **AI角色** | 主控调度 Agent（灵文） |

---

## 二、顶层目录结构

```
novel-factory/
├── CLAUDE.md              # 主控Agent说明书（本文档入口）
├── README.md              # 项目说明
├── workflow_state.json    # 工作流状态机
├── run_init.sh           # 初始化脚本
├── run_verify.sh         # 验证脚本
├── run_verify_engine.py   # 验证引擎
│
├── 01_灵感库/            # 灵感部门输出
├── 02_作家工作室/        # 作家部门工作区
├── 03_内容仓库/          # 四层内容存储
├── 04_审核员工作室/      # 审核部门工作区
├── 05_模拟读者池/        # 读者部门（20人）
├── 06_意见仓库/          # 六类审核/评论记录
├── 07_汇总仓库/           # 阶段/卷/全文汇总
├── 08_已发布/            # 最终成品
├── 09_规范文档/           # 工作流程文档
│
├── tools/                # 工具脚本
│   ├── consistency/       # 质量检查工具（10维度）
│   ├── content/          # 内容检查工具
│   ├── publish/          # 发布工具
│   └── workflow/          # 工作流控制
│
├── .skills/              # Skill管理（按部门分类）
├── .docs/                # 架构文档
├── .workflow_rules/       # 工作流规则
└── memory/               # Agent记忆
```

---

## 三、部门与目录对照

| 部门 | 目录 | 职责 |
|------|------|------|
| **灵感部门** | `01_灵感库/` | 生成立项文件（基础层+深度层） |
| **作家部门** | `02_作家工作室/` | 正文创作，每10章批次产出 |
| **审核部门** | `04_审核员工作室/` | 技术审核+市场审核 |
| **读者部门** | `05_模拟读者池/` | 评论收集，20人并行 |
| **汇总部门** | `07_汇总仓库/` | 分层汇总，3人串行整合 |
| **发布部门** | `08_已发布/` | 最终成品归档 |

---

## 四、内容仓库结构（03_内容仓库）

```
03_内容仓库/
├── 01_全文总体大纲/
│   ├── index.json
│   └── 全局大纲.md
│
├── 02_卷大纲/
│   ├── index.json
│   ├── 卷1/废土星火/
│   ├── 卷2/星际争锋/
│   └── 卷3/宇宙守护/
│
├── 03_阶段大纲/
│   ├── index.json
│   └── 卷1/阶段1-7/
│       ├── 卷1_阶段1_大纲.md
│       └── ...
│
├── 04_正文/
│   ├── index.json
│   ├── ch001.md ~ ch360.md
│   └── (每章独立文件)
│
├── index_README.md
└── update_index.py
```

---

## 五、意见仓库结构（06_意见仓库）

```
06_意见仓库/
├── 01_全文大纲_审核/       # 全文大纲审核意见
├── 02_卷大纲_审核/         # 卷大纲审核意见
├── 03_阶段大纲_审核/       # 阶段大纲审核意见
├── 04_正文_审核/           # 正文审核意见
├── 05_作家修改/             # 作家修改记录
├── 05_读者评论/            # 读者评论
└── 06_汇总_审核/           # 汇总审核意见
```

**优先级**：P0（硬伤）> P1（高优）> P2（中优）> P3（低优）

---

## 六、工具目录结构（tools）

```
tools/
├── consistency/           # 质量检查（10维度）
│   ├── run_quality_checks.py    # 统一调度脚本
│   ├── check_segment_relevance.py   # 情节关联度
│   ├── check_plot_device_tracking.py # 伏笔回收率
│   ├── check_scene_logic.py      # 场景逻辑
│   ├── check_emotional_rhythm.py # 情感节奏
│   ├── check_dialogue_style.py   # 对话风格
│   ├── check_character_arc_llm.py # 人物弧光（LLM）
│   ├── auto_consistency_checker.py  # 基础一致性
│   ├── check_naming.py          # 命名一致性
│   ├── check_content_integrity.py   # 内容完整性
│   ├── check_duplicate.py       # 章节重复
│   ├── check_character_state.py   # 人物状态
│   └── check_timeline.py        # 时间线
│
├── content/               # 内容工具
│   ├── run_check_naming.sh
│   └── run_fix_naming.sh
│
├── publish/              # 发布工具
│   └── run_publish.sh
│
└── workflow/             # 工作流控制
    └── run_workflow.sh
```

---

## 七、Skill管理架构（.skills）

按部门分类管理，每个部门管理自己的Skill。

```
.skills/
├── _global/                      # 全局通用
│   └── workflow-controller/       # 工作流状态控制
│       └── SKILL.md
│
├── inspiration-dept/            # 灵感部门
│   └── inspiration-generator/    # 灵感生成
│       └── SKILL.md
│
├── writer-dept/                 # 作家部门
│   ├── outline-drafting/         # 大纲起草
│   │   └── SKILL.md
│   └── review-opinion-synthesizer/ # 审核意见综合
│       └── SKILL.md
│
├── reviewer-dept/                # 审核部门
│   └── novel-quality-check/      # 10维度质量检查
│       ├── SKILL.md
│       └── evals/                # 评估测试
│
├── reader-dept/                 # 读者部门
│   └── reader-feedback-aggregator/ # 读者反馈收集
│       └── SKILL.md
│
└── summary-dept/                # 汇总部门
    └── summary-compiler/         # 汇总整合
        └── SKILL.md
```

### Skill安装说明

首次在新环境使用时需执行：
```bash
mkdir -p ~/.claude/skills && cp -r .skills/* ~/.claude/skills/
```

---

## 八、工作流状态机（workflow_state.json）

### 6大阶段

| Phase | 名称 | 状态 |
|-------|------|------|
| PHASE_1_LAUNCH | 立项 | ✅ 已完成 |
| PHASE_2_OUTLINE | 全文大纲迭代 | ✅ 已完成 |
| PHASE_3_VOLUME | 卷大纲迭代 | ✅ 已完成 |
| PHASE_4_STAGE | 阶段大纲迭代 | ✅ 已完成 |
| PHASE_5_BODY | 正文创作与双轨反馈 | ✅ 已完成 |
| PHASE_6_SUMMARY | 分层汇总与终审 | ✅ 已完成 |
| PHASE_7_CLOSE | 归档闭环 | ✅ 已完成 |

### 25个步骤

```
STEP_01-02 → STEP_03-05 → STEP_06-09 → STEP_10-13 → STEP_14-18 → STEP_19-24 → STEP_25
```

---

## 九、质量检查维度（10维度）

| 维度 | 类型 | 说明 |
|------|------|------|
| 命名一致性 | 规则 | 文件名chXXX.md与章节内标题"第X章"一致 |
| 内容完整性 | 规则 | **本章完**标记、字数≥500 |
| 章节重复 | 规则 | 跨章节相似度>80%预警 |
| 人物状态 | 规则 | 性别/生死/形态前后矛盾 |
| 时间线 | 规则 | "年前"与"瞬间"同时出现等明显错误 |
| 情节关联度 | 规则 | 每段落与前后章节的关联程度 |
| 伏笔回收率 | 规则 | 首次出现元素在后续N章内回收 |
| 场景逻辑 | 规则 | 场景转换合理性、孤岛章节检测 |
| 情感节奏 | 规则 | 情绪波动是否合理 |
| 对话风格 | 规则 | 角色对话字数异常检测 |
| 人物弧光 | **LLM** | 角色弧光完整性 |

---

## 十、调度命令速查

| 部门 | 命令 | 说明 |
|------|------|------|
| 工作流 | `./run_workflow.sh status` | 查看当前状态 |
| 灵感 | `./run_inspiration.sh generate <类型>` | 生成灵感 |
| 作家 | `./run_writer.sh batch ch001-ch010` | 批量分配 |
| 审核 | `./run_review.sh batch ch001-ch010` | 批量审核 |
| 读者 | `./run_reader.sh batch ch001-ch010` | 批量评论 |
| 汇总 | `./run_summary.sh volume 卷1` | 卷汇总 |
| 意见 | `./run_opinion.sh pending` | 查看待处理意见 |

---

## 十一、关键文件说明

| 文件 | 用途 |
|------|------|
| `CLAUDE.md` | 主控Agent说明书，项目根目录 |
| `workflow_state.json` | 工作流状态机，驱动所有进度 |
| `README.md` | 项目说明文档 |
| `.docs/workflow-architecture.md` | 流程架构详细文档 |
| `.skills/*/SKILL.md` | 各部门Skill定义 |

---

*文档版本: v1.0*
*创建时间: 2026-05-18*
*适用范围: 灵文 · 工业化小说生产系统*