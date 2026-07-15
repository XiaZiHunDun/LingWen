"""Phase 9.12 Task 5: EdgeInferrer — LLM-based reference edge inference per chapter.

Infers ReferenceEdge (real schema, NOT hypothetical fields) between reference
nodes for a single chapter. Uses the edge_inference.txt prompt template, an
LLM cache, and a cost tracker. On LLM path failure (4xx or retry-exhausted)
it returns [] (caller writes nodes separately — edge failure must not break
nodes).

Design:
- Filter nodes by confidence_threshold (drop low-confidence before LLM call)
- Cache key = SHA256(nodes_dump + chapter_content + prompt_id + model_id)
- Cache hit skips LLM
- 4xx errors (401/403/429) → raise immediately (no retry, edge path returns [])
- Other exceptions → retry up to LLM_MAX_RETRIES (2) times with exponential backoff
- After all retries fail → return [] (edge failure isolated)
- Cost tracking via cost_tracker.record(scenario="cvg_edge_inference", ...)
- ReferenceEdge.id is auto-generated uuid (do NOT pass edge_id from LLM)
"""
import json
import logging
import time
from pathlib import Path
from typing import Any

from infra.ai_service.cost_tracker import CostTracker
from infra.ai_service.model_tiers import ModelTier
from infra.cross_volume.llm_cache import LLMCache
from infra.cross_volume.reference_graph import ReferenceEdge, ReferenceNode
from infra.cross_volume.scanner_calibration import load_scanner_calibration

logger = logging.getLogger(__name__)


# --- Module-level constants (exported) -----------------------------------

LLM_MAX_RETRIES = 2  # 2 retries on top of the initial call (3 attempts total)
LLM_RETRY_BACKOFF_BASE = 1.0  # seconds
LLM_RETRY_BACKOFF_FACTOR = 2.0  # 1s, 2s exponential
LLM_EDGE_SCENARIO = "cvg_edge_inference"  # cost_tracker scenario tag

# Prompt template path
PROMPT_DIR = Path(__file__).parent / "llm_prompts"
PROMPT_FILE = "edge_inference.txt"

# 8 valid relationship types (mirror ReferenceEdge.RelationshipT)
VALID_REL_TYPES: frozenset[str] = frozenset(
    {
        "mentions",
        "evolves",
        "foreshadows",
        "pays_off",
        "appears_with",
        "causes",
        "conflicts_with",
        "supports",
    }
)

# Substrings that mark non-retryable 4xx errors
_4XX_MARKERS = ("401", "403", "429")


class EdgeInferrer:
    """Phase 9.12: LLM-based per-chapter edge inferrer with cache + retry.

    Public surface:
        __init__(router, cache, cost_tracker, model_tier=SONNET, confidence_threshold=3)
        infer_edges(chapter_id, chapter_content, nodes) -> list[ReferenceEdge]
    """

    def __init__(
        self,
        router: Any,
        cache: LLMCache,
        cost_tracker: CostTracker,
        model_tier: ModelTier = ModelTier.SONNET,
        confidence_threshold: int | None = None,
    ) -> None:
        if confidence_threshold is None:
            confidence_threshold = load_scanner_calibration().edge_infer_threshold
        self.router = router
        self.cache = cache
        self.cost_tracker = cost_tracker
        self.model_tier = model_tier
        self.confidence_threshold = confidence_threshold
        # Cache key part: stable per-tier identifier
        self.model_id = f"claude-{model_tier.value}"
        # Pre-load prompt template (read once at init; FileNotFoundError surfaces here)
        self._prompt = (PROMPT_DIR / PROMPT_FILE).read_text(encoding="utf-8")

    # --- Public API -----------------------------------------------------

    def infer_edges(
        self,
        chapter_id: int,
        chapter_content: str,
        nodes: list[ReferenceNode],
    ) -> list[ReferenceEdge]:
        """Infer ReferenceEdge list for one chapter given its nodes.

        - Empty nodes → []
        - Filter nodes by confidence >= threshold
        - Cache hit → parse from cache, skip LLM
        - Cache miss → call LLM, write-through cache, parse result
        - On any LLM/JSON error → log warn + return [] (edge failure isolated)
        """
        if not nodes:
            return []
        filtered = [n for n in nodes if n.confidence >= self.confidence_threshold]
        if not filtered:
            return []

        nodes_dump = json.dumps(
            [
                {"id": n.id, "dim": n.dimension, "conf": n.confidence}
                for n in filtered
            ],
            sort_keys=True,
            ensure_ascii=False,
        )
        cache_key = LLMCache.make_key(
            f"{nodes_dump}|{chapter_content}", PROMPT_FILE, self.model_id
        )

        cached = self.cache.get(cache_key)
        if cached is not None:
            return self._parse_edges(cached.get("parsed", {}), filtered, chapter_id)

        # Cache miss → format prompt and call LLM.
        # We use .replace() (NOT .format()) because the prompt template contains
        # literal braces (e.g. JSON example `{"edges": [...]}`) which would
        # conflict with str.format placeholders.
        prompt = (
            self._prompt.replace("{chapter_content}", chapter_content)
            .replace("{nodes}", nodes_dump)
        )

        try:
            text = self._call_with_retry(prompt)
        except Exception as e:
            # Edge failure is isolated: log warning and return []
            # (caller writes nodes separately, edge failure must not break nodes)
            logger.warning("edge inference LLM call failed for chapter_id=%s: %s", chapter_id, e)
            return []

        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning("edge inference LLM returned invalid JSON for chapter_id=%s: %s", chapter_id, e)
            return []

        # Write-through cache (even if parsed has 0 edges; we still cache the call)
        self.cache.put(
            cache_key,
            {"input_tokens": 0, "output_tokens": 0, "parsed": parsed},
        )
        return self._parse_edges(parsed, filtered, chapter_id)

    # --- Internal: LLM call with retry ----------------------------------

    def _call_with_retry(self, prompt: str) -> str:
        """Call LLM with retry+backoff. Re-raises on 4xx or max retries.

        Unlike LLMScanner, this method re-raises (does NOT swallow) so the
        caller (infer_edges) can decide how to handle the failure.
        """
        last_err: Exception | None = None
        for attempt in range(LLM_MAX_RETRIES + 1):
            try:
                text, usage = self.router.generate_with_usage(
                    prompt=prompt,
                    model_tier=self.model_tier,
                    temperature=0.3,
                    max_tokens=2000,
                )
                # Record cost (Phase 8 / 9.12 cost tracker)
                self.cost_tracker.record(
                    scenario=LLM_EDGE_SCENARIO,
                    tier=self.model_tier,
                    input_tokens=int(usage.get("input_tokens", 0)),
                    output_tokens=int(usage.get("output_tokens", 0)),
                )
                return text
            except Exception as e:
                last_err = e
                err_str = str(e)
                # Non-retryable 4xx: bail out immediately
                if any(marker in err_str for marker in _4XX_MARKERS):
                    raise
                # Retryable error: backoff and try again (unless last attempt)
                if attempt < LLM_MAX_RETRIES:
                    backoff = LLM_RETRY_BACKOFF_BASE * (LLM_RETRY_BACKOFF_FACTOR ** attempt)
                    time.sleep(backoff)
                    continue
                # All retries exhausted
                raise last_err
        # Defensive: should never reach here
        raise last_err if last_err else RuntimeError("LLM call failed without error")

    # --- Internal: parsing LLM JSON → ReferenceEdge list ----------------

    def _parse_edges(
        self,
        parsed: dict[str, Any],
        nodes: list[ReferenceNode],
        chapter_id: int,
    ) -> list[ReferenceEdge]:
        """Convert LLM JSON {"edges": [...]} to a list of ReferenceEdge.

        LLM field name → ReferenceEdge field mapping:
            from_id           → from_node_id
            to_id             → to_node_id
            relationship_type → relationship_type
            weight            → weight (validated [0.0, 1.0] by ReferenceEdge)
            evidence          → evidence (Phase 9.12 additive)

        Reject rules:
        - from_id/to_id not in valid_ids (the filtered nodes' ids) → skip
        - from_id == to_id (self-loop) → ReferenceEdge.__post_init__ raises, caught + skip
        - relationship_type not in VALID_REL_TYPES → skip
        - ReferenceEdge raises ValueError on bad weight → caught + skip
        """
        raw_edges = parsed.get("edges", []) if isinstance(parsed, dict) else []
        if not isinstance(raw_edges, list):
            return []

        valid_ids = {n.id for n in nodes}
        edges: list[ReferenceEdge] = []
        for e in raw_edges:
            if not isinstance(e, dict):
                continue
            from_id = e.get("from_id")
            to_id = e.get("to_id")
            rel_type = e.get("relationship_type")
            weight = e.get("weight", 1.0)
            evidence = e.get("evidence", "")

            # Reject: invalid from_id / to_id
            if from_id not in valid_ids or to_id not in valid_ids:
                logger.debug("edge skip: from_id=%s to_id=%s not in valid_ids", from_id, to_id)
                continue
            # Reject: invalid relationship_type
            if rel_type not in VALID_REL_TYPES:
                logger.debug("edge skip: relationship_type=%s not in VALID_REL_TYPES", rel_type)
                continue

            try:
                edge = ReferenceEdge(
                    from_node_id=from_id,
                    to_node_id=to_id,
                    relationship_type=rel_type,  # type: ignore[arg-type]
                    weight=float(weight),
                    created_by="edge_inferrer",
                    evidence=str(evidence) if evidence is not None else "",
                )
                edges.append(edge)
            except ValueError as ve:
                # ReferenceEdge.__post_init__ raises on:
                # - empty from_node_id/to_node_id
                # - self-loop (from_node_id == to_node_id)
                # - weight out of [0.0, 1.0]
                logger.debug("edge skip: ReferenceEdge validation failed: %s", ve)
                continue
        return edges
