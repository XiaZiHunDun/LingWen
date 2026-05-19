# Structure Design - Behavioral Specification

## Entry Condition

When this skill is invoked via `/structure-design` or "design structure" and:
- Character biographies exist (from character-design)
- User wants to create or refine story structure

## Exit Condition

When ALL of the following are true:
1. Beat sheet exists covering all 15 beats (or adapted structure)
2. Key structural points are quantified (chapter positions)
3. Second act midpoint and all-is-lost point are clearly defined
4. Foreshadowing plan is integrated (from 深度层.md)

## Input/Output Contract

| Input | Location | Required |
|-------|----------|----------|
| Character bios | 02_作家工作室/作家{N}/ | Yes (for protagonist + antagonist) |
| 深度层.md | 01_灵感库/{project_name}/ | Yes |
| Previous structure (if iteration) | 01_灵感库/结构设计/ | No |

| Output | Location | Required |
|--------|----------|----------|
| 节拍表.md | 01_灵感库/结构设计/{卷 or 全书}/ | Yes |

## Quality Criteria

- [ ] All 14/15 beats are present (Opening Image through Final Image)
- [ ] Midpoint is clearly marked (重大转折)
- [ ] "All Is Lost" moment is clearly defined (致命打击)
- [ ] Chapter positions are quantified for key beats
- [ ] Foreshadowed elements from 深度层.md are referenced
- [ ] B-story is connected to theme argument

## Common Structural Problems

| Problem | Symptom | Solution |
|---------|---------|----------|
| Second Act Sag | Middle section drags | Add midpoint turn, escalate stakes |
| Flat Climax | Final confrontation lacks tension | Extend climax, add cost |
| Broken Arc | Protagonist doesn't change or changes abruptly | Check each beat for progression |
| Weak Villain | Final confrontation is boring | Give villain more筹码 or intelligence |
| Disconnected B-Story | Subplot doesn't relate to main theme | Make subplot support theme argument |

## Beat Timing Reference (for 360-chapter novel)

| Beat | Position | Chapter (approx) |
|------|----------|-----------------|
| Opening Image | 1% | ch001 |
| Theme Stated | 5% | ch018 |
| Setup | 1-10% | ch001-36 |
| Catalyst | 10-12% | ch036-43 |
| Break into Two | 12-25% | ch043-90 |
| B-Story | 15-20% | ch054-72 |
| Fun and Games | 20-50% | ch072-180 |
| Midpoint | 50% | ch180 |
| Bad Guys Close In | 50-75% | ch180-270 |
| All Is Lost | 75% | ch270 |
| Dark Night of Soul | 77% | ch277 |
| Break into Three | 75-80% | ch270-288 |
| Finale | 80-90% | ch288-324 |
| Final Image | 90-100% | ch324-360 |

## Error Handling

| Error | Response |
|-------|----------|
| Character bios missing | Prompt: "请先完成人物设计（/character-design）" |
| No Catalyst event | Error: "缺少激励事件，无法进入第一扇门" |
| Midpoint missing | Error: "缺少中点转折，第二幕将塌陷" |
| All-Is-Lost too early | Warning: "灵魂黑夜应在75%位置，当前位置可能过早" |