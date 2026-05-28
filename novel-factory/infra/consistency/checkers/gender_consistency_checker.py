#!/usr/bin/env python3
"""
性别一致性检测器
检测角色代词（他/她）在跨章节使用时的不一致

检测维度（S2逻辑自洽）：
- P0: 主要角色性别代词矛盾（他/她混乱）- 自身属性描述错误
- P1: 次要角色性别代词矛盾
- P2: 代词使用不统一警告

工作原理：
1. 从 character_profiles.yaml 获取角色性别设定
2. 检测"角色名+的+身体部位+是/有/浮现出+他的/她的+属性"模式
3. 这种模式表示角色的自身属性被错误性别描述
4. 普通的"角色名+看着+他"不算错误（"他"是宾语）
5. "角色名+的声音...他的..."不算错误（"他的"描述其他人）
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from infra.consistency.engine.data_structures import Issue, IssueLocation, CheckerType, IssueSeverity
from .base_checker import BaseChecker


class GenderConsistencyChecker(BaseChecker):
    """
    性别一致性检测器

    检测角色代词使用的跨章节一致性
    只检测"角色自身属性被错误性别描述"的情况
    """

    def __init__(self, chapters_dir: Optional[str] = None):
        super().__init__(CheckerType.GENDER_CONSISTENCY)
        if chapters_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            chapters_dir = project_root / '03_内容仓库' / '04_正文'
        self.chapters_dir = Path(chapters_dir)

        # 加载角色档案
        self.character_profiles = self._load_character_profiles()

        # 身体部位列表（用于匹配属性描述模式）
        self.body_parts = [
            '脸', '嘴角', '眼中', '神色', '表情', '目光', '身体',
            '声音', '嘴角勾起', '脸上', '眼中闪', '目光中'
        ]

        # 描述性动词（用于判断是否是描述角色自身属性）
        self.descriptive_verbs = [
            '浮现出', '露出', '呈现', '显现', '展现',
            '勾起', '带着', '透着', '透着', '显示',
            '闪过', '出现', '有', '是'
        ]

        # 女性角色列表
        self.female_chars = set()
        # 男性角色列表
        self.male_chars = set()

        for name, info in self.character_profiles.items():
            if 'gender' in info:
                if info['gender'] == 'female':
                    self.female_chars.add(name)
                elif info['gender'] == 'male':
                    self.male_chars.add(name)

    def _load_character_profiles(self) -> Dict[str, Any]:
        """加载角色档案"""
        import yaml
        profiles_path = Path(__file__).parent.parent.parent.parent / 'context' / 'character_profiles.yaml'

        if not profiles_path.exists():
            return {}

        try:
            with open(profiles_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return data.get('characters', {})
        except Exception:
            return {}

    def check(self, chapter_content: str, chapter_num: int, context: Optional[Dict[str, Any]] = None) -> List[Issue]:
        """执行检查（符合BaseChecker接口）"""
        issues = []

        # 获取角色档案（如果有的话）
        profiles = self.character_profiles
        if context and 'character_profiles' in context:
            profiles = context['character_profiles']

        # 重建角色性别映射
        female_chars = set()
        male_chars = set()
        for char_name, char_info in profiles.items():
            if 'gender' in char_info:
                if char_info['gender'] == 'female':
                    female_chars.add(char_name)
                elif char_info['gender'] == 'male':
                    male_chars.add(char_name)

        if not female_chars and not male_chars:
            return issues

        # 检测性别描述错误
        for char_name in female_chars:
            char_issues = self._check_female_character(char_name, chapter_content, chapter_num)
            issues.extend(char_issues)

        for char_name in male_chars:
            char_issues = self._check_male_character(char_name, chapter_content, chapter_num)
            issues.extend(char_issues)

        return issues

    def _is_error_pattern(self, text: str, char_name: str, body_part: str, wrong_pronoun: str) -> bool:
        """
        判断是否是真正的错误模式

        错误: "苏琳的脸上浮现出他的神色" - 苏琳's face shows HIS expression (wrong!)
        非错误: "苏琳的声音传来，他的力量" - HIS power (describes 林夜, not 苏琳)

        关键区别：错误模式中，wrong_pronoun的属性是用来描述角色自身的属性
        """
        # 找到 char_name 的位置
        char_pos = text.find(char_name)
        if char_pos == -1:
            return False

        # 找到 body_part 的位置（在 char_name 之后）
        body_part_pos = text.find(body_part, char_pos)
        if body_part_pos == -1:
            return False

        # 找到 wrong_pronoun 的位置（在 body_part 之后）
        wrong_pos = text.find(wrong_pronoun, body_part_pos)
        if wrong_pos == -1:
            return False

        # 找到 wrong_pronoun 后面的第一个名词/属性
        # 比如 "他的神色" - "神色" 是属性
        # 比如 "他的力量" - "力量" 是属性

        after_wrong = text[wrong_pos + 2:]  # 跳过 "他" 或 "她"
        match = re.match(r'([一-龥]+)', after_wrong)
        if not match:
            return False

        attribute = match.group(1)

        # 检查这个属性是否是用来描述角色的身体部位
        # 错误模式: "脸上浮现出他的神色" - "神色"描述"脸"
        # 非错误: "声音传来，他的力量" - "力量"不描述"声音"

        # 我们需要检查是否有描述性动词连接 body_part 和 wrong_pronoun
        between = text[body_part_pos:wrong_pos]

        # 如果 between 包含描述性动词，则是错误模式
        # 例如: "脸上浮现出他的" - "浮现出"连接脸和神色
        for verb in self.descriptive_verbs:
            if verb in between:
                return True

        return False

    def _check_female_character(self, char_name: str, content: str, chapter_num: int) -> List[Issue]:
        """
        检查女性角色的性别描述错误

        错误模式: "莫言的脸上浮现出他的神色" - 她的神色才对
        """
        issues = []

        # 模式: 角色名 + 的 + 身体部位 + 任何内容 + 他的
        for body_part in self.body_parts:
            pattern = f'{char_name}的{body_part}.{{0,50}}他的'
            matches = list(re.finditer(pattern, content))

            for m in matches:
                matched_text = m.group()

                # 检查是否是真正的错误模式
                if not self._is_error_pattern(matched_text, char_name, body_part, '他的'):
                    continue

                # 获取上下文
                start = max(0, m.start() - 20)
                end = min(len(content), m.end() + 20)
                context_text = content[start:end]

                issues.append(Issue(
                    id=f"GC_{chapter_num:03d}_{char_name}_{body_part}",
                    severity=IssueSeverity.P1 if char_name in ['林夜', '苏琳', '莫言'] else IssueSeverity.P2,
                    checker_type=CheckerType.GENDER_CONSISTENCY,
                    issue_type="gender_inconsistency",
                    title=f"性别代词描述错误: {char_name}",
                    description=f"角色'{char_name}'为女性，但文本中使用'他的'描述其{body_part}",
                    location=IssueLocation(chapter=chapter_num),
                    evidence=f"匹配: {matched_text[:50]}",
                    suggestion=f"将'他的'改为'她的'（角色'{char_name}'为女性）"
                ))

        return issues

    def _check_male_character(self, char_name: str, content: str, chapter_num: int) -> List[Issue]:
        """
        检查男性角色的性别描述错误

        错误模式: "林夜的嘴角勾起她的冷笑" - 他的冷笑才对
        """
        issues = []

        for body_part in self.body_parts:
            pattern = f'{char_name}的{body_part}.{{0,50}}她的'
            matches = list(re.finditer(pattern, content))

            for m in matches:
                matched_text = m.group()

                if not self._is_error_pattern(matched_text, char_name, body_part, '她的'):
                    continue

                start = max(0, m.start() - 20)
                end = min(len(content), m.end() + 20)
                context_text = content[start:end]

                issues.append(Issue(
                    id=f"GC_{chapter_num:03d}_{char_name}_{body_part}",
                    severity=IssueSeverity.P1 if char_name in ['林夜', '苏琳', '莫言'] else IssueSeverity.P2,
                    checker_type=CheckerType.GENDER_CONSISTENCY,
                    issue_type="gender_inconsistency",
                    title=f"性别代词描述错误: {char_name}",
                    description=f"角色'{char_name}'为男性，但文本中使用'她的'描述其{body_part}",
                    location=IssueLocation(chapter=chapter_num),
                    evidence=f"匹配: {matched_text[:50]}",
                    suggestion=f"将'她的'改为'他的'（角色'{char_name}'为男性）"
                ))

        return issues

    def check_chapter(self, chapter_num: int) -> List[Dict[str, Any]]:
        """检查单个章节（返回结构化结果）"""
        ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
        if not ch_file.exists():
            return []

        content = ch_file.read_text(encoding='utf-8')

        issues = self.check(content, chapter_num)

        return [
            {
                'chapter': chapter_num,
                'character': i.character,
                'issue_type': i.issue_type,
                'description': i.description,
                'evidence': i.evidence,
                'suggestion': i.suggestion
            }
            for i in issues
        ]

    def check_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """检查所有章节"""
        all_issues = []
        chapter_files = sorted(self.chapters_dir.glob('ch*.md'))
        if limit:
            chapter_files = chapter_files[:limit]

        for ch_file in chapter_files:
            match = re.match(r'ch(\d+)\.md', ch_file.name)
            if match:
                ch_num = int(match.group(1))
                ch_issues = self.check_chapter(ch_num)
                all_issues.extend(ch_issues)

        return all_issues


if __name__ == '__main__':
    import sys

    checker = GenderConsistencyChecker()

    limit = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == '--limit' else None

    issues = checker.check_all(limit=limit)

    if issues:
        print(f"发现 {len(issues)} 处性别一致性问题:")
        for issue in issues[:20]:
            print(f"  ch{issue['chapter']:03d}: {issue['character']} - {issue['description']}")
            print(f"    证据: {issue['evidence'][:60]}...")
    else:
        print("✅ 性别一致性检查通过")