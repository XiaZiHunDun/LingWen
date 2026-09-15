# Phase 90 — REQ-002 多模态（封面/插图生成）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增封面 + 章节插图生成能力，含两阶段 pipeline (LLM 抽取 → MiniMax 生图) + 资产库 + UI 集成（写栏/库/设置）。

**Architecture:** 新建真包 `packages/lingwen-illustrations/` (3 workspace deps)，FastAPI 4 路由 + 前端 3 页面 + 1 集成 hook + 7 个回归守门。沿用 Phase 79-87 ARCHDEBT-REAL cycle 模式（5-7 atomic commits）。

**Tech Stack:** Python 3.12+ (uv workspace) / FastAPI / httpx (MiniMax API) / Vue 3 + Pinia / Naive UI / vitest + pytest

**Spec:** `docs/superpowers/specs/2026-09-15-phase-90-illustrations-design.md`

**Workflow:** 直接 master commit (no worktree, 2026-09-15 simplified)。

---

## 文件总览

**新建**:
- `packages/lingwen-illustrations/pyproject.toml`
- `packages/lingwen-illustrations/src/lingwen_illustrations/__init__.py`
- `packages/lingwen-illustrations/src/lingwen_illustrations/metadata.py`
- `packages/lingwen-illustrations/src/lingwen_illustrations/style_templates.py`
- `packages/lingwen-illustrations/src/lingwen_illustrations/storage.py`
- `packages/lingwen-illustrations/src/lingwen_illustrations/prompt_builder.py`
- `packages/lingwen-illustrations/src/lingwen_illustrations/image_generator.py`
- `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py`
- `packages/lingwen-illustrations/src/lingwen_illustrations/exceptions.py`
- `packages/lingwen-illustrations/tests/__init__.py`
- `packages/lingwen-illustrations/tests/test_metadata.py`
- `packages/lingwen-illustrations/tests/test_style_templates.py`
- `packages/lingwen-illustrations/tests/test_storage.py`
- `packages/lingwen-illustrations/tests/test_prompt_builder.py`
- `packages/lingwen-illustrations/tests/test_image_generator.py`
- `packages/lingwen-illustrations/tests/test_pipeline.py`
- `apps/studio_api/routes/illustrations.py`
- `apps/dashboard/src/composables/useIllustration.js`
- `apps/dashboard/src/stores/useIllustrationStore.js`
- `apps/dashboard/src/components/illustrations/IllustrationGallery.vue`
- `apps/dashboard/src/components/illustrations/IllustrationCard.vue`
- `apps/dashboard/src/components/illustrations/GenerateIllustrationDialog.vue`
- `tests/test_phase90_illustrations.py` (回归守门)

**修改**:
- `pyproject.toml` (root, workspace member + dep)
- `.lingwen/architecture.yml` (I087 invariant)
- `apps/studio_api/app.py` (注册 router)
- `apps/dashboard/src/pages/WriteWorkspacePage.vue` (生成按钮 + 侧栏)
- `apps/dashboard/src/pages/LibraryPage.vue` (资产 tab)
- `apps/dashboard/src/pages/ProjectSettingsPage.vue` (插图偏好)
- `apps/studio_api/tests/test_illustrations_api.py` (新建测试)
- `apps/dashboard/tests/composables/useIllustration.test.js` (新建)
- `apps/dashboard/tests/components/illustrations/*.spec.js` (新建 3 个)

---

## Task 1: Package scaffold + I087 invariant

**Files:**
- Modify: `pyproject.toml:1-100` (root, workspace members + deps)
- Create: `packages/lingwen-illustrations/pyproject.toml`
- Create: `packages/lingwen-illustrations/src/lingwen_illustrations/__init__.py`
- Modify: `.lingwen/architecture.yml` (追加 I087)

- [ ] **Step 1.1: 修改 root pyproject.toml** — workspace.members 加 `packages/lingwen-illustrations`，workspace.dependencies 加 `lingwen-illustrations = { workspace = true }`

- [ ] **Step 1.2: 创建 `packages/lingwen-illustrations/pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "lingwen-illustrations"
version = "0.1.0"
description = "LingWen canonical illustrations module (Phase 90 REQ-002 multimodal)"
requires-python = ">=3.11"
dependencies = [
    "lingwen-llm-service",        # I057 — Stage 1 LLM extraction
    "lingwen-project-characters", # I073 — character bible
    "lingwen-paths",              # I052 — project root resolution
]
# NOT-LEAF — 3 workspace deps

[tool.hatch.build.targets.wheel]
packages = ["src/lingwen_illustrations"]
```

- [ ] **Step 1.3: 创建 `packages/lingwen-illustrations/src/lingwen_illustrations/__init__.py`** (空骨架, 仅版本号 + re-exports 占位)

```python
"""lingwen-illustrations — canonical multimodal package (Phase 90)."""

from __future__ import annotations

__version__ = "0.1.0"
__all__: list[str] = []
```

- [ ] **Step 1.4: 在 `.lingwen/architecture.yml` 追加 I087 invariant**

在文件 invariants section 末尾加：

```yaml
  - id: I087
    rule: "packages/lingwen-illustrations/ 是图片生成（封面 + 章节插图）的唯一实包；infra.illustrations.* 路径非法"
    severity: error
    scope: all future REQ-002 multimodal code
```

- [ ] **Step 1.5: 运行 `uv sync` 验证 workspace 识别**

```bash
cd /home/ailearn/projects/LingWen && uv sync --all-packages
```

Expected: 成功识别新包

- [ ] **Step 1.6: 提交**

```bash
git add pyproject.toml packages/lingwen-illustrations/ .lingwen/architecture.yml
git commit -m "feat(phase-90): scaffold lingwen-illustrations package + I087"
```

---

## Task 2: exceptions.py — 自定义异常类

**Files:**
- Create: `packages/lingwen-illustrations/src/lingwen_illustrations/exceptions.py`
- Create: `packages/lingwen-illustrations/tests/test_exceptions.py`

- [ ] **Step 2.1: 写失败测试** `tests/test_exceptions.py`

```python
"""Test custom exception hierarchy for illustrations pipeline."""

from lingwen_illustrations.exceptions import (
    IllustrationError,
    LoadError,
    ExtractError,
    ComposeError,
    GenerateError,
    StoreError,
    Stage,
)


def test_stage_enum_values():
    assert Stage.LOAD == "load"
    assert Stage.EXTRACT == "extract"
    assert Stage.COMPOSE == "compose"
    assert Stage.GENERATE == "generate"
    assert Stage.STORE == "store"


def test_base_error_includes_stage_and_retryable():
    err = IllustrationError(Stage.LOAD, "chapter not found", retryable=False)
    assert err.stage == Stage.LOAD
    assert str(err) == "[load] chapter not found"
    assert err.retryable is False


def test_subclass_default_retryable():
    assert LoadError("x").retryable is False
    assert ExtractError("x").retryable is True
    assert ComposeError("x").retryable is False
    assert GenerateError("x", retry_after=30).retryable is True
    assert GenerateError("x", retry_after=30).retry_after == 30
    assert StoreError("x").retryable is False


def test_subclass_inherits_stage():
    assert LoadError("x").stage == Stage.LOAD
    assert ExtractError("x").stage == Stage.EXTRACT
```

- [ ] **Step 2.2: 跑测试确认 RED**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_exceptions.py -v
```

Expected: ImportError 或 ModuleNotFoundError

- [ ] **Step 2.3: 写实现** `src/lingwen_illustrations/exceptions.py`

```python
"""Custom exception hierarchy with stage-level error reporting.

Each exception maps to one Stage of the pipeline (load/extract/compose/
generate/store), enabling precise error reporting in API responses and
frontend retry logic.
"""

from __future__ import annotations

from enum import Enum


class Stage(str, Enum):
    """Pipeline stages. Used as error code in API responses."""

    LOAD = "load"
    EXTRACT = "extract"
    COMPOSE = "compose"
    GENERATE = "generate"
    STORE = "store"


class IllustrationError(Exception):
    """Base exception. All pipeline errors derive from this."""

    def __init__(self, stage: Stage, message: str, *, retryable: bool = False) -> None:
        super().__init__(f"[{stage.value}] {message}")
        self.stage = stage
        self.retryable = retryable
        self.message = message


class LoadError(IllustrationError):
    """Project / chapter / character bible loading failure."""

    def __init__(self, message: str) -> None:
        super().__init__(Stage.LOAD, message, retryable=False)


class ExtractError(IllustrationError):
    """Stage 1 LLM extraction failure. Usually transient."""

    def __init__(self, message: str) -> None:
        super().__init__(Stage.EXTRACT, message, retryable=True)


class ComposeError(IllustrationError):
    """Stage 2 prompt template compose failure (e.g. invalid preset)."""

    def __init__(self, message: str) -> None:
        super().__init__(Stage.COMPOSE, message, retryable=False)


class GenerateError(IllustrationError):
    """Stage 3 MiniMax API failure (rate limit / network / timeout)."""

    def __init__(self, message: str, *, retry_after: int | None = None) -> None:
        super().__init__(Stage.GENERATE, message, retryable=True)
        self.retry_after = retry_after


class StoreError(IllustrationError):
    """File system write failure (disk full / permission / invalid path)."""

    def __init__(self, message: str) -> None:
        super().__init__(Stage.STORE, message, retryable=False)


__all__ = [
    "Stage",
    "IllustrationError",
    "LoadError",
    "ExtractError",
    "ComposeError",
    "GenerateError",
    "StoreError",
]
```

- [ ] **Step 2.4: 跑测试确认 GREEN**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_exceptions.py -v
```

Expected: 4 passed

- [ ] **Step 2.5: 提交**

```bash
git add packages/lingwen-illustrations/
git commit -m "feat(phase-90): exception hierarchy (Stage enum + 5 stage errors)"
```

---

## Task 3: metadata.py — dataclass + JSON 序列化

**Files:**
- Create: `packages/lingwen-illustrations/src/lingwen_illustrations/metadata.py`
- Create: `packages/lingwen-illustrations/tests/test_metadata.py`

- [ ] **Step 3.1: 写失败测试** `tests/test_metadata.py`

```python
"""Test IllustrationMetadata dataclass serialization."""

from __future__ import annotations

import json
from lingwen_illustrations.metadata import IllustrationMetadata


def _sample_metadata() -> IllustrationMetadata:
    return IllustrationMetadata(
        id="1726416000-abc123",
        type="chapter",
        project_slug="starfall-era",
        chapter_num=17,
        style_preset="ink",
        custom_prompt=None,
        scene_json={
            "subject": "林渊",
            "scene": "幽冥谷入口",
            "mood": "紧张",
            "characters_in_scene": [
                {"name": "林渊", "role": "主角", "key_visual": "黑发青年"}
            ],
            "extraction_confidence": 0.85,
        },
        final_prompt="古风水墨风格...",
        prompt_hash="sha256:deadbeef",
        model="minimax-multimodal",
        created_at="2026-09-15T10:00:00Z",
    )


def test_to_dict_contains_all_fields():
    meta = _sample_metadata()
    d = meta.to_dict()
    assert d["id"] == "1726416000-abc123"
    assert d["type"] == "chapter"
    assert d["chapter_num"] == 17
    assert d["scene_json"]["extraction_confidence"] == 0.85
    assert d["created_at"] == "2026-09-15T10:00:00Z"


def test_to_json_parses_back():
    meta = _sample_metadata()
    raw = meta.to_json()
    parsed = json.loads(raw)
    assert parsed["id"] == "1726416000-abc123"
    assert parsed["scene_json"]["characters_in_scene"][0]["name"] == "林渊"


def test_from_dict_roundtrip():
    meta = _sample_metadata()
    d = meta.to_dict()
    restored = IllustrationMetadata.from_dict(d)
    assert restored.id == meta.id
    assert restored.chapter_num == meta.chapter_num
    assert restored.scene_json == meta.scene_json


def test_from_json_roundtrip():
    meta = _sample_metadata()
    raw = meta.to_json()
    restored = IllustrationMetadata.from_json(raw)
    assert restored == meta


def test_chapter_num_optional_for_cover():
    meta = IllustrationMetadata(
        id="x",
        type="cover",
        project_slug="p",
        chapter_num=None,
        style_preset="ink",
        custom_prompt=None,
        scene_json={},
        final_prompt="x",
        prompt_hash="sha256:x",
        model="minimax",
        created_at="2026-09-15T00:00:00Z",
    )
    d = meta.to_dict()
    assert d["chapter_num"] is None
```

- [ ] **Step 3.2: 跑测试确认 RED**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_metadata.py -v
```

Expected: ImportError on `from lingwen_illustrations.metadata import ...`

- [ ] **Step 3.3: 写实现** `src/lingwen_illustrations/metadata.py`

```python
"""IllustrationMetadata dataclass for per-asset .meta.json sidecar.

Stored alongside every .jpg file at:
  <project>/assets/covers/<id>.jpg.meta.json
  <project>/assets/illustrations/chapter-NNN/<id>.jpg.meta.json
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class IllustrationMetadata:
    """Immutable metadata for one generated illustration asset."""

    id: str
    type: str  # "chapter" | "cover"
    project_slug: str
    chapter_num: int | None  # None for cover
    style_preset: str  # "ink" | "realistic" | "anime"
    custom_prompt: str | None
    scene_json: dict[str, Any]  # Stage 1 output
    final_prompt: str
    prompt_hash: str
    model: str
    created_at: str  # ISO 8601

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "IllustrationMetadata":
        return cls(**d)

    @classmethod
    def from_json(cls, raw: str) -> "IllustrationMetadata":
        return cls.from_dict(json.loads(raw))


__all__ = ["IllustrationMetadata"]
```

- [ ] **Step 3.4: 跑测试确认 GREEN**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_metadata.py -v
```

Expected: 5 passed

- [ ] **Step 3.5: ruff 检查 + 提交**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m ruff check packages/lingwen-illustrations/
git add packages/lingwen-illustrations/
git commit -m "feat(phase-90): IllustrationMetadata dataclass + JSON serialization"
```

---

## Task 4: style_templates.py — 3 风格预设 + override

**Files:**
- Create: `packages/lingwen-illustrations/src/lingwen_illustrations/style_templates.py`
- Create: `packages/lingwen-illustrations/tests/test_style_templates.py`

- [ ] **Step 4.1: 写失败测试** `tests/test_style_templates.py`

```python
"""Test 3 style presets + custom override merge."""

from __future__ import annotations

import pytest
from lingwen_illustrations.style_templates import (
    PRESETS,
    compose,
    list_presets,
)
from lingwen_illustrations.exceptions import ComposeError


def test_list_presets_returns_three():
    presets = list_presets()
    assert set(presets) == {"ink", "realistic", "anime"}


def test_compose_ink_includes_chinese_aesthetic():
    scene = {
        "subject": "林渊",
        "scene": "幽冥谷",
        "mood": "紧张",
        "characters_in_scene": [{"name": "林渊", "role": "主角", "key_visual": "黑发"}],
        "extraction_confidence": 0.9,
    }
    prompt = compose("ink", scene_json=scene, custom_prompt=None)
    assert "古风" in prompt or "水墨" in prompt
    assert "林渊" in prompt
    assert "幽冥谷" in prompt
    assert "紧张" in prompt


def test_compose_realistic_modern():
    scene = {
        "subject": "测试",
        "scene": "城市",
        "mood": "现代",
        "characters_in_scene": [],
        "extraction_confidence": 0.8,
    }
    prompt = compose("realistic", scene_json=scene, custom_prompt=None)
    assert "photorealistic" in prompt.lower() or "realistic" in prompt.lower()


def test_compose_anime_modern():
    scene = {
        "subject": "测试",
        "scene": "校园",
        "mood": "轻松",
        "characters_in_scene": [],
        "extraction_confidence": 0.7,
    }
    prompt = compose("anime", scene_json=scene, custom_prompt=None)
    assert "anime" in prompt.lower() or "illustration" in prompt.lower()


def test_compose_with_custom_prompt_appends():
    scene = {
        "subject": "x",
        "scene": "y",
        "mood": "z",
        "characters_in_scene": [],
        "extraction_confidence": 0.5,
    }
    prompt = compose("ink", scene_json=scene, custom_prompt="镜头给远景、雾重")
    assert "镜头给远景、雾重" in prompt


def test_compose_invalid_preset_raises_compose_error():
    scene = {"subject": "x", "scene": "y", "mood": "z", "characters_in_scene": [], "extraction_confidence": 0.5}
    with pytest.raises(ComposeError) as exc:
        compose("foo", scene_json=scene, custom_prompt=None)
    assert "unknown preset" in str(exc.value).lower() or "foo" in str(exc.value)


def test_compose_includes_all_characters():
    scene = {
        "subject": "战斗场面",
        "scene": "对决",
        "mood": "激烈",
        "characters_in_scene": [
            {"name": "林渊", "role": "主角", "key_visual": "黑发"},
            {"name": "苏婉儿", "role": "女主", "key_visual": "白衣"},
        ],
        "extraction_confidence": 0.9,
    }
    prompt = compose("ink", scene_json=scene, custom_prompt=None)
    assert "林渊" in prompt
    assert "苏婉儿" in prompt
    assert "黑发" in prompt
    assert "白衣" in prompt
```

- [ ] **Step 4.2: 跑测试确认 RED**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_style_templates.py -v
```

Expected: ImportError

- [ ] **Step 4.3: 写实现** `src/lingwen_illustrations/style_templates.py`

```python
"""Style preset templates + custom prompt override.

3 fixed presets (ink / realistic / anime). Custom prompt appended
verbatim if provided. Validation raises ComposeError on invalid preset.
"""

from __future__ import annotations

from typing import Any
from lingwen_illustrations.exceptions import ComposeError


# Style template fragments. Each is a base instruction appended before
# scene content. Custom prompts are appended after the scene.
_STYLE_TEMPLATES: dict[str, str] = {
    "ink": (
        "古风水墨画风格，宣纸质感，淡墨晕染，"
        "留白构图，"
    ),
    "realistic": (
        "Photorealistic digital painting, high detail, "
        "cinematic lighting, 8k resolution, "
    ),
    "anime": (
        "Anime illustration style, vibrant colors, "
        "clean linework, expressive characters, "
    ),
}


def list_presets() -> list[str]:
    """Return available style preset names."""
    return list(_STYLE_TEMPLATES.keys())


def compose(
    preset: str,
    *,
    scene_json: dict[str, Any],
    custom_prompt: str | None,
) -> str:
    """Compose final image generation prompt from preset + scene + override.

    Args:
        preset: One of "ink" | "realistic" | "anime".
        scene_json: Stage 1 extraction output with subject/scene/mood/
            characters_in_scene fields.
        custom_prompt: Optional user override, appended verbatim.

    Returns:
        Final prompt string for image API.

    Raises:
        ComposeError: If preset is unknown or scene_json is malformed.
    """
    if preset not in _STYLE_TEMPLATES:
        raise ComposeError(f"unknown preset '{preset}'; choose from {list_presets()}")

    for required in ("subject", "scene", "mood", "characters_in_scene"):
        if required not in scene_json:
            raise ComposeError(f"scene_json missing required field '{required}'")

    parts: list[str] = [_STYLE_TEMPLATES[preset]]

    parts.append(f"主体: {scene_json['subject']}")
    parts.append(f"场景: {scene_json['scene']}")
    parts.append(f"氛围: {scene_json['mood']}")

    for char in scene_json["characters_in_scene"]:
        name = char.get("name", "未命名")
        visual = char.get("key_visual", "")
        parts.append(f"角色 {name}: {visual}")

    if custom_prompt:
        parts.append(f"附加: {custom_prompt}")

    return "。".join(parts)


PRESETS = list_presets

__all__ = ["PRESETS", "compose", "list_presets"]
```

- [ ] **Step 4.4: 跑测试确认 GREEN**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_style_templates.py -v
```

Expected: 7 passed

- [ ] **Step 4.5: ruff + 提交**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m ruff check packages/lingwen-illustrations/
git add packages/lingwen-illustrations/
git commit -m "feat(phase-90): style_templates with 3 presets + override merge"
```

---

## Task 5: storage.py — 资产 IO + sidecar

**Files:**
- Create: `packages/lingwen-illustrations/src/lingwen_illustrations/storage.py`
- Create: `packages/lingwen-illustrations/tests/test_storage.py`

- [ ] **Step 5.1: 写失败测试** `tests/test_storage.py`

```python
"""Test asset file IO + .meta.json sidecar writing."""

from __future__ import annotations

from pathlib import Path
import pytest
from lingwen_illustrations.storage import (
    asset_path,
    save_asset,
    delete_asset,
    list_assets,
)
from lingwen_illustrations.metadata import IllustrationMetadata
from lingwen_illustrations.exceptions import StoreError


def _sample_meta(id: str = "test-id", chapter_num: int | None = 17) -> IllustrationMetadata:
    return IllustrationMetadata(
        id=id,
        type="chapter" if chapter_num else "cover",
        project_slug="test-project",
        chapter_num=chapter_num,
        style_preset="ink",
        custom_prompt=None,
        scene_json={"subject": "x", "scene": "y", "mood": "z", "characters_in_scene": [], "extraction_confidence": 0.8},
        final_prompt="test prompt",
        prompt_hash="sha256:abc",
        model="minimax-multimodal",
        created_at="2026-09-15T10:00:00Z",
    )


def test_asset_path_cover(tmp_path: Path):
    p = asset_path(tmp_path, type="cover", id="abc")
    assert p == tmp_path / "assets" / "covers" / "abc.jpg"


def test_asset_path_chapter(tmp_path: Path):
    p = asset_path(tmp_path, type="chapter", id="abc", chapter_num=17)
    assert p == tmp_path / "assets" / "illustrations" / "chapter-017" / "abc.jpg"


def test_save_asset_writes_jpg_and_meta(tmp_path: Path):
    meta = _sample_meta(id="abc123")
    image_bytes = b"\xff\xd8\xff\xe0fake-jpeg-bytes"

    result_path = save_asset(tmp_path, image_bytes, meta)

    assert result_path == tmp_path / "assets" / "illustrations" / "chapter-017" / "abc123.jpg"
    assert result_path.exists()
    assert result_path.read_bytes() == image_bytes

    sidecar = result_path.with_suffix(result_path.suffix + ".meta.json")
    assert sidecar.exists()
    assert "abc123" in sidecar.read_text()


def test_save_asset_creates_parents(tmp_path: Path):
    meta = _sample_meta(id="x", chapter_num=5)
    save_asset(tmp_path, b"data", meta)
    assert (tmp_path / "assets" / "illustrations" / "chapter-005").exists()


def test_delete_asset_removes_jpg_and_meta(tmp_path: Path):
    meta = _sample_meta(id="del")
    save_asset(tmp_path, b"data", meta)
    delete_asset(tmp_path, meta)
    assert not (tmp_path / "assets" / "illustrations" / "chapter-017" / "del.jpg").exists()
    assert not (tmp_path / "assets" / "illustrations" / "chapter-017" / "del.jpg.meta.json").exists()


def test_list_assets_returns_all(tmp_path: Path):
    save_asset(tmp_path, b"a", _sample_meta(id="a", chapter_num=1))
    save_asset(tmp_path, b"b", _sample_meta(id="b", chapter_num=2))
    save_asset(tmp_path, b"c", IllustrationMetadata(
        id="c", type="cover", project_slug="test", chapter_num=None,
        style_preset="ink", custom_prompt=None, scene_json={},
        final_prompt="", prompt_hash="sha256:c", model="m", created_at="2026-09-15T00:00:00Z",
    ))
    assets = list_assets(tmp_path)
    assert len(assets) == 3
    types = {a.type for a in assets}
    assert types == {"chapter", "cover"}


def test_list_assets_empty_dir(tmp_path: Path):
    assert list_assets(tmp_path) == []


def test_save_asset_invalid_type_raises():
    from lingwen_illustrations.storage import asset_path as _ap
    with pytest.raises(StoreError):
        _ap(Path("/tmp"), type="bogus", id="x")  # type: ignore[arg-type]
```

- [ ] **Step 5.2: 跑测试确认 RED**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_storage.py -v
```

Expected: ImportError

- [ ] **Step 5.3: 写实现** `src/lingwen_illustrations/storage.py`

```python
"""Asset file IO with .meta.json sidecar management.

Layout:
  <project>/assets/covers/<id>.jpg + .meta.json
  <project>/assets/illustrations/chapter-NNN/<id>.jpg + .meta.json
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal
from lingwen_illustrations.metadata import IllustrationMetadata
from lingwen_illustrations.exceptions import StoreError

AssetType = Literal["cover", "chapter"]


def asset_path(
    project_root: Path,
    *,
    type: AssetType,
    id: str,
    chapter_num: int | None = None,
) -> Path:
    """Compute the .jpg path for a given asset type / id.

    Raises:
        StoreError: If type is invalid or chapter_num missing for chapter type.
    """
    if type == "cover":
        return project_root / "assets" / "covers" / f"{id}.jpg"
    if type == "chapter":
        if chapter_num is None:
            raise StoreError("chapter_num required for chapter assets")
        return project_root / "assets" / "illustrations" / f"chapter-{chapter_num:03d}" / f"{id}.jpg"
    raise StoreError(f"invalid asset type: {type}")


def save_asset(
    project_root: Path,
    image_bytes: bytes,
    meta: IllustrationMetadata,
) -> Path:
    """Write image bytes + .meta.json sidecar. Returns image path."""
    jpg_path = asset_path(
        project_root,
        type=meta.type,  # type: ignore[arg-type]
        id=meta.id,
        chapter_num=meta.chapter_num,
    )
    jpg_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        jpg_path.write_bytes(image_bytes)
    except OSError as e:
        raise StoreError(f"failed to write {jpg_path}: {e}") from e

    sidecar = jpg_path.with_suffix(jpg_path.suffix + ".meta.json")
    try:
        sidecar.write_text(meta.to_json(), encoding="utf-8")
    except OSError as e:
        # Roll back image write to avoid orphan
        try:
            jpg_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise StoreError(f"failed to write sidecar {sidecar}: {e}") from e

    return jpg_path


def delete_asset(project_root: Path, meta: IllustrationMetadata) -> None:
    """Remove image + sidecar. Idempotent (missing files are OK)."""
    jpg_path = asset_path(
        project_root,
        type=meta.type,  # type: ignore[arg-type]
        id=meta.id,
        chapter_num=meta.chapter_num,
    )
    sidecar = jpg_path.with_suffix(jpg_path.suffix + ".meta.json")
    for p in (jpg_path, sidecar):
        try:
            p.unlink(missing_ok=True)
        except OSError as e:
            raise StoreError(f"failed to delete {p}: {e}") from e


def list_assets(project_root: Path) -> list[IllustrationMetadata]:
    """Walk asset dirs and load all .meta.json sidecars. Returns sorted by created_at desc."""
    assets: list[IllustrationMetadata] = []
    assets_dir = project_root / "assets"
    if not assets_dir.exists():
        return []

    for sidecar in assets_dir.rglob("*.jpg.meta.json"):
        try:
            raw = sidecar.read_text(encoding="utf-8")
            meta = IllustrationMetadata.from_json(raw)
            assets.append(meta)
        except (OSError, ValueError):
            # Skip corrupt sidecars; do not crash whole listing
            continue

    assets.sort(key=lambda m: m.created_at, reverse=True)
    return assets


__all__ = ["asset_path", "save_asset", "delete_asset", "list_assets"]
```

- [ ] **Step 5.4: 跑测试确认 GREEN**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_storage.py -v
```

Expected: 8 passed

- [ ] **Step 5.5: ruff + 提交**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m ruff check packages/lingwen-illustrations/
git add packages/lingwen-illustrations/
git commit -m "feat(phase-90): storage layer (save/asset_path/delete/list + sidecar)"
```

---

## Task 6: prompt_builder.py — Stage 1 LLM 抽取

**Files:**
- Create: `packages/lingwen-illustrations/src/lingwen_illustrations/prompt_builder.py`
- Create: `packages/lingwen-illustrations/tests/test_prompt_builder.py`

- [ ] **Step 6.1: 写失败测试** `tests/test_prompt_builder.py`

```python
"""Test Stage 1 LLM extraction: prompt build + JSON parse + error handling."""

from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock
from lingwen_illustrations.prompt_builder import (
    build_extraction_prompt,
    parse_extraction_response,
    extract_scene,
)
from lingwen_illustrations.exceptions import ExtractError


def test_build_extraction_prompt_includes_chapter_text():
    prompt = build_extraction_prompt(
        chapter_text="林渊踏入幽冥谷，薄雾缠绕脚踝。",
        character_bible=[{"name": "林渊", "description": "黑发青年"}],
    )
    assert "林渊踏入幽冥谷" in prompt
    assert "林渊" in prompt
    assert "黑发青年" in prompt
    assert "JSON" in prompt or "json" in prompt


def test_parse_extraction_response_valid_json():
    raw = json.dumps({
        "subject": "林渊",
        "scene": "幽冥谷",
        "mood": "紧张",
        "characters_in_scene": [{"name": "林渊", "role": "主角", "key_visual": "黑发"}],
        "extraction_confidence": 0.85,
    }, ensure_ascii=False)
    parsed = parse_extraction_response(raw)
    assert parsed["subject"] == "林渊"
    assert parsed["extraction_confidence"] == 0.85


def test_parse_extraction_response_with_markdown_fence():
    raw = '```json\n{"subject": "x", "scene": "y", "mood": "z", "characters_in_scene": [], "extraction_confidence": 0.9}\n```'
    parsed = parse_extraction_response(raw)
    assert parsed["subject"] == "x"


def test_parse_extraction_response_missing_field_raises():
    raw = json.dumps({"subject": "x"})  # missing fields
    with pytest.raises(ExtractError) as exc:
        parse_extraction_response(raw)
    assert "scene" in str(exc.value).lower() or "missing" in str(exc.value).lower()


def test_parse_extraction_response_invalid_json_raises():
    with pytest.raises(ExtractError):
        parse_extraction_response("not valid json")


def test_extract_scene_calls_llm_service(monkeypatch):
    """Integration: extract_scene orchestrates LLM call + parse."""
    mock_service = MagicMock()
    mock_task = MagicMock()
    mock_task.execute.return_value = json.dumps({
        "subject": "林渊", "scene": "谷", "mood": "紧张",
        "characters_in_scene": [], "extraction_confidence": 0.8,
    }, ensure_ascii=False)
    mock_service.create_task.return_value = mock_task

    monkeypatch.setattr("lingwen_illustrations.prompt_builder.get_llm_service",
                        lambda: mock_service)

    result = extract_scene(
        chapter_text="测试章节文本",
        character_bible=[],
    )
    assert result["subject"] == "林渊"
    mock_service.create_task.assert_called_once()


def test_extract_scene_llm_failure_raises_extract_error(monkeypatch):
    mock_service = MagicMock()
    mock_task = MagicMock()
    mock_task.execute.side_effect = RuntimeError("LLM timeout")
    mock_service.create_task.return_value = mock_task

    monkeypatch.setattr("lingwen_illustrations.prompt_builder.get_llm_service",
                        lambda: mock_service)

    with pytest.raises(ExtractError) as exc:
        extract_scene(chapter_text="x", character_bible=[])
    assert exc.value.retryable is True
```

- [ ] **Step 6.2: 跑测试确认 RED**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_prompt_builder.py -v
```

Expected: ImportError

- [ ] **Step 6.3: 写实现** `src/lingwen_illustrations/prompt_builder.py`

```python
"""Stage 1: LLM extraction of scene JSON from chapter text + character bible.

Calls lingwen-llm-service (I057). Returns structured JSON for Stage 2
template composition. Failures raise ExtractError (retryable).
"""

from __future__ import annotations

import json
import re
from typing import Any
from lingwen_illustrations.exceptions import ExtractError
from lingwen_llm_service import LLMTask, TaskType, get_llm_service


_REQUIRED_FIELDS = ("subject", "scene", "mood", "characters_in_scene", "extraction_confidence")


def build_extraction_prompt(
    *,
    chapter_text: str,
    character_bible: list[dict[str, Any]],
) -> str:
    """Construct the LLM prompt for scene extraction."""
    char_lines = "\n".join(
        f"- {c.get('name', '?')}: {c.get('description', '')}"
        for c in character_bible
    ) or "(无角色档案)"

    # Truncate chapter text to avoid token bloat (8K chars ~ 2K tokens zh)
    truncated = chapter_text[:8000] if len(chapter_text) > 8000 else chapter_text

    return f"""你是小说场景抽取专家。从以下章节文本中抽取视觉化信息用于生成插图。

# 章节文本
{truncated}

# 角色档案
{char_lines}

# 任务
输出严格 JSON（不要 markdown 包裹），字段：
- subject: 主视觉主体（人物/物体/场景，1-2 词）
- scene: 具体场景（时间/地点/动作，1-2 句）
- mood: 氛围词（紧张/宁静/壮阔等）
- characters_in_scene: 出现在场景中的角色列表，每项含 name/role/key_visual
- extraction_confidence: 0-1 浮点表示抽取置信度
"""


def parse_extraction_response(raw: str) -> dict[str, Any]:
    """Parse LLM response to structured dict. Handles markdown fence.

    Raises:
        ExtractError: If JSON invalid or required fields missing.
    """
    # Strip markdown code fence if present
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ExtractError(f"LLM returned invalid JSON: {e}") from e

    if not isinstance(data, dict):
        raise ExtractError(f"LLM returned non-dict: {type(data).__name__}")

    missing = [f for f in _REQUIRED_FIELDS if f not in data]
    if missing:
        raise ExtractError(f"LLM JSON missing fields: {missing}")

    if not isinstance(data["extraction_confidence"], (int, float)):
        raise ExtractError("extraction_confidence must be a number")

    return data


def extract_scene(
    *,
    chapter_text: str,
    character_bible: list[dict[str, Any]],
) -> dict[str, Any]:
    """Orchestrate LLM call + response parse.

    Returns:
        Parsed scene JSON dict.

    Raises:
        ExtractError: If LLM call fails or response unparseable.
    """
    prompt = build_extraction_prompt(
        chapter_text=chapter_text,
        character_bible=character_bible,
    )

    try:
        service = get_llm_service()
        task = service.create_task(
            prompt=prompt,
            task_type=TaskType.STRUCTURED_EXTRACTION,
        )
        response_raw = task.execute()
    except Exception as e:
        raise ExtractError(f"LLM call failed: {e}") from e

    return parse_extraction_response(response_raw)


__all__ = ["build_extraction_prompt", "parse_extraction_response", "extract_scene"]
```

- [ ] **Step 6.4: 跑测试确认 GREEN**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_prompt_builder.py -v
```

Expected: 7 passed

- [ ] **Step 6.5: ruff + 提交**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m ruff check packages/lingwen-illustrations/
git add packages/lingwen-illustrations/
git commit -m "feat(phase-90): prompt_builder (Stage 1 LLM extraction + parse)"
```

---

## Task 7: image_generator.py — Stage 3 MiniMax API

**Files:**
- Create: `packages/lingwen-illustrations/src/lingwen_illustrations/image_generator.py`
- Create: `packages/lingwen-illustrations/tests/test_image_generator.py`

- [ ] **Step 7.1: 写失败测试** `tests/test_image_generator.py`

```python
"""Test Stage 3 MiniMax multimodal API call."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from lingwen_illustrations.image_generator import generate
from lingwen_illustrations.exceptions import GenerateError


@pytest.mark.asyncio
async def test_generate_returns_jpeg_bytes(monkeypatch):
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.content = b"\xff\xd8\xff\xe0fake-jpeg"
    fake_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = fake_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("lingwen_illustrations.image_generator.httpx.AsyncClient", return_value=mock_client):
        result = await generate(prompt="测试 prompt", api_key="test-key", api_host="https://api.test")

    assert result == b"\xff\xd8\xff\xe0fake-jpeg"
    mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_generate_rate_limit_raises_with_retry_after(monkeypatch):
    fake_response = MagicMock()
    fake_response.status_code = 429
    fake_response.headers = {"retry-after": "30"}
    fake_response.raise_for_status.side_effect = Exception("429 Too Many Requests")

    mock_client = AsyncMock()
    mock_client.post.return_value = fake_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("lingwen_illustrations.image_generator.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is True
    assert exc.value.retry_after == 30


@pytest.mark.asyncio
async def test_generate_network_error_raises(monkeypatch):
    mock_client = AsyncMock()
    mock_client.post.side_effect = ConnectionError("network down")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("lingwen_illustrations.image_generator.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is True


@pytest.mark.asyncio
async def test_generate_timeout_raises(monkeypatch):
    import httpx
    mock_client = AsyncMock()
    mock_client.post.side_effect = httpx.TimeoutException("timeout")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("lingwen_illustrations.image_generator.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(GenerateError) as exc:
            await generate(prompt="x", api_key="k", api_host="https://api.test")
    assert exc.value.retryable is True
```

- [ ] **Step 7.2: 跑测试确认 RED**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_image_generator.py -v
```

Expected: ImportError

- [ ] **Step 7.3: 写实现** `src/lingwen_illustrations/image_generator.py`

```python
"""Stage 3: MiniMax multimodal API call for image generation.

Calls https://api.MiniMax.chat/v1/image_generation (per minimax-multimodal-toolkit).
Returns raw image bytes (JPEG). Failures raise GenerateError (retryable)
with optional retry_after from rate-limit headers.
"""

from __future__ import annotations

import httpx
from lingwen_illustrations.exceptions import GenerateError


async def generate(
    *,
    prompt: str,
    api_key: str,
    api_host: str,
    timeout: float = 60.0,
) -> bytes:
    """Call MiniMax image generation API. Returns JPEG bytes.

    Args:
        prompt: Final composed image prompt (Stage 2 output).
        api_key: MiniMax API key (from config).
        api_host: Base URL (e.g. https://api.MiniMax.chat).
        timeout: HTTP timeout in seconds.

    Returns:
        Raw JPEG image bytes.

    Raises:
        GenerateError: On HTTP / network / timeout / rate-limit failures.
    """
    url = f"{api_host.rstrip('/')}/v1/image_generation"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "minimax-multimodal",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "response_format": "url",  # MiniMax returns URL; we re-fetch below
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
    except httpx.TimeoutException as e:
        raise GenerateError(f"image API timeout: {e}", retry_after=60) from e
    except httpx.HTTPError as e:
        raise GenerateError(f"image API network error: {e}") from e

    if resp.status_code == 429:
        retry_after = int(resp.headers.get("retry-after", "30"))
        raise GenerateError("rate limited", retry_after=retry_after)

    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise GenerateError(f"image API HTTP {resp.status_code}: {e}") from e

    # MiniMax returns JSON with image URL; fetch the actual bytes
    try:
        data = resp.json()
        image_url = data["data"][0]["url"]
    except (ValueError, KeyError, IndexError) as e:
        raise GenerateError(f"image API unexpected response: {e}") from e

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            img_resp = await client.get(image_url)
            img_resp.raise_for_status()
            return img_resp.content
    except httpx.HTTPError as e:
        raise GenerateError(f"image fetch error: {e}") from e


__all__ = ["generate"]
```

- [ ] **Step 7.4: 跑测试确认 GREEN**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_image_generator.py -v
```

Expected: 4 passed

- [ ] **Step 7.5: 提交**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m ruff check packages/lingwen-illustrations/
git add packages/lingwen-illustrations/
git commit -m "feat(phase-90): image_generator (Stage 3 MiniMax API + error mapping)"
```

---

## Task 8: pipeline.py — 编排器 (Stage 1→2→3→4)

**Files:**
- Create: `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py`
- Create: `packages/lingwen-illustrations/tests/test_pipeline.py`

- [ ] **Step 8.1: 写失败测试** `tests/test_pipeline.py`

```python
"""Integration test: full pipeline orchestrator (Stage 1→2→3→4)."""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from lingwen_illustrations.pipeline import generate_illustration
from lingwen_illustrations.metadata import IllustrationMetadata
from lingwen_illustrations.exceptions import ExtractError, GenerateError, StoreError


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    (tmp_path / "config").mkdir()
    return tmp_path


@pytest.fixture
def sample_chapter(project_root: Path) -> None:
    chapter_dir = project_root / "chapters"
    chapter_dir.mkdir()
    (chapter_dir / "017.md").write_text(
        "# 第 17 章\n\n林渊踏入幽冥谷，薄雾缠绕脚踝。", encoding="utf-8"
    )


@pytest.fixture
def sample_characters(project_root: Path) -> None:
    (project_root / "config").mkdir(exist_ok=True)
    (project_root / "config" / "characters.json").write_text(
        json.dumps([{"name": "林渊", "description": "黑发青年"}], ensure_ascii=False),
        encoding="utf-8",
    )


@pytest.mark.asyncio
async def test_pipeline_happy_path(project_root, sample_chapter, sample_characters):
    """Full pipeline: load → extract → compose → generate → store."""

    # Mock LLM
    mock_service = MagicMock()
    mock_task = MagicMock()
    mock_task.execute.return_value = json.dumps({
        "subject": "林渊", "scene": "幽冥谷", "mood": "紧张",
        "characters_in_scene": [{"name": "林渊", "role": "主角", "key_visual": "黑发"}],
        "extraction_confidence": 0.9,
    }, ensure_ascii=False)
    mock_service.create_task.return_value = mock_task

    # Mock image API
    fake_jpeg = b"\xff\xd8\xff\xe0fake"

    with patch("lingwen_illustrations.pipeline.get_llm_service", return_value=mock_service), \
         patch("lingwen_illustrations.pipeline.image_generator.generate",
               new=AsyncMock(return_value=fake_jpeg)) as mock_gen:
        meta = await generate_illustration(
            project_root=project_root,
            project_slug="test",
            type="chapter",
            chapter_num=17,
            style_preset="ink",
            custom_prompt=None,
            api_key="test-key",
            api_host="https://api.test",
        )

    assert isinstance(meta, IllustrationMetadata)
    assert meta.type == "chapter"
    assert meta.chapter_num == 17
    assert meta.style_preset == "ink"
    assert meta.scene_json["subject"] == "林渊"

    # Verify file written
    img_path = project_root / "assets" / "illustrations" / "chapter-017" / f"{meta.id}.jpg"
    assert img_path.exists()
    assert img_path.read_bytes() == fake_jpeg
    sidecar = img_path.with_suffix(img_path.suffix + ".meta.json")
    assert sidecar.exists()
    mock_gen.assert_called_once()


@pytest.mark.asyncio
async def test_pipeline_extract_failure_raises(project_root, sample_chapter, sample_characters):
    mock_service = MagicMock()
    mock_task = MagicMock()
    mock_task.execute.side_effect = RuntimeError("LLM down")
    mock_service.create_task.return_value = mock_task

    with patch("lingwen_illustrations.pipeline.get_llm_service", return_value=mock_service):
        with pytest.raises(ExtractError):
            await generate_illustration(
                project_root=project_root,
                project_slug="test",
                type="chapter",
                chapter_num=17,
                style_preset="ink",
                custom_prompt=None,
                api_key="k",
                api_host="https://api.test",
            )


@pytest.mark.asyncio
async def test_pipeline_generate_failure_raises(project_root, sample_chapter, sample_characters):
    mock_service = MagicMock()
    mock_task = MagicMock()
    mock_task.execute.return_value = json.dumps({
        "subject": "x", "scene": "y", "mood": "z",
        "characters_in_scene": [], "extraction_confidence": 0.8,
    }, ensure_ascii=False)
    mock_service.create_task.return_value = mock_task

    with patch("lingwen_illustrations.pipeline.get_llm_service", return_value=mock_service), \
         patch("lingwen_illustrations.pipeline.image_generator.generate",
               new=AsyncMock(side_effect=GenerateError("api down", retry_after=30))):
        with pytest.raises(GenerateError) as exc:
            await generate_illustration(
                project_root=project_root,
                project_slug="test",
                type="chapter",
                chapter_num=17,
                style_preset="ink",
                custom_prompt=None,
                api_key="k",
                api_host="https://api.test",
            )
    assert exc.value.retry_after == 30


@pytest.mark.asyncio
async def test_pipeline_store_failure_raises(project_root, sample_chapter, sample_characters):
    mock_service = MagicMock()
    mock_task = MagicMock()
    mock_task.execute.return_value = json.dumps({
        "subject": "x", "scene": "y", "mood": "z",
        "characters_in_scene": [], "extraction_confidence": 0.8,
    }, ensure_ascii=False)
    mock_service.create_task.return_value = mock_task

    with patch("lingwen_illustrations.pipeline.get_llm_service", return_value=mock_service), \
         patch("lingwen_illustrations.pipeline.image_generator.generate",
               new=AsyncMock(return_value=b"data")), \
         patch("lingwen_illustrations.pipeline.storage.save_asset",
               side_effect=StoreError("disk full")):
        with pytest.raises(StoreError):
            await generate_illustration(
                project_root=project_root,
                project_slug="test",
                type="chapter",
                chapter_num=17,
                style_preset="ink",
                custom_prompt=None,
                api_key="k",
                api_host="https://api.test",
            )
```

- [ ] **Step 8.2: 跑测试确认 RED**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_pipeline.py -v
```

Expected: ImportError

- [ ] **Step 8.3: 写实现** `src/lingwen_illustrations/pipeline.py`

```python
"""Pipeline orchestrator: load → extract → compose → generate → store.

Single entry point for the 4-stage illustration generation pipeline.
Each stage raises a stage-specific exception on failure; the orchestrator
propagates without wrapping.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from lingwen_illustrations import image_generator, storage
from lingwen_illustrations.metadata import IllustrationMetadata
from lingwen_illustrations.prompt_builder import extract_scene
from lingwen_illustrations.style_templates import compose as compose_prompt
from lingwen_illustrations.exceptions import LoadError
from lingwen_project_characters import load_agency_target_characters
from lingwen_paths import ProjectPaths, resolve_project_root


async def generate_illustration(
    *,
    project_root: Path,
    project_slug: str,
    type: Literal["cover", "chapter"],
    chapter_num: int | None,
    style_preset: str,
    custom_prompt: str | None,
    api_key: str,
    api_host: str,
) -> IllustrationMetadata:
    """Run the full pipeline. Returns metadata of saved asset.

    Raises:
        LoadError: Project / chapter / character bible missing.
        ExtractError: Stage 1 LLM failed.
        ComposeError: Stage 2 template failed (invalid preset).
        GenerateError: Stage 3 image API failed.
        StoreError: Stage 4 file write failed.
    """
    # Stage 1a: load chapter text
    chapter_text = ""
    if type == "chapter":
        if chapter_num is None:
            raise LoadError("chapter_num required for chapter type")
        chapter_file = project_root / "chapters" / f"{chapter_num:03d}.md"
        if not chapter_file.exists():
            raise LoadError(f"chapter {chapter_num} not found at {chapter_file}")
        chapter_text = chapter_file.read_text(encoding="utf-8")

    # Stage 1b: load character bible
    try:
        paths = ProjectPaths(project_root=project_root)
        character_bible = load_agency_target_characters(paths=paths)
    except Exception as e:
        raise LoadError(f"failed to load character bible: {e}") from e

    # Stage 2: LLM extract
    scene_json = extract_scene(
        chapter_text=chapter_text,
        character_bible=character_bible,
    )

    # Stage 3: compose prompt
    final_prompt = compose_prompt(
        style_preset,
        scene_json=scene_json,
        custom_prompt=custom_prompt,
    )

    # Stage 4: image generation
    image_bytes = await image_generator.generate(
        prompt=final_prompt,
        api_key=api_key,
        api_host=api_host,
    )

    # Stage 5: store
    asset_id = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
    prompt_hash = f"sha256:{hashlib.sha256(final_prompt.encode()).hexdigest()[:16]}"

    meta = IllustrationMetadata(
        id=asset_id,
        type=type,
        project_slug=project_slug,
        chapter_num=chapter_num,
        style_preset=style_preset,
        custom_prompt=custom_prompt,
        scene_json=scene_json,
        final_prompt=final_prompt,
        prompt_hash=prompt_hash,
        model="minimax-multimodal",
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    storage.save_asset(project_root, image_bytes, meta)
    return meta


__all__ = ["generate_illustration"]
```

- [ ] **Step 8.4: 跑测试确认 GREEN**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m pytest packages/lingwen-illustrations/tests/test_pipeline.py -v
```

Expected: 4 passed

- [ ] **Step 8.5: ruff + 提交**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m ruff check packages/lingwen-illustrations/
git add packages/lingwen-illustrations/
git commit -m "feat(phase-90): pipeline orchestrator (Stage 1→2→3→4)"
```

---

## Task 9: FastAPI router (4 路由)

**Files:**
- Create: `apps/studio_api/routes/illustrations.py`
- Create: `apps/studio_api/tests/test_illustrations_api.py`
- Modify: `apps/studio_api/app.py` (注册 router)

- [ ] **Step 9.1: 写失败测试** `apps/studio_api/tests/test_illustrations_api.py`

```python
"""Test illustrations API: POST generate / GET list / DELETE / GET image."""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def client_with_project(tmp_path: Path, monkeypatch):
    # Setup project structure
    (tmp_path / "chapters").mkdir()
    (tmp_path / "chapters" / "017.md").write_text("# 17\n林渊踏入幽冥谷", encoding="utf-8")
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "characters.json").write_text(
        json.dumps([{"name": "林渊", "description": "黑发"}], ensure_ascii=False)
    )

    from apps.studio_api.app import create_app
    app = create_app()
    return TestClient(app), tmp_path


def test_post_generate_success(client_with_project):
    client, project_root = client_with_project

    # Mock LLM
    mock_service = MagicMock()
    mock_task = MagicMock()
    mock_task.execute.return_value = json.dumps({
        "subject": "林渊", "scene": "幽冥谷", "mood": "紧张",
        "characters_in_scene": [], "extraction_confidence": 0.9,
    }, ensure_ascii=False)
    mock_service.create_task.return_value = mock_task

    with patch("lingwen_illustrations.pipeline.get_llm_service", return_value=mock_service), \
         patch("lingwen_illustrations.pipeline.image_generator.generate",
               new=AsyncMock(return_value=b"\xff\xd8\xff\xe0fake-jpeg")):
        resp = client.post("/api/illustrations/generate", json={
            "project_slug": "test",
            "type": "chapter",
            "chapter_num": 17,
            "style_preset": "ink",
            "custom_prompt": None,
        })

    assert resp.status_code == 200
    body = resp.json()
    assert "id" in body
    assert body["type"] == "chapter"
    assert body["chapter_num"] == 17


def test_post_generate_load_error_returns_404(client_with_project):
    client, _ = client_with_project
    resp = client.post("/api/illustrations/generate", json={
        "project_slug": "test", "type": "chapter", "chapter_num": 999,
        "style_preset": "ink", "custom_prompt": None,
    })
    assert resp.status_code == 404
    assert resp.json()["stage"] == "load"


def test_post_generate_compose_error_returns_400(client_with_project):
    client, project_root = client_with_project
    mock_service = MagicMock()
    mock_task = MagicMock()
    mock_task.execute.return_value = json.dumps({
        "subject": "x", "scene": "y", "mood": "z",
        "characters_in_scene": [], "extraction_confidence": 0.8,
    }, ensure_ascii=False)
    mock_service.create_task.return_value = mock_task

    with patch("lingwen_illustrations.pipeline.get_llm_service", return_value=mock_service):
        resp = client.post("/api/illustrations/generate", json={
            "project_slug": "test", "type": "chapter", "chapter_num": 17,
            "style_preset": "BOGUS", "custom_prompt": None,
        })
    assert resp.status_code == 400
    assert resp.json()["stage"] == "compose"


def test_post_generate_validation_error_returns_422(client_with_project):
    client, _ = client_with_project
    resp = client.post("/api/illustrations/generate", json={
        "project_slug": "test", "type": "chapter",  # missing chapter_num
        "style_preset": "ink",
    })
    assert resp.status_code == 422


def test_get_list_assets(client_with_project):
    client, _ = client_with_project
    resp = client.get("/api/illustrations/list?project_slug=test")
    assert resp.status_code == 200
    body = resp.json()
    assert "assets" in body
    assert isinstance(body["assets"], list)


def test_delete_asset(client_with_project, tmp_path):
    client, project_root = client_with_project
    # First create an asset directly
    from lingwen_illustrations.storage import save_asset
    from lingwen_illustrations.metadata import IllustrationMetadata
    meta = IllustrationMetadata(
        id="del-id", type="chapter", project_slug="test", chapter_num=17,
        style_preset="ink", custom_prompt=None, scene_json={},
        final_prompt="x", prompt_hash="sha256:x", model="m",
        created_at="2026-09-15T00:00:00Z",
    )
    save_asset(project_root, b"data", meta)

    resp = client.delete("/api/illustrations/del-id?project_slug=test")
    assert resp.status_code == 200
```

- [ ] **Step 9.2: 跑测试确认 RED**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m pytest apps/studio_api/tests/test_illustrations_api.py -v
```

Expected: 404 on routes (not registered yet)

- [ ] **Step 9.3: 写实现** `apps/studio_api/routes/illustrations.py`

```python
"""Phase 90 REQ-002: illustrations API routes."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import Body, FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field

from apps.studio_api.routes.ctx import RoutesContext
from lingwen_illustrations import storage
from lingwen_illustrations.exceptions import (
    LoadError, ExtractError, ComposeError, GenerateError, StoreError,
    IllustrationError,
)
from lingwen_illustrations.metadata import IllustrationMetadata


# --- Pydantic schemas ---

class GenerateRequest(BaseModel):
    project_slug: str
    type: str = Field(pattern="^(cover|chapter)$")
    chapter_num: Optional[int] = None
    style_preset: str = Field(pattern="^(ink|realistic|anime)$")
    custom_prompt: Optional[str] = None


class GenerateResponse(BaseModel):
    id: str
    type: str
    chapter_num: Optional[int]
    style_preset: str
    scene_json: dict
    url: str


class ListResponse(BaseModel):
    assets: list[dict]


# --- Helpers ---

def _project_root_for(slug: str) -> Path:
    """Resolve project root from slug. v1: lookup in projects/."""
    from lingwen_paths import resolve_project_root
    # resolve_project_root expects a path; for slug-based lookup, scan projects/
    projects_dir = Path("projects")
    candidate = projects_dir / slug
    if not candidate.exists():
        raise LoadError(f"project '{slug}' not found at {candidate}")
    return resolve_project_root(candidate)


def _api_credentials() -> tuple[str, str]:
    """Get MiniMax API key + host from config."""
    from lingwen_config import get_api_config
    cfg = get_api_config()
    return cfg.minimax_api_key, cfg.minimax_api_host


# --- Router registration ---

def register_illustrations(app: FastAPI, ctx: RoutesContext) -> None:
    """Mount /api/illustrations/* routes."""

    @app.post("/api/illustrations/generate", response_model=GenerateResponse)
    async def generate_illustration(req: GenerateRequest = Body(...)):
        try:
            project_root = _project_root_for(req.project_slug)
            api_key, api_host = _api_credentials()
        except LoadError as e:
            raise HTTPException(404, detail={"stage": e.stage.value, "error": e.message, "retryable": e.retryable})

        # Lazy import to avoid circular
        from lingwen_illustrations.pipeline import generate_illustration as run_pipeline

        try:
            meta = await run_pipeline(
                project_root=project_root,
                project_slug=req.project_slug,
                type=req.type,  # type: ignore[arg-type]
                chapter_num=req.chapter_num,
                style_preset=req.style_preset,
                custom_prompt=req.custom_prompt,
                api_key=api_key,
                api_host=api_host,
            )
        except LoadError as e:
            raise HTTPException(404, detail={"stage": e.stage.value, "error": e.message, "retryable": e.retryable})
        except ExtractError as e:
            raise HTTPException(502, detail={"stage": e.stage.value, "error": e.message, "retryable": e.retryable})
        except ComposeError as e:
            raise HTTPException(400, detail={"stage": e.stage.value, "error": e.message, "retryable": e.retryable})
        except GenerateError as e:
            raise HTTPException(502, detail={"stage": e.stage.value, "error": e.message, "retryable": e.retryable, "retry_after": e.retry_after})
        except StoreError as e:
            raise HTTPException(500, detail={"stage": e.stage.value, "error": e.message, "retryable": e.retryable})

        return GenerateResponse(
            id=meta.id,
            type=meta.type,
            chapter_num=meta.chapter_num,
            style_preset=meta.style_preset,
            scene_json=meta.scene_json,
            url=f"/api/illustrations/{meta.id}/image?project_slug={req.project_slug}",
        )

    @app.get("/api/illustrations/list", response_model=ListResponse)
    def list_assets(project_slug: str = Query(...), type: Optional[str] = Query(None)):
        try:
            project_root = _project_root_for(project_slug)
        except LoadError as e:
            raise HTTPException(404, detail={"stage": e.stage.value, "error": e.message, "retryable": e.retryable})

        assets = storage.list_assets(project_root)
        if type:
            assets = [a for a in assets if a.type == type]

        return ListResponse(assets=[a.to_dict() for a in assets])

    @app.delete("/api/illustrations/{asset_id}")
    def delete_asset(asset_id: str, project_slug: str = Query(...)):
        try:
            project_root = _project_root_for(project_slug)
        except LoadError as e:
            raise HTTPException(404, detail={"stage": e.stage.value, "error": e.message, "retryable": e.retryable})

        # Find the asset by id
        all_assets = storage.list_assets(project_root)
        meta = next((a for a in all_assets if a.id == asset_id), None)
        if not meta:
            raise HTTPException(404, detail=f"asset {asset_id} not found")

        storage.delete_asset(project_root, meta)
        return {"deleted": asset_id}

    @app.get("/api/illustrations/{asset_id}/image")
    def get_image(asset_id: str, project_slug: str = Query(...)):
        from fastapi.responses import FileResponse

        try:
            project_root = _project_root_for(project_slug)
        except LoadError as e:
            raise HTTPException(404, detail={"stage": e.stage.value, "error": e.message, "retryable": e.retryable})

        all_assets = storage.list_assets(project_root)
        meta = next((a for a in all_assets if a.id == asset_id), None)
        if not meta:
            raise HTTPException(404, detail=f"asset {asset_id} not found")

        img_path = storage.asset_path(
            project_root,
            type=meta.type,  # type: ignore[arg-type]
            id=meta.id,
            chapter_num=meta.chapter_num,
        )
        if not img_path.exists():
            raise HTTPException(404, detail=f"image file missing for {asset_id}")

        return FileResponse(img_path, media_type="image/jpeg")
```

- [ ] **Step 9.4: 注册 router** — 修改 `apps/studio_api/app.py`

找到 `create_app()` 函数，在其他 `register_*` 调用后加：

```python
from apps.studio_api.routes.illustrations import register_illustrations
register_illustrations(app, ctx)
```

- [ ] **Step 9.5: 跑测试确认 GREEN**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m pytest apps/studio_api/tests/test_illustrations_api.py -v
```

Expected: 6 passed (some may skip if MiniMax config unavailable; ensure LLM mock covers all)

- [ ] **Step 9.6: ruff + 提交**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m ruff check apps/studio_api/routes/illustrations.py apps/studio_api/tests/test_illustrations_api.py
git add apps/studio_api/
git commit -m "feat(phase-90): FastAPI router 4 endpoints (generate/list/delete/image)"
```

---

## Task 10: Auto-generate background task hook

**Files:**
- Modify: `apps/studio_api/background.py` (新增 illustrations_auto_generate_task)
- OR: 在 chapter_marked_complete 调用点直接调 generate_illustration

- [ ] **Step 10.1: 在 `apps/studio_api/background.py` 添加 task 注册**

（参考 P2-RESTART Phase 模式）追加：

```python
async def illustrations_auto_generate_task(
    project_slug: str,
    chapter_num: int,
    settings: dict,
) -> None:
    """Fire-and-forget illustration generation after chapter complete.

    Triggered by chapter_marked_complete event when user has auto-generate
    enabled in project settings. Failures logged but never raised.
    """
    from lingwen_illustrations.pipeline import generate_illustration
    from apps.studio_api.routes.illustrations import _project_root_for, _api_credentials
    from lingwen_illustrations.exceptions import IllustrationError
    import logging
    log = logging.getLogger(__name__)

    try:
        project_root = _project_root_for(project_slug)
        api_key, api_host = _api_credentials()
        await generate_illustration(
            project_root=project_root,
            project_slug=project_slug,
            type="chapter",
            chapter_num=chapter_num,
            style_preset=settings.get("style_preset", "ink"),
            custom_prompt=None,
            api_key=api_key,
            api_host=api_host,
        )
        log.info(f"auto-generated illustration for {project_slug} ch.{chapter_num}")
    except IllustrationError as e:
        log.warning(f"auto-generate failed [{e.stage.value}]: {e.message}")
    except Exception as e:
        log.error(f"auto-generate unexpected error: {e}")
```

- [ ] **Step 10.2: 在 `lingwen-persistence.write_chapter` 调用点（status=completed）触发**

找到 `apps/studio_api/routes/...` 中标记章节完成的端点（参考 write_workspace_api.py），追加：

```python
# After successful write_chapter with status="completed"
from apps.studio_api.background import illustrations_auto_generate_task
import asyncio

# Get project settings (check if auto-generate enabled)
settings = _get_illustration_settings(project_slug)
if settings.get("auto_generate", False):
    asyncio.create_task(
        illustrations_auto_generate_task(project_slug, chapter_num, settings)
    )
```

- [ ] **Step 10.3: 提交**

```bash
git add apps/studio_api/
git commit -m "feat(phase-90): auto-generate background task on chapter complete"
```

---

## Task 11: Frontend composable + store

**Files:**
- Create: `apps/dashboard/src/composables/useIllustration.js`
- Create: `apps/dashboard/src/stores/useIllustrationStore.js`
- Create: `apps/dashboard/tests/composables/useIllustration.test.js`

- [ ] **Step 11.1: 写失败测试** `apps/dashboard/tests/composables/useIllustration.test.js`

```javascript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useIllustrationStore } from '@/stores/useIllustrationStore'

describe('useIllustrationStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('starts with empty assets list', () => {
    const store = useIllustrationStore()
    expect(store.assets).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBe(null)
  })

  it('loadAssets populates store on success', async () => {
    const store = useIllustrationStore()
    globalThis.$fetch = vi.fn().mockResolvedValue({
      assets: [{ id: 'a', type: 'chapter', chapter_num: 17, style_preset: 'ink' }],
    })

    await store.loadAssets('test-project')
    expect(store.assets).toHaveLength(1)
    expect(store.assets[0].id).toBe('a')
  })

  it('loadAssets sets error on failure', async () => {
    const store = useIllustrationStore()
    globalThis.$fetch = vi.fn().mockRejectedValue(new Error('network'))

    await store.loadAssets('test-project')
    expect(store.error).toBeTruthy()
    expect(store.loading).toBe(false)
  })
})
```

- [ ] **Step 11.2: 写 store** `apps/dashboard/src/stores/useIllustrationStore.js`

```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useIllustrationStore = defineStore('illustrations', () => {
  const assets = ref([])
  const loading = ref(false)
  const error = ref(null)

  const byType = computed(() => (type) => assets.value.filter(a => a.type === type))

  async function loadAssets(projectSlug, type = null) {
    loading.value = true
    error.value = null
    try {
      const query = type ? `&type=${type}` : ''
      const res = await $fetch(`/api/illustrations/list?project_slug=${projectSlug}${query}`)
      assets.value = res.assets
    } catch (e) {
      error.value = e.message || 'load failed'
    } finally {
      loading.value = false
    }
  }

  async function generate(projectSlug, params) {
    loading.value = true
    error.value = null
    try {
      const res = await $fetch('/api/illustrations/generate', {
        method: 'POST',
        body: { project_slug: projectSlug, ...params },
      })
      // Prepend to list
      assets.value = [res, ...assets.value]
      return res
    } catch (e) {
      error.value = e.data?.detail?.error || e.message || 'generate failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function regenerate(projectSlug, assetId) {
    // Find original metadata, call generate again with same params
    const original = assets.value.find(a => a.id === assetId)
    if (!original) throw new Error(`asset ${assetId} not found`)

    const params = {
      type: original.type,
      chapter_num: original.chapter_num,
      style_preset: original.style_preset,
      custom_prompt: original.custom_prompt,
    }
    // Delete old
    await $fetch(`/api/illustrations/${assetId}?project_slug=${projectSlug}`, { method: 'DELETE' })
    // Generate new
    return await generate(projectSlug, params)
  }

  async function deleteAsset(projectSlug, assetId) {
    await $fetch(`/api/illustrations/${assetId}?project_slug=${projectSlug}`, { method: 'DELETE' })
    assets.value = assets.value.filter(a => a.id !== assetId)
  }

  return { assets, loading, error, byType, loadAssets, generate, regenerate, deleteAsset }
})
```

- [ ] **Step 11.3: 写 composable** `apps/dashboard/src/composables/useIllustration.js`

```javascript
import { computed } from 'vue'
import { useIllustrationStore } from '@/stores/useIllustrationStore'
import { storeToRefs } from 'pinia'

export function useIllustration(projectSlug) {
  const store = useIllustrationStore()
  const { assets, loading, error } = storeToRefs(store)

  const chapterAssets = computed(() => assets.value.filter(a => a.type === 'chapter'))
  const coverAssets = computed(() => assets.value.filter(a => a.type === 'cover'))

  function getForChapter(chapterNum) {
    return chapterAssets.value.find(a => a.chapter_num === chapterNum)
  }

  return {
    assets,
    chapterAssets,
    coverAssets,
    loading,
    error,
    getForChapter,
    loadAssets: () => store.loadAssets(projectSlug),
    generate: (params) => store.generate(projectSlug, params),
    regenerate: (assetId) => store.regenerate(projectSlug, assetId),
    deleteAsset: (assetId) => store.deleteAsset(projectSlug, assetId),
  }
}
```

- [ ] **Step 11.4: 跑测试确认 GREEN**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run tests/composables/useIllustration.test.js
```

Expected: 3 passed

- [ ] **Step 11.5: 提交**

```bash
git add apps/dashboard/src/composables/ apps/dashboard/src/stores/ apps/dashboard/tests/
git commit -m "feat(phase-90): useIllustration composable + Pinia store"
```

---

## Task 12: IllustrationCard 组件

**Files:**
- Create: `apps/dashboard/src/components/illustrations/IllustrationCard.vue`
- Create: `apps/dashboard/tests/components/illustrations/IllustrationCard.spec.js`

- [ ] **Step 12.1: 写失败测试** `IllustrationCard.spec.js`

```javascript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import IllustrationCard from '@/components/illustrations/IllustrationCard.vue'

describe('IllustrationCard', () => {
  const asset = {
    id: 'abc',
    type: 'chapter',
    chapter_num: 17,
    style_preset: 'ink',
    url: '/api/illustrations/abc/image?project_slug=test',
  }

  it('renders asset thumbnail', () => {
    const wrapper = mount(IllustrationCard, { props: { asset, projectSlug: 'test' } })
    const img = wrapper.find('img[data-testid="illustration-thumb"]')
    expect(img.exists()).toBe(true)
    expect(img.attributes('src')).toContain('abc')
  })

  it('shows chapter number badge', () => {
    const wrapper = mount(IllustrationCard, { props: { asset, projectSlug: 'test' } })
    expect(wrapper.text()).toContain('第 17 章')
  })

  it('emits regenerate event on button click', async () => {
    const wrapper = mount(IllustrationCard, { props: { asset, projectSlug: 'test' } })
    await wrapper.find('[data-testid="regenerate-btn"]').trigger('click')
    expect(wrapper.emitted('regenerate')).toBeTruthy()
    expect(wrapper.emitted('regenerate')[0]).toEqual(['abc'])
  })

  it('emits delete event on button click', async () => {
    const wrapper = mount(IllustrationCard, { props: { asset, projectSlug: 'test' } })
    await wrapper.find('[data-testid="delete-btn"]').trigger('click')
    expect(wrapper.emitted('delete')).toBeTruthy()
    expect(wrapper.emitted('delete')[0]).toEqual(['abc'])
  })
})
```

- [ ] **Step 12.2: 写组件** `IllustrationCard.vue`

```vue
<script setup>
const props = defineProps({
  asset: { type: Object, required: true },
  projectSlug: { type: String, required: true },
})

const emit = defineEmits(['regenerate', 'delete'])

const label = props.asset.type === 'cover' ? '封面' : `第 ${props.asset.chapter_num} 章`
</script>

<template>
  <div class="illustration-card" data-testid="illustration-card">
    <img
      :src="asset.url"
      :alt="label"
      class="thumb"
      data-testid="illustration-thumb"
      loading="lazy"
    />
    <div class="meta">
      <span class="badge">{{ label }}</span>
      <span class="style">{{ asset.style_preset }}</span>
    </div>
    <div class="actions">
      <button data-testid="regenerate-btn" @click="emit('regenerate', asset.id)">↻ 重生</button>
      <button data-testid="delete-btn" @click="emit('delete', asset.id)">🗑 删除</button>
    </div>
  </div>
</template>

<style scoped>
.illustration-card {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--color-border, #2a2a3a);
  border-radius: 8px;
  overflow: hidden;
  background: var(--color-surface, #14141e);
}
.thumb {
  width: 100%;
  aspect-ratio: 3 / 4;
  object-fit: cover;
  display: block;
}
.meta {
  display: flex;
  justify-content: space-between;
  padding: 8px;
  font-size: 12px;
}
.actions {
  display: flex;
  gap: 4px;
  padding: 0 8px 8px;
}
.actions button {
  flex: 1;
  font-size: 12px;
  padding: 6px 8px;
  border: 1px solid var(--color-border, #2a2a3a);
  border-radius: 4px;
  background: transparent;
  color: var(--color-text, #d0d0e0);
  cursor: pointer;
}
.actions button:hover {
  background: var(--color-hover, #2a2a3a);
}
</style>
```

- [ ] **Step 12.3: 跑测试 + 提交**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run tests/components/illustrations/IllustrationCard.spec.js
git add apps/dashboard/src/components/illustrations/ apps/dashboard/tests/
git commit -m "feat(phase-90): IllustrationCard component"
```

---

## Task 13: IllustrationGallery 组件

**Files:**
- Create: `apps/dashboard/src/components/illustrations/IllustrationGallery.vue`
- Create: `apps/dashboard/tests/components/illustrations/IllustrationGallery.spec.js`

- [ ] **Step 13.1: 写失败测试** `IllustrationGallery.spec.js`

```javascript
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import IllustrationGallery from '@/components/illustrations/IllustrationGallery.vue'
import { useIllustrationStore } from '@/stores/useIllustrationStore'

describe('IllustrationGallery', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('renders 3-column grid of cards', async () => {
    const store = useIllustrationStore()
    store.assets = [
      { id: 'a', type: 'chapter', chapter_num: 1, style_preset: 'ink', url: '/x' },
      { id: 'b', type: 'chapter', chapter_num: 2, style_preset: 'ink', url: '/y' },
      { id: 'c', type: 'cover', chapter_num: null, style_preset: 'realistic', url: '/z' },
    ]

    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'test' } })
    const cards = wrapper.findAll('[data-testid="illustration-card"]')
    expect(cards).toHaveLength(3)
  })

  it('filters by type when filter prop set', async () => {
    const store = useIllustrationStore()
    store.assets = [
      { id: 'a', type: 'chapter', chapter_num: 1, url: '/x' },
      { id: 'c', type: 'cover', chapter_num: null, url: '/z' },
    ]

    const wrapper = mount(IllustrationGallery, {
      props: { projectSlug: 'test', typeFilter: 'chapter' },
    })
    const cards = wrapper.findAll('[data-testid="illustration-card"]')
    expect(cards).toHaveLength(1)
    expect(cards[0].text()).toContain('第 1 章')
  })

  it('shows empty state when no assets', () => {
    const wrapper = mount(IllustrationGallery, { props: { projectSlug: 'test' } })
    expect(wrapper.find('[data-testid="empty-state"]').exists()).toBe(true)
  })
})
```

- [ ] **Step 13.2: 写组件** `IllustrationGallery.vue`

```vue
<script setup>
import { computed, onMounted } from 'vue'
import { useIllustration } from '@/composables/useIllustration'
import IllustrationCard from './IllustrationCard.vue'

const props = defineProps({
  projectSlug: { type: String, required: true },
  typeFilter: { type: String, default: null },  // 'cover' | 'chapter' | null
})

const emit = defineEmits(['regenerate', 'delete'])

const { assets, loadAssets, regenerate, deleteAsset } = useIllustration(props.projectSlug)

onMounted(() => loadAssets())

const filtered = computed(() => {
  if (!props.typeFilter) return assets.value
  return assets.value.filter(a => a.type === props.typeFilter)
})

function onRegenerate(id) {
  emit('regenerate', id)
  return regenerate(id)
}

function onDelete(id) {
  emit('delete', id)
  return deleteAsset(id)
}
</script>

<template>
  <div class="illustration-gallery" data-testid="illustration-gallery">
    <div v-if="filtered.length === 0" class="empty" data-testid="empty-state">
      尚未生成任何插图
    </div>
    <div v-else class="grid">
      <IllustrationCard
        v-for="asset in filtered"
        :key="asset.id"
        :asset="asset"
        :project-slug="projectSlug"
        @regenerate="onRegenerate"
        @delete="onDelete"
      />
    </div>
  </div>
</template>

<style scoped>
.illustration-gallery {
  padding: 16px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.empty {
  text-align: center;
  padding: 48px 16px;
  color: var(--color-text-muted, #888);
}
</style>
```

- [ ] **Step 13.3: 跑测试 + 提交**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run tests/components/illustrations/IllustrationGallery.spec.js
git add apps/dashboard/src/components/illustrations/ apps/dashboard/tests/
git commit -m "feat(phase-90): IllustrationGallery component with type filter"
```

---

## Task 14: GenerateIllustrationDialog 组件

**Files:**
- Create: `apps/dashboard/src/components/illustrations/GenerateIllustrationDialog.vue`
- Create: `apps/dashboard/tests/components/illustrations/GenerateIllustrationDialog.spec.js`

- [ ] **Step 14.1: 写失败测试** `GenerateIllustrationDialog.spec.js`

```javascript
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import GenerateIllustrationDialog from '@/components/illustrations/GenerateIllustrationDialog.vue'

describe('GenerateIllustrationDialog', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('renders 3 style preset options', () => {
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 17, type: 'chapter', modelValue: true },
    })
    const presets = wrapper.findAll('[data-testid^="style-preset-"]')
    expect(presets.length).toBe(3)
  })

  it('selects preset on click', async () => {
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 17, type: 'chapter', modelValue: true },
    })
    await wrapper.find('[data-testid="style-preset-ink"]').trigger('click')
    expect(wrapper.vm.selectedPreset).toBe('ink')
  })

  it('emits generate event with params on submit', async () => {
    const wrapper = mount(GenerateIllustrationDialog, {
      props: { projectSlug: 'test', chapterNum: 17, type: 'chapter', modelValue: true },
    })
    wrapper.vm.selectedPreset = 'ink'
    wrapper.vm.customPrompt = '远景镜头'

    await wrapper.find('[data-testid="generate-submit"]').trigger('click')
    expect(wrapper.emitted('generate')).toBeTruthy()
    expect(wrapper.emitted('generate')[0][0]).toMatchObject({
      type: 'chapter',
      chapter_num: 17,
      style_preset: 'ink',
      custom_prompt: '远景镜头',
    })
  })
})
```

- [ ] **Step 14.2: 写组件** `GenerateIllustrationDialog.vue`

```vue
<script setup>
import { ref, computed } from 'vue'
import { NDialog, NButton, NInput } from 'naive-ui'

const props = defineProps({
  projectSlug: { type: String, required: true },
  chapterNum: { type: Number, default: null },
  type: { type: String, default: 'chapter' },
  modelValue: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'generate'])

const presets = [
  { id: 'ink', label: '古风水墨', icon: '🏯' },
  { id: 'realistic', label: '现代写实', icon: '📷' },
  { id: 'anime', label: '动漫厚涂', icon: '🎨' },
]

const selectedPreset = ref('ink')
const customPrompt = ref('')

const isValid = computed(() => selectedPreset.value !== null)

function close() {
  emit('update:modelValue', false)
}

function submit() {
  if (!isValid.value) return
  emit('generate', {
    type: props.type,
    chapter_num: props.chapterNum,
    style_preset: selectedPreset.value,
    custom_prompt: customPrompt.value || null,
  })
  close()
}
</script>

<template>
  <NDialog :show="modelValue" @update:show="emit('update:modelValue', $event)" preset="card" title="生成插图" style="max-width: 520px">
    <div class="form">
      <p class="label">风格预设</p>
      <div class="presets">
        <button
          v-for="p in presets"
          :key="p.id"
          :class="['preset', { selected: selectedPreset === p.id }]"
          :data-testid="`style-preset-${p.id}`"
          @click="selectedPreset = p.id"
          type="button"
        >
          <span class="icon">{{ p.icon }}</span>
          <span class="name">{{ p.label }}</span>
        </button>
      </div>

      <p class="label">补充描述（可选）</p>
      <NInput
        v-model:value="customPrompt"
        placeholder="e.g. 远景镜头、林渊侧脸、雾气弥漫"
        type="text"
      />

      <p class="label">使用上下文</p>
      <div class="context">
        ✓ 章节文本（{{ chapterNum ? `第 ${chapterNum} 章` : '封面' }}）<br>
        ✓ 角色档案（自动加载）<br>
        <span class="hint">→ 提取后显示预览</span>
      </div>
    </div>

    <template #action>
      <NButton @click="close">取消</NButton>
      <NButton
        type="primary"
        :disabled="!isValid"
        data-testid="generate-submit"
        @click="submit"
      >
        开始生成
      </NButton>
    </template>
  </NDialog>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.label {
  font-size: 12px;
  text-transform: uppercase;
  color: var(--color-text-muted, #888);
  margin: 0 0 8px 0;
}
.presets {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.preset {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px;
  border: 2px solid var(--color-border, #3a3a5a);
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  color: var(--color-text, #d0d0e0);
}
.preset.selected {
  border-color: var(--color-accent, #6a4aff);
  background: rgba(106, 74, 255, 0.15);
}
.preset .icon { font-size: 24px; }
.preset .name { font-size: 12px; }
.context {
  font-size: 12px;
  color: var(--color-text-muted, #888);
  line-height: 1.6;
}
.hint { color: var(--color-accent, #6a4aff); }
</style>
```

- [ ] **Step 14.3: 跑测试 + 提交**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run tests/components/illustrations/GenerateIllustrationDialog.spec.js
git add apps/dashboard/src/components/illustrations/ apps/dashboard/tests/
git commit -m "feat(phase-90): GenerateIllustrationDialog (preset + custom + submit)"
```

---

## Task 15: 修改 WriteWorkspacePage (生成按钮 + 侧栏)

**Files:**
- Modify: `apps/dashboard/src/pages/WriteWorkspacePage.vue` (新增工具栏按钮 + 侧栏)

- [ ] **Step 15.1: 找到 WriteWorkspacePage 的工具栏 section**（参考 Phase 115/54 实现）

- [ ] **Step 15.2: 添加 script import + state**

```vue
<script setup>
// ... existing imports
import { useIllustration } from '@/composables/useIllustration'
import GenerateIllustrationDialog from '@/components/illustrations/GenerateIllustrationDialog.vue'
import IllustrationCard from '@/components/illustrations/IllustrationCard.vue'

const props = defineProps({ projectSlug: String, chapterNum: Number })
const { chapterAssets, getForChapter, generate } = useIllustration(props.projectSlug)
const dialogOpen = ref(false)
const currentIllustration = computed(() => getForChapter(props.chapterNum))

async function onGenerate(params) {
  await generate(params)
}
</script>
```

- [ ] **Step 15.3: 工具栏加按钮** — 在 "保存草稿" 和 "标记完成" 之间加：

```vue
<button class="toolbar-btn generate-btn" @click="dialogOpen = true" data-testid="generate-illustration-btn">
  ✦ 生成插图
</button>
```

- [ ] **Step 15.4: 右侧栏加插图位** — 在右侧栏加：

```vue
<div class="illustration-sidebar" v-if="chapterNum" data-testid="illustration-sidebar">
  <p class="label">本章节插图</p>
  <IllustrationCard
    v-if="currentIllustration"
    :asset="currentIllustration"
    :project-slug="projectSlug"
    @regenerate="regenerate"
    @delete="deleteAsset"
  />
  <div v-else class="placeholder">尚未生成</div>
</div>

<GenerateIllustrationDialog
  v-model="dialogOpen"
  :project-slug="projectSlug"
  :chapter-num="chapterNum"
  type="chapter"
  @generate="onGenerate"
/>
```

- [ ] **Step 15.5: 跑 vitest + vue-tsc 检查**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run && pnpm tsc --noEmit
```

Expected: 无新错误

- [ ] **Step 15.6: 提交**

```bash
git add apps/dashboard/src/pages/WriteWorkspacePage.vue
git commit -m "feat(phase-90): WriteWorkspace generate button + illustration sidebar"
```

---

## Task 16: 修改 LibraryPage (资产 tab)

**Files:**
- Modify: `apps/dashboard/src/pages/LibraryPage.vue` (新增 "资产" tab)

- [ ] **Step 16.1: 添加资产 tab** — 在现有 tabs 数组追加：

```vue
<NTabPane name="assets" tab="资产">
  <IllustrationGallery :project-slug="projectSlug" />
</NTabPane>
```

- [ ] **Step 16.2: 提交**

```bash
git add apps/dashboard/src/pages/LibraryPage.vue
git commit -m "feat(phase-90): LibraryPage assets tab"
```

---

## Task 17: 修改 ProjectSettingsPage (插图偏好)

**Files:**
- Modify: `apps/dashboard/src/pages/ProjectSettingsPage.vue` (新增 "插图偏好" section)

- [ ] **Step 17.1: 写测试** `apps/dashboard/tests/components/illustrations/ProjectSettingsIllustration.spec.js`

```javascript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import ProjectSettingsIllustration from '@/components/illustrations/ProjectSettingsIllustration.vue'

describe('ProjectSettingsIllustration', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('renders 3 default style options', () => {
    const wrapper = mount(ProjectSettingsIllustration, { props: { modelValue: defaultSettings() } })
    const presets = wrapper.findAll('[data-testid^="default-style-"]')
    expect(presets).toHaveLength(3)
  })

  it('emits update with new auto_generate toggle', async () => {
    const wrapper = mount(ProjectSettingsIllustration, { props: { modelValue: defaultSettings() } })
    await wrapper.find('[data-testid="auto-generate-toggle"]').trigger('click')
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
  })
})

function defaultSettings() {
  return { style_preset: 'ink', auto_generate: false, max_assets: 200, confirm_before_generate: true }
}
```

- [ ] **Step 17.2: 写子组件** `ProjectSettingsIllustration.vue`

```vue
<script setup>
const props = defineProps({ modelValue: { type: Object, required: true } })
const emit = defineEmits(['update:modelValue'])

const presets = [
  { id: 'ink', label: '古风水墨' },
  { id: 'realistic', label: '现代写实' },
  { id: 'anime', label: '动漫厚涂' },
]

function update(key, value) {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}
</script>

<template>
  <section class="illustration-prefs" data-testid="illustration-prefs">
    <h3>插图偏好</h3>

    <div class="field">
      <p class="label">默认风格</p>
      <div class="presets">
        <button
          v-for="p in presets"
          :key="p.id"
          :class="['preset', { selected: modelValue.style_preset === p.id }]"
          :data-testid="`default-style-${p.id}`"
          @click="update('style_preset', p.id)"
        >
          {{ p.label }}
        </button>
      </div>
    </div>

    <div class="field">
      <label>
        <input
          type="checkbox"
          :checked="modelValue.auto_generate"
          data-testid="auto-generate-toggle"
          @change="update('auto_generate', $event.target.checked)"
        />
        章节完成时自动生成插图
      </label>
      <p class="hint">每章约消耗 1 次 LLM 调用 + 1 次图片生成</p>
    </div>

    <div class="field">
      <label>资产数量上限</label>
      <input
        type="number"
        :value="modelValue.max_assets"
        data-testid="max-assets-input"
        @input="update('max_assets', parseInt($event.target.value, 10))"
      />
    </div>

    <div class="field">
      <label>
        <input
          type="checkbox"
          :checked="modelValue.confirm_before_generate"
          @change="update('confirm_before_generate', $event.target.checked)"
        />
        生成前确认
      </label>
    </div>
  </section>
</template>

<style scoped>
.illustration-prefs { display: flex; flex-direction: column; gap: 16px; max-width: 520px; }
.field { display: flex; flex-direction: column; gap: 8px; }
.label { font-size: 12px; text-transform: uppercase; color: var(--color-text-muted, #888); margin: 0; }
.presets { display: flex; gap: 6px; }
.preset { padding: 8px 12px; border: 1px solid var(--color-border, #3a3a5a); border-radius: 6px; background: transparent; cursor: pointer; }
.preset.selected { border: 2px solid var(--color-accent, #6a4aff); background: rgba(106, 74, 255, 0.15); }
.hint { font-size: 11px; color: var(--color-text-muted, #888); margin: 0; }
</style>
```

- [ ] **Step 17.3: 在 ProjectSettingsPage 引入子组件**

找到合适位置（创作设置附近）加：

```vue
<ProjectSettingsIllustration
  :model-value="illustrationSettings"
  @update:model-value="(v) => { illustrationSettings = v; saveSettings() }"
/>
```

+ script 部分：

```javascript
import ProjectSettingsIllustration from '@/components/illustrations/ProjectSettingsIllustration.vue'
const illustrationSettings = ref({
  style_preset: 'ink',
  auto_generate: false,
  max_assets: 200,
  confirm_before_generate: true,
})
```

- [ ] **Step 17.4: 跑测试 + 提交**

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard && pnpm vitest run tests/components/illustrations/ProjectSettingsIllustration.spec.js
git add apps/dashboard/src/pages/ProjectSettingsPage.vue apps/dashboard/src/components/illustrations/ apps/dashboard/tests/
git commit -m "feat(phase-90): ProjectSettings illustration preferences"
```

---

## Task 18: 回归守门 (G1-G7)

**Files:**
- Create: `tests/test_phase90_illustrations.py`

- [ ] **Step 18.1: 写 G1-G7 guards** `tests/test_phase90_illustrations.py`

```python
"""Phase 90 — REQ-002 multimodal regression guards G1-G7.

Validates:
G1: 5 backend submodules exist
G2: 4 API routes registered
G3: pyproject.toml workspace + dependencies
G4: I087 invariant in architecture.yml
G5: 9-pattern audit clean (no infra.illustrations.* refs)
G6: storage path pattern matches
G7: .meta.json sidecar has 4 required fields
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "packages" / "lingwen-illustrations"
ROUTER = REPO / "apps" / "studio_api" / "routes" / "illustrations.py"
ARCH_YML = REPO / ".lingwen" / "architecture.yml"
PYPROJECT = REPO / "pyproject.toml"


# --- G1: 5 submodules ---

@pytest.mark.parametrize("submodule", [
    "metadata.py", "style_templates.py", "storage.py",
    "prompt_builder.py", "image_generator.py", "pipeline.py",
    "exceptions.py",
])
def test_g1_submodule_exists(submodule):
    p = PKG / "src" / "lingwen_illustrations" / submodule
    assert p.exists(), f"missing submodule: {submodule}"


# --- G2: 4 routes registered ---

def test_g2_routes_registered():
    content = ROUTER.read_text(encoding="utf-8")
    for route in [
        "@app.post(\"/api/illustrations/generate\"",
        "@app.get(\"/api/illustrations/list\"",
        "@app.delete(\"/api/illustrations/{asset_id}\"",
        "@app.get(\"/api/illustrations/{asset_id}/image\"",
    ]:
        assert route in content, f"missing route: {route}"


# --- G3: pyproject workspace + 3 deps ---

def test_g3_pyproject_workspace_and_deps():
    content = PYPROJECT.read_text(encoding="utf-8")
    assert "packages/lingwen-illustrations" in content, "workspace member missing"
    assert "lingwen-illustrations = { workspace = true }" in content, "dep entry missing"

    pkg_pyproject = (PKG / "pyproject.toml").read_text(encoding="utf-8")
    for dep in ["lingwen-llm-service", "lingwen-project-characters", "lingwen-paths"]:
        assert dep in pkg_pyproject, f"dep {dep} missing from package pyproject"


# --- G4: I087 invariant ---

def test_g4_i087_invariant():
    with ARCH_YML.open() as f:
        arch = yaml.safe_load(f)
    invariants = arch.get("invariants", [])
    ids = [inv.get("id") for inv in invariants]
    assert "I087" in ids, "I087 not in architecture.yml"

    i087 = next(inv for inv in invariants if inv.get("id") == "I087")
    rule = i087.get("rule", "")
    assert "lingwen-illustrations" in rule
    assert "infra.illustrations" in rule or "infra/illustrations" in rule


# --- G5: 9-pattern audit (no infra.illustrations.*) ---

@pytest.mark.parametrize("pattern,description", [
    (r"from infra\.illustrations", "literal dotted import"),
    (r"infra\.illustrations\.", "module reference"),
    (r"infra/illustrations", "filesystem path"),
])
def test_g5_no_infra_illustrations_refs(pattern, description):
    """Search all .py files for any reference to the old path."""
    import subprocess
    result = subprocess.run(
        ["grep", "-rn", "-E", pattern, str(REPO),
         "--include=*.py", "--exclude-dir=.venv", "--exclude-dir=__pycache__",
         "--exclude-dir=.git"],
        capture_output=True, text=True,
    )
    # Allow historical comments / docstrings mentioning migration
    lines = [l for l in result.stdout.splitlines()
             if "/test_phase90" not in l and "/test_phase18" not in l]
    assert not lines, f"found infra.illustrations refs:\n" + "\n".join(lines[:5])


# --- G6: storage path pattern ---

def test_g6_storage_path_pattern():
    from lingwen_illustrations.storage import asset_path
    # Cover
    p1 = asset_path(Path("/tmp/proj"), type="cover", id="abc")
    assert str(p1).endswith("/assets/covers/abc.jpg"), p1
    # Chapter
    p2 = asset_path(Path("/tmp/proj"), type="chapter", id="abc", chapter_num=17)
    assert str(p2).endswith("/assets/illustrations/chapter-017/abc.jpg"), p2


# --- G7: sidecar fields ---

def test_g7_sidecar_required_fields(tmp_path):
    from lingwen_illustrations.storage import save_asset
    from lingwen_illustrations.metadata import IllustrationMetadata

    meta = IllustrationMetadata(
        id="x", type="chapter", project_slug="p", chapter_num=1,
        style_preset="ink", custom_prompt=None, scene_json={"s": "x"},
        final_prompt="fp", prompt_hash="sha256:x", model="m",
        created_at="2026-09-15T00:00:00Z",
    )
    save_asset(tmp_path, b"data", meta)
    sidecar = tmp_path / "assets" / "illustrations" / "chapter-001" / "x.jpg.meta.json"
    assert sidecar.exists()
    payload = json.loads(sidecar.read_text())
    for field in ("prompt_hash", "style_preset", "scene_json", "created_at"):
        assert field in payload, f"missing required sidecar field: {field}"
```

- [ ] **Step 18.2: 跑测试确认 GREEN**

```bash
cd /home/ailearn/projects/LingWen && .venv/bin/python -m pytest tests/test_phase90_illustrations.py -v
```

Expected: 14+ passed (7 parametrized × N + 6 standalone)

- [ ] **Step 18.3: 提交**

```bash
git add tests/test_phase90_illustrations.py
git commit -m "test(phase-90): 7 regression guards G1-G7"
```

---

## Task 19: 全栈质量门 + handoff 文档

**Files:**
- Create: `docs/superpowers/handoffs/2026-09-15-phase-90-illustrations-handoff.md`
- Modify: `CLAUDE.md` (版本行 v54.21 → v55.0)
- Modify: `collaboration/CURRENT_STATUS.md` + `BACKLOG.md`

- [ ] **Step 19.1: 跑全栈质量门**

```bash
cd /home/ailearn/projects/LingWen
.venv/bin/python -m pytest packages/lingwen-illustrations/tests/ apps/studio_api/tests/test_illustrations_api.py tests/test_phase90_illustrations.py -v
.venv/bin/python -m ruff check packages/lingwen-illustrations/ apps/studio_api/routes/illustrations.py

cd apps/dashboard
pnpm vitest run
pnpm exec eslint src/composables/useIllustration.js src/stores/useIllustrationStore.js src/components/illustrations/ src/pages/WriteWorkspacePage.vue src/pages/LibraryPage.vue src/pages/ProjectSettingsPage.vue
pnpm tsc --noEmit
pnpm exec knip
pnpm build
```

Expected: 全绿

- [ ] **Step 19.2: 写 handoff 文档** `docs/superpowers/handoffs/2026-09-15-phase-90-illustrations-handoff.md`

（参考 Phase 79-87 handoff 模板：执行摘要 + commits + validation + lessons + carryover）

- [ ] **Step 19.3: 更新 CLAUDE.md 版本行**

```markdown
# 灵文 · 工业化小说生产系统
> **版本**: v55.0 (Phase 90 REQ-002 多模态: 封面/插图生成 — 5 backend modules + 4 API routes + 3 frontend pages + 7 regression guards; ARCHDEBT-REAL cycle 5/5 complete, NEW FEATURE phase 1 闭环)
```

+ 追加 I087 invariant 到 architecture invariants table

- [ ] **Step 19.4: 更新 CURRENT_STATUS.md + BACKLOG.md**

- REQ-002 从"待评估"移到"✅ 完成" (BACKLOG 需求池 section)
- CURRENT_STATUS 添加 Phase 90 闭环记录

- [ ] **Step 19.5: 提交 + push**

```bash
git add docs/ CLAUDE.md collaboration/
git commit -m "docs(phase-90): handoff + CLAUDE.md v55.0 + status sync"
git push origin master
```

---

## 自审清单

执行 plan 前再次确认：

- [x] Spec 7 个 section 都有对应 task（架构 1, 组件 1, 数据流 8, UI 11-17, 测试 18, 交付物 19）
- [x] 0 placeholder（每步都有完整代码）
- [x] 类型一致（meta 实例、error 路径、API 字段名跨 task 一致）
- [x] 测试 pattern 一致（pytest + vitest + 7 guards）
- [x] commit 模式：每 task 一个原子 commit (Phase 79-87 ARCHDEBT-REAL 模式)
- [x] 风险缓解（auto-generate fire-and-forget 不阻塞；错误独立 stage code）
