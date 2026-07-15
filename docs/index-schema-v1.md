# 灵文系统 Index Schema v1

> 版本：v1.0
> 日期：2026-05-20
> 依据：docs/优化方案-v8.1.md Phase 4.1

---

## 概述

本文档定义灵文系统 `index.json` 的统一格式规范，用于4层内容仓库的索引管理。

### 背景问题

v8.1之前存在4套不兼容的schema：
1. **04_正文层**: `{updated_at, total_chapters, chapters[{chapter, filename, ...}]}`
2. **阶段大纲层(旧)**: `{updated_at, total_files, files[{filename, last_updated}]}`
3. **卷/全文大纲层**: `{layer, project, volume, created_at, methodology_markers, entries}`
4. **阶段层(v2)**: `{stage_id, stage_name, chapter_range, total_chapters, version}`

### 统一目标

- 统一根字段结构
- 兼容各层级的特殊需求
- 支持schema版本校验
- 便于自动化处理

---

## Schema 定义

### 统一根结构

```json
{
  "$schema": "https://lingwen.novel/index-schema/v1",

  "meta": {
    "layer": "04_正文",
    "project": "星陨纪元",
    "version": "1.0",
    "updated_at": "2026-05-20T13:57:02Z"
  },

  "summary": {
    "total_items": 360,
    "status_counts": {
      "draft": 0,
      "reviewing": 0,
      "finalized": 360
    }
  },

  "items": [...]
}
```

---

## 各层 Schema 规范

### 1. 04_正文层 (正文章节)

```json
{
  "$schema": "https://lingwen.novel/index-schema/v1",

  "meta": {
    "layer": "04_正文",
    "project": "星陨纪元",
    "version": "1.0",
    "updated_at": "ISO8601"
  },

  "summary": {
    "total_items": 360,
    "status_counts": {
      "draft": 0,
      "reviewing": 0,
      "finalized": 360
    }
  },

  "items": [
    {
      "id": "ch001",
      "title": "第一章 废土黄昏",
      "filename": "ch001.md",
      "status": "finalized",
      "version": "v1.0",
      "author": "作家A",
      "word_count": 3198,
      "char_count": 2905,
      "lines": 291,
      "last_updated": "2026-05-12",
      "outline_ref": {
        "full": 1,
        "volume": 1,
        "stage": 1
      }
    }
  ]
}
```

**required**: `meta.layer`, `meta.project`, `items`

### 2. 03_阶段大纲层

```json
{
  "$schema": "https://lingwen.novel/index-schema/v1",

  "meta": {
    "layer": "03_阶段大纲",
    "project": "星陨纪元",
    "version": "1.0",
    "updated_at": "ISO8601"
  },

  "summary": {
    "total_items": 1,
    "status_counts": {
      "draft": 0,
      "finalized": 1
    }
  },

  "items": [
    {
      "id": "卷1_阶段1",
      "title": "逃亡开始",
      "filename": "阶段大纲.md",
      "status": "finalized",
      "version": "v1.0",
      "chapter_range": "ch001-010",
      "total_chapters": 10,
      "author": "作家主编",
      "last_updated": "2026-05-12",
      "outline_ref": {
        "volume": 1,
        "stage": 1
      }
    }
  ]
}
```

**required**: `meta.layer`, `items`

### 3. 02_卷大纲层

```json
{
  "$schema": "https://lingwen.novel/index-schema/v1",

  "meta": {
    "layer": "02_卷大纲",
    "project": "星陨纪元",
    "version": "1.0",
    "volume": 1,
    "updated_at": "ISO8601"
  },

  "summary": {
    "total_items": 1,
    "status_counts": {
      "draft": 0,
      "finalized": 1
    }
  },

  "items": [
    {
      "id": "卷1大纲",
      "title": "卷1大纲",
      "filename": "卷1大纲.md",
      "status": "finalized",
      "version": "v1.0",
      "total_stages": 7,
      "chapter_range": "ch001-070",
      "author": "作家主编",
      "last_updated": "2026-05-12"
    }
  ]
}
```

**required**: `meta.layer`, `meta.volume`, `items`

### 4. 01_全文总体大纲层

```json
{
  "$schema": "https://lingwen.novel/index-schema/v1",

  "meta": {
    "layer": "01_全文总体大纲",
    "project": "星陨纪元",
    "version": "1.0",
    "updated_at": "ISO8601"
  },

  "summary": {
    "total_items": 1,
    "status_counts": {
      "draft": 0,
      "finalized": 1
    }
  },

  "items": [
    {
      "id": "全文大纲",
      "title": "星陨纪元全文大纲",
      "filename": "全文大纲.md",
      "status": "finalized",
      "version": "v1.0",
      "total_volumes": 3,
      "total_chapters": 360,
      "author": "作家主编",
      "last_updated": "2026-05-12"
    }
  ]
}
```

**required**: `meta.layer`, `items`

---

## 通用字段说明

### meta 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `layer` | string | 层级标识（必填） |
| `project` | string | 项目名称 |
| `version` | string | Schema版本，固定为 "1.0" |
| `volume` | int | 卷号（卷大纲层必填） |
| `updated_at` | string | ISO8601格式最后更新时间 |

### summary 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `total_items` | int | 总条目数 |
| `status_counts` | object | 各状态数量统计 |

### status_counts 选项

| 状态 | 说明 |
|------|------|
| `draft` | 草稿/创作中 |
| `reviewing` | 审核中 |
| `finalized` | 已定稿 |

### items 元素字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 唯一标识 |
| `title` | string | 标题 |
| `filename` | string | 文件名 |
| `status` | string | draft/reviewing/finalized |
| `version` | string | 版本标识 |
| `author` | string | 负责人 |
| `word_count` | int | 字数（正文层） |
| `char_count` | int | 字符数（正文层） |
| `lines` | int | 行数（正文层） |
| `chapter_range` | string | 章节范围，如 "ch001-010" |
| `total_chapters` | int | 总章节数 |
| `total_stages` | int | 总阶段数（卷层） |
| `total_volumes` | int | 总卷数（全文层） |
| `last_updated` | string | 最后更新时间 |
| `outline_ref` | object | 大纲引用关系 |

### outline_ref 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `full` | int | 全文大纲编号 |
| `volume` | int | 卷大纲编号 |
| `stage` | int | 阶段编号 |

---

## 迁移规则

### 旧 Schema → v1 映射

| 旧字段 | v1 路径 | 说明 |
|--------|---------|------|
| `updated_at` | `meta.updated_at` | 重命名+ISO8601 |
| `total_chapters` | `summary.total_items` | 重命名 |
| `chapters` | `items` | 字段重命名 |
| `chapter` | `items[].id` | 字段重命名 |
| `files` | `items` | 字段重命名 |
| `filename` | `items[].filename` | 保持 |
| `total_files` | `summary.total_items` | 重命名 |
| `layer` | `meta.layer` | 保持 |
| `project` | `meta.project` | 保持 |
| `volume` | `meta.volume` | 保持 |
| `created_at` | `meta.updated_at` | 旧字段废弃 |

---

## 验证规则

```python
def validate_index_json(data: dict) -> tuple[bool, list[str]]:
    """验证 index.json 是否符合 v1 schema

    Returns:
        (is_valid, errors)
    """
    errors = []

    # 1. 检查 $schema
    if data.get('$schema') != 'https://lingwen.novel/index-schema/v1':
        errors.append("缺少或无效的 $schema 字段")

    # 2. 检查 meta.layer
    if 'meta' not in data or 'layer' not in data.get('meta', {}):
        errors.append("缺少 meta.layer 字段")

    # 3. 检查 items
    if 'items' not in data:
        errors.append("缺少 items 字段")
    elif not isinstance(data['items'], list):
        errors.append("items 必须是数组")

    # 4. 检查 summary
    if 'summary' in data:
        summary = data['summary']
        if 'total_items' not in summary:
            errors.append("缺少 summary.total_items")
        if 'status_counts' not in summary:
            errors.append("缺少 summary.status_counts")

    return (len(errors) == 0, errors)
```

---

## 更新日志

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| v1.0 | 2026-05-20 | 初始版本，统一4层schema |
