# Character Design - Behavioral Specification

## Entry Condition

When this skill is invoked via `/character-design` or "design character" and either:
- Concept document exists (01_灵感库/{project_name}/概念/)
- User wants to create character biographies for existing project

## Exit Condition

When ALL of the following are true:
1. Character biography exists for protagonist
2. Character biography exists for antagonist
3. Character arc is clearly defined (start → end state)
4. Core flaw is identified and impacts story decisions
5. Character documents are saved to appropriate location

## Input/Output Contract

| Input | Location | Required |
|-------|----------|----------|
| 概念.md | 01_灵感库/{project_name}/概念/ | Yes |
| Character list | 基础层.yaml | Yes |

| Output | Location | Required |
|--------|----------|----------|
| {角色名}_小传.md | 02_作家工作室/作家{N}/ | Yes (for each major character) |

## Quality Criteria

- [ ] Protagonist has both external goal AND internal need
- [ ] Core flaw is identified and creates story complications
- [ ] Character arc has clear start and end states
- [ ] Antagonist has reasonable motivation (not pure evil)
- [ ] Each key character's voice is distinguishable

## Character Arc Types

| Type | Description |
|------|-------------|
| 成长型 | 由弱变强、由懦弱变勇敢 |
| 堕落型 | 由好变坏、由正义变邪恶 |
| 悲剧型 | 无法克服，最终毁灭 |
| 觉醒型 | 从不自知到自知 |

## Checklist

- [ ] 主角的外在目标和内在需求是否一致又矛盾？
- [ ] 核心缺陷是否足够明显、足够影响决策？
- [ ] 前史是否能解释当前的缺陷，但不解释太多？
- [ ] 人物弧光的起点和终点是否足够清晰？
- [ ] 每个关键配角是否有存在的理由？
- [ ] 反派的动机是否合理？

## Error Handling

| Error | Response |
|-------|----------|
| No concept document | Prompt user to run `/concept` first |
| Character arc missing | Error: "人物弧光未定义，无法进行人物设计" |
| Motivation unclear | Ask: "这个角色为什么要这样做？" |