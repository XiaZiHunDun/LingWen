# Summary Compiler - Behavioral Specification

## Entry Condition
When this skill is invoked via `/summary-compile` or "compile summary" and phase/volume summary is needed (STEP_19 阶段汇总, STEP_22 卷汇总, or STEP_23 全文汇总).

## Exit Condition
When BOTH of the following are true:
1. Summary document written to appropriate location in `07_汇总仓库/`
2. Summary passes quality check (完整度 ≥50%)

## Input/Output Contract

| Input | Location | Required |
|-------|----------|----------|
| All chapters in range | 03_内容仓库/04_正文/chXXX.md | Yes |
| 阶段大纲.md (if stage) | 03_内容仓库/03_阶段大纲/ | No |
| 卷大纲.md (if volume) | 03_内容仓库/02_卷大纲/ | No |
| 全局大纲.md (if full) | 03_内容仓库/01_全文总体大纲/ | No |

| Output | Location | Required |
|--------|----------|----------|
| 阶段汇总.md | 07_汇总仓库/阶段汇总/卷{n}_阶段{n}_{name}_汇总.md | Yes (STEP_19) |
| 卷汇总.md | 07_汇总仓库/卷{n}_汇总_优化版.md | Yes (STEP_22) |
| 全文汇总.md | 07_汇总仓库/全文汇总_final.md | Yes (STEP_23) |

## Quality Standards

| Grade | Completeness | Action |
|-------|--------------|--------|
| S级 | >90% | Directly pass, mark as final |
| A级 | 70%-90% | Edit and polish, then pass |
| B级 | 50%-70% | Return for rewrite |
| 不合格 | <50% | Reject and redo |

## Error Handling

| Error | Response |
|-------|----------|
| Chapter file missing | Note gap, include placeholder, do not fail |
| Summary <50% complete | Return error: "汇总完整度不足，请补充内容" |
| Logical inconsistency detected | Mark as B级, list inconsistencies in待优化项 |

## Quality Criteria

- [ ] Summary covers all chapters in the specified range
- [ ] Logical consistency maintained (no contradictions)
- [ ] Transitions between sections are smooth
- [ ] No duplicate content from multiple chapter summaries
- [ ] Foreshadowed plot devices are resolved (伏笔回收)
- [ ] Quality check list completed: 逻辑一致性, 过渡平滑, 无重复内容, 伏笔回收
- [ ] Summary graded (S/A/B/不合格) and recorded
- [ ] Summary written to appropriate location in 07_汇总仓库/
- [ ] Version number assigned (v1.0, v2.0, v3.0, final)