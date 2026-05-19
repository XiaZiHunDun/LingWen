# novel-factory/agent_system/social_engine/writing_suggestion.py
from typing import Dict, List, Optional


class WritingSuggestion:
    """写作建议生成器"""

    def generate_suggestions(self, relationship_tracker, chapter: int) -> List[str]:
        """生成写作建议"""
        suggestions = []
        network = relationship_tracker.get_network()

        for rel in network.get("relationships", []):
            # 高冲突关系建议
            if rel.get("conflict", 0) >= 0.6:
                suggestions.append(
                    f"【关系提示】{rel['from']}和{rel['to']}之间冲突即将爆发，考虑加入一场对峙场景"
                )

            # 高信任关系建议
            if rel.get("trust", 0) >= 0.7 and rel.get("type") == "ally":
                suggestions.append(
                    f"【关系深化】{rel['from']}和{rel['to']}信任度很高，可以考虑分享秘密或承诺"
                )

            # 长时间无互动
            if rel.get("last_event"):
                try:
                    last_ch = int(rel["last_event"].replace("ch", ""))
                    if chapter - last_ch >= 5:
                        suggestions.append(
                            f"【关系维护】{rel['from']}和{rel['to']}已{chapter - last_ch}章无互动，建议安排场景"
                        )
                except ValueError:
                    pass

        return suggestions

    def suggest_dialogue(self, character1: str, character2: str, relationship: Dict) -> str:
        """生成对话建议"""
        conflict = relationship.get("conflict", 0)
        trust = relationship.get("trust", 0)

        if conflict >= 0.5:
            return f"{character1}和{character2}之间的对话应该充满火药味，可以有争执和反驳"
        elif trust >= 0.7:
            return f"{character1}和{character2}之间可以深入交流，分享内心想法"
        else:
            return f"{character1}和{character2}的对话应该保持一定距离感"