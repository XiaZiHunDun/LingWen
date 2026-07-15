# Phase 2 性能优化设计文档

> **版本**: v1.0
> **日期**: 2026-05-26
> **阶段**: Phase 2 - 性能优化

## 1. 概述

### 1.1 目标

提升小说工厂质量检查系统的性能，通过缓存、预编译和误报过滤减少无效计算。

### 1.2 现状问题

- **LLM API 调用昂贵**：每次检测都重新调用，无缓存
- **Regex 模式重复编译**：每次检测重新编译相同模式
- **误报率高**：约 40% 的检测结果是检测器局限，非真实问题

### 1.3 优化收益

| 优化项 | 收益 |
|--------|------|
| 结果缓存 | 重复检测速度提升 10x+ |
| 预编译模式 | 模式匹配速度提升 2-3x |
| 误报过滤 | 减少 40% 无效 LLM 调用 |

## 2. 设计方案

### 2.1 结果缓存

#### 缓存结构

```
context/checker_cache/
└── {checker_name}/
    └── {chapter_num}_{content_hash}.json
```

#### 缓存内容

```json
{
  "chapter": 1,
  "checker": "character_checker",
  "content_hash": "abc123",
  "timestamp": "2026-05-26T10:00:00",
  "result": {
    "issues": [...],
    "score": 0.85
  }
}
```

#### 缓存策略

- **命中条件**：`checker_name` + `chapter_num` + `content_hash` 完全匹配
- **失效条件**：章节内容变化（hash 不同）
- **过期时间**：7 天（防止数据陈旧）
- **存储位置**：`context/checker_cache/`

### 2.2 预编译模式

#### 当前问题

`SentenceDiversityChecker` 等检测器在每次检测时重新编译 Regex 模式：

```python
# 当前：每次调用都编译
pattern = re.compile(r'「[^」]+」')
```

#### 解决方案

创建 `PatternRegistry` 统一管理预编译模式：

```python
# infra/patterns.py
class PatternRegistry:
    """全局模式注册表（单例）"""

    _instance = None
    _patterns = {}

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._compile_all()
        return cls._instance

    def _compile_all(self):
        """启动时编译所有模式"""
        from tools.rules import SENTENCE_DIVERSITY_PATTERNS
        for name, (pattern, _) in SENTENCE_DIVERSITY_PATTERNS.items():
            self._patterns[name] = re.compile(pattern)

    def get(self, name: str) -> re.Pattern:
        return self._patterns.get(name)
```

#### 修改清单

| 文件 | 修改 |
|------|------|
| `SentenceDiversityChecker` | 使用 `PatternRegistry.get()` 替代直接编译 |
| `CharacterChecker` | 使用预编译模式 |
| `AITraceChecker` | 使用预编译模式 |

### 2.3 误报过滤

#### 集成 ProblemClassifier

在检测管道中集成 `ProblemClassifier`：

```python
class SmartChecker:
    def __init__(self):
        self.classifier = ProblemClassifier()

    def check(self, chapter_num, content):
        issues = self._run_checkers(content)

        # 过滤误报
        real_issues = []
        for issue in issues:
            classification = self.classifier.classify(issue, content)
            if classification == "CONTENT_ISSUE":
                real_issues.append(issue)
            # DETECTOR_ISSUE 和 NEEDS_CONTEXT 跳过

        return real_issues
```

#### 过滤效果

| 分类 | 处理 |
|------|------|
| CONTENT_ISSUE | 保留，需要修复 |
| DETECTOR_ISSUE | 跳过，检测器局限 |
| NEEDS_CONTEXT | 跳过，需更多上下文 |

## 3. 文件清单

### 3.1 新增文件

| 文件 | 行数 | 说明 |
|------|------|------|
| `infra/patterns.py` | ~100 | PatternRegistry 单例 |
| `infra/cache.py` | ~150 | CheckerCache 结果缓存 |
| `infra/filter.py` | ~80 | FalsePositiveFilter 误报过滤 |

### 3.2 修改文件

| 文件 | 修改 | 说明 |
|------|------|------|
| `SentenceDiversityChecker` | 使用 PatternRegistry | 模式预编译 |
| `CharacterChecker` | 使用 PatternRegistry | 模式预编译 |
| `LLMQualityChecker` | 集成过滤 | 减少无效调用 |

## 4. 实现顺序

1. **PatternRegistry** - 最简单，先实现
2. **CheckerCache** - 缓存基础设施
3. **FalsePositiveFilter** - 依赖 ProblemClassifier
4. **修改检测器** - 使用新组件

## 5. 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 缓存过期 | 检测结果陈旧 | 7天过期 + 内容hash验证 |
| 模式遗漏 | 检测失效 | 保留原始模式作为fallback |
| 过滤过度 | 漏掉真问题 | 仅过滤明确的 DETECTOR_ISSUE |

## 6. 成功标准

- [ ] PatternRegistry 单例正常工作
- [ ] 检测器启动时预编译所有模式
- [ ] CheckerCache 命中时返回缓存结果
- [ ] FalsePositiveFilter 过滤掉 40% 误报
- [ ] 整体检测速度提升 30%+
- [ ] 所有现有测试继续通过
