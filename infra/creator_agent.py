"""Phase 126 v16.2.4 shim: re-export from lingwen_creator.content.agent.

Migrated to packages/lingwen-creator/src/lingwen_creator/content/agent.py.
Shim will be deleted in v16.2.7 final cleanup.
"""
from lingwen_creator.content.agent import *  # noqa: F401,F403
from lingwen_creator.content.agent import _has_llm_api_key  # noqa: F401  # test compat (monkeypatch)
