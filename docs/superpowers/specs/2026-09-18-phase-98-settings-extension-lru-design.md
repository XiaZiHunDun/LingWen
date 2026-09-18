# Phase 98 — ProjectSettings extension + LRU archive

> **设计目标**: 闭环 BACKLOG 中 4 项 v2 carryover: LRU archive + ProjectSettings extension (auto_generate / max_assets / confirm_before_generate 三个字段后端持久化 + UI 接入 + 后端 audit log)
>
> **状态**: 设计草案 — 等用户 review
>
> **版本影响**: v56.1 → v56.2
>
> **Previous**: Phase 97 v56.1 (reference image i2i — second REQ-002 v2 sub-project delivered)

---

## §1. 范围 & 非目标

### 范围内

- ProjectSettings Pydantic schema 扩展三个字段: `auto_generate` / `max_assets` / `confirm_before_generate`
- 后端 schema 迁移：旧 yaml 缺字段走 Pydantic default fill（向后兼容）
- 新模块 `packages/lingwen-illustrations/src/lingwen_illustrations/audit_log.py` — JSONL append-only illustration event log
- `storage.py` 新增 `lru_cleanup(project_root, *, type, chapter_num, max_count)` 纯函数（per-type + per-chapter 隔离）
- `pipeline.generate_illustration()` 在 `save_asset` 后同步调用 `lru_cleanup`
- 新 endpoint `POST /api/projects/{slug}/illustrations/cleanup` — 手动触发 + dry-run 模式
- `apps/studio_api/routes/write_workspace.py:40-42` 修复 `auto_generate` 真正读 yaml（之前永远 False 因为字段不存）
- `pipeline.regenerate_illustration()` 集成 audit log
- frontend `ProjectSettingsIllustration.vue` 三个字段接通 PUT 持久化（修复 line 43-45 当前只 emit 不 save）
- frontend `GenerateIllustrationDialog.vue` 加 confirm 拦截（confirm_before_generate=true 时弹原生 confirm）
- 新 invariant I090: `lingwen_illustrations/storage.py:lru_cleanup` + `lingwen_illustrations/audit_log.py:record_event` 是 illustration policy 唯一入口
- 13 regression guards G1-G13

### 非目标

- 不引入新 workspace 包（YAGNI，policy 留 inline in lingwen-illustrations）
- 不实现 illustration 删除历史快照（用户要的是当前文件被覆盖）
- 不实现 LRU 全局调度（per-save 同步触发足够）
- 不动 illustrations_api 现有 endpoints（generate / list / delete / regenerate / reference image 都不变）
- 不实现 confirm token 强制（仅前端拦截 + 后端 audit log 记录 bypassed 状态；后端不 reject）

---

## §2. 数据流 & 模块边界

```
┌────────────────────────────────────────────────────────────────────────┐
│                          Frontend (apps/dashboard)                      │
│  ┌─────────────────────────────┐  ┌───────────────────────────────────┐ │
│  │ ProjectSettingsIllustration │  │ GenerateIllustrationDialog         │ │
│  │ - PUT 3 fields via update() │  │ - if confirm: window.confirm()    │ │
│  │   call NEW save on every    │  │ - if confirmed: send + audit log   │ │
│  │   field change (line 43 fix)│  │   records "user_confirmed=true"   │ │
│  │ - max_assets / auto_generate│  │ - send via useIllustrationStore   │ │
│  │   / confirm 持久化到 yaml   │  │   .generate (existing Phase 90)   │ │
│  └──────────┬──────────────────┘  └────────────────┬──────────────────┘ │
└─────────────┼──────────────────────────────────────┼────────────────────┘
              │ PUT /api/projects/{slug}/settings     │ POST /api/illustrations/generate
              ▼                                       ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       Backend (apps/studio_api)                        │
│                                                                        │
│  project_settings.py:  PUT/GET /api/projects/{slug}/settings           │
│                        - ProjectSettings model: 4 fields                │
│                          default_provider / auto_generate              │
│                          max_assets / confirm_before_generate          │
│                        - yaml 后向兼容: Pydantic default fill           │
│                                                                        │
│  illustrations_api.py:  POST /api/illustrations/generate               │
│                        - reads settings from project_root               │
│                        - records audit (Phase 98 NEW)                  │
│                                                                        │
│  write_workspace.py: NEW auto_generate flow triggers                   │
│                        illustrations_auto_generate_task when           │
│                        settings.auto_generate is True (line 40-42)    │
│                                                                        │
│  cleanup_route.py: NEW POST /api/projects/{slug}/illustrations/cleanup │
│                        - body: { type?, chapter_num?, dry_run? }       │
│                        - calls storage.lru_cleanup                      │
│                        - returns: { deleted: [...], remaining: int }   │
└────────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────────┐
│         Package (packages/lingwen-illustrations) — I087/I089 extend    │
│                                                                        │
│  storage.py: 5 → 6 funcs                                               │
│    + lru_cleanup(project_root, *, type, chapter_num, max_count)        │
│      - list_assets filtered by type+chapter                             │
│      - sort by created_at desc (already done in list_assets)            │
│      - if len > max_count: delete oldest (len - max_count) entries     │
│      - return list of deleted metadata                                  │
│                                                                        │
│  pipeline.py: generate_illustration()                                  │
│    - after save_asset, calls lru_cleanup by meta.type+chapter_num       │
│    - settings.max_assets controls max_count                             │
│    - records audit_log event for generation                             │
│                                                                        │
│  audit_log.py: NEW module                                              │
│    + record_event(project_root, *, event, asset_meta, confirmed,       │
│                    bypassed=False, extra=None)                          │
│      - writes to <root>/.lingwen/illustration_audit.jsonl               │
│      - JSONL append-only (one event per line)                           │
│      - idempotent: audit failures (OSError) silently swallowed          │
└────────────────────────────────────────────────────────────────────────┘
```

### 关键不变量

| ID | 约束 |
|----|------|
| I087 | (Phase 90) `packages/lingwen-illustrations/` 是图片生成唯一实包 |
| I088 | (Phase 96) `packages/lingwen-illustrations/src/lingwen_illustrations/providers/` 是 provider 抽象 |
| I089 | (Phase 97) `providers/ProviderAdapter` + `supports_i2i` 扩展 i2i |
| **I090** (NEW) | `packages/lingwen-illustrations/src/lingwen_illustrations/storage.py:lru_cleanup` 是 illustration LRU 删除唯一入口；`audit_log.record_event` 是 illustration 事件记录唯一入口；`infra.illustrations.*` / `infra.illustration_settings.*` 路径非法 |

---

## §3. LRU 算法细节

```python
# storage.py 新增
def lru_cleanup(
    project_root: Path,
    *,
    type: AssetType,            # "cover" or "chapter"
    chapter_num: int | None = None,
    max_count: int,
) -> list[IllustrationMetadata]:
    """Per-type+per-chapter LRU: keep newest `max_count`, delete the rest.

    Scope:
      - type="cover"     → all <root>/assets/covers/*.jpg
      - type="chapter"   → all <root>/assets/illustrations/chapter-NNN/*.jpg
                           (chapter_num selects which chapter folder)

    Returns:
      - list of deleted metadata (oldest first). Useful for UI feedback
        and audit logging. Empty list if no-op.

    Behavior:
      - if max_count <= 0: raises StoreError("max_count must be positive")
      - if asset count <= max_count: no-op, returns []
      - deletion is idempotent (missing files silently skipped via delete_asset)
      - sort: meta.created_at desc; ties broken by meta.id asc (stable)

    Raises:
      StoreError: If type="chapter" and chapter_num is None.
      StoreError: If max_count <= 0.
    """
```

### 调用示例

```python
# In pipeline.py after save_asset (Phase 98 NEW):
def generate_illustration(project_root, ..., user_confirmed=False):
    # ... existing 4-stage flow (extract scene → prompt → generate → save_asset) ...
    save_asset(project_root, image_bytes, meta)
    
    # NEW: per-type+per-chapter LRU cleanup (synchronous, ~5ms)
    settings = _load_settings(project_root)
    if settings.max_assets > 0:
        lru_cleanup(
            project_root,
            type=meta.type,
            chapter_num=meta.chapter_num,
            max_count=settings.max_assets,
        )
    
    # NEW: audit log
    audit_log.record_event(
        project_root,
        event="generation",
        asset_meta=meta,
        confirmed=user_confirmed,
        bypassed=not user_confirmed and settings.confirm_before_generate,
    )
    return meta
```

### 测试矩阵 (`packages/lingwen-illustrations/tests/test_lru_cleanup.py`)

| # | 测试 | 输入 | 期望 |
|---|------|------|------|
| L1 | `max_count=3 keep all` | 2 assets, max=3 | deleted=[] |
| L2 | `max_count=3 delete 1` | 4 assets, max=3 | deleted=[oldest], remaining=3 |
| L3 | `max_count=3 delete 2` | 5 assets, max=3 | deleted=[oldest 2], remaining=3 |
| L4 | `cover scope` | 2 covers + 3 chapter assets, max=2 | deleted=[oldest cover] only |
| L5 | `chapter-NNN scope` | 2 assets ch1 + 3 ch2, max=2, chapter=1 | deleted=[oldest ch1] only |
| L6 | `max_count=0 raises` | max=0 | StoreError |
| L7 | `max_count<0 raises` | max=-1 | StoreError |
| L8 | `idempotent on missing` | delete file manually, then call | no error |
| L9 | `chapter_num=None for cover` | type=cover | OK (no StoreError) |
| L10 | `chapter_num=None for chapter` | type=chapter, no num | StoreError |
| L11 | `sort tie-break stable` | 2 assets same created_at | deterministic |
| L12 | `no assets dir` | fresh project | deleted=[] |

---

## §4. ProjectSettings Schema 迁移

### v1 schema (Phase 96, current)

```yaml
# .lingwen/illustration_settings.yaml
default_provider: minimax
```

### v2 schema (Phase 98)

```yaml
default_provider: minimax
auto_generate: false          # NEW (default False)
max_assets: 20                # NEW (default 20)
confirm_before_generate: false # NEW (default False)
```

### 向后兼容

```python
# apps/studio_api/routes/project_settings.py 扩展
class ProjectSettings(BaseModel):
    default_provider: Literal["minimax", "openai", "stability"] = "minimax"
    auto_generate: bool = False              # NEW
    max_assets: int = 20                     # NEW
    confirm_before_generate: bool = False    # NEW
```

Pydantic 自动用 default 填充缺失字段。`_load_settings` 现有 `ValidationError → defaults` 已覆盖完全缺失场景。

### 测试 (`apps/studio_api/tests/test_project_settings.py` 扩展)

| # | 测试 | 输入 yaml | 期望 |
|---|------|-----------|------|
| S1 | `old yaml defaults fill` | `default_provider: openai` only | default_provider=openai, others default |
| S2 | `partial yaml merge` | `max_assets: 5` only | max_assets=5, others default |
| S3 | `full yaml round-trip` | all 4 fields | all preserved |
| S4 | `malformed yaml defaults` | garbage | all defaults |
| S5 | `missing yaml defaults` | file not exists | all defaults |

---

## §5. audit_log 设计

```python
# packages/lingwen-illustrations/src/lingwen_illustrations/audit_log.py
"""JSONL append-only illustration event audit (Phase 98).

Layout: <project_root>/.lingwen/illustration_audit.jsonl (one event per line)

Best-effort: audit failures NEVER block generation. The log is for
post-hoc inspection only (e.g. "did user bypass confirm?", "which chapter
has the most cleanup activity?").
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from lingwen_illustrations.metadata import IllustrationMetadata

EventType = Literal["generation", "regeneration", "cleanup", "deletion"]


def _audit_path(project_root: Path) -> Path:
    return project_root / ".lingwen" / "illustration_audit.jsonl"


def record_event(
    project_root: Path,
    *,
    event: EventType,
    asset_meta: IllustrationMetadata | None = None,
    confirmed: bool | None = None,
    bypassed: bool = False,
    extra: dict | None = None,
) -> None:
    """Append JSONL event. Best-effort: OSError silently swallowed."""
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "asset_id": asset_meta.id if asset_meta else None,
        "asset_type": asset_meta.type if asset_meta else None,
        "chapter_num": asset_meta.chapter_num if asset_meta else None,
        "confirmed": confirmed,
        "bypassed": bypassed,
        **(extra or {}),
    }
    target = _audit_path(project_root)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError:
        pass  # best-effort, never raise
```

### 调用点

1. `pipeline.generate_illustration()`: `record_event("generation", asset_meta=meta, confirmed=user_confirmed, bypassed=not user_confirmed and settings.confirm_before_generate)`
2. `pipeline.regenerate_illustration()`: `record_event("regeneration", asset_meta=meta)`
3. `storage.lru_cleanup()` per deleted asset: `record_event("cleanup", asset_meta=deleted_meta)`

### 测试 (`packages/lingwen-illustrations/tests/test_audit_log.py`)

| # | 测试 | 验证 |
|---|------|------|
| A1 | `append + read back` | write 3 events, read file, verify 3 lines + JSON parseable |
| A2 | `OSError swallowed` | readonly parent dir, no exception raised |
| A3 | `parent dir created` | `.lingwen/` auto-created via `parents=True` |
| A4 | `unicode safe` | Chinese characters in extra, JSON dumps no escape |

---

## §6. Frontend 改动

### ProjectSettingsIllustration.vue 修复

**问题**: line 43-45 `update(key, value)` 仅 emit `update:modelValue` 到 parent；只有 `on_provider_change`（line 47-50）触发 `store.save`。三个新字段（auto_generate / max_assets / confirm_before_generate）当前**仅更新 modelValue，不持久化**。

**修复**: 把 `update()` 改造为既 emit 又**逐字段异步 save**（不需 debounce — toggle/input blur 后立即 save，每个字段独立 PUT；与 Phase 96 provider change 模式一致）：

```vue
<script setup>
import { useProjectSettingsStore } from '@/stores/useProjectSettings.js'
import ReferenceImageUpload from './ReferenceImageUpload.vue'

const props = defineProps({
  modelValue: { type: Object, required: true },
  slug: { type: String, required: true },
})
const emit = defineEmits(['update:modelValue'])

const store = useProjectSettingsStore()
const presets = [...]  // unchanged
const providers = [...]  // unchanged

// Phase 98: emit AND persist every field change (Phase 96 only persisted on provider)
async function update(key, value) {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
  await store.save(props.slug, { [key]: value })  // persist via existing PATCH logic
}

// on_provider_change simplifies to just update() (no special-case path needed)
const on_provider_change = (value) => update('default_provider', value)
</script>
```

### GenerateIllustrationDialog.vue 改动

```vue
<script setup>
// Phase 98: confirm_before_generate integration
import { useProjectSettingsStore } from '@/stores/useProjectSettings.js'

const projectSettings = useProjectSettingsStore()
const store = useIllustrationStore()

async function onConfirmGenerate() {
  // Fetch fresh settings (in case user changed toggle since last fetch)
  await projectSettings.fetch(props.slug)
  const settings = projectSettings.settings
  
  if (settings?.confirm_before_generate) {
    const provider = settings.default_provider || 'minimax'
    const ok = window.confirm(`将使用 ${provider} 生成插图。继续？`)
    if (!ok) return
  }
  await store.generate(props.slug, prompt.value, { user_confirmed: true })
}
</script>
```

`store.generate(slug, prompt, { user_confirmed: true })` 通过 `extra` 字段传到后端 audit log。

### 测试

**`useProjectSettings.spec.ts` 新增**:
| # | 测试 |
|---|------|
| U1 | `save(partial) merges with current` (already implemented line 50, test only) |
| U2 | `save({default_provider:'openai'}) preserves max_assets` |

**`ProjectSettingsIllustration.spec.ts` 已存在** — 仅跑回归（spec 已 verify 3 字段渲染）。

**`GenerateIllustrationDialog.spec.ts` 新增**:
| # | 测试 |
|---|------|
| G1 | `confirm_before_generate=true shows native confirm` |
| G2 | `confirm_before_generate=false skips confirm` |

---

## §7. 测试覆盖 & 回归守卫

### 新增测试 (31 tests)

| 文件 | 数量 | 内容 |
|------|------|------|
| `packages/lingwen-illustrations/tests/test_lru_cleanup.py` | 12 | L1-L12 |
| `packages/lingwen-illustrations/tests/test_audit_log.py` | 4 | A1-A4 |
| `packages/lingwen-illustrations/tests/test_pipeline_integration.py` | 1 NEW | `lru_cleanup called after save_asset` + `audit_event on generation` |
| `apps/studio_api/tests/test_project_settings.py` | +5 | S1-S5 |
| `apps/studio_api/tests/test_cleanup_route.py` | 5 NEW | POST endpoint success + dry-run + bad request |
| `apps/dashboard/src/stores/useProjectSettings.spec.ts` | +2 | U1-U2 |
| `apps/dashboard/src/components/illustrations/GenerateIllustrationDialog.spec.ts` | +2 | G1-G2 |

### 回归守卫 `tests/test_phase98_settings_extension_lru.py` (13 guards)

| Guard | 验证 |
|-------|------|
| G1 | `storage.lru_cleanup` exists (defensive grep) |
| G2 | `ProjectSettings` has 4 fields (default_provider / auto_generate / max_assets / confirm_before_generate) |
| G3 | `audit_log.record_event` exists |
| G4 | `pipeline.generate_illustration` calls `lru_cleanup` after `save_asset` (regex anchored) |
| G5 | POST `/api/projects/{slug}/illustrations/cleanup` endpoint registered |
| G6 | PUT `/api/projects/{slug}/settings` accepts 4-field body 200 OK |
| G7 | `write_workspace.py` reads `auto_generate` from settings (line 40) |
| G8 | `ProjectSettingsIllustration.spec.ts` contains all 3 field testids |
| G9 | `GenerateIllustrationDialog` has confirm logic |
| G10 | yaml schema backwards-compat (old yaml → defaults filled) |
| G11 | `audit_log.record_event` failures don't raise (defensive try/except) |
| G12 | I090 invariant exists in `.lingwen/architecture.yml` |
| G13 | per-type+per-chapter scope (cover cleanup doesn't touch chapter) |

---

## §8. 验证门

1. `uv run pytest packages/lingwen-illustrations/tests/ -v` → 12+4+1 NEW + 既存 178 → 195 PASS
2. `uv run pytest apps/studio_api/tests/test_project_settings.py apps/studio_api/tests/test_cleanup_route.py` → 5+5 NEW + 既存 → 125 PASS
3. `cd apps/dashboard && pnpm vitest run` → 2+2 NEW + 既存 2055 → 2059 PASS
4. `cd apps/dashboard && pnpm tsc --noEmit` → 0 new errors
5. `cd apps/dashboard && pnpm exec knip` → 0
6. `ruff check packages/lingwen-illustrations/src/ apps/studio_api/routes/project_settings.py apps/studio_api/routes/cleanup_route.py` → clean
7. 13/13 regression guards GREEN

---

## §9. Commit 计划 (按 LingWen 2026-09-15 simplified workflow: direct master commits)

| # | commit | 内容 |
|---|--------|------|
| 1 | `docs(phase-98): spec` | 本文档 |
| 2 | `docs(phase-98): plan` | 实现计划 |
| 3 | `test(phase-98): project_settings schema migration TDD red` | S1-S5 + G2/G10 |
| 4 | `feat(phase-98): ProjectSettings 3 new fields` | schema 扩展 |
| 5 | `test(phase-98): lru_cleanup TDD red` | L1-L12 |
| 6 | `feat(phase-98): storage.lru_cleanup + audit_log module` | LRU + audit_log |
| 7 | `feat(phase-98): pipeline calls lru_cleanup after save_asset` | pipeline 集成 |
| 8 | `feat(phase-98): write_workspace auto_generate from yaml` | line 40-42 真正激活 |
| 9 | `feat(phase-98): POST /cleanup endpoint + audit log on regenerate` | cleanup route + regenerate audit |
| 10 | `feat(phase-98): frontend useProjectSettings PATCH + GenerateIllustrationDialog confirm` | U1-U2 + G1-G2 |
| 11 | `test(phase-98): 13 regression guards G1-G13` | 守卫 |
| 12 | `docs(phase-98): CLAUDE.md v56.1 → v56.2 + I090 + handoff` | 文档同步 |

**估算**: 12 atomic commits, ~6-8 hour 实现 + 1 hour docs.

---

## §10. 风险 & 缓解

| 风险 | 缓解 |
|------|------|
| **旧 yaml 缺字段 → Pydantic ValidationError** | 测试 S1/S2 + `_load_settings` 已有 default fallback |
| **LRU 在 hot path 增加 latency** | `list_assets` 已 O(n) + max=20 → ~5ms；端到端测 pipeline 总耗时 baseline vs after 对比 |
| **audit log 写失败影响生成** | `record_event` best-effort OSError swallow，pipeline 不感知 |
| **`update()` 改造影响 provider 字段双 save** | `on_provider_change` 简化为 `update()` 一行调用（去重复）— Phase 96 的 provider 行为完全保留 |
| **ProjectSettingsIllustration spec 已写 3 字段但代码未挂载** | G8 regression grep spec + G7/G9 端到端 mount test |
| **per-chapter 限粒度导致 max_assets=20 语义模糊** | UI label 显式 "资产数量上限（每章节/封面）" 区分 |
| **GenerateIllustrationDialog confirm 弹窗 vs SettingsPage 实际触发** | spec test 覆盖 G1/G2 + 手动 e2e 验证 |
| **`.turbo/cache/` gitignore** | 顺带补 .gitignore entry（一个 line，不算 commit） |

---

## §11. 闭环后状态

### BACKLOG 闭环 4 项

- ✅ **LRU archive** (REQ-002 v2 第三子项目)
- ✅ **ProjectSettings extension** (REQ-002 v2 — auto_generate / max_assets / confirm_before_generate 三字段后端持久化 + UI 接入 + audit log)
- ✅ **write_workspace auto_generate 真激活** (写章节时自动生成插图)
- ✅ **I090 invariant NEW** (illustration policy 唯一入口)

### REQ-002 v2 remaining (5 项)

- LRU archive ✅ **(this phase)**
- notification center
- multi-model per provider
- atomic provider fallback
- ProjectSettings extension ✅ **(this phase)**

### Future work candidates

- Phase 99+ 候选: notification center / multi-model / atomic fallback / REQ-004 团队协作
- `.turbo/cache/` gitignore 修复 (5min 小项, 顺带)

---

## §12. 关联 spec/handoff

- 本 spec: `docs/superpowers/specs/2026-09-18-phase-98-settings-extension-lru-design.md`
- 关联 spec: `docs/superpowers/specs/2026-09-18-phase-97-reference-image-i2i-design.md` (前一 phase)
- handoff: `docs/superpowers/handoffs/2026-09-18-phase-98-settings-extension-lru-handoff.md` (Phase 98 完成后写)
- BACKLOG: `collaboration/BACKLOG.md` REQ-002 v2 行更新
- CURRENT_STATUS: `collaboration/CURRENT_STATUS.md` 新增 Phase 98 行

---

**SPEC STATUS**: 草案 v0, 等用户 review
