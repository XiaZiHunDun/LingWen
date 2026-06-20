# 《静海日志》Golden Set

冻结样本章，用于流水线升级后的**回归 smoke**（非最终定稿）。

| 章 | 角色 | baseline full-check issues |
|----|------|---------------------------|
| ch001 | 开篇钩子（雾港·沈舟） | 5 |
| ch005 | 中段转折（出港·雾规） | 3 |
| ch010 | 终章收束（静海） | 3 |

## 回归

```bash
cd novel-factory
./scripts/verify-golden-set.sh jinghai-rizhi
```

通过标准：三章均 `[OK]`；LLM quick 检出问题数 ≤ baseline + 2。

## 更新基线

人审定稿后，覆盖 `chapters/chNNN.md` 并更新 `manifest.json` 中的 `full_check_issues_baseline`。
