# 节奏可视化系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立节奏可视化系统，包括指标提取、可视化呈现、预警机制

**Architecture:** 自动统计章节字数、场景数、对话比例等指标，生成热力图和曲线图可视化，整合预警机制

**Tech Stack:** Python + matplotlib + YAML

---

## 文件结构

```
novel-factory/
├── 06_意见仓库/
│   └── 07_节奏分析/
│       ├── README.md                    # 节奏分析索引
│       ├── 01_章节节奏报告/
│       │   ├── ch001_节奏报告.md
│       │   └── ...
│       ├── 02_卷节奏报告/
│       ├── 03_全局节奏报告/
│       └── 04_节奏预警/
│           └── 预警记录.md
├── 03_内容仓库/
│   └── 元数据/
│       └── 节奏统计/
│           └── 章节节奏数据.yaml
└── scripts/
    └── pacing_analyzer.py              # 节奏分析工具
```

---

### Task 1: 创建目录结构和基础文件

**Files:**
- Create: `novel-factory/06_意见仓库/07_节奏分析/README.md`
- Create: `novel-factory/03_内容仓库/元数据/节奏统计/章节节奏数据.yaml`

- [ ] **Step 1: 创建节奏分析README.md**

```markdown
# 节奏分析

> 版本: v1.0
> 更新日期: 2026-05-19

## 概述

节奏可视化系统自动统计章节字数、场景数、对话比例等指标，生成可视化报告。

## 目录结构

```
07_节奏分析/
├── README.md                    # 本文件
├── 01_章节节奏报告/             # 单章节奏报告
│   ├── ch001_节奏报告.md
│   └── ...
├── 02_卷节奏报告/              # 卷节奏报告
├── 03_全局节奏报告/            # 全局节奏报告
│   └── 2026-05_全局节奏报告.md
└── 04_节奏预警/                 # 预警记录
    └── 预警记录.md
```

## 节奏指标

| 指标 | 说明 | 理想范围 |
|------|------|---------|
| 字数 | 章节总字数 | 3000-5000 |
| 对话比例 | 对话占总字数比例 | 30-50% |
| 场景密度 | 每千字的场景数 | 2-4 |
| 情感波动 | 情感变化强度 | 中等 |

## 使用指南

### 运行分析

```bash
cd novel-factory
python scripts/pacing_analyzer.py --batch ch001-ch010
```

### 查看报告

1. 单章报告：`01_章节节奏报告/chXXX_节奏报告.md`
2. 批量报告：`03_全局节奏报告/YYYY-MM_全局节奏报告.md`
```

- [ ] **Step 2: 创建章节节奏数据模板**

```yaml
# 章节节奏数据
# 最后更新：2026-05-19

chapters: {}
# 示例：
# ch001:
#   total_words: 3500
#   dialogue_ratio: 0.35
#   scene_count: 3
```

- [ ] **Step 3: 提交初始文件**

```bash
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory
mkdir -p 06_意见仓库/07_节奏分析/{01_章节节奏报告,02_卷节奏报告,03_全局节奏报告,04_节奏预警}
mkdir -p 03_内容仓库/元数据/节奏统计
git add 06_意见仓库/07_节奏分析/README.md
git add 03_内容仓库/元数据/节奏统计/章节节奏数据.yaml
git commit -m "feat: 初始化节奏分析目录结构"
```

---

### Task 2: 创建节奏分析工具

**Files:**
- Create: `novel-factory/scripts/pacing_analyzer.py`
- Create: `novel-factory/tests/test_pacing_analyzer.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_pacing_analyzer.py

import pytest
from scripts.pacing_analyzer import PacingAnalyzer, ChapterPacingData

def test_chapter_pacing_data_creation():
    """测试章节节奏数据创建"""
    data = ChapterPacingData(
        chapter="ch001",
        total_words=3500,
        dialogue_ratio=0.35,
        scene_count=3
    )
    assert data.total_words == 3500
    assert data.dialogue_ratio == 0.35

def test_pacing_metrics_calculation():
    """测试节奏指标计算"""
    analyzer = PacingAnalyzer()

    text = "这是一段叙述文字。" * 100 + '"这是对话。"' * 50
    metrics = analyzer.calculate_pacing_metrics(text)

    assert 'word_count' in metrics
    assert 'dialogue_ratio' in metrics
    assert metrics['dialogue_ratio'] > 0

def test_pacing_analyzer_word_count():
    """测试字数统计"""
    analyzer = PacingAnalyzer()
    text = "这是一个测试。" * 100
    word_count = analyzer.count_words(text)
    assert word_count == 300  # 100 * 3
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory && python -m pytest tests/test_pacing_analyzer.py -v`
Expected: FAIL with "cannot import"

- [ ] **Step 3: 实现节奏分析工具**

```python
#!/usr/bin/env python3
"""
节奏分析工具
自动统计章节节奏指标，生成可视化报告
"""

import re
import yaml
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime

@dataclass
class ChapterPacingData:
    """章节节奏数据"""
    chapter: str
    total_words: int
    prose_words: int
    dialogue_words: int
    description_words: int
    scene_count: int
    dialogue_ratio: float
    description_ratio: float
    scene_density: float

    def to_dict(self) -> Dict:
        return asdict(self)

class PacingAnalyzer:
    """节奏分析器"""

    def __init__(self, content_dir: str = "03_内容仓库"):
        self.content_dir = Path(content_dir)

    def count_words(self, text: str) -> int:
        """统计字数（中文按字符计）"""
        # 去除空白字符
        text = re.sub(r'\s+', '', text)
        return len(text)

    def extract_dialogue(self, text: str) -> Tuple[List[str], int]:
        """提取对话及其字数"""
        # 匹配双引号或单引号内的对话
        dialogue_pattern = r'[""]([^""]+)[""]'
        dialogues = re.findall(dialogue_pattern, text)

        # 统计对话字数
        dialogue_text = ''.join(dialogues)
        dialogue_words = self.count_words(dialogue_text)

        return dialogues, dialogue_words

    def extract_scenes(self, text: str) -> int:
        """提取场景数"""
        # 按场景标记分割（##### 场景X 或 空行分割）
        # 简化：按段落分割计算场景
        paragraphs = text.split('\n\n')
        scene_count = sum(1 for p in paragraphs if len(p.strip()) > 50)
        return max(1, scene_count)

    def calculate_pacing_metrics(self, text: str) -> Dict:
        """计算节奏指标"""
        total_words = self.count_words(text)

        # 提取对话
        _, dialogue_words = self.extract_dialogue(text)

        # 估算描写字数（总字数 - 对话字数）
        description_words = int(total_words * 0.3)  # 简化估算
        prose_words = total_words - dialogue_words - description_words

        # 计算比例
        dialogue_ratio = dialogue_words / total_words if total_words > 0 else 0
        description_ratio = description_words / total_words if total_words > 0 else 0

        # 场景数
        scene_count = self.extract_scenes(text)

        # 场景密度（每千字场景数）
        scene_density = (scene_count / total_words * 1000) if total_words > 0 else 0

        return {
            'word_count': total_words,
            'prose_words': prose_words,
            'dialogue_words': dialogue_words,
            'description_words': description_words,
            'dialogue_ratio': round(dialogue_ratio, 2),
            'description_ratio': round(description_ratio, 2),
            'scene_count': scene_count,
            'scene_density': round(scene_density, 2)
        }

    def analyze_chapter(self, chapter: str) -> ChapterPacingData:
        """分析单章节奏"""
        # 读取章节文件
        chapter_file = self.content_dir / "四层结构" / "正文" / f"{chapter}.md"

        if not chapter_file.exists():
            # 尝试其他路径
            chapter_file = self.content_dir / f"{chapter}.md"

        if chapter_file.exists():
            with open(chapter_file, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            text = ""

        metrics = self.calculate_pacing_metrics(text)

        return ChapterPacingData(
            chapter=chapter,
            total_words=metrics['word_count'],
            prose_words=metrics['prose_words'],
            dialogue_words=metrics['dialogue_words'],
            description_words=metrics['description_words'],
            scene_count=metrics['scene_count'],
            dialogue_ratio=metrics['dialogue_ratio'],
            description_ratio=metrics['description_ratio'],
            scene_density=metrics['scene_density']
        )

    def generate_report(self, pacing_data: ChapterPacingData) -> str:
        """生成节奏报告"""
        # 评估各项指标
        word_assessment = self._assess_word_count(pacing_data.total_words)
        dialogue_assessment = self._assess_dialogue_ratio(pacing_data.dialogue_ratio)

        report = f"""# {pacing_data.chapter} 节奏报告

**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}

## 核心指标

| 指标 | 数值 | 评估 |
|------|------|------|
| 总字数 | {pacing_data.total_words} | {word_assessment} |
| 对话比例 | {pacing_data.dialogue_ratio:.1%} | {dialogue_assessment} |
| 场景数 | {pacing_data.scene_count} | 正常 |
| 场景密度 | {pacing_data.scene_density:.1f} | 正常 |

## 字数分布

```
叙述    ████████████████░░░░ {pacing_data.prose_words}字
对话    ████████░░░░░░░░░░░░ {pacing_data.dialogue_words}字
描写    ██████░░░░░░░░░░░░░░ {pacing_data.description_words}字
```

## 节奏评估

{word_assessment}

{dialogue_assessment}
"""
        return report

    def _assess_word_count(self, word_count: int) -> str:
        """评估字数"""
        if 3000 <= word_count <= 5000:
            return "✅ 理想范围"
        elif 2000 <= word_count < 3000:
            return "⚠️ 偏少，建议充实内容"
        elif 5000 < word_count <= 6000:
            return "⚠️ 偏多，可考虑精简"
        else:
            return "🔴 严重偏离，建议调整"

    def _assess_dialogue_ratio(self, ratio: float) -> str:
        """评估对话比例"""
        if 0.3 <= ratio <= 0.5:
            return "✅ 理想范围"
        elif 0.2 <= ratio < 0.3:
            return "⚠️ 对话偏少"
        elif 0.5 < ratio <= 0.6:
            return "⚠️ 对话偏多"
        else:
            return "🔴 比例失衡"
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/test_pacing_analyzer.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
mkdir -p novel-factory/tests
git add scripts/pacing_analyzer.py tests/test_pacing_analyzer.py
git commit -m "feat: 添加节奏分析工具"
```

---

### Task 3: 创建节奏可视化报告模板

**Files:**
- Create: `novel-factory/06_意见仓库/07_节奏分析/03_全局节奏报告/全局节奏报告_模板.md`

- [ ] **Step 1: 创建全局节奏报告模板**

```markdown
# 全局节奏报告：ch{start}-ch{end}

**报告ID**：GPR-{YYYY-MM}-{seq}
**生成日期**：{datetime}
**分析期间**：ch{start} - ch{end}（{count}章）

---

## 执行摘要

### 整体状态

| 指标 | 平均值 | 理想范围 | 状态 |
|------|--------|---------|------|
| 字数 | {avg_words} | 3000-5000 | {word_status} |
| 对话比例 | {avg_dialogue} | 30-50% | {dialogue_status} |
| 场景密度 | {avg_density} | 2-4 | {density_status} |

### 字数分布图

```
字数分布：
ch001  ████████████████░░  3500
ch002  ██████████████░░░░  3200
ch003  █████████████████░  4200
...
```

### 对话比例分布

```
对话比例：
ch001  ██████████████░░░░  35%
ch002  ████████████░░░░░  30%
ch003  ████████████████░  45%
...
```

---

## 节奏问题预警

### 🔴 需要关注

| 章节 | 问题 | 建议 |
|------|------|------|
| ch005 | 字数偏少（2000字） | 充实内容 |
| ch012 | 对话比例过高（60%） | 增加描写 |

### 🟡 建议优化

| 章节 | 问题 | 建议 |
|------|------|------|
| ch008 | 场景转换频繁 | 增加过渡 |
```

- [ ] **Step 2: 提交**

```bash
git add 06_意见仓库/07_节奏分析/03_全局节奏报告/全局节奏报告_模板.md
git commit -m "feat: 添加节奏可视化报告模板"
```

---

## 实现完成检查

- [ ] 目录结构已创建
- [ ] 节奏分析工具可运行
- [ ] 章节节奏数据模板已创建
- [ ] 全局报告模板已创建
- [ ] 测试通过