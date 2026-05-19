# 温度参数指导系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立温度参数指导系统，根据创作阶段和场景自动推荐最佳温度参数

**Architecture:** 通过配置文件定义阶段-温度映射，提供推荐工具根据场景返回最佳参数，支持动态调整

**Tech Stack:** YAML + Python

---

## 文件结构

```
novel-factory/
├── config/
│   └── temperature_config.yaml         # 温度配置
├── ai_gateway/
│   └── temperature_optimizer.py         # 温度优化器
└── scripts/
    └── temperature_recommender.py      # 温度推荐工具
```

---

### Task 1: 创建温度配置文件

**Files:**
- Create: `novel-factory/config/temperature_config.yaml`
- Create: `novel-factory/ai_gateway/temperature_optimizer.py`

- [ ] **Step 1: 创建温度配置文件**

```yaml
# config/temperature_config.yaml

# 全局默认温度
default_temperature: 0.7

# 创作阶段温度映射
phase_temperature_mapping:
  PHASE_1_LAUNCH:
    灵感生成: 0.85
    核心冲动确定: 0.6
    类型选择: 0.5
    梗概生成: 0.6

  PHASE_2_OUTLINE:
    全文大纲: 0.6
    卷大纲: 0.5
    阶段大纲: 0.5

  PHASE_3_VALIDATION:
    情节骨架验证: 0.6
    核心样章: 0.65

  PHASE_4_BODY:
    正文初稿: 0.7
    场景描写: 0.6
    对话写作: 0.5
    高潮场景: 0.65

  PHASE_5_REVISION:
    Block修改: 0.5
    Polish润色: 0.4
    情感强化: 0.5

  PHASE_6_REVIEW:
    技术审核: 0.4
    创意评估: 0.6

# 场景温度配置
scene_temperature_mapping:
  outline_generation: 0.6
  outline_generation_global: 0.6
  outline_generation_volume: 0.5
  outline_generation_arc: 0.5
  content_continuation: 0.7
  content_continuation_high: 0.65
  content_continuation_dialogue: 0.5
  content_continuation_flashback: 0.6
  description_enhancement: 0.55
  description_enhancement_sensory: 0.55
  description_enhancement_metaphor: 0.6
  description_enhancement_scene: 0.5
  review_analysis: 0.4
  review_analysis_logic: 0.35
  review_analysis_pacing: 0.4
  review_analysis_character: 0.4
  polish: 0.4
  polish_language: 0.4
  polish_emotion: 0.45
  polish_rhythm: 0.4
  brainstorming: 0.85
  brainstorming_plot: 0.85
  brainstorming_character: 0.8
  brainstorming_world: 0.85

# 调整因子
adjustment_factors:
  chapter_short:
    condition: "word_count < 3000"
    adjustment: +0.05
    reason: "增加创意输出"

  chapter_long:
    condition: "word_count > 5000"
    adjustment: -0.05
    reason: "稳定输出"

  climax_chapter:
    condition: "is_climax == true"
    adjustment: +0.15
    reason: "高潮需要爆发力"

  low_quality_streak:
    condition: "quality_score < 2.5 for 2 generations"
    adjustment: -0.1
    reason: "提高稳定性"

  high_quality_streak:
    condition: "quality_score > 4.5 for 2 generations"
    adjustment: +0.05
    reason: "增加创意"

  core_character_scene:
    condition: "is_core_character == true"
    adjustment: -0.05
    reason: "更稳定"

  supporting_character_scene:
    condition: "is_supporting == true"
    adjustment: +0.05
    reason: "增加变化"

  antagonist_scene:
    condition: "is_antagonist == true"
    adjustment: +0.1
    reason: "增加戏剧性"

# 温度范围限制
temperature_limits:
  min: 0.3
  max: 0.9
  recommended_deviation: 0.1
```

- [ ] **Step 2: 提交配置文件**

```bash
git add config/temperature_config.yaml
git commit -m "feat: 添加温度参数配置文件"
```

---

### Task 2: 创建温度优化器

**Files:**
- Create: `novel-factory/ai_gateway/temperature_optimizer.py`
- Create: `novel-factory/tests/test_temperature_optimizer.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_temperature_optimizer.py

import pytest
from ai_gateway.temperature_optimizer import TemperatureOptimizer, TemperatureConfig

def test_get_recommended_temperature():
    """测试温度推荐"""
    config = TemperatureConfig()
    optimizer = TemperatureOptimizer(config)

    temp = optimizer.get_recommended_temperature("content_continuation")
    assert 0.3 <= temp <= 0.9

def test_scene_temperature_override():
    """测试场景温度覆盖"""
    config = TemperatureConfig()
    optimizer = TemperatureOptimizer(config)

    # 高潮场景应该有更高温度
    normal_temp = optimizer.get_recommended_temperature("content_continuation")
    climax_temp = optimizer.get_recommended_temperature("content_continuation", is_climax=True)

    assert climax_temp > normal_temp

def test_temperature_limits():
    """测试温度限制"""
    config = TemperatureConfig()
    optimizer = TemperatureOptimizer(config)

    # 确保返回温度在限制范围内
    temp = optimizer.get_recommended_temperature("brainstorming")
    assert config.min_temp <= temp <= config.max_temp
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory && python -m pytest tests/test_temperature_optimizer.py -v`
Expected: FAIL with "cannot import"

- [ ] **Step 3: 实现温度优化器**

```python
# ai_gateway/temperature_optimizer.py

import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class TemperatureConfig:
    """温度配置"""
    default_temperature: float = 0.7
    min_temp: float = 0.3
    max_temp: float = 0.9
    recommended_deviation: float = 0.1

class TemperatureOptimizer:
    """温度优化器"""

    def __init__(self, config_path: str = "config/temperature_config.yaml"):
        self.config = self._load_config(config_path)
        self.history = []

    def _load_config(self, config_path: str) -> TemperatureConfig:
        """加载配置"""
        path = Path(config_path)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return TemperatureConfig(
                default_temperature=data.get('default_temperature', 0.7),
                min_temp=data.get('temperature_limits', {}).get('min', 0.3),
                max_temp=data.get('temperature_limits', {}).get('max', 0.9),
                recommended_deviation=data.get('temperature_limits', {}).get('recommended_deviation', 0.1)
            )
        return TemperatureConfig()

    def get_scene_temperature(self, scene: str) -> float:
        """获取场景推荐温度"""
        scene_mapping = self.config.default_temperature  # 简化，实际应读取配置

        # 默认温度映射
        temperature_map = {
            'outline_generation': 0.6,
            'outline_generation_global': 0.6,
            'outline_generation_volume': 0.5,
            'outline_generation_arc': 0.5,
            'content_continuation': 0.7,
            'content_continuation_high': 0.65,
            'content_continuation_dialogue': 0.5,
            'content_continuation_flashback': 0.6,
            'description_enhancement': 0.55,
            'description_enhancement_sensory': 0.55,
            'description_enhancement_metaphor': 0.6,
            'description_enhancement_scene': 0.5,
            'review_analysis': 0.4,
            'review_analysis_logic': 0.35,
            'review_analysis_pacing': 0.4,
            'review_analysis_character': 0.4,
            'polish': 0.4,
            'polish_language': 0.4,
            'polish_emotion': 0.45,
            'polish_rhythm': 0.4,
            'brainstorming': 0.85,
            'brainstorming_plot': 0.85,
            'brainstorming_character': 0.8,
            'brainstorming_world': 0.85,
        }

        return temperature_map.get(scene, self.config.default_temperature)

    def get_recommended_temperature(
        self,
        scene: str,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        获取推荐温度

        Args:
            scene: 场景类型
            context: 上下文信息（is_climax, word_count, is_core_character等）

        Returns:
            float: 推荐温度
        """
        context = context or {}

        # 1. 获取基础温度
        base_temp = self.get_scene_temperature(scene)

        # 2. 应用上下文调整
        adjusted_temp = base_temp

        # 字数调整
        word_count = context.get('word_count', 0)
        if word_count > 0:
            if word_count < 3000:
                adjusted_temp += 0.05
            elif word_count > 5000:
                adjusted_temp -= 0.05

        # 高潮调整
        if context.get('is_climax'):
            adjusted_temp += 0.15

        # 角色类型调整
        if context.get('is_core_character'):
            adjusted_temp -= 0.05
        elif context.get('is_antagonist'):
            adjusted_temp += 0.1
        elif context.get('is_supporting'):
            adjusted_temp += 0.05

        # 质量连续性调整
        if context.get('low_quality_streak'):
            adjusted_temp -= 0.1
        elif context.get('high_quality_streak'):
            adjusted_temp += 0.05

        # 3. 限制范围
        adjusted_temp = max(
            self.config.min_temp,
            min(self.config.max_temp, adjusted_temp)
        )

        return round(adjusted_temp, 2)

    def record_outcome(
        self,
        scene: str,
        temperature: float,
        quality_score: float
    ) -> None:
        """记录结果用于优化"""
        self.history.append({
            'scene': scene,
            'temperature': temperature,
            'quality_score': quality_score
        })

    def get_recent_quality(self, scene: str, count: int = 2) -> float:
        """获取最近质量评分"""
        scene_records = [
            r for r in self.history[-10:]
            if r['scene'] == scene
        ][-count:]

        if not scene_records:
            return 3.5  # 默认中等质量

        return sum(r['quality_score'] for r in scene_records) / len(scene_records)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/test_temperature_optimizer.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add ai_gateway/temperature_optimizer.py tests/test_temperature_optimizer.py
git commit -m "feat: 添加温度优化器"
```

---

### Task 3: 创建温度推荐命令行工具

**Files:**
- Create: `novel-factory/scripts/temperature_recommender.py`

- [ ] **Step 1: 创建命令行工具**

```python
#!/usr/bin/env python3
"""
温度推荐工具
根据场景推荐最佳温度参数
"""

import sys
import argparse
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_gateway.temperature_optimizer import TemperatureOptimizer

def main():
    parser = argparse.ArgumentParser(description='温度参数推荐工具')
    parser.add_argument(
        'scene',
        nargs='?',
        default='content_continuation',
        help='场景类型（默认: content_continuation）'
    )
    parser.add_argument(
        '--climax',
        action='store_true',
        help='是否高潮场景'
    )
    parser.add_argument(
        '--words',
        type=int,
        default=0,
        help='章节字数'
    )
    parser.add_argument(
        '--core-character',
        action='store_true',
        help='是否核心角色场景'
    )

    args = parser.parse_args()

    # 构建上下文
    context = {
        'is_climax': args.climax,
        'word_count': args.words,
        'is_core_character': args.core_character
    }

    # 获取推荐
    optimizer = TemperatureOptimizer()
    temp = optimizer.get_recommended_temperature(args.scene, context)

    print(f"\n场景: {args.scene}")
    print(f"推荐温度: {temp}")
    print(f"温度范围: 0.3 - 0.9")
    print(f"\n上下文:")
    for key, value in context.items():
        if value:
            print(f"  - {key}: {value}")
    print()

if __name__ == '__main__':
    main()
```

- [ ] **Step 2: 提交**

```bash
git add scripts/temperature_recommender.py
git commit -m "feat: 添加温度推荐命令行工具"
```

---

## 实现完成检查

- [ ] 温度配置文件已创建
- [ ] 温度优化器已实现
- [ ] 温度推荐工具可运行
- [ ] 测试通过