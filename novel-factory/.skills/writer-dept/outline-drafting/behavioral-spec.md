# Outline Drafting - Behavioral Specification

## Entry Condition
When this skill is invoked via `/outline-drafting` or "draft outline" and workflow_state.json `current_step` is STEP_03 (全文大纲初稿), STEP_06 (卷大纲生成), or STEP_10 (阶段大纲生成).

## Exit Condition
When BOTH of the following are true:
1. Output file exists at the appropriate location (卷大纲 or 阶段大纲)
2. workflow_state.json `step_status` for the current step is updated to completed

## Input/Output Contract

| Input | Location | Required |
|-------|----------|----------|
| 基础层.yaml | 01_灵感库/{project_name}/基础层.yaml | Yes |
| 深度层.md | 01_灵感库/{project_name}/深度层.md | Yes |
| Previous outline | 02_卷大纲/ or 03_阶段大纲/ (if iteration) | No |
| workflow_state.json | project root | Yes |

| Output | Location | Required |
|--------|----------|----------|
| 全局大纲.md | 03_内容仓库/01_全文总体大纲/ (STEP_03) | Yes |
| 卷{n}_{名称}.md | 03_内容仓库/02_卷大纲/卷{n}/ (STEP_06) | Yes |
| 卷{n}_阶段{n}_{名称}.md | 03_内容仓库/03_阶段大纲/卷{n}/阶段{n}/ (STEP_10) | Yes |

## Error Handling

| Error | Response |
|-------|----------|
| 基础层.yaml missing | Error: "灵感部门未完成基础层.yaml，请先完成灵感生成" |
| 深度层.md missing | Warning: "深度层.md不存在，将只使用基础层信息" |
| Previous outline missing (iteration) | Proceed with new draft, note as v1.0 |
| Chapter range conflict | Return error listing conflicting ranges |

## Quality Criteria

- [ ] 全局大纲.md exists for STEP_03 with all 3 volumes planned
- [ ] 卷大纲.md exists for STEP_06 covering chapters for that volume
- [ ] 阶段大纲.md exists for STEP_10 covering chapters for that stage
- [ ] All character arcs match those defined in 基础层.yaml
- [ ] Foreshadowed plot devices from 深度层.md are referenced
- [ ] workflow_state.json step_status updated for current step
- [ ] Plot curve includes rising action, climax, falling action per volume/stage