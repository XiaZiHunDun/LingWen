# 角色一致性检查系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立角色一致性检查系统，包括特征关键词库、一致性检查引擎、可视化报告

**Architecture:** 采用目录结构管理角色特征库，通过检查引擎自动检测角色一致性偏差，生成可视化报告整合到审核流程

**Tech Stack:** Markdown + YAML + Python脚本

---

## 文件结构

```
novel-factory/
├── 02_作家工作室/作家主编/角色特征库/
│   ├── README.md                    # 特征库索引
│   ├── 00_角色索引.yaml             # 角色清单
│   ├── 01_林夜/
│   │   ├── 基础信息.yaml
│   │   ├── 语言风格.yaml
│   │   ├── 行为模式.yaml
│   │   ├── 情感曲线.yaml
│   │   └── 一致性基准.md
│   ├── 02_苏琳/
│   │   └── ...
│   └── 03_暗皇/
│       └── ...
├── 06_意见仓库/
│   └── 06_角色一致性/
│       ├── README.md
│       └── 检查报告_chXXX-chYYY.md
└── scripts/
    └── character_consistency_checker.py  # 一致性检查工具
```

---

### Task 1: 创建目录结构和基础文件

**Files:**
- Create: `novel-factory/02_作家工作室/作家主编/角色特征库/README.md`
- Create: `novel-factory/02_作家工作室/作家主编/角色特征库/00_角色索引.yaml`
- Create: `novel-factory/06_意见仓库/06_角色一致性/README.md`

- [ ] **Step 1: 创建角色特征库README.md**

```markdown
# 角色特征库

> 版本: v1.0
> 更新日期: 2026-05-19

## 概述

角色特征库用于结构化存储角色语言、行为、情感特征，为一致性检查提供基准数据。

## 目录结构

```
角色特征库/
├── 00_角色索引.yaml    # 角色清单索引
├── 01_林夜/           # 林夜角色特征
│   ├── 基础信息.yaml
│   ├── 语言风格.yaml
│   ├── 行为模式.yaml
│   ├── 情感曲线.yaml
│   └── 一致性基准.md
├── 02_苏琳/           # 苏琳角色特征
└── 03_暗皇/           # 暗皇角色特征
```

## 角色列表

| 角色ID | 角色名 | 重要性 | 状态 |
|--------|--------|--------|------|
| C001 | 林夜 | core | 已建立 |
| C002 | 苏琳 | core | 已建立 |
| C003 | 暗皇 | supporting | 已建立 |

## 使用指南

### 创建新角色特征

1. 在`00_角色索引.yaml`中添加角色条目
2. 创建角色目录
3. 按模板创建各维度文件
4. 更新本文件中的角色列表

### 更新已有角色

1. 修改对应维度的yaml文件
2. 更新`一致性基准.md`中的检查点
3. 记录变更历史
```

- [ ] **Step 2: 创建00_角色索引.yaml**

```yaml
# 角色索引清单
# 最后更新：2026-05-19

characters:
  - character_id: C001
    character_name: 林夜
    importance: core
    role: protagonist
    first_appearance: ch001
    profile_path: 01_林夜
    status: established

  - character_id: C002
    character_name: 苏琳
    importance: core
    role: protagonist
    first_appearance: ch003
    profile_path: 02_苏琳
    status: established

  - character_id: C003
    character_name: 暗皇
    importance: supporting
    role: antagonist
    first_appearance: ch015
    profile_path: 03_暗皇
    status: established

total_count: 3
```

- [ ] **Step 3: 创建06_角色一致性README.md**

```markdown
# 角色一致性检查

> 版本: v1.0
> 更新日期: 2026-05-19

## 概述

角色一致性检查系统自动检测角色在小说中的语言、行为、情感是否与设定一致。

## 目录结构

```
06_角色一致性/
├── README.md                    # 本文件
├── 检查报告_ch001-ch010.md      # 批次检查报告
├── 检查报告_ch011-ch020.md
└── ...
```

## 检查维度

| 维度 | 说明 | 权重 |
|------|------|------|
| 语言一致性 | 词汇、句式、语气是否符合角色设定 | 30% |
| 行为一致性 | 决策模式、冲突应对是否合理 | 30% |
| 情感一致性 | 情感状态变化是否连贯 | 25% |
| 能力一致性 | 力量表现是否与等级匹配 | 15% |

## 评分标准

| 分档 | 分数 | 措施 |
|------|------|------|
| 优秀 | 4.5-5.0 | 无需修改 |
| 良好 | 3.5-4.4 | 轻微润色 |
| 合格 | 2.5-3.4 | 建议修改 |
| 较差 | 1.5-2.4 | 需要修改 |
| 失败 | <1.5 | 结构性失败 |

## SOP

### 运行检查

```bash
cd novel-factory
python scripts/character_consistency_checker.py --batch ch001-ch010
```

### 查看报告

1. 打开`06_意见仓库/06_角色一致性/检查报告_chXXX-chYYY.md`
2. 查看总体评分和各项得分
3. 根据修改建议进行修改
4. 复查后更新报告状态
```

- [ ] **Step 4: 提交初始文件**

```bash
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory
mkdir -p 02_作家工作室/作家主编/角色特征库/{01_林夜,02_苏琳,03_暗皇}
mkdir -p 06_意见仓库/06_角色一致性
git add 02_作家工作室/作家主编/角色特征库/README.md
git add 02_作家工作室/作家主编/角色特征库/00_角色索引.yaml
git add 06_意见仓库/06_角色一致性/README.md
git commit -m "feat: 初始化角色特征库目录结构"
```

---

### Task 2: 创建林夜角色特征库

**Files:**
- Create: `novel-factory/02_作家工作室/作家主编/角色特征库/01_林夜/基础信息.yaml`
- Create: `novel-factory/02_作家工作室/作家主编/角色特征库/01_林夜/语言风格.yaml`
- Create: `novel-factory/02_作家工作室/作家主编/角色特征库/01_林夜/行为模式.yaml`
- Create: `novel-factory/02_作家工作室/作家主编/角色特征库/01_林夜/情感曲线.yaml`
- Create: `novel-factory/02_作家工作室/作家主编/角色特征库/01_林夜/一致性基准.md`

- [ ] **Step 1: 创建林夜基础信息.yaml**

```yaml
# 林夜基础信息
# 最后更新：2026-05-19

character_id: C001
character_name: 林夜

basic_info:
  identity: 修炼者
  role: protagonist
  importance: core
  first_appearance: ch001

  # 人物三角
  character_triangle:
    desire: "变得更强，保护重要的人"
    fear: "失去所爱之人"
    flaw: "过度承担，不信任他人"
    conflict_description: "欲望是保护他人，但过度承担会导致身边人失去依靠；恐惧是失去所爱，但缺陷使他难以信任他人来共同保护"

  # 能力设定
  abilities:
    power_level: "逐步成长，从觉醒初期到问鼎期"
    skill_set:
      - 灵力感知
      - 战斗技巧
      - 意志力
    limitations:
      - 过度消耗
      - 情感羁绊
    power_evolution: "ch001觉醒 → ch020炼体 → ch040筑基 → ch080金丹 → ch100元婴 → ch101+问鼎"

  # 关系网络
  relationships:
    - character_id: C002
      relationship_type: 羁绊
      dynamic_description: "从陌生到相互理解，共同成长"
      current_state: "并肩作战"

    - character_id: C003
      relationship_type: 对立
      dynamic_description: "宿命之敌，理念冲突"
      current_state: "对抗"
```

- [ ] **Step 2: 创建林夜语言风格.yaml**

```yaml
# 林夜语言风格
# 最后更新：2026-05-19

character_id: C001

language_style:
  vocabulary:
    frequently_used:
      - 坚定
      - 守护
      - 责任
      - 必须
      - 变强
      - 不会让
      - 相信
      - 一起

    forbidden_words:
      - 犹豫不决
      - 放弃
      - 无所谓
      - 随便
      - 软弱

    signature_phrases:
      - "我会变得更强"
      - "不会再让任何人失去"
      - "这是我必须承担的"

  sentence_structure:
    typical_length: 中等
    punctuation_pattern: "多使用陈述句，少用问句；战斗场景多用短句"
    dialogue_tags:
      - 说
      - 声音低沉
      - 目光坚定

  tone:
    primary_tone: "坚定、沉稳、有责任感"
    emotional_range:
      - 坚定
      - 压抑
      - 愤怒
      - 温柔
      - 绝望（极少数）
    slang_level: 低
```

- [ ] **Step 3: 创建林夜行为模式.yaml**

```yaml
# 林夜行为模式
# 最后更新：2026-05-19

character_id: C001

behavior_pattern:
  decision_making:
    approach: "基于保护他人的欲望做决策，会权衡但最终选择承担"
    speed: 中
    risk_tolerance: 0.6

  conflict_response:
    initial_reaction: "直面问题，不逃避"
    escalation_pattern: "从不退让到全力反击"
    resolution_preference: "通过战斗解决，但愿意为保护的人暂时妥协"

  social_interaction:
    openness: 0.5
    trust_pattern: "很难信任他人，但对认定的人会完全信任"
    leadership_style: "承担责任，身先士卒"
```

- [ ] **Step 4: 创建林夜情感曲线.yaml**

```yaml
# 林夜情感曲线
# 最后更新：2026-05-19

character_id: C001

emotional_arc:
  baseline_emotion: "迷茫但坚定"
  emotional_range: "从压抑到释放，从迷茫到坚定"

  emotional_triggers:
    positive:
      - 伙伴支持
      - 战斗胜利
      - 力量提升
      - 目标达成
    negative:
      - 失去重要之物
      - 战友受伤
      - 力量不足
      - 被背叛

  growth_trajectory:
    beginning: "迷茫、不自信、过度承担"
    middle: "成长、坚定、学会信任"
    end: "成熟、平静、能够放手"

# 阶段性情感预期
phase_expectations:
  ch001-ch020:
    baseline: "迷茫但坚定"
    expected_changes: "迷茫逐渐减少，坚定逐渐增强"
    emotional_peaks: ["第一次战斗胜利", "伙伴受伤"]

  ch021-ch060:
    baseline: "成长中的自信"
    expected_changes: "自信建立，开始学会信任"
    emotional_peaks: ["重大战斗胜利", "与苏琳深入交流"]

  ch061-ch100:
    baseline: "坚定但脆弱"
    expected_changes: "承担更多，但内心也有挣扎"
    emotional_peaks: ["重大牺牲", "真相揭示"]

  ch101+:
    baseline: "成熟的平静"
    expected_changes: "能够接受失去，但依然守护"
    emotional_peaks: ["最终战斗", "目标达成"]
```

- [ ] **Step 5: 创建林夜一致性基准.md**

```markdown
# 林夜一致性基准

> 最后更新：2026-05-19

## 声音检查点

1. **坚定表达**：林夜的对话应体现坚定感，使用"必须"、"一定"、"不会让"等词汇
2. **责任承担**：面对问题时，林夜的反应是承担责任而非推卸
3. **保护欲**：对他人的安全表现出强烈关注

## 行为检查点

1. **决策模式**：重大决策应基于"保护他人"的欲望
2. **战斗风格**：勇往直前，不轻易撤退
3. **信任问题**：不轻易信任陌生人，但会信任认定的人

## 决策模式

| 场景 | 预期决策 | 一致性检查 |
|------|---------|-----------|
| 面对强敌 | 战斗或战术撤退（不为逃跑） | 是否体现勇气 |
| 伙伴受伤 | 优先保护，可能过度消耗 | 是否体现保护欲 |
| 被质疑 | 坚持自己判断 | 是否体现自信 |
| 需要帮助 | 先尝试独自承担 | 是否体现不信任他人的缺陷 |

## 常见偏离

1. **语言偏离**：使用"犹豫不决"、"随便"等禁用词
2. **行为偏离**：未经思考就撤退、轻易信任陌生人
3. **情感偏离**：过早出现"绝望"情绪（在ch060前）
```

- [ ] **Step 6: 提交林夜特征库**

```bash
git add 02_作家工作室/作家主编/角色特征库/01_林夜/
git commit -m "feat: 添加林夜角色特征库"
```

---

### Task 3: 创建苏琳和暗皇角色特征库

**Files:**
- Create: `novel-factory/02_作家工作室/作家主编/角色特征库/02_苏琳/`下所有文件
- Create: `novel-factory/02_作家工作室/作家主编/角色特征库/03_暗皇/`下所有文件

- [ ] **Step 1: 创建苏琳基础信息.yaml**

```yaml
# 苏琳基础信息
# 最后更新：2026-05-19

character_id: C002
character_name: 苏琳

basic_info:
  identity: 神秘少女
  role: protagonist
  importance: core
  first_appearance: ch003

  character_triangle:
    desire: "寻找真相，了解自己的过去"
    fear: "被揭穿真实身份"
    flaw: "习惯性疏离，难以敞开心扉"
    conflict_description: "欲望驱使她接近林夜，但恐惧和缺陷使她保持距离"

  abilities:
    power_level: "实力神秘，逐步揭示"
    skill_set:
      - 未知能力
      - 空间感知
    limitations: "真实能力受限"
    power_evolution: "ch003神秘 → ch030初显 → ch060部分揭示 → ch100完全揭示"

  relationships:
    - character_id: C001
      relationship_type: 羁绊
      dynamic_description: "从警惕到信任，从疏离到敞开心扉"
      current_state: "信任建立中"
```

- [ ] **Step 2: 创建苏琳语言风格.yaml**

```yaml
# 苏琳语言风格
# 最后更新：2026-05-19

character_id: C002

language_style:
  vocabulary:
    frequently_used:
      - 神秘
      - 观察
      - 沉默
      - 好奇
      - 也许

    forbidden_words:
      - 直接拒绝
      - 热情
      - 主动搭话

    signature_phrases:
      - "这只是巧合"
      - "我不太确定"
      - "你在说什么"

  sentence_structure:
    typical_length: 短到中等
    punctuation_pattern: "多使用问句，表达疑惑或反问"
    dialogue_tags:
      - 轻声说
      - 淡淡道
      - 目光闪烁

  tone:
    primary_tone: "神秘、疏离、带有好奇"
    emotional_range:
      - 疏离
      - 好奇
      - 警惕
      - 温柔（极少数）
    slang_level: 低
```

- [ ] **Step 3: 创建暗皇基础信息.yaml**

```yaml
# 暗皇基础信息
# 最后更新：2026-05-19

character_id: C003
character_name: 暗皇

basic_info:
  identity: 最高存在
  role: antagonist
  importance: supporting
  first_appearance: ch015

  character_triangle:
    desire: "绝对的力量和控制"
    fear: "失去控制权"
    flaw: "傲慢，轻视对手"
    conflict_description: "对力量的追求使他成为对立面，但傲慢也是他的弱点"

  abilities:
    power_level: "超越问鼎期（恒定最高存在）"
    skill_set:
      - 压倒性力量
      - 黑暗力量
    limitations: "傲慢导致的判断失误"
    power_evolution: "恒定"

  relationships:
    - character_id: C001
      relationship_type: 对立
      dynamic_description: "宿命之敌"
      current_state: "对抗"
```

- [ ] **Step 4: 创建暗皇语言风格.yaml**

```yaml
# 暗皇语言风格
# 最后更新：2026-05-19

character_id: C003

language_style:
  vocabulary:
    frequently_used:
      - 力量
      - 蝼蚁
      - 臣服
      - 毁灭
      - 无聊

    forbidden_words:
      - 害怕
      - 请求
      - 也许

    signature_phrases:
      - "就凭你？"
      - "这个世界将属于我"
      - "太弱了"

  sentence_structure:
    typical_length: 短
    punctuation_pattern: "多使用肯定句，命令式"
    dialogue_tags:
      - 冷声道
      - 俯视
      - 淡淡

  tone:
    primary_tone: "傲慢、冷酷、绝对"
    emotional_range:
      - 傲慢
      - 不屑
      - 愤怒（极少数）
      - 无聊
    slang_level: 低
```

- [ ] **Step 5: 提交苏琳和暗皇特征库**

```bash
git add 02_作家工作室/作家主编/角色特征库/02_苏琳/
git add 02_作家工作室/作家主编/角色特征库/03_暗皇/
git commit -m "feat: 添加苏琳和暗皇角色特征库"
```

---

### Task 4: 创建角色一致性检查工具

**Files:**
- Create: `novel-factory/scripts/character_consistency_checker.py`
- Create: `novel-factory/tests/test_character_consistency_checker.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_character_consistency_checker.py

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from character_consistency_checker import (
    CharacterConsistencyChecker,
    LanguageStyleChecker,
    load_character_profile
)

def test_load_character_profile():
    """测试加载角色特征库"""
    profile = load_character_profile('C001')
    assert profile is not None
    assert profile['character_id'] == 'C001'
    assert profile['character_name'] == '林夜'

def test_language_style_checker_vocab_match():
    """测试词汇匹配检查"""
    checker = LanguageStyleChecker()

    profile = {
        'language_style': {
            'vocabulary': {
                'frequently_used': ['坚定', '守护', '变强'],
                'forbidden_words': ['犹豫不决', '放弃']
            }
        }
    }

    # 测试常用词匹配
    text = "他坚定地说：我会变强，保护重要的人"
    match_rate = checker.check_vocab_match(text, profile)
    assert match_rate > 0.5

    # 测试禁用词检测
    text_with_forbidden = "他犹豫不决地放弃了"
    forbidden_count = checker.check_forbidden_words(text_with_forbidden, profile)
    assert forbidden_count == 2

def test_character_consistency_checker_initialization():
    """测试检查器初始化"""
    checker = CharacterConsistencyChecker('02_作家工作室/作家主编/角色特征库')
    assert len(checker.characters) >= 3
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory && python -m pytest tests/test_character_consistency_checker.py -v`
Expected: FAIL with "module not found" or "function not defined"

- [ ] **Step 3: 编写最小实现**

```python
#!/usr/bin/env python3
"""
角色一致性检查工具
自动检测角色一致性偏差
"""

import yaml
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

@dataclass
class ConsistencyScore:
    """一致性评分"""
    overall: float
    language: float
    behavior: float
    emotional: float
    ability: float

    def to_dict(self) -> Dict[str, float]:
        return {
            'overall': self.overall,
            'language': self.language,
            'behavior': self.behavior,
            'emotional': self.emotional,
            'ability': self.ability
        }

class LanguageStyleChecker:
    """语言风格检查器"""

    def check_vocab_match(self, text: str, profile: Dict) -> float:
        """检查词汇匹配率"""
        vocab = profile.get('language_style', {}).get('vocabulary', {})
        frequent_words = vocab.get('frequently_used', [])

        if not frequent_words:
            return 1.0

        match_count = sum(1 for word in frequent_words if word in text)
        return match_count / len(frequent_words)

    def check_forbidden_words(self, text: str, profile: Dict) -> int:
        """检测禁用词出现次数"""
        vocab = profile.get('language_style', {}).get('vocabulary', {})
        forbidden_words = vocab.get('forbidden_words', [])

        return sum(1 for word in forbidden_words if word in text)

    def calculate_language_score(self, text: str, profile: Dict) -> float:
        """计算语言风格一致性分数"""
        vocab_match = self.check_vocab_match(text, profile)
        forbidden_count = self.check_forbidden_words(text, profile)

        # 禁用词扣分
        forbidden_penalty = min(forbidden_count * 0.2, 1.0)

        score = vocab_match * 2.5 - forbidden_penalty * 2.5
        return max(1.0, min(5.0, score))

class CharacterConsistencyChecker:
    """角色一致性检查器"""

    def __init__(self, profile_dir: str):
        self.profile_dir = Path(profile_dir)
        self.characters = self._load_character_index()
        self.language_checker = LanguageStyleChecker()

    def _load_character_index(self) -> Dict[str, Dict]:
        """加载角色索引"""
        index_file = self.profile_dir / '00_角色索引.yaml'
        with open(index_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return {c['character_id']: c for c in data['characters']}

    def load_character_profile(self, character_id: str) -> Optional[Dict]:
        """加载角色特征库"""
        if character_id not in self.characters:
            return None

        char_info = self.characters[character_id]
        profile_path = self.profile_dir / char_info['profile_path']

        profile = {}

        # 加载基础信息
        basic_file = profile_path / '基础信息.yaml'
        if basic_file.exists():
            with open(basic_file, 'r', encoding='utf-8') as f:
                profile.update(yaml.safe_load(f))

        # 加载语言风格
        language_file = profile_path / '语言风格.yaml'
        if language_file.exists():
            with open(language_file, 'r', encoding='utf-8') as f:
                profile['language_style'] = yaml.safe_load(f).get('language_style', {})

        return profile

    def check_chapter(self, chapter_text: str, character_id: str) -> ConsistencyScore:
        """检查单章角色一致性"""
        profile = self.load_character_profile(character_id)

        if not profile:
            return ConsistencyScore(1.0, 1.0, 1.0, 1.0, 1.0)

        # 语言风格检查
        language_score = self.language_checker.calculate_language_score(
            chapter_text, profile
        )

        return ConsistencyScore(
            overall=language_score,
            language=language_score,
            behavior=3.5,
            emotional=3.5,
            ability=3.5
        )

def load_character_profile(character_id: str) -> Optional[Dict]:
    """便捷函数：加载角色特征"""
    checker = CharacterConsistencyChecker(
        '02_作家工作室/作家主编/角色特征库'
    )
    return checker.load_character_profile(character_id)

if __name__ == '__main__':
    checker = CharacterConsistencyChecker(
        '02_作家工作室/作家主编/角色特征库'
    )

    # 测试加载
    profile = checker.load_character_profile('C001')
    print(f"已加载角色: {profile['character_name']}")

    # 测试检查
    test_text = "他坚定地说：我会变强，保护重要的人。这是我的责任。"
    score = checker.check_chapter(test_text, 'C001')
    print(f"一致性评分: {score.overall:.2f}")
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/test_character_consistency_checker.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
mkdir -p novel-factory/tests
git add scripts/character_consistency_checker.py tests/test_character_consistency_checker.py
git commit -m "feat: 添加角色一致性检查工具"
```

---

### Task 5: 创建一致性报告模板

**Files:**
- Create: `novel-factory/06_意见仓库/06_角色一致性/检查报告_模板.md`

- [ ] **Step 1: 创建检查报告模板**

```markdown
# 角色一致性检查报告

**报告ID**：CCR-{YYYY-MM}-{seq}
**检查期间**：ch{start}-ch{end}
**生成日期**：{datetime}

---

## 执行摘要

### 总体评分

```
一致性指数：■■■■□□  {score}/5
语言一致性：■■■■■□  {language_score}/5
行为一致性：■■■■□□  {behavior_score}/5
情感一致性：■■■■□□  {emotional_score}/5
能力一致性：■■■■■□  {ability_score}/5
```

### 问题统计

| 严重程度 | 数量 | 说明 |
|---------|------|------|
| 🔴 严重 | {critical_count} | 需立即修改 |
| 🟡 重要 | {major_count} | 应当修改 |
| 🟢 次要 | {minor_count} | 建议修改 |

---

## 详细检查结果

### 角色：{character_name}

#### 语言风格一致性
**评分**：{score}/5 {status}

**词汇匹配**：
- 常用词匹配率：{match_rate}%
- 禁用词出现：{forbidden_count}次
- 标志性用语出现：{signature_count}次

**异常检测**：
{anomalies}

**修改建议**：
{suggestions}

---

## 修改优先级

### 🔴 严重问题（需立即修改）

1. **{chapter} {character}语言偏离**
   - 问题：{forbidden_word}与角色设定不符
   - 影响：S7主角魅力
   - 建议：替换为{alternative}

### 🟡 重要问题（应当修改）

{other_issues}

### 🟢 次要问题（建议修改）

{minor_issues}
```

- [ ] **Step 2: 提交报告模板**

```bash
git add 06_意见仓库/06_角色一致性/检查报告_模板.md
git commit -m "feat: 添加角色一致性检查报告模板"
```

---

## 实现完成检查

- [ ] 目录结构已创建
- [ ] 林夜特征库已建立
- [ ] 苏琳特征库已建立
- [ ] 暗皇特征库已建立
- [ ] 一致性检查工具可运行
- [ ] 测试通过
- [ ] 报告模板可用