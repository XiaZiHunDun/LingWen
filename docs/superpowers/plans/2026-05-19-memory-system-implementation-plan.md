# 记忆系统实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 构建整合记忆系统，统一向量记忆与状态追踪，实现上下文自动推送与主动查询

**架构：** 采用 Qdrant 向量存储 + 文件系统状态快照的双层架构。MemoryGateway 作为统一入口，QueryEngine 处理混合检索，PushEngine 负责章节变更时自动推送上下文。

**技术栈：** Python, Qdrant, PyMilvus/Embedding模型, PyYAML, JSON

---

## 文件结构

```
novel-factory/
├── memory_system/
│   ├── __init__.py
│   ├── gateway/
│   │   ├── __init__.py
│   │   ├── memory_gateway.py        # 统一入口
│   │   ├── query_engine.py         # 混合查询引擎
│   │   └── push_engine.py           # 自动推送引擎
│   ├── vector/
│   │   ├── __init__.py
│   │   ├── qdrant_client.py        # Qdrant客户端封装
│   │   ├── embedder.py             # 嵌入模型管理
│   │   └── collections.py          # 集合管理
│   ├── state/
│   │   ├── __init__.py
│   │   ├── character_tracker.py    # 角色状态追踪
│   │   ├── plot_thread_tracker.py  # 伏笔追踪
│   │   ├── timeline_manager.py      # 时间线管理
│   │   └── fact_base.py             # 事实库管理
│   ├── config/
│   │   ├── __init__.py
│   │   ├── memory_config.yaml       # 记忆系统配置
│   │   └── collections_schema.yaml # 集合Schema
│   └── scripts/
│       ├── __init__.py
│       ├── init_memory.py          # 初始化脚本
│       ├── embed_chapters.py       # 章节批量嵌入
│       ├── query_context.py        # 上下文查询
│       └── update_state.py          # 状态更新
```

---

## 数据结构定义

### collections_schema.yaml (Qdrant集合配置)

```yaml
collections:
  chapters_seg:
    description: "章节内容片段向量"
    vector_size: 1536
    distance: "Cosine"
    fields:
      - name: "chapter"
        type: "integer"
      - name: "segment_text"
        type: "text"
      - name: "characters"
        type: "array_of_keyword"
      - name: "location"
        type: "keyword"
      - name: "time_marker"
        type: "text"
      - name: "tags"
        type: "array_of_keyword"

  entities:
    description: "实体向量（角色/物品/地点）"
    vector_size: 1536
    distance: "Cosine"
    fields:
      - name: "entity_type"
        type: "keyword"
      - name: "name"
        type: "text"
      - name: "current_state"
        type: "text"
      - name: "first_appearance"
        type: "integer"
      - name: "key_attributes"
        type: "array_of_keyword"

  relationships:
    description: "关系向量"
    vector_size: 1536
    distance: "Cosine"
    fields:
      - name: "source"
        type: "keyword"
      - name: "target"
        type: "keyword"
      - name: "relationship_type"
        type: "keyword"
      - name: "trust_level"
        type: "keyword"
      - name: "chapter_start"
        type: "integer"
      - name: "chapter_end"
        type: "text"
```

### state_tracker.json (角色状态快照)

```json
{
  "characters": {
    "<角色名>": {
      "current_location": "<位置>",
      "current_form": "<形态>",
      "alive": true,
      "emotion_state": "<情绪>",
      "last_updated_chapter": 50
    }
  },
  "items": {
    "<物品名>": {
      "owner": "<角色名>",
      "location": "<位置>",
      "status": "<状态>",
      "last_updated_chapter": 50
    }
  }
}
```

### plot_threads.yaml (伏笔追踪表)

```yaml
threads:
  - id: "FP-001"
    introduced_chapter: 5
    status: "pending"  # pending / in_progress / recycled / invalid
    description: "<伏笔描述>"
    key_mentions: [5, 20, 45, 80]
    expected_recycle: "ch150-ch180"
    actual_recycle: null
```

### timeline.json (时间线索引)

```json
{
  "events": [
    {
      "id": "EVT-001",
      "chapter": 50,
      "time_marker": "战后第3天",
      "location": "灰巢废墟",
      "description": "铁蛋调试信号器",
      "participants": ["铁蛋"]
    }
  ]
}
```

---

## 任务清单

### Task 1: 初始化脚本与目录结构

**Files:**
- Create: `novel-factory/memory_system/__init__.py`
- Create: `novel-factory/memory_system/gateway/__init__.py`
- Create: `novel-factory/memory_system/vector/__init__.py`
- Create: `novel-factory/memory_system/state/__init__.py`
- Create: `novel-factory/memory_system/config/__init__.py`
- Create: `novel-factory/memory_system/scripts/__init__.py`
- Create: `docs/superpowers/plans/2026-05-19-memory-system-implementation-plan.md`

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p novel-factory/memory_system/{gateway,vector,state,config,scripts}
touch novel-factory/memory_system/__init__.py
touch novel-factory/memory_system/gateway/__init__.py
touch novel-factory/memory_system/vector/__init__.py
touch novel-factory/memory_system/state/__init__.py
touch novel-factory/memory_system/config/__init__.py
touch novel-factory/memory_system/scripts/__init__.py
```

- [ ] **Step 2: 创建 collections_schema.yaml**

```yaml
# novel-factory/memory_system/config/collections_schema.yaml
collections:
  chapters_seg:
    description: "章节内容片段向量"
    vector_size: 1536
    distance: "Cosine"

  entities:
    description: "实体向量（角色/物品/地点）"
    vector_size: 1536
    distance: "Cosine"

  relationships:
    description: "关系向量"
    vector_size: 1536
    distance: "Cosine"
```

- [ ] **Step 3: 创建 memory_config.yaml**

```yaml
# novel-factory/memory_system/config/memory_config.yaml
qdrant:
  host: "localhost"
  port: 6333
  grpc_port: 6334

embedding:
  model: "text-embedding-3-small"
  dimension: 1536

storage:
  state_file: "novel-factory/memory_system/state/state_tracker.json"
  plot_threads_file: "novel-factory/memory_system/state/plot_threads.yaml"
  timeline_file: "novel-factory/memory_system/state/timeline.json"

retrieval:
  default_top_k: 5
  hybrid_alpha: 0.7  # 向量权重
```

- [ ] **Step 4: 提交**

```bash
git add novel-factory/memory_system/
git commit -m "feat(memory): 创建记忆系统目录结构"
```

---

### Task 2: Qdrant客户端封装

**Files:**
- Create: `novel-factory/memory_system/vector/qdrant_client.py`
- Create: `tests/memory_system/test_qdrant_client.py`

- [ ] **Step 1: 编写测试**

```python
# tests/memory_system/test_qdrant_client.py
import pytest
from memory_system.vector.qdrant_client import QdrantClientWrapper

def test_qdrant_client_initialization():
    client = QdrantClientWrapper(host="localhost", port=6333)
    assert client.host == "localhost"
    assert client.port == 6333

def test_get_collections():
    client = QdrantClientWrapper(host="localhost", port=6333)
    collections = client.get_collections()
    assert isinstance(collections, list)
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/memory_system/test_qdrant_client.py -v
# 预期: FAIL - module 'memory_system.vector.qdrant_client' has no attribute 'QdrantClientWrapper'
```

- [ ] **Step 3: 实现 QdrantClientWrapper**

```python
# novel-factory/memory_system/vector/qdrant_client.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from typing import List, Optional
import yaml

class QdrantClientWrapper:
    def __init__(self, host: str = "localhost", port: int = 6333, grpc_port: int = 6334):
        self.client = QdrantClient(host=host, port=port, grpc_port=grpc_port)
        self.host = host
        self.port = port
        self.grpc_port = grpc_port

    def get_collections(self) -> List[str]:
        return [c.name for c in self.client.get_collections().collections]

    def create_collection(self, collection_name: str, vector_size: int = 1536, distance: str = "Cosine"):
        self.client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance[distance]
            )
        )

    def upsert(self, collection_name: str, points: List[dict]):
        from qdrant_client.models import PointStruct, Payload
        self.client.upsert(
            collection_name=collection_name,
            points=[
                PointStruct(
                    id=point["id"],
                    vector=point["vector"],
                    payload=point.get("payload", {})
                )
                for point in points
            ]
        )

    def search(self, collection_name: str, query_vector: List[float], top_k: int = 5, query_filter: Optional[dict] = None):
        return self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter
        )

    def scroll(self, collection_name: str, filter_cond: Optional[dict] = None, limit: int = 100):
        return self.client.scroll(collection_name=collection_name, filter=filter_cond, limit=limit)
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/memory_system/test_qdrant_client.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/memory_system/vector/qdrant_client.py tests/memory_system/test_qdrant_client.py
git commit -m "feat(memory): 实现Qdrant客户端封装"
```

---

### Task 3: 嵌入模型管理

**Files:**
- Create: `novel-factory/memory_system/vector/embedder.py`
- Create: `tests/memory_system/test_embedder.py`

- [ ] **Step 1: 编写测试**

```python
# tests/memory_system/test_embedder.py
import pytest
from memory_system.vector.embedder import Embedder

def test_embedder_initialization():
    embedder = Embedder(model="text-embedding-3-small")
    assert embedder.model == "text-embedding-3-small"
    assert embedder.dimension == 1536

def test_embed_single_text():
    embedder = Embedder()
    result = embedder.embed("测试文本")
    assert isinstance(result, list)
    assert len(result) == 1536

def test_embed_batch():
    embedder = Embedder()
    texts = ["文本1", "文本2", "文本3"]
    results = embedder.embed_batch(texts)
    assert len(results) == 3
    assert all(len(r) == 1536 for r in results)
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/memory_system/test_embedder.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 Embedder**

```python
# novel-factory/memory_system/vector/embedder.py
from openai import OpenAI
from typing import List, Optional
import os

class Embedder:
    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        self.dimension = 1536
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def embed(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [item.embedding for item in response.data]
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/memory_system/test_embedder.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/memory_system/vector/embedder.py tests/memory_system/test_embedder.py
git commit -m "feat(memory): 实现嵌入模型管理"
```

---

### Task 4: 集合管理器

**Files:**
- Create: `novel-factory/memory_system/vector/collections.py`
- Create: `tests/memory_system/test_collections.py`

- [ ] **Step 1: 编写测试**

```python
# tests/memory_system/test_collections.py
import pytest
from memory_system.vector.collections import CollectionManager
from memory_system.vector.qdrant_client import QdrantClientWrapper

def test_collection_manager_init():
    client = QdrantClientWrapper()
    manager = CollectionManager(client)
    assert manager.client is not None

def test_init_collections_from_schema():
    client = QdrantClientWrapper()
    manager = CollectionManager(client)
    # 注意: 实际运行需要Qdrant服务
    # 这里只测试方法存在
    assert hasattr(manager, 'init_collections')
    assert hasattr(manager, 'get_collection_info')
```

- [ ] **Step 2: 实现 CollectionManager**

```python
# novel-factory/memory_system/vector/collections.py
from typing import Dict, List, Optional
import yaml
from .qdrant_client import QdrantClientWrapper

class CollectionManager:
    def __init__(self, client: QdrantClientWrapper, schema_path: Optional[str] = None):
        self.client = client
        self.schema_path = schema_path or "novel-factory/memory_system/config/collections_schema.yaml"
        self._schema = self._load_schema()

    def _load_schema(self) -> Dict:
        with open(self.schema_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def init_collections(self):
        """根据schema初始化所有集合"""
        for collection_name, config in self._schema.get("collections", {}).items():
            vector_size = config.get("vector_size", 1536)
            distance = config.get("distance", "Cosine")
            self.client.create_collection(collection_name, vector_size, distance)

    def get_collection_info(self, collection_name: str) -> Dict:
        collections = self.client.get_collections()
        if collection_name in collections:
            return {"name": collection_name, "exists": True}
        return {"name": collection_name, "exists": False}

    def list_collections(self) -> List[str]:
        return self.client.get_collections()
```

- [ ] **Step 3: 运行测试验证**

```bash
pytest tests/memory_system/test_collections.py -v
# 预期: PASS (mock或实际Qdrant)
```

- [ ] **Step 4: 提交**

```bash
git add novel-factory/memory_system/vector/collections.py tests/memory_system/test_collections.py
git commit -m "feat(memory): 实现集合管理器"
```

---

### Task 5: 状态管理基类与文件操作

**Files:**
- Create: `novel-factory/memory_system/state/state_manager.py`
- Create: `tests/memory_system/test_state_manager.py`

- [ ] **Step 1: 编写测试**

```python
# tests/memory_system/test_state_manager.py
import pytest
import json
import tempfile
import os
from memory_system.state.state_manager import StateManager

def test_state_manager_initialization():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "state.json")
        manager = StateManager(state_file)
        assert manager.state_file == state_file

def test_load_state():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "state.json")
        data = {"characters": {"铁蛋": {"alive": True}}}
        with open(state_file, 'w') as f:
            json.dump(data, f)
        manager = StateManager(state_file)
        state = manager.load_state()
        assert state["characters"]["铁蛋"]["alive"] == True

def test_save_state():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "state.json")
        manager = StateManager(state_file)
        data = {"characters": {"铁蛋": {"alive": True}}}
        manager.save_state(data)
        with open(state_file, 'r') as f:
            loaded = json.load(f)
        assert loaded["characters"]["铁蛋"]["alive"] == True
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/memory_system/test_state_manager.py -v
# 预期: FAIL - module not found
```

- [ ] **Step 3: 实现 StateManager**

```python
# novel-factory/memory_system/state/state_manager.py
import json
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

class StateManager:
    def __init__(self, state_file: str):
        self.state_file = state_file
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        Path(self.state_file).parent.mkdir(parents=True, exist_ok=True)
        if not Path(self.state_file).exists():
            self.save_state({})

    def load_state(self) -> Dict[str, Any]:
        with open(self.state_file, 'r', encoding='utf-8') as f:
            if self.state_file.endswith('.yaml') or self.state_file.endswith('.yml'):
                return yaml.safe_load(f) or {}
            return json.load(f)

    def save_state(self, state: Dict[str, Any]):
        with open(self.state_file, 'w', encoding='utf-8') as f:
            if self.state_file.endswith('.yaml') or self.state_file.endswith('.yml'):
                yaml.dump(state, f, allow_unicode=True)
            else:
                json.dump(state, f, ensure_ascii=False, indent=2)

    def update_key(self, key_path: str, value: Any):
        """更新嵌套键，如 'characters.铁蛋.alive'"""
        state = self.load_state()
        keys = key_path.split('.')
        current = state
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
        self.save_state(state)

    def get_key(self, key_path: str, default: Any = None) -> Any:
        """获取嵌套键的值"""
        state = self.load_state()
        keys = key_path.split('.')
        current = state
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/memory_system/test_state_manager.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/memory_system/state/state_manager.py tests/memory_system/test_state_manager.py
git commit -m "feat(memory): 实现状态管理基类"
```

---

### Task 6: 角色状态追踪

**Files:**
- Create: `novel-factory/memory_system/state/character_tracker.py`
- Create: `tests/memory_system/test_character_tracker.py`

- [ ] **Step 1: 编写测试**

```python
# tests/memory_system/test_character_tracker.py
import pytest
import tempfile
import os
from memory_system.state.character_tracker import CharacterTracker

def test_character_tracker_init():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "state.json")
        tracker = CharacterTracker(state_file)
        assert tracker.state_file == state_file

def test_register_character():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "state.json")
        tracker = CharacterTracker(state_file)
        tracker.register_character("铁蛋", first_appearance=1, attributes=["机械师", "话少可靠"])
        state = tracker.get_state()
        assert "铁蛋" in state["characters"]

def test_update_character_state():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "state.json")
        tracker = CharacterTracker(state_file)
        tracker.register_character("铁蛋", first_appearance=1)
        tracker.update_character_state("铁蛋", location="灰巢废墟", alive=True)
        state = tracker.get_character_state("铁蛋")
        assert state["current_location"] == "灰巢废墟"
        assert state["alive"] == True
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/memory_system/test_character_tracker.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 CharacterTracker**

```python
# novel-factory/memory_system/state/character_tracker.py
from typing import Dict, List, Optional, Any
from .state_manager import StateManager

class CharacterTracker:
    def __init__(self, state_file: str):
        self.state_manager = StateManager(state_file)
        self._ensure_initial_state()

    def _ensure_initial_state(self):
        state = self.state_manager.load_state()
        if "characters" not in state:
            state["characters"] = {}
            self.state_manager.save_state(state)

    def get_state(self) -> Dict:
        return self.state_manager.load_state()

    def register_character(self, name: str, first_appearance: int, attributes: Optional[List[str]] = None, voice_pattern: Optional[str] = None):
        state = self.state_manager.load_state()
        state["characters"][name] = {
            "first_appearance": first_appearance,
            "current_location": None,
            "current_form": None,
            "alive": True,
            "emotion_state": None,
            "key_attributes": attributes or [],
            "voice_pattern": voice_pattern,
            "last_updated_chapter": first_appearance
        }
        self.state_manager.save_state(state)

    def update_character_state(self, name: str, chapter: int = None, **kwargs):
        state = self.state_manager.load_state()
        if name not in state["characters"]:
            return
        for key, value in kwargs.items():
            if key in ["current_location", "current_form", "alive", "emotion_state"]:
                state["characters"][name][key] = value
        if chapter:
            state["characters"][name]["last_updated_chapter"] = chapter
        self.state_manager.save_state(state)

    def get_character_state(self, name: str) -> Optional[Dict[str, Any]]:
        state = self.state_manager.load_state()
        return state["characters"].get(name)

    def get_all_characters(self) -> List[str]:
        state = self.state_manager.load_state()
        return list(state["characters"].keys())
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/memory_system/test_character_tracker.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/memory_system/state/character_tracker.py tests/memory_system/test_character_tracker.py
git commit -m "feat(memory): 实现角色状态追踪"
```

---

### Task 7: 伏笔追踪

**Files:**
- Create: `novel-factory/memory_system/state/plot_thread_tracker.py`
- Create: `tests/memory_system/test_plot_thread_tracker.py`

- [ ] **Step 1: 编写测试**

```python
# tests/memory_system/test_plot_thread_tracker.py
import pytest
import tempfile
import os
from memory_system.state.plot_thread_tracker import PlotThreadTracker

def test_plant_foreshadow():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "plot_threads.yaml")
        tracker = PlotThreadTracker(state_file)
        tracker.plant_foreshadow("FP-001", introduced_chapter=5, description="神秘信号", expected_recycle="ch150-ch180")
        threads = tracker.get_all_threads()
        assert "FP-001" in threads

def test_update_foreshadow_status():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "plot_threads.yaml")
        tracker = PlotThreadTracker(state_file)
        tracker.plant_foreshadow("FP-001", introduced_chapter=5, description="神秘信号")
        tracker.update_foreshadow("FP-001", chapter=150, event_type="recycled")
        thread = tracker.get_foreshadow("FP-001")
        assert thread["status"] == "recycled"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/memory_system/test_plot_thread_tracker.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 PlotThreadTracker**

```python
# novel-factory/memory_system/state/plot_thread_tracker.py
from typing import Dict, List, Optional, Any
from .state_manager import StateManager

class PlotThreadTracker:
    def __init__(self, state_file: str):
        self.state_manager = StateManager(state_file)
        self._ensure_initial_state()

    def _ensure_initial_state(self):
        state = self.state_manager.load_state()
        if "threads" not in state:
            state["threads"] = []
            self.state_manager.save_state(state)

    def get_state(self) -> Dict:
        return self.state_manager.load_state()

    def plant_foreshadow(self, fp_id: str, introduced_chapter: int, description: str = "", expected_recycle: str = None):
        state = self.state_manager.load_state()
        thread = {
            "id": fp_id,
            "introduced_chapter": introduced_chapter,
            "status": "pending",
            "description": description,
            "key_mentions": [introduced_chapter],
            "expected_recycle": expected_recycle,
            "actual_recycle": None
        }
        existing = [t for t in state["threads"] if t["id"] == fp_id]
        if not existing:
            state["threads"].append(thread)
        self.state_manager.save_state(state)

    def update_foreshadow(self, fp_id: str, chapter: int, event_type: str):
        state = self.state_manager.load_state()
        for thread in state["threads"]:
            if thread["id"] == fp_id:
                thread["key_mentions"].append(chapter)
                if event_type == "recycled":
                    thread["status"] = "recycled"
                    thread["actual_recycle"] = chapter
                elif event_type == "invalid":
                    thread["status"] = "invalid"
        self.state_manager.save_state(state)

    def get_foreshadow(self, fp_id: str) -> Optional[Dict[str, Any]]:
        state = self.state_manager.load_state()
        for thread in state["threads"]:
            if thread["id"] == fp_id:
                return thread
        return None

    def get_all_threads(self) -> Dict[str, Dict]:
        state = self.state_manager.load_state()
        return {t["id"]: t for t in state["threads"]}

    def get_pending_threads(self) -> List[Dict]:
        state = self.state_manager.load_state()
        return [t for t in state["threads"] if t["status"] == "pending"]
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/memory_system/test_plot_thread_tracker.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/memory_system/state/plot_thread_tracker.py tests/memory_system/test_plot_thread_tracker.py
git commit -m "feat(memory): 实现伏笔追踪"
```

---

### Task 8: 时间线管理

**Files:**
- Create: `novel-factory/memory_system/state/timeline_manager.py`
- Create: `tests/memory_system/test_timeline_manager.py`

- [ ] **Step 1: 编写测试**

```python
# tests/memory_system/test_timeline_manager.py
import pytest
import tempfile
import os
from memory_system.state.timeline_manager import TimelineManager

def test_add_event():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "timeline.json")
        manager = TimelineManager(state_file)
        manager.add_event(chapter=50, time_marker="战后第3天", description="铁蛋调试信号器", participants=["铁蛋"])
        events = manager.get_events()
        assert len(events) == 1

def test_get_events_by_chapter():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "timeline.json")
        manager = TimelineManager(state_file)
        manager.add_event(chapter=50, time_marker="战后第3天", description="事件1")
        manager.add_event(chapter=51, time_marker="战后第4天", description="事件2")
        events = manager.get_events_by_chapter(50)
        assert len(events) == 1
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/memory_system/test_timeline_manager.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 TimelineManager**

```python
# novel-factory/memory_system/state/timeline_manager.py
from typing import Dict, List, Optional, Any
from .state_manager import StateManager
import uuid

class TimelineManager:
    def __init__(self, state_file: str):
        self.state_manager = StateManager(state_file)
        self._ensure_initial_state()

    def _ensure_initial_state(self):
        state = self.state_manager.load_state()
        if "events" not in state:
            state["events"] = []
            self.state_manager.save_state(state)

    def get_state(self) -> Dict:
        return self.state_manager.load_state()

    def add_event(self, chapter: int, time_marker: str, description: str, participants: Optional[List[str]] = None, location: Optional[str] = None):
        state = self.state_manager.load_state()
        event = {
            "id": f"EVT-{uuid.uuid4().hex[:8]}",
            "chapter": chapter,
            "time_marker": time_marker,
            "description": description,
            "participants": participants or [],
            "location": location
        }
        state["events"].append(event)
        self.state_manager.save_state(state)

    def get_events(self) -> List[Dict[str, Any]]:
        state = self.state_manager.load_state()
        return sorted(state["events"], key=lambda x: x["chapter"])

    def get_events_by_chapter(self, chapter: int) -> List[Dict[str, Any]]:
        return [e for e in self.get_events() if e["chapter"] == chapter]

    def get_events_by_range(self, start_chapter: int, end_chapter: int) -> List[Dict[str, Any]]:
        return [e for e in self.get_events() if start_chapter <= e["chapter"] <= end_chapter]
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/memory_system/test_timeline_manager.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/memory_system/state/timeline_manager.py tests/memory_system/test_timeline_manager.py
git commit -m "feat(memory): 实现时间线管理"
```

---

### Task 9: 事实库管理

**Files:**
- Create: `novel-factory/memory_system/state/fact_base.py`
- Create: `tests/memory_system/test_fact_base.py`

- [ ] **Step 1: 编写测试**

```python
# tests/memory_system/test_fact_base.py
import pytest
import tempfile
import os
from memory_system.state.fact_base import FactBase

def test_add_fact():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "facts.json")
        base = FactBase(state_file)
        base.add_fact("铁蛋有一台信号器", chapter=50)
        facts = base.get_all_facts()
        assert len(facts) == 1

def test_query_facts():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "facts.json")
        base = FactBase(state_file)
        base.add_fact("铁蛋有一台信号器", chapter=50)
        base.add_fact("林夜发现了敌人", chapter=51)
        facts = base.query_facts("铁蛋")
        assert len(facts) >= 1
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/memory_system/test_fact_base.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 FactBase**

```python
# novel-factory/memory_system/state/fact_base.py
from typing import Dict, List, Any
from .state_manager import StateManager

class FactBase:
    def __init__(self, state_file: str):
        self.state_manager = StateManager(state_file)
        self._ensure_initial_state()

    def _ensure_initial_state(self):
        state = self.state_manager.load_state()
        if "facts" not in state:
            state["facts"] = []
            self.state_manager.save_state(state)

    def get_state(self) -> Dict:
        return self.state_manager.load_state()

    def add_fact(self, fact_text: str, chapter: int, entity_type: str = None):
        state = self.state_manager.load_state()
        fact = {
            "text": fact_text,
            "chapter": chapter,
            "entity_type": entity_type
        }
        state["facts"].append(fact)
        self.state_manager.save_state(state)

    def get_all_facts(self) -> List[Dict[str, Any]]:
        state = self.state_manager.load_state()
        return sorted(state["facts"], key=lambda x: x["chapter"])

    def query_facts(self, keyword: str) -> List[Dict[str, Any]]:
        return [f for f in self.get_all_facts() if keyword in f["text"]]
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/memory_system/test_fact_base.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/memory_system/state/fact_base.py tests/memory_system/test_fact_base.py
git commit -m "feat(memory): 实现事实库管理"
```

---

### Task 10: 查询引擎

**Files:**
- Create: `novel-factory/memory_system/gateway/query_engine.py`
- Create: `tests/memory_system/test_query_engine.py`

- [ ] **Step 1: 编写测试**

```python
# tests/memory_system/test_query_engine.py
import pytest
from unittest.mock import Mock, patch
from memory_system.gateway.query_engine import QueryEngine

def test_query_engine_init():
    with patch('memory_system.gateway.query_engine.QdrantClientWrapper'):
        with patch('memory_system.gateway.query_engine.Embedder'):
            engine = QueryEngine()
            assert engine is not None

def test_hybrid_search_signature():
    with patch('memory_system.gateway.query_engine.QdrantClientWrapper'):
        with patch('memory_system.gateway.query_engine.Embedder'):
            engine = QueryEngine()
            assert hasattr(engine, 'hybrid_search')
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/memory_system/test_query_engine.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 QueryEngine**

```python
# novel-factory/memory_system/gateway/query_engine.py
from typing import List, Dict, Optional, Any
from ..vector.qdrant_client import QdrantClientWrapper
from ..vector.embedder import Embedder
from ..state.character_tracker import CharacterTracker
from ..state.plot_thread_tracker import PlotThreadTracker
from ..state.timeline_manager import TimelineManager

class QueryEngine:
    def __init__(
        self,
        qdrant_client: Optional[QdrantClientWrapper] = None,
        embedder: Optional[Embedder] = None,
        state_dir: str = "novel-factory/memory_system/state"
    ):
        self.qdrant = qdrant_client or QdrantClientWrapper()
        self.embedder = embedder or Embedder()
        self.character_tracker = CharacterTracker(f"{state_dir}/state_tracker.json")
        self.plot_tracker = PlotThreadTracker(f"{state_dir}/plot_threads.yaml")
        self.timeline_manager = TimelineManager(f"{state_dir}/timeline.json")

    def hybrid_search(self, query: str, collection: str = "chapters_seg", top_k: int = 5, filters: Optional[Dict] = None) -> List[Dict]:
        """混合检索：向量 + 关键词"""
        query_vector = self.embedder.embed(query)
        results = self.qdrant.search(collection, query_vector, top_k, filters)
        return [
            {
                "id": r.id,
                "score": r.score,
                "payload": r.payload
            }
            for r in results
        ]

    def get_character_state(self, character: str, before_chapter: int = None) -> Optional[Dict]:
        """获取角色状态"""
        return self.character_tracker.get_character_state(character)

    def get_all_characters(self) -> List[str]:
        """获取所有角色"""
        return self.character_tracker.get_all_characters()

    def get_plot_threads(self) -> Dict[str, Dict]:
        """获取所有伏笔"""
        return self.plot_tracker.get_all_threads()

    def get_pending_foreshadows(self) -> List[Dict]:
        """获取待回收伏笔"""
        return self.plot_tracker.get_pending_threads()

    def get_timeline_events(self, start_chapter: int = None, end_chapter: int = None) -> List[Dict]:
        """获取时间线事件"""
        if start_chapter and end_chapter:
            return self.timeline_manager.get_events_by_range(start_chapter, end_chapter)
        return self.timeline_manager.get_events()
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/memory_system/test_query_engine.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/memory_system/gateway/query_engine.py tests/memory_system/test_query_engine.py
git commit -m "feat(memory): 实现查询引擎"
```

---

### Task 11: 自动推送引擎

**Files:**
- Create: `novel-factory/memory_system/gateway/push_engine.py`
- Create: `tests/memory_system/test_push_engine.py`

- [ ] **Step 1: 编写测试**

```python
# tests/memory_system/test_push_engine.py
import pytest
from unittest.mock import Mock, patch
from memory_system.gateway.push_engine import PushEngine

def test_push_engine_init():
    with patch('memory_system.gateway.push_engine.QueryEngine'):
        engine = PushEngine()
        assert engine is not None

def test_build_chapter_context():
    with patch('memory_system.gateway.push_engine.QueryEngine') as MockQE:
        mock_qe = Mock()
        mock_qe.get_character_state.return_value = {"name": "铁蛋", "alive": True}
        MockQE.return_value = mock_qe
        engine = PushEngine()
        context = engine.build_chapter_context(50)
        assert isinstance(context, dict)
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/memory_system/test_push_engine.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 PushEngine**

```python
# novel-factory/memory_system/gateway/push_engine.py
from typing import Dict, List, Optional, Any
from .query_engine import QueryEngine

class PushEngine:
    def __init__(self, query_engine: Optional[QueryEngine] = None):
        self.query_engine = query_engine or QueryEngine()

    def build_chapter_context(self, chapter_num: int) -> Dict[str, Any]:
        """构建新章节上下文"""
        # 获取角色状态摘要
        characters = self.query_engine.get_all_characters()
        character_states = {}
        for char in characters:
            state = self.query_engine.get_character_state(char)
            if state:
                character_states[char] = state

        # 获取待回收伏笔
        pending_foreshadows = self.query_engine.get_pending_foreshadows()

        # 获取时间线摘要
        recent_events = self.query_engine.get_timeline_events(
            start_chapter=max(1, chapter_num - 20),
            end_chapter=chapter_num - 1
        )

        return {
            "chapter": chapter_num,
            "character_states": character_states,
            "pending_foreshadows": pending_foreshadows,
            "recent_events": recent_events[-5:] if recent_events else [],
            "relevant_history": self._get_relevant_history(chapter_num)
        }

    def _get_relevant_history(self, chapter_num: int, top_k: int = 3) -> List[Dict]:
        """获取相关历史片段"""
        try:
            results = self.query_engine.hybrid_search(
                f"第{chapter_num}章相关",
                top_k=top_k
            )
            return results
        except:
            return []

    def auto_push(self, chapter_num: int) -> Dict[str, Any]:
        """自动推送上下文（主入口）"""
        return self.build_chapter_context(chapter_num)
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/memory_system/test_push_engine.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/memory_system/gateway/push_engine.py tests/memory_system/test_push_engine.py
git commit -m "feat(memory): 实现自动推送引擎"
```

---

### Task 12: MemoryGateway 统一入口

**Files:**
- Create: `novel-factory/memory_system/gateway/memory_gateway.py`
- Create: `tests/memory_system/test_memory_gateway.py`

- [ ] **Step 1: 编写测试**

```python
# tests/memory_system/test_memory_gateway.py
import pytest
from unittest.mock import Mock, patch

def test_memory_gateway_init():
    with patch('memory_system.gateway.memory_gateway.QdrantClientWrapper'):
        with patch('memory_system.gateway.memory_gateway.Embedder'):
            from memory_system.gateway.memory_gateway import MemoryGateway
            gateway = MemoryGateway()
            assert gateway is not None

def test_auto_push_context():
    with patch('memory_system.gateway.memory_gateway.PushEngine') as MockPE:
        mock_pe = Mock()
        mock_pe.auto_push.return_value = {"chapter": 50, "character_states": {}}
        MockPE.return_value = mock_pe
        from memory_system.gateway.memory_gateway import MemoryGateway
        gateway = MemoryGateway()
        context = gateway.auto_push_context(50)
        assert context["chapter"] == 50
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/memory_system/test_memory_gateway.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 MemoryGateway**

```python
# novel-factory/memory_system/gateway/memory_gateway.py
from typing import Dict, List, Optional, Any
from .query_engine import QueryEngine
from .push_engine import PushEngine
from ..state.character_tracker import CharacterTracker
from ..state.plot_thread_tracker import PlotThreadTracker

class MemoryGateway:
    """记忆系统统一入口"""

    def __init__(
        self,
        state_dir: str = "novel-factory/memory_system/state",
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333
    ):
        from ..vector.qdrant_client import QdrantClientWrapper
        from ..vector.embedder import Embedder

        qdrant_client = QdrantClientWrapper(host=qdrant_host, port=qdrant_port)
        embedder = Embedder()

        self.query_engine = QueryEngine(qdrant_client, embedder, state_dir)
        self.push_engine = PushEngine(self.query_engine)

        self.character_tracker = CharacterTracker(f"{state_dir}/state_tracker.json")
        self.plot_tracker = PlotThreadTracker(f"{state_dir}/plot_threads.yaml")

    def auto_push_context(self, chapter_num: int) -> Dict[str, Any]:
        """
        自动推送上下文（作家写新章节时调用）
        """
        return self.push_engine.auto_push(chapter_num)

    def query(self, query: str, scope: str = "all") -> Dict[str, Any]:
        """
        主动查询
        """
        results = self.query_engine.hybrid_search(query)
        return {
            "query": query,
            "results": results
        }

    def update_character_state(self, character: str, chapter: int = None, **kwargs):
        """更新角色状态"""
        self.character_tracker.update_character_state(character, chapter, **kwargs)

    def register_character(self, name: str, first_appearance: int, **kwargs):
        """注册角色"""
        self.character_tracker.register_character(name, first_appearance, **kwargs)

    def plant_foreshadow(self, fp_id: str, introduced_chapter: int, **kwargs):
        """登记伏笔"""
        self.plot_tracker.plant_foreshadow(fp_id, introduced_chapter, **kwargs)

    def update_foreshadow(self, fp_id: str, chapter: int, event_type: str):
        """更新伏笔状态"""
        self.plot_tracker.update_foreshadow(fp_id, chapter, event_type)

    def get_character_state(self, character: str) -> Optional[Dict]:
        """获取角色状态"""
        return self.query_engine.get_character_state(character)

    def check_consistency(self, chapter_content: str) -> List[Dict]:
        """一致性检查（简化版，实际对接ConsistencyEngine）"""
        # 后续与一致性系统集成
        return []
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/memory_system/test_memory_gateway.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/memory_system/gateway/memory_gateway.py tests/memory_system/test_memory_gateway.py
git commit -m "feat(memory): 实现MemoryGateway统一入口"
```

---

### Task 13: 批量嵌入脚本

**Files:**
- Create: `novel-factory/memory_system/scripts/embed_chapters.py`
- Test: `tests/memory_system/test_embed_chapters.py`

- [ ] **Step 1: 编写脚本框架**

```python
# novel-factory/memory_system/scripts/embed_chapters.py
#!/usr/bin/env python3
"""
批量嵌入现有章节到向量存储

用法:
    python -m memory_system.scripts.embed_chapters --chapters 1-360
    python -m memory_system.scripts.embed_chapters --chapters 50-100
"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from memory_system.vector.qdrant_client import QdrantClientWrapper
from memory_system.vector.embedder import Embedder
from memory_system.vector.collections import CollectionManager

def get_chapter_content(chapter_num: int) -> str:
    """从文件系统读取章节内容"""
    # TODO: 实现从现有章节文件读取
    chapter_file = Path(f"novel-factory/02_作家工作室/第{chapter_num}章.txt")
    if chapter_file.exists():
        return chapter_file.read_text(encoding='utf-8')
    return ""

def embed_chapters(start: int, end: int, collection_name: str = "chapters_seg"):
    """批量嵌入章节"""
    client = QdrantClientWrapper()
    embedder = Embedder()
    manager = CollectionManager(client)

    print(f"开始嵌入章节 {start}-{end}...")

    for chapter in range(start, end + 1):
        content = get_chapter_content(chapter)
        if not content:
            print(f"  [跳过] 章节 {chapter} 无内容")
            continue

        # 分段处理（每1000字符为一段）
        segment_size = 1000
        segments = [content[i:i+segment_size] for i in range(0, len(content), segment_size)]

        for seg_idx, segment in enumerate(segments):
            if len(segment.strip()) < 50:
                continue

            vector = embedder.embed(segment)
            point = {
                "id": f"ch{chapter:03d}_seg{seg_idx:03d}",
                "vector": vector,
                "payload": {
                    "chapter": chapter,
                    "segment_text": segment[:200],  # 保留前200字符用于展示
                    "segment_index": seg_idx
                }
            }
            client.upsert(collection_name, [point])

        print(f"  [完成] 章节 {chapter}: {len(segments)} 片段")

    print(f"嵌入完成: {end - start + 1} 章")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="批量嵌入章节")
    parser.add_argument("--chapters", type=str, default="1-360", help="章节范围，如 1-360")
    args = parser.parse_args()

    start, end = map(int, args.chapters.split('-'))
    embed_chapters(start, end)
```

- [ ] **Step 2: 提交**

```bash
git add novel-factory/memory_system/scripts/embed_chapters.py
git commit -m "feat(memory): 添加批量嵌入脚本"
```

---

### Task 14: 初始化脚本

**Files:**
- Create: `novel-factory/memory_system/scripts/init_memory.py`

- [ ] **Step 1: 编写初始化脚本**

```python
# novel-factory/memory_system/scripts/init_memory.py
#!/usr/bin/env python3
"""
初始化记忆系统

用法:
    python -m memory_system.scripts.init_memory --mode full
    python -m memory_system.scripts.init_memory --mode quick
"""

import argparse
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from memory_system.vector.qdrant_client import QdrantClientWrapper
from memory_system.vector.collections import CollectionManager
from memory_system.state.character_tracker import CharacterTracker
from memory_system.state.plot_thread_tracker import PlotThreadTracker
from memory_system.state.timeline_manager import TimelineManager
from memory_system.state.fact_base import FactBase

def init_collections():
    """初始化Qdrant集合"""
    print("初始化Qdrant集合...")
    client = QdrantClientWrapper()
    manager = CollectionManager(client)
    manager.init_collections()
    print("  [完成] 集合初始化")

def init_state_files():
    """初始化状态文件"""
    print("初始化状态文件...")
    state_dir = Path("novel-factory/memory_system/state")
    state_dir.mkdir(parents=True, exist_ok=True)

    # 初始化角色追踪
    tracker = CharacterTracker(str(state_dir / "state_tracker.json"))
    print("  [完成] state_tracker.json")

    # 初始化伏笔追踪
    plot_tracker = PlotThreadTracker(str(state_dir / "plot_threads.yaml"))
    print("  [完成] plot_threads.yaml")

    # 初始化时间线
    timeline = TimelineManager(str(state_dir / "timeline.json"))
    print("  [完成] timeline.json")

    # 初始化事实库
    fact_base = FactBase(str(state_dir / "facts.json"))
    print("  [完成] facts.json")

def main():
    parser = argparse.ArgumentParser(description="初始化记忆系统")
    parser.add_argument("--mode", choices=["full", "quick"], default="full",
                        help="full: 完整初始化(含集合); quick: 仅状态文件")
    args = parser.parse_args()

    print("=" * 50)
    print("记忆系统初始化")
    print("=" * 50)

    if args.mode == "full":
        init_collections()

    init_state_files()

    print("=" * 50)
    print("初始化完成!")
    print("=" * 50)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 提交**

```bash
git add novel-factory/memory_system/scripts/init_memory.py
git commit -m "feat(memory): 添加初始化脚本"
```

---

### Task 15: 上下文查询脚本

**Files:**
- Create: `novel-factory/memory_system/scripts/query_context.py`

- [ ] **Step 1: 编写查询脚本**

```python
# novel-factory/memory_system/scripts/query_context.py
#!/usr/bin/env python3
"""
查询上下文

用法:
    python -m memory_system.scripts.query_context --character 铁蛋
    python -m memory_system.scripts.query_context --query "灰巢废墟"
    python -m memory_system.scripts.query_context --foreshadow
"""

import argparse
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from memory_system.gateway.memory_gateway import MemoryGateway

def main():
    parser = argparse.ArgumentParser(description="查询上下文")
    parser.add_argument("--character", type=str, help="查询角色状态")
    parser.add_argument("--query", type=str, help="语义查询")
    parser.add_argument("--foreshadow", action="store_true", help="查看待回收伏笔")
    args = parser.parse_args()

    gateway = MemoryGateway()

    if args.character:
        state = gateway.get_character_state(args.character)
        if state:
            print(f"角色: {args.character}")
            for k, v in state.items():
                print(f"  {k}: {v}")
        else:
            print(f"未找到角色: {args.character}")

    elif args.query:
        results = gateway.query(args.query)
        print(f"查询: {args.query}")
        print(f"结果数: {len(results.get('results', []))}")
        for r in results.get('results', [])[:5]:
            print(f"  - [{r['score']:.3f}] {r['payload'].get('segment_text', '')[:100]}...")

    elif args.foreshadow:
        pending = gateway.query_engine.get_pending_foreshadows()
        print(f"待回收伏笔 ({len(pending)} 个):")
        for f in pending:
            print(f"  - {f['id']}: {f.get('description', 'N/A')}")
            print(f"    引入于: 第{f['introduced_chapter']}章")
            print(f"    预期回收: {f.get('expected_recycle', 'N/A')}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 提交**

```bash
git add novel-factory/memory_system/scripts/query_context.py
git commit -m "feat(memory): 添加上下文查询脚本"
```

---

## 自检清单

- [ ] 所有文件路径是否存在且正确
- [ ] 所有类和方法是否有对应测试
- [ ] 测试是否使用 TDD 模式（先写测试）
- [ ] 提交消息是否符合规范 (feat: ...)
- [ ] 是否覆盖 spec 中的所有需求

---

## 执行选项

**Plan complete and saved to `docs/superpowers/plans/2026-05-19-memory-system-implementation-plan.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**