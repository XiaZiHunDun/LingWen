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