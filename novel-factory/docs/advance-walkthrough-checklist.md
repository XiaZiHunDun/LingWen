# 推进模式真人走通 Checklist

> 一页清单：从定卷纲到 batch 预检通过 + 卷摘要就绪。  
> 自动化冒烟：`bash scripts/verify-advance-walkthrough.sh`（无 LLM 花费）

## 准备

- [ ] `cd novel-factory`
- [ ] 了解 `max_chapter` 与卷纲章范围一致

## 1. 新建推进项目

```bash
python lingwen.py init-project my-saga \
  --title "长篇 saga" \
  --protagonist 林晚 \
  --creation-mode advance \
  --chapters 20

export LINGWEN_PROJECT_ROOT="$(pwd)/projects/my-saga"
```

- [ ] `creation_mode: advance`
- [ ] `03_内容仓库/01_全文总体大纲/全局大纲.md` 含卷纲占位表

## 2. 锁定卷纲

在 Dashboard `?nav=creator` **脉络** 栏，或编辑全局大纲卷纲表：

- [ ] 每卷填写章范围 + 核心冲突
- [ ] 首批要写的卷 → **锁定**
- [ ] 保存卷纲（无重叠 alert）

卷操作：

- **合并**：多卷合一（章范围自动并集）
- **拆分**：一卷按章号拆成上下两卷

## 3. Batch 预检（不花钱）

```bash
export LINGWEN_PRODUCTION_MODE=canon
python -m infra.agent_system.chapter_production_batch \
  --preflight-only \
  --start-chapter 1 \
  --end-chapter 3 \
  --max-chapters 3 \
  --dry-run
```

- [ ] Preflight 通过（支柱 + 分章大纲齐全）

## 4. 小范围真 batch（可选）

```bash
export LINGWEN_REAL_LLM=1
bash scripts/run-advance-volume.sh 1 3 3 0.15
```

- [ ] 产出 ch001–ch003 正文
- [ ] 生成 `docs/volume-summary-ch001-003.md`

Dashboard **推进 batch** 面板可 Preflight + 启动（需 `LINGWEN_ALLOW_DASHBOARD_BATCH=1`）。

## 5. 验收与守门

```bash
bash scripts/run-companion-check.sh
```

- [ ] P0 通过
- [ ] 创作页偏离列表可接受（缺章 / 关键词 / 越界）

## 通过标准

| 项 | 标准 |
|----|------|
| 卷纲 | 已锁定卷范围无重叠 |
| 预检 | batch preflight dry-run OK |
| 摘要 | batch 后卷摘要文件存在（真跑时） |
| 守门 | P0 无 blocking |

## 相关文档

- [`creator-onboarding.md`](creator-onboarding.md)
- [`companion-walkthrough-checklist.md`](companion-walkthrough-checklist.md)
