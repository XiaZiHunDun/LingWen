"""Phase 17.9 守卫：lingwen_quality 包结构正确。"""


def test_quality_module_importable():
    import lingwen_quality  # noqa: F401


def test_consistency_module_importable():
    from lingwen_quality import consistency  # noqa: F401


def test_quality_submodule_importable():
    from lingwen_quality import quality  # noqa: F401
