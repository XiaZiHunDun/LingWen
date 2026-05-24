import pytest
from infra.consistency.engine.checker_inspector import CheckerInspector, InspectionResult

class TestCheckerInspector:
    def test_singleton(self):
        i1 = CheckerInspector()
        i2 = CheckerInspector()
        assert i1 is i2

    def test_record_issue_result(self):
        inspector = CheckerInspector()
        inspector.record_issue_result("timeline_checker", is_false_positive=False, confidence_score=0.8)
        inspector.record_issue_result("timeline_checker", is_false_positive=True, confidence_score=0.3)
        stats = inspector.get_checker_stats("timeline_checker")
        assert stats["total_detections"] == 2
        assert stats["false_positive_count"] == 1

    def test_inspect_checker_no_data(self):
        inspector = CheckerInspector()
        result = inspector.inspect_checker("nonexistent_checker")
        assert result.total_issues == 0

    def test_inspect_checker_with_data(self):
        inspector = CheckerInspector()
        for _ in range(5):
            inspector.record_issue_result("character_checker", is_false_positive=False, confidence_score=0.9)
        for _ in range(3):
            inspector.record_issue_result("character_checker", is_false_positive=True, confidence_score=0.2)
        result = inspector.inspect_checker("character_checker")
        assert result.total_issues == 8
        assert result.false_positive_rate == 0.375  # 3/8 = 37.5%
        assert result.should_auto_fix == True  # > 30%