# 陪伴模式真人走通 Checklist

> 一页清单：从零到「写完一章 + P0 守门通过」。  
> 自动化冒烟：`bash scripts/verify-companion-walkthrough.sh`

## 准备

- [ ] `cd novel-factory`
- [ ] 已配置 API Key（仅机写单章时需要；纯手写可跳过）

## 1. 新建陪伴项目

```bash
python lingwen.py init-project my-story \
  --title "我的故事" \
  --protagonist 林晚 \
  --chapters 12

export LINGWEN_PROJECT_ROOT="$(pwd)/projects/my-story"
```

- [ ] `config/project.yaml` 中 `creation_mode: companion`
- [ ] `max_chapter` 符合预期（默认 12）

## 2. 填设定（可选但推荐）

- [ ] 编辑 `docs/novel-pillars.md` — 主角、世界规则、禁忌
- [ ] 浏览 `03_内容仓库/04_正文/ch001_大纲.md` — 确认分章大纲存在

## 3. 主笔第一章

- [ ] 在 `ch001.md` 写入正文（建议 ≥1500 字）
- [ ] 大纲与正文无硬性矛盾

## 4. 逻辑守门

```bash
bash scripts/run-companion-check.sh
```

- [ ] 退出码 0
- [ ] 无 P0（设定矛盾、时间线硬伤）

## 5. Dashboard 创作页（可选）

打开 `http://localhost:8765/?nav=creator`（需 `LINGWEN_SERVE_UI=1` 或 Vite dev）

- [ ] **写** 栏：ch001 显示「已写 / 字数」
- [ ] **脉络** 栏：可添加卷纲、锁定、保存
- [ ] **设定** 栏：编辑支柱 → 变更预览 → 确认保存
- [ ] 若提示「已在别处修改」→ 点 **重新加载**

### Dashboard Beta（v7.0+）

详见 [`creator-beta-pack/companion-dashboard-beta.md`](creator-beta-pack/companion-dashboard-beta.md)

- [ ] 逻辑审查 P0 内嵌 · 复查段落跳转
- [ ] 三模式切换无障碍清单 ≥4 项
- [ ] 冒烟：`bash scripts/verify-creator-beta-pack.sh`

## 6. 日常循环

1. 写下一章正文
2. `run-companion-check.sh`
3. 有 P0 则改文或改设定，直到通过

## 通过标准

| 项 | 标准 |
|----|------|
| 守门 | `lingwen check --fail-severity P0` 通过 |
| 模式 | `creation_mode=companion`，无 judge 压力 |
| 卷纲 | 可选；锁定后偏离列表仅作提醒 |

## 相关文档

- [`creator-onboarding.md`](creator-onboarding.md) — 三模式入门
- [`creator-product-prd-v1.md`](creator-product-prd-v1.md) — 产品 PRD
