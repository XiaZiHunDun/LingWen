# 创作者产品线 PRD v1

> **状态**：v1 已落地配置层 + 脚本 MVP（2026-06-22）  
> **并列产品线**：灵文工作室 **Studio 工厂线**（七样章、全绿 CI、judge≥4.0）

## 1. 背景

Studio v12 优化的是「样章工厂 + 质量 KPI」，服务的是**可复用生产 pipeline**，不是大多数想写百万字以内小说的人。

创作者产品线面向：

- **百万字以内**想写完一本书的人
- 文笔要求不高，但要**负担轻、少必读、多可操作、有愉悦创作感**
- 两种模式可切换，而非单一「自动写书机」

## 2. 目标用户

| 画像 | 诉求 |
|------|------|
| 短篇 / 中篇新手 | 自己写，怕逻辑穿帮，不想被 judge 打分 |
| 长篇连载作者 | 定好卷纲后让机器主笔，只看脉络和偏离预警 |
| 工作室运营（次要） | 继续用 `studio` 模式走样章工厂 |

## 3. 双模式定义

```
【陪伴模式 companion】  ≤30 章 · 人主笔
  系统 = 记录 + P0 逻辑审查
  默认关：prose 校准 / LLM judge / golden

【推进模式 advance】    几十万字 · 人定卷纲
  系统 = batch 产章 + 卷摘要 + P0 偏离预警
  用户不默认逐章精读全文

【工作室 studio】       工厂线（与 v12 一致）
  全量质量门 · 样章 KPI · CI
```

## 4. 配置模型

`config/project.yaml` 新增字段：

```yaml
project:
  creation_mode: companion   # companion | advance | studio
  quality_profile: creator_relaxed  # creator_relaxed | studio_full
```

解析逻辑：`infra/creator_mode.py` → `resolve_creator_settings()`。

| 模式 | fail_severity | prose | judge | golden | 通知 |
|------|---------------|-------|-------|--------|------|
| companion | P0 | off | off | off | 每章可选 |
| advance | P0 | off | off | off | 卷级摘要 |
| studio | P0+ | on | on | on | 工厂默认 |

**向后兼容**：无 `creation_mode` 的旧项目默认为 `studio`。

## 5. 用户旅程（MVP）

### 5.1 陪伴模式

1. `python lingwen.py init-project my-book --title "书名" --creation-mode companion --chapters 12`
2. 人写正文（或局部用 pilot）
3. `bash scripts/run-companion-check.sh` — 仅 P0
4. 报告点开才看细节；无 judge 分数压迫

### 5.2 推进模式

1. `init-project ... --creation-mode advance --chapters 80`
2. 编辑 `全局大纲.md` 卷纲表
3. `bash scripts/run-advance-volume.sh 1 10 10 0.30`
4. 阅读 `docs/volume-summary-ch001-010.md`
5. 偏离时 P0 check 报警，不强制全文审校

### 5.3 工作室（不变）

`--creation-mode studio` 或七样章既有项目；走 `run-primary-revision-verify.sh` 等工厂验收。

## 6. 非目标（v1）

- 一体化 Web UI（dashboard 仍偏工厂）
- SaaS / 多租户
- 每次 push 全跑 llm×7
- 第九本样章书

## 7. 成功指标（创作者向）

| 指标 | 目标 |
|------|------|
| 新建项目默认模式 | companion |
| 陪伴模式检查耗时 | < 全量 check 的 30% |
| 推进模式卷摘要 | batch 后自动生成 |
| 用户必读文档 | 0（onboarding 一页） |

## 8. 实现映射

| PRD 条目 | 代码 / 脚本 |
|----------|-------------|
| 模式配置 | `infra/creator_mode.py`, `ProjectConfig` |
| 脚手架 | `init-project --creation-mode --chapters` |
| 陪伴守门 | `scripts/run-companion-check.sh` |
| 推进 MVP | `scripts/run-advance-volume.sh`, `creator_volume_summary.py` |
| 入门 | `docs/creator-onboarding.md` |

## 9. 后续（v1.1+）

- Dashboard「写 / 脉络 / 设定」三栏（陪伴默认） — ✅ v1.1
- `lingwen.py check` 自动读 `creation_mode` 应用 profile — ✅ v1.1
- 卷纲锁定 UI + 偏离 diff 高亮 — ✅ v1.2
- 推进模式：卷纲 vs 实际 diff 对比 — ✅ v1.2（`infra/creator_volume_plan.py`）

## 10. 后续（v1.3+）

- 卷纲与分章大纲关键词偏离（语义级） — ✅ v1.3
- Dashboard 内嵌正文只读预览 — ✅ v1.3
- `lingwen check` / `all` 尊重 `max_chapter` — ✅ v1.3

## 11. 后续（v1.4+）

- 卷纲拖拽/合并与范围重叠检测 — ✅ v1.4（重叠 alert）
- Dashboard 一键 advance batch — ✅ v1.4
- 设定栏轻量在线编辑 — ✅ v1.4
- 创作页 Playwright live e2e — ✅ v1.4（7 tests）

## 12. 后续（v1.5+）

- 卷纲拖拽排序 — ✅ v1.5
- batch 完成后自动刷新卷摘要 — ✅ v1.5
- 设定编辑 diff 预览 — ✅ v1.5

## 13. 后续（v1.6+）

- 卷纲合并向导 — ✅ v1.6
- 设定与卷纲并发编辑冲突提示 — ✅ v1.6（revision + HTTP 409）
- companion 真人走通 checklist — ✅ v1.6

## 14. 后续（v1.7+）

- 卷纲拆分 — ✅ v1.7
- 设定版本历史 — ✅ v1.7
- advance 真人走通 checklist — ✅ v1.7

## 15. 后续（v1.8+）

- 卷纲模板库 — ✅ v1.8
- 设定 diff 三路合并 — ✅ v1.8
- studio 创作者 hybrid 走通 — ✅ v1.8

## 16. 后续（v1.9+）

- 卷纲模板自定义保存 — ✅ v1.9
- 设定合并策略 UI — ✅ v1.9
- 创作者 onboarding 合一页向导 — ✅ v1.9

## 17. 后续（v2.0+）

- 卷纲自定义模板删除 — ✅ v2.0
- 合并策略可视化 diff — ✅ v2.0
- 向导 deep-link `?nav=creator&wizard=1` — ✅ v2.0

## 18. 后续（v2.1+）

- 卷纲自定义模板重命名 — ✅ v2.1
- 合并策略预设（一键全选磁盘/历史）— ✅ v2.1
- 向导步骤完成勾选与进度持久化 — ✅ v2.1

## 19. 后续（v2.2+）

- 卷纲自定义模板导入/导出 — ✅ v2.2
- 向导步骤自动勾选（检测支柱/卷纲文件）— ✅ v2.2
- 合并策略记忆上次选择 — ✅ v2.2

## 20. 后续（v2.3+）

- 卷纲自定义模板跨项目批量同步 — ✅ v2.3
- 向导单步 deep-link `?wizard=1&step=volume` — ✅ v2.3
- 合并策略记忆历史快照 id — ✅ v2.3

## 21. 后续（v2.4+）

- 工厂级共享模板库（非项目 `.state`）— ✅ v2.4
- 向导进度分享链接 — ✅ v2.4
- 合并策略按用户全局配置 — ✅ v2.4

## 22. 后续（v2.5+）

- 模板库版本标签 — ✅ v2.5
- 向导协作批注 — ✅ v2.5
- 合并策略按文档类型拆分 — ✅ v2.5

## 23. 后续（v2.6+）

- 模板版本 semver 校验 — ✅ v2.6
- 向导批注 @提及 — ✅ v2.6
- 合并策略导入导出 — ✅ v2.6

## 24. 后续（v2.7+）

- 模板版本变更日志 — ✅ v2.7
- 向导批注通知 — ✅ v2.7
- 合并策略预设包 — ✅ v2.7

## 25. 后续（v2.8+）

- 模板变更 diff 摘要 — ✅ v2.8
- 向导通知按 handle 过滤 — ✅ v2.8
- 合并预设包分享 — ✅ v2.8

## 26. 后续（v2.9+）

- 模板变更可视化对比 — ✅ v2.9
- 向导通知 Webhook — ✅ v2.9
- 合并预设包工厂库 — ✅ v2.9

## 27. 后续（v3.0+）

- 模板变更回滚 — ✅ v3.0
- 向导通知邮件 — ✅ v3.0
- 合并预设包 semver — ✅ v3.0

## 28. 后续（v3.1+）

- 模板变更审批 — ✅ v3.1
- 向导通知摘要 digest — ✅ v3.1
- 合并预设包依赖图 — ✅ v3.1

## 29. 后续（v3.2+）

- 模板变更审批链 — ✅ v3.2
- 向导通知定时 digest — ✅ v3.2
- 合并预设包冲突检测 — ✅ v3.2

## 30. 后续（v3.3+）

- 模板审批审计与 Webhook — ✅ v3.3
- digest 后台轮询 — ✅ v3.3
- 预设包冲突修复向导 — ✅ v3.3

## 31. 后续（v3.4+）

- 模板审批 SLA/邮件 — ✅ v3.4
- digest 静默时段与重试队列 — ✅ v3.4
- 预设包导入预检与批量修复 — ✅ v3.4

## 32. 后续（v3.5+）

- 审批链 step 指派/备注/超时邮件 — ✅ v3.5
- digest handle 路由/指数退避/统计 — ✅ v3.5
- 预设拓扑排序/import diff/工厂冲突检测 — ✅ v3.5

## 33. 后续（v3.6+）

- 审批 OR 签/转交/快照 diff 预览 — ✅ v3.6
- digest 按 handle 静默/死信队列 — ✅ v3.6
- Webhook HMAC 签名 · 工厂拉取预检/changelog/拓扑可视化 — ✅ v3.6

## 34. 后续（v3.7+）

- 快照漂移阻断与批量审批 — ✅ v3.7
- digest 死信重放与按 channel 重试策略 — ✅ v3.7
- 工厂拉取冲突合并向导与 changelog diff — ✅ v3.7

## 35. 后续（v3.8+）

- 模式化 UI profile（companion/advance 隐藏 Studio 运维面板）— ✅ v3.8
- 陪伴模式一键逻辑审查 API — ✅ v3.8
- 推进模式卷级脉络 pulse — ✅ v3.8
