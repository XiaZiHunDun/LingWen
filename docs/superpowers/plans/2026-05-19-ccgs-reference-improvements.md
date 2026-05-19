# CCGS Reference Improvements for Novel Factory

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement 6 key improvements adapted from Claude-Code-Game-Studios-English to enhance the LingWen Novel Factory's automation, standardization, and quality control systems.

**Architecture:** Each improvement is implemented as an independent module that integrates with the existing `workflow_state.json` state machine and `.skills/` skill system. Changes are backward-compatible with the existing v3.0 workflow.

**Tech Stack:** Claude Code hooks (shell scripts) / Python / YAML frontmatter / JSON state management

---

## Overview: 6 Improvement Items

| # | Improvement | Priority | Complexity | Files to Create/Modify |
|---|-------------|----------|------------|----------------------|
| 1 | Skill System Standardization | 🔴 High | Medium | `.skills/_global/hooks-controller/`, `.claude/hooks/` |
| 2 | Automated Hook System (post-chapter checks) | 🔴 High | Low | `.claude/hooks/post-chapter-*.sh`, `tools/automated-checks/` |
| 3 | 8-Section Structured Document Standard | 🟡 Medium | Medium | `.claude/docs/design-doc-standards.md`, `09_规范文档/` |
| 4 | Explicit Model Tier Strategy Enhancement | 🟡 Medium | Low | `.claude/docs/model-tier-guide.md`, model overrides in agent YAML |
| 5 | Review Modes (full/lean/solo) | 🟡 Medium | Low | `workflow_state.json` review modes, `run_review.sh --mode` |
| 6 | Registry Architecture | 🟢 Lower | High | `docs/registry/architecture.yaml`, ownership tracking in workflow_state.json |

---

## Prerequisite: Read Existing Files

Before implementing, read these files to understand the current structure:

```
- novel-factory/workflow_state.json
- novel-factory/.claude/docs/model-tier-guide.md
- novel-factory/.claude/docs/coordination-rules.md
- novel-factory/.claude/docs/context-management.md
- novel-factory/.skills/_global/workflow-controller/SKILL.md
- novel-factory/tools/consistency/run_quality_checks.py
```

---

## Task 1: Skill System Standardization

**Goal:** Bring all 6 department skills (inspiration, writer, reviewer, reader, summary, main-controller) into a unified skill structure matching CCGS's `/skill-name` slash command pattern. Each skill should have invocation prompts, behavioral specs, and evaluation criteria.

**Files:**
- Create: `novel-factory/.skills/_global/hooks-controller/SKILL.md`
- Create: `novel-factory/.skills/_global/hooks-controller/evals/`
- Modify: `novel-factory/.skills/inspiration-dept/inspiration-generator/SKILL.md` (enhance)
- Modify: `novel-factory/.skills/writer-dept/outline-drafting/SKILL.md` (enhance)
- Modify: `novel-factory/.skills/writer-dept/review-opinion-synthesizer/SKILL.md` (enhance)
- Modify: `novel-factory/.skills/reviewer-dept/novel-quality-check/SKILL.md` (enhance)
- Modify: `novel-factory/.skills/reader-dept/reader-feedback-aggregator/SKILL.md` (enhance)
- Modify: `novel-factory/.skills/summary-dept/summary-compiler/SKILL.md` (enhance)
- Create: `novel-factory/.skills/inspiration-dept/inspiration-generator/behavioral-spec.md`
- Create: `novel-factory/.skills/writer-dept/outline-drafting/behavioral-spec.md`
- Create: `novel-factory/.skills/reviewer-dept/novel-quality-check/behavioral-spec.md`
- Create: `novel-factory/.skills/reader-dept/reader-feedback-aggregator/behavioral-spec.md`
- Create: `novel-factory/.skills/summary-dept/summary-compiler/behavioral-spec.md`

### Step 1: Create hooks-controller Skill

Create `novel-factory/.skills/_global/hooks-controller/SKILL.md`:

```markdown
# Hooks Controller Skill

## Invocation
`/hooks-controller` or "control automated hooks" or "run hook checks"

## Purpose
Central controller for all automated hooks in the novel factory. Manages hook execution,
disabled hooks, audit trail, and manual hook triggering.

## Behavioral Spec

### When Invoked
1. Read `novel-factory/.claude/settings.json` hooks section
2. Show which hooks are enabled/disabled
3. Offer to run specific hooks or show hook audit log

### Commands
- `/hooks-controller list` — show all hooks with status
- `/hooks-controller enable <hook-name>` — enable a disabled hook
- `/hooks-controller disable <hook-name>` — disable a hook
- `/hooks-controller run <hook-name>` — manually trigger a hook
- `/hooks-controller audit` — show recent hook execution log

### Hook Naming Convention
```
PreToolUse:  validate-* (before tool execution)
PostToolUse:  format-* | lint-* | check-* (after tool execution)
Stop:         final-* (session end)
SessionStart: info-* (session start)
```

## Skill Metadata
```yaml
skill_name: hooks-controller
department: _global
model: haiku
trigger_phrases:
  - /hooks-controller
  - control automated hooks
  - run hook checks
```

### Step 2: Add Behavioral Specs to Each Department Skill

For each department skill, create a `behavioral-spec.md` file that defines:

1. **Entry Condition** — When this skill should be invoked
2. **Exit Condition** — When the skill considers its task complete
3. **Input/Output Contract** — What files it reads, what files it writes
4. **Error Handling** — What to do when inputs are missing or malformed
5. **Quality Criteria** — How to evaluate the output

Example for `inspiration-dept/inspiration-generator/behavioral-spec.md`:

```markdown
# Inspiration Generator — Behavioral Spec

## Entry Condition
Skill invoked via `/inspiration` or "generate inspiration" when workflow_state.json
current_step is STEP_01 (灵感生成).

## Exit Condition
- `01_灵感库/{project_name}/基础层.yaml` exists and passes schema validation
- `01_灵感库/{project_name}/深度层.md` exists and passes schema validation
- `workflow_state.json` step_status for STEP_01 is updated

## Input Contract
| Input | Location | Required |
|-------|----------|----------|
| Project name | workflow_state.json project_status.name | Yes |
| Type preference | User prompt | No (default: auto-detect) |
| Previous inspiration | 01_灵感库/{project_name}/ | No (for iteration) |

## Output Contract
| Output | Location | Required |
|--------|----------|----------|
| 基础层.yaml | 01_灵感库/{project_name}/ | Yes |
| 深度层.md | 01_灵感库/{project_name}/ | Yes |

## Quality Criteria
- [ ] 基础层.yaml has all 8 sections (see Task 3)
- [ ] 深度层.md mentions at least 3 foreshadowed plot devices
- [ ] No hardcoded values — all thresholds are configurable
- [ ] Model tier assigned per model-tier-guide.md
```

Repeat for each department skill.

### Step 3: Verify Skill Structure

- [ ] **Step: Run skill discovery**

```bash
find novel-factory/.skills -name "SKILL.md" -o -name "behavioral-spec.md" | sort
```

Expected output: 6 department skills, each with SKILL.md and behavioral-spec.md.

- [ ] **Step: Commit**

```bash
git add novel-factory/.skills/
git commit -m "feat: standardize skill system with behavioral specs per CCGS reference"
```

---

## Task 2: Automated Hook System

**Goal:** Add CCGS-style automated hooks that run on file operations: pre-write validation, post-chapter checks (naming, word count, completeness marker), session-start status, and session-stop archiving.

**Files:**
- Create: `novel-factory/.claude/hooks/post-chapter-check.sh`
- Create: `novel-factory/.claude/hooks/session-start-info.sh`
- Create: `novel-factory/.claude/hooks/session-stop-archive.sh`
- Create: `novel-factory/.claude/hooks/validate-commit.sh`
- Create: `novel-factory/.claude/settings.json` (hooks section)
- Create: `novel-factory/tools/automated-checks/check_naming.sh`
- Create: `novel-factory/tools/automated-checks/check_completeness.sh`
- Create: `novel-factory/tools/automated-checks/check_wordcount.sh`
- Modify: `novel-factory/.claude/settings.json` (add hooks configuration)

### Step 1: Create Post-Chapter Check Hook

Create `novel-factory/.claude/hooks/post-chapter-check.sh`:

```bash
#!/bin/bash
# post-chapter-check.sh
# Runs after a chapter file (ch*.md) is written
# Checks: naming consistency, "本章完" marker, minimum word count

CHAPTER_FILE="$1"
[[ -z "$CHAPTER_FILE" ]] && exit 0

# Only run for chapter files
[[ ! "$CHAPTER_FILE" =~ ch[0-9]+\.md$ ]] && exit 0

BASE_DIR="$(cd "$(dirname "$CHAPTER_FILE")/../.." && pwd)"
CHAPTER_DIR="$BASE_DIR/03_内容仓库/04_正文"

echo "[Hook] Post-chapter check: $CHAPTER_FILE"

# 1. Naming consistency: filename chXXX.md must match "第X章" in content
python3 "$BASE_DIR/tools/automated-checks/check_naming.sh" "$CHAPTER_FILE"

# 2. Completeness marker: must contain "本章完"
python3 "$BASE_DIR/tools/automated-checks/check_completeness.sh" "$CHAPTER_FILE"

# 3. Word count: minimum 500 characters
python3 "$BASE_DIR/tools/automated-checks/check_wordcount.sh" "$CHAPTER_FILE" 500

exit 0
```

Make executable: `chmod +x novel-factory/.claude/hooks/post-chapter-check.sh`

### Step 2: Create Automated Check Scripts

Create `novel-factory/tools/automated-checks/check_naming.sh`:

```bash
#!/bin/bash
# check_naming.sh
# Validates filename chapter number matches content "第X章" heading

FILE="$1"
[[ ! -f "$FILE" ]] && echo "[ERROR] File not found: $FILE" && exit 1

FILENAME=$(basename "$FILE")
[[ ! "$FILENAME" =~ ^ch([0-9]+)\.md$ ]] && exit 0

FILE_NUM=$(printf "%03d" "${BASH_REMATCH[1]}")

# Extract chapter number from content
CONTENT_NUM=$(grep -oP '(?<=第)\d+(?=章)' "$FILE" | head -1)
[[ -z "$CONTENT_NUM" ]] && CONTENT_NUM=$(grep -oP '(?<=第)\d+(?=节)' "$FILE" | head -1)
[[ -z "$CONTENT_NUM" ]] && echo "[WARN] Cannot find chapter number in content" && exit 0

CONTENT_NUM=$(printf "%03d" "$CONTENT_NUM")

if [[ "$FILE_NUM" != "$CONTENT_NUM" ]]; then
    echo "[ERROR] Chapter number mismatch: file=$FILE_NUM, content=$CONTENT_NUM"
    exit 1
fi

echo "[OK] Chapter naming consistent: $FILE_NUM"
exit 0
```

Create `novel-factory/tools/automated-checks/check_completeness.sh`:

```bash
#!/bin/bash
# check_completeness.sh
# Validates chapter contains "本章完" marker

FILE="$1"
[[ ! -f "$FILE" ]] && echo "[ERROR] File not found: $FILE" && exit 1

if ! grep -q "本章完" "$FILE"; then
    echo "[WARN] Missing '本章完' marker in $FILE"
    exit 1
fi

echo "[OK] Completeness marker found"
exit 0
```

Create `novel-factory/tools/automated-checks/check_wordcount.sh`:

```bash
#!/bin/bash
# check_wordcount.sh
# Validates minimum character count (not word count for Chinese)

FILE="$1"
MIN_CHARS="${2:-500}"
[[ ! -f "$FILE" ]] && echo "[ERROR] File not found: $FILE" && exit 1

CHAR_COUNT=$(wc -c < "$FILE")
# Subtract the count of the file itself (markdown overhead roughly)
CHAR_COUNT=$((CHAR_COUNT - 200))  # rough overhead estimate

if [[ "$CHAR_COUNT" -lt "$MIN_CHARS" ]]; then
    echo "[WARN] Word count below minimum: $CHAR_COUNT < $MIN_CHARS in $FILE"
    exit 1
fi

echo "[OK] Character count: $CHAR_COUNT >= $MIN_CHARS"
exit 0
```

Make all executable: `chmod +x novel-factory/tools/automated-checks/*.sh`

### Step 3: Create Session Start/Stop Hooks

Create `novel-factory/.claude/hooks/session-start-info.sh`:

```bash
#!/bin/bash
# session-start-info.sh
# Shows project status on session start

STATE_FILE="novel-factory/workflow_state.json"
[[ ! -f "$STATE_FILE" ]] && exit 0

echo "========================================="
echo " 灵文 · Novel Factory Session Status"
echo "========================================="

PROJECT=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(d['project_status']['name'])" 2>/dev/null)
PHASE=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(d['current_phase'])" 2>/dev/null)
STEP=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(d['current_step'])" 2>/dev/null)
CHAPTERS=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(d['project_status'].get('total_chapters','N/A'))" 2>/dev/null)

echo "Project:  $PROJECT"
echo "Phase:    $PHASE"
echo "Step:     $STEP"
echo "Chapters: $CHAPTERS"
echo "========================================="
```

Create `novel-factory/.claude/hooks/session-stop-archive.sh`:

```bash
#!/bin/bash
# session-stop-archive.sh
# Archives session state on session end

STATE_FILE="novel-factory/workflow_state.json"
ARCHIVE_DIR="novel-factory/production/session-state"
[[ ! -f "$STATE_FILE" ]] && exit 0

mkdir -p "$ARCHIVE_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp "$STATE_FILE" "$ARCHIVE_DIR/state_at_${TIMESTAMP}.json"
echo "[Hook] Session state archived: state_at_${TIMESTAMP}.json"
```

Create `novel-factory/.claude/hooks/validate-commit.sh`:

```bash
#!/bin/bash
# validate-commit.sh
# Pre-commit validation: checks for TODO comments, hardcoded values

echo "[Hook] Running pre-commit validation..."

# Check for TODO without tracking
if grep -r "TODO" novel-factory/ --include="*.md" --include="*.py" 2>/dev/null | grep -v "意见仓库" | grep -v "# TODO"; then
    echo "[WARN] TODO comments found without tracking"
fi

# Check for hardcoded secrets (basic check)
if grep -rE "(api_key|password|token)\s*=" novel-factory/ --include="*.py" 2>/dev/null | grep -v "os.environ"; then
    echo "[ERROR] Potential hardcoded secret found"
    exit 1
fi

echo "[OK] Pre-commit validation passed"
exit 0
```

### Step 4: Create Hooks Configuration in settings.json

Create `novel-factory/.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "novel-factory/.claude/hooks/post-chapter-check.sh \"$FILE_PATH\"",
        "description": "Post-chapter validation: naming, completeness, word count"
      }
    ],
    "Stop": [
      {
        "command": "novel-factory/.claude/hooks/session-stop-archive.sh",
        "description": "Archive session state on session end"
      }
    ]
  },
  "permissions": {
    "allow": ["Bash", "Read", "Glob", "Grep"],
    "deny": []
  }
}
```

**Note:** Session-start hooks require Claude Code configuration. Manual setup in Claude Code settings.json is needed for session-start hooks.

### Step 5: Install Hooks (Manual Step for User)

Document the installation in `novel-factory/.claude/docs/hooks-setup.md`:

```markdown
# Hooks Setup (Manual)

## Claude Code Settings

To enable automated hooks, add to your Claude Code `settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "novel-factory/.claude/hooks/post-chapter-check.sh \"$FILE_PATH\""
      }
    ],
    "Stop": [
      {
        "command": "novel-factory/.claude/hooks/session-stop-archive.sh"
      }
    ]
  }
}
```

## Alternative: Direct Shell Execution

For immediate hook execution without Claude Code integration:

```bash
# Run post-chapter check manually
./novel-factory/.claude/hooks/post-chapter-check.sh novel-factory/03_内容仓库/04_正文/ch001.md

# List all hooks
ls -la novel-factory/.claude/hooks/
```
```

- [ ] **Step: Commit**

```bash
git add novel-factory/.claude/hooks/ novel-factory/tools/automated-checks/ novel-factory/.claude/settings.json
git commit -m "feat: add CCGS-style automated hooks for post-chapter validation and session management"
```

---

## Task 3: 8-Section Structured Document Standard

**Goal:** Restructure the "基础层.yaml" and "深度层.md" documents (and all design docs) to follow CCGS's 8-section standard. This improves auditability, reviewer onboarding, and cross-document consistency.

**Files:**
- Modify: `novel-factory/.claude/docs/design-doc-standards.md` (rewrite)
- Create: `novel-factory/.claude/docs/templates/inspiration-baseline-template.md`
- Create: `novel-factory/.claude/docs/templates/inspiration-deep-template.md`
- Create: `novel-factory/.claude/docs/templates/outline-template.md`
- Create: `novel-factory/.claude/docs/templates/chapter-template.md`
- Create: `novel-factory/09_规范文档/文档结构标准.md`

### Step 1: Create the 8-Section Standard Document

Rewrite `novel-factory/.claude/docs/design-doc-standards.md`:

```markdown
# Design Document Standards — 8-Section Structure

> Extends CCGS's Game Design Document standard for novel factory workflows.

## The 8 Required Sections

Every design document (inspiration baseline/deep, outline, stage plan) MUST contain these 8 sections. Missing any section is a BLOCKING finding during review.

### Section 1: Overview (概述)
**Required content:** One-paragraph summary of the document's purpose and scope.
**Template:** "本文档定义____，适用于____阶段，核心目标是____。"

### Section 2: Reader Fantasy (读者体验目标)
**Required content:** The emotional experience intended for the reader at this stage.
**Template:** "读者在此阶段应感受到____，核心情绪弧线为____。"
**Questions to answer:**
- What emotion should dominate this stage?
- What surprises or revelations are planned?
- What tension should build?

### Section 3: Detailed Rules (详细规则)
**Required content:** Concrete rules governing this stage's narrative logic.
**Template:**
```
规则1: ____（描述）
规则2: ____（描述）
规则3: ____（描述）
```
**For outlines:** List structural rules (chapter count, arc segments, cliffhanger positions).
**For chapters:** List consistency rules (character states, timeline markers, location flags).

### Section 4: Formulas & Metrics (公式与指标)
**Required content:** Quantifiable targets for this stage.
**Template:**
```
| 指标 | 目标值 | 说明 |
|------|--------|------|
| 章节字数 | 1500-2500 | 含本章完标记 |
| 情感张力 | ≥7/10 | 高潮章需达到 |
| 伏笔埋入 | ≥2/章 | 新伏笔数量 |
```

### Section 5: Edge Cases (边界情况)
**Required content:** How to handle unusual situations, exceptions, degenerate narrative paths.
**Template:**
```
情况1: ____发生时 → 执行____
情况2: ____发生时 → 执行____
```

### Section 6: Dependencies (依赖关系)
**Required content:** What this document depends on from previous stages/documents.
**Template:**
```
依赖:
  - 前序章节: chXXX-chXXX（内容引用）
  - 大纲锚点: 卷N阶段M（阶段引用）
  - 伏笔引用: {伏笔ID}（伏笔追踪）
```

### Section 7: Tuning Knobs (可调参数)
**Required content:** Configurable values that can be adjusted without structural changes.
**Template:**
```
| 参数 | 默认值 | 可调范围 | 说明 |
|------|--------|---------|------|
| 虐点比例 | 30% | 20-40% | 虐心情节占比 |
| 甜点间隔 | 5章 | 3-8章 | 甜蜜情节间隔 |
| 反派强度 | 7/10 | 5-10 | 冲突强度系数 |
```

### Section 8: Acceptance Criteria (验收标准)
**Required content:** Testable success conditions — how to verify this stage is complete.
**Template:**
```
验收标准:
- [ ] 标准1
- [ ] 标准2
- [ ] 标准3（自动检查）
```
**For chapters:** Include automated check criteria (e.g., "本章完标记存在", "字数≥500").

## Document Type Mappings

| Document | Sections 1-4 | Sections 5-8 |
|----------|-------------|-------------|
| 基础层.yaml | Overview, Reader Fantasy, Detailed Rules, Formulas | Edge Cases, Dependencies, Tuning Knobs, Acceptance Criteria |
| 深度层.md | Overview, Foreshadow Map, Timeline Rules, Narrative Structure | Edge Cases, Foreshadow Dependencies, Knobs, Acceptance Criteria |
| 卷大纲 | Overview, Volume Arc, Chapter Count Rules, Volume Metrics | Edge Cases, Inter-Stage Dependencies, Volume Knobs, Volume Acceptance |
| 阶段大纲 | Overview, Stage Arc, Chapter Breakdown, Stage Metrics | Edge Cases, Outline Dependencies, Stage Knobs, Stage Acceptance |
| 单章正文 | Overview, Chapter Purpose, Consistency Rules, Chapter Metrics | Edge Cases, Previous/Next Chapter Links, Chapter Knobs, Chapter Acceptance |

## Review Checklist for Editors

When reviewing any design document:
```
[ ] Section 1 (Overview): Exists and is one paragraph
[ ] Section 2 (Reader Fantasy): Emotional target stated
[ ] Section 3 (Detailed Rules): At least 3 concrete rules
[ ] Section 4 (Formulas): Metrics are quantifiable
[ ] Section 5 (Edge Cases): Covers at least 2 edge situations
[ ] Section 6 (Dependencies): References at least 1 prior document
[ ] Section 7 (Tuning Knobs): At least 2 tunable parameters
[ ] Section 8 (Acceptance Criteria): At least 3 checkable criteria
[ ] No placeholder text (TBD, TODO without tracking, "..." without meaning)
```

## Migration Guide

Apply to existing documents incrementally:
1. New documents — use 8-section standard immediately
2. In-review documents — convert before approval
3. Existing approved documents — no migration required unless modified

---

*Document version: v1.0*
*Adapted from CCGS (Claude-Code-Game-Studios-English)*
*Created: 2026-05-19*
```

### Step 2: Create Templates

Create `novel-factory/.claude/docs/templates/inspiration-baseline-template.md`:

```markdown
# 基础层.yaml — 灵感基准模板

## Section 1: Overview (概述)
本文档定义 [项目名称] 的基础创意框架，适用于立项阶段，核心目标是 [一句话目标]。

## Section 2: Reader Fantasy (读者体验目标)
读者在此阶段应感受到 [核心情绪]，核心情感弧线为 [弧线描述]。

## Section 3: Detailed Rules (详细规则)
- 类型定位: [类型]
- 核心冲突: [冲突1], [冲突2]
- 卖点: [卖点1], [卖点2], [卖点3]
- 风格禁忌: [禁忌1], [禁忌2]
- 受众分析: [目标读者群体]

## Section 4: Formulas & Metrics (公式与指标)
| 指标 | 目标值 | 说明 |
|------|--------|------|
| 总章节数 | 300-400 | 预估 |
| 单章字数 | 1500-2500 | 含本章完 |
| 情感峰值 | ≥3/卷 | 每卷高潮次数 |
| 伏笔埋入率 | ≥80% | 回收率目标 |

## Section 5: Edge Cases (边界情况)
- 情况1: [极端情节] 发生时 → [处理方式]
- 情况2: [市场反馈] 发生时 → [调整方式]

## Section 6: Dependencies (依赖关系)
依赖:
  - 灵感深度层: 深度层.md（同期生成）
  - 无前序依赖

## Section 7: Tuning Knobs (可调参数)
| 参数 | 默认值 | 可调范围 | 说明 |
|------|--------|---------|------|
| 虐点比例 | 30% | 20-40% | 情感虐点占比 |
| 甜点间隔 | 5章 | 3-8章 | 甜蜜情节间隔 |
| 反派强度 | 7/10 | 5-10 | 冲突强度系数 |
| 更新节奏 | 2章/周 | 1-3章/周 | 发布频率 |

## Section 8: Acceptance Criteria (验收标准)
验收标准:
- [ ] 类型定位清晰，有明确受众
- [ ] 核心冲突能支撑300+章
- [ ] 卖点具有市场差异化
- [ ] 无风格禁忌违规
- [ ] 参数配置在可调范围内

---
*模板版本: v1.0*
*Created: 2026-05-19*
```

Create `novel-factory/.claude/docs/templates/inspiration-deep-template.md`:

```markdown
# 深度层.md — 灵感深度模板

## Section 1: Overview (概述)
本文档定义 [项目名称] 的深度创作规范，包含世界观、叙事结构、伏笔布局，适用于审核和汇总阶段。

## Section 2: Foreshadow Map (伏笔地图)
### 核心伏笔
| 伏笔ID | 首次埋入 | 计划回收 | 回收方式 |
|--------|---------|---------|---------|
| FP001 | chXXX | chXXX | [方式] |
| FP002 | chXXX | chXXX | [方式] |

### 伏笔层级
- 一级伏笔（核心悬念）: [列表]
- 二级伏笔（章节悬念）: [列表]
- 三级伏笔（情感点缀）: [列表]

## Section 3: Timeline Rules (时间线规则)
```
[纪元/时间线标记规则]
- 星历纪元: [公元/纪年方式]
- 力量觉醒时间点: [锚定章节]
- 关键历史事件时间轴: [列表]
```

## Section 4: Narrative Structure (叙事结构)
### 卷结构
- 卷1 [卷名]: ch001-ch120 — 核心弧线: [弧线]
- 卷2 [卷名]: ch121-ch240 — 核心弧线: [弧线]
- 卷3 [卷名]: ch241-ch360 — 核心弧线: [弧线]

### 高潮分布
| 卷 | 高潮位置 | 情感类型 | 预期强度 |
|----|---------|---------|---------|
| 卷1 | ch060, ch120 | [类型] | 9/10 |
| 卷2 | ch180, ch240 | [类型] | 10/10 |
| 卷3 | ch300, ch360 | [类型] | 10/10 |

## Section 5: Edge Cases (边界情况)
- 情况1: 伏笔无法按时回收 → [替代方案]
- 情况2: 时间线冲突 → [重置/解释机制]
- 情况3: 角色死亡需撤回 → [复活规则]

## Section 6: Foreshadow Dependencies (伏笔依赖)
伏笔依赖:
  - FP001 依赖: 世界观设定-力量体系
  - FP002 依赖: FP001（递进关系）
  - 跨卷依赖: 卷2反派动机 ← 卷1背景故事

## Section 7: Tuning Knobs (可调参数)
| 参数 | 默认值 | 可调范围 | 说明 |
|------|--------|---------|------|
| 伏笔密度 | 3伏笔/章 | 2-5 | 新伏笔埋入数 |
| 回收延迟 | ≤30章 | 20-50章 | 伏笔到回收的章数差 |
| 悬念释放节奏 | 5章/次 | 3-8章 | 小悬念频率 |

## Section 8: Acceptance Criteria (验收标准)
验收标准:
- [ ] 伏笔地图包含至少10个核心伏笔
- [ ] 每个伏笔有明确的回收计划
- [ ] 时间线无矛盾（需运行 check_timeline.py）
- [ ] 高潮分布均衡（每卷≥2个高潮）
- [ ] 叙事结构匹配读者体验目标

---
*模板版本: v1.0*
*Created: 2026-05-19*
```

### Step 3: Create Chapter Template

Create `novel-factory/.claude/docs/templates/chapter-template.md`:

```markdown
# 正文模板 — 单章标准结构

## Section 1: Overview (概述)
第[X]章 [章名] — 本章服务于[核心弧线]，核心任务是[任务描述]。

## Section 2: Chapter Purpose (章节目标)
- 核心任务: [本章要推进的情节]
- 情感目标: [本章结尾应给读者的情绪]
- 信息目标: [本章需传递的关键信息]

## Section 3: Consistency Rules (一致性规则)
- 本章时间点: [在整体时间线中的位置]
- 地点/场景: [物理位置]
- 人物状态: [关键人物的状态快照]
  - 主角: [状态]
  - 女主: [状态]
  - 关键NPC: [状态]
- 进行中伏笔: [本章涉及的伏笔ID列表]

## Section 4: Chapter Metrics (章节指标)
| 指标 | 目标值 | 实际值 |
|------|--------|--------|
| 字数 | 1500-2500 | [完成后填入] |
| 情感张力 | 5-8/10 | [完成后填入] |
| 新伏笔埋入 | 0-2 | [完成后填入] |
| 伏笔回收 | 0-1 | [完成后填入] |

## Section 5: Edge Cases (边界情况)
- 场景切换冲突: [处理方式]
- 角色状态矛盾: [处理方式]

## Section 6: Dependencies (依赖关系)
- 前序章节: ch[N-1] — [关键引用]
- 后继章节: ch[N+1] — [关键铺垫]
- 大纲锚点: [阶段大纲中的位置]

## Section 7: Tuning Knobs (可调参数)
| 参数 | 本章值 | 说明 |
|------|--------|------|
| 虐点强度 | 0-10 | 情感虐点强度 |
| 甜点位置 | 章首/章中/章末 | 甜景安置位置 |
| 悬念强度 | 0-10 | 结尾悬念强度 |

## Section 8: Acceptance Criteria (验收标准)
- [ ] 文件名 chXXX.md 与内容"第X章"一致
- [ ] 包含"本章完"标记
- [ ] 字数≥500字符
- [ ] 无硬编码（人物名/地名一致性）
- [ ] 伏笔埋入/回收已记录到伏笔追踪表

---
*模板版本: v1.0*
*Created: 2026-05-19*
```

### Step 4: Create 规范文档 Entry

Create `novel-factory/09_规范文档/文档结构标准.md` with the same content as the 8-section standard, plus a reference index.

- [ ] **Step: Commit**

```bash
git add novel-factory/.claude/docs/design-doc-standards.md \
         novel-factory/.claude/docs/templates/ \
         novel-factory/09_规范文档/
git commit -m "feat: add 8-section document standard (CCGS reference) with templates"
```

---

## Task 4: Explicit Model Tier Strategy Enhancement

**Goal:** Enhance the existing `model-tier-guide.md` with explicit model declarations in each agent YAML frontmatter, model override commands, and cost optimization guidelines.

**Files:**
- Modify: `novel-factory/.claude/docs/model-tier-guide.md` (enhance with cost optimization section)
- Modify: `novel-factory/.claude/agents/*.md` (add model declaration to each YAML frontmatter)
- Create: `novel-factory/.claude/docs/model-tier-quickref.md` (one-page reference)

### Step 1: Enhance model-tier-guide.md

Append to the existing `model-tier-guide.md` file a new section "Cost Optimization" before the footer:

```markdown
## Cost Optimization Guidelines

### When to Use Haiku (Lowest Cost)
Haiku is sufficient when:
- Task is purely deterministic (format check, counter, regex)
- Task requires only reading and reporting (no generation)
- Task output can be automatically verified (no subjective judgment)

### When to Use Sonnet (Default — Balanced)
Sonnet is required when:
- Task involves creative judgment (writing, outlining)
- Task requires understanding context across multiple files
- Task outcome is subjective (quality assessment, readability)
- Task involves coordinating multiple concerns

### When to Use Opus (Highest Cost)
Opus is required when:
- Task spans 3+ departments coordination
- Decision could cause major rework (outline推翻)
- Task requires full-novel-context understanding
- High-stakes arbitration (弃书率>80%)
- LLM-based analysis (character arc, emotional rhythm)

### Cost Budget per 100 Chapters

| Task | Model | Estimated Cost (USD) |
|------|-------|---------------------|
| 章节写作（常规） | Sonnet | ~$0.50/chapter |
| 章节写作（高潮） | Opus | ~$2.00/chapter |
| 格式检查 | Haiku | ~$0.01/chapter |
| 质量检查（规则） | Haiku | ~$0.05/chapter |
| 质量检查（情感） | Sonnet | ~$0.30/chapter |
| 伏笔追踪（LLM） | Opus | ~$1.00/chapter |
| 读者评论 | Haiku | ~$0.02/chapter |
| 汇总编译 | Sonnet | ~$0.50/volume |

### Model Override Commands

In emergency or specialized scenarios, the controller can override the default model:

```bash
# Force Opus for critical scene writing
./run_workflow.sh assign --model opus 作家A ch150

# Force Haiku for batch format checking
./run_workflow.sh batch --model haiku ch001-ch050

# Force Sonnet for outline review
./run_workflow.sh review --model sonnet outline_vol1
```

### Model Declaration in Agent YAML

Each agent file MUST declare its default model in YAML frontmatter:

```yaml
---
model: sonnet  # default model for this agent
model_override_allowed: true  # whether controller can override
cost_tier: medium  # for cost tracking
---
```

| Tier | Model | Cost Budget |
|------|-------|-----------|
| low | haiku | <$0.10/chapter equivalent |
| medium | sonnet | $0.10-$1.00/chapter equivalent |
| high | opus | >$1.00/chapter equivalent |

---

*Document version: v1.1*
*Enhancement added: 2026-05-19*
```

### Step 2: Add Model Declarations to Agent YAML

For each agent file in `novel-factory/.claude/agents/`, add YAML frontmatter if missing, or update if present.

Example for `novel-factory/.claude/agents/主控调度.md`:
```yaml
---
model: sonnet
model_override_allowed: false
cost_tier: medium
department: _global
description: Main controller for novel factory workflow orchestration
---
```

Example for `novel-factory/.claude/agents/作家部门.md`:
```yaml
---
model: sonnet
model_override_allowed: true
cost_tier: medium
department: writer
description: Novel body writing — 10 concurrent writers
specialties:
  - sonnet: 常规章节写作
  - opus: 高潮/关键场景写作
  - haiku: 自我格式检查
---
```

Do this for all 6 department agents.

### Step 3: Create Quick Reference

Create `novel-factory/.claude/docs/model-tier-quickref.md`:

```markdown
# Model Tier Quick Reference

## Default Model Map

| Agent | Default | Override? | Cost Tier |
|-------|---------|-----------|-----------|
| 主控调度 | Sonnet | No | Medium |
| 灵感部门 | Sonnet | Yes | Medium |
| 作家部门 | Sonnet | Yes | Medium |
| 审核部门 | Sonnet | Yes | Medium |
| 读者部门 | Haiku | Yes | Low |
| 汇总部门 | Sonnet | Yes | Medium |

## Task → Model Decision Tree

```
Is the task deterministic (format check, counter)?
├─ YES → Use Haiku
└─ NO ↓
Does the task require creative judgment or context understanding?
├─ YES → Use Sonnet
└─ NO ↓
Is the task a high-stakes cross-department decision?
├─ YES → Use Opus
└─ NO → Use Sonnet
```

## Cost Budget Target

| Phase | Budget |
|-------|--------|
| Per 100 chapters | <$150 USD |
| Full novel (360 chapters) | <$540 USD |

---

*Quick reference — full details in model-tier-guide.md*
```

- [ ] **Step: Commit**

```bash
git add novel-factory/.claude/docs/model-tier-guide.md \
         novel-factory/.claude/docs/model-tier-quickref.md \
         novel-factory/.claude/agents/
git commit -m "feat: enhance model tier strategy with cost optimization and agent declarations"
```

---

## Task 5: Review Modes (full/lean/solo)

**Goal:** Add configurable review intensity modes to the workflow, matching CCGS's `full/lean/solo` pattern. This allows flexible quality control based on project phase and resource constraints.

**Files:**
- Modify: `novel-factory/workflow_state.json` (add review_modes section)
- Modify: `novel-factory/run_review.sh` (add --mode flag)
- Create: `novel-factory/.claude/docs/review-modes.md`

### Step 1: Add Review Modes to workflow_state.json

Add to `workflow_state.json` under a new top-level key `review_modes`:

```json
{
  "review_modes": {
    "full": {
      "description": "All 10+1 quality dimensions, all reviewers, highest rigor",
      "quality_threshold": "S级 (≥90%)",
      "reviewer_count": 10,
      "dimensions": [
        "naming_consistency",
        "content_integrity",
        "chapter_repeat",
        "character_state",
        "timeline",
        "plot_relevance",
        "foreshadow_tracking",
        "scene_logic",
        "emotional_rhythm",
        "dialogue_style",
        "character_arc"  // LLM
      ],
      "iterations_max": 3,
      "approval_criteria": "全审核员一致通过 或 未解决意见≤3条"
    },
    "lean": {
      "description": "Key dimensions only, faster turnaround, 5 reviewers",
      "quality_threshold": "A级 (≥70%)",
      "reviewer_count": 5,
      "dimensions": [
        "naming_consistency",
        "content_integrity",
        "chapter_repeat",
        "character_state",
        "plot_relevance",
        "scene_logic"
      ],
      "iterations_max": 2,
      "approval_criteria": "≥70%审核员通过 且 无P0问题"
    },
    "solo": {
      "description": "Self-review only, no external reviewers, fastest",
      "quality_threshold": "B级 (≥50%)",
      "reviewer_count": 1,
      "dimensions": [
        "naming_consistency",
        "content_integrity"
      ],
      "iterations_max": 1,
      "approval_criteria": "自评≥B级 无P0问题"
    }
  },
  "active_review_mode": "full"
}
```

### Step 2: Update run_review.sh with --mode Flag

Add to `run_review.sh`:

```bash
# Add near the top of run_review.sh
REVIEW_MODE="${REVIEW_MODE:-full}"

show_help() {
    echo "Usage: ./run_review.sh [command] [options]"
    echo "Commands:"
    echo "  batch <chapter_range>    Batch review (default: 10 chapters)"
    echo "  assign <reviewer> <chapters>  Assign single reviewer"
    echo "  status                  Show current review status"
    echo ""
    echo "Options:"
    echo "  --mode <full|lean|solo>  Set review intensity (default: full)"
    echo "  --help                  Show this help"
}

# Parse --mode flag
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            REVIEW_MODE="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

# Validate mode
if [[ ! "$REVIEW_MODE" =~ ^(full|lean|solo)$ ]]; then
    echo "[ERROR] Invalid review mode: $REVIEW_MODE"
    echo "Valid modes: full, lean, solo"
    exit 1
fi

echo "[INFO] Review mode: $REVIEW_MODE"
```

### Step 3: Create Review Modes Documentation

Create `novel-factory/.claude/docs/review-modes.md`:

```markdown
# Review Modes — Full / Lean / Solo

> Adapted from CCGS's review intensity pattern.

## Overview

Three configurable review intensities allow the novel factory to balance quality rigor against throughput speed based on project phase and resource availability.

## Mode Comparison

| Aspect | Full | Lean | Solo |
|--------|------|------|------|
| **Quality bar** | S级 (≥90%) | A级 (≥70%) | B级 (≥50%) |
| **Reviewers** | 10 concurrent | 5 concurrent | Self only |
| **Dimensions** | 10+1 (all) | 6 (key rules) | 2 (basic) |
| **LLM-based checks** | Yes (character_arc) | No | No |
| **Max iterations** | 3 | 2 | 1 |
| **Throughput** | Slowest | Balanced | Fastest |
| **Use when** | Final quality gate, major release | Batch review, iterative improvement | Early drafts, self-check |

## Dimension Mapping by Mode

| Dimension | Full | Lean | Solo |
|-----------|------|------|------|
| naming_consistency | ✅ | ✅ | ✅ |
| content_integrity | ✅ | ✅ | ✅ |
| chapter_repeat | ✅ | ✅ | ❌ |
| character_state | ✅ | ✅ | ❌ |
| timeline | ✅ | ❌ | ❌ |
| plot_relevance | ✅ | ✅ | ❌ |
| foreshadow_tracking | ✅ | ❌ | ❌ |
| scene_logic | ✅ | ✅ | ❌ |
| emotional_rhythm | ✅ | ❌ | ❌ |
| dialogue_style | ✅ | ❌ | ❌ |
| character_arc (LLM) | ✅ | ❌ | ❌ |

## When to Use Each Mode

### Full Review (Default)
- Major milestones: volume finals, novel completion
- High-stakes chapters: climaxes, emotional peaks
- When quality is non-negotiable (e.g., publication-ready)
- Resource cost: ~$15-30 per 10-chapter batch

### Lean Review
- Regular batch reviews (weekly cycles)
- When time-to-market matters more than perfection
- Mid-project iteration tracking
- Resource cost: ~$5-10 per 10-chapter batch

### Solo Review
- First draft self-check before submission
- When writer wants a quick sanity check
- Exploratory chapters with high revision probability
- Resource cost: ~$0.50 per 10-chapter batch

## Switching Modes

```bash
# Switch to lean mode for faster iteration
REVIEW_MODE=lean ./run_review.sh batch ch101-ch110

# Check current mode
cat novel-factory/workflow_state.json | grep active_review_mode

# Mode is persisted per workflow state
```

## Mode Transition Rules

| Transition | Allowed? | Notes |
|------------|----------|-------|
| solo → lean | ✅ | After self-check passes |
| lean → full | ✅ | After lean review reveals issues |
| full → lean | ✅ | After critical path stabilized |
| lean → solo | ❌ | Cannot skip human review entirely |
| solo → full | ✅ | Jump to highest rigor anytime |

---

*Document version: v1.0*
*Adapted from CCGS review modes*
*Created: 2026-05-19*
```

- [ ] **Step: Commit**

```bash
git add novel-factory/workflow_state.json \
         novel-factory/run_review.sh \
         novel-factory/.claude/docs/review-modes.md
git commit -m "feat: add review modes (full/lean/solo) per CCGS reference"
```

---

## Task 6: Registry Architecture

**Goal:** Introduce a state ownership registry (matching CCGS's `architecture.yaml` pattern) that defines which agent owns which state fields, who can modify what, and forbidden state transitions. This prevents conflicting writes and clarifies the data ownership model.

**Files:**
- Create: `novel-factory/docs/registry/state-ownership.yaml`
- Modify: `novel-factory/workflow_state.json` (add ownership annotations)
- Modify: `novel-factory/.claude/docs/coordination-rules.md` (reference registry)
- Create: `novel-factory/docs/registry/forbidden-patterns.yaml`

### Step 1: Create State Ownership Registry

Create `novel-factory/docs/registry/state-ownership.yaml`:

```yaml
# State Ownership Registry
# Defines which agent "owns" each state field, who can modify it,
# and what transitions are forbidden.

version: "v1.0"
created: "2026-05-19"

# Top-level state fields and their ownership
state_fields:
  version:
    owner: "main_controller"
    read_access: ["any_agent"]
    write_access: ["main_controller"]
    validation: "semver"

  current_phase:
    owner: "main_controller"
    read_access: ["any_agent"]
    write_access: ["main_controller"]
    validation: "enum:PHASE_*"

  current_step:
    owner: "main_controller"
    read_access: ["any_agent"]
    write_access: ["main_controller"]
    validation: "enum:STEP_*"

  project_status:
    owner: "main_controller"
    read_access: ["any_agent"]
    write_access: ["main_controller"]
    sub_fields:
      name:
        owner: "inspiration_dept"
        read_access: ["writer_dept", "reviewer_dept"]
      total_chapters:
        owner: "writer_dept"
        read_access: ["any_agent"]
      emotion_quality:
        owner: "reviewer_dept"
        read_access: ["any_agent"]
      phase:
        owner: "main_controller"

  review_queue:
    owner: "reviewer_dept"
    read_access: ["writer_dept", "reader_dept", "main_controller"]
    write_access: ["reviewer_dept", "main_controller"]
    sub_fields:
      pending:
        owner: "reviewer_dept"
        read_access: ["writer_dept"]
      in_review:
        owner: "reviewer_dept"
      completed:
        owner: "reviewer_dept"
        read_access: ["writer_dept", "reader_dept", "summary_dept"]

  phases:
    owner: "main_controller"
    read_access: ["inspiration_dept", "writer_dept", "reviewer_dept"]
    write_access: ["main_controller"]
    # Each phase sub-field owned by respective department
    sub_fields:
      PHASE_1_LAUNCH:
        owner: "inspiration_dept"
      PHASE_2_OUTLINE:
        owner: "writer_dept"
      PHASE_3_VOLUME:
        owner: "writer_dept"
      PHASE_4_STAGE:
        owner: "writer_dept"
      PHASE_5_BODY:
        owner: "writer_dept"
      PHASE_6_SUMMARY:
        owner: "summary_dept"
      PHASE_7_CLOSE:
        owner: "main_controller"

  agent_tasks:
    owner: "main_controller"
    read_access: ["any_agent"]
    write_access: ["main_controller", "dispatched_agent"]
    validation: "task_id_required"

# Forbidden state transitions
forbidden_transitions:
  - from: "PHASE_5_BODY"
    to: "PHASE_3_VOLUME"
    reason: "Cannot regress to outline after body writing has started"

  - from: "PHASE_7_CLOSE"
    to: "PHASE_5_BODY"
    reason: "Cannot reopen closed project"

  - trigger: "step_status: completed"
    without: "agent_tasks.*.status: verified"
    reason: "Cannot mark step complete without verified agent task"

  - field: "project_status.emotion_quality"
    change: "任何修改"
    without: "review_queue.pending: empty"
    reason: "Cannot change quality rating while reviews are pending"

# File ownership (mirrors state ownership)
file_ownership:
  "03_内容仓库/04_正文/ch*.md":
    owner: "writer_dept"
    read_access: ["reviewer_dept", "reader_dept", "summary_dept"]
    write_access: ["writer_dept", "main_controller"]
    validation_script: "tools/automated-checks/post-chapter-check.sh"

  "01_灵感库/*/基础层.yaml":
    owner: "inspiration_dept"
    read_access: ["writer_dept", "main_controller"]
    write_access: ["inspiration_dept"]

  "01_灵感库/*/深度层.md":
    owner: "inspiration_dept"
    read_access: ["writer_dept", "reviewer_dept", "summary_dept"]
    write_access: ["inspiration_dept"]

  "06_意见仓库/*":
    owner: "reviewer_dept"
    read_access: ["writer_dept", "main_controller"]
    write_access: ["reviewer_dept", "writer_dept"]

  "07_汇总仓库/*":
    owner: "summary_dept"
    read_access: ["main_controller"]
    write_access: ["summary_dept"]
```

### Step 2: Create Forbidden Patterns

Create `novel-factory/docs/registry/forbidden-patterns.yaml`:

```yaml
# Forbidden Patterns Registry
# Patterns that are never allowed in the novel factory.

version: "v1.0"
created: "2026-05-19"

# Agent behavior prohibitions
agent_prohibitions:
  - pattern: "主控直接修改文件"
    severity: "critical"
    reason: "主控不得自己改文件 — must use Agent to execute modifications"
    enforcement: "workflow_state.json validation"

  - pattern: "跳过审核直接标记完成"
    severity: "critical"
    reason: "审核完成后必须进入修改主持流程 — no skipping"
    enforcement: "workflow_state.json step_status validation"

  - pattern: "单作家串行修改10章"
    severity: "high"
    reason: "Must use parallel writers — one chapter per writer minimum"
    enforcement: "run_workflow.sh validation"

# State transition prohibitions
state_prohibitions:
  - pattern: "step_status: completed without verified agent task"
    severity: "critical"
    reason: "Cannot mark complete without TaskOutput verification"
    enforcement: "run_workflow.sh verify command"

  - pattern: "未经Agent执行修改即改写workflow_state.json"
    severity: "critical"
    reason: "No direct state writes — all changes via agent tasks"
    enforcement: "coordination-rules.md"

# Content prohibitions
content_prohibitions:
  - pattern: "ch*.md without 本章完 marker"
    severity: "high"
    enforcement: "post-chapter-check.sh hook"

  - pattern: "ch*.md filename != content chapter number"
    severity: "high"
    enforcement: "check_naming.sh"

  - pattern: "伏笔首次埋入后超过50章未回收"
    severity: "medium"
    enforcement: "check_plot_device_tracking.py"
```

### Step 3: Update Coordination Rules to Reference Registry

Add to `novel-factory/.claude/docs/coordination-rules.md` after the existing content:

```markdown
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

---

*Last updated: 2026-05-19*
*Registry reference added per CCGS architecture.yaml pattern*
```

- [ ] **Step: Commit**

```bash
git add novel-factory/docs/registry/ \
         novel-factory/workflow_state.json \
         novel-factory/.claude/docs/coordination-rules.md
git commit -m "feat: add registry architecture (state ownership + forbidden patterns) per CCGS reference"
```

---

## Task 7: Collaborative Workflow Enhancement

**Goal:** Introduce CCGS's "Question → Options → Decision → Draft → Approval" workflow for major decision points in the novel factory (inspiration approval, outline acceptance, review verdicts).

**Files:**
- Modify: `novel-factory/.claude/docs/coordination-rules.md` (add collaborative workflow section)
- Create: `novel-factory/.claude/docs/templates/decision-proposal-template.md`

### Step 1: Add Collaborative Workflow to Coordination Rules

Append to `novel-factory/.claude/docs/coordination-rules.md`:

```markdown
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

*Last updated: 2026-05-19*
*Collaborative workflow added per CCGS reference*
```

### Step 2: Create Decision Proposal Template

Create `novel-factory/.claude/docs/templates/decision-proposal-template.md`:

```markdown
# Decision Proposal — {Decision Title}

**Proposer:** {Agent Name}
**Date:** {YYYY-MM-DD}
**Decision Point:** {STEP_XX / Phase name}
**Status:** PROPOSED / APPROVED / REJECTED

## 1. Context

{Describe the situation that requires a decision. Why is this decision needed now?}

## 2. Questions for Clarification

- ❓ Question 1
- ❓ Question 2
- ❓ Question 3

## 3. Options

### Option A: {Option Name}
**Description:** {What this option entails}
**Pros:**
- {Pro 1}
- {Pro 2}
**Cons:**
- {Con 1}
- {Con 2}
**Theory:** {Theoretical grounding (e.g., "Based on Bartle player types...")}

### Option B: {Option Name}
**Description:** {What this option entails}
**Pros:**
- {Pro 1}
- {Pro 2}
**Cons:**
- {Con 1}
- {Con 2}
**Theory:** {Theoretical grounding}

### Option C: {Option Name} (if applicable)
...

## 4. Recommendation

{Based on the analysis, the agent recommends Option X because...}

## 5. Decision

```
✅ Decision: [Option A / Option B / Option C / Custom]
```

**Decided by:** {Name}
**Decision date:** {YYYY-MM-DD}
**Rationale:** {Brief rationale for the decision}

## 6. Implementation Plan

{If approved, how will this be executed?}

---

*Template version: v1.0*
*Created: 2026-05-19*
```

- [ ] **Step: Commit**

```bash
git add novel-factory/.claude/docs/coordination-rules.md \
         novel-factory/.claude/docs/templates/decision-proposal-template.md
git commit -m "feat: add collaborative decision workflow (CCGS pattern) to coordination rules"
```

---

## Implementation Order

Implement Tasks in this order (dependencies noted):

```
1. Skill System Standardization  (foundation for all)
2. Automated Hook System        (independent, high value)
3. 8-Section Document Standard  (independent)
4. Model Tier Enhancement        (independent)
5. Review Modes                  (depends on Task 4 model system)
6. Registry Architecture        (high complexity, do last)
7. Collaborative Workflow       (can start after Task 3, parallel with others)
```

## Overall Commit Message (after all tasks)

```bash
git commit -m "feat: adopt CCGS reference improvements

- Skill system standardization with behavioral specs
- Automated hooks for post-chapter validation
- 8-section structured document standard
- Model tier strategy with cost optimization
- Review modes (full/lean/solo)
- Registry architecture (state ownership + forbidden patterns)
- Collaborative decision workflow

BREAKING: None — all changes backward compatible with v3.0 workflow"
```

---

## Self-Review Checklist

After writing the complete plan, verify:

1. **Spec coverage:** Can you point to a task that implements each of the 6 improvements?
   - [ ] Task 1: Skill System Standardization ✅
   - [ ] Task 2: Automated Hook System ✅
   - [ ] Task 3: 8-Section Document Standard ✅
   - [ ] Task 4: Model Tier Enhancement ✅
   - [ ] Task 5: Review Modes ✅
   - [ ] Task 6: Registry Architecture ✅

2. **Placeholder scan:** No "TBD", "TODO", or vague implementation steps remain

3. **Type consistency:** File paths, command names, and field names are consistent across tasks

4. **Backward compatibility:** All improvements extend existing v3.0 workflow without breaking changes

5. **Measurable outcomes:** Each task has acceptance criteria that can be verified

---

## Execution Options

**Plan complete and saved to `docs/superpowers/plans/2026-05-19-ccgs-reference-improvements.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - Dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**