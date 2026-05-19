# Inspiration Generator - Behavioral Specification

## Entry Condition
When this skill is invoked via `/inspiration` or "generate inspiration" and workflow_state.json `current_step` is STEP_01 (灵感生成立项).

## Exit Condition
When BOTH of the following are true:
1. `01_灵感库/{project_name}/基础层.yaml` exists and contains all 8 required sections
2. `01_灵感库/{project_name}/深度层.md` exists and mentions at least 3 foreshadowed plot devices
3. workflow_state.json `step_status` for STEP_01 is updated to completed

## Input/Output Contract

| Input | Location | Required |
|-------|----------|----------|
| Project name | workflow_state.json → project_name | Yes |
| Type preference | User prompt or workflow_state.json | Yes |
| Style禁忌 | User prompt or defaults | No |
| Target audience | User prompt or defaults | No |

| Output | Location | Required |
|--------|----------|----------|
| 基础层.yaml | 01_灵感库/{project_name}/基础层.yaml | Yes |
| 深度层.md | 01_灵感库/{project_name}/深度层.md | Yes |
| 灵感_v{version}.yaml | 01_灵感库/{project_name}/立项/ | Yes |

## Error Handling

| Error | Response |
|-------|----------|
| Project name missing | Query workflow_state.json, prompt user if not found |
| Type preference unclear | Use default type "玄幻" after confirming with user |
| 基础层.yaml incomplete | Return error listing missing sections |
| 深度层.md lacks foreshadowing | Return error requiring at least 3 plot devices |

## Quality Criteria

- [ ] 基础层.yaml has all 8 sections: type, theme, core_conflict, selling_points, audience, style_taboo, character_preview, world_rules
- [ ] 深度层.md mentions at least 3 foreshadowed plot devices with chapter ranges
- [ ] 灵感.v1.0.yaml generated in 立项/ directory
- [ ] workflow_state.json step_status updated for STEP_01
- [ ] No hardcoded content — all generated from templates + user input