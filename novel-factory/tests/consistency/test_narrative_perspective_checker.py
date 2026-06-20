"""NarrativePerspectiveChecker integration with ConsistencyEngine."""
from infra.consistency.checkers.narrative_perspective_checker import NarrativePerspectiveChecker


def test_check_accepts_inline_content_without_typeerror():
    checker = NarrativePerspectiveChecker()
    content = "沈柯站在射电阵。与此同时，风很大。\n"
    issues = checker.check(content, chapter_num=1)
    assert isinstance(issues, list)
