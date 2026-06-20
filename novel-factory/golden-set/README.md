# 星陨纪元 · Golden Set（testbed）

抽样章用于 CI 回归，覆盖卷首 / 中段 / 正史末章。

| 章 | 说明 |
|----|------|
| ch001 | 开篇 |
| ch050 | 卷1中段 |
| ch360 | 正史上限 |

```bash
./scripts/verify-golden-set.sh xingyun-jiyuan
```

更新快照：`cp 03_内容仓库/04_正文/chNNN.md golden-set/chapters/`
