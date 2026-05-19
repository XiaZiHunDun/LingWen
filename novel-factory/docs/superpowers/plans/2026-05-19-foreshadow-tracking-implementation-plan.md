# 伏笔追踪系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立完整的伏笔追踪系统，包括伏笔登记、追踪、回收验证三阶段管理

**Architecture:** 采用目录结构管理伏笔文件，伏笔登记表（总表）+追踪文件（每个伏笔）+分析报告（周期性），通过标准化模板和SOP流程管理

**Tech Stack:** Markdown + YAML + Python脚本

---

## 文件结构

```
novel-factory/
├── 06_意见仓库/
│   └── 05_伏笔管理/
│       ├── README.md
│       ├── 00_伏笔登记总表.md
│       ├── 01_伏笔类型定义.md
│       ├── 02_伏笔回收追踪/
│       │   ├── 伏笔FP-001_追踪.md
│       │   └── ...
│       ├── 03_伏笔分析报告/
│       │   └── YYYY-MM_报告.md
│       └── 04_伏笔预警/
│           └── 预警记录.md
└── scripts/
    └── foreshadowing_tracker.py    # 伏笔追踪工具
```

---

### Task 1: 创建目录结构和基础文件

**Files:**
- Create: `novel-factory/06_意见仓库/05_伏笔管理/README.md`
- Create: `novel-factory/06_意见仓库/05_伏笔管理/00_伏笔登记总表.md`
- Create: `novel-factory/06_意见仓库/05_伏笔管理/01_伏笔类型定义.md`
- Create: `novel-factory/06_意见仓库/05_伏笔管理/02_伏笔回收追踪/README.md`
- Create: `novel-factory/06_意见仓库/05_伏笔管理/03_伏笔分析报告/README.md`
- Create: `novel-factory/06_意见仓库/05_伏笔管理/04_伏笔预警/README.md`

- [ ] **Step 1: 创建README.md**

```markdown
# 伏笔管理

> 版本: v1.0
> 更新日期: 2026-05-19

## 概述

伏笔追踪系统用于记录、管理和追踪小说中的伏笔，确保叙事完整性和逻辑一致性。

## 目录结构

```
05_伏笔管理/
├── 00_伏笔登记总表.md    # 全局伏笔登记
├── 01_伏笔类型定义.md    # 类型定义和示例
├── 02_伏笔回收追踪/       # 每个伏笔的追踪文件
├── 03_伏笔分析报告/       # 周期性分析报告
└── 04_伏笔预警/          # 预警记录
```

## 伏笔类型

| 类型 | 说明 | 示例 |
|------|------|------|
| 人物 | 角色背景/能力/命运暗示 | 角色A的神秘身世 |
| 物品 | 关键道具/信物 | 「暗皇令牌」 |
| 事件 | 世界观规则/历史事件 | 三十年前的灭世之战 |
| 情感 | 情感关系暗示 | 角色A对B的微妙态度 |
| 主题 | 核心主题铺垫 | 「什么是真正的力量」 |

## 状态定义

| 状态 | 说明 |
|------|------|
| 未回收 | 伏笔已埋入，尚未回收 |
| 进行中 | 伏笔开始回收但未完全 |
| 已回收 | 伏笔完整揭示 |
| 已失效 | 因大纲变更不再适用 |

## SOP

### 埋设时登记
1. 识别伏笔类型
2. 填写伏笔登记表
3. 创建追踪文件
4. 更新总表

### 回收时更新
1. 判断回收状态
2. 填写追踪记录
3. 更新伏笔状态
```

- [ ] **Step 2: 创建00_伏笔登记总表.md**

```markdown
# 伏笔登记总表

> 最后更新：2026-05-19
> 总伏笔数：0
> 已回收：0（0%）
> 进行中：0
> 未回收：0

## 统计概览

| 类型 | 总数 | 已回收 | 进行中 | 未回收 |
|------|------|--------|--------|--------|
| 人物 | 0 | 0 | 0 | 0 |
| 物品 | 0 | 0 | 0 | 0 |
| 事件 | 0 | 0 | 0 | 0 |
| 情感 | 0 | 0 | 0 | 0 |
| 主题 | 0 | 0 | 0 | 0 |
| **合计** | **0** | **0** | **0** | **0** |

## 伏笔列表

### 关键伏笔（Critical）

| ID | 标题 | 类型 | 埋设 | 预期 | 状态 |
|----|------|------|------|------|------|
| （暂无记录） |

### 重要伏笔（Major）

| ID | 标题 | 类型 | 埋设 | 预期 | 状态 |
|----|------|------|------|------|------|

### 次要伏笔（Minor）

| ID | 标题 | 类型 | 埋设 | 预期 | 状态 |
|----|------|------|------|------|------|
```

- [ ] **Step 3: 创建01_伏笔类型定义.md**

```markdown
# 伏笔类型定义

## 人物伏笔

### 定义
关于角色背景、能力、命运、关系的暗示性描写。

### 子类型
| 子类型 | 描述 | 示例 |
|--------|------|------|
| 身份伏笔 | 角色真实身份的暗示 | "她总是回避谈论自己的童年" |
| 能力伏笔 | 角色隐藏能力的暗示 | "他似乎对那种力量有着本能的感知" |
| 命运伏笔 | 角色未来命运的暗示 | "每当夜深人静，他总会做同一个梦" |
| 关系伏笔 | 角色之间隐藏关系的暗示 | "第一次见面，却有种熟悉的亲切感" |

### 审核关联
- 关联S2（逻辑自洽）审核
- 关联S7（主角魅力）审核

---

## 物品伏笔

### 定义
关于关键道具、信物、神秘物品的暗示性描写。

### 子类型
| 子类型 | 描述 | 示例 |
|--------|------|------|
| 功能伏笔 | 物品功能的暗示 | "老人说这块石头有着特殊的力量" |
| 来源伏笔 | 物品来源的暗示 | "据古籍记载，这种玉佩来自上古时代" |
| 归属伏笔 | 物品归属的暗示 | "只有真正的主人才能唤醒它的光芒" |

---

## 事件伏笔

### 定义
关于世界观规则、历史事件、未来危机的暗示性描写。

### 子类型
| 子类型 | 描述 | 示例 |
|--------|------|------|
| 世界观伏笔 | 世界运行规则的暗示 | "传说每千年会有一次灵气潮汐" |
| 历史伏笔 | 过去事件的暗示 | "那场战争改变了一切" |
| 危机伏笔 | 未来危机的暗示 | "老人说最危险的时候即将来临" |

---

## 情感伏笔

### 定义
关于角色情感关系、心理变化、人际互动的暗示性描写。

### 子类型
| 子类型 | 描述 | 示例 |
|--------|------|------|
| 爱情伏笔 | 爱情关系的暗示 | "每次目光相遇，她的心跳都会漏一拍" |
| 亲情伏笔 | 亲情关系的暗示 | "看到那个孩子，他心中涌起莫名的亲切感" |
| 仇恨伏笔 | 仇恨或冲突的暗示 | "不知为何，他就是无法对那个人产生好感" |

---

## 主题伏笔

### 定义
关于核心主题、哲学思考、价值观讨论的暗示性描写。

### 示例
- "什么是真正的力量？每个人都有自己的答案"
- "如果成功需要牺牲无辜，你会如何选择？"
```

- [ ] **Step 4: 提交初始文件**

```bash
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory
mkdir -p 06_意见仓库/05_伏笔管理/{02_伏笔回收追踪,03_伏笔分析报告,04_伏笔预警}
git add 06_意见仓库/05_伏笔管理/README.md
git add 06_意见仓库/05_伏笔管理/00_伏笔登记总表.md
git add 06_意见仓库/05_伏笔管理/01_伏笔类型定义.md
git commit -m "feat: 初始化伏笔追踪系统目录结构"
```

---

### Task 2: 创建伏笔追踪文件模板

**Files:**
- Create: `novel-factory/06_意见仓库/05_伏笔管理/02_伏笔回收追踪/伏笔FP-001_追踪.md`
- Create: `novel-factory/06_意见仓库/05_伏笔管理/02_伏笔回收追踪/伏笔追踪_模板.md`

- [ ] **Step 1: 创建伏笔追踪模板**

```markdown
# 伏笔追踪：FP-{id}

## 伏笔基本信息

| 字段 | 内容 |
|------|------|
| 伏笔ID | FP-{id} |
| 标题 | {title} |
| 类型 | {type} |
| 重要性 | {importance} |
| 埋设章节 | {planted_chapter} |
| 预期回收 | {expected_chapter} |
| 当前状态 | {current_status} |

## 追踪轨迹

### 埋设记录
- **章节**：ch{planted_ch}
- **场景**：{scene_location}
- **上下文**：{context_summary}
- **埋设文本**：
  ```
  {planting_text_quote}
  ```
- **埋设方式**：{planting_method}

### 追踪条目

#### ch{num} - {entry_type}
**日期**：{date}
**章节摘要**：{chapter_summary}

**相关文本引用**：
> {text_quote}

**追踪备注**：
{track_notes}

---

## 状态历史

| 日期 | 状态 | 章节 | 备注 |
|------|------|------|------|

## 风险预警

### 当前预警
- ⚠️ {warning}

### 历史预警
- {past_warning} - {resolution}

## 审核记录

### 关联审核
- ch{num} S2审核：{assessment}

### 修改记录
- {date}：{modification}
```

- [ ] **Step 2: 提交模板**

```bash
git add 06_意见仓库/05_伏笔管理/02_伏笔回收追踪/伏笔追踪_模板.md
git commit -m "feat: 添加伏笔追踪模板"
```

---

### Task 3: 创建伏笔分析报告模板

**Files:**
- Create: `novel-factory/06_意见仓库/05_伏笔管理/03_伏笔分析报告/分析报告_模板.md`

- [ ] **Step 1: 创建分析报告模板**

```markdown
# 伏笔分析报告：ch{start}-ch{end}

**报告ID**：FAR-{YYYY-MM}-{seq}
**生成日期**：{datetime}
**分析期间**：ch{start} - ch{end}（{count}章）

---

## 执行摘要

### 整体状态
- 总伏笔数：{total_count}
- 已回收：{recycled_count}（{recycled_rate}%）
- 进行中：{in_progress_count}（{in_progress_rate}%）
- 未回收：{pending_count}（{pending_rate}%）

### 回收率评估
| 评估 | 结果 |
|------|------|
| 整体回收率 | {overall_rate}% |
| 按时回收率 | {on_time_rate}% |
| 超期回收率 | {overdue_rate}% |

### 风险等级
- 🔴 高风险：{critical_count}个伏笔超期
- 🟡 中风险：{major_count}个伏笔需关注
- 🟢 低风险：状态正常

---

## 统计详情

### 伏笔类型分布

```
人物伏笔    ████████████░░░░ {person_count}个
物品伏笔    ████████░░░░░░░ {item_count}个
事件伏笔    ██████████████░░ {event_count}个
情感伏笔    ██████░░░░░░░░ {emotion_count}个
主题伏笔    ████░░░░░░░░░░░ {theme_count}个
```

### 伏笔密度分布

```
ch001-010   ██████████░░░░░  每章平均{avg_1}个伏笔
ch011-020   ██████████████░  每章平均{avg_2}个伏笔
...
```

---

## 超期伏笔详情

| ID | 标题 | 类型 | 预期章节 | 实际章节 | 超期 | 风险 |
|----|------|------|---------|---------|------|------|
```

- [ ] **Step 2: 提交模板**

```bash
git add 06_意见仓库/05_伏笔管理/03_伏笔分析报告/分析报告_模板.md
git commit -m "feat: 添加伏笔分析报告模板"
```

---

### Task 4: 创建伏笔追踪工具

**Files:**
- Create: `novel-factory/scripts/foreshadowing_tracker.py`
- Create: `novel-factory/tests/test_foreshadowing_tracker.py`

- [ ] **Step 1: 创建追踪工具**

```python
#!/usr/bin/env python3
"""
伏笔追踪工具
自动提取、登记、追踪伏笔
"""

import yaml
import re
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

@dataclass
class ForeshadowRecord:
    """伏笔记录"""
    fp_id: str
    title: str
    type: str  # person/item/event/emotion/theme
    importance: str  # critical/major/minor
    planted_at: str
    expected_recycle: str
    status: str  # pending/in_progress/recycled/invalid

class ForeshadowingTracker:
    """伏笔追踪器"""

    def __init__(self, registry_file: Path):
        self.registry_file = registry_file
        self.records = self._load_registry()

    def _load_registry(self) -> dict:
        """加载伏笔登记总表"""
        # 实现加载逻辑
        return {}

    def register_foreshadow(
        self,
        title: str,
        fp_type: str,
        planted_chapter: str,
        expected_chapter: str,
        importance: str = 'major'
    ) -> str:
        """登记新伏笔"""
        # 生成新ID
        next_id = len(self.records) + 1
        fp_id = f"FP-{next_id:03d}"

        record = ForeshadowRecord(
            fp_id=fp_id,
            title=title,
            type=fp_type,
            importance=importance,
            planted_at=planted_chapter,
            expected_recycle=expected_chapter,
            status='pending'
        )

        self.records[fp_id] = record
        self._save_registry()
        self._create_tracking_file(record)

        return fp_id

    def update_status(
        self,
        fp_id: str,
        new_status: str,
        actual_chapter: str = None
    ):
        """更新伏笔状态"""
        if fp_id in self.records:
            self.records[fp_id].status = new_status
            if actual_chapter:
                self.records[fp_id].expected_recycle = actual_chapter
            self._save_registry()

    def get_statistics(self) -> dict:
        """获取统计信息"""
        stats = {
            'total': len(self.records),
            'by_type': {},
            'by_status': {},
            'overdue_count': 0
        }
        # 统计实现
        return stats

    def generate_report(self, start_ch: int, end_ch: int) -> str:
        """生成分析报告"""
        # 生成报告逻辑
        pass

    def _create_tracking_file(self, record: ForeshadowRecord):
        """创建追踪文件"""
        tracking_dir = self.registry_file.parent / "02_伏笔回收追踪"
        tracking_file = tracking_dir / f"伏笔{record.fp_id}_追踪.md"

        content = f"""# 伏笔追踪：{record.fp_id}

## 伏笔基本信息

| 字段 | 内容 |
|------|------|
| 伏笔ID | {record.fp_id} |
| 标题 | {record.title} |
| 类型 | {record.type} |
| 重要性 | {record.importance} |
| 埋设章节 | {record.planted_at} |
| 预期回收 | {record.expected_recycle} |
| 当前状态 | {record.status} |

## 追踪轨迹

（待填充）

## 状态历史

（待填充）
"""
        with open(tracking_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def _save_registry(self):
        """保存登记总表"""
        # 实现保存逻辑
        pass

if __name__ == "__main__":
    tracker = ForeshadowingTracker(
        Path("06_意见仓库/05_伏笔管理/00_伏笔登记总表.md")
    )
    print("伏笔追踪工具已加载")
```

- [ ] **Step 2: 创建测试**

```python
import pytest
from foreshadowing_tracker import ForeshadowingTracker, ForeshadowRecord
from pathlib import Path

def test_register_foreshadow():
    tracker = ForeshadowingTracker(Path("06_意见仓库/05_伏笔管理/00_伏笔登记总表.md"))

    fp_id = tracker.register_foreshadow(
        title="林夜身世之谜",
        fp_type="person",
        planted_chapter="ch005",
        expected_chapter="ch080",
        importance="critical"
    )

    assert fp_id == "FP-001"
    assert fp_id in tracker.records

def test_update_status():
    tracker = ForeshadowingTracker(Path("06_意见仓库/05_伏笔管理/00_伏笔登记总表.md"))
    tracker.update_status("FP-001", "in_progress", "ch075")
    assert tracker.records["FP-001"].status == "in_progress"

def test_get_statistics():
    tracker = ForeshadowingTracker(Path("06_意见仓库/05_伏笔管理/00_伏笔登记总表.md"))
    stats = tracker.get_statistics()
    assert 'total' in stats
    assert 'by_type' in stats
```

- [ ] **Step 3: 运行测试**

```bash
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory
python -m pytest tests/test_foreshadowing_tracker.py -v
```

- [ ] **Step 4: 提交**

```bash
git add scripts/foreshadowing_tracker.py tests/test_foreshadowing_tracker.py
git commit -m "feat: 添加伏笔追踪工具"
```

---

### Task 5: 与审核流程整合

**Files:**
- Modify: `novel-factory/10_方法论/PART4_操作规范/章节扩展SOP.md`

- [ ] **Step 1: 更新审核流程添加伏笔检查点**

（在章节扩展SOP中添加伏笔登记和追踪的检查点）

- [ ] **Step 2: 提交**

```bash
git add 10_方法论/PART4_操作规范/章节扩展SOP.md
git commit -m "feat: 整合伏笔追踪到审核流程"
```

---

## 实现完成检查

- [ ] 目录结构已创建
- [ ] 伏笔登记总表可使用
- [ ] 伏笔类型定义完整
- [ ] 追踪模板可用
- [ ] 分析报告模板可用
- [ ] 追踪工具可运行
- [ ] 测试通过
- [ ] 审核流程已整合