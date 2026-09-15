# Phase 90 — REQ-002 多模态（封面/插图生成）设计

> **状态**: 待审（2026-09-15 brainstorming 完成）
> **范围**: 小说封面 + 章节插图生成 + 资产库 + UI 集成
> **不属于本 phase**: 角色/地点头像 (v2 候选)、批处理队列 (v2 候选)、reference image upload (v2 候选)
> **依赖基线**: v54.21 (Phase 89 闭环) + I052 paths + I057 llm-service + I073 project-characters + I075 persistence

## 0. 决策摘要

| 维度 | 决策 |
|------|------|
| 范围 | 封面 + 章节插图（不含角色/地点头像） |
| Provider | MiniMax multimodal（复用现有 `lingwen-llm-service`） |
| 触发模式 | 混合：写栏手动按钮 + 项目设置可勾选"章节完成自动生成" |
| Prompt 上下文 | 章节文本 + `load_agency_target_characters` 角色档案 |
| 资产存储 | `<project_root>/assets/covers/` + `assets/illustrations/chapter-NNN/`，每图配 `.meta.json` sidecar |
| UI 集成面 | `WriteWorkspacePage` (生成按钮) + `LibraryPage` (资产 tab) + `ProjectSettingsPage` (插图偏好) |
| 风格预设 | 3 固定（古风水墨 / 现代写实 / 动漫厚涂）+ 自定义 prompt override |
| 迭代模式 | 单次 1 张 + "重生" 按钮覆盖原图 |
| 架构方案 | 两阶段：LLM 抽取场景 JSON → 模板组装 prompt → MiniMax 生图 |
| 包拓扑 | 新建 `packages/lingwen-illustrations/`（3 workspace deps） |
| 路由 | 4 个 RESTful 端点（generate / list / delete / image 静态服务） |

---

## 1. 架构与组件

### 1.1 Package 拓扑

新建 **`packages/lingwen-illustrations/`**，3 workspace deps：

| 依赖 | 来源 | 用途 |
|------|------|------|
| `lingwen-llm-service` | I057, Phase 43 | Stage 1 LLM 抽取（复用现有 LLM service） |
| `lingwen-project-characters` | I073, Phase 51 | 角色档案加载（`load_project_character_names` + `load_agency_target_characters`） |
| `lingwen-paths` | I052, Phase 37 | 项目根路径解析（`ProjectPaths` / `resolve_project_root`） |

子模块 5 个：

| 文件 | 职责 |
|------|------|
| `prompt_builder.py` | Stage 1：LLM 抽取场景 JSON |
| `style_templates.py` | 3 风格硬编码模板 + override 合并 |
| `image_generator.py` | Stage 2：MiniMax multimodal API 调用 |
| `storage.py` | 资产 IO（写 .jpg + .meta.json） |
| `metadata.py` | 元数据 dataclass + 序列化 |

### 1.2 入口层

**`apps/studio_api/`** — FastAPI router（沿用 Phase 54 persistence + Phase 118 world 模式）：

| 路由 | 方法 | 用途 |
|------|------|------|
| `/api/illustrations/generate` | POST | 手动生成（写栏触发） |
| `/api/illustrations/list` | GET | 资产库列表查询（支持 `?type=cover|chapter`） |
| `/api/illustrations/{id}` | DELETE | 删资产（重生流程） |
| `/api/illustrations/{id}/image` | GET | 静态文件服务（FastAPI `FileResponse`） |

**`apps/dashboard/`** — UI：

| 文件 | 用途 |
|------|------|
| `pages/WriteWorkspacePage.vue` | 顶部工具栏新增 "生成插图" 按钮 + 右侧插图位 |
| `pages/LibraryPage.vue` | 新增 "资产" tab（grid 视图，按 type 过滤） |
| `pages/ProjectSettingsPage.vue` | 新增 "插图偏好" section |
| `composables/useIllustration.js` | API wrapper + 加载/错误状态 |
| `stores/useIllustrationStore.js` | Pinia store（项目维度） |
| `components/illustrations/IllustrationGallery.vue` | 资产 grid |
| `components/illustrations/IllustrationCard.vue` | 单图卡片（缩略图 + 操作） |
| `components/illustrations/GenerateIllustrationDialog.vue` | 生成对话框（风格选择 + 描述 + 进度） |

### 1.3 架构不变量

`.lingwen/architecture.yml` 新增 **I087**：

> `packages/lingwen-illustrations/` 是图片生成（封面 + 章节插图）的唯一实包；`infra.illustrations.*` 路径非法。

---

## 2. 数据流与错误处理

### 2.1 手动生成流程（写栏触发）

```
[WriteWorkspacePage.vue]
  click "生成插图"
  → useIllustration.generateChapter({chapter_num, style_preset, custom_prompt?})
       │
       ▼
[POST /api/illustrations/generate]
  body: {
    project_slug: str,
    type: "chapter" | "cover",
    chapter_num: int | null,   // cover 时为 null
    style_preset: "ink" | "realistic" | "anime",  // enum 严格
    custom_prompt: str | null  // 用户补充描述
  }
       │
       ▼
[studio_api: illustration_service.generate()]
  ① resolve project paths (lingwen-paths.ProjectPaths)
  ② load chapter text (lingwen-persistence，type=cover 时跳过)
  ③ load character bible (lingwen-project-characters.load_agency_target_characters)
  ④ Stage 1: prompt_builder.extract_scene(chapter_text, character_bible)
       → lingwen-llm-service.chat() → JSON {subject, scene, mood, characters_in_scene, extraction_confidence}
  ⑤ Stage 2: style_templates.compose(preset, override, scene_json)
       → final prompt string
  ⑥ Stage 3: image_generator.generate(final_prompt)
       → MiniMax multimodal API → image bytes
  ⑦ storage.save(bytes, project_slug, chapter_num, metadata)
       → <project>/assets/{covers|illustrations/chapter-NNN}/<timestamp>-<uuid>.jpg
       → <same>.meta.json sidecar
  ⑧ return {id, url, metadata, scene_json}
       │
       ▼
[Frontend 更新 useIllustrationStore → 写栏右侧显示缩略图]
```

### 2.2 自动生成流程（章节完成 hook）

完全相同 pipeline，触发点 = `lingwen-persistence.write_chapter` 完成（章节 marked status=completed）→ 后台 task 调 `/api/illustrations/generate` 同步接口（不阻塞章节保存路径）。失败仅写 log（不阻塞章节完成）。ProjectSettings 勾选启用。后台 task 在 `apps/studio_api/background.py` 已有任务调度基础（沿用 P2-RESTART Phase 模式），新增 `illustrations_auto_generate_task` 注册。

### 2.3 错误处理（每阶段独立 error code）

| 阶段 | 失败场景 | HTTP | 错误对象 |
|------|----------|------|----------|
| ①②③ | 项目/章节/角色加载失败 | 404 | `{stage: "load", error: "...", retryable: false}` |
| ④ | LLM 抽取失败/超时 | 502 | `{stage: "extract", error: "...", retryable: true}` |
| ⑤ | 风格预设非法/JSON schema 不符 | 400 | `{stage: "compose", error: "...", retryable: false}` |
| ⑥ | MiniMax 限流/网络/超时 | 502 | `{stage: "generate", error: "...", retryable: true, retry_after: 30}` |
| ⑦ | 磁盘满/权限/路径非法 | 500 | `{stage: "store", error: "...", retryable: false}` |
| 任意 | Pydantic 验证失败 | 422 | `{stage: "validate", errors: [...]}` |

前端按 `stage` 字段给用户友好提示 + retry 按钮（仅 `retryable: true` 时显示）。

### 2.4 Stage 1 JSON Schema（设计契约）

```json
{
  "subject": "主视觉主体（人物/物体/场景）",
  "scene": "具体场景描述（时间/地点/动作）",
  "mood": "氛围词（e.g. 紧张、宁静、壮阔）",
  "characters_in_scene": [
    {
      "name": "林渊",
      "role": "主角",
      "key_visual": "黑发青年，剑眉星目，左肩有疤痕"
    }
  ],
  "extraction_confidence": 0.85
}
```

`extraction_confidence` 为 0-1 浮点数（LLM 自我评估），`< 0.5` 时前端弹"抽取置信度低"提示，用户可手动补充 prompt 触发重生。阈值 0.5 在 ProjectSettings 可配置（默认 0.5）。

### 2.5 资产文件结构

```
<project_root>/
└── assets/
    ├── covers/
    │   ├── 1726416000-abc123.jpg
    │   └── 1726416000-abc123.jpg.meta.json
    └── illustrations/
        └── chapter-017/
            ├── 1726416000-abc123.jpg
            └── 1726416000-abc123.jpg.meta.json
```

`.meta.json` 必填字段：

```json
{
  "id": "1726416000-abc123",
  "type": "chapter",
  "project_slug": "starfall-era",
  "chapter_num": 17,
  "style_preset": "ink",
  "custom_prompt": null,
  "scene_json": { /* Stage 1 输出 */ },
  "final_prompt": "...",
  "prompt_hash": "sha256:...",
  "model": "minimax-multimodal",
  "created_at": "2026-09-15T10:00:00Z"
}
```

---

## 3. UI/UX 流程

5 个 mockup 已推送到 visual companion（见 `docs/superpowers/brainstorm/3486151-1789475612/content/ui-flow.html`）：

### 3.1 写栏触发
- 顶部工具栏新增 "✦ 生成插图" 按钮（紫色强调）
- 右侧栏"本章节插图"位（未生成时显示占位）

### 3.2 生成对话框
- 3 风格预设卡（选中态紫边 + 浅紫底）
- "补充描述"输入框（可选）
- 上下文确认：章节文本 + 角色档案，提示"提取后显示预览"

### 3.3 进度展示
- 3 阶段展开（已完成 ✓ / 进行中 ⟳ / 等待 ○）
- 进度条（紫色渐变）
- 阶段耗时显示（如"3.2s"）

### 3.4 结果展示
- 写栏右侧"↻ 重生" + "⤓ 下载" 按钮
- 库资产 tab：3 列 grid，按 `type=cover|chapter` 过滤（v1 仅这两种，角色类目 v2 再加）
- 缩略图懒加载

### 3.5 项目设置 · 插图偏好
- 默认风格单选（3 选 1）
- "章节完成时自动生成插图" 开关（带说明）
- 资产数量上限（数字输入，默认 200）
- "生成前确认"开关

---

## 4. 测试策略

### 4.1 后端单元测试（`packages/lingwen-illustrations/tests/`）

| 测试文件 | 覆盖 | Mock 策略 |
|---------|------|----------|
| `test_prompt_builder.py` | Stage 1 JSON 抽取 + 角色合并 | `lingwen-llm-service.chat` mock 返回固定 JSON |
| `test_style_templates.py` | 3 风格模板 + custom override 合并 + 非法预设异常 | 无外部依赖（纯函数） |
| `test_image_generator.py` | Stage 3 MiniMax API 调用 + 限流/超时/网络错误 | `httpx.AsyncClient` mock |
| `test_storage.py` | 写 .jpg + .meta.json sidecar + 路径解析 + 重复 ID 防御 | tmp_path fixture |
| `test_metadata.py` | dataclass ↔ JSON 序列化 + 字段完整性 | 无 |
| `test_pipeline.py`（集成） | Stage 1→2→3 全链路 happy path + 每阶段失败注入 | 全部 mock + 注入失败 |

### 4.2 API 端点测试（`apps/studio_api/tests/`）

| 测试文件 | 覆盖 |
|---------|------|
| `test_illustrations_api.py` | POST generate / GET list / DELETE / 静态文件服务 + 4 种 error stage → 对应 HTTP code + 422 验证错误 |
| `test_illustrations_regression.py` | I087 invariant / 路径守门 / 旧 `infra.illustrations.*` 引用 0 |

### 4.3 前端测试（vitest）

| 文件 | 覆盖 |
|------|------|
| `useIllustration.test.js` | composable 加载状态 / 错误处理 / 重生流程 |
| `GenerateIllustrationDialog.spec.js` | 风格选择 / 描述输入 / 提交 / 进度订阅 |
| `IllustrationGallery.spec.js` | 网格渲染 / type 过滤 / 缩略图懒加载 |
| `ProjectSettingsIllustration.spec.js` | 风格默认 / 自动开关 / 数量上限 / 立即持久化 |

### 4.4 不测什么（YAGNI 防御）

- ❌ LLM 抽取质量（主观，集成测用 mock 固定 JSON）
- ❌ MiniMax API 实际行为（供应商责任）
- ❌ 跨包 wiring 完整性（架构 invariant + 集成测覆盖）

### 4.5 回归守门（Phase 88 模式）

`tests/test_phase90_illustrations.py`：

- G1: `packages/lingwen-illustrations/` 5 子模块存在
- G2: `apps/studio_api/routes/illustrations.py` 4 路由注册
- G3: `pyproject.toml` workspace member + dependencies = 3
- G4: `.lingwen/architecture.yml` 含 I087 invariant
- G5: 9-pattern audit 0 hits（`infra.illustrations.*` 引用清零）
- G6: 存储路径守门 `<project>/assets/{covers|illustrations/chapter-NNN}/<id>.jpg`
- G7: `.meta.json` sidecar 存在 + 含 4 必填字段 (prompt_hash, style, scene_json, timestamp)

---

## 5. 交付物清单（v1 phase）

### 5.1 后端
- [ ] `packages/lingwen-illustrations/` 完整包（5 子模块 + tests/ + pyproject.toml）
- [ ] `apps/studio_api/routes/illustrations.py`（4 路由）
- [ ] `pyproject.toml` workspace member 声明 + `dependencies = ["lingwen-llm-service", "lingwen-project-characters", "lingwen-paths"]`
- [ ] `.lingwen/architecture.yml` I087 invariant

### 5.2 前端
- [ ] `WriteWorkspacePage.vue` 生成按钮 + 右侧栏
- [ ] `LibraryPage.vue` 资产 tab
- [ ] `ProjectSettingsPage.vue` 插图偏好 section
- [ ] `composables/useIllustration.js` + `stores/useIllustrationStore.js`
- [ ] 3 个新组件（Gallery / Card / Dialog）

### 5.3 文档
- [ ] `docs/superpowers/specs/2026-09-15-phase-90-illustrations-design.md`（本文）
- [ ] `docs/superpowers/handoffs/2026-09-15-phase-90-illustrations-handoff.md`（实施后）
- [ ] `CLAUDE.md` 版本行更新（v54.21 → v55.0）
- [ ] `collaboration/CURRENT_STATUS.md` + `BACKLOG.md` 同步

### 5.4 测试
- [ ] 6 个后端测试文件（4.1 节）
- [ ] 2 个 API 测试文件（4.2 节）
- [ ] 4 个前端测试文件（4.3 节）
- [ ] 1 个回归守门文件（4.5 节）

---

## 6. 风险与缓解

| 风险 | 缓解 |
|------|------|
| MiniMax multimodal API 限流或不可用 | Stage 3 设计为可替换（image_generator.py 单一接口），未来可加 DALL-E/Replicate adapter |
| Stage 1 LLM 抽取质量差 | `extraction_confidence` 字段 + 前端提示；v2 可加 reference image 强化人物一致性 |
| 资产膨胀 | ProjectSettings 数量上限 + 超限确认；v2 加 LRU 自动归档 |
| 自动生成章节完成时静默失败 | 仅 log 不阻塞；v2 加通知中心（已在 BACKLOG 候选） |
| 跨项目路径穿越攻击 | `lingwen-paths.resolve_project_root` 已是 invariant-enforced；storage 层加 path validation 防御 |

---

## 7. 不在范围（v2 候选）

- 角色 / 地点 / 场景 头像（资产库多类型 UI 复杂度高）
- 批处理队列（多章并发）
- Reference image upload (i2i 人物一致性)
- LRU 自动归档
- 通知中心（自动生成完成通知）
- 历史版本回滚（多次生成全部保留）
- DALL-E / Replicate provider adapter
