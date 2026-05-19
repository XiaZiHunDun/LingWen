# Novel Quality Check - Behavioral Specification

## Entry Condition
When this skill is invoked via `/quality-check` or "run quality check" with a batch of chapters specified (e.g., ch001-ch010).

## Exit Condition
When BOTH of the following are true:
1. Quality report written to `06_意见仓库/04_正文_审核/质量检查报告_{batch}_{timestamp}.md`
2. Report includes all 10 quality dimensions with pass/fail status

## Input/Output Contract

| Input | Location | Required |
|-------|----------|----------|
| Chapter range | User prompt (e.g., ch001-ch010) | Yes |
| 阶段大纲.md | 03_内容仓库/03_阶段大纲/ | Yes |
| 正文 files | 03_内容仓库/04_正文/chXXX.md | Yes |

| Output | Location | Required |
|--------|----------|----------|
| 质量检查报告.md | 06_意见仓库/04_正文_审核/质量检查报告_{batch}_{timestamp}.md | Yes |

## Quality Dimensions (10 total)

| Dimension | Type | Description |
|-----------|------|-------------|
| 命名一致性 | 规则 | 文件名chXXX.md与章节内标题"第X章"一致 |
| 内容完整性 | 规则 | **本章完**标记、字数≥500 |
| 章节重复 | 规则 | 跨章节相似度>80%预警 |
| 人物状态 | 规则 | 性别/生死/形态前后矛盾 |
| 时间线 | 规则 | "年前"与"瞬间"同时出现等明显错误 |
| 情节关联度 | 规则 | 每段落与前后章节的关联程度 |
| 伏笔回收率 | 规则 | 首次出现元素在后续N章内回收 |
| 场景逻辑 | 规则 | 场景转换合理性、孤岛章节检测 |
| 情感节奏 | 规则 | 情绪波动是否合理 |
| 人物弧光 | LLM | 角色弧光完整性（通过Agent调用） |

## Error Handling

| Error | Response |
|-------|----------|
| Chapter file missing | Skip that chapter, note in report as "文件缺失" |
| Chapter range invalid | Error: "章节范围格式错误，请使用ch001-ch010格式" |
| LLM check timeout | Mark as "待复查", continue with rule-based checks |

## Quality Criteria

- [ ] Report covers all 10 dimensions for the specified chapter range
- [ ] Rule-based checks (dimensions 1-9) complete for all chapters
- [ ] LLM-based check (dimension 10) completes or marked as "待复查"
- [ ] Each dimension shows: pass/fail status, count of issues found, severity
- [ ] Report includes chapter-by-chapter breakdown
- [ ] Report includes overall batch score (X/10)
- [ ] Report written to 06_意见仓库/04_正文_审核/ with timestamp