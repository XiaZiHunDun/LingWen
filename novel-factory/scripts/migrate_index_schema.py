#!/usr/bin/env python3
"""
index.json Schema 迁移脚本

将旧版 index.json 迁移到 v1 统一 schema

用法:
    python3 scripts/migrate_index_schema.py [--dry-run] [--verify] [path]
"""

import json
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

# Schema 版本
SCHEMA_VERSION = "https://lingwen.novel/index-schema/v1"

# 默认项目名
DEFAULT_PROJECT = "星陨纪元"


def detect_layer(path: Path) -> str:
    """根据路径检测层级"""
    path_str = str(path)
    if "04_正文" in path_str:
        return "04_正文"
    elif "03_阶段大纲" in path_str:
        return "03_阶段大纲"
    elif "02_卷大纲" in path_str:
        return "02_卷大纲"
    elif "01_全文总体大纲" in path_str:
        return "01_全文总体大纲"
    else:
        # 从目录结构推断
        parent = path.parent.name
        if parent.startswith("卷") or "卷" in parent:
            return "02_卷大纲"
        return "unknown"


def detect_volume(path: Path) -> int | None:
    """从路径推断卷号"""
    path_str = str(path)
    # 卷1_阶段2 → 1
    if "卷1_阶段" in path_str:
        return 1
    elif "卷2_阶段" in path_str:
        return 2
    elif "卷3_阶段" in path_str:
        return 3
    elif "/卷1/" in path_str or path_str.endswith("/卷1"):
        return 1
    elif "/卷2/" in path_str or path_str.endswith("/卷2"):
        return 2
    elif "/卷3/" in path_str or path_str.endswith("/卷3"):
        return 3
    return None


def detect_stage(path: Path) -> int | None:
    """从路径推断阶段号"""
    path_str = str(path)
    import re
    match = re.search(r'阶段(\d+)', path_str)
    if match:
        return int(match.group(1))
    return None


def migrate_04_body(data: dict, path: Path) -> dict:
    """迁移 04_正文 层"""
    meta = {
        "layer": "04_正文",
        "project": data.get("project", DEFAULT_PROJECT),
        "version": "1.0",
        "updated_at": data.get("updated_at", datetime.now().isoformat()),
    }

    # 转换章节数据
    items = []
    for ch in data.get("chapters", []):
        items.append({
            "id": ch.get("chapter", ch.get("id", "")),
            "title": ch.get("title", ""),
            "filename": ch.get("filename", ""),
            "status": "finalized",  # 假设已有章节都是finalized
            "version": "v1.0",
            "author": ch.get("author", ""),
            "word_count": ch.get("word_count", 0),
            "char_count": ch.get("char_count", 0),
            "lines": ch.get("lines", 0),
            "last_updated": ch.get("last_updated", ""),
        })

    summary = {
        "total_items": data.get("total_chapters", len(items)),
        "status_counts": {
            "draft": 0,
            "reviewing": 0,
            "finalized": len(items),
        }
    }

    return {
        "$schema": SCHEMA_VERSION,
        "meta": meta,
        "summary": summary,
        "items": items,
    }


def migrate_03_outline(data: dict, path: Path) -> dict:
    """迁移 03_阶段大纲 层"""
    meta = {
        "layer": "03_阶段大纲",
        "project": data.get("project", DEFAULT_PROJECT),
        "version": "1.0",
        "updated_at": data.get("updated_at", data.get("created_at", datetime.now().isoformat())),
    }

    # 检测是否是新版格式
    if "entries" in data and isinstance(data["entries"], list):
        items = []
        for entry in data.get("entries", []):
            items.append({
                "id": entry.get("id", ""),
                "title": entry.get("title", ""),
                "filename": entry.get("filename", "阶段大纲.md"),
                "status": "finalized",
                "version": "v1.0",
                "chapter_range": entry.get("chapter_range", ""),
                "total_chapters": entry.get("total_chapters", 0),
                "last_updated": entry.get("last_updated", ""),
            })
    elif "files" in data:
        # 旧版格式
        stage_num = detect_stage(path)
        volume_num = detect_volume(path)
        chapter_range = f"ch{(stage_num - 1) * 10 + 1:03d}-{min(stage_num * 10, 360):03d}" if stage_num else ""

        items = [{
            "id": f"卷{volume_num}_阶段{stage_num}" if volume_num and stage_num else "unknown",
            "title": f"阶段{stage_num}",
            "filename": data["files"][0].get("filename", "阶段大纲.md") if data.get("files") else "阶段大纲.md",
            "status": "finalized",
            "version": "v1.0",
            "chapter_range": chapter_range,
            "total_chapters": 10,  # 假设每阶段10章
            "author": "",
            "last_updated": data["files"][0].get("last_updated", "") if data.get("files") else "",
            "outline_ref": {
                "volume": volume_num,
                "stage": stage_num,
            } if stage_num else {},
        }]
    elif "stage_id" in data:
        # v2格式
        items = [{
            "id": data.get("stage_id", ""),
            "title": data.get("stage_name", ""),
            "filename": "阶段大纲.md",
            "status": "finalized",
            "version": data.get("version", "v1.0"),
            "chapter_range": data.get("chapter_range", ""),
            "total_chapters": data.get("total_chapters", 0),
            "last_updated": data.get("created_at", ""),
        }]
    else:
        items = []

    summary = {
        "total_items": len(items),
        "status_counts": {
            "draft": 0,
            "reviewing": 0,
            "finalized": len(items),
        }
    }

    return {
        "$schema": SCHEMA_VERSION,
        "meta": meta,
        "summary": summary,
        "items": items,
    }


def migrate_02_volume(data: dict, path: Path) -> dict:
    """迁移 02_卷大纲 层"""
    volume_num = detect_volume(path)

    meta = {
        "layer": "02_卷大纲",
        "project": data.get("project", DEFAULT_PROJECT),
        "version": "1.0",
        "volume": volume_num or data.get("volume", 0),
        "updated_at": data.get("updated_at", data.get("created_at", datetime.now().isoformat())),
    }

    # 检测新版格式
    if "entries" in data and isinstance(data["entries"], list):
        items = []
        for entry in data.get("entries", []):
            items.append({
                "id": entry.get("id", f"卷{meta['volume']}大纲"),
                "title": entry.get("title", f"卷{meta['volume']}大纲"),
                "filename": entry.get("filename", f"卷{meta['volume']}大纲.md"),
                "status": "finalized",
                "version": "v1.0",
                "last_updated": entry.get("last_updated", ""),
            })
    elif "files" in data:
        items = [{
            "id": f"卷{meta['volume']}大纲",
            "title": f"卷{meta['volume']}大纲",
            "filename": data["files"][0].get("filename", f"卷{meta['volume']}大纲.md") if data.get("files") else f"卷{meta['volume']}大纲.md",
            "status": "finalized",
            "version": "v1.0",
            "last_updated": data["files"][0].get("last_updated", "") if data.get("files") else "",
        }]
    else:
        items = [{
            "id": f"卷{meta['volume']}大纲",
            "title": f"卷{meta['volume']}大纲",
            "filename": f"卷{meta['volume']}大纲.md",
            "status": "finalized",
            "version": "v1.0",
            "last_updated": meta["updated_at"],
        }]

    summary = {
        "total_items": len(items),
        "status_counts": {
            "draft": 0,
            "reviewing": 0,
            "finalized": len(items),
        }
    }

    return {
        "$schema": SCHEMA_VERSION,
        "meta": meta,
        "summary": summary,
        "items": items,
    }


def migrate_01_full(data: dict, path: Path) -> dict:
    """迁移 01_全文总体大纲 层"""
    meta = {
        "layer": "01_全文总体大纲",
        "project": data.get("project", DEFAULT_PROJECT),
        "version": "1.0",
        "updated_at": data.get("updated_at", data.get("created_at", datetime.now().isoformat())),
    }

    if "entries" in data and isinstance(data["entries"], list):
        items = []
        for entry in data.get("entries", []):
            items.append({
                "id": entry.get("id", "全文大纲"),
                "title": entry.get("title", "全文大纲"),
                "filename": entry.get("filename", "全文大纲.md"),
                "status": "finalized",
                "version": "v1.0",
                "total_volumes": entry.get("total_volumes", 3),
                "total_chapters": entry.get("total_chapters", 360),
                "last_updated": entry.get("last_updated", ""),
            })
    else:
        items = [{
            "id": "全文大纲",
            "title": "星陨纪元全文大纲",
            "filename": "全文大纲.md",
            "status": "finalized",
            "version": "v1.0",
            "total_volumes": 3,
            "total_chapters": 360,
            "last_updated": meta["updated_at"],
        }]

    summary = {
        "total_items": len(items),
        "status_counts": {
            "draft": 0,
            "reviewing": 0,
            "finalized": len(items),
        }
    }

    return {
        "$schema": SCHEMA_VERSION,
        "meta": meta,
        "summary": summary,
        "items": items,
    }


def migrate_index_file(path: Path, dry_run: bool = False) -> tuple[bool, str]:
    """迁移单个 index.json 文件

    Returns:
        (success, message)
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            old_data = json.load(f)

        # 检测层级
        layer = detect_layer(path)

        # 根据层级选择迁移函数
        migrators = {
            "04_正文": migrate_04_body,
            "03_阶段大纲": migrate_03_outline,
            "02_卷大纲": migrate_02_volume,
            "01_全文总体大纲": migrate_01_full,
        }

        migrator = migrators.get(layer)
        if not migrator:
            return (False, f"未知层级: {layer}")

        new_data = migrator(old_data, path)

        # 验证必填字段
        if "$schema" not in new_data:
            return (False, "迁移后缺少 $schema")
        if "meta" not in new_data:
            return (False, "迁移后缺少 meta")
        if "items" not in new_data:
            return (False, "迁移后缺少 items")

        if dry_run:
            return (True, f"[干跑] {path}\n旧: {json.dumps(old_data, ensure_ascii=False)[:200]}...\n新: {json.dumps(new_data, ensure_ascii=False, indent=2)[:200]}...")

        # 备份原文件
        backup_path = Path(str(path) + ".bak")
        shutil.copy2(path, backup_path)

        # 写入新文件
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)

        return (True, f"已迁移: {path} → 备份: {backup_path}")

    except json.JSONDecodeError as e:
        return (False, f"JSON解析错误: {e}")
    except Exception as e:
        return (False, f"迁移失败: {e}")


def validate_index(path: Path) -> tuple[bool, list[str]]:
    """验证 index.json 是否符合 v1 schema

    Returns:
        (is_valid, errors)
    """
    errors = []

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 1. 检查 $schema
        if data.get('$schema') != SCHEMA_VERSION:
            errors.append(f"缺少或无效的 $schema，期望: {SCHEMA_VERSION}")

        # 2. 检查 meta.layer
        if 'meta' not in data:
            errors.append("缺少 meta 字段")
        elif 'layer' not in data.get('meta', {}):
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

    except Exception as e:
        errors.append(f"验证异常: {e}")

    return (len(errors) == 0, errors)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="index.json Schema 迁移工具")
    parser.add_argument("path", nargs="?", default=".", help="要迁移的 index.json 路径或目录")
    parser.add_argument("--dry-run", action="store_true", help="干跑模式，不实际修改文件")
    parser.add_argument("--verify", action="store_true", help="仅验证模式，不迁移")
    parser.add_argument("--recursive", "-r", action="store_true", help="递归处理子目录")
    args = parser.parse_args()

    base_path = Path(args.path)

    # 查找 index.json 文件
    if base_path.is_file() and base_path.name == "index.json":
        index_files = [base_path]
    else:
        if args.recursive:
            index_files = list(base_path.rglob("index.json"))
        else:
            index_files = list(base_path.glob("*/index.json"))

    if not index_files:
        print("未找到 index.json 文件")
        sys.exit(1)

    print(f"找到 {len(index_files)} 个 index.json 文件")
    print()

    results = []
    for idx, path in enumerate(index_files, 1):
        print(f"[{idx}/{len(index_files)}] 处理: {path}")

        if args.verify:
            is_valid, errors = validate_index(path)
            if is_valid:
                print(f"  ✅ 验证通过")
            else:
                print(f"  ❌ 验证失败:")
                for err in errors:
                    print(f"     - {err}")
            results.append((path, is_valid, errors))
        else:
            success, message = migrate_index_file(path, dry_run=args.dry_run)
            if success:
                print(f"  ✅ {message}")
            else:
                print(f"  ❌ {message}")
            results.append((path, success, [message]))

    # 汇总
    print()
    print("=" * 50)
    if args.verify:
        passed = sum(1 for _, is_valid, _ in results if is_valid)
        print(f"验证结果: {passed}/{len(results)} 通过")
    else:
        if args.dry_run:
            print("干跑模式，未实际修改文件")
        else:
            migrated = sum(1 for _, success, _ in results if success)
            print(f"迁移结果: {migrated}/{len(results)} 成功")


if __name__ == "__main__":
    main()
