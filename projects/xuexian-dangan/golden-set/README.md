# 《雪线档案》Golden Set

冻结样本章，用于流水线升级后的**回归 smoke**（非最终定稿）。

| 章 | 角色 | baseline full-check issues |
|----|------|---------------------------|
| ch001 | 开篇钩子（封山·频道 9） | 3 |
| ch005 | 中段转折（冰舌·抓痕） | 3 |
| ch010 | 终章收束（雪线） | 3 |

## 回归

```bash
# 从项目根目录运行
./scripts/verify-golden-set.sh xuexian-dangan
```

通过标准：三章均 `[OK]`；LLM quick 检出问题数 ≤ baseline + 2。

## 更新基线

人审定稿后，覆盖 `chapters/chNNN.md` 并更新 `manifest.json` 中的 `full_check_issues_baseline`。
