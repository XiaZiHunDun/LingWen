#!/usr/bin/env python3
"""
核心道具修复器 - 确保核心道具在后续章节中出现
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.consistency.repairers import BaseConsistencyRepairer, ConsistencyRepairResult


class CorePropsRepairer(BaseConsistencyRepairer):
    """核心道具贯穿修复器

    确保第1章出现的核心道具在后续章节中有适当再现。
    如果某个核心道具在某章节缺失，则进行修复。
    """

    # 第1章必须贯穿的核心道具
    CH1_MANDATORY_PROPS = [
        '木勺',
        '地窖',
        '母亲',
        '父亲'
    ]

    def __init__(self, project_root=None):
        super().__init__(project_root)
        self._ch1_props: list = []
        self._current_file: str = ""

    def _get_fix_rules(self):
        """修复规则由动态检测生成，非静态规则"""
        return []

    def _get_ch1_props(self) -> list:
        """获取第1章的核心道具列表"""
        if self._ch1_props:
            return self._ch1_props

        ch1_file = self.chapters_dir / "ch001.md"
        if not ch1_file.exists():
            return []

        import re
        content = ch1_file.read_text(encoding="utf-8")
        props = []

        # 提取【道具:名称】标记
        prop_pattern = r'【道具:(.+?)】'
        matches = re.findall(prop_pattern, content)
        props.extend(matches)

        # 检查强制性道具
        for mandatory in self.CH1_MANDATORY_PROPS:
            if mandatory in content and mandatory not in props:
                props.append(mandatory)

        self._ch1_props = props
        return props

    def _find_prop_mentions_in_chapter(self, chapter_num: int, prop_name: str) -> int:
        """统计某个道具在指定章节的出现次数"""
        ch_file = self.chapters_dir / f"ch{chapter_num:03d}.md"
        if not ch_file.exists():
            return 0

        content = ch_file.read_text(encoding="utf-8")
        return content.count(prop_name)

    def _needs_prop_repair(self, chapter_num: int, prop_name: str) -> bool:
        """检查某章节是否需要修复（该道具应该出现但未出现）"""
        # 第1章跳过
        if chapter_num == 1:
            return False

        # 检查该道具在本章的出现次数
        count = self._find_prop_mentions_in_chapter(chapter_num, prop_name)
        return count == 0

    def _generate_prop_insert_context(self, chapter_num: int, prop_name: str) -> str:
        """生成道具插入的上下文句子

        根据道具类型生成自然的出现语句
        """
        contexts = {
            '木勺': f'握着母亲留下的木勺',
            '地窖': f'走进地窖',
            '母亲': f'想起母亲',
            '父亲': f'想起父亲'
        }
        return contexts.get(prop_name, f'看到{prop_name}')

    def _apply_fixes(self, content: str, issues=None, chapter_num: int = None) -> tuple:
        """应用修复

        对于缺少核心道具的章节，在合适位置插入道具引用

        Returns:
            (new_content, change_count, repaired_issue_descriptions)
        """
        import re

        if chapter_num is None:
            # 从文件名提取章节号
            match = re.search(r'ch(\d+)\.md', self._current_file or '')
            if match:
                chapter_num = int(match.group(1))

        if chapter_num is None or chapter_num == 1:
            # 无法确定章节号或第1章，返回原内容
            return content, 0, []

        ch1_props = self._get_ch1_props()
        if not ch1_props:
            return content, 0, []

        repaired = []
        result = content
        change_count = 0

        # 检查本章缺少哪些核心道具
        for prop in ch1_props:
            if self._needs_prop_repair(chapter_num, prop):
                # 生成插入上下文
                insert_context = self._generate_prop_insert_context(chapter_num, prop)

                # 在章节开头找一个合适的位置插入
                # 策略：找到第一个句号后的位置，在适当位置插入
                insert_point = len(result)
                for i, char in enumerate(result):
                    if char == '。' and i > 10:
                        insert_point = i + 1
                        break

                # 插入道具引用
                insert_text = f'，{insert_context}'
                result = result[:insert_point] + insert_text + result[insert_point:]
                change_count += 1
                repaired.append(f"插入核心道具'{prop}'")

        return result, change_count, repaired

    def repair(self, chapter_num: int, issues=None) -> ConsistencyRepairResult:
        """修复单个章节"""
        import re

        # 设置当前文件用于提取章节号
        self._current_file = f"ch{chapter_num:03d}.md"

        content = self._read_chapter(chapter_num)
        if not content:
            return ConsistencyRepairResult(
                chapter=chapter_num,
                success=False,
                error="章节不存在"
            )

        try:
            new_content, changes, repaired = self._apply_fixes(content, issues or [], chapter_num=chapter_num)
            if changes > 0:
                self._write_chapter(chapter_num, new_content)

            return ConsistencyRepairResult(
                chapter=chapter_num,
                success=True,
                changes=changes,
                new_content=new_content,
                repaired_issues=repaired
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"修复章节{ch}失败: {e}")
            return ConsistencyRepairResult(
                chapter=chapter_num,
                success=False,
                error=str(e)
            )

    def dry_run(self, chapter_num: int, issues=None) -> str:
        """预览修复效果（不写入）"""
        self._current_file = f"ch{chapter_num:03d}.md"

        content = self._read_chapter(chapter_num)
        if not content:
            return ""

        new_content, _, _ = self._apply_fixes(content, issues or [], chapter_num=chapter_num)
        return new_content


def main():
    import argparse
    import re

    parser = argparse.ArgumentParser(description='核心道具修复器')
    parser.add_argument('--chapters', type=str, default='1-10',
                        help='章节范围，如 1-10 或 5,7,9')
    parser.add_argument('--dry-run', action='store_true',
                        help='只输出不保存')
    args = parser.parse_args()

    # 解析章节范围
    chapter_nums = []
    if '-' in args.chapters:
        start, end = args.chapters.split('-')
        chapter_nums = list(range(int(start), int(end) + 1))
    else:
        chapter_nums = [int(x) for x in args.chapters.split(',')]

    repairer = CorePropsRepairer()

    # 获取第1章道具
    ch1_props = repairer._get_ch1_props()
    print(f"第1章核心道具: {ch1_props}")

    # 批量修复
    for ch in chapter_nums:
        if ch == 1:
            continue  # 跳过第1章

        if args.dry_run:
            result = repairer.dry_run(ch)
            print(f"\n--- ch{ch:03d} 预览 ---")
            print(result[:500] if len(result) > 500 else result)
        else:
            result = repairer.repair(ch)
            status = "✅" if result.success else "❌"
            print(f"{status} ch{ch:03d}: 修复{result.changes}处 - {', '.join(result.repaired_issues) if result.repaired_issues else '无修复'}")


if __name__ == '__main__':
    main()