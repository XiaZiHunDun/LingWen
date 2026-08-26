"""Orchestrate benchmark runs and CLI entrypoint."""
from __future__ import annotations

import argparse
import logging
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

from infra.llm_benchmarks.fixtures import (
    CHAPTER_IDS,
    CHARACTER_SLUG,
    load_golden_chapters,
)
from infra.llm_benchmarks.metrics import (
    CallResult,
    ProviderMetrics,
    compute_metrics,
    consistency_score,
)
from infra.llm_benchmarks.providers import get_provider_llm
from infra.llm_benchmarks.results import write_call_result
from infra.world_db.agent_extractors import SYSTEM_PROMPT
from infra.world_db.agent_schemas import ProposalResponse, parse_proposals_json

logger = logging.getLogger(__name__)


def _build_user_prompt(character_slug: str, chapter_texts: list[str]) -> str:
    chapters = "\n\n".join(
        f"### 第{i+1}段\n{t}" for i, t in enumerate(chapter_texts)
    )
    return f"角色 slug: {character_slug}\n\n章节文本 (按顺序):\n\n{chapters}\n\n请输出 JSON。"


def _call_provider(
    *,
    provider: str,
    chapter_id: int,
    chapter_texts: list[str],
    run_index: int,
    llm: Any,
) -> CallResult:
    """Make one LLM call and parse + validate the response."""
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        t0 = time.monotonic()
        raw = llm.generate(
            prompt=_build_user_prompt(CHARACTER_SLUG, chapter_texts),
            system=SYSTEM_PROMPT,
            max_tokens=4000,
            temperature=0.2,
        )
        latency_s = time.monotonic() - t0
    except Exception as exc:
        logger.warning("%s call failed: %s", provider, exc)
        return CallResult(
            provider=provider,
            chapter_id=chapter_id,
            run_index=run_index,
            timestamp=timestamp,
            raw_response="",
            parsed_proposals=[],
            parse_ok=False,
            schema_ok=False,
            canon_level_ok=False,
            latency_s=0.0,
            output_tokens=0,
            cost_usd=0.0,
            failed=True,
            error=str(exc),
        )

    parse_ok = True
    parsed_proposals: list[dict] = []
    schema_ok = True
    canon_level_ok = True
    try:
        proposals = parse_proposals_json(raw)
        for p in proposals:
            validated = ProposalResponse(**p.model_dump())
            parsed_proposals.append(p.model_dump())
            # canon_level is Optional in CharacterUpdatePayload; only mark
            # non-compliant if a value IS provided AND not in the enum.
            if (
                validated.payload.canon_level is not None
                and validated.payload.canon_level not in {"Draft", "Secondary", "Primary"}
            ):
                canon_level_ok = False
    except Exception as exc:
        logger.warning("%s parse failure: %s", provider, exc)
        parse_ok = False
        schema_ok = False

    # Rough estimate: ~4 chars per token. Real provider would return usage.
    output_tokens = len(raw) // 4
    # Rough cost estimate: $3 per 1M output tokens (provider-agnostic placeholder).
    cost_usd = output_tokens * 0.000003

    return CallResult(
        provider=provider,
        chapter_id=chapter_id,
        run_index=run_index,
        timestamp=timestamp,
        raw_response=raw,
        parsed_proposals=parsed_proposals,
        parse_ok=parse_ok,
        schema_ok=schema_ok,
        canon_level_ok=canon_level_ok,
        latency_s=latency_s,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        failed=False,
    )


def run_benchmark(
    provider: str,
    run_id: str,
    *,
    real: bool = False,
    chapter_ids: list[int] | None = None,
) -> ProviderMetrics:
    """Run N=10 calls (3 chapters × 3 runs + 1 control) for one provider."""
    chapter_ids = chapter_ids or CHAPTER_IDS
    chapters = load_golden_chapters("huiyu-dangan", chapter_ids)
    chapter_texts_by_id = dict(zip(chapter_ids, chapters))

    llm = get_provider_llm(provider, real=real)

    calls: list[CallResult] = []
    for chapter_id in chapter_ids:
        for run_index in [1, 2, 3]:
            result = _call_provider(
                provider=provider,
                chapter_id=chapter_id,
                chapter_texts=[chapter_texts_by_id[chapter_id]],
                run_index=run_index,
                llm=llm,
            )
            write_call_result(run_id, result)
            calls.append(result)
            logger.info(
                "%s chapter=%d run=%d done (parse_ok=%s)",
                provider,
                chapter_id,
                run_index,
                result.parse_ok,
            )

    # Control call (chapter_id=0 marks it as control, not in consistency)
    result = _call_provider(
        provider=provider,
        chapter_id=0,
        chapter_texts=chapters[:1],
        run_index=0,
        llm=llm,
    )
    write_call_result(run_id, result)
    calls.append(result)

    metrics = compute_metrics(calls, provider)
    metrics = replace(metrics, consistency_score=consistency_score(calls))
    return metrics


def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="Run LLM provider benchmark (Phase 120)",
    )
    parser.add_argument(
        "--provider",
        choices=["minimax", "anthropic", "openai", "all"],
        required=True,
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--real",
        action="store_true",
        help="Use real LLM provider (env var gated)",
    )
    parser.add_argument(
        "--chapters",
        default="1,3,10",
        help="comma-separated chapter IDs",
    )
    parser.add_argument(
        "--report-output",
        default=None,
        help="Optional path to write markdown report",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    providers = (
        ["minimax", "anthropic", "openai"]
        if args.provider == "all"
        else [args.provider]
    )
    chapter_ids = [int(x) for x in args.chapters.split(",")]

    all_metrics: list[ProviderMetrics] = []
    for p in providers:
        m = run_benchmark(p, args.run_id, real=args.real, chapter_ids=chapter_ids)
        all_metrics.append(m)

    if args.report_output:
        from infra.llm_benchmarks.metrics import recommend_priority
        from infra.llm_benchmarks.render import render_report

        priority = recommend_priority(all_metrics)
        report = render_report(args.run_id, all_metrics, priority)
        Path(args.report_output).write_text(report, encoding="utf-8")
        logger.info("report written: %s", args.report_output)
        logger.info("recommended priority: %s", priority)


if __name__ == "__main__":
    _cli()
