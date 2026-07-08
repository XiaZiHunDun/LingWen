# 创作者 Beta 文档包

> v7.0 之后产品级交付：陪伴/推进 walkthrough 与 Dashboard 能力对齐。  
> 自动化验收：`bash scripts/verify-creator-beta-pack.sh`

## 文档地图

| 文档 | 读者 | 用途 |
|------|------|------|
| [`companion-dashboard-beta.md`](companion-dashboard-beta.md) | 陪伴模式作者 | Dashboard 写/脉络/设定 + 逻辑审查 + 无障碍 |
| [`advance-dashboard-beta.md`](advance-dashboard-beta.md) | 推进模式作者 | 卷纲 diff、batch 历史、分享协作 v2、运维摘要 |
| [`../companion-walkthrough-checklist.md`](../companion-walkthrough-checklist.md) | 全员 | CLI 守门真人走通 |
| [`../advance-walkthrough-checklist.md`](../advance-walkthrough-checklist.md) | 全员 | batch 预检真人走通 |
| [`../creator-changelog.md`](../creator-changelog.md) | 维护者 | 创作者线独立变更记录 |
| [`../creator-onboarding-wizard.md`](../creator-onboarding-wizard.md) | 进阶 | 向导 / 模板 / digest 全功能 |

## Beta 范围（v7.0 基线）

- **三模式**：companion / advance / studio 创作页 `?nav=write`（`nav=creator` 仍兼容）
- **v7.0 里程碑**：分享闭环 E2E · batch 运维摘要折叠 · 无障碍验收清单
- **v7.0+ 产品级**：分享协作 v2（diff × 卷级批注）· 本 beta 文档包 · Studio/Creator changelog 解耦

## 快速启动

```bash
cd novel-factory
export LINGWEN_SERVE_UI=1   # 或 Vite dev
# 陪伴
bash scripts/verify-companion-walkthrough.sh
# 推进
bash scripts/verify-advance-walkthrough.sh
# beta 包文档 + 分享协作 v2 冒烟
bash scripts/verify-creator-beta-pack.sh
```

## 通过标准

| 项 | 标准 |
|----|------|
| walkthrough | companion / advance 脚本退出码 0 |
| beta pack | `verify-creator-beta-pack.sh` 退出码 0 |
| Dashboard | 创作页可加载，ui_profile 含 v7.0 + collab v2 标志 |
| 分享协作 v2 | v3 token 含 `n` 批注字段，应用后写入 diff collab notes |
