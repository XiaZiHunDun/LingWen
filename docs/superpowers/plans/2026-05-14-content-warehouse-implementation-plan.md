# 内容仓库细化 · 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为内容仓库建立索引机制，包括各层目录的index.json自动生成脚本和workflow_state.json状态追踪。

**Architecture:** 在现有四层目录结构（大纲→卷→阶段→正文）基础上，添加index.json索引文件和update_index.py脚本，实现分层索引自动更新；状态追踪由workflow_state.json统一管理。

**Tech Stack:** Python脚本 / JSON格式 / shell命令

---

## 一、创建索引脚本

### Task 1: 创建索引生成脚本 update_index.py

**Files:**
- Create: `novel-factory/03_内容仓库/update_index.py`

- [ ] **Step 1: 创建update_index.py脚本**

```python
#!/usr/bin/env python3
"""
内容仓库索引生成脚本
用法：
  python update_index.py --layer volume     # 更新卷大纲索引
  python update_index.py --layer stage      # 更新阶段大纲索引
  python update_index.py --layer chapter    # 更新正文索引
  python update_index.py --query ch001      # 查询ch001状态
  python update_index.py --range ch001-010  # 查询ch001-010列表
  python update_index.py --update ch001    # 更新ch001的索引（作家提交后调用）
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime

CONTENT_ROOT = Path(__file__).parent.absolute()

def get_chapter_info(chapter_file):
    """从正文章节文件获取基本信息"""
    with open(chapter_file, 'r', encoding='utf-8') as f:
        content = f.read()
    return {
        "filename": chapter_file.name,
        "word_count": len(content),
        "char_count": len(content.replace('\n', '').replace(' ', '')),
        "lines": content.count('\n'),
        "last_updated": datetime.fromtimestamp(os.path.getmtime(chapter_file)).strftime('%Y-%m-%d')
    }

def update_chapter_index():
    """更新正文目录索引（04_正文/index.json）"""
    chapters_dir = CONTENT_ROOT / "04_正文"
    index_file = chapters_dir / "index.json"

    chapters = []
    for f in sorted(chapters_dir.glob("ch*.md")):
        if f.is_file():
            info = get_chapter_info(f)
            chapters.append({
                "chapter": f.stem,  # e.g. "ch001"
                **info
            })

    index_data = {
        "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "total_chapters": len(chapters),
        "chapters": chapters
    }

    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    print(f"Updated chapter index: {len(chapters)} chapters")
    return index_data

def update_stage_index(volume=None):
    """更新阶段大纲索引（03_阶段大纲/*/index.json）"""
    stages_dir = CONTENT_ROOT / "03_阶段大纲"

    for stage_dir in stages_dir.rglob("*/"):
        if stage_dir.is_dir():
            index_file = stage_dir / "index.json"
            stage_files = list(stage_dir.glob("*.md"))

            stages = []
            for f in stage_files:
                if f.name != "index.json":
                    stages.append({
                        "filename": f.name,
                        "last_updated": datetime.fromtimestamp(os.path.getmtime(f)).strftime('%Y-%m-%d')
                    })

            index_data = {
                "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "total_files": len(stages),
                "files": stages
            }

            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)

    print(f"Updated stage indices")

def update_volume_index():
    """更新卷大纲索引（02_卷大纲/*/index.json）"""
    volumes_dir = CONTENT_ROOT / "02_卷大纲"

    for volume_dir in volumes_dir.rglob("*/"):
        if volume_dir.is_dir():
            index_file = volume_dir / "index.json"
            volume_files = list(volume_dir.glob("*.md"))

            volumes = []
            for f in volume_files:
                if f.name != "index.json":
                    volumes.append({
                        "filename": f.name,
                        "last_updated": datetime.fromtimestamp(os.path.getmtime(f)).strftime('%Y-%m-%d')
                    })

            index_data = {
                "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "total_files": len(volumes),
                "files": volumes
            }

            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)

    print(f"Updated volume indices")

def update_full_index():
    """更新全文大纲索引（01_全文总体大纲/index.json）"""
    full_dir = CONTENT_ROOT / "01_全文总体大纲"
    index_file = full_dir / "index.json"

    full_files = [f for f in full_dir.glob("*.md") if f.name != "index.json"]

    full_data = []
    for f in full_files:
        full_data.append({
            "filename": f.name,
            "last_updated": datetime.fromtimestamp(os.path.getmtime(f)).strftime('%Y-%m-%d')
        })

    index_data = {
        "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "total_files": len(full_data),
        "files": full_data
    }

    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    print(f"Updated full novel index")

def update_all():
    """更新所有索引"""
    update_full_index()
    update_volume_index()
    update_stage_index()
    update_chapter_index()
    print("All indices updated")

def query_chapter(chapter_name):
    """查询指定章节信息"""
    chapter_file = CONTENT_ROOT / "04_正文" / f"{chapter_name}.md"
    if not chapter_file.exists():
        print(f"Chapter {chapter_name} not found")
        return None

    info = get_chapter_info(chapter_file)
    print(f"Chapter: {chapter_name}")
    print(f"  Word count: {info['word_count']}")
    print(f"  Last updated: {info['last_updated']}")
    return info

def query_range(start_ch, end_ch):
    """查询章节范围"""
    chapters_dir = CONTENT_ROOT / "04_正文"
    result = []

    # 解析章节范围
    start_num = int(start_ch.replace('ch', ''))
    end_num = int(end_ch.replace('ch', ''))

    for i in range(start_num, end_num + 1):
        ch_name = f"ch{str(i).zfill(3)}"
        chapter_file = chapters_dir / f"{ch_name}.md"
        if chapter_file.exists():
            info = get_chapter_info(chapter_file)
            result.append(info)

    print(f"Range {start_ch}-{end_ch}: {len(result)} chapters")
    return result

def main():
    parser = argparse.ArgumentParser(description='内容仓库索引管理脚本')
    parser.add_argument('--layer', choices=['full', 'volume', 'stage', 'chapter'],
                        help='指定更新的层级')
    parser.add_argument('--update', help='更新单个章节索引（章节名，如ch001）')
    parser.add_argument('--query', help='查询单个章节信息')
    parser.add_argument('--range', nargs=2, metavar=('START', 'END'),
                        help='查询章节范围，如 --range ch001 ch010')
    parser.add_argument('--all', action='store_true', help='更新所有索引')

    args = parser.parse_args()

    if args.all:
        update_all()
    elif args.layer:
        if args.layer == 'full':
            update_full_index()
        elif args.layer == 'volume':
            update_volume_index()
        elif args.layer == 'stage':
            update_stage_index()
        elif args.layer == 'chapter':
            update_chapter_index()
    elif args.update:
        update_chapter_index()
    elif args.query:
        query_chapter(args.query)
    elif args.range:
        query_range(args.range[0], args.range[1])
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
```

- [ ] **Step 2: 添加执行权限**

```bash
chmod +x novel-factory/03_内容仓库/update_index.py
```

- [ ] **Step 3: 测试脚本（生成当前索引）**

```bash
cd novel-factory/03_内容仓库 && python update_index.py --all
```

预期输出：
```
Updated full novel index
Updated volume indices
Updated stage indices
Updated chapter index: 12288 chapters
All indices updated
```

- [ ] **Step 4: 验证生成的文件**

```bash
ls -la novel-factory/03_内容仓库/04_正文/index.json
cat novel-factory/03_内容仓库/04_正文/index.json | head -30
```

- [ ] **Step 5: 提交**

```bash
git add novel-factory/03_内容仓库/update_index.py
git commit -m "feat(内容仓库): 添加索引生成脚本update_index.py"
```

---

## 二、创建索引文档

### Task 2: 创建内容仓库索引文档 index_README.md

**Files:**
- Create: `novel-factory/03_内容仓库/index_README.md`

- [ ] **Step 1: 创建索引使用文档**

```markdown
# 内容仓库索引使用指南

## 概述

内容仓库采用分层索引机制，各层目录下的`index.json`文件提供快速检索能力。

## 目录结构

```
03_内容仓库/
├── 01_全文总体大纲/
│   ├── index.json      # 全卷索引
│   └── 全局大纲.md
├── 02_卷大纲/
│   ├── index.json      # 卷索引
│   └── 卷1/
│       ├── index.json  # 卷1内阶段索引
│       └── 卷1大纲.md
├── 03_阶段大纲/
│   ├── index.json      # 阶段索引
│   └── 卷1/阶段1/
│       ├── index.json  # 阶段1内章节索引
│       └── 阶段大纲.md
└── 04_正文/
    ├── index.json      # 全章节索引
    ├── ch001.md
    ├── ch002.md
    └── ...（12288个文件）
```

## 索引更新

### 自动更新

索引脚本会在以下时机自动更新：
- 作家提交新章节时
- 审核完成时
- 主控调度时

### 手动更新

```bash
cd novel-factory/03_内容仓库

# 更新所有索引
python update_index.py --all

# 更新特定层级
python update_index.py --layer full      # 更新全文大纲索引
python update_index.py --layer volume   # 更新卷大纲索引
python update_index.py --layer stage    # 更新阶段大纲索引
python update_index.py --layer chapter  # 更新正文章节索引
```

## 查询命令

### 查询单个章节
```bash
python update_index.py --query ch001
```
输出：
```
Chapter: ch001
  Word count: 3200
  Last updated: 2026-05-14
```

### 查询章节范围
```bash
python update_index.py --range ch001 ch010
```
输出：
```
Range ch001-ch010: 10 chapters
```

## 版本管理

### 正文文件版本策略
- **原位覆盖**：同一文件直接更新，不保留历史版本
- **历史追踪**：意见仓库（06_意见仓库）记录审核历史
- **状态追踪**：workflow_state.json统一管理状态

### 回溯方式
1. 查看审核记录 → 意见仓库对应章节目录
2. 查看当前状态 → workflow_state.json
3. 不需要从文件系统回溯历史版本

## 文件命名规范

| 类型 | 格式 | 示例 |
|------|------|------|
| 正文 | `ch{编号}.md` | ch001.md |
| 卷大纲 | `卷{n}_{名称}.md` | 卷1_全局大纲.md |
| 阶段大纲 | `卷{n}_阶段{n}_{名称}.md` | 卷1_阶段1_废土星火.md |
| 阶段汇总 | `卷{n}_阶段{n}_汇总.md` | 卷1_阶段1_汇总.md |
| 卷汇总 | `卷{n}_汇总.md` | 卷1_汇总.md |

## 状态说明

章节状态由workflow_state.json管理：

| 状态 | 说明 |
|------|------|
| 草稿 | 作家创作中 |
| 已提交 | 等待审核 |
| 审核中 | 审核部门处理中 |
| 需修改 | 有意见需作家处理 |
| 定稿 | 审核通过，锁定 |

## 索引字段说明

### 正文index.json字段
```json
{
  "updated_at": "2026-05-14 18:00:00",
  "total_chapters": 12288,
  "chapters": [
    {
      "chapter": "ch001",
      "filename": "ch001.md",
      "word_count": 3200,
      "char_count": 2800,
      "lines": 150,
      "last_updated": "2026-05-14"
    }
  ]
}
```

### 各层index.json字段
```json
{
  "updated_at": "2026-05-14 18:00:00",
  "total_files": 10,
  "files": [
    {
      "filename": "卷1_阶段1_废土星火.md",
      "last_updated": "2026-05-14"
    }
  ]
}
```
```

- [ ] **Step 2: 提交**

```bash
git add novel-factory/03_内容仓库/index_README.md
git commit -m "docs(内容仓库): 添加索引使用文档index_README.md"
```

---

## 三、更新CLAUDE.md

### Task 3: 在CLAUDE.md中添加内容仓库说明

**Files:**
- Modify: `novel-factory/CLAUDE.md`

- [ ] **Step 1: 读取CLAUDE.md末尾**

- [ ] **Step 2: 在CLAUDE.md末尾添加内容仓库说明**

```markdown
---

## 内容仓库管理

### 目录结构
```
03_内容仓库/
├── 01_全文总体大纲/
│   ├── index.json      # 全卷索引（自动生成）
│   └── 全局大纲.md
├── 02_卷大纲/
│   ├── index.json      # 卷索引（自动生成）
│   └── 卷1/
├── 03_阶段大纲/
│   ├── index.json      # 阶段索引（自动生成）
│   └── 卷1/阶段1/
└── 04_正文/
    ├── index.json      # 全章节索引（自动生成）
    └── ch001-ch360.md
```

### 索引更新命令
```bash
cd 03_内容仓库
python update_index.py --all      # 更新所有索引
python update_index.py --layer chapter  # 更新章节索引
python update_index.py --query ch001   # 查询ch001
```

### 版本策略
- 正文文件原位覆盖
- 历史追踪：意见仓库
- 状态追踪：workflow_state.json

### 文件命名规范
- 正文：`ch{编号}.md`（如ch001.md）
- 卷大纲：`卷{n}_{名称}.md`
- 阶段大纲：`卷{n}_阶段{n}_{名称}.md`
- 汇总：`卷{n}_阶段{n}_汇总.md`
```

- [ ] **Step 3: 提交**

```bash
git add novel-factory/CLAUDE.md
git commit -m "feat(CLAUDE): 添加内容仓库管理说明"
```

---

## 四、验证

### Task 4: 验证内容仓库索引机制

- [ ] **Step 1: 验证索引文件生成**

```bash
ls -la novel-factory/03_内容仓库/04_正文/index.json
head -50 novel-factory/03_内容仓库/04_正文/index.json
```

预期输出：包含ch001-ch360的章节索引

- [ ] **Step 2: 验证查询功能**

```bash
cd novel-factory/03_内容仓库 && python update_index.py --query ch001
```

预期输出：显示ch001的字数、更新时间

- [ ] **Step 3: 验证目录结构**

```bash
find novel-factory/03_内容仓库 -name "index.json" | sort
```

预期输出：
```
03_内容仓库/01_全文总体大纲/index.json
03_内容仓库/02_卷大纲/卷1/index.json
03_内容仓库/03_阶段大纲/卷1/阶段1/index.json
03_内容仓库/04_正文/index.json
```

- [ ] **Step 4: 最终提交**

```bash
git add novel-factory/03_内容仓库/
git commit -m "feat: 完成内容仓库索引机制，4个index.json+update_index.py+文档"
git log --oneline -5
```

---

## 自检清单

- [ ] Task 1: update_index.py脚本创建 ✅/❌
- [ ] Task 2: index_README.md文档创建 ✅/❌
- [ ] Task 3: CLAUDE.md更新 ✅/❌
- [ ] Task 4: 索引机制验证 ✅/❌

**Spec覆盖检查：**
- [x] 版本管理策略（Task 1-4）
- [x] 索引机制（Task 1）
- [x] 文件命名规范（Task 2）
- [x] 目录结构保持不变（Task 4）
- [x] update_index.py脚本（Task 1）
- [x] 使用文档（Task 2）
- [x] CLAUDE.md更新（Task 3）

---

**Plan完成时间：** 2026-05-14