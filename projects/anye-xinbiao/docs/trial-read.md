# 《暗夜信标》试读包

> **版本**：trial-read-v1 · 2026-06-18  
> **状态**：发布候选（全书 10 章人审定稿）

## 简介

科幻悬疑短篇。维护工程师**沈柯**在滨海射电阵听见父亲二十年前的信标脉冲，追查 B3 封存实验与「失足落水」真相。

**主题**：听见 vs 装作没听见。

## 章节目录

| 章 | 标题 | 约字数 | 文件 |
|----|------|--------|------|
| 1 | 暗夜信标 | ~1870 | [`../03_内容仓库/04_正文/ch001.md`](../03_内容仓库/04_正文/ch001.md) |
| 2–9 | … | ~2500/章 | `03_内容仓库/04_正文/` |
| 10 | 余波 | ~2765 | [`../03_内容仓库/04_正文/ch010.md`](../03_内容仓库/04_正文/ch010.md) |

## 单文件分发

| 包 | 路径 | 说明 |
|----|------|------|
| 试读 3 章 | `docs/trial-read-ch001-003.md` | 开篇钩子 |
| 全书 | `docs/trial-read-ch001-010.md` | 完整 10 章 |

生成：

```bash
bash scripts/build-trial-read.sh anye-xinbiao 1 3
bash scripts/build-trial-read.sh anye-xinbiao 1 10
```

## 质检

```bash
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/anye-xinbiao"
python lingwen.py check 1-10 --quick
bash scripts/verify-golden-set.sh anye-xinbiao
```

报告：`docs/full-check-report.md`
