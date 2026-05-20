#!/usr/bin/env python3
"""
问题追踪工具
提供 CLI 接口管理问题追踪系统
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

ISSUES_DIR = Path(__file__).parent.parent / "issues"
INDEX_FILE = ISSUES_DIR / "_index.json"
TEMPLATE_FILE = ISSUES_DIR / "_template.md"


def load_index() -> Dict:
    """加载问题索引"""
    if INDEX_FILE.exists():
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "version": "1.0",
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "total_issues": 0,
        "by_severity": {"P0": 0, "P1": 0, "P2": 0},
        "by_status": {"open": 0, "in_progress": 0, "resolved": 0, "verified": 0},
        "issues": []
    }


def save_index(index: Dict):
    """保存问题索引"""
    index["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    ISSUES_DIR.mkdir(parents=True, exist_ok=True)
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def create_issue(chapter_id: str, severity: str, issue_type: str,
                 description: str, discovered_by: str = "system") -> str:
    """创建新问题"""
    ISSUES_DIR.mkdir(parents=True, exist_ok=True)
    issue_file = ISSUES_DIR / f"{chapter_id}.md"

    # 检查是否已存在
    is_new = not issue_file.exists()

    if is_new:
        # 创建新问题文件
        with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            template = f.read()

        content = template.replace("{chapter_id}", chapter_id)
        content = content.replace("{YYYY-MM-DD}", datetime.now().strftime("%Y-%m-%d"))
        content = content.replace("{P0|P1|P2}", severity)
        content = content.replace("{章节重复|人物状态矛盾|时间线冲突|命名不一致|...}", issue_type)
        content = content.replace("{open|in_progress|resolved|verified}", "open")
        content = content.replace("{agent_name}", discovered_by)
        content = content.replace("{详细描述问题}", description)
        content = content.replace("{chXXX, chYYY}", chapter_id)

        with open(issue_file, 'w', encoding='utf-8') as f:
            f.write(content)

        # 更新索引
        index = load_index()
        index["total_issues"] += 1
        index["by_severity"][severity] = index["by_severity"].get(severity, 0) + 1
        index["issues"].append({
            "chapter_id": chapter_id,
            "issue_file": str(issue_file),
            "severity": severity,
            "status": "open"
        })
        save_index(index)
    else:
        # 追加到现有文件
        with open(issue_file, 'a', encoding='utf-8') as f:
            f.write(f"\n## 新问题 - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"\n**严重程度**: {severity}\n")
            f.write(f"**问题类型**: {issue_type}\n")
            f.write(f"**状态**: open\n")
            f.write(f"\n### 问题描述\n\n{description}\n")

    return str(issue_file)


def list_issues(status: Optional[str] = None, severity: Optional[str] = None):
    """列出问题"""
    index = load_index()
    issues = index.get("issues", [])

    if status:
        issues = [i for i in issues if i.get("status") == status]
    if severity:
        issues = [i for i in issues if i.get("severity") == severity]

    print(f"共 {len(issues)} 个问题:")
    for issue in issues:
        print(f"  [{issue['severity']}] {issue['chapter_id']} - {issue['status']}")


def update_status(chapter_id: str, new_status: str):
    """更新问题状态"""
    index = load_index()

    for issue in index["issues"]:
        if issue["chapter_id"] == chapter_id:
            old_status = issue.get("status", "open")
            issue["status"] = new_status
            issue["old_status"] = old_status
            # 更新统计
            index["by_status"][old_status] = max(0, index["by_status"].get(old_status, 1) - 1)
            index["by_status"][new_status] = index["by_status"].get(new_status, 0) + 1
            break
    else:
        print(f"未找到问题: {chapter_id}")
        return

    save_index(index)
    print(f"已更新 {chapter_id} 状态为 {new_status}")


def main():
    parser = argparse.ArgumentParser(description="问题追踪工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # create 子命令
    create_parser = subparsers.add_parser("create", help="创建新问题")
    create_parser.add_argument("--chapter", required=True, help="章节ID")
    create_parser.add_argument("--severity", required=True, choices=["P0", "P1", "P2"], help="严重程度")
    create_parser.add_argument("--type", required=True, help="问题类型")
    create_parser.add_argument("--desc", required=True, help="问题描述")
    create_parser.add_argument("--by", default="system", help="发现者")

    # list 子命令
    list_parser = subparsers.add_parser("list", help="列出问题")
    list_parser.add_argument("--status", choices=["open", "in_progress", "resolved", "verified"], help="按状态筛选")
    list_parser.add_argument("--severity", choices=["P0", "P1", "P2"], help="按严重程度筛选")

    # update 子命令
    update_parser = subparsers.add_parser("update", help="更新问题状态")
    update_parser.add_argument("--chapter", required=True, help="章节ID")
    update_parser.add_argument("--status", required=True,
                              choices=["open", "in_progress", "resolved", "verified"], help="新状态")

    args = parser.parse_args()

    if args.command == "create":
        result = create_issue(args.chapter, args.severity, args.type, args.desc, args.by)
        print(f"问题已创建: {result}")
    elif args.command == "list":
        list_issues(args.status, args.severity)
    elif args.command == "update":
        update_status(args.chapter, args.status)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()