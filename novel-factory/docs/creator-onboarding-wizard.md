# 创作者入门向导（v1.9）

Dashboard 创作页顶部的 **入门向导** 面板，按 `creation_mode` 展示一条可执行的创作路径。

## 入口

- UI：`?nav=creator` 创作页顶部 `data-testid="onboarding-wizard-panel"`
- **Deep link**：`?nav=creator&wizard=1` 自动展开向导并滚动到面板
- **单步 deep-link**：`?nav=creator&wizard=1&step=volume` 高亮并滚动到对应步骤
- **分享链接**：`?nav=creator&wizard=1&done=pillars,volume` 打开时合并已完成步骤
- API：`GET /api/creator/onboarding`

返回字段：

| 字段 | 说明 |
|------|------|
| `steps` | 分步标题与说明 |
| `checklist_doc` | 对应模式的真人走通清单 |
| `smoke_command` | 本地冒烟脚本 |
| `onboarding_doc` | 本文档路径 |

## 三模式路径

### 陪伴（companion）

1. `init-project` 短篇
2. 填写支柱 / 打开创作页
3. 主笔章节
4. `run-companion-check.sh`

清单：`docs/companion-walkthrough-checklist.md`  
冒烟：`bash scripts/verify-companion-walkthrough.sh`

### 推进（advance）

1. `init-project --creation-mode advance`
2. 支柱 → 创作页
3. 模板库 / 锁定卷纲
4. 小范围 batch
5. P0 守门 + 卷摘要

清单：`docs/advance-walkthrough-checklist.md`  
冒烟：`bash scripts/verify-advance-walkthrough.sh`

### 工作室（studio）

1. Studio 项目初始化
2. 支柱 → 创作页管卷纲
3. batch 预检
4. `lingwen check --full`

清单：`docs/studio-creator-hybrid-checklist.md`  
冒烟：`bash scripts/verify-studio-creator-hybrid.sh`

## v1.9 关联能力

- **卷纲模板自定义**：编辑卷纲 →「存为模板」→ `POST /api/creator/volume-plan/templates/save`
- **设定合并策略**：三路 diff 出现冲突时，在保存前选择支柱/大纲保留来源（编辑器 / 磁盘 / 历史快照）

## v2.0 关联能力

- **删除自定义模板**：`DELETE /api/creator/volume-plan/templates/{id}`（仅 `custom_*`）
- **合并策略可视化 diff**：`POST /api/creator/settings-docs/merge-preview` — 展示将写入内容 vs 磁盘
- **向导 deep-link**：`?nav=creator&wizard=1`

## v2.1 关联能力

- **重命名自定义模板**：`PATCH /api/creator/volume-plan/templates/{id}`
- **合并策略预设**：创作页「全选磁盘 / 全选历史 / 全选编辑器」
- **向导进度**：步骤勾选 · `PUT /api/creator/onboarding/progress` · 持久化至 `.state/creator_onboarding_progress.json`

## v2.2 关联能力

- **模板导入/导出**：`GET /api/creator/volume-plan/templates/export` · `POST .../import`
- **向导自动勾选**：检测支柱/卷纲/正文等 · 返回 `auto_completed_step_ids`
- **合并策略记忆**：`GET /api/creator/settings-docs/merge-preferences` · 保存设定时写入 `.state/creator_merge_preferences.json`

## v2.3 关联能力

- **跨项目模板同步**：`GET .../templates/sync-sources` · `POST .../templates/sync`
- **合并快照记忆**：`merge_preferences.merge_snapshot_id` 与历史来源一并恢复

## v2.4 关联能力

- **工厂级模板库**：`GET .../templates/factory` · `POST .../factory/publish` · `POST .../factory/pull` · 存储于 `infra/.state/factory_volume_templates.json`
- **向导分享链接**：`?nav=creator&wizard=1&done=pillars,volume` · `POST /api/creator/onboarding/progress/apply-share`
- **合并策略全局默认**：`GET .../merge-preferences/global` · 新项目无项目级偏好时继承全局 · 保存时同步写入 `infra/.state/creator_merge_preferences_global.json`

## v2.5 关联能力

- **模板版本标签**：`version_label` 字段 · `PUT .../templates/{id}/version` · 列表显示 `[v1.2] 模板名`
- **向导协作批注**：`step_notes` 持久化 · `PUT /api/creator/onboarding/notes` · 分享链接 `notes` 参数（base64 JSON）
- **合并策略分文档快照**：`pillars_merge_snapshot_id` / `global_outline_merge_snapshot_id` 独立记忆

## v2.6 关联能力

- **模板 semver 校验**：`version_label` 须符合 `v1.2.3` / `1.2.3-beta` · 列表带 `version_semver_valid`
- **向导 @提及**：批注内 `@handle` 解析为 `step_mentions` · 分享链接随 `notes` 一并传递
- **合并策略导入导出**：`GET/POST .../merge-preferences/export|import` · 支持 `scope=project|global|both`

## v2.7 关联能力

- **模板版本变更日志**：设版本标签时写入 `version_changelog` · `GET .../templates/{id}/version-changelog`
- **向导批注通知**：`@提及` 生成未读通知 · `GET/POST .../onboarding/notifications`
- **合并策略预设包**：内置 6 组组合 + 项目自定义 · `GET .../merge-preferences/preset-packages`

## 本地验证

```bash
cd novel-factory
bash scripts/verify-creator-onboarding-wizard.sh
python -m pytest tests/infra/test_creator_onboarding.py tests/dashboard/test_creator_endpoints.py -q -k onboarding
```
