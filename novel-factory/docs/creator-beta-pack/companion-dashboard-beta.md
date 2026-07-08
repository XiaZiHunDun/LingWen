# 陪伴模式 · Dashboard Beta 走通

> 与 [`companion-walkthrough-checklist.md`](../companion-walkthrough-checklist.md) 配套；本节仅覆盖 **Dashboard** 能力（v7.0 基线）。

## 打开创作页

```
http://localhost:8765/?nav=write
```

- [ ] 顶部导航：**今日** / **创作** / **工具箱**（Human-first IA；创作即书桌）
- [ ] **导出 / 发布**：human-first 书桌顶栏 `export-btn` / `publish-btn` 可见
- [ ] 模式徽章显示 **陪伴**
- [ ] 向导默认折叠；首次未完成步骤时自动展开（`wizard_expand_if_incomplete`）

## 写栏（书桌）

- [ ] ch001 显示字数 / 已写状态
- [ ] **正文内嵌编辑**（`chapter_inline_edit`）保存后触发单章 P0 复查
- [ ] 复查问题可点击定位段落；支持键盘导航（↑↓）
- [ ] **脉络 / 记忆** 可通过侧滑抽屉打开（`creator-desk-drawer-pulse` / `creator-desk-drawer-memory`），不必切 Tab

## 脉络（抽屉或 Tab）

- [ ] 可添加 / 锁定 / 保存卷纲
- [ ] 卷纲未保存时出现 **diff 预览**（推进同款，陪伴可选使用）
- [ ] 冲突 409 时显示重新加载

## 设定栏

- [ ] 编辑支柱 → 三路 diff 预览 → 确认保存
- [ ] 合并策略记忆上次选择

## 逻辑审查

- [ ] 一键逻辑审查（`runCreatorLogicCheck`）
- [ ] 问题列表内嵌，**仅展示 P0**（`logic_check_p0_only`）
- [ ] 问题段落高亮与复查样式统一

## 三模式切换（v6.x–v7.0）

- [ ] 切换预览 / 确认对话框 / 撤销提示
- [ ] 快捷键 Alt+Shift+1/2/3 复制 YAML
- [ ] 语音朗读 / 触觉反馈（可选）
- [ ] **无障碍验收清单**（`creation_mode_accessibility_checklist`）≥4 项打勾

## 不包含（陪伴 beta）

- batch 历史面板、卷 pulse 运维图
- 卷纲 diff 分享链接 v3（属推进 advance）

## 相关

- [`creator-onboarding.md`](../creator-onboarding.md)
- [`creator-changelog.md`](../creator-changelog.md)
