# Story Contracts Phase 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Story Contracts minimum viable product - genre routing CSV, anti-pattern aggregation, contract persistence to .story-system/, and context injection

**Architecture:** Data layer (CSV) → Contract engine (router + aggregator) → Persistence (.story-system/) → Injection (hooks.yaml)

**Tech Stack:** Python 3.13, CSV (UTF-8 BOM), JSON, SQLite (via existing workflow.db patterns)

---

## File Structure

### New Files

```
novel-factory/
├── rules/story_contracts/
│   └── 题材与调性推理.csv         # Genre routing table (seed data)
├── infra/story_contracts/
│   ├── __init__.py
│   ├── paths.py                 # StoryContractPaths - path management
│   ├── router.py                # GenreRouter - CSV routing logic
│   ├── anti_patterns.py         # AntiPatternAggregator - merge/dedup
│   ├── persister.py             # ContractPersister - JSON/MD persistence
│   ├── engine.py                # StoryContractEngine - main orchestrator
│   └── exceptions.py            # Custom exceptions
├── tests/story_contracts/
│   ├── __init__.py
│   ├── test_paths.py
│   ├── test_router.py
│   ├── test_anti_patterns.py
│   ├── test_persister.py
│   └── test_engine.py
└── infra/cli/commands.py         # Add story-contract command (MODIFY)
```

### Modified Files

- `novel-factory/infra/cli/commands.py` - Add `StoryContractCommand` to COMMANDS dict

---

## Task 1: StoryContractPaths Path Management

**Files:**
- Create: `novel-factory/infra/story_contracts/paths.py`
- Create: `novel-factory/tests/story_contracts/test_paths.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/story_contracts/test_paths.py
import pytest
from pathlib import Path
from infra.story_contracts.paths import StoryContractPaths

def test_paths_live_under_project_root(tmp_path):
    paths = StoryContractPaths.from_project_root(tmp_path)

    assert paths.root == tmp_path / ".story-system"
    assert paths.master_json == tmp_path / ".story-system" / "MASTER_SETTING.json"
    assert paths.anti_patterns_json == tmp_path / ".story-system" / "anti_patterns.json"
    assert paths.chapters_dir == tmp_path / ".story-system" / "chapters"
    assert paths.chapter_json(1) == tmp_path / ".story-system" / "chapters" / "chapter_001.json"

def test_paths_from_string_expands_user(tmp_path):
    paths = StoryContractPaths.from_project_root(str(tmp_path))
    assert paths.root == tmp_path / ".story-system"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd novel-factory && python -m pytest tests/story_contracts/test_paths.py::test_paths_live_under_project_root -v`
Expected: FAIL with "No module named 'infra.story_contracts.paths'"

- [ ] **Step 3: Write minimal implementation**

```python
# infra/story_contracts/paths.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StoryContractPaths:
    """Manages paths for story contract persistence."""
    project_root: Path

    @classmethod
    def from_project_root(cls, project_root: str | Path) -> "StoryContractPaths":
        return cls(Path(project_root).expanduser().resolve())

    @property
    def root(self) -> Path:
        return self.project_root / ".story-system"

    @property
    def chapters_dir(self) -> Path:
        return self.root / "chapters"

    @property
    def master_json(self) -> Path:
        return self.root / "MASTER_SETTING.json"

    @property
    def master_md(self) -> Path:
        return self.root / "MASTER_SETTING.md"

    @property
    def anti_patterns_json(self) -> Path:
        return self.root / "anti_patterns.json"

    @property
    def anti_patterns_md(self) -> Path:
        return self.root / "anti_patterns.md"

    def chapter_json(self, chapter: int) -> Path:
        return self.chapters_dir / f"chapter_{chapter:03d}.json"

    def chapter_md(self, chapter: int) -> Path:
        return self.chapters_dir / f"chapter_{chapter:03d}.md"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd novel-factory && python -m pytest tests/story_contracts/test_paths.py -v`
Expected: PASS

- [ ] **Step 5: Add __init__.py and commit**

```bash
touch novel-factory/infra/story_contracts/__init__.py
touch novel-factory/tests/story_contracts/__init__.py
git add infra/story_contracts/__init__.py infra/story_contracts/paths.py tests/story_contracts/__init__.py tests/story_contracts/test_paths.py
git commit -m "feat(story-contracts): add StoryContractPaths path management"
```

---

## Task 2: GenreRouter CSV Routing

**Files:**
- Create: `novel-factory/infra/story_contracts/router.py`
- Create: `novel-factory/tests/story_contracts/test_router.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/story_contracts/test_router.py
import pytest
import csv
from pathlib import Path
from infra.story_contracts.router import GenreRouter

def _write_csv(path, headers, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

def test_router_loads_csv_and_matches_keyword(tmp_path):
    csv_dir = tmp_path / "csv"
    csv_dir.mkdir()

    _write_csv(
        csv_dir / "题材与调性推理.csv",
        ["编号", "分类", "关键词", "意图与同义词", "题材/流派", "题材别名", "核心调性", "节奏策略", "强制禁忌/毒点", "推荐基础检索表", "推荐动态检索表"],
        [
            {
                "编号": "GR-001",
                "分类": "题材路由",
                "关键词": "玄幻退婚流|退婚打脸",
                "意图与同义词": "退婚流|废材逆袭",
                "题材/流派": "玄幻退婚流",
                "题材别名": "退婚流",
                "核心调性": "压抑蓄势后爆裂反击",
                "节奏策略": "前压后爆，三章内必须首个反打",
                "强制禁忌/毒点": "打脸节奏不能缺最后一拍补刀|配角不能压过主角兑现",
                "推荐基础检索表": "命名规则|人设与关系",
                "推荐动态检索表": "桥段套路|爽点与节奏",
            }
        ],
    )

    router = GenreRouter(csv_dir=csv_dir)
    result = router.route(query="我想写一个玄幻退婚流的故事")

    assert result.primary_genre == "玄幻退婚流"
    assert result.core_tone == "压抑蓄势后爆裂反击"
    assert result.route_source == "keyword_match"

def test_router_falls_back_to_explicit_genre(tmp_path):
    csv_dir = tmp_path / "csv"
    csv_dir.mkdir()

    _write_csv(
        csv_dir / "题材与调性推理.csv",
        ["编号", "分类", "关键词", "意图与同义词", "题材/流派", "题材别名", "核心调性", "节奏策略", "强制禁忌/毒点", "推荐基础检索表", "推荐动态检索表"],
        [
            {
                "编号": "GR-001",
                "分类": "题材路由",
                "关键词": "玄幻退婚流",
                "意图与同义词": "退婚流",
                "题材/流派": "玄幻退婚流",
                "题材别名": "退婚流",
                "核心调性": "压抑蓄势后爆裂反击",
                "节奏策略": "前压后爆",
                "强制禁忌/毒点": "",
                "推荐基础检索表": "命名规则",
                "推荐动态检索表": "桥段套路",
            }
        ],
    )

    router = GenreRouter(csv_dir=csv_dir)
    result = router.route(query="压抑一点，后面爆", genre="都市")

    assert result.primary_genre == "都市"
    assert result.route_source == "explicit_genre_fallback"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd novel-factory && python -m pytest tests/story_contracts/test_router.py -v`
Expected: FAIL with "No module named 'infra.story_contracts.router'"

- [ ] **Step 3: Write implementation**

```python
# infra/story_contracts/router.py
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional


@dataclass(frozen=True)
class RouteResult:
    primary_genre: str
    genre_aliases: List[str]
    core_tone: str
    pacing_strategy: str
    forbidden_patterns: List[str]
    recommended_base_tables: List[str]
    recommended_dynamic_tables: List[str]
    route_source: str  # keyword_match | explicit_genre_fallback | default_fallback


class GenreRouter:
    def __init__(self, csv_dir: str | Path):
        self.csv_dir = Path(csv_dir)

    def route(self, query: str, genre: Optional[str] = None) -> RouteResult:
        rows = self._load_csv_rows("题材与调性推理")
        query_text = self._normalize_text(f"{query} {genre or ''}")

        # Keyword match first
        for row in rows:
            keywords = self._split_multi_value(row.get("关键词", ""))
            synonyms = self._split_multi_value(row.get("意图与同义词", ""))
            aliases = self._split_multi_value(row.get("题材别名", ""))
            all_terms = keywords + synonyms + aliases

            if any(term and term in query_text for term in all_terms):
                return self._build_result(row, "keyword_match")

        # Explicit genre fallback
        if genre:
            for row in rows:
                applicable_genres = self._split_multi_value(row.get("题材/流派", ""))
                if genre in applicable_genres:
                    return self._build_result(row, "explicit_genre_fallback")

        # Default fallback
        if rows:
            return self._build_result(rows[0], "default_fallback")

        # Empty fallback
        return RouteResult(
            primary_genre=genre or "通用",
            genre_aliases=[],
            core_tone="",
            pacing_strategy="",
            forbidden_patterns=[],
            recommended_base_tables=["命名规则", "人设与关系"],
            recommended_dynamic_tables=["桥段套路", "爽点与节奏", "场景写法"],
            route_source="empty_fallback",
        )

    def _build_result(self, row: dict[str, Any], route_source: str) -> RouteResult:
        return RouteResult(
            primary_genre=str(row.get("题材/流派", "")).strip() or "通用",
            genre_aliases=self._split_multi_value(row.get("题材别名", "")),
            core_tone=str(row.get("核心调性", "")).strip(),
            pacing_strategy=str(row.get("节奏策略", "")).strip(),
            forbidden_patterns=self._split_multi_value(row.get("强制禁忌/毒点", "")),
            recommended_base_tables=self._split_multi_value(row.get("推荐基础检索表", "")),
            recommended_dynamic_tables=self._split_multi_value(row.get("推荐动态检索表", "")),
            route_source=route_source,
        )

    def _load_csv_rows(self, table_name: str) -> List[dict[str, Any]]:
        csv_path = self.csv_dir / f"{table_name}.csv"
        if not csv_path.is_file():
            return []
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    def _normalize_text(self, text: str) -> str:
        return text.lower().strip()

    def _split_multi_value(self, raw: Any) -> List[str]:
        return [item.strip() for item in str(raw or "").split("|") if item.strip()]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd novel-factory && python -m pytest tests/story_contracts/test_router.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add infra/story_contracts/router.py tests/story_contracts/test_router.py
git commit -m "feat(story-contracts): add GenreRouter CSV routing logic"
```

---

## Task 3: AntiPatternAggregator

**Files:**
- Create: `novel-factory/infra/story_contracts/anti_patterns.py`
- Create: `novel-factory/tests/story_contracts/test_anti_patterns.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/story_contracts/test_anti_patterns.py
import pytest
from infra.story_contracts.anti_patterns import AntiPatternAggregator, AntiPattern

def test_aggregator_deduplicates_by_text():
    aggregator = AntiPatternAggregator()

    patterns = aggregator.merge(
        [{"text": "打脸节奏不能缺补刀", "source_table": "题材与调性推理", "source_id": "GR-001"}],
        [{"text": "打脸节奏不能缺补刀", "source_table": "爽点与节奏", "source_id": "PA-001"}],
        [{"text": "配角不能压过主角", "source_table": "题材与调性推理", "source_id": "GR-001"}],
    )

    assert len(patterns) == 2
    texts = [p.text for p in patterns]
    assert "打脸节奏不能缺补刀" in texts
    assert "配角不能压过主角" in texts

def test_aggregator_preserves_first_occurrence_metadata():
    aggregator = AntiPatternAggregator()

    patterns = aggregator.merge(
        [{"text": "打脸节奏不能缺补刀", "source_table": "爽点与节奏", "source_id": "PA-001"}],
        [{"text": "打脸节奏不能缺补刀", "source_table": "题材与调性推理", "source_id": "GR-001"}],
    )

    # Should preserve first occurrence metadata
    assert patterns[0].source_table == "爽点与节奏"
    assert patterns[0].source_id == "PA-001"

def test_aggregator_empty_input():
    aggregator = AntiPatternAggregator()
    patterns = aggregator.merge()
    assert patterns == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd novel-factory && python -m pytest tests/story_contracts/test_anti_patterns.py -v`
Expected: FAIL with "No module named 'infra.story_contracts.anti_patterns'"

- [ ] **Step 3: Write implementation**

```python
# infra/story_contracts/anti_patterns.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List


@dataclass(frozen=True)
class AntiPattern:
    text: str
    source_table: str
    source_id: str


class AntiPatternAggregator:
    def merge(self, *groups: Iterable[dict[str, Any]]) -> List[AntiPattern]:
        seen: set[str] = set()
        result: List[AntiPattern] = []

        for group in groups:
            for row in group:
                text = str(row.get("text") or "").strip()
                if not text or text in seen:
                    continue
                seen.add(text)
                result.append(AntiPattern(
                    text=text,
                    source_table=str(row.get("source_table", "")),
                    source_id=str(row.get("source_id", "")),
                ))

        return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd novel-factory && python -m pytest tests/story_contracts/test_anti_patterns.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add infra/story_contracts/anti_patterns.py tests/story_contracts/test_anti_patterns.py
git commit -m "feat(story-contracts): add AntiPatternAggregator with dedup logic"
```

---

## Task 4: ContractPersister

**Files:**
- Create: `novel-factory/infra/story_contracts/persister.py`
- Create: `novel-factory/tests/story_contracts/test_persister.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/story_contracts/test_persister.py
import json
import pytest
from pathlib import Path
from infra.story_contracts.persister import ContractPersister, ContractPayload
from infra.story_contracts.paths import StoryContractPaths

def test_persist_writes_master_and_anti_patterns(tmp_path):
    paths = StoryContractPaths.from_project_root(tmp_path)
    persister = ContractPersister(paths)

    payload = ContractPayload(
        master_setting={
            "meta": {"schema_version": "story-contracts/v1", "contract_type": "MASTER_SETTING"},
            "route": {"primary_genre": "玄幻退婚流", "route_source": "keyword_match"},
            "master_constraints": {"core_tone": "压抑蓄势后爆裂反击"},
        },
        anti_patterns=[
            {"text": "打脸节奏不能缺补刀", "source_table": "题材与调性推理", "source_id": "GR-001"},
        ],
        chapter_brief=None,
    )

    persister.persist(payload)

    # Verify JSON files exist
    assert paths.master_json.exists()
    assert paths.anti_patterns_json.exists()

    # Verify content
    master_data = json.loads(paths.master_json.read_text(encoding="utf-8"))
    assert master_data["route"]["primary_genre"] == "玄幻退婚流"

    anti_data = json.loads(paths.anti_patterns_json.read_text(encoding="utf-8"))
    assert len(anti_data) == 1
    assert anti_data[0]["text"] == "打脸节奏不能缺补刀"

def test_persist_creates_directories(tmp_path):
    paths = StoryContractPaths.from_project_root(tmp_path / "book")
    persister = ContractPersister(paths)

    payload = ContractPayload(
        master_setting={"meta": {}},
        anti_patterns=[],
        chapter_brief=None,
    )

    persister.persist(payload)

    assert paths.root.exists()
    assert paths.master_json.exists()

def test_load_returns_none_if_no_files(tmp_path):
    paths = StoryContractPaths.from_project_root(tmp_path)
    persister = ContractPersister(paths)

    result = persister.load()

    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd novel-factory && python -m pytest tests/story_contracts/test_persister.py -v`
Expected: FAIL with "No module named 'infra.story_contracts.persister'"

- [ ] **Step 3: Write implementation**

```python
# infra/story_contracts/persister.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .paths import StoryContractPaths


MARKER_BEGIN = "<!-- STORY-SYSTEM:BEGIN -->"
MARKER_END = "<!-- STORY-SYSTEM:END -->"


@dataclass
class ContractPayload:
    master_setting: Dict[str, Any]
    anti_patterns: List[Dict[str, Any]]
    chapter_brief: Optional[Dict[str, Any]] = None


class ContractPersister:
    def __init__(self, paths: StoryContractPaths):
        self.paths = paths

    def persist(self, payload: ContractPayload) -> None:
        # Create directories
        self.paths.root.mkdir(parents=True, exist_ok=True)
        self.paths.chapters_dir.mkdir(parents=True, exist_ok=True)

        # Write master setting
        self._write_json(self.paths.master_json, payload.master_setting)
        self._write_markdown(
            self.paths.master_md,
            self._render_master_markdown(payload.master_setting)
        )

        # Write anti patterns
        self._write_json(self.paths.anti_patterns_json, payload.anti_patterns)
        self._write_markdown(
            self.paths.anti_patterns_md,
            self._render_anti_patterns_markdown(payload.anti_patterns)
        )

        # Write chapter brief if present
        if payload.chapter_brief:
            chapter_num = int(payload.chapter_brief.get("meta", {}).get("chapter", 0))
            if chapter_num > 0:
                self._write_json(self.paths.chapter_json(chapter_num), payload.chapter_brief)
                self._write_markdown(
                    self.paths.chapter_md(chapter_num),
                    self._render_chapter_markdown(payload.chapter_brief)
                )

    def load(self) -> Optional[ContractPayload]:
        if not self.paths.master_json.exists():
            return None

        master_setting = self._read_json(self.paths.master_json)
        anti_patterns = self._read_json(self.paths.anti_patterns_json) or []

        chapter_brief = None
        return ContractPayload(
            master_setting=master_setting,
            anti_patterns=anti_patterns,
            chapter_brief=chapter_brief,
        )

    def _write_json(self, path: Path, data: Any) -> None:
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def _read_json(self, path: Path) -> Any:
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Bad JSON in {path}") from exc

    def _write_markdown(self, path: Path, content: str) -> None:
        wrapped = f"{MARKER_BEGIN}\n{content.rstrip()}\n{MARKER_END}\n"
        if path.exists():
            current = path.read_text(encoding="utf-8")
            if MARKER_BEGIN in current and MARKER_END in current:
                before, _, rest = current.partition(MARKER_BEGIN)
                _, _, after = rest.partition(MARKER_END)
                path.write_text(f"{before}{wrapped}{after.lstrip()}", encoding="utf-8")
                return
        path.write_text(wrapped, encoding="utf-8")

    def _render_master_markdown(self, master: Dict[str, Any]) -> str:
        route = master.get("route", {})
        constraints = master.get("master_constraints", {})
        lines = ["# MASTER_SETTING", f"- 题材：{route.get('primary_genre', '')}"]
        if constraints.get("core_tone"):
            lines.append(f"- 调性：{constraints['core_tone']}")
        if constraints.get("pacing_strategy"):
            lines.append(f"- 节奏：{constraints['pacing_strategy']}")
        return "\n".join(lines)

    def _render_anti_patterns_markdown(self, patterns: List[Dict[str, Any]]) -> str:
        lines = ["# ANTI_PATTERNS"]
        for p in patterns:
            lines.append(f"- {p.get('text', '')}")
        return "\n".join(lines)

    def _render_chapter_markdown(self, chapter: Dict[str, Any]) -> str:
        chapter_num = int(chapter.get("meta", {}).get("chapter", 0))
        focus = (chapter.get("override_allowed") or {}).get("chapter_focus", "")
        return f"# CHAPTER_{chapter_num:03d}\n\n- 章节焦点：{focus}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd novel-factory && python -m pytest tests/story_contracts/test_persister.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add infra/story_contracts/persister.py tests/story_contracts/test_persister.py
git commit -m "feat(story-contracts): add ContractPersister for JSON/MD persistence"
```

---

## Task 5: StoryContractEngine

**Files:**
- Create: `novel-factory/infra/story_contracts/engine.py`
- Create: `novel-factory/tests/story_contracts/test_engine.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/story_contracts/test_engine.py
import pytest
import csv
from pathlib import Path
from infra.story_contracts.engine import StoryContractEngine

def _write_csv(path, headers, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

def test_engine_build_returns_contract(tmp_path):
    csv_dir = tmp_path / "csv"
    csv_dir.mkdir()

    _write_csv(
        csv_dir / "题材与调性推理.csv",
        ["编号", "分类", "关键词", "意图与同义词", "题材/流派", "题材别名", "核心调性", "节奏策略", "强制禁忌/毒点", "推荐基础检索表", "推荐动态检索表"],
        [
            {
                "编号": "GR-001",
                "分类": "题材路由",
                "关键词": "玄幻退婚流",
                "意图与同义词": "退婚流",
                "题材/流派": "玄幻退婚流",
                "题材别名": "退婚流",
                "核心调性": "压抑蓄势后爆裂反击",
                "节奏策略": "前压后爆",
                "强制禁忌/毒点": "打脸节奏不能缺最后一拍补刀",
                "推荐基础检索表": "命名规则",
                "推荐动态检索表": "桥段套路",
            }
        ],
    )

    engine = StoryContractEngine(csv_dir=csv_dir)
    contract = engine.build(query="我想写玄幻退婚流", genre=None)

    assert contract.master_setting.route.primary_genre == "玄幻退婚流"
    assert contract.master_setting.master_constraints.core_tone == "压抑蓄势后爆裂反击"
    assert len(contract.anti_patterns) == 1
    assert contract.anti_patterns[0].text == "打脸节奏不能缺最后一拍补刀"

def test_engine_build_with_chapter(tmp_path):
    csv_dir = tmp_path / "csv"
    csv_dir.mkdir()

    _write_csv(
        csv_dir / "题材与调性推理.csv",
        ["编号", "分类", "关键词", "意图与同义词", "题材/流派", "题材别名", "核心调性", "节奏策略", "强制禁忌/毒点", "推荐基础检索表", "推荐动态检索表"],
        [
            {
                "编号": "GR-001",
                "分类": "题材路由",
                "关键词": "玄幻",
                "意图与同义词": "",
                "题材/流派": "玄幻",
                "题材别名": "",
                "核心调性": "热血",
                "节奏策略": "升级",
                "强制禁忌/毒点": "",
                "推荐基础检索表": "命名规则",
                "推荐动态检索表": "桥段套路",
            }
        ],
    )

    engine = StoryContractEngine(csv_dir=csv_dir)
    contract = engine.build(query="玄幻", genre=None, chapter=1)

    assert contract.chapter_brief is not None
    assert contract.chapter_brief.meta.chapter == 1

def test_engine_persist_and_load(tmp_path):
    csv_dir = tmp_path / "csv"
    csv_dir.mkdir()

    _write_csv(
        csv_dir / "题材与调性推理.csv",
        ["编号", "分类", "关键词", "意图与同义词", "题材/流派", "题材别名", "核心调性", "节奏策略", "强制禁忌/毒点", "推荐基础检索表", "推荐动态检索表"],
        [
            {
                "编号": "GR-001",
                "分类": "题材路由",
                "关键词": "退婚",
                "意图与同义词": "",
                "题材/流派": "玄幻退婚流",
                "题材别名": "",
                "核心调性": "压抑蓄势",
                "节奏策略": "前压后爆",
                "强制禁忌/毒点": "打脸不能软",
                "推荐基础检索表": "命名规则",
                "推荐动态检索表": "桥段套路",
            }
        ],
    )

    project_root = tmp_path / "book"
    engine = StoryContractEngine(csv_dir=csv_dir)

    # Build and persist
    contract = engine.build(query="退婚", genre=None)
    engine.persist(project_root, contract)

    # Load and verify
    loaded = engine.load(project_root)
    assert loaded is not None
    assert loaded.master_setting.route.primary_genre == "玄幻退婚流"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd novel-factory && python -m pytest tests/story_contracts/test_engine.py -v`
Expected: FAIL with "No module named 'infra.story_contracts.engine'"

- [ ] **Step 3: Write implementation**

```python
# infra/story_contracts/engine.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .paths import StoryContractPaths
from .router import GenreRouter, RouteResult
from .anti_patterns import AntiPatternAggregator, AntiPattern
from .persister import ContractPersister, ContractPayload


@dataclass(frozen=True)
class MasterSettingPayload:
    meta: Dict[str, Any]
    route: RouteResult
    master_constraints: Dict[str, Any]
    source_trace: List[Dict[str, Any]]


@dataclass
class ChapterBriefPayload:
    meta: Dict[str, Any]
    override_allowed: Dict[str, Any]
    source_trace: List[Dict[str, Any]]


@dataclass
class ContractResult:
    master_setting: MasterSettingPayload
    anti_patterns: List[AntiPattern]
    chapter_brief: Optional[ChapterBriefPayload]


class StoryContractEngine:
    def __init__(self, csv_dir: str | Path):
        self.csv_dir = Path(csv_dir)
        self.router = GenreRouter(csv_dir)
        self.aggregator = AntiPatternAggregator()

    def build(self, query: str, genre: Optional[str], chapter: Optional[int] = None) -> ContractResult:
        route = self.router.route(query=query, genre=genre)

        # Build anti-patterns from route
        route_anti_patterns = []
        for text in route.forbidden_patterns:
            route_anti_patterns.append({
                "text": text,
                "source_table": "题材与调性推理",
                "source_id": "route",
            })

        merged_patterns = self.aggregator.merge(route_anti_patterns)

        master_constraints = {
            "core_tone": route.core_tone,
            "pacing_strategy": route.pacing_strategy,
            "forbidden_patterns": route.forbidden_patterns,
        }

        master_setting = MasterSettingPayload(
            meta={
                "schema_version": "story-contracts/v1",
                "contract_type": "MASTER_SETTING",
                "query": query,
                "genre": genre or "",
            },
            route=route,
            master_constraints=master_constraints,
            source_trace=[{"table": "题材与调性推理", "id": "route", "reason": route.route_source}],
        )

        chapter_brief = None
        if chapter is not None:
            chapter_brief = ChapterBriefPayload(
                meta={
                    "schema_version": "story-contracts/v1",
                    "contract_type": "CHAPTER_BRIEF",
                    "chapter": chapter,
                },
                override_allowed={"chapter_focus": ""},
                source_trace=[],
            )

        return ContractResult(
            master_setting=master_setting,
            anti_patterns=merged_patterns,
            chapter_brief=chapter_brief,
        )

    def persist(self, project_root: str | Path, contract: ContractResult) -> None:
        paths = StoryContractPaths.from_project_root(project_root)
        persister = ContractPersister(paths)

        master_dict = {
            "meta": contract.master_setting.meta,
            "route": {
                "primary_genre": contract.master_setting.route.primary_genre,
                "genre_aliases": contract.master_setting.route.genre_aliases,
                "route_source": contract.master_setting.route.route_source,
            },
            "master_constraints": contract.master_setting.master_constraints,
            "source_trace": contract.master_setting.source_trace,
        }

        anti_patterns_dict = [
            {"text": p.text, "source_table": p.source_table, "source_id": p.source_id}
            for p in contract.anti_patterns
        ]

        chapter_dict = None
        if contract.chapter_brief:
            chapter_dict = {
                "meta": contract.chapter_brief.meta,
                "override_allowed": contract.chapter_brief.override_allowed,
                "source_trace": contract.chapter_brief.source_trace,
            }

        payload = ContractPayload(
            master_setting=master_dict,
            anti_patterns=anti_patterns_dict,
            chapter_brief=chapter_dict,
        )

        persister.persist(payload)

    def load(self, project_root: str | Path) -> Optional[ContractResult]:
        paths = StoryContractPaths.from_project_root(project_root)
        persister = ContractPersister(paths)
        loaded = persister.load()

        if loaded is None:
            return None

        route_dict = loaded.master_setting.get("route", {})
        route = RouteResult(
            primary_genre=route_dict.get("primary_genre", ""),
            genre_aliases=route_dict.get("genre_aliases", []),
            core_tone=loaded.master_setting.get("master_constraints", {}).get("core_tone", ""),
            pacing_strategy=loaded.master_setting.get("master_constraints", {}).get("pacing_strategy", ""),
            forbidden_patterns=loaded.master_setting.get("master_constraints", {}).get("forbidden_patterns", []),
            recommended_base_tables=[],
            recommended_dynamic_tables=[],
            route_source=route_dict.get("route_source", ""),
        )

        master_setting = MasterSettingPayload(
            meta=loaded.master_setting.get("meta", {}),
            route=route,
            master_constraints=loaded.master_setting.get("master_constraints", {}),
            source_trace=loaded.master_setting.get("source_trace", []),
        )

        anti_patterns = [
            AntiPattern(text=p["text"], source_table=p["source_table"], source_id=p["source_id"])
            for p in loaded.anti_patterns
        ]

        chapter_brief = None
        if loaded.chapter_brief:
            chapter_brief = ChapterBriefPayload(
                meta=loaded.chapter_brief.get("meta", {}),
                override_allowed=loaded.chapter_brief.get("override_allowed", {}),
                source_trace=loaded.chapter_brief.get("source_trace", []),
            )

        return ContractResult(
            master_setting=master_setting,
            anti_patterns=anti_patterns,
            chapter_brief=chapter_brief,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd novel-factory && python -m pytest tests/story_contracts/test_engine.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add infra/story_contracts/engine.py tests/story_contracts/test_engine.py
git commit -m "feat(story-contracts): add StoryContractEngine orchestrator"
```

---

## Task 6: CLI Integration

**Files:**
- Modify: `novel-factory/infra/cli/commands.py`
- Create: `novel-factory/rules/story_contracts/题材与调性推理.csv` (seed data)

- [ ] **Step 1: Add seed CSV data**

Create `novel-factory/rules/story_contracts/题材与调性推理.csv` with 3 seed rows:
```csv
编号,分类,层级,关键词,意图与同义词,适用题材,大模型指令,核心摘要,详细展开,题材/流派,题材别名,核心调性,节奏策略,强制禁忌/毒点,推荐基础检索表,推荐动态检索表,默认查询词
GR-001,write|plan,知识补充,玄幻退婚流|退婚打脸,退婚流|废材逆袭,玄幻,先压后爆,玄幻退婚流需要耻辱起手和强兑现,,玄幻退婚流,退婚流|废材逆袭,压抑蓄势后爆裂反击,前压后爆，三章内必须首个反打,打脸节奏不能缺最后一拍补刀|配角不能压过主角兑现,命名规则|人设与关系|金手指与设定,桥段套路|爽点与节奏|场景写法,退婚|打脸|废材逆袭
GR-002,write|plan,知识补充,规则动物园|怪谈副本,规则怪谈|动物园规则,悬疑|轻小说,规则先立死，代价必须兑现,规则动物园重在规则压迫与试错代价,,规则动物园,规则怪谈|动物园规则,诡异压迫与冷感观察,每章至少一个规则验证或误判后果,规则解释过量|系统提前剧透真相,命名规则|人设与关系,桥段套路|场景写法|写作技法,规则|动物园|副本
GR-003,write|plan,知识补充,压抑后爆|后期翻盘,压抑一点后面爆|前面憋屈后面翻盘,现言|都市,压抑不能空耗，必须绑定后续兑现资产,压抑后爆路线需要持续累积反弹势能,,压抑后爆,前憋后爆|后期翻盘,持续压迫后的集中爆发,每2-3章必须补一个可见反抗信号,压抑没有收益|委屈全靠旁白硬说,命名规则|人设与关系|写作技法,爽点与节奏|场景写法|桥段套路,压抑|翻盘|反弹
```

- [ ] **Step 2: Add CLI command to commands.py**

Add `StoryContractCommand` to COMMANDS dict in `infra/cli/commands.py`:

```python
class StoryContractCommand:
    def __init__(self, paths: CLIProjectPaths):
        self.paths = paths

    def execute(self, args: list[str]) -> bool:
        from infra.story_contracts import StoryContractEngine

        parser = argparse.ArgumentParser(description="Story Contracts")
        parser.add_argument("query", help="题材描述或当前意图")
        parser.add_argument("--genre", default="", help="显式题材")
        parser.add_argument("--chapter", type=int, default=0, help="章节号")
        parser.add_argument("--persist", action="store_true", help="写入 .story-system/")
        parsed = parser.parse_args(args)

        csv_dir = Path(__file__).parent.parent.parent / "rules" / "story_contracts"
        engine = StoryContractEngine(csv_dir=csv_dir)

        chapter = parsed.chapter if parsed.chapter > 0 else None
        contract = engine.build(query=parsed.query, genre=parsed.genre or None, chapter=chapter)

        if parsed.persist:
            engine.persist(self.paths.project_root, contract)
            print(f"已写入 {self.paths.project_root / '.story-system'}")
        else:
            import json
            print(json.dumps({
                "primary_genre": contract.master_setting.route.primary_genre,
                "core_tone": contract.master_setting.master_constraints.get("core_tone", ""),
                "anti_patterns": [p.text for p in contract.anti_patterns],
            }, ensure_ascii=False, indent=2))

        return True
```

- [ ] **Step 3: Add to COMMANDS dict and commit**

In `commands.py`, add to COMMANDS dict:
```python
"story-contract": StoryContractCommand,
```

Run tests and commit:
```bash
git add infra/cli/commands.py rules/story_contracts/
git commit -m "feat(story-contracts): add CLI command and seed CSV data"
```

---

## Task 7: Integration Tests

**Files:**
- Create: `novel-factory/tests/story_contracts/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# tests/story_contracts/test_integration.py
import pytest
import csv
from pathlib import Path
from infra.story_contracts import StoryContractEngine

def _write_csv(path, headers, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

def test_full_flow_build_persist_load(tmp_path):
    csv_dir = tmp_path / "csv"
    csv_dir.mkdir()

    _write_csv(
        csv_dir / "题材与调性推理.csv",
        ["编号", "分类", "关键词", "意图与同义词", "题材/流派", "题材别名", "核心调性", "节奏策略", "强制禁忌/毒点", "推荐基础检索表", "推荐动态检索表"],
        [
            {
                "编号": "GR-001",
                "分类": "题材路由",
                "关键词": "玄幻退婚流",
                "意图与同义词": "退婚流",
                "题材/流派": "玄幻退婚流",
                "题材别名": "退婚流",
                "核心调性": "压抑蓄势后爆裂反击",
                "节奏策略": "前压后爆",
                "强制禁忌/毒点": "打脸节奏不能缺最后一拍补刀",
                "推荐基础检索表": "命名规则",
                "推荐动态检索表": "桥段套路",
            }
        ],
    )

    project_root = tmp_path / "book"
    engine = StoryContractEngine(csv_dir=csv_dir)

    # Build
    contract = engine.build(query="我想写玄幻退婚流", genre=None, chapter=1)
    assert contract.master_setting.route.primary_genre == "玄幻退婚流"
    assert len(contract.anti_patterns) == 1

    # Persist
    engine.persist(project_root, contract)
    assert (project_root / ".story-system" / "MASTER_SETTING.json").exists()
    assert (project_root / ".story-system" / "anti_patterns.json").exists()
    assert (project_root / ".story-system" / "chapters" / "chapter_001.json").exists()

    # Load
    loaded = engine.load(project_root)
    assert loaded is not None
    assert loaded.master_setting.route.primary_genre == "玄幻退婚流"
    assert len(loaded.anti_patterns) == 1
```

- [ ] **Step 2: Run test to verify it passes**

Run: `cd novel-factory && python -m pytest tests/story_contracts/test_integration.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/story_contracts/test_integration.py
git commit -m "test(story-contracts): add integration tests for full flow"
```

---

## Completion Criteria

- All 7 tasks completed
- All tests passing (minimum 20 tests)
- CLI command works: `lingwen.py story-contract "玄幻退婚流" --persist`
- Contract files written to `.story-system/`
- No modifications to existing S1-S11 quality framework

---

## Spec Coverage Check

| Spec Requirement | Task |
|-----------------|------|
| 题材路由CSV | Task 2 (GenreRouter) |
| Anti-patterns聚合 | Task 3 (AntiPatternAggregator) |
| JSON持久化 | Task 4 (ContractPersister) |
| MD渲染 | Task 4 (ContractPersister) |
| CLI集成 | Task 6 (CLI) |
| Context注入接口 | Task 5 (Engine.load) |
| 种子数据 | Task 6 (CSV) |

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-31-story-contracts-phase3-plan.md`**

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**