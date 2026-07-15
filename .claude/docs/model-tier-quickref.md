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