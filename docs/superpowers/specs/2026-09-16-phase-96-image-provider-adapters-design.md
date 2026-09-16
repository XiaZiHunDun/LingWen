# Phase 96 — image provider adapters design

> **Date**: 2026-09-16
> **Phase**: 96
> **Version target**: v55.5 → v56.0
> **Type**: REQ-002 v2 sub-project — multi-provider abstraction (3 adapters)
> **Status**: spec — informs implementation

## 1. Goal & context

REQ-002 v2 ship 多 image provider 支持。Phase 90 + 91 + 92 + 93 + 94 + 95 已完成 v1（MiniMax 单 provider + 完整 pipeline + 完整 dev tooling），但**只支持 MiniMax**。v2 第一步把单 provider 抽象为 adapter pattern，ship 3 adapters：MiniMax + OpenAI DALL-E 3 + Stability SDXL/SD3。Anthropic 删除（无原生 image gen API；APIConfig `anthropic_api_key` property 留 dormant 待未来需要时再说）。

### 1.1 与现有状态关系

- **Phase 93 已完成** `image_generator.py` b64_json real-API decoding（deviation #3 closed）。Phase 96 不是"加 b64_json decoding" — 这是已完成工作。Phase 96 是 **adapter abstraction**。
- **Phase 95 deferred** "持久化在 v2 走 /api/projects/{slug}/settings"。Phase 96 吸收这部分工作 — 新建 `project_settings.py` route。
- **APIConfig 已前瞻** Phase 83 P3-ARCHDEBT 时已加 `openai_api_key` + `anthropic_api_key` properties。Phase 96 复用现有 config singleton，只需扩展 `openai_api_host` + `stability_api_key` + `stability_api_host`。

### 1.2 不变量

- **provider 解析优先级 (single source of truth)**: per-call body/query > project settings yaml > hardcoded `"minimax"`。Route 层一次性 resolve，pipeline / adapter 不再 validate。
- **adapter 永远不需要知道其他 provider 存在** — 每个 adapter 只负责自己的 API contract。
- **persistence 是 yaml 不是 SQLite** — Phase 96 v1 简单优先。
- **任何 `GenerateError` raised by provider dispatch 必须有非 `"unknown"` 的 provider 字段**。`"unknown"` 仅 legacy path 用。
- **`image_generator.generate()` legacy wrapper 保留** — 内部 delegate `providers.get_provider("minimax").generate(...)`，现有测试 mocks 通过 re-export 仍 work。

### 1.3 Decisions log (from brainstorming)

| 维度 | 决策 | 理由 |
|---|---|---|
| Provider scope | MiniMax + OpenAI DALL-E 3 + Stability SD3 | 3 adapters, phase 多但覆盖广; Anthropic 删; Imagen v2 |
| Selection model | Per-project 默认 + per-call override | UX 最完整; ProjectSettingsIllustration + GenerateIllustrationDialog 双层 |
| Persistence | Backend `PUT/GET /api/projects/{slug}/settings` (yaml) | 吸收 Phase 95 deferred; durable; future-extensible |
| Adapter signature | Minimal `(prompt, *, api_key, api_host, timeout=60) → bytes` | 3 adapters 同形; future i2i 需拆时再说 |
| Error model | GenerateError + 新 `provider` 字段 | 最小侵入; per-provider 错误信息; HTTP 错误 payload 加 provider |
| Metadata schema | 加 `provider: str = "minimax"` + 保留 model | provider = billing/quota 路由; model = 技术身份 |
| Architecture | Registry-based dispatch (方案 A) | Phase 90 feature-module pattern 延续; 不引入魔法 |

## 2. Architecture (Component map)

### 2.1 组件图

```
packages/lingwen-illustrations/
├── src/lingwen_illustrations/
│   ├── image_generator.py # thin wrapper → providers.minimax (向后兼容)
│   ├── providers/                  # NEW subpackage
│   │   ├── __init__.py             # KNOWN_PROVIDERS + get_provider() + UnknownProviderError
│   │   ├── _b64_decode.py          # 复用 Phase 93 safe-decode triad
│   │   ├── minimax.py              # MiniMax adapter (Phase 93 代码搬入)
│   │   ├── openai.py               # OpenAI DALL-E 3 adapter (NEW)
│   │   └── stability.py            # Stability SD3 adapter (NEW)
│   ├── pipeline.py                 # + provider: str = "minimax" 参数
│   ├── metadata.py                 # + provider: str = "minimax" 字段
│   ├── exceptions.py # GenerateError + provider: str = "unknown" 字段
│   └── ... (现有 bible_loader, style_templates, prompt_builder, storage, ...)
└── tests/
    ├── test_image_generator.py     # 保留 (向后兼容 wrapper 测试)
    ├── test_providers/             # NEW
    │   ├── test_minimax.py         # 搬自 test_image_generator + 调整 mock target
    │   ├── test_openai.py          # NEW
    │   ├── test_stability.py       # NEW
    │   └── test_registry.py        # KNOWN_PROVIDERS + get_provider() 行为
    └── ...

apps/studio_api/
├── routes/illustrations.py         # + provider in GenerateRequest body
└── routes/project_settings.py      # NEW: PUT/GET /api/projects/{slug}/settings

apps/dashboard/src/
├── components/illustrations/
│   ├── ProjectSettingsIllustration.vue   # + default_provider dropdown
│   └── GenerateIllustrationDialog.vue    # + provider picker
├── stores/
│   └── useProjectSettings.js              # NEW: PUT/GET project settings
```

### 2.2 9 项关键变更

1. **Provider abstraction** — `providers/` subpackage，3 modules。Each exports `generate(prompt, *, api_key, api_host, timeout=60) -> bytes`。
2. **Registry pattern** — `KNOWN_PROVIDERS = ("minimax", "openai", "stability")` + `get_provider(name) -> Callable`。未知名 raise `UnknownProviderError`。
3. **Pipeline dispatch** — `pipeline.generate_illustration(..., provider="minimax")` + `regenerate_illustration` from `existing_meta.provider`。
4. **Metadata schema** — `IllustrationMetadata` 加 `provider: str = "minimax"`；`from_dict()` 处理缺字段 (向后兼容)。
5. **Route signature** — `GenerateRequest` 加 `provider: Optional[str] = None`。`None` → settings → `"minimax"`。
6. **Project settings persistence** — `PUT/GET /api/projects/{slug}/settings`，存 `<project_root>/.lingwen/illustration_settings.yaml`。
7. **Frontend dropdowns** — `ProjectSettingsIllustration.vue` + `GenerateIllustrationDialog.vue` 各加 provider picker。
8. **GenerateError provider field** — `__init__(message, *, retry_after=None, provider="unknown")`。
9. **Image generator backwards compat** — `image_generator.generate()` thin wrapper around MiniMax adapter。

## 3. Components (详细 interfaces)

### 3.1 `providers/__init__.py`

```python
KNOWN_PROVIDERS: tuple[str, ...] = ("minimax", "openai", "stability")
DEFAULT_PROVIDER: str = "minimax"

class UnknownProviderError(ValueError):
    """Raised when get_provider(name) gets a name not in KNOWN_PROVIDERS."""

def get_provider(name: str) -> "Callable[..., Awaitable[bytes]]":
    """Look up adapter generate() function by name."""
    if name not in _REGISTRY:
        raise UnknownProviderError(
            f"unknown provider '{name}', expected one of {KNOWN_PROVIDERS}"
        )
    return _REGISTRY[name]

# Eager import — each adapter ~50 LOC; all use httpx anyway.
from lingwen_illustrations.providers import minimax, openai, stability  # noqa: E402, F401

_REGISTRY: dict[str, "Callable[..., Awaitable[bytes]"]"] = {
    "minimax": minimax.generate,
    "openai": openai.generate,
    "stability": stability.generate,
}
```

### 3.2 `providers/_b64_decode.py`

```python
"""Shared b64_json envelope decoder. Extracted from Phase 93."""
import base64, binascii, json
import httpx
from lingwen_illustrations.exceptions import GenerateError


def decode_b64_envelope(resp: httpx.Response, *, provider: str) -> bytes:
    """Decode {"data": [{"b64_json": "..."}]} envelope → raw image bytes.
    Phase 93 safe-decode triad (isinstance ×3 + b64decode(validate=True))
    reused. Errors raise GenerateError with provider field set.
    """
    try:
        body = resp.json()
    except (json.JSONDecodeError, ValueError) as e:
        raise GenerateError(f"image API non-JSON response: {e}", provider=provider) from e
    data = body.get("data") if isinstance(body, dict) else None
    if not isinstance(data, list) or not data:
        raise GenerateError("image API response missing 'data' array", provider=provider)
    first = data[0]
    if not isinstance(first, dict):
        raise GenerateError("image API data[0] is not an object", provider=provider)
    b64_value = first.get("b64_json")
    if not isinstance(b64_value, str) or not b64_value:
        raise GenerateError("image API data[0] missing 'b64_json' string", provider=provider)
    try:
        return base64.b64decode(b64_value, validate=True)
    except (binascii.Error, ValueError) as e:
        raise GenerateError(f"image API b64_json decode failed: {e}", provider=provider) from e
```

### 3.3 Three adapter modules

| Module | URL pattern | Response decode | Model default | Size default |
|---|---|---|---|---|
| `providers/minimax.py` | `{host}/v1/image_generation` | `decode_b64_envelope` | `minimax-multimodal` | `1024x1024` |
| `providers/openai.py` | `{host}/v1/images/generations` | `decode_b64_envelope` | `dall-e-3` | `1024x1024` |
| `providers/stability.py` | `{host}/v2beta/stable-image/generate/sd3` | `resp.content` (raw PNG, header `Accept: image/*`) | `sd3-medium` (path-encoded) | `1024x1024` (multipart `output_format: png`) |

All adapters same signature: `async def generate(*, prompt, api_key, api_host, timeout=60.0) -> bytes`.

错误处理 per-adapter (uniform pattern):
- `httpx.TimeoutException` → `GenerateError(retry_after=60, provider=...)`
- `httpx.HTTPError` / `ConnectionError` / `OSError` → `GenerateError(provider=...)`
- HTTP 429 → parse `retry-after` (Phase 93 fallback: non-numeric → 60s; Stability default → 30s)
- HTTP 4xx (除 429) → `GenerateError(retryable=False, provider=...)`
- HTTP 5xx → `GenerateError(retryable=True, provider=...)`

### 3.4 `metadata.py`

```python
@dataclass(frozen=True)
class IllustrationMetadata:
    id: str
    type: Literal["chapter", "cover"]
    project_slug: str
    chapter_num: int | None
    style_preset: str
    custom_prompt: str | None
    scene_json: dict[str, Any]
    final_prompt: str
    prompt_hash: str
    model: str
    provider: str = "minimax"  # NEW. Default for old .meta.json files.
    created_at: str

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "IllustrationMetadata":
        # Backwards compat: inject "minimax" if old .meta.json missing provider.
        if "provider" not in d:
            d = {**d, "provider": "minimax"}
        try:
            return cls(**d)
        except (KeyError, TypeError) as e:
            from lingwen_illustrations.exceptions import LoadError
            raise LoadError(f"invalid metadata dict: {e}") from e
```

### 3.5 `exceptions.py`

```python
class GenerateError(IllustrationError):
    def __init__(
        self,
        message: str,
        *,
        retry_after: int | None = None,
        provider: str = "unknown",
    ) -> None:
        super().__init__(Stage.GENERATE, message, retryable=True)
        self.retry_after = retry_after
        self.provider = provider
```

Note: default `retryable=True` 保留 (向后兼容 Phase 95)。Phase 96 在 adapter HTTP 4xx 路径显式传 `retryable=False` (Section 4.4)。

### 3.6 `pipeline.py`

```python
async def generate_illustration(
    *,
    project_root: Path,
    project_slug: str,
    type: _TYPE,
    chapter_num: int | None,
    style_preset: str,
    custom_prompt: str | None,
    api_key: str,
    api_host: str,
    provider: str = "minimax",  # NEW
) -> IllustrationMetadata:
    # ... (stages 1-3 unchanged) ...

    provider_fn = get_provider(provider)  # raises UnknownProviderError if invalid
    image_bytes = await provider_fn(
        prompt=final_prompt, api_key=api_key, api_host=api_host,
    )

    meta = IllustrationMetadata(
        # ... (existing fields) ...
        model=_MODEL_FOR_PROVIDER[provider],
        provider=provider,
        created_at=_iso_utc_now(),
    )

_MODEL_FOR_PROVIDER: dict[str, str] = {
    "minimax": "minimax-multimodal",
    "openai": "dall-e-3",
    "stability": "sd3-medium",
}
```

`regenerate_illustration` 同形变化: 新 `provider: str | None = None` arg；`None` → 读 `existing_meta.provider`。Route 层 (PUT `/api/illustrations/{asset_id}/regenerate`) 加 `provider: Optional[str] = Query(None)` —— query param 简单优先 (no body schema change for backward compat)。

### 3.7 `apps/studio_api/routes/illustrations.py`

```python
class GenerateRequest(BaseModel):
    project_slug: str
    type: str = Field(pattern="^(cover|chapter)$")
    chapter_num: Optional[int] = None
    style_preset: str
    custom_prompt: Optional[str] = None
    provider: Optional[str] = None  # NEW. None → fetch from project settings.

@asyncify
async def generate_illustration(req: GenerateRequest) -> GenerateResponse:
    if req.provider is not None:
        if req.provider not in KNOWN_PROVIDERS:
            raise HTTPException(400, detail=f"unknown provider '{req.provider}', expected one of {KNOWN_PROVIDERS}")
        provider = req.provider
    else:
        settings = _load_project_settings_for(req.project_slug)
        provider = settings.default_provider if settings else "minimax"
    api_key, api_host = _api_credentials_for(provider)
    # ... (rest unchanged, passes provider= to run_pipeline) ...
```

`_api_credentials_for(provider)`:
```python
def _api_credentials_for(provider: str) -> tuple[str, str]:
    from lingwen_config import APIConfig
    cfg = APIConfig()
    if provider == "minimax":
        return cfg.minimax_api_key or "", cfg.minimax_api_host or "https://api.minimaxi.com"
    if provider == "openai":
        return cfg.openai_api_key or "", cfg.openai_api_host or "https://api.openai.com"
    if provider == "stability":
        return cfg.stability_api_key or "", cfg.stability_api_host or "https://api.stability.ai"
    raise ValueError(f"unknown provider '{provider}'")
```

`_err_detail` 加 `provider` 字段 (见 Section 4.2)。

### 3.8 `apps/studio_api/routes/project_settings.py` (NEW)

```python
"""Phase 96: project settings persistence."""
from pydantic import BaseModel
from typing import Literal
import yaml

class ProjectSettings(BaseModel):
    default_provider: Literal["minimax", "openai", "stability"] = "minimax"
    # Future fields added in subsequent phases without breaking schema.

def register_project_settings(app, ctx) -> None:
    @app.put("/api/projects/{slug}/settings")
    async def put_settings(slug: str, settings: ProjectSettings) -> dict:
        project_root = _project_root_for(slug)
        _save_project_settings(project_root, settings)
        return settings.model_dump()

    @app.get("/api/projects/{slug}/settings")
    def get_settings(slug: str) -> ProjectSettings:
        project_root = _project_root_for(slug)
        return _load_project_settings(project_root) or ProjectSettings()


def _save_project_settings(root: Path, settings: ProjectSettings) -> None:
    target = root / ".lingwen" / "illustration_settings.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump(settings.model_dump()), encoding="utf-8")


def _load_project_settings(root: Path) -> ProjectSettings | None:
    target = root / ".lingwen" / "illustration_settings.yaml"
    if not target.exists():
        return None
    try:
        return ProjectSettings(**yaml.safe_load(target.read_text(encoding="utf-8")))
    except (yaml.YAMLError, ValidationError) as e:
        return None  # silently fallback to defaults
```

`_project_root_for` from `routes/illustrations.py` extracted to `routes/_helpers.py` (or duplicated ~10 LOC) for cross-route reuse. Decide during implementation.

### 3.9 Frontend

**ProjectSettingsIllustration 接 `slug: String` prop**（NEW — Phase 95 组件无 slug 因 persistence deferred）。SettingsPage 决定 active project slug 传给组件。`data-testid="project-settings-illustration"` 不变。

**`ProjectSettingsIllustration.vue`** — 加 `<select>` for default_provider：
```html
<div class="field project-settings-illustration-field">
  <label class="project-settings-illustration-label" for="default-provider">默认图片生成器</label>
  <select
    id="default-provider"
    class="project-settings-illustration-provider-select"
    :value="modelValue.default_provider"
    data-testid="project-settings-illustration-default-provider"
    @change="on_provider_change($event.target.value)"
  >
    <option value="minimax">MiniMax</option>
    <option value="openai">OpenAI DALL-E 3</option>
    <option value="stability">Stability SD3</option>
  </select>
</div>
```
Component 接 `useProjectSettingsStore`：`on_provider_change(value)` 同时 emit `update:modelValue` 和 call `store.save(slug, { default_provider: value })`。

**`GenerateIllustrationDialog.vue`** — 加 provider picker:
- 初始 selected value 从 `useProjectSettingsStore.settings?.default_provider ?? "minimax"` 读
- 用户可临时切换；emit payload 加 `provider` 字段；**不**更新 store (per-call override 不持久化)

**`useProjectSettings.js`** (NEW Pinia store):
- `state: { settings: ProjectSettings | null, slug: string | null }`
- `actions: { fetch(slug), save(slug, partial) }`
- 调 `PUT/GET /api/projects/{slug}/settings`

## 4. Data flow

### 4.1 主流程：POST /api/illustrations/generate

```
User clicks "Generate" in GenerateIllustrationDialog
  ↓
Dialog emits { project_slug, type, chapter_num, style_preset, custom_prompt, provider }
  ↓
POST /api/illustrations/generate
  ├─ Resolve: body.provider > project_settings.default_provider > "minimax"
  ├─ api_key + api_host via _api_credentials_for(provider)
  └─ run_pipeline(provider=provider, ...)
      ↓
      pipeline.generate_illustration
        ├─ Stage 1a: load chapter text + character bible
        ├─ Stage 2: LLM extract_scene
        ├─ Stage 3: compose_prompt
        ├─ Stage 4: provider_fn = get_provider(provider)
        │            provider_fn(prompt, api_key, api_host) → bytes
        │ ↓
        │   providers/<X>.py:generate
        │     ├─ POST httpx.AsyncClient(url, payload)
        │     ├─ 429 → GenerateError(retry_after=…, provider="X")
        │     ├─ 4xx (除 429) → GenerateError(retryable=False, provider="X")
        │     ├─ 5xx / Timeout / network → GenerateError(retryable=True, provider="X")
        │     └─ 200 → decode_b64_envelope(resp, provider="X") OR resp.content
        ├─ Stage 5: IllustrationMetadata(provider=provider, model=...) + storage.save_asset
        └─ Return meta
  ↓
GenerateResponse(id, type, chapter_num, style_preset, scene_json, url)
```

### 4.2 PUT /api/projects/{slug}/settings

```
User changes default_provider in ProjectSettingsIllustration dropdown
  ↓
Component emits update:modelValue + calls useProjectSettingsStore.save(slug, {default_provider})
  ↓
PUT /api/projects/{slug}/settings → routes/project_settings.py:put_settings
  ├─ Validate ProjectSettings (Pydantic, Literal)
  ├─ _save_project_settings: write <root>/.lingwen/illustration_settings.yaml
  └─ Return settings.model_dump()
```

### 4.3 GET /api/projects/{slug}/settings

```
ProjectSettingsIllustration mounts
  ↓
useProjectSettingsStore.fetch(slug)
  ↓
GET /api/projects/{slug}/settings
  ├─ _load_project_settings: read yaml OR return ProjectSettings() defaults
  └─ Corrupt yaml → silently fallback to defaults
  ↓
Store state populated → component renders with modelValue
```

### 4.4 后台：chapter complete → illustrations_auto_generate_task

```
PUT /api/write/{chapter_id} (chapter marked complete)
  ↓
chapter_marked_complete event → illustrations_auto_generate_task(slug, chapter_num, settings)
  ├─ _get_illustration_settings(slug) — Phase 96 增强: 也读 default_provider 从 yaml
  ├─ if not settings.auto_generate → return (no-op)
  └─ generate_illustration(provider=settings.default_provider, ...)
      ├─ GenerateError caught → log.warning(f"auto-generate failed [{stage}] provider={provider}: {message}")
      └─ Other exceptions → log.error
```

### 4.5 PUT /api/illustrations/{asset_id}/regenerate (atomic swap)

```
User clicks "Regenerate" on IllustrationCard
  ↓
PUT /api/illustrations/{asset_id}/regenerate?project_slug=X[&provider=Y]
  ├─ Lookup existing_meta via storage.list_assets
  ├─ Resolve provider: query/body override > existing_meta.provider > settings > "minimax"
  ├─ api_key + api_host via _api_credentials_for(resolved_provider)
  └─ run_regen(provider=resolved_provider, ...)
      ↓
      pipeline.regenerate_illustration
        ├─ Re-load chapter + character bible
        ├─ Re-extract + re-compose (new scene_json, final_prompt, prompt_hash)
        ├─ provider_fn(...) → new image bytes
        ├─ build new_meta(same asset_id, new provider/model/created_at)
        └─ storage.replace_asset (atomic; original preserved on failure)
  ↓
GenerateResponse(same asset_id, fresh scene_json + url)
```

## 5. Error handling

### 5.1 GenerateError provider attribution

每 adapter 在 raise `GenerateError` 时显式 set `provider` 字段。例：

```python
# providers/openai.py
raise GenerateError("OpenAI rate limited", retry_after=retry_after, provider="openai")
raise GenerateError("OpenAI HTTP 400: billing hard limit", provider="openai", retryable=False)
```

`_b64_decode.decode_b64_envelope` 接受 `provider=` 参数。

**Invariant**: 任何 `GenerateError` raised by provider dispatch path 必须有非 `"unknown"` 的 provider 字段。`"unknown"` 仅 legacy path (image_generator.generate direct call) 用。

### 5.2 HTTP error response shape

```python
def _err_detail(exc: IllustrationError) -> dict:
    payload = {"stage": exc.stage.value, "error": exc.message, "retryable": exc.retryable}
    if isinstance(exc, GenerateError):
        if exc.retry_after is not None:
            payload["retry_after"] = exc.retry_after
        payload["provider"] = exc.provider
    return payload
```

HTTP status mapping仍走 `STAGE_HTTP_CODES` (GenerateError → 502)。`provider` 是 secondary metadata。

### 5.3 Rate-limit semantics per provider

| Provider | retry-after header | Default fallback |
|---|---|---|
| MiniMax | seconds OR HTTP-date | 60s on non-numeric (Phase 93 RFC 7231 fallback) |
| OpenAI | seconds OR HTTP-date | 60s |
| Stability | not always present | 30s (降级默认) |

### 5.4 Provider-specific failure modes

| Provider | Known failure | HTTP | retryable | GenerateError message |
|---|---|---|---|---|
| MiniMax | `b64_json` decode fail | 200 | True | "image API non-JSON response: …" |
| OpenAI | `billing_hard_limit_reached` | 400 | False | "OpenAI HTTP 400: …" |
| OpenAI | `content_policy_violation` | 400 | False | "OpenAI HTTP 400: …" |
| OpenAI | `model_not_found` | 404 | False | "OpenAI HTTP 404: …" |
| Stability | `invalid_prompt` | 400 | False | "Stability HTTP 400: …" |
| Stability | `insufficient_credit` | 402 | False | "Stability HTTP 402: …" |

### 5.5 UI error display (Phase 96 增强)

`useIllustration` composable 现有错误处理读 `exc.detail.stage` / `exc.detail.retryable` / `exc.detail.retry_after`。Phase 96 新增读 `exc.detail.provider`：

- Provider known → `[OpenAI] 生成失败: billing limit reached. 请检查 OpenAI 账单。`
- Provider unknown → `生成失败: ...` (向后兼容)
- `retryable=False` → toast 文案换成针对性建议；按钮从 "重试" 变 "关闭"

### 5.6 Background task error swallow (增强)

```python
except IllustrationError as e:
    log.warning(
        f"auto-generate failed [{e.stage.value}] "
        f"provider={getattr(e, 'provider', 'unknown')}: {e.message}"
    )
```

### 5.7 UnknownProviderError → HTTP 400 (not 500)

Route 层校验 `req.provider not in KNOWN_PROVIDERS` → `HTTPException(400, detail=f"unknown provider '{req.provider}', expected one of {KNOWN_PROVIDERS}")`。Stage 不适用 (user input error)。

## 6. Testing strategy

### 6.1 测试分层

| Layer | Scope | Mock strategy | Count |
|---|---|---|---|
| Per-adapter unit | `providers/<X>.py:generate()` | `patch("lingwen_illustrations.providers.<X>.httpx.AsyncClient")` | 25-30 |
| Registry unit | `providers/__init__.py` | No mock (pure) | 5 |
| Metadata | provider field + backwards compat | No mock | 5 (augmented) |
| Pipeline | provider dispatch | Adapter-level mock | 3 (augmented) |
| Project settings API | yaml round-trip + fallback | No mock (tmp_path) | 5 (NEW) |
| Illustrations API | provider in body | Adapter-level mock | 3 (augmented) |
| Frontend | dropdown / picker | Pinia + Vue test utils | 13 |
| Regression guards | schema invariants | Source-only (no runtime) | 14 |
| **Total new** | | | **~77** |
| **Existing preserved** | Phase 90-95 tests | | 78 (some moved) |

### 6.2 Per-adapter test pattern (example: OpenAI)

```python
import base64, json, pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from lingwen_illustrations.exceptions import GenerateError
from lingwen_illustrations.providers.openai import generate

PNG_MAGIC = b"\x89PNG\r\n\x1a\nfake-png-bytes-here"


def _json_response(body, status_code=200):
    fake = MagicMock()
    fake.status_code = status_code
    fake.headers = {}
    fake.raise_for_status = MagicMock()
    if status_code == 200:
        fake.json.return_value = body
    else:
        fake.raise_for_status.side_effect = Exception(f"{status_code}")
        fake.json.return_value = body
    return fake


def _client_with_response(fake_response):
    mock_client = AsyncMock()
    mock_client.post.return_value = fake_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


@pytest.mark.asyncio
async def test_openai_returns_decoded_png_bytes():
    """Real API path: b64_json envelope → PNG bytes.
    DALL-E 3 returns {"created": ..., "data": [{"b64_json": "..."}]}.
    """
    b64 = base64.b64encode(PNG_MAGIC).decode("ascii")
    api_body = {"created": 1234567890, "data": [{"b64_json": b64}]}
    fake = _json_response(api_body)
    mock_client = _client_with_response(fake)
    with patch("lingwen_illustrations.providers.openai.httpx.AsyncClient", return_value=mock_client):
        result = await generate(prompt="X", api_key="k", api_host="https://api.test")
    assert result == PNG_MAGIC


@pytest.mark.asyncio
async def test_openai_content_policy_raises_non_retryable():
    """HTTP 400 content_policy_violation → GenerateError(retryable=False).
    Per Section 5.4: 4xx (除 429) are non-retryable — user/billing issue.
    """
    fake = _json_response({"error": {"code": "content_policy_violation"}}, status_code=400)
    mock_client = _client_with_response(fake)
    with patch("lingwen_illustrations.providers.openai.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="X", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is False
    assert exc.value.provider == "openai"
```

Per-adapter coverage:
- 200 b64_json success (MiniMax/OpenAI) / 200 raw PNG (Stability)
- 429 rate limit (with retry-after header)
- 429 non-numeric retry-after (RFC 7231 HTTP-date fallback)
- 4xx content policy / billing limit / model not found / invalid prompt / insufficient credit → retryable=False
- 5xx → retryable=True
- TimeoutException → retry_after=60
- ConnectionError / OSError → retryable=True
- Multi-item data array → picks data[0]
- Malformed JSON / missing data / missing b64_json → GenerateError

### 6.3 Stability adapter tests (different response shape)

```python
@pytest.mark.asyncio
async def test_stability_returns_raw_png_bytes():
    """Stability v2beta with Accept: image/* → raw PNG bytes (no envelope)."""
    fake = MagicMock()
    fake.status_code = 200
    fake.content = b"\x89PNG\r\n\x1a\nfake-png"
    fake.headers = {}
    fake.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.post.return_value = fake
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    with patch("lingwen_illustrations.providers.stability.httpx.AsyncClient", return_value=mock_client):
        result = await generate(prompt="X", api_key="k", api_host="https://api.test")
    assert result == b"\x89PNG\r\n\x1a\nfake-png"
```

### 6.4 Backwards compat tests

- `test_metadata_backwards_compat_loads_missing_provider` — `IllustrationMetadata.from_dict({"id": "x", ... no provider ...})` succeeds, `meta.provider == "minimax"`.
- `test_metadata_round_trip_with_provider` — create with provider="openai" → to_dict() → from_dict() → meta.provider == "openai".
- `test_image_generator_wrapper_delegates_to_minimax` — mock `providers.minimax.httpx.AsyncClient`, verify `image_generator.generate()` delegates to it.

### 6.5 Real-API integration tests — NOT in v1

Out of scope. Documented as BACKLOG future work: 需要 API keys + CI infra + opt-in env var。

### 6.6 Regression guards (`tests/test_phase96_image_provider_adapters.py`)

```
G1  providers/ subpackage exists with 4 files (__init__, _b64_decode, minimax, openai, stability)
G2  KNOWN_PROVIDERS == ("minimax", "openai", "stability")
G3  3 adapter modules each export async def generate(...) — ast parse
G4  GenerateError.__init__ accepts provider kwarg
G5  IllustrationMetadata has provider: str = "minimax" field — ast.parse
G6  IllustrationMetadata.from_dict() backwards compat: missing provider → "minimax"
G7  pipeline.generate_illustration signature includes provider: str = "minimax"
G8  pipeline.regenerate_illustration reads existing_meta.provider as default
G9  GenerateRequest Pydantic has provider: Optional[str] = None field
G10 route resolves provider priority (body > settings > "minimax") — source grep
G11 apps/studio_api/routes/project_settings.py exists with PUT/GET
G12 APIConfig has openai_api_host + stability_api_key + stability_api_host properties
G13 ProjectSettingsIllustration.vue has default_provider dropdown (template + data-testid)
G14 GenerateIllustrationDialog.vue emits provider in generate payload
```

### 6.7 Frontend tests (Vitest)

**ProjectSettingsIllustration.spec.ts** (4 new, augment existing 4):
- `renders_default_provider_dropdown_with_minimax_selected_when_no_setting`
- `emits_update_when_provider_changed`
- `dropdown_lists_all_three_providers`
- `data_testid_default_provider_set`

**GenerateIllustrationDialog.spec.ts** (4 new, augment existing):
- `preselects_provider_from_project_default`
- `emits_provider_in_generate_payload`
- `user_can_override_provider_per_call`
- `dialog_does_not_persist_provider_change_to_store`

**useProjectSettingsStore.spec.ts** (5 NEW):
- `fetch_loads_settings_from_api`
- `fetch_falls_back_to_defaults_when_yaml_missing`
- `save_persists_to_api`
- `state_reactive_across_components`
- `save_optimistic_with_rollback_on_500`

### 6.8 Known lessons reused

- **Phase 93 lesson 1**: mock tests matching broken behavior mask implementation bugs → adapter tests verify mock shape via **curl doc once** before writing.
- **Phase 56b2 lesson**: cwd-relative paths → tests use `tmp_path` fixture only.
- **N.14 lesson 1 v21**: docstring strip before regex search → G11/G13 source guards use `_strip_docstrings(text)` helper.
- **Phase 92/93/94/95 lessons**: regression guards **parametrized** for each provider name (not literal "openai") → future-proof for v2 providers.

## 7. Out of scope (Phase 96 v1)

- Real-API integration tests (need keys + CI infra) — BACKLOG v2 followup
- Reference image i2i (different provider APIs) — REQ-002 v2 separate phase
- LRU archive + notification center — REQ-002 v2 separate phases
- Multi-model per provider (e.g., OpenAI dall-e-3 + gpt-image-1) — v2 once user feedback
- Style preset per-provider (provider-specific prompt templates) — v2 if consistency issue
- Atomic provider fallback chain (auto-retry on alt provider) — v2 user request

## 8. Open carryover chain after Phase 96

| Item | Status |
|---|---|
| Phase 90 deviations | 5/5 closed (Phase 91/92/93/94/95) ✅ |
| Phase 95 deferred (`/api/projects/{slug}/settings`) | ✅ closed by Phase 96 (Section 3.8) |
| Phase 96 → v2 followups | i2i / LRU archive / notification center / real-API tests |

## 9. Lessons (anticipated)

### 9.1 APIConfig forward-looking properties are valuable

Phase 83 在 APIConfig 加 `openai_api_key` + `anthropic_api_key` 时 (dev: "future provider adapters") 看似 over-engineering. Phase 96 复用 — 不需新增 config 层、不破坏向后兼容。前瞻基础设施当**仅当**是真前瞻（不是 YAGNI）时有 ROI。

### 9.2 Minimal interface signature enables DRY helper extraction

3 个 adapter 用 `(prompt, *, api_key, api_host, timeout=60) → bytes` 同签名 → `_b64_decode.py` helper 自然成立 (MiniMax + OpenAI 都返 envelope)。如果当时选 extended signature (含 model/size)，helper 难提取、Phase 96 复杂 3x。

### 9.3 Provider field on errors enables UX improvements without breaking compat

GenerateError 默认 `retryable=True` 不破坏 Phase 95 行为。新 `provider` 字段是 **additive** — 旧 consumer (frontend) 不读新字段仍 work。HTTP error payload 加 provider 字段同理。

### 9.4 Persistence yaml 比 SQLite 简单足够

`<project>/.lingwen/illustration_settings.yaml` 一文件 + Pydantic model。v2 如加 multi-field schema 复杂后再换 SQLite。**Phase 96 v1 用最少 overhead 的工具**。

## 10. References

- Phase 90 spec: `docs/superpowers/specs/2026-09-15-phase-90-illustrations-design.md`
- Phase 93 handoff (b64_json real decode): `docs/superpowers/handoffs/2026-09-16-phase-93-b64-json-real-decode-handoff.md`
- Phase 95 handoff (substitution closure): `docs/superpowers/handoffs/2026-09-16-phase-95-project-settings-substitution-handoff.md`
- APIConfig (`packages/lingwen-config/src/lingwen_config/api_config_loader.py`)
- Phase 83 P3-ARCHDEBT lingwen-config handoff (forward-looking keys rationale)
- N.14 lesson 1 v21 (docstring strip pattern): Phase 57b / 93 reuse
- Phase 93 lesson 1 (mock tests matching broken behavior): per-adapter mock discipline
- Phase 92 / 93 / 94 / 95 lessons: parametrized regression guards

## 11. Implementation plan location

Implementation plan will be created via `superpowers:writing-plans` skill after user approves this spec. Plan file: `docs/superpowers/plans/2026-09-16-phase-96-image-provider-adapters.md`.