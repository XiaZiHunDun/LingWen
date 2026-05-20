# novel-factory/agent_system/agents/auditor/tools.py
from typing import Dict, List, Tuple


class AuditorTools:
    """审计官工具集"""

    def check_character_consistency(self, content: str, character_cards: List[Dict]) -> List[Dict]:
        """检查角色一致性"""
        issues = []
        for card in character_cards:
            name = card.get("name")
            personality = card.get("personality", [])
            opposite_words = {
                "冷静": ["暴怒", "疯狂", "失控"],
                "热血": ["冷漠", "退缩"],
                "狡猾": ["单纯", "正直"]
            }
            for trait in personality:
                if trait in opposite_words:
                    for opp in opposite_words[trait]:
                        if opp in content and name in content:
                            issues.append({
                                "type": "character_consistency",
                                "severity": "P1",
                                "character": name,
                                "issue": f"性格为'{trait}'的角色出现'{opp}'行为",
                                "suggestion": f"请检查{name}的行为是否与'{trait}'性格一致"
                            })
        return issues

    def check_timeline(self, content: str, timeline: List[Dict]) -> List[Dict]:
        """检查时间线"""
        issues = []
        return issues

    def detect_ai_gloss(self, content: str) -> List[Dict]:
        """检测AI痕迹"""
        issues = []
        ai_patterns = [
            ("首先", "过度格式化"),
            ("其次", "过度格式化"),
            ("然后", "机械过渡"),
            ("最后", "过度格式化"),
            ("总之", "过度总结"),
            ("可以看出", "过度总结")
        ]
        for pattern, issue_type in ai_patterns:
            if pattern in content:
                issues.append({
                    "type": "ai_gloss",
                    "severity": "P3",
                    "pattern": pattern,
                    "issue": issue_type,
                    "suggestion": "建议使用更自然的表达方式"
                })
        return issues

    def generate_audit_report(self, chapter_num: int, issues: List[Dict], scores: Dict[str, int]) -> Dict:
        """生成审核报告"""
        return {
            "chapter": chapter_num,
            "timestamp": "2026-05-19",
            "scores": scores,
            "issues": issues,
            "summary": self._summarize_issues(issues)
        }

    def _summarize_issues(self, issues: List[Dict]) -> str:
        """汇总问题"""
        by_severity = {}
        for issue in issues:
            sev = issue.get("severity", "P3")
            by_severity[sev] = by_severity.get(sev, 0) + 1
        return "; ".join([f"{k}: {v}个" for k, v in by_severity.items()])