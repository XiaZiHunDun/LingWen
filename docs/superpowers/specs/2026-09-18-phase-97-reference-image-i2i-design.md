# Phase 97 REQ-002 v2: Reference Image i2i — Design

> **状态**: 草稿 v1 (2026-09-18)
> **作者**: 协调者 (self-service, per 2026-09-15 simplified workflow)
> **优先级**: P3 (REQ-002 v2 sub-project, 紧接 Phase 96 image provider adapters)
> **父级**: Phase 96 (`docs/superpowers/specs/2026-09-17-phase-96-image-provider-adapters-design.md`)
> **作用域**: `lingwen-illustrations` package (v1 + v2 extension) + 1 new backend route module + 3 frontend component/store extensions
> **预期规模**: ~250 LOC production + ~85 new tests + 12 regression guards, 28-32 atomic commits

## 1. 背景与目标

Phase 90-95 建立了封面/章节插图生成 (REQ-002 多模态 v1), 用单次文本 prompt 生成图像. Phase 96 引入多 provider registry (MiniMax / OpenAI DALL-E 3 / Stability SD3).

**v1 限制**: 风格一致性问题 — 同一项目的多张插图各自独立生成, 视觉风格可能漂移 (人物/场景/笔触), 缺乏"风格圣经".

**Phase 97 目标**: 引入 image-to-image (i2i) 能力 — 用户上传 1 张参考图 (style bible), 后续生成以此图为风格基准. 2/3 provider 支持 (minimax + stability), 1/3 不支持 (openai DALL-E 3 纯文本).

## 2. 决策摘要 (Brainstormed 2026-09-18)

| 维度 | 决策 | 理由 |
|------|------|------|
| 能力策略 | SUPPORTS_I2I 声明 + 硬错误 (HTTP 422) | 明确失败语义, UI 引导用户切 provider |
| 作用域 | 项目默认 + per-call override | 匹配 Phase 96 `default_provider` 模式 |
| i2i strength | 服务端默认 (minimax=0.5, stability=0.35), 不暴露 UI | v1 极简, 避开用户误调 |
| 存储格式 | 单文件原格式 (JPG/PNG), 不 resize | 最简, provider 自处理尺寸 |
| 上传 UX | 项目设置页 + 弹窗 override | 主路径 + per-call 灵活性 |
| Provider 接口 | 双函数 + SUPPORTS_I2I 常量 (Approach A) | 零 Phase 96 retrofit, 清晰能力声明 |

## 3. 架构

### 3.1 Provider registry 扩展 (Phase 96 → Phase 97)

Phase 96 `get_provider(name)` 返回裸 `async def generate(...)` 函数. Phase 97 改为返回 `ProviderAdapter` dataclass:

```python
# providers/__init__.py
@dataclass(frozen=True)
class ProviderAdapter:
    name: str                                                  # "minimax" | "openai" | "stability"
    generate: Callable[..., Awaitable[bytes]]                  # 文本生成 (Phase 96 不变)
    generate_with_reference: Callable[..., Awaitable[bytes]]   # i2i 生成 (Phase 97 新增)
    supports_i2i: bool                                         # 能力声明 (Phase 97 新增)


def get_provider(name: str) -> ProviderAdapter:
    """Returns adapter; dynamic module attribute access for monkeypatch compat."""
    if name not in KNOWN_PROVIDERS:
        raise UnknownProviderError(...)
    module = importlib.import_module(f"lingwen_illustrations.providers.{name}")
    return ProviderAdapter(
        name=name,
        generate=module.generate,
        generate_with_reference=module.generate_with_reference,
        supports_i2i=module.SUPPORTS_I2I,
    )
```

**Monkeypatch 兼容性**: Phase 96 测试大量用 `monkeypatch.setattr("lingwen_illustrations.providers.minimax.generate", fake)`. Phase 97 通过 `importlib.import_module` 在 `get_provider()` 调用时重读 `module.generate`, 保证 monkeypatch 仍生效.

### 3.2 Provider 模块扩展

每个 provider module 加 `SUPPORTS_I2I` 常量 + `generate_with_reference` 函数:

**minimax.py** (SUPPORTS_I2I=True):
```python
SUPPORTS_I2I = True

async def generate_with_reference(
    *, prompt: str, reference_image_bytes: bytes,
    api_key: str, api_host: str,
    strength: float = 0.5,
    timeout: float = 60.0,
) -> bytes:
    """MiniMax i2i endpoint. JSON body with base64-encoded image."""
    url = f"{api_host.rstrip('/')}/v1/image_generation"
    image_b64 = base64.b64encode(reference_image_bytes).decode("ascii")
    payload = {
        "model": "minimax-multimodal",
        "prompt": prompt,
        "image_base64": image_b64,
        "strength": strength,
        "n": 1, "size": "1024x1024",
        "response_format": "b64_json",
    }
    # ... 复用 Phase 96 错误处理 (timeout, 429, 4xx/5xx) + decode_b64_envelope
```

> **实施时验证**: `image_base64` 字段名待真实 API 调一次验证; 字段名错时改 1 行. v0 plan 假设此字段名, 真实 API 可能是 `image_url` 或 `reference_image`.

**openai.py** (SUPPORTS_I2I=False):
```python
SUPPORTS_I2I = False

async def generate_with_reference(
    *, prompt: str, reference_image_bytes: bytes,
    api_key: str, api_host: str,
    strength: float = 0.0,
    timeout: float = 60.0,
) -> bytes:
    """OpenAI DALL-E 3 has no i2i capability. Raises GenerateError(retryable=False)."""
    raise GenerateError(
        "OpenAI DALL-E 3 does not support image-to-image generation",
        provider="openai",
        retryable=False,
    )
```

> **设计哲学**: 当调用方 (pipeline) 已在调用前检查 `supports_i2i=False` 时, 此函数不会到达. 但作为防御性编程保留 raise, 防止任何绕过 check 的调用.

**stability.py** (SUPPORTS_I2I=True):
```python
SUPPORTS_I2I = True

async def generate_with_reference(
    *, prompt: str, reference_image_bytes: bytes,
    api_key: str, api_host: str,
    strength: float = 0.35,                # Stability 文档推荐值
    timeout: float = 60.0,
) -> bytes:
    """Stability SD3 i2i: multipart with image file + strength."""
    url = f"{api_host.rstrip('/')}/v2beta/stable-image/generate/sd3"
    files = {
        "prompt": (None, prompt),
        "image": ("reference.jpg", reference_image_bytes, "image/jpeg"),
        "strength": (None, str(strength)),
        "output_format": (None, "png"),
    }
    # ... 复用 Phase 96 错误处理 (timeout, 429, 4xx/5xx) + Accept: image/*
```

### 3.3 参考图存储 (`reference_image.py`, 新模块)

```python
MAX_REFERENCE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIME_TYPES = frozenset({"image/jpeg", "image/png"})

def save_reference_image(project_root: Path, image_bytes: bytes, mime_type: str) -> Path:
    """Save to <root>/.lingwen/reference_image.{ext}. Overwrites if exists.
    Raises ValueError for invalid format, oversize."""

def delete_reference_image(project_root: Path) -> bool:
    """Idempotent remove. Returns True if existed, False otherwise."""

def load_reference_image(project_root: Path) -> bytes | None:
    """Returns bytes or None if not set."""

def reference_image_info(project_root: Path) -> dict | None:
    """Returns {size_bytes, mime_type, exists} or None if not set."""
```

**文件命名**: `<root>/.lingwen/reference_image.<ext>` (ext 从 mime_type 推: jpeg→jpg, png→png).

**为什么不在 ProjectSettings yaml 存**: 避免 yaml 序列化 binary base64 膨胀 + reference image 生命周期独立于 settings schema 演进.

### 3.4 Pipeline 扩展 (`pipeline.py`)

```python
async def generate_illustration(
    *, project_root, project_slug, type, chapter_num, style_preset,
    custom_prompt, api_key, api_host,
    provider: str = "minimax",
    reference_image_bytes: bytes | None = None,  # NEW (Phase 97)
) -> IllustrationMetadata:
    # Stages 1-3 (load, extract, compose) — Phase 96 不变
    ...

    adapter = get_provider(provider)

    # Stage 4 dispatch: i2i vs text (NEW Phase 97)
    if reference_image_bytes is not None:
        if not adapter.supports_i2i:
            raise GenerateError(
                f"provider '{provider}' does not support image-to-image generation",
                provider=provider, retryable=False,
            )
        image_bytes = await adapter.generate_with_reference(
            prompt=final_prompt,
            reference_image_bytes=reference_image_bytes,
            api_key=api_key, api_host=api_host,
            # strength 不传 → 用各 provider 默认值
        )
    else:
        image_bytes = await adapter.generate(
            prompt=final_prompt, api_key=api_key, api_host=api_host,
        )

    # Stage 5 (build metadata + storage) — Phase 96 不变 + used_reference_image 标记
    meta = IllustrationMetadata(
        ...existing fields...,
        used_reference_image=reference_image_bytes is not None,
    )
    storage.save_asset(project_root, image_bytes, meta)
    return meta
```

`regenerate_illustration` 同样加 `reference_image_bytes` 参数 — regenerate 时也允许更新参考图语义.

### 3.5 IllustrationMetadata 扩展

```python
@dataclass(frozen=True)
class IllustrationMetadata:
    ...existing 11 fields...
    used_reference_image: bool = False  # NEW (Phase 97). Default False for Phase 90-96 metadata.json 兼容.
```

`from_dict` 自动补 `used_reference_image=False` 当旧 metadata.json 缺此字段 (类似 Phase 96 `provider` field 的 backwards compat 模式).

### 3.6 新路由模块 (`routes/reference_image.py`)

3 endpoints:

```
POST   /api/projects/{slug}/reference-image   multipart upload (file=)
GET    /api/projects/{slug}/reference-image   → {exists, size_bytes, mime_type} | 404
DELETE /api/projects/{slug}/reference-image   → {deleted: true|false}
```

错误映射 (复用 Phase 96 `STAGE_HTTP_CODES` 模式):

| 错误 | HTTP | Stage |
|------|------|-------|
| Project 不存在 | 404 | load |
| multipart file 缺失 | 400 | load |
| 格式不支持 | 415 | load |
| > 10MB | 413 | load |
| OSError (disk/perm) | 500 | store |

### 3.7 现有路由扩展 (`routes/illustrations.py`)

```python
class GenerateRequest(BaseModel):
    ...existing 6 fields...
    # NEW (Phase 97): per-call reference image override via multipart file=
    # 路由层用 python-multipart 读取 file 字段 → bytes 传给 pipeline
    # JSON path 也接受 use_project_reference: bool = True, 控制是否使用项目默认参考图
    use_project_reference: bool = True  # 用户可显式设为 False 跳过参考图
```

**Multipart 处理**: `register_illustrations` 中 `generate_illustration` 接受 `file: UploadFile | None = File(None)` 参数. 路由层语义:

1. 当 `file` 不为 None (multipart 上传) → 用 per-call bytes, 不读 disk
2. 当 `file` 为 None 且 `use_project_reference=True` 且项目默认存在 → 从 disk 读 bytes
3. 当 `file` 为 None 且 `use_project_reference=False` → 跳过参考图, 走纯文本路径
4. 当 `file` 为 None 且项目无默认 → 走纯文本路径 (静默)

> **为什么需要 `use_project_reference` 字段**: 用户可能显式取消勾选 "使用项目默认参考图" — 这是用户意图, 不是默认值. Backend 必须能区分 "用户想要用默认" vs "用户显式不想用默认".

## 4. 前端组件

### 4.1 新组件: `ReferenceImageUpload.vue`

独立组件, 嵌入 `ProjectSettingsIllustration.vue` 使用:

- `<input type="file" hidden>` + 触发按钮
- 上传后展示预览 + 文件大小 + mime 类型
- 「替换」按钮 (重置 input.value 后触发 click)
- 「删除」按钮 (DELETE endpoint)
- 错误消息显示 (413/415/其他)
- data-testid: `reference-image-upload`, `reference-image-upload-input`, `reference-image-preview`, `reference-image-replace`, `reference-image-remove`, `reference-image-error`

### 4.2 `ProjectSettingsIllustration.vue` 修改

在 max_assets 字段前嵌入 `<ReferenceImageUpload :slug="slug" />`. ReferenceImageUpload 不通过 v-model 持久化 (独立调 endpoint), 与 default_provider 的 store-save 行为区分.

### 4.3 `GenerateIllustrationDialog.vue` 修改

新增 section: 「参考图 (可选)」

- Checkbox: "使用项目默认参考图" (默认勾选, 当 selectedProvider==openai 时禁用 + 警告)
- File input: "本次生成上传不同参考图" (覆盖项目默认)
- 警告消息: "OpenAI DALL-E 3 不支持参考图，已自动取消"

submit() payload:
```javascript
emit('generate', {
  ...existing fields...,
  // 当 perCallFile 是 File 对象时, store 自动转 multipart
  // 当 useProjectReference=true 且 perCallFile=null 时, 走 JSON (backend 从 disk 加载)
})
```

### 4.4 `useProjectSettings.js` store 扩展

新增 state + methods:
- `referenceImage: ref(null)` — {exists, size_bytes, mime_type}
- `fetchReferenceImage(slug)` — GET endpoint, 404 → null
- `fetchReferenceImageBlob(slug)` — 返回 blob URL 用于 `<img :src>` (binary, 不走 JSON)
- `uploadReferenceImage(slug, file)` — FormData POST
- `deleteReferenceImage(slug)` — DELETE endpoint

### 4.5 `useIllustrationStore.js` generate 方法

分流:
- `params.per_call_reference instanceof File` → multipart/form-data
- 否则 → JSON (Phase 96 现有 path, 加 `use_project_reference` boolean 字段)

### 4.6 Typed wrappers (`api/illustrations.ts`)

```typescript
export interface ReferenceImageInfo { exists: true; size_bytes: number; mime_type: 'image/jpeg' | 'image/png' }
export interface ReferenceImageNotFound { exists: false }
export function fetchReferenceImageInfo(slug: string): Promise<...>
export function fetchReferenceImageBlob(slug: string): Promise<Blob>
export function uploadReferenceImage(slug: string, file: File): Promise<void>
export function deleteReferenceImage(slug: string): Promise<void>
export interface GenerateRequest { ...existing..., use_project_reference?: boolean, per_call_reference?: File }
```

## 5. 数据流

### 5.1 项目默认参考图上传

```
[1] 用户在 ProjectSettingsIllustration → ReferenceImageUpload 点击「上传参考图」
    ↓
[2] File input change → onFileChange(file) → store.uploadReferenceImage(slug, file)
    ↓
[3] store builds FormData → POST /api/projects/{slug}/reference-image (file=)
    ↓
[4] apps/studio_api routes/reference_image.py POST handler:
    - project_root_for(slug) → 路径
    - read UploadFile bytes → validate size (≤10MB) + mime (jpeg/png)
    - reference_image.save_reference_image(root, bytes, mime_type)
        → 写 <root>/.lingwen/reference_image.{ext}
    - 返回 {exists: true, size_bytes, mime_type}
    ↓
[5] store 刷新 referenceImage.value → UI 切到预览态
```

### 5.2 带参考图的插图生成

```
[1] 用户打开 GenerateIllustrationDialog, onMounted 调 store.fetchReferenceImage(slug)
    → referenceImage.value 反映项目默认存在与否
    ↓
[2] 用户可:
    (A) 勾选/取消勾选 "使用项目默认参考图" (默认勾选)
    (B) 上传 per-call file 覆盖
    ↓
[3] submit() → emit generate event with params
    ↓
[4] useIllustrationStore.generate(slug, params):
    - per_call_reference is File → multipart/form-data
    - else → JSON {..., use_project_reference: bool}
    ↓
[5] POST /api/illustrations/generate:
    - multipart 时读 file 字段 → bytes
    - JSON 时按 use_project_reference 标志从 disk 加载
    - pipeline.generate_illustration(..., reference_image_bytes=...)
        → adapter.supports_i2i 检查
        → adapter.generate_with_reference(...)
    - 返回 IllustrationMetadata (with used_reference_image=True)
```

## 6. 测试策略

### 6.1 后端 pytest (~62 新测试)

| 文件 | 测试数 | 覆盖 |
|------|-------|------|
| `tests/test_reference_image.py` (新) | ~14 | save/load/delete/格式/大小/边界 (空文件/超大/格式错) |
| `tests/test_providers_i2i.py` (新) | ~16 | SUPPORTS_I2I 常量 + generate_with_reference per provider (mock httpx) + openai raise |
| `tests/test_providers_registry_adapter.py` (新) | ~6 | adapter object 形态 + dynamic lookup + monkeypatch 兼容 |
| `tests/test_pipeline_i2i.py` (新) | ~12 | dispatch i2i vs text + reference_image_bytes 透传 + openai hard error + metadata used_reference_image 标记 |
| `tests/test_illustrations_api.py` (extend) | ~6 | multipart 上传 + JSON use_project_reference + 422 i2i unsupported |
| `tests/test_routes_reference_image.py` (新) | ~8 | POST/GET/DELETE 3 endpoints + multipart + 413/415 |

### 6.2 前端 vitest (~24 新测试)

| 文件 | 测试数 | 覆盖 |
|------|-------|------|
| `components/illustrations/ReferenceImageUpload.spec.ts` (新) | ~6 | upload/preview/delete 状态机 + 错误显示 |
| `components/illustrations/ProjectSettingsIllustration.spec.ts` (extend) | ~3 | ReferenceImageUpload 嵌入 + 不影响 default_provider 等其他 field |
| `components/illustrations/GenerateIllustrationDialog.spec.ts` (extend) | ~5 | toggle 状态 + per-call file + openai auto-uncheck |
| `stores/useProjectSettings.spec.js` (extend) | ~4 | fetch + upload + delete + blob URL |
| `stores/useIllustrationStore.spec.js` (extend) | ~3 | multipart 分流 (File 走 multipart, else 走 JSON) |
| `api/illustrations.spec.ts` (extend) | ~3 | typed wrappers 类型断言 |

### 6.3 Regression Guards (G1-G12, source-only)

| ID | 名称 | 验证内容 |
|----|------|---------|
| G1 | `get_provider_returns_adapter_with_4_fields` | `get_provider(name)` 返回 `ProviderAdapter` 含 name/generate/generate_with_reference/supports_i2i |
| G2 | `provider_supports_i2i_constants_correct` | minimax + stability: SUPPORTS_I2I=True; openai: SUPPORTS_I2I=False (parametrized) |
| G3 | `providers_have_generate_with_reference_function` | 每个 provider module 导出 `generate_with_reference` (parametrized) |
| G4 | `openai_generate_with_reference_raises_with_unsupported` | openai.generate_with_reference 调 → GenerateError(retryable=False, provider="openai") |
| G5 | `reference_image_module_exists_with_4_functions` | `lingwen_illustrations.reference_image` 模块 + save/load/delete/info |
| G6 | `pipeline_dispatches_to_generate_with_reference_when_bytes_provided` | pipeline reference_image_bytes 非 None 时调 adapter.generate_with_reference (regex stub check) |
| G7 | `pipeline_raises_generate_error_for_openai_with_reference` | provider=openai + reference_image_bytes=non-None → GenerateError |
| G8 | `illustration_metadata_has_used_reference_image_field` | IllustrationMetadata dataclass 含 `used_reference_image: bool = False` |
| G9 | `routes_reference_image_three_endpoints_registered` | POST/GET/DELETE 三个 endpoint 注册到 FastAPI app |
| G10 | `generate_request_accepts_multipart_file_field` | route 端 generate 接受 file UploadFile 参数 |
| G11 | `frontend_reference_image_upload_component_exists` | ReferenceImageUpload.vue 存在 + 含 6 个 data-testid markers |
| G12 | `frontend_project_settings_store_has_reference_image_methods` | useProjectSettings store 含 fetch/upload/delete/blob 4 methods |

### 6.4 验证门

| 门 | 期望 |
|---|------|
| pytest lingwen-illustrations | ~194 (existing 132 + new 62) |
| pytest studio_api | ~121 (existing 113 + new 8) |
| pytest phase96+97 guards | 26 全过 (Phase 96 14 + Phase 97 12) |
| pytest phase90 guards | 29 全过 (确保 Phase 90-96 不回归) |
| ruff check | 0 new error |
| vitest apps/dashboard | ~2060 (existing 2036 + new 24) |
| pnpm tsc --noEmit | 0 new error |

## 7. 风险评估与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| Monkeypatch 兼容回归 (Phase 96 测试) | 高 — 22+ test 失败 | G1 part 2 显式测; 复用 `importlib.import_module` 模式 |
| 参考图过大 (10MB+) | 中 — 网络/内存 | 10MB 上限 + 前端 accept 限制 + 后端 MAX_REFERENCE_BYTES 校验 |
| i2i API 字段名错误 (MiniMax) | 中 — 真实调用失败 | dev 调一次验证 + 字段名错时 1 行修改 |
| Phase 95 G13b 冲突 (无 dedicated ProjectSettingsPage) | 低 | Phase 97 不引入新 page, 仍嵌入 SettingsPage |
| OpenAI 用户升级路径 | 中 — UX 摩擦 | UI 提示 + 自动取消勾选 + 引导切 provider |

## 8. 实施计划 (high-level)

按 v55+ 的 atomic direct master commit 模式 (per 2026-09-15 simplified workflow):

```
C0  spec + plan (本文件)
C2  test reference_image.py (TDD red)
C3  feat reference_image.py module (TDD green)
C4  test providers_i2i.py (red)
C5  feat providers/minimax.py + openai.py + stability.py: SUPPORTS_I2I + generate_with_reference
C6  test providers_registry_adapter.py (red + green)
C7  refactor providers/__init__.py: get_provider returns ProviderAdapter
C8  test pipeline_i2i.py (red)
C9  feat pipeline.py: reference_image_bytes param + dispatch
C10 feat metadata.py: used_reference_image field + from_dict compat
C11 test routes_reference_image.py (red)
C12 feat routes/reference_image.py: 3 endpoints
C13 feat routes/illustrations.py: multipart file handling
C14 feat app.py: register reference_image router
C15 test illustrations_api: multipart + 422 i2i unsupported
C16 test frontend ReferenceImageUpload.vue (vitest)
C17 feat frontend ReferenceImageUpload.vue component
C18 feat frontend useProjectSettings.js store: 4 reference image methods
C19 feat frontend ProjectSettingsIllustration.vue: embed ReferenceImageUpload
C20 feat frontend useIllustrationStore.js: multipart vs JSON dispatch
C21 feat frontend GenerateIllustrationDialog.vue: toggle + per-call file + openai auto-uncheck
C22 feat frontend api/illustrations.ts: typed wrappers
C23 test 12 regression guards G1-G12
C24 docs CLAUDE.md v56.0 → v56.1 + I089 NEW invariant (ProviderAdapter canonical home)
```

总计 ~28-32 atomic commits (含 plan 文档 + I089 invariant)。

## 9. 不引入的 (Out of scope for Phase 97)

- i2i strength UI 暴露 (Phase v3+ 考虑)
- 多参考图预设 (Phase v3+ 考虑)
- 参考图服务端 resize (Phase v3+ 考虑)
- LRU archive (独立 Phase)
- Notification center (独立 Phase)
- OpenAI i2i 工作 (DALL-E 3 不支持; 若 DALL-E 4 发布, 后续评估)
- Atomic provider fallback chain (Phase v3+)

## 10. 验证完成定义 (DoD)

Phase 97 闭环条件 (CHECKLIST):

- [ ] 28+ atomic commits on master (per 2026-09-15 simplified workflow)
- [ ] pytest lingwen-illustrations 194/194
- [ ] pytest studio_api 121/121
- [ ] pytest phase96+97 guards 26/26
- [ ] pytest phase90 guards 29/29 preserved
- [ ] vitest apps/dashboard 2060/2060
- [ ] ruff check 0 new error
- [ ] pnpm tsc --noEmit 0 new error
- [ ] CLAUDE.md bumped v56.0 → v56.1
- [ ] I089 NEW invariant in .lingwen/architecture.yml + CLAUDE.md
- [ ] Handoff doc at `docs/superpowers/handoffs/2026-09-18-phase-97-reference-image-i2i-handoff.md`
- [ ] BACKLOG updated (REQ-002 v2 remaining: LRU archive + notification center)
- [ ] CURRENT_STATUS updated

## 11. 关联文档

- Phase 96 spec: `docs/superpowers/specs/2026-09-17-phase-96-image-provider-adapters-design.md`
- Phase 96 handoff: `docs/superpowers/handoffs/2026-09-17-phase-96-image-provider-adapters-handoff.md`
- Phase 95 spec: `docs/superpowers/specs/2026-09-16-phase-95-project-settings-substitution-design.md`
- I088 invariant: provider registry canonical home
- BACKLOG: REQ-002 v2 sub-projects tracking
- `.lingwen/architecture.yml`: machine-readable invariants (I088 NEW for ProviderAdapter)
- `.lingwen/constraints.yml`: 9 anti-patterns (applies: no hardcoded secrets, no mutation, no console.log)