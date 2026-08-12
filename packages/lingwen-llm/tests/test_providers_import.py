"""Phase 17.5 守卫：lingwen_llm 包结构正确。"""


def test_providers_module_importable():
    from lingwen_llm.providers import OpenAIProvider  # noqa: F401
