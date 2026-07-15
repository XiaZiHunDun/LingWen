# 小说工厂 · CCGS 升级整合指南

> 整合《小说工作室方案》与 CCGS 优化框架
> 版本：1.0 | 日期：2026-05-19

---

## 一、文档体系总览

```
小说工厂文档体系
├── 顶层管理文档
│   ├── CLAUDE.md                    # 主控调度定义
│   └── 小说工作室方案.md             # 完整架构（原文档）
│
├── 规范文档（docs/）
│   ├── collaborative-protocol.md    # ⭐ 协作协议（新增）
│   ├── novel-pillars.md             # ⭐ 小说支柱框架（新增）
│   ├── character-bible.md           # ⭐ 角色圣经模板（新增）
│   ├── faction-design.md            # ⭐ 势力设计模板（新增）
│   ├── lore-registry.md             # ⭐ 世界观注册表（新增）
│   ├── context-management.md        # ⭐ 上下文管理规范（新增）
│   ├── 部门协调协议.md              # 部门协调（原已存在）
│   └── 工作流模式库.md              # 工作流模式（原已存在）
│
└── 模板文档（docs/templates/）
    ├── CCGS_UPGRADE.md              # ⭐ CCGS 升级总览（新增）
    ├── character-profile-template.md # 角色卡片模板（待升级）
    └── outline-template.md          # 大纲模板（待升级）
```

---

## 二、核心改进项对照

| 改进项 | 来源 | 位置 | 优先级 |
|--------|------|------|--------|
| 协作协议（Options→Decision） | CCGS leadership-agent-protocol | docs/collaborative-protocol.md | **P0** |
| 小说支柱框架 | CCGS game-pillars | docs/novel-pillars.md | **P0** |
| 角色圣经（升级版） | CCGS narrative-character-sheet | docs/character-bible.md | **P1** |
| 势力设计模板 | CCGS faction-design | docs/faction-design.md | **P2** |
| 世界观注册表 | CCGS world-builder | docs/lore-registry.md | **P2** |
| 上下文管理 | CCGS context-management | docs/context-management.md | **P1** |

---

## 三、《星陨纪元》项目适配

### 3.1 小说支柱（待填充）

基于项目基础层.yaml，项目已有以下支柱雏形：

```
支柱1（推测）：主角智商全程在线
支柱2（推测）：环环相扣的势力博弈
支柱3（推测）：光明与黑暗的辩证
```

**待执行**：将这些写成可证伪的支柱声明，写入 `docs/novel-pillars.md`

### 3.2 角色圣经（4个主角待建）

| 角色 | Canon等级 | 状态 | 位置 |
|------|-----------|------|------|
| 林夜 | Provisional | ch001-ch050已分析，弧光2/5 | docs/character-bible/ |
| 苏琳 | Provisional | 待建 | docs/character-bible/ |
| 铁蛋 | Provisional | 待建 | docs/character-bible/ |
| 莫言 | Provisional | 待建 | docs/character-bible/ |

### 3.3 冲突升级路径（已适配）

| 情况 | 原路径 | CCGS优化后 |
|------|--------|-----------|
| 两个审核员冲突 | 作家→主编→汇总→人工 | 主编（narrative-director）仲裁 |
| 人设vs剧情 | - | 主作家（creative-director）仲裁 |
| 设定vs世界观 | - | 世界观管理员（world-builder）仲裁 |
| 进度冲突 | 主控调度 | 调度Agent（producer） |

---

## 四、工作流程升级要点

### 4.1 协作协议核心差异

**原流程**：
```
作家写稿 → 提交审核 → 审核意见 → 作家修改
```

**CCGS优化后**：
```
作家草稿 → 展示草案（带Options）→ 用户决策 → 确认后写入 → 提交审核
                         ↑ 决策在此
```

**关键区别**：
- 重大修改前，作家必须展示 Options 并等待用户决策
- 审核意见也需要带「影响分析」，不只是指出问题

### 4.2 ADR系统启用

当设定变更影响多个卷/阶段时，创建 ADR：

```
09_规范文档/架构决策/
├── README.md
├── ADR-001-林夜力量觉醒机制.md    # 待创建
└── ADR-002-苏琳预言能力边界.md     # 待创建
```

### 4.3 上下文管理策略

**层级聚合**（解决长篇上下文溢出）：
```
正文（3000字/章）
  ↓ 节摘要
阶段汇总（~2000字）
  ↓ 阶段摘要
卷汇总（~1500字）
  ↓ 卷摘要
全文汇总（~1000字）
```

---

## 五、下一步行动清单

### P0（立即执行）✅ 完成

- [x] **填充 novel-pillars.md**：`docs/novel-pillars.md`（已 Approved，creative-director 会话确认）
- [ ] **启用协作协议**：需要在实际创作中应用 `collaborative-protocol.md` 的 Options→Decision 流程

### P1（本周执行）✅ 完成

- [x] **创建林夜 character-bible.md**：`docs/character-bible/林夜.md`
- [x] **创建苏琳 character-bible.md**：`docs/character-bible/苏琳.md`
- [x] **创建铁蛋 character-bible.md**：`docs/character-bible/铁蛋.md`
- [x] **创建莫言 character-bible.md**：`docs/character-bible/莫言.md`

### P2（持续完善）✅ 完成

- [x] **建立 lore-registry.md**：`docs/lore-registry.md`（地理、势力、历史、伏笔注册）
- [x] **创建 ADR-001**：`09_规范文档/架构决策/ADR-001-林夜力量觉醒机制.md`
- [ ] **启用 context-management.md**：规范会话状态文件管理

---

## 六、模板升级建议

### 6.1 角色卡片模板（原版 → 升级版）

**原版** (`docs/templates/character-profile-template.md`)：
- 基本信息、性格、关系、弧光、道具、审核备注
- 结构简单，适合快速创建

**升级版** (`docs/character-bible.md`) 新增：
- Canon 等级标记（Established/Provisional/Under Review）
- 情绪触发表（Emotion | Trigger | Expression | Example Line）
- 角色弧光3阶段表（Introduction/Development/Resolution）
- 对话状态依赖表
- 跨引用索引

**建议**：两套模板并存，原版用于快速创建，升级版用于重要角色的完整定义

### 6.2 大纲模板升级

原版大纲模板已包含：基本信息、阶段目标、关键情节点、人物安排、伏笔回收、审核记录

**建议补充**：
- 服务的支柱（明确此阶段服务于哪个支柱）
- 情绪弧线设计（此阶段的情感基调变化）
- Canon 等级标记（已确立/暂定）

---

## 七、已有材料的复用

### 7.1 基础层.yaml 的转化

基础层.yaml 已有内容 → 对应 CCGS 文档：

| 基础层.yaml 字段 | CCGS 对应文档 |
|-----------------|--------------|
| 核心主题 | novel-pillars.md 的 Core Fantasy |
| 核心主角人设 | character-bible.md（4个主角） |
| 核心冲突主线 | novel-pillars.md 的 Pillar |
| 目标受众 | novel-pillars.md 的 Player Motivation |
| 风格指南 | novel-pillars.md 的 Anti-Pillars |
| 禁忌设定 | novel-pillars.md 的 Anti-Pillars |

### 7.2 角色弧光分析的转化

已有 `林夜_角色弧光分析_ch001-ch050.md` → 转化为 `character-bible/林夜.md`

**转化内容**：
- 弧光阶段分析 → character-bible Arc 部分
- 缺失阶段 → Internal Conflict 部分
- 建议 → Cross-References 部分

---

*本文档是《星陨纪元》项目的 CCGS 升级适配指南。所有新增文档在 `docs/` 目录下，原有文档结构保持不变。*