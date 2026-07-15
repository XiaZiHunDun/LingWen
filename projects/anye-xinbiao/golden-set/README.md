# 《暗夜信标》Golden Set

冻结样本章，用于流水线升级后的**回归 smoke**（非最终定稿）。

| 章 | 角色 | baseline quick issues |
|----|------|----------------------|
| ch001 | 开篇钩子（暗夜信标） | 5 |
| ch005 | 中段转折（顾岚坦白） | 3 |
| ch010 | 终章余波 | 4 |

## 回归

```bash
# 从项目根目录运行
./scripts/run-golden-set-check.sh anye-xinbiao
```

通过标准：三章均 `[OK]`；LLM quick 检出问题数 ≤ baseline + 2。

## 更新基线

人审定稿后，覆盖 `chapters/chNNN.md` 并更新 `manifest.json` 中的 `quick_check_issues_baseline`。
