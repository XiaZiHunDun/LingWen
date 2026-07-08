# 前端信息架构 V1（人类习惯优先）

> 用户可见导航真源：`src/config/humanFirstNav.js`  
> 模式裁剪：`src/config/dashboardNavByMode.js`（`creation_mode` 仅影响「工具箱」内容与写栏厚度，不出现在一级文案）

## 1. 设计原则

1. **默认帮用户选**：冷启动不问字数、不问 companion/advance/studio。
2. **一级 ≤ 4 项**：聊聊 / 书桌 / 书架 / 工具箱
3. **对话 ≠ 写作**：L1「聊聊」负责搞明白与导航；正文只落在「书桌」编辑器。
4. **脉络是书内抽屉**（伴侣/推进默认）：单书内 write 为主，pulse/memory 侧滑（`creator_desk_drawer` + `CreatorWorkspaceShell` 抽屉触发器）。

## 2. 一级导航

| 用户看到的 | `nav` 参数 | 内部页面 | 说明 |
|-----------|------------|---------|------|
| 💬 聊聊 | `ask` | `AskPage` | 新用户默认落地；问答 + 速记 Tab |
| ✍️ 书桌 | `write` | `CreatorPage`（`nav=creator` 兼容） | 有草稿/章节时默认落地 |
| 📚 书架 | `library` | `LibraryPage` | 项目卡片、换书、新建入口 |
| 🧰 工具箱 | `more` | `MorePage` | 生产、待办、洞察、**系统设置**（L1 不用「设置」以免与内页重名） |

## 3. 默认落地规则

无 URL `nav` 参数时（`resolveDefaultLandingNav`）：

```
审阅模式 → inbox
有 localStorage 写作断点 或 chapters_written > 0 → write
否则 → ask
```

写作断点：`writeResumeStorage.js`，在选章/保存正文时写入 `{ slug, chapter, at }`。

## 4. 「聊聊」产品边界

**做：**

- 查进度、设定、人物、伏笔（`memory/query` + overview 摘要）
- 新用户引导与建议气泡
- 底部动作：去书桌写 / 收成新书（wizard 深链）

**不做：**

- 长文续写、候选 diff、checkpoint（属于写栏 workbench）
- Batch / 工厂队列（属于「工具箱 → 生产」）

## 5. 与现有模块映射

| 用户路径 | 现有实现 |
|---------|---------|
| 书桌 | `CreatorPage` + `CreatorWritePanel` + workbench |
| 聊聊 · 问答 | `queryCreatorMemory` + overview 摘要 |
| 书架 | `fetchStudioProjects` + `setStudioActive` |
| 工具箱 · 生产 | `ProducePage` |
| 工具箱 · 系统设置 | `SettingsPage`（页内标题「系统设置」） |

## 6. URL 约定

- `?nav=write&chapter=12` — 书桌并聚焦章节
- `?nav=ask` — 聊聊
- `?nav=library` — 书架
- `?nav=more` — 工具箱
- `?nav=creator` — **兼容旧链**，等同 `write`

## 7. 验收

1. 新用户打开无 `nav` → 进入聊聊，30 秒内可发出第一条消息。
2. 有章节进度用户 → 默认书桌（或聊聊一键跳转 ≤ 2 次点击）。
3. 侧栏仅 4 项；生产/待办从「工具箱」进入；「设置」仅指系统设置子页。

## 8. 书桌 P0 行为（人类习惯）

| 行为 | 说明 |
|------|------|
| L1 进书桌 | `navigateTo('write', { clearFocus: true })` 清除 `workspace=pulse` 等深链 |
| 默认 Tab | 陪伴 / 推进 → **写作**；工厂（studio）仍默认脉络（写 Tab 隐藏） |
| 显式深链 | `?nav=write&workspace=pulse` 仍打开脉络 Tab |
| 页标题 | 书桌页 `page-title` 为「书桌」，非「创作伴侣」 |
| 弱化技术 chrome | 顶栏隐藏 `CreationModeHint`；侧栏副标题显示书名或「写作助手」；项目下拉不显示 `(production)` |
| 陪伴 / 推进模式 | 隐藏模式徽章、偏好摘要、导出/发布、重复页标题；启用写栏工作台；记忆/设定收进次要 Tab 行；不弹「尚未开始写作」黄条 |
| 书桌打磨 | 章节列表在左栏；编辑器首屏优先；写作工具默认折叠；目标卡用人话文案；书架卡片不显示 production 角色；无重复只读大纲；路径卡默认折叠；作用域显示「正在写：第 N 章」 |

## 9. 测试基线（2026-07-08）

| 维度 | 数量 | 命令 |
|------|------|------|
| Vitest | 941 | `pnpm vitest run` |
| 测试 typecheck（relaxed + strict） | — | `pnpm typecheck` / `pnpm typecheck:tests:strict`（CI 门禁） |
| Live E2E | 60 | `LINGWEN_E2E_LIVE=1 pnpm e2e:live` |
| 视觉回归 | 18 | `LINGWEN_E2E_LIVE=1 pnpm e2e:visual-regression` |
| a11y L1 | 7 | `LINGWEN_E2E_LIVE=1 pnpm e2e:a11y`（critical / serious / moderate） |
| UI metrics | 10 | `LINGWEN_E2E_LIVE=1 pnpm e2e:ui-metrics`（1280×720 `clippedBelowFold`） |

本地跑法详见 [creator-panel-matrix.md §10](./creator-panel-matrix.md#10-playwright-本地跑法)。
