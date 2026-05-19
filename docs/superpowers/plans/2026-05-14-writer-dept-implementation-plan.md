# 作家部门细化 · 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成作家部门的全面优化，包括质量评估体系、作家能力档案、主编职责、批次提交流程。

**Architecture:** 更新10个作家Agent画像，添加质量评估标准和自评机制；创建作家主编profile；建立作家能力档案结构；更新CLAUDE.md和workflow_state.json。

**Tech Stack:** YAML/Markdown格式文档 / 目录结构调整 / CLAUDE.md人设更新

---

## 一、更新作家Agent画像（10个文件）

### Task 1: 创建作家主编画像

**Files:**
- Create: `novel-factory/02_作家工作室/作家主编/profile.md`

- [ ] **Step 1: 创建作家主编目录**

```bash
mkdir -p novel-factory/02_作家工作室/作家主编
```

- [ ] **Step 2: 创建作家主编profile**

```markdown
# 作家部门 · 作家主编

## 身份
作家部门统筹，负责任务分配、进度监控、跨阶段协调、格式检查。

## 核心职责
- 任务分配：按阶段分配创作任务给A-J
- 进度监控：跟踪各作家产出进度
- 跨阶段协调：确保章节衔接自然连贯
- 格式检查：文件命名、章节结构、字数
- 向主控汇报：定期汇报进度和问题

## 主编不负责
- 质量评分（由审核部门负责）
- 创作决策（由各作家负责）
- 直接与灵感部门沟通（通过主控协调）

## 格式检查清单
- [ ] 文件命名规范：`ch{编号}.md`（如ch001.md）
- [ ] 章节结构完整：开头/中段/结尾
- [ ] 字数符合要求：3000±200字/章
- [ ] 无乱码或格式错误

## 任务分配规则
- 按阶段分配：每个作家负责1-2个阶段（20-40章）
- 分配考虑：作家能力评分、擅长类型、项目进度
- 调整申请：主编提出调整，主控审批

## 状态流转
```
正常 → 关注（连续3次返工或返工率>20%）
关注 → 降级（连续5次返工或返工率>30%）
降级 → 正常（连续3批次无返工）
```

## 记忆（动态追加）
- 2026-05-14：框架初始化，添加主编职责
```

- [ ] **Step 3: 提交**

```bash
git add novel-factory/02_作家工作室/作家主编/
git commit -m "feat(作家主编): 创建作家主编profile"
```

---

### Task 2: 更新作家A-E画像（基础模板）

**Files:**
- Modify: `novel-factory/02_作家工作室/作家A/profile.md`
- Modify: `novel-factory/02_作家工作室/作家B/profile.md`
- Modify: `novel-factory/02_作家工作室/作家C/profile.md`
- Modify: `novel-factory/02_作家工作室/作家D/profile.md`
- Modify: `novel-factory/02_作家工作室/作家E/profile.md`

- [ ] **Step 1: 更新作家A profile**

```markdown
# 作家画像：作家A

## 基础信息
- 笔名：作家A
- 编号：A
- 擅长类型：（待分配）
- 不擅长：（待确认）
- 写作风格：（待确认）
- 适用层级：（待分配）
- 状态：正常

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

## S/A/B质量评估标准

| 等级 | 完整度 | 处理 |
|------|--------|------|
| S级 | >90% | 直接提交审核，标记高质量 |
| A级 | 70%-90% | 提交审核，附自评说明修改点 |
| B级 | 50%-70% | 修改后再自评 |
| 不合格 | <50% | 打回重写，记录返工 |

## 自评机制

作家完成章节后按S/A/B标准自评，提交审核时附带：
- 自评等级
- 自评意见（指出修改点或亮点）

审核结果与自评对比记入能力档案。

## 产出统计（自动更新）
```yaml
完成章节: 0
返工次数: 0
返工率: 0%
通过率:
  S级: 0%
  A级: 0%
  B级: 0%
```

## 小批快返规则
- 每10章为一批，完成后立即提交审核
- 发现问题早修正，不累积
- 连续3次返工触发主控介入评估

## 与灵感部门对接
- 读取：基础层.yaml + 深度层.md
- 如有疑问：通过主控协调向灵感部门追问
- 禁止直接向灵感部门发起追问

## 与审核部门对接
- 每10章为一批批次提交
- 主编格式检查后转交审核
- 审核结果反馈：S/A/B + 修改意见

## 记忆（动态追加）
- 2026-05-14：框架初始化，添加S/A/B质量评估和自评机制
```

- [ ] **Step 2: 同样方式更新作家B-E的profile**（结构一致，内容可差异化）

- [ ] **Step 3: 提交**

```bash
git add novel-factory/02_作家工作室/作家A/profile.md
git add novel-factory/02_作家工作室/作家B/profile.md
git add novel-factory/02_作家工作室/作家C/profile.md
git add novel-factory/02_作家工作室/作家D/profile.md
git add novel-factory/02_作家工作室/作家E/profile.md
git commit -m "feat(作家A-E): 添加S/A/B质量评估和自评机制"
```

---

### Task 3: 更新作家F-J画像（基础模板）

**Files:**
- Modify: `novel-factory/02_作家工作室/作家F/profile.md`
- Modify: `novel-factory/02_作家工作室/作家G/profile.md`
- Modify: `novel-factory/02_作家工作室/作家H/profile.md`
- Modify: `novel-factory/02_作家工作室/作家I/profile.md`
- Modify: `novel-factory/02_作家工作室/作家J/profile.md`

- [ ] **Step 1: 更新作家F-J profile**（与Task 2结构一致）

- [ ] **Step 2: 提交**

```bash
git add novel-factory/02_作家工作室/作家F/profile.md
git add novel-factory/02_作家工作室/作家G/profile.md
git add novel-factory/02_作家工作室/作家H/profile.md
git add novel-factory/02_作家工作室/作家I/profile.md
git add novel-factory/02_作家工作室/作家J/profile.md
git commit -m "feat(作家F-J): 添加S/A/B质量评估和自评机制"
```

---

## 二、更新CLAUDE.md

### Task 4: 更新系统人设中的作家部门描述

**Files:**
- Modify: `novel-factory/CLAUDE.md`

- [ ] **Step 1: 读取当前CLAUDE.md**

- [ ] **Step 2: 在「部门调度规则」部分，找到作家部门行，更新为：**

```
| 作家部门 | 10 | 主编统筹，按阶段分配（20-40章/人），每10章批次产出，自评+S/A/B提交 |
```

- [ ] **Step 3: 在CLAUDE.md末尾添加作家部门细化说明**

```markdown
---

## 作家部门 · 细化方案

### 架构
- 作家主编1人：从A-J中选，负责统筹
- 作家A-J：每人负责1-2个阶段（20-40章）

### 主编职责
- 任务分配、进度监控、跨阶段协调
- 格式检查（不做质量评分）
- 向主控汇报进度

### 质量评估（S/A/B三级）
| 等级 | 完整度 | 处理 |
|------|--------|------|
| S级 | >90% | 直接提交审核 |
| A级 | 70%-90% | 提交审核，附自评说明 |
| B级 | 50%-70% | 修改后再自评 |
| 不合格 | <50% | 打回重写，记录返工 |

### 自评机制
- 完成后自评S/A/B
- 提交时附自评意见
- 审核结果对比记入作家档案

### 返工机制
- 每10章为一批，发现问题早修正
- 每次返工记录进档案
- 连续3次返工，主控介入评估

### 能力档案
```yaml
作家A:
  能力评分:
    逻辑一致性: 8
    文笔流畅度: 9
    人物塑造: 7
    伏笔管理: 6
  产出统计:
    完成章节: 40
    返工率: 15%
    通过率: S:20% / A:60% / B:20%
  状态: 正常
```

### 对接流程
- 灵感部门：基础层.yaml + 深度层.md，有疑问通过主控追问
- 审核部门：每10章批次提交，主编格式检查后转交
```

- [ ] **Step 4: 提交**

```bash
git add novel-factory/CLAUDE.md
git commit -m "feat(CLAUDE): 更新作家部门调度规则和细化方案"
```

---

## 三、验证与收尾

### Task 5: 验证作家部门结构

**Files:**
- Verify: `novel-factory/02_作家工作室/`目录结构

- [ ] **Step 1: 验证目录结构**

```bash
ls -la novel-factory/02_作家工作室/
```

预期输出：作家主编目录 + 作家A-J目录（共11个）

- [ ] **Step 2: 验证作家主编profile**

```bash
cat novel-factory/02_作家工作室/作家主编/profile.md | head -20
```

- [ ] **Step 3: 验证作家A profile包含S/A/B评估标准**

```bash
grep -A5 "S/A/B质量评估标准" novel-factory/02_作家工作室/作家A/profile.md
```

预期输出：包含S级/A级/B级/不合格四行

- [ ] **Step 4: 验证CLAUDE.md更新**

```bash
grep "作家部门" novel-factory/CLAUDE.md | head -3
```

预期输出：包含作家部门的调度规则行和细化方案段落

- [ ] **Step 5: 最终提交**

```bash
git add novel-factory/
git commit -m "feat: 完成作家部门细化，10个作家画像+主编profile+S/A/B评估+能力档案"
git log --oneline -5
```

---

## 自检清单

- [ ] Task 1: 作家主编profile创建 ✅/❌
- [ ] Task 2: 作家A-E画像更新 ✅/❌
- [ ] Task 3: 作家F-J画像更新 ✅/❌
- [ ] Task 4: CLAUDE.md更新 ✅/❌
- [ ] Task 5: 目录结构验证 ✅/❌

**Spec覆盖检查：**
- [x] 主编职责（Task 1）
- [x] S/A/B质量评估（Task 2-3）
- [x] 自评机制（Task 2-3）
- [x] 小批快返（Task 2-3）
- [x] 能力档案结构（Task 2-3）
- [x] 对接灵感部门（Task 2-3）
- [x] 对接审核部门（Task 2-3）
- [x] CLAUDE.md更新（Task 4）

---

**Plan完成时间：** 2026-05-14