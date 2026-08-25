# 灵文沉浸写作工作台 · 设计稿

> **状态**：design v1 · 待用户审阅 · 2026-08-26
> **作者**：brainstorming 会话输出（5 个 section 全部经用户确认）
> **Phase**：2026-08-26 · v15 路线 · 创作端 UX 子项目 #1
> **方案**：A · TipTap + 章节-场景两级 + Markdown 落地

---

## 0. Context

### 0.1 项目当前定位

灵文（líng wén）· 工业化小说生产系统已经自我宣称达到「v12 顶级 KPI」（2026-06-22）：
- 7 本 Studio 样章 LLM judge 章均分 ≥4.0
- 主修验收一条命令 · Dashboard prose 热力+diff+judge · CI 50% 覆盖 + golden×8 + e2e 默认绿
- pytest 3011+ · 真实 LLM batch 三章 DoD · 七样章 dist 对外 zip

最近 50+ phase（Phase 60–114）集中在 dashboard 工程清理（性能、knip、CI），dashboard 处于 v14.2 干净状态。

### 0.2 缺口分析

| 维度 | 当前 | 顶级目标 | 差距 |
|------|------|----------|------|
| 工厂生产端（5-agent pipeline） | ★★★★★ | 顶级 | 几乎无 |
| 创作端 UX（作者日常使用） | ★★☆☆☆ | 顶级 | **明显缺口** |

**核心痛点**：`apps/dashboard/src/components/creator/CreatorWriteChat.vue`（134 行）实际上**只是个聊天面板**——不是真正的长文写作编辑器。项目没有 TipTap / Monaco / ProseMirror / Slate / Lexical 任何 rich text 编辑器依赖。

### 0.3 用户角色与工作流

- **混合工作流**：用户能写大纲/关键场景，正文靠 agent 生成
- 双模式（纯写 vs 编辑）需要切换
- 不替代 CreatorPage（工厂视角），而是作者专注模式专用入口

---

## 1. 架构总览（Mental Model）

### 1.1 产品表面定位

新增**独立顶级页面** `WriteWorkspacePage.vue`，与 `StudioPage` / `ChaptersPage` 同级，通过路由 `/write/:chapterId` 进入。不替换 `CreatorPage`，而是「工匠视角」专用入口。CreatorPage 保留工厂视角。

### 1.2 模式

| 模式 | 目的 | 默认显示 |
|------|------|----------|
| **Author 模式** | 纯创作 | 章节大纲 + 编辑器 + AI 抽屉（收起） |
| **Editor 模式** | 润色/审稿 | 章节大纲 + 编辑器 + AI 抽屉 + **质量面板**（行内标注 + S-check 概览） |

模式通过 header 切换，不刷路由；状态持久化到 localStorage。

### 1.3 章节-场景两级

- **章节**（Chapter）：现有单位，文件 `ch{N}.md` 在 `03_内容仓库/04_正文/`
- **场景**（Scene）：用 Markdown H3 (`###`) 切分，agent 写完后 split 出 3–8 个场景
- 场景边界用 front-matter 标记 `<!--scene:scene_id -->` 或 TipTap 自定义 `sceneBreak` mark

### 1.4 3-Pane Scrivener 风布局

```
┌─────────────────────────────────────────────────────────┐
│ Header: 章节号 · 标题 · [Author/Editor 切换] · 字数 · 目标 │
├──────────┬─────────────────────────────┬───────────────┤
│ Outline  │ Editor (TipTap)             │ AI Drawer     │
│ (左)     │ 沉浸 + 打字机模式 │ (右, 默认收起) │
│          │                             │               │
│ - 卷大纲 │ Author: 留白多              │ Author: 续写  │
│ - 场景卡 │ Editor: 行内 P0/P1 标注     │ Editor: 修辞  │
│ - 字数   │                             │               │
└──────────┴─────────────────────────────┴───────────────┘
```

### 1.5 数据落地

Markdown 文件 + YAML front-matter。front-matter 存场景边界、修改时间、字数快照、agent 写入标记位。**不引入 IndexedDB 双写**，避免和 5-agent pipeline 抢 source of truth。

### 1.6 与现有系统集成

- 从 `VolumePlan`（已有）选章节进入
- 编辑后写回文件 → `content_writer` agent 下次读到的就是最新版本
- Editor 模式的 P0/P1 标注 → 调 `infra/quality/checkers/` 复用，不重写
- AI Drawer 复用现有 `CreatorWriteChat` 的核心（已有 134 行不丢），加 outline 上下文注入

---

## 2. 组件树 + 状态管理

### 2.1 组件树

新增组件放在 `apps/dashboard/src/components/writeWorkspace/`，与 `creator/` 平级：

```
WriteWorkspacePage.vue                    # /write/:chapterId 入口
├── WriteWorkspaceHeader.vue              # 章节号 · 标题 · 模式切换 · 字数 · 目标
├── WriteWorkspaceOutlinePane.vue         # 左：卷大纲 + 场景卡列表
├── WriteWorkspaceEditorPane.vue          # 中：TipTap 编辑器 + 行内标注
│   ├── TipTapEditor.vue                  # 封装 ProseMirror + 自定义 sceneBreak mark
│   └── WriteInlineAnnotationLayer.vue    # Editor 模式行内 P0/P1 浮标
├── WriteWorkspaceAIDrawer.vue            # 右：AI 抽屉（复用 CreatorWriteChat 核心）
│   └── WriteChatContextInjector.vue      # 注入当前章节/场景上下文到 prompt
└── WriteWorkspaceStatusBar.vue           # 底：字数 · 自动保存状态 · 模式提示
```

### 2.2 Store 设计

新增 `stores/useWriteWorkspaceStore.js`，shallowRef 主（遵循项目 Phase 77 收敛后模式）：

```js
state = {
  chapterId: shallowRef(null),
  mode: shallowRef('author'),           // 'author' | 'editor'
  outline: shallowRef([]),              // {id, title, sceneCount, wordCount}[]
  scenes: shallowRef([]),               // {id, title, body, annotations[], wordCount}[]
  annotations: shallowRef([]),          // {sceneId, offset, severity, rule, msg}
  aiDrawerOpen: shallowRef(false),
  writeGoal: shallowRef({ daily: 0, todayWritten: 0 }),
  saveState: shallowRef({ status: 'idle', lastSavedAt: null, dirty: false }),
}
actions = { load, save, addScene, splitScene, runCheck, openAI }
```

### 2.3 持久化策略

| 操作 | 策略 |
|------|------|
| **保存** | debounce 800ms 自动写回 Markdown 文件 + front-matter 更新（覆盖式） |
| **快照** | 每次保存生成 `ch{N}.snapshots/{timestamp}.md`，保留最近 20 个（gitignore） |
| **冲突** | 文件 mtime 检测到外部修改（agent 写）→ 提示用户：rebase / 放弃本地 / 复制本地到剪贴板 |
| **场景标记** | TipTap `sceneBreak` mark 序列化到 Markdown 为 `<!--scene:id-->`，agent 可读 |

### 2.4 与现有 store 关系

- **不复用** `useCreatorWriteWorkbench`（已是 facade + 4 submodules，专门服务 CreatorPage 工厂视角）
- **共用** `useNavStore` 注册新路由 `/write/:chapterId`
- **复用** `infra/quality/checkers/` 的 P0/P1 引擎（Editor 模式调用），不复制逻辑

### 2.5 类型安全

TypeScript strict（已开启），新增 `types/writeWorkspace.ts` 定义 `Scene` / `Annotation` / `SaveState` 类型。

---

## 3. 数据流

### 3.1 核心循环

```
[键盘输入] → [TipTap doc] → [debounce 800ms] → [md serializer]
  → [PUT /api/write/:id] → [infra.persist.write_chapter()]
  → [原子写 ch{N}.md] → [更新 index.json]
  → [触发 save snapshot] → [agent 下次读到最新]
```

### 3.2 序列化格式（Markdown + front-matter）

```markdown
---
chapter: 12
title: 灰烬中的回声
scenes:
  - id: s1
    title: 雨夜
    word_count: 412
  - id: s2
    title: 剑光
    word_count: 387
total_words: 2830
last_modified_by: human
last_modified_at: 2026-08-26T14:32:11Z
---

<!--scene:s1-->
雨下得很大。林夜握剑的手在发抖。

「师叔——」她低声说。
...

<!--scene:s2-->
剑光起时，林夜没看清是谁先动的手。
...
```

### 3.3 Agent 复读链路（与现有 5-agent pipeline 兼容关键）

1. `content_writer` agent 写下一章前，调 `infra/persistence/read_chapter(N)` 读 `ch{N}.md` —— 现在读到的是**人类已编辑的版本**，含 front-matter 场景结构
2. `polisher` 同理——读到的最新 Markdown 也是人类版
3. agent 写下一章会**保留 front-matter 结构**（不破坏 sceneBreak）；agent 不感知 scene id 是给 UI 用的，只看 H3 标题
4. **agent 不会写 `last_modified_by: human`** —— 只有 WriteWorkspacePage 写

**关键约束**：人类编辑器与 agent writer **共用同一 `MarkdownSerializer` 模块**（在 spec 实施 Day 1 抽出）。

### 3.4 AI Drawer 上下文注入

```js
// WriteChatContextInjector.vue
buildContextPrompt() {
  const currentScene = scenes.value[activeSceneIndex.value]
  const prevChapterEnd = lastParagraphOf(chapterId.value - 1)
  return {
    current_chapter_heading: outline.value[chapterId.value].title,
    current_scene: currentScene.title,
    current_scene_body: currentScene.body,
    prev_chapter_tail: prevChapterEnd,
    characters_in_scene: detectCharacters(currentScene.body),
  }
}
```

### 3.5 Editor 模式质量联动

```
[Editor 模式开启] → [runCheck() action] → [infra/quality/checkers/run_full()]
 → [annotations[]: {sceneId, offset, severity, rule, msg}]
    → [WriteInlineAnnotationLayer 在 TipTap decoration 层渲染]
    → [鼠标悬停 → 浮窗显示 S-check 规则解释 + 修复建议]
```

### 3.6 冲突场景（关键 edge case）

用户打开 `/write/12` 写作中 → agent 异步写了 `ch12.md` → `mtime` 变更 → 顶部弹条 `检测到外部修改（content_writer 写于 X 分钟前）` → 三选项：
- **rebase 他们的到本地**
- **放弃本地**
- **导出本地到 `ch12.local.md`**

---

## 4. 模式切换 + 快捷键 + 沉浸 UX

### 4.1 模式切换

| 触发 | 行为 |
|------|------|
| Header 开关 toggle | `mode.value = 'author' \| 'editor'`，动画过渡 200ms |
| `Cmd + .` | 快速 toggle |
| 进入页面默认 | 上次离开时的 mode（localStorage 持久化） |

### 4.2 Editor 模式视觉变化

- 编辑器右侧出现细窄 gutter 显示 P0/P1 标记（红/黄圆点）
- 底部 status bar 显示 `P0: 0 P1: 3 (点击查看)`
- 顶部 header 右侧出现 `运行质量门` 按钮（手动触发完整检查）

### 4.3 Author 模式视觉（默认）

- 无 gutter、无质量提示、无 status bar 干扰
- 唯一持久元素：Header 的章节号+标题 + status bar 的字数

### 4.4 快捷键体系（统一 prefix = `Cmd` on Mac, `Ctrl` on Win）

| 快捷键 | 功能 | 适用模式 |
|--------|------|----------|
| `Cmd + S` | 立即保存（跳过 debounce） | 全部 |
| `Cmd + .` | toggle Author/Editor | 全部 |
| `Cmd + 1` | 切换左大纲面板 | 全部 |
| `Cmd + 2` | toggle AI 抽屉 | 全部 |
| `Cmd + 3` | toggle 打字机模式 | Author |
| `Cmd + K` | 命令面板（跳转章节/插入模板/召唤 AI） | 全部 |
| `Cmd + Shift + Enter` | 在光标处插入场景断点 | Author |
| `Cmd + Shift + V` | 粘贴为纯文本（去掉格式） | 全部 |

### 4.5 打字机模式

- 当前编辑行始终在屏幕中央 1/3 处
- TipTap 的 scrollIntoView + CSS transform
- 行号自动跟随
- 关闭时恢复正常滚动

### 4.6 字数目标

- Header 显示 `2,830 / 3,000 字 ▓▓▓▓▓▓▓▓▓░ 94%`
- 目标在 Settings 设置（v1 存 localStorage `lingwen.write_goal.daily`；项目级 yaml 持久化留待 v2）
- 完成时 Header confetti 效果（200ms，不打扰）
- 每日字数聚合：dashboard Today 页显示本周写作曲线（顺接 Phase 79 性能测量）

### 4.7 自动保存 UX

- 编辑 → debounce 800ms → 保存
- status bar 状态机：`idle` → `saving` → `saved 14:32` → 5 秒后回 `idle`
- 失败时 `error` 红色 + 可点击重试
- 退出页面前若有未保存 dirty，弹原生 confirm

### 4.8 AI Drawer 触发（仅 Author 模式可主动召唤）

- `Cmd + 2` 召唤抽屉
- 抽屉顶部小气泡显示当前场景上下文（如 `现在场景：雨夜 · 人物：林夜、莫言 · 上章末：「……这一剑我没躲。」`）
- 聊天框 prompt 自动注入上下文

---

## 5. 测试 + 验收 + 风险

### 5.1 测试策略

| 层 | 工具 | 覆盖目标 |
|----|------|----------|
| 单元 | Vitest | `useWriteWorkspaceStore` actions、Markdown 序列化/反序列化、`sceneBreak` 解析、字数计算 |
| 组件 | Vitest + Vue Test Utils | `WriteWorkspaceHeader` / `OutlinePane` / `EditorPane` 的渲染 + 交互冒烟 |
| 集成 | Vitest | store ↔ API mock 链路、front-matter 写入、annotation 渲染 |
| E2E | Playwright | 关键流：进入写作 → 打字 → 自动保存 → 文件落盘 → 切换 Editor → 看到标注 |
| 视觉 | Playwright screenshot | 与 CreatorPage 视觉对比，确保不"撞脸" |

### 5.2 验收标准（v1 完成定义）

- [ ] `/write/:chapterId` 路由可访问，章节列表来自 `VolumePlan`
- [ ] Author 模式无质量门 UI，Editor 模式可见 P0/P1 行内标注
- [ ] TipTap 编辑器场景断点可增删，前后内容完整保留
- [ ] 自动保存 800ms debounce 生效，文件 mtime 更新，agent 下次读到最新版
- [ ] AI 抽屉 `Cmd+2` 召唤，关闭不打断写作
- [ ] 字数实时统计，达成目标 confetti 不干扰
- [ ] 打字机模式开启时编辑行居中
- [ ] **不破坏**：Tests 1545+ 全绿、`vue-tsc 0 errors`、Build OK、knip 0/7
- [ ] **不破坏**：CreatorPage 现有工厂视角不受影响
- [ ] **不破坏**：5-agent pipeline（content_writer 读到的 front-matter 仍合法）
- [ ] 页面测试覆盖率 ≥ 80%（OPTIMIZATION_PLAN 24%→80% 命中）

### 5.3 风险与缓解

| 风险 | 概率 | 缓解 |
|------|------|------|
| TipTap 中文标点 + sceneBreak mark 边界问题 | 中 | 早期 spike（spec 阶段先做最小 demo 验证） |
| 引入新依赖膨胀 bundle | 中 | dynamic import + route-level code splitting（已有 Phase 113 经验） |
| 与 content_writer agent 写入格式冲突 | 中 | 双方共用同一 `MarkdownSerializer` 模块（**必须**——spec 阶段先抽出来） |
| 用户写作时 agent 异步写覆盖本地 | 高 | mtime 检测 + 三选项冲突弹条（§3.6 已设计） |
| 现有 CreatorPage 用户迁移成本 | 低 | 保留两套入口，文档说明何时用哪个 |

### 5.4 回滚策略

- 新增在独立 route `/write/*` 下，**不动 CreatorPage 任何代码**
- API 新增 `/api/write/:id`（不替换现有 `/api/chapters/:id`，先共存）
- v1 跑不通时，git revert 单 commit 即可回退（暂不需要 feature flag）

---

## 6. 构建顺序（参考时间线，约 2 周 v1）

1. **Day 1–2**：MarkdownSerializer 抽取 + front-matter schema
2. **Day 3**：TipTap spike + sceneBreak 验证（中文标点 round-trip）
3. **Day 4–5**：WriteWorkspaceStore + OutlinePane
4. **Day 6–8**：EditorPane + 自动保存（含 mtime 冲突检测）
5. **Day 9–10**：AI drawer 集成（上下文注入）
6. **Day 11–12**：Editor 模式 + annotation 渲染
7. **Day 13–14**：测试 + 视觉对比 + 收尾

---

## 7. 范围外（Out of Scope）

v1 不做：
- 富文本格式工具栏（粗体/斜体/标题）—— Markdown 本身 + 自定义 mark 已足够
- 多用户协作（仅本机单人）
- 移动端响应式（桌面优先）
- 离线编辑 + sync（在线优先）
- 富媒体（图片/表格/代码块）—— 小说不需要
- AI 行内续写（Sudowrite 风格）—— 仅抽屉式召唤
- 完整工作流（这不在 WriteWorkspacePage 职责内，归 CreatorPage 工厂）

---

## 8. 与后续工作的衔接

- **Phase 后续**：v1 上线后，可考虑：
  - 场景级字数分布热力图（接 prose 热力）
  - 多章节同时编辑（标签页）
  - 移动响应式（Tauri 已配置但未验证）
  - 与 Studio 8 本短篇样本的"作者模板"互通
- **OPTIMIZATION_PLAN 命中**：页面测试覆盖率 24% → 80%（v1 页面至少 12 个测试）
- **OPTIMIZATION_PLAN 命中**：ESLint 警告 148 → ≤50（WriteWorkspace 新代码零警告）

---

## 9. 决策日志

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-08-26 | 不替换 CreatorPage，独立页面 | CreatorPage 是工厂视角，混在一起会冲突 |
| 2026-08-26 | Markdown 落地而非 IndexedDB 双写 | 与 5-agent pipeline 抢 source of truth 会爆 |
| 2026-08-26 | TipTap 而非 Monaco | Vue 3 生态首选，bundle 可控（~200KB vs ~3MB） |
| 2026-08-26 | 章节-场景两级粒度 | 360 章项目单章 3000–5000 字，场景分块让大纲更可导航 |
| 2026-08-26 | 共用 MarkdownSerializer 模块 | 人类编辑器和 agent writer 不能走两条序列化路径 |
| 2026-08-26 | Author/Editor 双模式同 store | 用户工作流混合，避免路由级 mode 切换 |