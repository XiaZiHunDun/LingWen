# RAG支持系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立RAG（检索增强生成）支持系统，通过向量数据库存储已生成内容，生成时检索相关内容作为参考，解决上下文一致性问题

**Architecture:** 采用分层架构，包括内容分块、向量存储、检索接口、上下文注入，通过AI服务抽象层集成

**Tech Stack:** Python + Qdrant（向量数据库）+ sentence-transformers（Embedding）

---

## 文件结构

```
novel-factory/
├── rag_system/
│   ├── __init__.py
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── query_builder.py          # 查询构建器
│   │   ├── vector_search.py          # 向量检索
│   │   ├── reranker.py               # 重排序
│   │   └── context_assembler.py      # 上下文组装
│   ├── indexing/
│   │   ├── __init__.py
│   │   ├── chunker.py                # 内容分块
│   │   ├── embedder.py               # Embedding生成
│   │   └── indexer.py                # 索引管理
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── vector_store.py           # 向量存储
│   │   └── metadata_store.py         # 元数据存储
│   ├── config/
│   │   ├── rag_config.yaml           # RAG配置
│   │   └── embedding_config.yaml     # Embedding配置
│   └── integration/
│       ├── __init__.py
│       └── ai_gateway_integration.py  # 与AI网关集成
└── config/
    └── vector_db.yaml                # 向量数据库配置
```

---

### Task 1: 创建配置和向量存储基础

**Files:**
- Create: `novel-factory/rag_system/config/rag_config.yaml`
- Create: `novel-factory/rag_system/config/embedding_config.yaml`
- Create: `novel-factory/config/vector_db.yaml`

- [ ] **Step 1: 创建RAG配置文件**

```yaml
# rag_system/config/rag_config.yaml

# RAG系统配置
# 最后更新：2026-05-19

# 向量数据库配置
vector_db:
  provider: qdrant
  host: localhost
  port: 6333
  grpc_port: 6334
  collection_prefix: novel_factory_

# 集合配置
collections:
  character_context:
    name: character_context
    vector_size: 384
    description: 角色上下文库

  world_context:
    name: world_context
    vector_size: 384
    description: 世界观上下文库

  foreshadowing:
    name: foreshadowing
    vector_size: 384
    description: 伏笔库

  chapter_context:
    name: chapter_context
    vector_size: 384
    description: 章节上下文库

# 检索配置
retrieval:
  default_limit: 5
  max_context_tokens: 4000
  rerank_top_k: 3

# 分块配置
chunking:
  max_chunk_size: 1000
  overlap_size: 100
  scene_boundary_priority: true
```

```yaml
# rag_system/config/embedding_config.yaml

# Embedding模型配置

model:
  provider: sentence-transformers
  model_name: paraphrase-multilingual-MiniLM-L12-v2
  device: cpu
  batch_size: 32

# 如果使用OpenAI
# model:
#   provider: openai
#   model_name: text-embedding-3-small
#   api_key: ${OPENAI_API_KEY}
```

```yaml
# config/vector_db.yaml

# 向量数据库总配置
# 最后更新：2026-05-19

qdrant:
  host: localhost
  port: 6333
  timeout: 5
  retry_attempts: 3

collections:
  character_context:
    vector_size: 384
    distance: Cosine

  world_context:
    vector_size: 384
    distance: Cosine

  foreshadowing:
    vector_size: 384
    distance: Cosine

  chapter_context:
    vector_size: 384
    distance: Cosine
```

- [ ] **Step 2: 提交配置文件**

```bash
git add rag_system/config/rag_config.yaml rag_system/config/embedding_config.yaml config/vector_db.yaml
git commit -m "feat(rag): 添加RAG配置文件"
```

---

### Task 2: 实现内容分块器

**Files:**
- Create: `novel-factory/rag_system/indexing/chunker.py`
- Create: `novel-factory/tests/test_chunker.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_chunker.py

import pytest
from rag_system.indexing.chunker import NovelChunker, Chunk, ChunkMetadata

def test_chunker_initialization():
    """测试分块器初始化"""
    chunker = NovelChunker()
    assert chunker.max_chunk_size == 1000
    assert chunker.overlap_size == 100

def test_simple_chunking():
    """测试简单分块"""
    chunker = NovelChunker()

    text = "这是第一段内容。" * 100 + "\n\n" + "这是第二段内容。" * 100
    chunks = chunker.chunk_text(text)

    assert len(chunks) >= 1

def test_chunk_metadata():
    """测试分块元数据"""
    metadata = ChunkMetadata(
        chapter="ch001",
        scene_id="scene_1",
        sub_index=0,
        start_pos=0,
        char_count=100,
        tags=["林夜", "战斗"]
    )

    assert metadata.chapter == "ch001"
    assert metadata.tags == ["林夜", "战斗"]
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory && python -m pytest tests/test_chunker.py -v`
Expected: FAIL with "cannot import"

- [ ] **Step 3: 实现内容分块器**

```python
# rag_system/indexing/chunker.py

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class ChunkMetadata:
    """分块元数据"""
    chapter: str
    scene_id: Optional[str]
    sub_index: int
    start_pos: int
    char_count: int
    tags: List[str]

@dataclass
class Chunk:
    """内容块"""
    content: str
    metadata: ChunkMetadata
    chunk_id: str

class NovelChunker:
    """小说内容分块器"""

    def __init__(
        self,
        max_chunk_size: int = 1000,
        overlap_size: int = 100
    ):
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size

    def chunk_text(
        self,
        text: str,
        chapter: str = "unknown",
        scene_id: Optional[str] = None
    ) -> List[Chunk]:
        """
        将文本分割为块

        Args:
            text: 待分割文本
            chapter: 章节号
            scene_id: 场景ID

        Returns:
            List[Chunk]: 分块列表
        """
        chunks = []

        # 按场景分割
        scenes = self._split_by_scenes(text)

        for i, scene in enumerate(scenes):
            scene_id = f"{chapter}_scene_{i}" if scene_id is None else f"{scene_id}_{i}"

            # 如果场景过大，进一步分割
            if len(scene) > self.max_chunk_size:
                sub_chunks = self._split_large_chunk(scene)
                for j, sub_content in enumerate(sub_chunks):
                    chunk = self._create_chunk(
                        content=sub_content,
                        chapter=chapter,
                        scene_id=scene_id,
                        sub_index=j,
                        start_pos=self._get_start_pos(scenes, i, j)
                    )
                    chunks.append(chunk)
            else:
                chunk = self._create_chunk(
                    content=scene,
                    chapter=chapter,
                    scene_id=scene_id,
                    sub_index=0,
                    start_pos=self._get_start_pos(scenes, i, 0)
                )
                chunks.append(chunk)

        return chunks

    def _split_by_scenes(self, text: str) -> List[str]:
        """按场景分割"""
        # 使用空行分割
        paragraphs = text.split('\n\n')
        scenes = []
        current_scene = []

        for para in paragraphs:
            if len(para.strip()) < 50:
                # 短段落可能是场景过渡
                if current_scene:
                    scenes.append('\n\n'.join(current_scene))
                    current_scene = []
            else:
                current_scene.append(para)

        if current_scene:
            scenes.append('\n\n'.join(current_scene))

        return scenes if scenes else [text]

    def _split_large_chunk(self, text: str) -> List[str]:
        """分割大块文本"""
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.max_chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - self.overlap_size

        return chunks

    def _create_chunk(
        self,
        content: str,
        chapter: str,
        scene_id: str,
        sub_index: int,
        start_pos: int
    ) -> Chunk:
        """创建块"""
        metadata = ChunkMetadata(
            chapter=chapter,
            scene_id=scene_id,
            sub_index=sub_index,
            start_pos=start_pos,
            char_count=len(content),
            tags=self._extract_tags(content)
        )

        chunk_id = f"{chapter}_{scene_id}_{sub_index}"

        return Chunk(
            content=content,
            metadata=metadata,
            chunk_id=chunk_id
        )

    def _extract_tags(self, content: str) -> List[str]:
        """提取标签（角色名等）"""
        tags = []

        # 已知角色名
        known_characters = ['林夜', '苏琳', '暗皇']

        for char in known_characters:
            if char in content:
                tags.append(char)

        # 简单关键词提取
        keywords = ['战斗', '对话', '回忆', '场景']
        for kw in keywords:
            if kw in content:
                tags.append(kw)

        return tags

    def _get_start_pos(self, scenes: List[str], scene_idx: int, sub_idx: int) -> int:
        """计算起始位置"""
        pos = 0
        for i in range(scene_idx):
            pos += len(scenes[i])
        return pos + sub_idx * self.overlap_size
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/test_chunker.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
mkdir -p rag_system/indexing
git add rag_system/indexing/chunker.py rag_system/__init__.py rag_system/indexing/__init__.py tests/test_chunker.py
git commit -m "feat(rag): 实现内容分块器"
```

---

### Task 3: 实现向量存储

**Files:**
- Create: `novel-factory/rag_system/storage/vector_store.py`

- [ ] **Step 1: 创建向量存储接口（简化版，无需实际Qdrant）**

```python
# rag_system/storage/vector_store.py

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np

@dataclass
class SearchResult:
    """检索结果"""
    chunk_id: str
    content: str
    score: float
    metadata: Dict[str, Any]

class VectorStore:
    """向量存储管理器（简化版）"""

    def __init__(self, collection_name: str, vector_size: int = 384):
        self.collection_name = collection_name
        self.vector_size = vector_size
        self._vectors: Dict[str, np.ndarray] = {}
        self._payloads: Dict[str, Dict] = {}

    async def upsert(
        self,
        chunk_id: str,
        vector: np.ndarray,
        payload: Dict[str, Any]
    ) -> bool:
        """存储向量"""
        if len(vector) != self.vector_size:
            raise ValueError(f"Vector size must be {self.vector_size}")

        self._vectors[chunk_id] = vector
        self._payloads[chunk_id] = payload
        return True

    async def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """搜索相似向量"""
        if not self._vectors:
            return []

        # 计算余弦相似度
        results = []
        for chunk_id, stored_vector in self._vectors.items():
            # 简化：使用负距离作为分数
            similarity = self._cosine_similarity(query_vector, stored_vector)

            # 应用过滤器（简化）
            if filters:
                payload = self._payloads.get(chunk_id, {})
                if not self._passes_filters(payload, filters):
                    continue

            results.append(SearchResult(
                chunk_id=chunk_id,
                content=payload.get('content', ''),
                score=similarity,
                metadata=payload
            ))

        # 排序并返回top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def _passes_filters(
        self,
        payload: Dict,
        filters: Dict
    ) -> bool:
        """检查是否通过过滤器"""
        for key, value in filters.items():
            if payload.get(key) != value:
                return False
        return True

    async def delete(self, chunk_id: str) -> bool:
        """删除向量"""
        if chunk_id in self._vectors:
            del self._vectors[chunk_id]
            del self._payloads[chunk_id]
            return True
        return False

    async def count(self) -> int:
        """统计向量数量"""
        return len(self._vectors)
```

- [ ] **Step 2: 提交**

```bash
git add rag_system/storage/__init__.py rag_system/storage/vector_store.py
git commit -m "feat(rag): 实现向量存储"
```

---

### Task 4: 实现检索流程

**Files:**
- Create: `novel-factory/rag_system/retrieval/query_builder.py`
- Create: `novel-factory/rag_system/retrieval/context_assembler.py`

- [ ] **Step 1: 创建查询构建器**

```python
# rag_system/retrieval/query_builder.py

from dataclasses import dataclass
from typing import Dict, Any, List, Optional

@dataclass
class QueryCondition:
    """查询条件"""
    type: str
    value: str
    weight: float

@dataclass
class RetrievalQuery:
    """检索查询"""
    conditions: List[QueryCondition]
    chapter: Optional[str] = None
    character: Optional[str] = None
    context: Optional[str] = None

class QueryBuilder:
    """查询构建器"""

    def build_from_request(
        self,
        request: Dict[str, Any]
    ) -> RetrievalQuery:
        """
        从生成请求构建查询

        例如：
        请求：{"chapter": "ch200", "character": "林夜", "context": "新场景进入"}
        ->
        Query:
          - chapter: ch200
          - character: 林夜
          - context: 新场景进入
        """
        query = RetrievalQuery(conditions=[])

        # 提取角色
        if request.get('character'):
            query.character = request['character']
            query.conditions.append(QueryCondition(
                type='character',
                value=request['character'],
                weight=1.0
            ))

        # 提取章节
        if request.get('chapter'):
            query.chapter = request['chapter']
            query.conditions.append(QueryCondition(
                type='chapter',
                value=request['chapter'],
                weight=0.8
            ))

        # 提取上下文
        if request.get('context'):
            query.context = request['context']
            query.conditions.append(QueryCondition(
                type='context',
                value=request['context'],
                weight=0.7
            ))

        return query

    def add_chapter_range(
        self,
        query: RetrievalQuery,
        current_chapter: str,
        range_size: int = 5
    ) -> RetrievalQuery:
        """添加相关章节范围"""
        # 提取章节号
        import re
        match = re.search(r'ch(\d+)', current_chapter)
        if match:
            ch_num = int(match.group(1))
            start = max(1, ch_num - range_size)
            end = ch_num + range_size

            query.conditions.append(QueryCondition(
                type='chapter_range',
                value=f"ch{start}-ch{end}",
                weight=0.6
            ))

        return query
```

- [ ] **Step 2: 创建上下文组装器**

```python
# rag_system/retrieval/context_assembler.py

from typing import List, Dict, Any
from .vector_store import SearchResult

class ContextAssembler:
    """上下文组装器"""

    def __init__(self, max_context_tokens: int = 4000):
        self.max_context_tokens = max_context_tokens

    def assemble(
        self,
        original_prompt: str,
        retrieved_results: List[SearchResult]
    ) -> str:
        """
        组装检索结果到提示词

        格式：
        [相关上下文]
        ---
        [原始请求]
        """
        if not retrieved_results:
            return original_prompt

        # 按相关性排序
        sorted_results = sorted(
            retrieved_results,
            key=lambda x: x.score,
            reverse=True
        )

        # 选择高相关性结果
        selected = []
        total_tokens = self._estimate_tokens(original_prompt)

        for result in sorted_results:
            result_tokens = self._estimate_tokens(result.content)
            if total_tokens + result_tokens <= self.max_context_tokens:
                selected.append(result)
                total_tokens += result_tokens

        # 组装上下文
        context_parts = []

        if selected:
            context_parts.append("【相关上下文】")
            for i, r in enumerate(selected):
                context_parts.append(
                    f"\n--- 参考{i+1} (相关度:{r.score:.2f}) ---\n"
                    f"{r.content}"
                )
            context_parts.append("\n--- END ---\n")

        context_parts.append("【原始请求】\n" + original_prompt)

        return '\n'.join(context_parts)

    def _estimate_tokens(self, text: str) -> int:
        """估算token数（中文约2字/token）"""
        return len(text) // 2
```

- [ ] **Step 3: 提交**

```bash
git add rag_system/retrieval/__init__.py rag_system/retrieval/query_builder.py rag_system/retrieval/context_assembler.py
git commit -m "feat(rag): 实现检索流程"
```

---

### Task 5: 实现与AI网关集成

**Files:**
- Create: `novel-factory/rag_system/integration/ai_gateway_integration.py`

- [ ] **Step 1: 创建RAG集成**

```python
# rag_system/integration/ai_gateway_integration.py

from typing import Dict, Any, Optional, List
import numpy as np

from ..retrieval.query_builder import QueryBuilder, RetrievalQuery
from ..retrieval.context_assembler import ContextAssembler
from ..storage.vector_store import VectorStore, SearchResult
from ..indexing.chunker import NovelChunker

class RAGIntegration:
    """RAG与AI网关集成"""

    def __init__(
        self,
        vector_store: VectorStore,
        query_builder: QueryBuilder,
        context_assembler: ContextAssembler,
        chunker: Optional[NovelChunker] = None
    ):
        self.vector_store = vector_store
        self.query_builder = query_builder
        self.context_assembler = context_assembler
        self.chunker = chunker or NovelChunker()

    async def generate_with_rag(
        self,
        request: Dict[str, Any],
        generate_func
    ) -> str:
        """
        使用RAG增强的生成

        Args:
            request: 生成请求，包含chapter、character、context等
            generate_func: 实际的生成函数

        Returns:
            str: 生成的文本
        """
        # 1. 构建查询
        query = self.query_builder.build_from_request(request)

        # 2. 添加章节范围
        if query.chapter:
            query = self.query_builder.add_chapter_range(
                query,
                query.chapter,
                range_size=5
            )

        # 3. 模拟向量检索（实际需要embedding）
        # 这里使用简化实现
        mock_vector = np.random.randn(384)
        search_results = await self.vector_store.search(
            query_vector=mock_vector,
            top_k=5,
            filters={'chapter': query.chapter} if query.chapter else None
        )

        # 4. 提取检索内容
        retrieved_texts = [r.content for r in search_results]

        # 5. 组装增强提示词
        original_prompt = request.get('prompt', '')
        enhanced_prompt = self.context_assembler.assemble(
            original_prompt=original_prompt,
            retrieved_results=search_results
        )

        # 6. 调用生成函数
        # 实际实现中，这里会调用AI网关的generate方法
        # response = await ai_gateway.generate(prompt=enhanced_prompt, ...)

        return enhanced_prompt  # 简化返回增强后的提示词

    async def index_chapter(
        self,
        chapter: str,
        content: str,
        embed_func
    ) -> int:
        """
        索引章节内容

        Args:
            chapter: 章节号
            content: 章节内容
            embed_func: embedding函数

        Returns:
            int: 索引的块数量
        """
        # 1. 分块
        chunks = self.chunker.chunk_text(content, chapter=chapter)

        # 2. 为每个块生成向量并存储
        indexed_count = 0
        for chunk in chunks:
            # 生成embedding
            vector = await embed_func(chunk.content)

            # 存储
            await self.vector_store.upsert(
                chunk_id=chunk.chunk_id,
                vector=vector,
                payload={
                    'content': chunk.content,
                    'chapter': chunk.metadata.chapter,
                    'scene_id': chunk.metadata.scene_id,
                    'tags': chunk.metadata.tags
                }
            )
            indexed_count += 1

        return indexed_count
```

- [ ] **Step 2: 提交**

```bash
git add rag_system/integration/__init__.py rag_system/integration/ai_gateway_integration.py
git commit -m "feat(rag): 实现AI网关集成"
```

---

## 实现完成检查

- [ ] 配置文件已创建
- [ ] 内容分块器已实现
- [ ] 向量存储已实现
- [ ] 查询构建器已实现
- [ ] 上下文组装器已实现
- [ ] AI网关集成已实现
- [ ] 测试通过