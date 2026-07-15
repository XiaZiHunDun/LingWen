# 《星陨纪元》试读包（开篇抽样）

> **版本**：trial-read-v1 · 2026-06-18  
> **角色**：testbed（工程回归 / 长篇正史 ch001–360）

## 简介

玄幻科幻长篇。**林夜**在陨星坠落后的废土上求生，从孩童流浪到踏上守护之路。试读包仅含正史开篇 3 章，用于对外展示文风与世界观入口。

**主题**：智谋驱动 · 守护者的辩证 · 情感克制而深沉。

## 章节目录（试读）

| 章 | 标题 | 文件 |
|----|------|------|
| 1 | 废土黄昏 | [`../03_内容仓库/04_正文/ch001.md`](../03_内容仓库/04_正文/ch001.md) |
| 2 | 独自求生 | [`../03_内容仓库/04_正文/ch002.md`](../03_内容仓库/04_正文/ch002.md) |
| 3 | 废土求生 | [`../03_内容仓库/04_正文/ch003.md`](../03_内容仓库/04_正文/ch003.md) |

**单文件试读**：[`trial-read-ch001-003.md`](trial-read-ch001-003.md)

## 生成

```bash
cd novel-factory
bash scripts/build-trial-read.sh xingyun-jiyuan 1 3
```

## 质检 / 回归

```bash
export LINGWEN_PROJECT_ROOT="$(pwd)"
bash scripts/verify-golden-set.sh xingyun-jiyuan   # ch001 / ch050 / ch360 抽样
```

## 说明

- 正史上限 **ch360**；ch361+ 为 stress test，见 `03_内容仓库/experimental/README.md`
- 全书归档见 `08_已发布/`、`07_汇总仓库/全文正文/`
- Studio 新书试读索引：[`trial-read-index.md`](trial-read-index.md)
