"""Phase 17.10 守卫：lingwen_cli 包结构正确。"""


def test_cli_module_importable():
    import lingwen_cli  # noqa: F401


def test_main_module_importable():
    from lingwen_cli.main import main  # noqa: F401


def test_options_module_importable():
    from lingwen_cli.options import UnifiedOptions  # noqa: F401