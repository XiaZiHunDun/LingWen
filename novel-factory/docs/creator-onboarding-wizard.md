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

## v2.8 关联能力

- **模板变更 diff 摘要**：版本日志附带 `diff_summary`（卷纲行级 +/−）
- **向导通知 handle 过滤**：`GET .../notifications?handle=` · ack 支持按 handle
- **合并预设包分享**：`GET/POST .../preset-packages/export|import`

## v2.9 关联能力

- **模板可视化对比**：changelog `visual_diff.lines`（add/remove/context 着色）
- **向导 Webhook**：`GET/PUT .../onboarding/webhook` · @提及 创建时 POST 推送
- **合并预设包工厂库**：`.../preset-packages/factory` publish/pull/delete

## v3.0 关联能力

- **模板变更回滚**：changelog `can_rollback` · `POST .../templates/{id}/version-rollback`
- **向导通知邮件**：`GET/PUT .../onboarding/email` · SMTP 推送 @提及
- **合并预设包 semver**：预设包 `version_label` + `version_semver_valid` · 列表/分享/工厂库继承

## v3.1 关联能力

- **模板变更审批**：`POST .../version-approval` · `GET .../approvals` · approve/reject
- **向导通知 digest**：`GET .../notifications/digest` · 按 handle/步骤聚合未读
- **合并预设包依赖图**：`depends_on` 字段 · `GET .../preset-packages/graph`

## v3.2 关联能力

- **模板变更审批链**：`GET/PUT .../approvals/chain-config` · 多步 approve 才生效 · UI 显示 `chain_progress`
- **向导通知定时 digest**：`GET/PUT .../notifications/digest/schedule` · `POST .../digest/dispatch`
- **合并预设包冲突检测**：`GET .../preset-packages/conflicts` · 缺依赖/semver 降级/环依赖

## v3.3 关联能力

- **模板审批审计**：`GET .../approvals/history` · `GET .../audit-export` · 审批事件 Webhook（`type: template_approval`）
- **digest 后台轮询**：Dashboard lifespan 每 15 分钟自动检查到期 digest（`LINGWEN_CREATOR_DIGEST_POLL_SEC` 可覆盖）
- **预设包冲突修复**：`GET .../conflicts/fixes` · `POST .../conflicts/apply-fix` · 一键移除坏依赖/semver 提升

## v3.4 关联能力

- **模板审批 SLA/邮件**：`GET/PUT .../approvals/sla-config` · `GET .../overdue` · 提交/驳回 SMTP 通知
- **digest 静默与重试**：schedule `quiet_hours_start/end` · `GET .../digest/retry-queue` · `POST .../digest/retry`
- **预设包导入预检**：`POST .../import/preflight` · `POST .../conflicts/apply-all` 批量修复

## v3.5 关联能力

- **审批链指派**：`PUT .../approvals/chain-config` 支持 `step_assignees`、步骤备注与超时邮件
- **digest 路由与统计**：`handle_channels` · `GET .../digest/stats` · 重试指数退避
- **预设拓扑与冲突**：`GET .../toposort` · `POST .../import/preview-diff` · `GET .../factory/conflicts`

## v3.6 关联能力

- **审批 OR 签/转交**：`step_assignee_groups` · `POST .../transfer` · `GET .../snapshot-diff`
- **digest 死信**：`handle_quiet_hours` · `GET .../digest/dead-letter`
- **Webhook 签名**：`signing_secret` · `X-LingWen-Signature` · 工厂拉取 `POST .../factory/pull/preflight`

## v3.7 关联能力

- **快照漂移阻断**：`GET .../snapshot-drift` · `POST .../approve` 支持 `force` · `POST .../batch-approve|batch-reject`
- **死信重放与 channel 重试**：`POST .../digest/dead-letter/replay` · schedule `channel_retry_config`
- **工厂拉取向导**：`POST .../factory/pull` 支持 `conflict_strategies` · `GET .../changelog/diff`

## v3.8 关联能力

- **模式化 UI**：`GET /api/creator/overview` 返回 `ui_profile`（按 companion/advance/studio 隐藏运维面板）
- **陪伴一键审查**：`POST /api/creator/logic-check`（P0 only，无 judge）
- **推进卷级脉络**：overview `volume_pulse` 卷进度与偏离摘要（非逐章列表）

## v3.9 关联能力

- **陪伴折叠向导**：`ui_profile.wizard_default_collapsed`（无 @提及 / 无 deep-link 时默认收起）
- **推进 alert 过滤**：`deviation_min_severity: alert` · `volume_pulse.alerts_only`
- **简化通知**：`simplified_notifications` 隐藏 Webhook/邮件配置面板

## v4.0 关联能力

- **正文内嵌编辑**：`PUT /api/creator/chapters/{n}` · `ui_profile.chapter_inline_edit`（陪伴模式）
- **batch 卷摘要**：`POST /api/creator/volume-summary/generate` · batch 完成后 Dashboard 提示查看卷摘要
- **向导首次展开**：`wizard_expand_if_incomplete` · 未完成且未 dismiss 时展开 · `PUT /api/creator/onboarding/wizard-dismiss` 持久折叠

## v4.1 关联能力

- **推进只读全文**：`chapter_full_preview` · `GET /api/creator/chapters/{n}?full=1` 展示完整正文（非内嵌编辑）
- **逻辑审查内嵌**：`logic_check_inline_issues` · `POST /api/creator/logic-check` 返回 `issues[]` · 点击跳转对应章
- **pulse/摘要跳转**：卷级脉络行点击跳转首章 · 最新摘要 / batch 提示一键展开卷摘要

## v4.2 关联能力

- **偏离跳转**：`deviation_chapter_jump` · 偏离列表点击跳转对应章
- **P0 过滤**：`logic_check_p0_only` · 逻辑审查内嵌列表仅展示 P0
- **状态色同步**：卷摘要 `pulse_status` / `volume_label` 与卷级 pulse 对齐

## v4.3 关联能力

- **batch 高亮 alert 卷**：`batch_highlight_alert_volumes` · batch 完成后滚动并高亮偏离卷
- **保存后 P0 复查**：`chapter_save_p0_recheck` · `POST /api/creator/logic-check?chapter=N` 单章复查
- **pulse 生成摘要**：`volume_pulse_summary_generate` · 卷级脉络行「生成摘要」按钮

## v4.4 关联能力

- **batch 自动展开摘要**：`batch_auto_open_summary` · batch 完成后自动展开对应卷摘要
- **写栏内嵌复查**：`chapter_recheck_inline` · 保存正文后在写栏展示单章 P0 复查结果
- **batch 偏离提示**：`batch_deviation_prompt` · batch 完成提示 alert 卷名称

## v4.5 关联能力

- **复查段落定位**：`recheck_issue_paragraph_jump` · 内嵌复查问题点击后选中正文对应段落
- **batch 清除高亮**：`batch_clear_pulse_no_alert` · batch 完成且无 alert 卷时收起 pulse 高亮
- **章纲并排编辑**：`chapter_outline_inline_edit` · 陪伴写栏大纲与正文并排内嵌保存

## v4.6 关联能力

- **复查高亮动画**：`recheck_issue_highlight` · 复查问题定位段落后正文与问题行闪烁高亮
- **batch 滚偏离列表**：`batch_scroll_deviation_list` · batch 完成且范围内有偏离时滚到偏离列表
- **章纲只读预览**：`chapter_outline_read_preview` · 推进模式章节预览展示完整章纲

## v4.7 关联能力

- **偏离列表高亮**：`deviation_list_highlight` · batch 滚到偏离列表时高亮范围内首条偏离
- **batch 展开偏离章**：`batch_open_first_deviation` · batch 完成后自动跳转首个偏离章节
- **逻辑审查问题高亮**：`logic_check_issue_highlight` · 陪伴一键逻辑审查问题点击后闪烁高亮

## v4.8 关联能力

- **偏离点击高亮**：`deviation_click_highlight` · 点击偏离项跳转章节时同步高亮该行
- **写栏偏离摘要**：`batch_deviation_inline_summary` · batch 完成后在写栏展示范围内偏离列表
- **段落高亮统一**：`issue_paragraph_highlight_unified` · 逻辑审查与复查共用 `issue-line--active` 与正文高亮样式

## v4.9 关联能力

- **偏离摘要 dismiss**：`batch_deviation_inline_dismiss` · 写栏 batch 偏离摘要「知道了」收起
- **偏离卷摘要联动**：`batch_deviation_summary_link` · batch 有偏离时自动展开并按钮跳转卷摘要
- **问题键盘导航**：`issue_keyboard_navigation` · 逻辑审查/复查问题列表 ↑↓ 键切换并跳转

## v5.0 关联能力

- **模式切换引导**：`creation_mode_switch_hint` · 陪伴/推进页顶提示如何改 `config/project.yaml` 切换模式
- **卷纲 diff 预览**：`volume_plan_diff_preview` · 推进模式编辑卷纲时展示相对已保存版本的变更列表
- **batch 历史**：`batch_history_panel` · 推进模式展示最近 5 条 batch 任务（章范围 + 状态）

## v5.1 关联能力

- **卷纲保存确认**：`volume_plan_diff_save_confirm` · 有未保存 diff 时点击保存先弹出确认
- **batch 历史重放**：`batch_history_replay_range` · 点击历史任务填入 batch 起止章
- **Studio 入口提示**：`studio_creation_entry_hint` · 工作室模式页顶提示 companion/advance 切换方式

## v5.2 关联能力

- **diff 展开详情**：`volume_plan_diff_expand_detail` · 卷纲 diff 每项可展开查看字段级 before/after
- **batch 状态筛选**：`batch_history_status_filter` · 按 completed / running / failed 过滤历史任务
- **模式文档链接**：`creation_mode_switch_doc_link` · 陪伴/推进页顶一键打开对方走通清单与模式说明路径

## v5.3 关联能力

- **diff 大纲并排**：`volume_plan_diff_outline_side_by_side` · 卷纲 diff 旁展示全局大纲摘录
- **batch 历史导出**：`batch_history_export` · 导出最近 batch 任务 JSON
- **Studio 向导折叠记忆**：`studio_wizard_collapse_memory` · 工作室模式记住入门向导展开/收起状态

## v5.4 关联能力

- **大纲卷表高亮**：`volume_plan_diff_outline_row_highlight` · diff 旁全局大纲卷表行按变更卷名高亮
- **batch 日期分组**：`batch_history_date_group` · batch 历史按完成日期分组展示
- **模式徽章说明**：`creation_mode_badge_hint` · 陪伴/推进徽章悬停或点击显示模式摘要

## v5.5 关联能力

- **diff 跳转大纲编辑**：`volume_plan_diff_jump_outline_edit` · 卷纲 diff 面板一键跳转设定栏全局大纲
- **batch 状态色标**：`batch_history_status_color` · completed / failed / running 左侧色条区分
- **Studio 徽章说明**：`studio_creation_mode_badge_hint` · 工作室模式徽章悬停或点击显示摘要

## v5.6 关联能力

- **保存后刷新 diff**：`volume_plan_diff_refresh_on_save` · 卷纲保存成功后立即刷新 diff 预览
- **batch 运行中动画**：`batch_history_running_pulse` · running 任务条目呼吸动画
- **陪伴徽章色标**：`companion_creation_mode_badge_tint` · 陪伴模式徽章绿色强调

## v5.7 关联能力

- **diff 无变更折叠**：`volume_plan_diff_auto_collapse` · 无未保存变更时折叠 diff，有变更自动展开
- **batch 失败重试**：`batch_history_failed_retry` · 失败任务一键回填范围与预算
- **推进徽章色标**：`advance_creation_mode_badge_tint` · 推进模式徽章蓝色强调

## 本地验证

```bash
cd novel-factory
bash scripts/verify-creator-onboarding-wizard.sh
python -m pytest tests/infra/test_creator_onboarding.py tests/dashboard/test_creator_endpoints.py -q -k onboarding
```
