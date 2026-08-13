"""MasterController 社交引擎 Mixin

Phase 15.0 P3-SPLIT: 从 master_controller.py 拆分的社交引擎方法。
"""


class SocialEngineMixin:
    """社交引擎相关方法"""

    def apply_event(self, event_type, from_char, to_char, chapter):
        """应用事件并更新关系"""
        self.event_calculator.apply_event(
            event_type, from_char, to_char, self.relationship_tracker
        )
        self.relationship_tracker.record_event(from_char, to_char, event_type, chapter)

    def check_alerts(self, chapter):
        """检查预警"""
        return self.conflict_alert.check_alerts(self.relationship_tracker, chapter)

    def get_writing_suggestions(self, chapter):
        """获取写作建议"""
        return self.writing_suggestion.generate_suggestions(
            self.relationship_tracker, chapter
        )