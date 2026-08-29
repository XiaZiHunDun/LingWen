"""Agent extractors (LLM-backed).

Phase 118: real LLM call replaces the Phase 117 stub. Returns proposal
dicts that match the ``proposal`` table schema; the route layer is
responsible for calling ``create_proposal`` to persist them.

Cost guards (per handoff §5):
  - ``max_chapters`` defaults to 10 (most-recent N)
  - ``max_tokens`` defaults to 4000 (output cap)
  - Per-session rate limit (5 calls) is enforced by the route layer

Tests inject a mock ``llm_service`` via the ``llm_service`` kwarg so we
don't hit the real provider in CI.
"""
from __future__ import annotations

import logging
from typing import Any, Iterable, Protocol

from infra.world_db.agent_schemas import (
    ProposalResponse,
    parse_proposals_json,
)

logger = logging.getLogger(__name__)


class _LLMRunnable(Protocol):
    """Minimal interface the extractor requires from an LLM service.

    Both ``lingwen_llm.port_adapter.LLMServiceAdapter.generate`` (which wraps
    the concrete ``infra.llm_service.LLMService.generate``) and the test
    mock satisfy this protocol.
    """

    def generate(self, prompt: str, system: str | None = None, **kwargs: Any) -> str: ...


MAX_CHAPTERS_DEFAULT = 10
MAX_OUTPUT_TOKENS_DEFAULT = 4000
TEMPERATURE_DEFAULT = 0.2


SYSTEM_PROMPT = """你是小说设定编辑。分析章节正文,提取与指定角色相关的设定变更提案。

要求:
1. 只输出在正文中能找到证据的变更;无证据则不提案。
2. 每个 proposal 必须包含 kind, target_kind, target_id, payload, source_context, confidence。
3. payload 字段对应 character.update 接口接受的字段(name / canon_level / status / first_chapter / last_seen_chapter / attributes / aliases / notes)。
4. canon_level 只允许 Draft / Secondary / Primary。
5. confidence: high (明确文本证据) / medium (合理推断) / low (猜测)。
6. 没有发现任何变更时,返回空数组,不要编造。
7. **target_id 必须是整数 (JSON number),不是字符串。** 如果不知道角色的整数数据库 ID,**使用 0**。绝对不要把角色 slug 或角色名字符串作为 target_id(这是 JSON number,不是 JSON string)。

输出严格 JSON,不要 markdown 标题,不要解释。返回格式示例:
{"proposals":[{"kind":"character.update","target_kind":"character","target_id":5,"payload":{"status":"alive","last_seen_chapter":42},"source_context":"第42章明确说...","confidence":"high"}]}
"""


def _build_user_prompt(character_slug: str, chapter_texts: list[str]) -> str:
    chapters = "\n\n".join(
        f"### 第{i+1}段\n{t}" for i, t in enumerate(chapter_texts)
    )
    return (
        f"角色 slug: {character_slug}\n\n"
        f"章节文本 (按顺序):\n\n{chapters}\n\n"
        "请输出 JSON。"
    )


def _build_prompt_user_prompt(character_slug: str, user_prompt: str) -> str:
    return (
        f"角色 slug: {character_slug}\n\n"
        f"用户描述:\n{user_prompt}\n\n"
        "请基于以上描述推断角色设定变更,输出 JSON。"
    )


def _to_proposal_dict(proposal: ProposalResponse) -> dict:
    """Convert a validated ProposalResponse into the dict shape accepted
    by ``infra.world_db.queries.proposals.create_proposal``.
    """
    return {
        "kind": proposal.kind,
        "target_kind": proposal.target_kind,
        "target_id": proposal.target_id,
        "payload": proposal.payload.model_dump(exclude_none=True),
        "source": proposal.source,
        "source_context": proposal.source_context,
    }


def extract_proposals_from_chapters(
    character_slug: str,
    chapter_texts: Iterable[str],
    *,
    llm_service: _LLMRunnable | None = None,
    max_chapters: int = MAX_CHAPTERS_DEFAULT,
    max_tokens: int = MAX_OUTPUT_TOKENS_DEFAULT,
    temperature: float = TEMPERATURE_DEFAULT,
) -> list[dict]:
    """Return proposal dicts extracted from the given chapter texts.

    The list is capped to ``max_chapters`` most-recent entries. Returns
    an empty list when the LLM emits no proposals or the response fails
    to parse / validate (errors are logged, never raised — the caller
    treats this as a no-op extraction).
    """
    chapters = list(chapter_texts)
    if not chapters:
        return []
    chapters = chapters[-max_chapters:]

    svc = llm_service or _default_llm_service()
    raw = svc.generate(
        prompt=_build_user_prompt(character_slug, chapters),
        system=SYSTEM_PROMPT,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    try:
        proposals = parse_proposals_json(raw)
    except ValueError as exc:
        logger.warning("agent extraction parse failure: %s", exc)
        return []
    return [_to_proposal_dict(p) for p in proposals]


def extract_proposals_from_prompt(
    character_slug: str,
    user_prompt: str,
    *,
    llm_service: _LLMRunnable | None = None,
    max_tokens: int = MAX_OUTPUT_TOKENS_DEFAULT,
    temperature: float = TEMPERATURE_DEFAULT,
) -> list[dict]:
    """Return proposal dicts extracted from a free-form user prompt.

    Same error semantics as ``extract_proposals_from_chapters``.
    """
    if not user_prompt or not user_prompt.strip():
        return []
    svc = llm_service or _default_llm_service()
    raw = svc.generate(
        prompt=_build_prompt_user_prompt(character_slug, user_prompt),
        system=SYSTEM_PROMPT,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    try:
        proposals = parse_proposals_json(raw)
    except ValueError as exc:
        logger.warning("agent extraction parse failure: %s", exc)
        return []
    return [_to_proposal_dict(p) for p in proposals]


def _default_llm_service() -> _LLMRunnable:
    """Lazy import to avoid pulling llm_service at module load time.

    The service is a singleton; constructing it triggers API-key checks
    and provider plugin loading, which we don't want during tests that
    pass an explicit ``llm_service`` mock.
    """
    from lingwen_llm.port_adapter import LLMServiceAdapter  # re-exported from infra.llm_service for DP-02

    return LLMServiceAdapter()
