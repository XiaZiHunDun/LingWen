#!/usr/bin/env python3
"""
模板版本管理器 (Version Manager)

管理提示词模板的版本历史、变更追踪、回滚支持

Usage:
    from version_manager import VersionManager

    vm = VersionManager("config/prompts")
    vm.create_version("outline_full_novel", "修复了bug")
    history = vm.get_history("outline_full_novel")
"""
import os
import yaml
import shutil
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TemplateVersion:
    """模板版本信息"""
    version: str
    template_id: str
    created_at: str
    changelog: str
    file_hash: str
    file_path: str
    status: str = "active"


@dataclass
class VersionDiff:
    """版本差异"""
    version_from: str
    version_to: str
    template_id: str
    changed_fields: List[str]
    diff_content: Optional[str] = None


class VersionManager:
    """模板版本管理器"""

    # 版本目录名称
    VERSIONS_DIR = ".template_versions"
    HISTORY_FILE = "version_history.yaml"

    def __init__(self, config_dir: str = "config/prompts"):
        # 允许传入不同的路径格式，尝试找到正确的根目录
        config_path = Path(config_dir)
        # 如果传入的是具体配置文件，跳到父目录
        if config_path.suffix in ['.yaml', '.yml', '.py']:
            config_path = config_path.parent
        # 如果是 config/prompts 这样的结构，取 parent
        self.config_dir = config_path.parent if config_path.name == 'prompts' else config_path
        self.versions_dir = self.config_dir / self.VERSIONS_DIR
        self.history_file = self.versions_dir / self.HISTORY_FILE
        self._ensure_directories()

    def _ensure_directories(self):
        """确保版本目录存在"""
        self.versions_dir.mkdir(parents=True, exist_ok=True)

    def _compute_hash(self, file_path: Path) -> str:
        """计算文件内容的MD5哈希"""
        if not file_path.exists():
            return ""

        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def _load_history(self) -> Dict[str, List[Dict]]:
        """加载版本历史"""
        if not self.history_file.exists():
            return {}

        with open(self.history_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def _save_history(self, history: Dict[str, List[Dict]]):
        """保存版本历史"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            yaml.safe_dump(history, f, allow_unicode=True, default_flow_style=False, indent=2)

    def _get_next_version(self, template_id: str) -> str:
        """生成下一个版本号"""
        history = self._load_history()
        versions = history.get(template_id, [])

        if not versions:
            return "v1.0.0"

        # 获取最新版本
        latest = sorted(versions, key=lambda x: x['version'])[-1]
        current = latest['version']

        # 解析版本号
        parts = current.lstrip('v').split('.')
        major = int(parts[0])
        minor = int(parts[1])
        patch = int(parts[2])

        # 小版本号递增
        return f"v{major}.{minor}.{patch + 1}"

    def create_version(
        self,
        template_id: str,
        changelog: str,
        template_dir: Optional[Path] = None
    ) -> TemplateVersion:
        """
        创建新版本

        Args:
            template_id: 模板ID (如 "outline_full_novel")
            changelog: 变更说明
            template_dir: 模板文件目录

        Returns:
            新创建的版本信息
        """
        # 确定模板文件路径
        if template_dir is None:
            template_dir = self._find_template_file(template_id)

        if template_dir is None or not template_dir.exists():
            raise FileNotFoundError(f"Template file not found for: {template_id}")

        # 计算哈希
        file_hash = self._compute_hash(template_dir)

        # 生成版本号
        version = self._get_next_version(template_id)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 备份文件
        backup_dir = self.versions_dir / template_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file = backup_dir / f"{version}{template_dir.suffix}"
        shutil.copy2(template_dir, backup_file)

        # 更新历史
        version_info = {
            'version': version,
            'template_id': template_id,
            'created_at': timestamp,
            'changelog': changelog,
            'file_hash': file_hash,
            'file_path': str(template_dir.relative_to(self.config_dir)),
            'status': 'active'
        }

        history = self._load_history()
        if template_id not in history:
            history[template_id] = []
        history[template_id].append(version_info)
        self._save_history(history)

        return TemplateVersion(**version_info)

    def _find_template_file(self, template_id: str) -> Optional[Path]:
        """查找模板文件"""
        # 从索引文件查找
        index_file = self.config_dir / "00_模板索引.yaml"

        if not index_file.exists():
            return None

        with open(index_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        for template in data.get('templates', []):
            # 匹配ID（去掉版本后缀）
            base_id = template_id.rsplit('_v', 1)[0]
            if template['id'].startswith(base_id):
                file_path = self.config_dir / template['file']
                if file_path.exists():
                    return file_path

        return None

    def get_history(
        self,
        template_id: str,
        limit: Optional[int] = None
    ) -> List[TemplateVersion]:
        """
        获取模板版本历史

        Args:
            template_id: 模板ID
            limit: 限制返回数量

        Returns:
            版本历史列表
        """
        history = self._load_history()
        versions = history.get(template_id, [])

        if not versions:
            return []

        # 按时间倒序排列
        sorted_versions = sorted(
            [TemplateVersion(**v) for v in versions],
            key=lambda x: x.created_at,
            reverse=True
        )

        if limit:
            return sorted_versions[:limit]

        return sorted_versions

    def get_latest_version(self, template_id: str) -> Optional[TemplateVersion]:
        """获取最新版本"""
        history = self.get_history(template_id, limit=1)
        return history[0] if history else None

    def compare_versions(
        self,
        template_id: str,
        version_from: str,
        version_to: Optional[str] = None
    ) -> VersionDiff:
        """
        比较两个版本

        Args:
            template_id: 模板ID
            version_from: 比较起始版本
            version_to: 比较目标版本（默认为最新）

        Returns:
            版本差异
        """
        if version_to is None:
            latest = self.get_latest_version(template_id)
            version_to = latest.version if latest else None

        history = self._load_history()
        versions = history.get(template_id, [])

        from_info = next((v for v in versions if v['version'] == version_from), None)
        to_info = next((v for v in versions if v['version'] == version_to), None)

        if not from_info or not to_info:
            raise ValueError(f"Version not found")

        # 读取文件内容对比
        diff_content = None
        if from_info['file_path'] == to_info['file_path']:
            # 同一文件，读取两个版本
            backup_dir = self.versions_dir / template_id
            from_file = backup_dir / f"{version_from}{Path(from_info['file_path']).suffix}"
            to_file = backup_dir / f"{version_to}{Path(to_info['file_path']).suffix}"

            if from_file.exists() and to_file.exists():
                with open(from_file, 'r', encoding='utf-8') as f:
                    from_content = f.read()
                with open(to_file, 'r', encoding='utf-8') as f:
                    to_content = f.read()

                if from_content != to_content:
                    diff_content = self._generate_diff(from_content, to_content)

        # 识别变更字段
        changed_fields = []
        if from_info['file_hash'] != to_info['file_hash']:
            changed_fields.append('content')
        if from_info['changelog'] != to_info['changelog']:
            changed_fields.append('changelog')

        return VersionDiff(
            version_from=version_from,
            version_to=version_to,
            template_id=template_id,
            changed_fields=changed_fields,
            diff_content=diff_content
        )

    def _generate_diff(self, from_content: str, to_content: str) -> str:
        """生成简单的文本差异"""
        from_lines = from_content.splitlines()
        to_lines = to_content.splitlines()

        diff_lines = ["--- 旧版本", "+++ 新版本"]
        max_lines = max(len(from_lines), len(to_lines))

        for i in range(max_lines):
            old = from_lines[i] if i < len(from_lines) else ""
            new = to_lines[i] if i < len(to_lines) else ""

            if old != new:
                if old:
                    diff_lines.append(f"- {old}")
                if new:
                    diff_lines.append(f"+ {new}")

        return "\n".join(diff_lines)

    def rollback(
        self,
        template_id: str,
        target_version: str
    ) -> bool:
        """
        回滚到指定版本

        Args:
            template_id: 模板ID
            target_version: 目标版本号

        Returns:
            是否成功
        """
        history = self._load_history()
        versions = history.get(template_id, [])

        target_info = next((v for v in versions if v['version'] == target_version), None)
        if not target_info:
            return False

        # 找到当前文件位置
        current_file = self.config_dir / target_info['file_path']
        if not current_file.exists():
            return False

        # 读取备份版本
        backup_dir = self.versions_dir / template_id
        backup_file = backup_dir / f"{target_version}{current_file.suffix}"

        if not backup_file.exists():
            return False

        # 备份当前版本
        current_backup = backup_dir / f"rollback_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}{current_file.suffix}"
        shutil.copy2(current_file, current_backup)

        # 恢复目标版本
        shutil.copy2(backup_file, current_file)

        return True

    def export_version(
        self,
        template_id: str,
        version: str,
        output_dir: Path
    ) -> Optional[Path]:
        """导出版本到指定目录"""
        backup_dir = self.versions_dir / template_id

        # 查找版本文件
        history = self._load_history()
        versions = history.get(template_id, [])
        version_info = next((v for v in versions if v['version'] == version), None)

        if not version_info:
            return None

        ext = Path(version_info['file_path']).suffix
        version_file = backup_dir / f"{version}{ext}"

        if not version_file.exists():
            return None

        output_path = output_dir / f"{template_id}_{version}{ext}"
        shutil.copy2(version_file, output_path)

        return output_path

    def get_all_templates_with_history(self) -> Dict[str, List[TemplateVersion]]:
        """获取所有有版本历史的模板"""
        history = self._load_history()
        result = {}

        for template_id, versions in history.items():
            result[template_id] = [
                TemplateVersion(**v) for v in sorted(
                    versions,
                    key=lambda x: x['created_at'],
                    reverse=True
                )
            ]

        return result

    def cleanup_old_versions(
        self,
        template_id: str,
        keep_count: int = 5
    ) -> int:
        """
        清理旧版本（保留最近N个）

        Args:
            template_id: 模板ID
            keep_count: 保留版本数量

        Returns:
            删除的版本数
        """
        history = self._load_history()
        versions = history.get(template_id, [])

        if len(versions) <= keep_count:
            return 0

        # 按时间排序，保留最新的
        sorted_versions = sorted(
            versions,
            key=lambda x: x['created_at'],
            reverse=True
        )

        to_delete = sorted_versions[keep_count:]
        backup_dir = self.versions_dir / template_id

        deleted = 0
        for v in to_delete:
            # 删除文件
            ext = Path(v['file_path']).suffix
            version_file = backup_dir / f"{v['version']}{ext}"
            if version_file.exists():
                version_file.unlink()
                deleted += 1

            # 从历史中移除
            versions.remove(v)

        history[template_id] = versions
        self._save_history(history)

        return deleted


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="模板版本管理器")
    parser.add_argument("--config", "-c", default="config/prompts", help="配置目录")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有模板历史")
    parser.add_argument("--history", "-H", metavar="TEMPLATE_ID", help="查看模板历史")
    parser.add_argument("--compare", "-C", nargs=3, metavar=("TEMPLATE_ID", "V1", "V2"),
                        help="比较两个版本")
    parser.add_argument("--rollback", "-R", nargs=2, metavar=("TEMPLATE_ID", "VERSION"),
                        help="回滚到指定版本")
    parser.add_argument("--create", "-C", dest="create_version", nargs=2,
                        metavar=("TEMPLATE_ID", "CHANGELOG"), help="创建新版本")

    args = parser.parse_args()

    vm = VersionManager(args.config)

    if args.list:
        all_histories = vm.get_all_templates_with_history()
        print("\n所有模板版本历史:\n")
        for tid, versions in all_histories.items():
            print(f"{tid}: {len(versions)} 个版本")
            for v in versions[:3]:
                print(f"  - {v.version} ({v.created_at})")
                if v.changelog:
                    print(f"    {v.changelog[:50]}...")
        return

    if args.history:
        history = vm.get_history(args.history)
        print(f"\n模板 {args.history} 版本历史:\n")
        for v in history:
            print(f"  {v.version}")
            print(f"    创建: {v.created_at}")
            print(f"    变更: {v.changelog}")
            print(f"    状态: {v.status}")
            print()

    if args.compare:
        template_id, v1, v2 = args.compare
        diff = vm.compare_versions(template_id, v1, v2)
        print(f"\n版本对比: {v1} -> {v2}\n")
        print(f"变更字段: {', '.join(diff.changed_fields) if diff.changed_fields else '无'}")
        if diff.diff_content:
            print("\n差异内容:\n")
            print(diff.diff_content)


if __name__ == "__main__":
    import sys
    sys.exit(main() or 0)
