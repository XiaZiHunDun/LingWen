# Phase 2 性能优化实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended)

**Goal:** 提升检测性能，通过缓存+预编译+误报过滤减少无效计算

**Architecture:**
- `PatternRegistry` 单例管理所有预编译正则表达式
- `CheckerCache` 基于内容hash的检测结果缓存
- `FalsePositiveFilter` 集成 ProblemClassifier 过滤误报

**Tech Stack:** Python 3.13, dataclasses, hashlib, re

---

## 文件结构

```
novel-factory/
├── infra/
│   ├── patterns.py              # PatternRegistry 单例 (NEW)
│   ├── cache.py                  # CheckerCache 缓存 (NEW)
│   ├── filter.py                 # FalsePositiveFilter (NEW)
│   └── consistency/
│       └── checkers/
│           ├── sentence_diversity_checker.py  # 修改: 使用PatternRegistry
│           └── character_checker.py          # 修改: 使用PatternRegistry
└── tools/
    └── llm_quality_deep_check.py            # 修改: 集成缓存和过滤
```

---

## Task 1: 创建 PatternRegistry 单例

**Files:**
- Create: `infra/patterns.py`
- Test: `tests/test_patterns.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_patterns.py
import pytest
from infra.patterns import PatternRegistry

def test_singleton():
    r1 = PatternRegistry.get()
    r2 = PatternRegistry.get()
    assert r1 is r2  # Same instance

def test_get_pattern():
    registry = PatternRegistry.get()
    # Should have pre-compiled patterns
    assert 'dialog' in registry.list_patterns()

def test_pattern_is_compiled():
    registry = PatternRegistry.get()
    pattern = registry.get('dialog')
    assert hasattr(pattern, 'match')  # It's a compiled pattern

def test_list_patterns():
    registry = PatternRegistry.get()
    patterns = registry.list_patterns()
    assert len(patterns) > 0
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_patterns.py -v`
Expected: FAIL - module not found

- [ ] **Step 3: 创建 patterns.py**

```python
# infra/patterns.py
import re
from typing import Dict, Pattern, List, Optional


class PatternRegistry:
    """
    全局正则表达式模式注册表（单例）

    在模块加载时预编译所有模式，避免重复编译开销
    """

    _instance: Optional["PatternRegistry"] = None
    _patterns: Dict[str, Pattern] = {}

    # 句子多样性模式
    _SENTENCE_PATTERNS = {
        'dialog': (r'「[^」]+」', 'dialog', '对话句'),
        'dialog_english': (r'"[^"]+"', 'dialog_english', '对话句(英文)'),
        'narrate_he': (r'他[说问道喊叫笑叹谓称著显示露出透露出冒][^「"。，！？]*[。！？]?', 'narrate_he', '他述句'),
        # ... more patterns
    }

    # AI痕迹模式
    _AI_TRACE_PATTERNS = {
        'template_first': (r'首先', 'ai_trace', 'AI模板词'),
        'template_second': (r'其次', 'ai_trace', 'AI模板词'),
        # ... more patterns
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._compile_all()
        return cls._instance

    @classmethod
    def get(cls) -> "PatternRegistry":
        """获取单例实例"""
        return cls()

    def _compile_all(self):
        """编译所有模式"""
        # 编译句子多样性模式
        for name, (pattern, _, _) in self._SENTENCE_PATTERNS.items():
            try:
                self._patterns[name] = re.compile(pattern)
            except re.error:
                pass  # Skip invalid patterns

        # 编译AI痕迹模式
        for name, (pattern, _, _) in self._AI_TRACE_PATTERNS.items():
            try:
                self._patterns[name] = re.compile(pattern)
            except re.error:
                pass

    def get(self, name: str) -> Optional[Pattern]:
        """获取编译后的模式"""
        return self._patterns.get(name)

    def list_patterns(self) -> List[str]:
        """列出所有模式名称"""
        return list(self._patterns.keys())

    def get_pattern_info(self, name: str) -> Optional[tuple]:
        """获取模式信息 (pattern, type, description)"""
        if name in self._SENTENCE_PATTERNS:
            return self._SENTENCE_PATTERNS[name]
        if name in self._AI_TRACE_PATTERNS:
            return self._AI_TRACE_PATTERNS[name]
        return None
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_patterns.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add tests/test_patterns.py infra/patterns.py
git commit -m "feat(patterns): add PatternRegistry for pre-compiled regex"
```

---

## Task 2: 创建 CheckerCache 结果缓存

**Files:**
- Create: `infra/cache.py`
- Test: `tests/test_cache.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_cache.py
import pytest
import hashlib
from infra.cache import CheckerCache

def test_cache_set_and_get():
    cache = CheckerCache()
    content = "测试内容"
    result = {"issues": [], "score": 0.9}

    cache.set("test_checker", 1, content, result)
    cached = cache.get("test_checker", 1, content)

    assert cached is not None
    assert cached["score"] == 0.9

def test_cache_miss_on_content_change():
    cache = CheckerCache()
    result = {"issues": [], "score": 0.9}

    cache.set("test_checker", 1, "旧内容", result)
    cached = cache.get("test_checker", 1, "新内容")

    assert cached is None  # Content changed, cache miss

def test_cache_expiry():
    cache = CheckerCache()
    result = {"issues": [], "score": 0.9}

    cache.set("test_checker", 1, "内容", result, ttl_seconds=0)  # Immediate expiry
    cached = cache.get("test_checker", 1, "内容")

    assert cached is None  # Expired
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_cache.py -v`
Expected: FAIL - module not found

- [ ] **Step 3: 创建 cache.py**

```python
# infra/cache.py
import json
import hashlib
import time
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class CacheEntry:
    """缓存条目"""
    chapter: int
    checker: str
    content_hash: str
    timestamp: float
    ttl: float  # 秒
    result: Dict[str, Any]

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl <= 0:
            return False  # 永不过期
        return (time.time() - self.timestamp) > self.ttl


class CheckerCache:
    """
    检测结果缓存

    使用内容hash作为缓存键，章节内容变化时自动失效
    """

    def __init__(self, cache_dir: Optional[Path] = None, default_ttl: float = 7 * 24 * 3600):
        """
        Args:
            cache_dir: 缓存目录，默认 context/checker_cache
            default_ttl: 默认过期时间（秒），默认7天
        """
        if cache_dir is None:
            self.cache_dir = Path("context/checker_cache")
        else:
            self.cache_dir = Path(cache_dir)

        self.default_ttl = default_ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _content_hash(self, content: str) -> str:
        """计算内容hash"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:12]

    def _get_cache_path(self, checker: str, chapter: int, content_hash: str) -> Path:
        """获取缓存文件路径"""
        checker_dir = self.cache_dir / checker
        checker_dir.mkdir(exist_ok=True)
        return checker_dir / f"ch{chapter:03d}_{content_hash}.json"

    def set(self, checker: str, chapter: int, content: str, result: Dict[str, Any], ttl_seconds: float = None):
        """
        设置缓存

        Args:
            checker: 检测器名称
            chapter: 章节号
            content: 章节内容
            result: 检测结果
            ttl_seconds: 过期时间（秒），None使用默认值
        """
        content_hash = self._content_hash(content)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl

        entry = CacheEntry(
            chapter=chapter,
            checker=checker,
            content_hash=content_hash,
            timestamp=time.time(),
            ttl=ttl,
            result=result
        )

        cache_path = self._get_cache_path(checker, chapter, content_hash)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(entry), f, ensure_ascii=False)

    def get(self, checker: str, chapter: int, content: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存

        Returns:
            缓存结果，或None（未命中/过期）
        """
        content_hash = self._content_hash(content)
        cache_path = self._get_cache_path(checker, chapter, content_hash)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            entry = CacheEntry(**data)

            # 检查过期
            if entry.is_expired():
                cache_path.unlink()  # 删除过期缓存
                return None

            return entry.result

        except (json.JSONDecodeError, KeyError):
            return None

    def clear(self, checker: str = None, chapter: int = None):
        """清除缓存"""
        if checker is None:
            # 清除所有
            for f in self.cache_dir.rglob("*.json"):
                f.unlink()
        elif chapter is None:
            # 清除指定检测器
            checker_dir = self.cache_dir / checker
            if checker_dir.exists():
                for f in checker_dir.glob("*.json"):
                    f.unlink()
        else:
            # 清除指定章节（所有hash）
            checker_dir = self.cache_dir / checker
            if checker_dir.exists():
                for f in checker_dir.glob(f"ch{chapter:03d}_*.json"):
                    f.unlink()
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_cache.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add tests/test_cache.py infra/cache.py
git commit -m "feat(cache): add CheckerCache for result caching"
```

---

## Task 3: 创建 FalsePositiveFilter 误报过滤

**Files:**
- Create: `infra/filter.py`
- Test: `tests/test_filter.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_filter.py
import pytest
from infra.filter import FalsePositiveFilter

def test_filter_removes_detector_issues():
    filter = FalsePositiveFilter()
    from infra.quality import Issue

    # 创建检测器局限问题
    issue = Issue(
        chapter=1,
        dimension="一致性",
        issue_type="时间线矛盾",
        severity="P1",
        description="亿万年时间跨度",
        evidence="宇宙级场景"
    )

    filtered = filter.filter([issue], "章节内容...")
    assert len(filtered) == 0  # 应该被过滤

def test_filter_keeps_content_issues():
    filter = FalsePositiveFilter()
    from infra.quality import Issue

    # 创建真实内容问题
    issue = Issue(
        chapter=1,
        dimension="一致性",
        issue_type="状态矛盾",
        severity="P0",
        description="角色状态前后不一致",
        evidence="前文说死了，后文活着"
    )

    filtered = filter.filter([issue], "章节内容...")
    assert len(filtered) == 1  # 应该保留
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_filter.py -v`
Expected: FAIL - module not found

- [ ] **Step 3: 创建 filter.py**

```python
# infra/filter.py
from typing import List
from infra.quality import Issue
from tools.problem_classifier import ProblemClassifier


class FalsePositiveFilter:
    """
    误报过滤器

    使用 ProblemClassifier 区分：
    - CONTENT_ISSUE: 真实问题，保留
    - DETECTOR_ISSUE: 检测器局限，过滤
    - NEEDS_CONTEXT: 需要上下文，暂保留
    """

    def __init__(self):
        self.classifier = ProblemClassifier()

    def filter(self, issues: List[Issue], chapter_content: str = "") -> List[Issue]:
        """
        过滤误报

        Args:
            issues: 问题列表
            chapter_content: 章节内容（用于更精确判断）

        Returns:
            过滤后的问题列表
        """
        filtered = []

        for issue in issues:
            classification = self.classifier.classify(issue, chapter_content)

            if classification == "CONTENT_ISSUE":
                # 真实问题，保留
                filtered.append(issue)
            elif classification == "NEEDS_CONTEXT":
                # 需要上下文的问题暂保留（保守策略）
                filtered.append(issue)
            # DETECTOR_ISSUE 直接过滤

        return filtered

    def filter_batch(self, issues_by_chapter: dict, chapter_contents: dict = None) -> dict:
        """
        批量过滤误报

        Args:
            issues_by_chapter: {chapter_num: [issues]}
            chapter_contents: {chapter_num: content}

        Returns:
            过滤后的问题映射
        """
        result = {}

        for chapter, issues in issues_by_chapter.items():
            content = chapter_contents.get(chapter, "") if chapter_contents else ""
            filtered = self.filter(issues, content)
            if filtered:  # 只保留有问题的章节
                result[chapter] = filtered

        return result
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_filter.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add tests/test_filter.py infra/filter.py
git commit -m "feat(filter): add FalsePositiveFilter for issue classification"
```

---

## Task 4: 修改 SentenceDiversityChecker 使用 PatternRegistry

**Files:**
- Modify: `infra/consistency/checkers/sentence_diversity_checker.py`

- [ ] **Step 1: 读取当前实现**

查看 `SentenceDiversityChecker` 如何使用正则表达式

- [ ] **Step 2: 修改为使用 PatternRegistry**

在 `check()` 方法中：

```python
from infra.patterns import PatternRegistry

def check(self, chapter_content: str, chapter_num: int, context: Optional[Dict] = None) -> List[DiversityIssue]:
    registry = PatternRegistry.get()

    # 使用预编译的模式
    dialog_pattern = registry.get('dialog')
    if dialog_pattern:
        matches = dialog_pattern.findall(chapter_content)
        # ...
```

- [ ] **Step 3: 测试修改**

Run: `pytest tests/test_sentence_diversity_checker.py -v`

- [ ] **Step 4: 提交**

```bash
git add infra/consistency/checkers/sentence_diversity_checker.py
git commit -m "refactor: use PatternRegistry in SentenceDiversityChecker"
```

---

## Task 5: 修改 LLMQualityChecker 集成缓存和过滤

**Files:**
- Modify: `tools/llm_quality_deep_check.py`

- [ ] **Step 1: 在 LLMQualityChecker.__init__ 中初始化缓存和过滤器**

```python
from infra.cache import CheckerCache
from infra.filter import FalsePositiveFilter

class LLMQualityChecker:
    def __init__(self, llm_service=None):
        self.llm = llm_service or LLMService()
        self.cache = CheckerCache()
        self.filter = FalsePositiveFilter()
        # ...
```

- [ ] **Step 2: 在 check 方法中先查缓存**

```python
def check(self, chapter_num: int, content: str = None):
    # 先从缓存获取
    cached = self.cache.get("llm_quality", chapter_num, content or "")
    if cached:
        return cached

    # ... 执行检测 ...

    # 保存缓存
    self.cache.set("llm_quality", chapter_num, content, result)
    return result
```

- [ ] **Step 3: 在返回结果前过滤误报**

```python
def check_character_consistency(self, chapter_num, content):
    # ... LLM 检测 ...

    # 过滤误报
    filtered_issues = self.filter.filter(issues, content)
    return filtered_issues
```

- [ ] **Step 4: 测试修改**

Run: `pytest tests/ -k "llm_quality" -v`

- [ ] **Step 5: 提交**

```bash
git add tools/llm_quality_deep_check.py
git commit -m "feat(llm_quality): integrate CheckerCache and FalsePositiveFilter"
```

---

## Task 6: 运行完整测试套件

- [ ] **Step 1: 运行所有测试**

Run: `pytest tests/ -x -q --tb=short`

- [ ] **Step 2: 性能基准测试**

```bash
# 缓存前后对比
python -c "
import time
from tools.llm_quality_deep_check import LLMQualityChecker

# 第一次（无缓存）
start = time.time()
checker = LLMQualityChecker()
result = checker.check(1)
print(f'First run: {time.time() - start:.2f}s')

# 第二次（有缓存）
start = time.time()
result = checker.check(1)
print(f'Cached run: {time.time() - start:.2f}s')
"
```

- [ ] **Step 3: 提交**

```bash
git add -A
git commit -m "test: verify Phase 2 performance optimizations"
```

---

## 验证清单

- [ ] PatternRegistry 单例正常工作
- [ ] SentenceDiversityChecker 使用预编译模式
- [ ] CheckerCache 命中时返回缓存结果
- [ ] FalsePositiveFilter 过滤误报
- [ ] LLMQualityChecker 集成缓存和过滤
- [ ] 所有 715+ 测试继续通过
- [ ] 缓存命中时速度提升 10x+
