from infra.cli.output import OutputFormatter

def test_init_formatter():
    formatter = OutputFormatter(verbose=False)
    assert formatter.verbose is False

def test_format_chapters_summary():
    formatter = OutputFormatter()
    result = formatter.format_chapters_summary([1, 2, 3, 4, 5])
    assert "ch001" in result or "1" in result

def test_merge_ranges():
    formatter = OutputFormatter()
    # [1,2,3,5,7,8,9] should merge to [(1,3), (5,5), (7,9)]
    ranges = formatter._merge_ranges([1, 2, 3, 5, 7, 8, 9])
    assert ranges == [(1, 3), (5, 5), (7, 9)]

def test_format_issue():
    formatter = OutputFormatter()
    issue = {"location": "ch001", "type": "worldview", "description": "术语不一致"}
    result = formatter.format_issue(issue)
    assert "ch001" in result
    assert "术语不一致" in result

def test_print_methods():
    formatter = OutputFormatter()
    # Just verify methods exist and don't crash
    formatter.print_success("test")
    formatter.print_error("test")
    formatter.print_warning("test")
    formatter.print_info("test")