# 创作者入门（一页）

> 面向想写完一本书的人，不是工厂 KPI 操作员。  
> 产品说明见 [`creator-product-prd-v1.md`](creator-product-prd-v1.md)。

## 选模式

| 你想怎么写 | 命令 |
|------------|------|
| **自己写**（≤30 章） | `--creation-mode companion` |
| **定纲让机写**（长篇） | `--creation-mode advance` |
| **样章工厂 / 七书同款** | `--creation-mode studio` |

## 1. 新建项目

```bash

# 陪伴：默认，12 章大纲
python lingwen.py init-project my-story \
  --title "我的故事" \
  --protagonist 林晚 \
  --chapters 12

# 推进：80 章上限，先锁卷纲
python lingwen.py init-project my-saga \
  --title "长篇 saga" \
  --creation-mode advance \
  --chapters 80

export LINGWEN_PROJECT_ROOT="$(pwd)/projects/my-story"
```

## 2. 陪伴模式日常

真人走通清单：[`companion-walkthrough-checklist.md`](companion-walkthrough-checklist.md)  
Dashboard Beta：[`creator-beta-pack/README.md`](creator-beta-pack/README.md)  
冒烟脚本：`bash scripts/verify-companion-walkthrough.sh`

1. 改 `docs/novel-pillars.md` 和各章 `chNNN_大纲.md`（可选）
2. **你主笔**写 `chNNN.md` 正文
3. 保存后跑逻辑守门：

```bash
bash scripts/run-companion-check.sh
```

- 只拦 **P0**（设定矛盾、时间线硬伤等）
- **不会**默认弹 LLM 文笔打分

## 3. 推进模式日常

走通清单：[`advance-walkthrough-checklist.md`](advance-walkthrough-checklist.md)  
Dashboard Beta：[`creator-beta-pack/README.md`](creator-beta-pack/README.md)  
冒烟：`bash scripts/verify-advance-walkthrough.sh`

1. 打开 `03_内容仓库/01_全文总体大纲/全局大纲.md`，填**卷纲表**
2. 批量产一章范围：

```bash
export LINGWEN_REAL_LLM=1
bash scripts/run-advance-volume.sh 1 10 10 0.30
```

3. 看卷摘要（不用逐章读全文）：

```text
docs/volume-summary-ch001-010.md
```

4. 有疑点再 `run-companion-check.sh`

### Dashboard（`?nav=write` · Human-first 书桌）

- **导航**：顶部 **今日** / **创作** / **工具箱**；默认进入创作即书桌（`creator-write-workbench`）
- **写**：点击章节行 → 正文编辑；脉络 / 记忆可从侧滑抽屉打开
- **脉络**：编辑卷纲 → **模板库** → 拖拽/合并/拆分 → 锁定 → 保存（抽屉或 Tab）
- **推进**：Preflight + 启动 Batch；完成后自动刷新卷摘要
- **设定**：变更预览 · **三路 diff（磁盘/编辑器/历史）** · 版本历史可恢复
- companion/advance 项目打开 Dashboard 默认进创作页（`nav=write`）

## 4. 和工作室线的关系

- **七样章 / CI / judge≥4.0** = Studio 工厂，继续维护，不是创作者默认路径
- 你的书 `creation_mode: companion` 时，**不必**追 judge 分数
- 要工厂级验收：显式 `--creation-mode studio` 或改 yaml 为 `studio` + `studio_full`

## 5. 常见问题

**Q：我能混用机写和自己写吗？**  
A：可以。陪伴模式照样能 `chapter_production_pilot` 单章机写；守门仍建议 P0-only。

**Q：推进模式预算？**  
A：`run-advance-volume.sh` 第 4 个参数是美元预算；可先小范围试 3 章。

**Q：旧项目没 creation_mode？**  
A：视为 `studio`，行为与升级前一致。
