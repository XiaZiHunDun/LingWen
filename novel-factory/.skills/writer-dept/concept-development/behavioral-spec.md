# Concept Development - Behavioral Specification

## Entry Condition

When this skill is invoked via `/concept` or "develop concept" and the user wants to:
- Create a new story concept from scratch
- Refine/clarify an existing fuzzy concept
- Validate if a concept is viable

## Exit Condition

When ALL of the following are true:
1. One-sentence logline is crafted and passes the "eye contact" test
2. Theme is clearly defined
3. Type and audience are specified
4. Concept document is saved to `01_灵感库/{project_name}/概念/`

## Input/Output Contract

| Input | Location | Required |
|-------|----------|----------|
| Raw idea | User's description (verbal or text) | Yes |
| Previous concept (if refining) | 01_灵感库/{project_name}/概念/ | No |

| Output | Location | Required |
|--------|----------|----------|
| 概念.md | 01_灵感库/{project_name}/概念/ | Yes |

## Quality Criteria

- [ ] Logline contains all 5 elements: protagonist, flaw, goal, obstacle, consequence
- [ ] Logline passes "眼神测试" (listener asks "然后呢？")
- [ ] Theme is specific and arguable (not generic like "友情" or "成长")
- [ ] Type and audience are clearly specified
- [ ] Concept document follows standard template

## Error Handling

| Error | Response |
|-------|----------|
| Concept too vague | Ask user for more specifics: "主角是什么样的人？他的目标是什么？" |
| No conflict | Point out: "这个概念缺少强烈的冲突，需要重新考虑" |
| Goal too abstract | Refine: "目标需要具体可衡量，比如'赢得比赛'而不是'成为强者'" |

## Logline Formula

```
一个【性格缺陷】的【主角】，为了【目标】，必须克服【阻碍】，否则就会【代价】
```

## Verification Checklist

- [ ] 一句话概括能否在30秒内讲清楚？
- [ ] 主角是否有鲜明的性格缺陷？
- [ ] 目标是否足够具体、可量化？
- [ ] 阻碍是否足够大、足够合理？
- [ ] 代价是否足够严重、足够紧迫？
- [ ] 是否有强烈的戏剧反讽或张力？
- [ ] 讲给别人听时，对方是否追问"然后呢"？