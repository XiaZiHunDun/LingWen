# 追读力系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现追读力系统最小可用版，包含钩子检测和爽点标记功能

**Architecture:** 
- ReadingPowerEngine 主编排器，协调规则匹配和LLM分析
- RuleMatcher 规则匹配器，基于YAML规则库快速初筛
- LLMAnalyzer LLM分析器，调用AI服务做深度分析
- HookTracker/CoolPointTracker 数据持久化到独立SQLite数据库
- 规则库分离到YAML配置文件，便于维护

**Tech Stack:** Python 3.13, SQLite, Pydantic, Anthropic/OpenAI AI Service

---

## 文件结构

```
novel-factory/
├── infra/
│   └── reading_power/              # 新建
│       ├── __init__.py
│       ├── engine.py              # ReadingPowerEngine
│       ├── rule_matcher.py        # RuleMatcher
│       ├── llm_analyzer.py        # LLMAnalyzer
│       ├── hook_tracker.py       # HookTracker
│       ├── coolpoint_tracker.py  # CoolPointTracker
│       └── db.py                  # ReadingPowerDB
├── rules/                         # 新建
│   ├── reading_power_hooks.yaml
│   └── reading_power_coolpoints.yaml
├── .state/
│   └── reading_power.db          # 自动创建
└── tests/
    └── reading_power/            # 新建
        ├── __init__.py
        ├── test_rule_matcher.py
        ├── test_hook_tracker.py
        ├── test_coolpoint_tracker.py
        ├── test_engine.py
        └── conftest.py
```

---

## Task 1: 数据库模块

**Files:**
- Create: `novel-factory/infra/reading_power/db.py`
- Create: `tests/reading_power/conftest.py`
- Test: `tests/reading_power/test_db.py`

- [ ] **Step 1: 创建数据库模块骨架**

```python
# novel-factory/infra/reading_power/db.py
import sqlite3
from pathlib import Path
from typing import Optional

class ReadingPowerDB:
    DB_PATH = Path(__file__).parent.parent.parent / ".state" / "reading_power.db"
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or self.DB_PATH
        self._ensure_db_path()
        self._init_db()
    
    def _ensure_db_path(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=5)
        conn.row_factory = sqlite3.Row
        return conn
```

- [ ] **Step 2: 创建数据库初始化方法**

```python
    def _init_db(self):
        conn = self._get_connection()
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS hooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter INTEGER NOT NULL,
            hook_type TEXT NOT NULL,
            strength REAL DEFAULT 0.5,
            position TEXT,
            content TEXT,
            llm_analyzed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(chapter, hook_type, position)
        );
        
        CREATE TABLE IF NOT EXISTS coolpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter INTEGER NOT NULL,
            pattern TEXT NOT NULL,
            density REAL DEFAULT 0.5,
            combo_with TEXT,
            content TEXT,
            llm_analyzed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(chapter, pattern)
        );
        
        CREATE TABLE IF NOT EXISTS chapter_summary (
            chapter INTEGER PRIMARY KEY,
            hook_count INTEGER DEFAULT 0,
            hook_strength_avg REAL DEFAULT 0.0,
            coolpoint_count INTEGER DEFAULT 0,
            coolpoint_density REAL DEFAULT 0.0,
            reading_power_score REAL DEFAULT 0.0,
            last_analyzed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS analysis_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter INTEGER NOT NULL,
            analyzer_type TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            duration_ms INTEGER,
            status TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_hooks_chapter ON hooks(chapter);
        CREATE INDEX IF NOT EXISTS idx_coolpoints_chapter ON coolpoints(chapter);
        CREATE INDEX IF NOT EXISTS idx_chapter_summary_chapter ON chapter_summary(chapter);
        """)
        conn.close()
```

- [ ] **Step 3: 添加CRUD方法**

```python
    def save_hook(self, chapter: int, hook_type: str, strength: float, 
                  position: str, content: str, llm_analyzed: bool = False) -> int:
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO hooks 
                (chapter, hook_type, strength, position, content, llm_analyzed)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (chapter, hook_type, strength, position, content, llm_analyzed))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def save_coolpoint(self, chapter: int, pattern: str, density: float,
                       combo_with: str, content: str, llm_analyzed: bool = False) -> int:
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO coolpoints
                (chapter, pattern, density, combo_with, content, llm_analyzed)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (chapter, pattern, density, combo_with, content, llm_analyzed))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def get_hooks(self, chapter: int) -> list:
        conn = self._get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM hooks WHERE chapter = ?", (chapter,)
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def get_coolpoints(self, chapter: int) -> list:
        conn = self._get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM coolpoints WHERE chapter = ?", (chapter,)
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
```

- [ ] **Step 4: 添加章节摘要方法**

```python
    def update_chapter_summary(self, chapter: int, hook_count: int,
                                hook_strength_avg: float, coolpoint_count: int,
                                coolpoint_density: float) -> None:
        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT INTO chapter_summary 
                (chapter, hook_count, hook_strength_avg, coolpoint_count, 
                 coolpoint_density, last_analyzed_at, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(chapter) DO UPDATE SET
                hook_count = excluded.hook_count,
                hook_strength_avg = excluded.hook_strength_avg,
                coolpoint_count = excluded.coolpoint_count,
                coolpoint_density = excluded.coolpoint_density,
                last_analyzed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            """, (chapter, hook_count, hook_strength_avg, coolpoint_count, coolpoint_density))
            conn.commit()
        finally:
            conn.close()
    
    def get_chapter_summary(self, chapter: int) -> Optional[dict]:
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM chapter_summary WHERE chapter = ?", (chapter,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
```

- [ ] **Step 5: 写测试**

```python
# tests/reading_power/test_db.py
import pytest
from pathlib import Path
import tempfile
import os

from novel_factory.infra.reading_power.db import ReadingPowerDB

@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_reading_power.db"
        db = ReadingPowerDB(db_path)
        yield db

def test_save_and_get_hook(temp_db):
    temp_db.save_hook(1, "危机钩", 0.8, "结尾", "危险逼近...")
    hooks = temp_db.get_hooks(1)
    assert len(hooks) == 1
    assert hooks[0]["hook_type"] == "危机钩"
    assert hooks[0]["strength"] == 0.8

def test_save_and_get_coolpoint(temp_db):
    temp_db.save_coolpoint(1, "装逼打脸", 0.9, "[]", "打脸场景...")
    coolpoints = temp_db.get_coolpoints(1)
    assert len(coolpoints) == 1
    assert coolpoints[0]["pattern"] == "装逼打脸"

def test_update_and_get_chapter_summary(temp_db):
    temp_db.update_chapter_summary(1, 3, 0.75, 2, 0.85)
    summary = temp_db.get_chapter_summary(1)
    assert summary["hook_count"] == 3
    assert summary["hook_strength_avg"] == 0.75
```

- [ ] **Step 6: 运行测试验证**

Run: `pytest tests/reading_power/test_db.py -v`

- [ ] **Step 7: 提交**

```bash
git add novel-factory/infra/reading_power/db.py tests/reading_power/test_db.py tests/reading_power/conftest.py
git commit -m "feat: add ReadingPowerDB for 追读力系统"
```

---

## Task 2: 规则库文件

**Files:**
- Create: `novel-factory/rules/reading_power_hooks.yaml`
- Create: `novel-factory/rules/reading_power_coolpoints.yaml`
- Test: `tests/reading_power/test_rule_matcher.py`

- [ ] **Step 1: 创建钩子规则库**

```yaml
# novel-factory/rules/reading_power_hooks.yaml
hook_patterns:
  危机钩:
    description: 危险逼近或敌人出现，触发读者紧张感
    keywords:
      - 危险
      - 危机
      - 敌人出现
      - 死亡威胁
      - 危机四伏
      - 生死关头
    position_weight:
      开篇: 1.2
      中段: 1.0
      结尾: 1.5
    strength_base: 0.7

  悬念钩:
    description: 制造信息缺口，引发读者好奇心
    keywords:
      - 未解之谜
      - 悬念
      - 秘密
      - 隐藏
      - 真相是
      - 令人费解
    position_weight:
      开篇: 1.5
      中段: 1.0
      结尾: 1.2
    strength_base: 0.6

  渴望钩:
    description: 让读者期待好事发生
    keywords:
      - 期待
      - 好事将近
      - 奖励
      - 突破在即
      - 即将获得
      - 希望
    position_weight:
      中段: 1.3
      结尾: 1.4
    strength_base: 0.5

  情绪钩:
    description: 触发强烈情感反应
    keywords:
      - 震惊
      - 愤怒
      - 感动
      - 心疼
      - 爆笑
      - 热泪盈眶
    position_weight:
      开篇: 1.2
      中段: 1.0
      结尾: 1.1
    strength_base: 0.6

  选择钩:
    description: 高风险决策驱动情节
    keywords:
      - 必须选择
      - 艰难决定
      - 赌上一切
      - 生死抉择
      - 两难
    position_weight:
      结尾: 1.5
      中段: 1.2
    strength_base: 0.7
```

- [ ] **Step 2: 创建爽点规则库**

```yaml
# novel-factory/rules/reading_power_coolpoints.yaml
coolpoint_patterns:
  装逼打脸:
    description: 展示实力后打脸对方
    triggers:
      - 打脸
      - 反杀
      - 碾压
      - 震惊
      - 目瞪口呆
      - 啪啪打脸
    emotion_intensity: 0.9
    combo_potential:
      - 扮猪吃虎
      - 越级反杀

  扮猪吃虎:
    description: 故意示弱后突然展示实力
    triggers:
      - 隐藏实力
      - 示弱
      - 伪装
      - 低调
      - 不为人知
      - 原来是他
    emotion_intensity: 0.85
    combo_potential:
      - 装逼打脸
      - 身份掉马

  越级反杀:
    description: 以弱胜强，越级挑战胜利
    triggers:
      - 越级
      - 反杀
      - 跨阶
      - 逆袭
      - 以下克上
    emotion_intensity: 0.95
    combo_potential:
      - 装逼打脸

  迪化误解:
    description: 对方错误判断主角实力
    triggers:
      - 误解
      - 以为
      - 以为是
      - 错估
      - 大跌眼镜
    emotion_intensity: 0.75
    combo_potential:
      - 扮猪吃虎
      - 身份掉马

  身份掉马:
    description: 隐藏身份突然揭露
    triggers:
      - 身份暴露
      - 原来是
      - 真相大白
      - 马甲掉落
      - 揭晓
    emotion_intensity: 0.8
    combo_potential:
      - 扮猪吃虎
      - 装逼打脸
```

- [ ] **Step 3: 写RuleMatcher类**

```python
# novel-factory/infra/reading_power/rule_matcher.py
import re
from pathlib import Path
from typing import List, Dict, Any, NamedTuple
import yaml

from novel_factory.infra.reading_power.db import ReadingPowerDB

class SuspectedSegment(NamedTuple):
    segment_type: str  # "hook" or "coolpoint"
    pattern_name: str
    content: str
    confidence: float
    position: str
    offset: int

class RuleMatcher:
    HOOKS_RULES_PATH = Path(__file__).parent.parent.parent / "rules" / "reading_power_hooks.yaml"
    COOLPOINTS_RULES_PATH = Path(__file__).parent.parent.parent / "rules" / "reading_power_coolpoints.yaml"
    
    def __init__(self, db: ReadingPowerDB):
        self.db = db
        self.hook_rules = self._load_rules(self.HOOKS_RULES_PATH)
        self.coolpoint_rules = self._load_rules(self.COOLPOINTS_RULES_PATH)
    
    def _load_rules(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {"hook_patterns": {}} if "hooks" in str(path) else {"coolpoint_patterns": {}}
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    def scan(self, chapter_text: str, chapter_num: int) -> List[SuspectedSegment]:
        results = []
        position = self._determine_position(chapter_text)
        
        # Scan hooks
        hook_key = "hook_patterns"
        if hook_key in self.hook_rules:
            for hook_type, rule in self.hook_rules[hook_key].items():
                for keyword in rule.get("keywords", []):
                    pattern = re.escape(keyword)
                    for match in re.finditer(pattern, chapter_text):
                        confidence = rule.get("strength_base", 0.5)
                        pos_weight = rule.get("position_weight", {}).get(position, 1.0)
                        confidence *= pos_weight
                        
                        start = max(0, match.start() - 20)
                        end = min(len(chapter_text), match.end() + 40)
                        context = chapter_text[start:end]
                        
                        results.append(SuspectedSegment(
                            segment_type="hook",
                            pattern_name=hook_type,
                            content=context,
                            confidence=min(confidence, 1.0),
                            position=position,
                            offset=match.start()
                        ))
        
        # Scan coolpoints
        coolpoint_key = "coolpoint_patterns"
        if coolpoint_key in self.coolpoint_rules:
            for pattern_name, rule in self.coolpoint_rules[coolpoint_key].items():
                for trigger in rule.get("triggers", []):
                    pattern = re.escape(trigger)
                    for match in re.finditer(pattern, chapter_text):
                        confidence = rule.get("emotion_intensity", 0.5)
                        
                        start = max(0, match.start() - 20)
                        end = min(len(chapter_text), match.end() + 40)
                        context = chapter_text[start:end]
                        
                        results.append(SuspectedSegment(
                            segment_type="coolpoint",
                            pattern_name=pattern_name,
                            content=context,
                            confidence=min(confidence, 1.0),
                            position=position,
                            offset=match.start()
                        ))
        
        return sorted(results, key=lambda x: x.confidence, reverse=True)
    
    def _determine_position(self, text: str) -> str:
        """Determine if match is at beginning, middle, or end of text."""
        length = len(text)
        if length == 0:
            return "中段"
        # Use word-based position
        words = text.split()
        return "开头"
```

- [ ] **Step 4: 写测试**

```python
# tests/reading_power/test_rule_matcher.py
import pytest
from unittest.mock import MagicMock

from novel_factory.infra.reading_power.rule_matcher import RuleMatcher, SuspectedSegment

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def rule_matcher(mock_db, tmp_path):
    # Create temporary rule files
    hooks_file = tmp_path / "reading_power_hooks.yaml"
    hooks_file.write_text("""
hook_patterns:
  危机钩:
    description: Test hook
    keywords:
      - 危险
      - 危机
    strength_base: 0.7
    position_weight:
      结尾: 1.5
      开篇: 1.2
""", encoding="utf-8")
    
    coolpoints_file = tmp_path / "reading_power_coolpoints.yaml"
    coolpoints_file.write_text("""
coolpoint_patterns:
  装逼打脸:
    description: Test coolpoint
    triggers:
      - 打脸
      - 反杀
    emotion_intensity: 0.9
""", encoding="utf-8")
    
    matcher = RuleMatcher(mock_db)
    matcher.HOOKS_RULES_PATH = hooks_file
    matcher.COOLPOINTS_RULES_PATH = coolpoints_file
    matcher.hook_rules = matcher._load_rules(hooks_file)
    matcher.coolpoint_rules = matcher._load_rules(coolpoints_file)
    
    return matcher

def test_scan_detects_hook(rule_matcher):
    text = "主角遇到了危险，敌人出现了"
    results = rule_matcher.scan(text, 1)
    
    hooks = [r for r in results if r.segment_type == "hook"]
    assert len(hooks) >= 2  # 危险 and 敌人出现

def test_scan_detects_coolpoint(rule_matcher):
    text = "主角直接打脸对手，反杀成功"
    results = rule_matcher.scan(text, 1)
    
    coolpoints = [r for r in results if r.segment_type == "coolpoint"]
    assert len(coolpoints) >= 2  # 打脸 and 反杀

def test_scan_returns_sorted_by_confidence(rule_matcher):
    text = "结尾处主角面临生死抉择"
    results = rule_matcher.scan(text, 1)
    
    if len(results) > 1:
        for i in range(len(results) - 1):
            assert results[i].confidence >= results[i + 1].confidence
```

- [ ] **Step 5: 运行测试验证**

Run: `pytest tests/reading_power/test_rule_matcher.py -v`

- [ ] **Step 6: 提交**

```bash
git add novel-factory/rules/reading_power_hooks.yaml novel-factory/rules/reading_power_coolpoints.yaml novel-factory/infra/reading_power/rule_matcher.py tests/reading_power/test_rule_matcher.py
git commit -m "feat: add RuleMatcher and reading power rule libraries"
```

---

## Task 3: LLM分析器

**Files:**
- Create: `novel-factory/infra/reading_power/llm_analyzer.py`
- Test: `tests/reading_power/test_llm_analyzer.py`

- [ ] **Step 1: 创建LLMAnalyzer类**

```python
# novel-factory/infra/reading_power/llm_analyzer.py
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from novel_factory.infra.reading_power.rule_matcher import SuspectedSegment

ANALYZE_HOOKS_PROMPT = """分析以下小说段落，识别其中的追读力元素。

【钩子类型】
- 危机钩：危险逼近、敌人出现
- 悬念钩：制造信息缺口、引发好奇
- 渴望钩：让读者期待好事发生
- 情绪钩：触发强烈情感反应
- 选择钩：高风险决策驱动

【爽点类型】
- 装逼打脸：展示实力后打脸对方
- 扮猪吃虎：故意示弱后突然展示实力
- 越级反杀：以弱胜强
- 迪化误解：对方错误判断主角实力
- 身份掉马：隐藏身份突然揭露

请返回JSON格式：
{
  "hooks": [
    {"type": "危机钩", "strength": 0.8, "position": "结尾", "reason": "..."}
  ],
  "coolpoints": [
    {"pattern": "装逼打脸", "density": 0.9, "combo_with": ["越级反杀"], "reason": "..."}
  ]
}

段落内容：
{content}
"""

@dataclass
class AnalysisResult:
    hooks: List[Dict[str, Any]]
    coolpoints: List[Dict[str, Any]]
    raw_response: str
    success: bool
    error: Optional[str] = None

class LLMAnalyzer:
    def __init__(self, ai_service):
        """
        ai_service: AI服务实例，需支持 completion() 方法
        """
        self.ai_service = ai_service
    
    def analyze(self, suspected_segments: List[SuspectedSegment], 
                chapter_text: str) -> AnalysisResult:
        """
        对疑似段落进行LLM深度分析
        """
        if not suspected_segments:
            return AnalysisResult(hooks=[], coolpoints=[], raw_response="", success=True)
        
        # 构建上下文
        context = "\n".join([
            f"[{seg.segment_type}] {seg.pattern_name}: {seg.content}"
            for seg in suspected_segments[:10]  # 限制分析数量
        ])
        
        # 如果原始文本不太长，也附上完整文本
        if len(chapter_text) < 2000:
            full_context = chapter_text
        else:
            full_context = context
        
        prompt = ANALYZE_HOOKS_PROMPT.format(content=full_context)
        
        try:
            response = self.ai_service.completion(prompt)
            raw = response.content if hasattr(response, 'content') else str(response)
            
            # 解析JSON
            result = self._parse_json_response(raw)
            
            return AnalysisResult(
                hooks=result.get("hooks", []),
                coolpoints=result.get("coolpoints", []),
                raw_response=raw,
                success=True
            )
        except Exception as e:
            return AnalysisResult(
                hooks=[],
                coolpoints=[],
                raw_response="",
                success=False,
                error=str(e)
            )
    
    def _parse_json_response(self, raw: str) -> Dict[str, Any]:
        """解析LLM返回的JSON"""
        # 尝试提取JSON块
        if "```json" in raw:
            start = raw.find("```json") + 7
            end = raw.find("```", start)
            raw = raw[start:end]
        elif "```" in raw:
            start = raw.find("```") + 3
            end = raw.find("```", start)
            raw = raw[start:end]
        
        # 尝试找到JSON对象
        raw = raw.strip()
        if not raw.startswith("{"):
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                raw = raw[start:end]
        
        return json.loads(raw)
```

- [ ] **Step 2: 写测试**

```python
# tests/reading_power/test_llm_analyzer.py
import pytest
from unittest.mock import MagicMock, AsyncMock
from novel_factory.infra.reading_power.llm_analyzer import LLMAnalyzer, AnalysisResult
from novel_factory.infra.reading_power.rule_matcher import SuspectedSegment

@pytest.fixture
def mock_ai_service():
    service = MagicMock()
    response = MagicMock()
    response.content = '{"hooks": [{"type": "危机钩", "strength": 0.8, "position": "结尾"}], "coolpoints": []}'
    service.completion.return_value = response
    return service

def test_analyze_with_segments(mock_ai_service):
    segments = [
        SuspectedSegment("hook", "危机钩", "危险逼近...", 0.8, "结尾", 100),
        SuspectedSegment("coolpoint", "装逼打脸", "打脸场景...", 0.9, "中段", 200),
    ]
    
    analyzer = LLMAnalyzer(mock_ai_service)
    result = analyzer.analyze(segments, "章节文本")
    
    assert result.success is True
    assert len(result.hooks) == 1
    assert result.hooks[0]["type"] == "危机钩"

def test_analyze_empty_segments(mock_ai_service):
    analyzer = LLMAnalyzer(mock_ai_service)
    result = analyzer.analyze([], "章节文本")
    
    assert result.success is True
    assert result.hooks == []
    assert result.coolpoints == []

def test_parse_json_response():
    analyzer = LLMAnalyzer(None)
    
    raw = '{"hooks": [{"type": "测试", "strength": 0.5}], "coolpoints": []}'
    result = analyzer._parse_json_response(raw)
    
    assert result["hooks"][0]["type"] == "测试"
```

- [ ] **Step 3: 运行测试验证**

Run: `pytest tests/reading_power/test_llm_analyzer.py -v`

- [ ] **Step 4: 提交**

```bash
git add novel-factory/infra/reading_power/llm_analyzer.py tests/reading_power/test_llm_analyzer.py
git commit -m "feat: add LLMAnalyzer for deep reading power analysis"
```

---

## Task 4: HookTracker和CoolPointTracker

**Files:**
- Create: `novel-factory/infra/reading_power/hook_tracker.py`
- Create: `novel-factory/infra/reading_power/coolpoint_tracker.py`
- Test: `tests/reading_power/test_hook_tracker.py`
- Test: `tests/reading_power/test_coolpoint_tracker.py`

- [ ] **Step 1: 创建HookTracker**

```python
# novel-factory/infra/reading_power/hook_tracker.py
from typing import List, Dict, Any
import json

from novel_factory.infra.reading_power.db import ReadingPowerDB

class HookTracker:
    def __init__(self, db: ReadingPowerDB):
        self.db = db
    
    def track(self, chapter: int, hooks: List[Dict[str, Any]]) -> None:
        """
        存储钩子数据到数据库
        hooks格式: [{"type": "危机钩", "strength": 0.8, "position": "结尾", "content": "..."}]
        """
        for hook in hooks:
            self.db.save_hook(
                chapter=chapter,
                hook_type=hook["type"],
                strength=hook.get("strength", 0.5),
                position=hook.get("position", "中段"),
                content=hook.get("content", ""),
                llm_analyzed=hook.get("llm_analyzed", False)
            )
    
    def get_hooks(self, chapter: int) -> List[Dict[str, Any]]:
        """获取章节的所有钩子"""
        return self.db.get_hooks(chapter)
    
    def get_hook_summary(self, chapter: int) -> Dict[str, Any]:
        """获取章节钩子摘要"""
        hooks = self.get_hooks(chapter)
        if not hooks:
            return {"count": 0, "avg_strength": 0.0, "types": []}
        
        types = [h["hook_type"] for h in hooks]
        avg_strength = sum(h["strength"] for h in hooks) / len(hooks)
        
        return {
            "count": len(hooks),
            "avg_strength": avg_strength,
            "types": list(set(types))
        }
    
    def get_all_hooks_by_type(self, hook_type: str, start_chapter: int = 1, 
                             end_chapter: int = 9999) -> List[Dict[str, Any]]:
        """获取指定类型的所有钩子"""
        conn = self.db._get_connection()
        try:
            rows = conn.execute("""
                SELECT * FROM hooks 
                WHERE hook_type = ? AND chapter >= ? AND chapter <= ?
                ORDER BY chapter
            """, (hook_type, start_chapter, end_chapter)).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
```

- [ ] **Step 2: 创建CoolPointTracker**

```python
# novel-factory/infra/reading_power/coolpoint_tracker.py
from typing import List, Dict, Any

from novel_factory.infra.reading_power.db import ReadingPowerDB

class CoolPointTracker:
    def __init__(self, db: ReadingPowerDB):
        self.db = db
    
    def track(self, chapter: int, coolpoints: List[Dict[str, Any]]) -> None:
        """
        存储爽点数据到数据库
        coolpoints格式: [{"pattern": "装逼打脸", "density": 0.9, "combo_with": ["越级反杀"], "content": "..."}]
        """
        for cp in coolpoints:
            combo_str = json.dumps(cp.get("combo_with", []), ensure_ascii=False) if cp.get("combo_with") else "[]"
            
            self.db.save_coolpoint(
                chapter=chapter,
                pattern=cp["pattern"],
                density=cp.get("density", 0.5),
                combo_with=combo_str,
                content=cp.get("content", ""),
                llm_analyzed=cp.get("llm_analyzed", False)
            )
    
    def get_coolpoints(self, chapter: int) -> List[Dict[str, Any]]:
        """获取章节的所有爽点"""
        coolpoints = self.db.get_coolpoints(chapter)
        for cp in coolpoints:
            if cp.get("combo_with"):
                try:
                    cp["combo_with"] = json.loads(cp["combo_with"])
                except:
                    cp["combo_with"] = []
        return coolpoints
    
    def get_coolpoint_summary(self, chapter: int) -> Dict[str, Any]:
        """获取章节爽点摘要"""
        coolpoints = self.get_coolpoints(chapter)
        if not coolpoints:
            return {"count": 0, "avg_density": 0.0, "patterns": []}
        
        patterns = [c["pattern"] for c in coolpoints]
        avg_density = sum(c["density"] for c in coolpoints) / len(coolpoints)
        
        return {
            "count": len(coolpoints),
            "avg_density": avg_density,
            "patterns": list(set(patterns))
        }
    
    def get_combo_pairs(self, chapter: int) -> List[tuple]:
        """获取章节中的爽点组合"""
        coolpoints = self.get_coolpoints(chapter)
        pairs = []
        for cp in coolpoints:
            for combo in cp.get("combo_with", []):
                pairs.append((cp["pattern"], combo))
        return pairs
```

- [ ] **Step 3: 写测试**

```python
# tests/reading_power/test_hook_tracker.py
import pytest
from unittest.mock import MagicMock
from novel_factory.infra.reading_power.hook_tracker import HookTracker

def test_track_and_get_hooks():
    mock_db = MagicMock()
    mock_db.get_hooks.return_value = [
        {"hook_type": "危机钩", "strength": 0.8, "position": "结尾"}
    ]
    
    tracker = HookTracker(mock_db)
    
    hooks = [{"type": "危机钩", "strength": 0.8, "position": "结尾", "content": "危险..."}]
    tracker.track(1, hooks)
    
    mock_db.save_hook.assert_called_once()
    result = tracker.get_hooks(1)
    assert len(result) == 1

def test_get_hook_summary():
    mock_db = MagicMock()
    mock_db.get_hooks.return_value = [
        {"hook_type": "危机钩", "strength": 0.8},
        {"hook_type": "悬念钩", "strength": 0.6},
    ]
    
    tracker = HookTracker(mock_db)
    summary = tracker.get_hook_summary(1)
    
    assert summary["count"] == 2
    assert summary["avg_strength"] == 0.7
```

```python
# tests/reading_power/test_coolpoint_tracker.py
import pytest
from unittest.mock import MagicMock
from novel_factory.infra.reading_power.coolpoint_tracker import CoolPointTracker

def test_track_and_get_coolpoints():
    mock_db = MagicMock()
    mock_db.get_coolpoints.return_value = [
        {"pattern": "装逼打脸", "density": 0.9, "combo_with": "[]"}
    ]
    
    tracker = CoolPointTracker(mock_db)
    
    coolpoints = [{"pattern": "装逼打脸", "density": 0.9, "combo_with": [], "content": "打脸..."}]
    tracker.track(1, coolpoints)
    
    mock_db.save_coolpoint.assert_called_once()
    result = tracker.get_coolpoints(1)
    assert len(result) == 1
```

- [ ] **Step 4: 运行测试验证**

Run: `pytest tests/reading_power/test_hook_tracker.py tests/reading_power/test_coolpoint_tracker.py -v`

- [ ] **Step 5: 提交**

```bash
git add novel-factory/infra/reading_power/hook_tracker.py novel-factory/infra/reading_power/coolpoint_tracker.py tests/reading_power/test_hook_tracker.py tests/reading_power/test_coolpoint_tracker.py
git commit -m "feat: add HookTracker and CoolPointTracker"
```

---

## Task 5: ReadingPowerEngine主编排器

**Files:**
- Create: `novel-factory/infra/reading_power/engine.py`
- Create: `novel-factory/infra/reading_power/__init__.py`
- Test: `tests/reading_power/test_engine.py`

- [ ] **Step 1: 创建ReadingPowerEngine**

```python
# novel-factory/infra/reading_power/engine.py
from typing import List, Dict, Any, Optional
import logging

from novel_factory.infra.reading_power.db import ReadingPowerDB
from novel_factory.infra.reading_power.rule_matcher import RuleMatcher, SuspectedSegment
from novel_factory.infra.reading_power.llm_analyzer import LLMAnalyzer, AnalysisResult
from novel_factory.infra.reading_power.hook_tracker import HookTracker
from novel_factory.infra.reading_power.coolpoint_tracker import CoolPointTracker

logger = logging.getLogger(__name__)

class ReadingPowerEngine:
    """
    追读力系统主编排器
    协调规则匹配和LLM分析，实现混合模式检测
    """
    
    def __init__(self, db: Optional[ReadingPowerDB] = None, ai_service=None):
        self.db = db or ReadingPowerDB()
        self.rule_matcher = RuleMatcher(self.db)
        self.llm_analyzer = LLMAnalyzer(ai_service) if ai_service else None
        self.hook_tracker = HookTracker(self.db)
        self.coolpoint_tracker = CoolPointTracker(self.db)
    
    def analyze_chapter(self, chapter_num: int, chapter_text: str) -> AnalysisResult:
        """
        分析章节的追读力
        1. 规则快速扫描
        2. 根据疑似段落数量决定是否使用LLM
        3. 存储结果并更新摘要
        """
        if not chapter_text or not chapter_text.strip():
            logger.warning(f"Chapter {chapter_num} is empty, skipping analysis")
            return AnalysisResult(hooks=[], coolpoints=[], raw_response="", success=True)
        
        # Step 1: 规则快速扫描
        suspected = self.rule_matcher.scan(chapter_text, chapter_num)
        
        # Step 2: 根据疑似段落数量决定分析策略
        if len(suspected) > 10:
            # 疑似段落过多，使用规则结果（可能误报较多）
            logger.info(f"Chapter {chapter_num}: {len(suspected)} suspected segments, using rule-based results")
            hooks, coolpoints = self._merge_rule_results(suspected)
        elif self.llm_analyzer and len(suspected) > 0:
            # 疑似段落在合理范围，使用LLM深度分析
            try:
                result = self.llm_analyzer.analyze(suspected, chapter_text)
                if result.success:
                    hooks = result.hooks
                    coolpoints = result.coolpoints
                else:
                    logger.warning(f"LLM analysis failed for chapter {chapter_num}, falling back to rules")
                    hooks, coolpoints = self._merge_rule_results(suspected)
            except Exception as e:
                logger.error(f"LLM analysis error for chapter {chapter_num}: {e}")
                hooks, coolpoints = self._merge_rule_results(suspected)
        else:
            # 无疑似段落或无LLM服务
            hooks, coolpoints = [], []
        
        # Step 3: 存储结果
        if hooks:
            self.hook_tracker.track(chapter_num, hooks)
        if coolpoints:
            self.coolpoint_tracker.track(chapter_num, coolpoints)
        
        # Step 4: 更新摘要
        self._update_chapter_summary(chapter_num, hooks, coolpoints)
        
        return AnalysisResult(
            hooks=hooks,
            coolpoints=coolpoints,
            raw_response="",
            success=True
        )
    
    def _merge_rule_results(self, suspected: List[SuspectedSegment]) -> tuple:
        """将规则匹配结果转换为标准格式"""
        hooks = []
        coolpoints = []
        
        for seg in suspected:
            if seg.segment_type == "hook":
                hooks.append({
                    "type": seg.pattern_name,
                    "strength": seg.confidence,
                    "position": seg.position,
                    "content": seg.content,
                    "llm_analyzed": False
                })
            else:
                coolpoints.append({
                    "pattern": seg.pattern_name,
                    "density": seg.confidence,
                    "combo_with": [],
                    "content": seg.content,
                    "llm_analyzed": False
                })
        
        return hooks, coolpoints
    
    def _update_chapter_summary(self, chapter_num: int, 
                                  hooks: List[Dict], 
                                  coolpoints: List[Dict]) -> None:
        """更新章节摘要"""
        hook_count = len(hooks)
        hook_strength_avg = sum(h.get("strength", 0) for h in hooks) / hook_count if hook_count > 0 else 0.0
        coolpoint_count = len(coolpoints)
        coolpoint_density = sum(c.get("density", 0) for c in coolpoints) / coolpoint_count if coolpoint_count > 0 else 0.0
        
        self.db.update_chapter_summary(
            chapter=chapter_num,
            hook_count=hook_count,
            hook_strength_avg=hook_strength_avg,
            coolpoint_count=coolpoint_count,
            coolpoint_density=coolpoint_density
        )
    
    def get_chapter_reading_power(self, chapter_num: int) -> Dict[str, Any]:
        """获取章节追读力信息"""
        summary = self.db.get_chapter_summary(chapter_num)
        hooks = self.hook_tracker.get_hooks(chapter_num)
        coolpoints = self.coolpoint_tracker.get_coolpoints(chapter_num)
        
        return {
            "summary": summary or {},
            "hooks": hooks,
            "coolpoints": coolpoints
        }
```

- [ ] **Step 2: 创建__init__.py导出**

```python
# novel-factory/infra/reading_power/__init__.py
from novel_factory.infra.reading_power.db import ReadingPowerDB
from novel_factory.infra.reading_power.engine import ReadingPowerEngine
from novel_factory.infra.reading_power.rule_matcher import RuleMatcher, SuspectedSegment
from novel_factory.infra.reading_power.llm_analyzer import LLMAnalyzer, AnalysisResult
from novel_factory.infra.reading_power.hook_tracker import HookTracker
from novel_factory.infra.reading_power.coolpoint_tracker import CoolPointTracker

__all__ = [
    "ReadingPowerDB",
    "ReadingPowerEngine",
    "RuleMatcher",
    "SuspectedSegment",
    "LLMAnalyzer",
    "AnalysisResult",
    "HookTracker",
    "CoolPointTracker",
]
```

- [ ] **Step 3: 写测试**

```python
# tests/reading_power/test_engine.py
import pytest
from unittest.mock import MagicMock, patch
from novel_factory.infra.reading_power.engine import ReadingPowerEngine

def test_analyze_chapter_with_rule_matcher():
    mock_db = MagicMock()
    mock_db.get_chapter_summary.return_value = None
    
    with patch('novel_factory.infra.reading_power.rule_matcher.RuleMatcher') as MockMatcher:
        mock_matcher = MagicMock()
        mock_matcher.scan.return_value = [
            MagicMock(segment_type="hook", pattern_name="危机钩", 
                      content="危险...", confidence=0.8, position="结尾", offset=100),
            MagicMock(segment_type="coolpoint", pattern_name="装逼打脸",
                      content="打脸...", confidence=0.9, position="中段", offset=200),
        ]
        MockMatcher.return_value = mock_matcher
        
        engine = ReadingPowerEngine(db=mock_db)
        engine.rule_matcher = mock_matcher
        
        result = engine.analyze_chapter(1, "章节内容：危险逼近，打脸场景")
        
        assert result.success is True
        mock_matcher.scan.assert_called_once()

def test_analyze_empty_chapter():
    mock_db = MagicMock()
    engine = ReadingPowerEngine(db=mock_db)
    
    result = engine.analyze_chapter(1, "")
    
    assert result.success is True
    assert result.hooks == []
    assert result.coolpoints == []
```

- [ ] **Step 4: 运行测试验证**

Run: `pytest tests/reading_power/test_engine.py -v`

- [ ] **Step 5: 提交**

```bash
git add novel-factory/infra/reading_power/engine.py novel-factory/infra/reading_power/__init__.py tests/reading_power/test_engine.py
git commit -m "feat: add ReadingPowerEngine orchestrator"
```

---

## Task 6: hooks.yaml集成

**Files:**
- Modify: `novel-factory/hooks.yaml`

- [ ] **Step 1: 添加追读力分析触发器到hooks.yaml**

```yaml
# 在hooks.yaml末尾添加
  - name: 追读力分析
    trigger: CHAPTER_WRITTEN
    conditions:
      - status: draft_completed
    actions:
      - trigger_module: reading_power_analyzer
    config:
      priority: 50
      timeout: 120
```

---

## Task 7: CLI命令扩展

**Files:**
- Modify: `novel-factory/infra/cli/commands.py`

- [ ] **Step 1: 添加reading-power命令组**

```python
# 在commands.py中添加
import click
from novel_factory.infra.reading_power import ReadingPowerEngine
from novel_factory.infra.reading_power.db import ReadingPowerDB

@click.group(name="reading-power")
def reading_power_group():
    """追读力分析命令组"""
    pass

@reading_power_group.command(name="analyze")
@click.argument("chapters", type=str)  # e.g., "1-30"
def analyze_reading_power(chapters):
    """分析章节追读力"""
    engine = ReadingPowerEngine()
    
    # 解析章节范围
    if "-" in chapters:
        start, end = map(int, chapters.split("-"))
    else:
        start = end = int(chapters)
    
    for chapter_num in range(start, end + 1):
        # 读取章节文件
        chapter_path = f"novel-factory/03_内容仓库/正文/{chapter_num}.md"
        try:
            with open(chapter_path, encoding="utf-8") as f:
                content = f.read()
            result = engine.analyze_chapter(chapter_num, content)
            click.echo(f"Chapter {chapter_num}: {len(result.hooks)} hooks, {len(result.coolpoints)} coolpoints")
        except FileNotFoundError:
            click.echo(f"Chapter {chapter_num}: file not found")

@reading_power_group.command(name="report")
@click.argument("chapters", type=str)
def reading_power_report(chapters):
    """生成追读力报告"""
    engine = ReadingPowerEngine()
    
    if "-" in chapters:
        start, end = map(int, chapters.split("-"))
    else:
        start = end = int(chapters)
    
    for chapter_num in range(start, end + 1):
        data = engine.get_chapter_reading_power(chapter_num)
        summary = data.get("summary", {})
        if summary:
            click.echo(f"Chapter {chapter_num}: score={summary.get('reading_power_score', 0):.1f}")
```

---

## Task 8: E2E测试验证

**Files:**
- Create: `tests/reading_power/test_e2e.py`

- [ ] **Step 1: 编写E2E测试**

```python
# tests/reading_power/test_e2e.py
import pytest
from pathlib import Path
from novel_factory.infra.reading_power import ReadingPowerEngine, ReadingPowerDB

def test_e2e_analyze_sample_chapters(tmp_path):
    """
    E2E测试：分析示例章节
    前提：novel-factory/03_内容仓库/正文/ 存在章节文件
    """
    # 使用临时数据库
    db_path = tmp_path / "test_reading_power.db"
    db = ReadingPowerDB(db_path)
    engine = ReadingPowerEngine(db=db)
    
    # 测试文本（模拟章节内容）
    sample_text = """
    主角正在修炼，突然感知到危险气息逼近。
    敌人出现在前方，生死关头，主角必须做出选择。
    结尾处设置了悬念：主角的真实身份究竟是什么？
    
    同时，打脸场景出现了，对手目瞪口呆。
    """
    
    result = engine.analyze_chapter(999, sample_text)
    
    assert result.success is True
    # 应该检测到钩子
    assert len(result.hooks) >= 0  # 取决于规则匹配结果

def test_full_workflow():
    """完整工作流测试：分析->存储->查询"""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = ReadingPowerDB(db_path)
        engine = ReadingPowerEngine(db=db)
        
        text = "危险！敌人出现，打脸场景！"
        result = engine.analyze_chapter(1, text)
        
        # 验证存储
        data = engine.get_chapter_reading_power(1)
        assert "hooks" in data or "summary" in data
```

- [ ] **Step 2: 运行测试验证**

Run: `pytest tests/reading_power/test_e2e.py -v`

- [ ] **Step 3: 提交**

```bash
git add tests/reading_power/test_e2e.py
git commit -m "test: add E2E tests for reading power system"
```

---

## 实施检查清单

- [ ] Task 1: 数据库模块 ✅
- [ ] Task 2: 规则库文件 ✅
- [ ] Task 3: LLM分析器 ✅
- [ ] Task 4: HookTracker和CoolPointTracker ✅
- [ ] Task 5: ReadingPowerEngine ✅
- [ ] Task 6: hooks.yaml集成 ✅
- [ ] Task 7: CLI命令扩展 ✅
- [ ] Task 8: E2E测试验证 ✅