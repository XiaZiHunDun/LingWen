"""Mock + real LLM provider factory for benchmark runs.

In test/CI mode, returns MockLLMService (no API calls).
In CLI --real mode, returns real LLMService for minimax only;
anthropic/openai --real raises NotImplementedError (cost-controlled mock).
"""
from __future__ import annotations

import hashlib
import os
from typing import Any, Protocol


class _LLMRunnable(Protocol):
    def generate(self, prompt: str, system: str | None = None, **kwargs: Any) -> str: ...


def _hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt[:200].encode()).hexdigest()[:16]


# Mock canned JSON — keyed by hash(prompt[:200]). Each provider has 3 entries
# (one per huiyu-dangan chapter). Designed to show schema_compliance differences.
anthropic_mock_canned: dict[str, str] = {
    _hash_prompt("角色 slug: 林栀\n\n章节文本 (按顺序):\n\n### 第1段\n林栀"): (
        '{"proposals":[{"kind":"character.update","target_kind":"character",'
        '"target_id":5,"payload":{"status":"alive","confidence":"high"},'
        '"source_context":"第1章提到林栀","confidence":"high"}]}'
    ),
    _hash_prompt("角色 slug: 林栀\n\n章节文本 (按顺序):\n\n### 第1段\n周姐"): (
        # intentionally missing some fields to model hallucination
        '{"proposals":[{"kind":"character.update","target_id":5,'
        '"payload":{"status":"alive"}}]}'
    ),
    _hash_prompt("角色 slug: 林栀\n\n章节文本 (按顺序):\n\n### 第1段\n街灯"): (
        '{"proposals":[]}'  # no evidence, returns empty per prompt instructions
    ),
}

openai_mock_canned: dict[str, str] = {
    _hash_prompt("角色 slug: 林栀\n\n章节文本 (按顺序):\n\n### 第1段\n林栀"): (
        '{"proposals":[{"kind":"character.update","target_kind":"character",'
        '"target_id":5,"payload":{"status":"alive","canon_level":"Primary","confidence":"high"},'
        '"source_context":"第1章","confidence":"high"}]}'
    ),
    _hash_prompt("角色 slug: 林栀\n\n章节文本 (按顺序):\n\n### 第1段\n周姐"): (
        '{"proposals":[{"kind":"character.update","target_kind":"character",'
        '"target_id":5,"payload":{"status":"alive","canon_level":"Primary","confidence":"high"},'
        '"source_context":"周姐对话","confidence":"high"}]}'
    ),
    _hash_prompt("角色 slug: 林栀\n\n章节文本 (按顺序):\n\n### 第1段\n街灯"): (
        '{"proposals":[]}'
    ),
}

minimax_mock_canned: dict[str, str] = {
    _hash_prompt("角色 slug: 林栀\n\n章节文本 (按顺序):\n\n### 第1段\n林栀"): (
        '{"proposals":[{"kind":"character.update","target_kind":"character",'
        '"target_id":5,"payload":{"status":"alive","canon_level":"Primary","confidence":"medium"},'
        '"source_context":"林栀出现","confidence":"medium"}]}'
    ),
    _hash_prompt("角色 slug: 林栀\n\n章节文本 (按顺序):\n\n### 第1段\n周姐"): (
        '{"proposals":[{"kind":"character.update","target_kind":"character",'
        '"target_id":5,"payload":{"status":"alive","canon_level":"Primary","confidence":"medium"},'
        '"source_context":"周姐对话","confidence":"medium"}]}'
    ),
    _hash_prompt("角色 slug: 林栀\n\n章节文本 (按顺序):\n\n### 第1段\n街灯"): (
        '{"proposals":[]}'
    ),
}


class MockLLMService:
    """Deterministic LLM mock keyed on prompt hash.

    Returns canned JSON responses; for unknown prompts, returns an empty
    proposals array (graceful default).
    """

    def __init__(self, canned: dict[str, str]) -> None:
        self._canned = canned

    def generate(self, prompt: str, system: str | None = None, **kwargs: Any) -> str:
        h = _hash_prompt(prompt)
        if h in self._canned:
            return self._canned[h]
        # default: empty proposals (no evidence)
        return '{"proposals":[]}'


def _canned_for(name: str) -> dict[str, str]:
    return {
        "anthropic": anthropic_mock_canned,
        "openai": openai_mock_canned,
        "minimax": minimax_mock_canned,
    }[name]


def get_provider_llm(name: str, *, real: bool = False) -> _LLMRunnable:
    """Return LLM service for the named provider.

    real=False → MockLLMService (no env var check, safe for tests).
    real=True + name=="minimax" → LLMService.get() (requires MINIMAX_API_KEY).
    real=True + name in {"anthropic","openai"} → NotImplementedError.
    """
    if not real:
        return MockLLMService(canned=_canned_for(name))

    if name == "minimax":
        if not os.environ.get("MINIMAX_API_KEY"):
            raise RuntimeError(
                "MINIMAX_API_KEY not set; add to .env or export before --real"
            )
        # Lazy import to avoid module-load side effects in tests
        from infra.llm_service import LLMService

        return LLMService.get()

    if name in {"anthropic", "openai"}:
        raise NotImplementedError(
            f"real {name} benchmark not in scope (Phase 120 cost-controlled mock only)"
        )

    raise ValueError(f"unknown provider: {name!r}")
