# 《灰域档案》Golden Set

冻结样本章，用于流水线升级后的**回归 smoke**（第三本书 onboarding 基线）。

| 章 | 角色 | baseline quick issues |
|----|------|----------------------|
| ch001 | 开篇钩子（异常信号） | 7 |
| ch003 | 第一幕门槛（踏入迷雾） | 4 |
| ch010 | 终章余波 | 1 |

## 回归

```bash
# 从项目根目录运行
./scripts/verify-golden-set.sh huiyu-dangan
./scripts/run-golden-set-check.sh huiyu-dangan   # 需 MINIMAX_API_KEY
```

## 更新基线

人审定稿后，覆盖 `chapters/chNNN.md` 并更新 `manifest.json`。
