# Review Opinion Synthesizer - Behavioral Specification

## Entry Condition
When this skill is invoked via `/review-opinion-synthesizer` or "synthesize review opinions" and审核意见 exists in `06_意见仓库/` (any subdirectory).

## Exit Condition
When BOTH of the following are true:
1. Synthesized report written to `06_意见仓库/审核意见综合_{timestamp}.md`
2. workflow_state.json updated with synthesized opinion count

## Input/Output Contract

| Input | Location | Required |
|-------|----------|----------|
| 审核意见 (multiple) | 06_意见仓库/01_全文大纲_审核/ | No |
| 审核意见 (multiple) | 06_意见仓库/02_卷大纲_审核/ | No |
| 审核意见 (multiple) | 06_意见仓库/03_阶段大纲_审核/ | No |
| 审核意见 (multiple) | 06_意见仓库/04_正文_审核/ | No |
| 作家修改记录 | 06_意见仓库/05_作家修改/ | No |

| Output | Location | Required |
|--------|----------|----------|
| 审核意见综合报告 | 06_意见仓库/审核意见综合_{timestamp}.md | Yes |
| P0/P1/P2/P3分类 | Within report | Yes |

## Error Handling

| Error | Response |
|-------|----------|
| No 审核意见 found | Warning: "意见仓库为空，无需综合" |
| Duplicate opinions | Merge duplicates, note count of duplicates |
| Conflicting priorities | Apply higher priority, note conflict |

## Quality Criteria

- [ ] All 审核意见 from all sources are collected
- [ ] Duplicate opinions are merged and counted
- [ ] Opinions are classified by priority: P0/P1/P2/P3
- [ ] P0 issues (硬伤/死锁) are listed first with source reviewer's name
- [ ] Each opinion includes: chapter/section, problem description, suggested fix, source reviewer
- [ ] Report includes total counts per priority level
- [ ] Report written to 06_意见仓库/ with timestamp