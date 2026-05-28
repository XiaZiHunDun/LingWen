"""
因果断裂检测规则库

定义所有因果链断裂的触发条件和解决条件
"""

CAUSAL_BREAK_RULES = [
    {
        "action": "broke",
        "action_keywords": ["打破了", "击碎", "粉碎", "毁坏"],
        "state_after": "destroyed",
        "contradiction_trigger": "完好无损",
        "contradiction_patterns": ["完好无损", "完整无缺", "丝毫无损"],
        "resolution_required": ["修复", "修补", "复原", "神奇恢复", "换了一个", "取出另一个"],
        "severity": "P0"
    },
    {
        "action": "killed",
        "action_keywords": ["杀死了", "击杀了", "灭杀", "诛杀"],
        "state_after": "dead",
        "contradiction_trigger": "活着",
        "contradiction_patterns": ["活着", "生存", "气息尚存", "并未真正死亡"],
        "resolution_required": ["复活", "假死", "替身", "逃亡", "救治"],
        "severity": "P0"
    },
    {
        "action": "stole",
        "action_keywords": ["偷走了", "盗取", "窃取"],
        "state_after": "taken",
        "contradiction_trigger": "仍然持有",
        "contradiction_patterns": ["仍然持有", "还在", "未曾丢失"],
        "resolution_required": ["归还", "夺回", "丢失后找回"],
        "severity": "P1"
    },
    {
        "action": "revealed_secret",
        "action_keywords": ["揭露了秘密", "说出了真相", "告知", "告诉了"],
        "state_after": "known",
        "contradiction_trigger": "不知情",
        "contradiction_patterns": ["不知道", "毫不知情", "并未得知"],
        "resolution_required": ["忘记", "失忆", "故意隐瞒"],
        "severity": "P1"
    },
]


class CausalRuleEngine:
    """因果规则引擎 - 匹配动作和状态"""

    def __init__(self, rules=None):
        self.rules = rules or CAUSAL_BREAK_RULES

    def match_action(self, action_text: str, target: str) -> list[dict]:
        """匹配动作文本"""
        results = []
        for rule in self.rules:
            for keyword in rule["action_keywords"]:
                if keyword in action_text:
                    results.append({
                        "rule": rule,
                        "action": rule["action"],
                        "target": target,
                        "keyword": keyword
                    })
        return results

    def match_contradiction(self, text: str, rule: dict) -> bool:
        """检测文本中是否存在状态矛盾"""
        for pattern in rule["contradiction_patterns"]:
            if pattern in text:
                return True
        return False

    def match_resolution(self, text: str, rule: dict) -> bool:
        """检测文本中是否存在解决词"""
        for keyword in rule["resolution_required"]:
            if keyword in text:
                return True
        return False