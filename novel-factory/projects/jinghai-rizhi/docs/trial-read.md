# 《静海日志》试读包（ch001–003）

> **版本**：trial-read-v1 · 2026-06-18  
> **状态**：第四本 LLM pilot · 人审修稿

## 简介

沿海悬疑短篇。**沈舟**在禁航日登上旧渡轮「海雾号」，从频道十七的一声呼吸追到被改写的航行记录，最后在灯塔与海面灯语里确认：妹妹可能还活着，但不在岸上。

**主题**：目击 vs 记录。

## 章节目录

| 章 | 标题 | 文件 |
|----|------|------|
| 1 | 雾灯 | [`../03_内容仓库/04_正文/ch001.md`](../03_内容仓库/04_正文/ch001.md) |
| 2 | 盐线 | [`ch002.md`](../03_内容仓库/04_正文/ch002.md) |
| 3 | 灯塔 | [`ch003.md`](../03_内容仓库/04_正文/ch003.md) |

> **状态**：第四本 · **全书 10 章** · 发布候选（人审修稿）

## 单文件分发

| 包 | 路径 |
|----|------|
| 试读 3 章 | `docs/trial-read-ch001-003.md` |
| 全书 10 章 | `docs/trial-read-ch001-010.md` |

```bash
bash scripts/build-trial-read.sh jinghai-rizhi 1 10
```

## 质检

```bash
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/jinghai-rizhi"
python lingwen.py check 1-3 --quick
bash scripts/generate-full-check-report.sh jinghai-rizhi 1 3
```

报告：`docs/full-check-report.md`
