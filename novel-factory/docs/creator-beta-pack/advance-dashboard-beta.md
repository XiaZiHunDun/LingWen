# 推进模式 · Dashboard Beta 走通

> 与 [`advance-walkthrough-checklist.md`](../advance-walkthrough-checklist.md) 配套；本节覆盖 **Dashboard** 全量能力至 v7.0+。

## 打开创作页

```
http://localhost:8765/?nav=write
```

- [ ] 顶部导航：**今日** / **创作** / **工具箱**
- [ ] 顶栏 **导出 / 发布** 可见（human-first 书桌）
- [ ] 模式徽章显示 **推进**
- [ ] 卷级 **pulse** 仅 alert 偏离；可一键生成卷摘要

## 卷纲 diff（A 柱 · v5–v7）

- [ ] 未保存变更 → diff 预览 / 逐项展开 / 卷筛选 / 类型筛选
- [ ] 与全局大纲并排对比、行高亮、跳转编辑
- [ ] 导出：JSON · Markdown · PDF · ZIP · 邮件 · **分享链接**
- [ ] 分享链接解析预览（`#creator-diff=`）
- [ ] 一键应用 · 应用确认 · token 校验 · 冲突合并向导
- [ ] **分享闭环 E2E**：解析 → 应用 → 保存 三步条
- [ ] **分享协作 v2**：v3 token 附带卷级批注 `n`，预览与应用时联动

### 分享协作 v2 操作

1. 在 diff 面板 **协作批注** 区为变更卷填写 `@handle` 批注
2. 点 **复制分享链接**（自动 v3，含 draft + 批注）
3. 协作者打开链接 → 预览变更与批注 → 一键应用
4. 批注合并入项目 `.state/creator_diff_collab_notes.json`

## batch 历史（B 柱 · v5–v7）

- [ ] 历史面板：筛选 / 分组 / 导出 / 重放范围 / 失败重试
- [ ] 图表：成功率 · 耗时分布 · 并发 · 队列深度 · 吞吐率 · 成本效率 · 重试堆叠 · 章节失败热力
- [ ] **运维摘要**折叠区：默认收起，按钮展示一行摘要（任务数 / 成功率 / 均时）

## 推进 batch 面板

- [ ] Preflight + 启动（需 `LINGWEN_ALLOW_DASHBOARD_BATCH=1`）
- [ ] 完成后：卷摘要提示 · 偏离联动 · 自动展开首个偏离章

## 三模式切换（C 柱 · v6–v7）

- [ ] 同陪伴：预览 / 快捷键 / 语音 / 触觉 / ARIA / 减动画 / 固定侧栏
- [ ] **无障碍验收清单**全部打勾

## API 速查

| 能力 | 端点 |
|------|------|
| 卷纲保存 | `PUT /api/creator/volume-plan` |
| diff 预览 | `POST /api/creator/volume-plan/diff-preview` |
| 协作批注 | `GET/PUT /api/creator/diff-collab-notes` |
| batch 历史 | `GET /api/creator/batch-history` |

## 相关

- [`creator-onboarding-wizard.md`](../creator-onboarding-wizard.md)
- [`creator-changelog.md`](../creator-changelog.md)
