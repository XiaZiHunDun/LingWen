"""Phase 9.12 Task 4: LLMScanner — LLM-based reference node extraction per chapter.

Orchestrates per-chapter LLM scanning across 4 dimensions (character, foreshadow,
setting, plot_point) using prompt templates, an LLM cache, and cost tracking.
On LLM path failure (4xx or retry-exhausted) it falls back to rule-based
extractors. Output is a flat list of ReferenceNode (real schema, NOT
hypothetical fields).

Design:
- 4 dims run serially (deterministic order: character → foreshadow → setting → plot_point)
- Empty content → [] (no LLM call)
- Content > MAX_CONTENT_CHARS → truncate to MAX_CONTENT_CHARS
- Cache key = SHA256(content + prompt_id + model_id); cache hit skips LLM
- 4xx errors (401/403/429) → raise LLMRetryExhausted immediately (no retry)
- Other exceptions → retry up to LLM_MAX_RETRIES (2) times with exponential backoff
- After all retries fail → fallback to rule extractor for that dim
- Cost tracking via cost_tracker.record(scenario="cvg_llm_scan", ...)
- ReferenceNode.id is auto-generated uuid (do NOT pass node_id from LLM)
"""
import json
import logging
import time
from pathlib import Path
from typing import Any

from infra.ai_service.cost_tracker import CostTracker
from infra.ai_service.model_tiers import ModelTier
from infra.cross_volume.llm_cache import LLMCache
from infra.cross_volume.reference_graph import DimensionT, ReferenceNode

logger = logging.getLogger(__name__)


# --- Module-level constants (exported) -----------------------------------

LLM_MAX_RETRIES = 2  # 2 retries on top of the initial call (3 attempts total)
LLM_RETRY_BACKOFF_BASE = 1.0  # seconds
LLM_RETRY_BACKOFF_FACTOR = 2.0  # 1s, 2s exponential
MAX_CONTENT_CHARS = 50_000  # truncate content > 50K to fit LLM context
LLM_SCENARIO = "cvg_llm_scan"  # cost_tracker scenario tag

# Per-dimension prompt filenames (under PROMPT_DIR)
PROMPT_DIR = Path(__file__).parent / "llm_prompts"
PROMPT_FILES: dict[DimensionT, str] = {
    "character": "character.txt",
    "foreshadow": "foreshadow.txt",
    "setting": "setting.txt",
    "plot_point": "plot_point.txt",
}

# Serial scan order (deterministic)
DIM_ORDER: tuple[DimensionT, ...] = ("character", "foreshadow", "setting", "plot_point")

# Substrings that mark non-retryable 4xx errors
_4XX_MARKERS = ("401", "403", "429")


class LLMRetryExhausted(Exception):
    """Raised when LLM call cannot proceed: 4xx or all retries failed."""


class LLMScanner:
    """Phase 9.12: LLM-based 4-dim per-chapter scanner with cache + retry + fallback.

    Public surface:
        __init__(router, cache, fallback_backfiller, cost_tracker, model_tier=SONNET)
        scan_chapter(chapter_id, chapter_content, context) -> list[ReferenceNode]
    """

    def __init__(
        self,
        router: Any,
        cache: LLMCache,
        fallback_backfiller: Any,
        cost_tracker: CostTracker,
        model_tier: ModelTier = ModelTier.SONNET,
    ) -> None:
        self.router = router
        self.cache = cache
        self.fallback_backfiller = fallback_backfiller
        self.cost_tracker = cost_tracker
        self.model_tier = model_tier
        # Cache key part: stable per-tier identifier
        self.model_id = f"claude-{model_tier.value}"
        # Pre-load 4 prompt templates (read once at init)
        self._prompts: dict[DimensionT, str] = {
            dim: (PROMPT_DIR / fname).read_text(encoding="utf-8")
            for dim, fname in PROMPT_FILES.items()
        }

    # --- Public API -----------------------------------------------------

    def scan_chapter(
        self,
        chapter_id: int,
        chapter_content: str,
        context: str = "",
    ) -> list[ReferenceNode]:
        """Scan one chapter across 4 dimensions; return flat list of ReferenceNode."""
        if not chapter_content:
            return []
        if len(chapter_content) > MAX_CONTENT_CHARS:
            chapter_content = chapter_content[:MAX_CONTENT_CHARS]

        nodes: list[ReferenceNode] = []
        for dim in DIM_ORDER:
            try:
                nodes.extend(self._scan_one_dim(chapter_id, chapter_content, context, dim))
            except LLMRetryExhausted:
                # LLM path failed → fall back to rule extractor for that dim
                fallback_nodes = self._fallback_extract(chapter_id, chapter_content, context, dim)
                nodes.extend(fallback_nodes)
        return nodes

    # --- Internal: per-dim scan -----------------------------------------

    def _scan_one_dim(
        self,
        chapter_id: int,
        chapter_content: str,
        context: str,
        dim: DimensionT,
    ) -> list[ReferenceNode]:
        """LLM-driven scan for a single dimension. Raises LLMRetryExhausted on hard fail."""
        cache_key = LLMCache.make_key(chapter_content, PROMPT_FILES[dim], self.model_id)
        cached = self.cache.get(cache_key)
        if cached is not None:
            # Cache hit: parse the stored "parsed" payload, skip LLM call
            return self._parse_nodes(cached.get("parsed", {}), dim, chapter_id)

        # Cache miss → call LLM.
        # Templates use Python str.format with {chapter_content}/{context};
        # other literal braces in the template (e.g. JSON example `{"nodes": [...]}`)
        # are not format placeholders. We do a 2-replace swap to avoid touching templates.
        prompt = (
            self._prompts[dim]
            .replace("{chapter_content}", chapter_content)
            .replace("{context}", context)
        )
        text = self._call_with_retry(prompt)

        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning("LLM returned invalid JSON for dim=%s: %s", dim, e)
            return []

        # Write-through cache: store both token usage and parsed payload
        self.cache.put(
            cache_key,
            {"input_tokens": 0, "output_tokens": 0, "parsed": parsed},
        )
        return self._parse_nodes(parsed, dim, chapter_id)

    # --- Internal: LLM call with retry ----------------------------------

    def _call_with_retry(self, prompt: str) -> str:
        """Call LLM with retry+backoff. Raises LLMRetryExhausted on 4xx or max retries."""
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
                    scenario=LLM_SCENARIO,
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
                    raise LLMRetryExhausted(f"4xx: {e}") from e
                # Retryable error: backoff and try again (unless last attempt)
                if attempt < LLM_MAX_RETRIES:
                    backoff = LLM_RETRY_BACKOFF_BASE * (LLM_RETRY_BACKOFF_FACTOR ** attempt)
                    time.sleep(backoff)
                    continue
                # All retries exhausted
                raise LLMRetryExhausted(f"max retries: {last_err}") from last_err
        # Defensive: should never reach here, but be explicit
        raise LLMRetryExhausted(f"max retries: {last_err}")

    # --- Internal: parsing LLM JSON → ReferenceNode list ----------------

    def _parse_nodes(
        self,
        parsed: dict[str, Any],
        dim: DimensionT,
        chapter_id: int,
    ) -> list[ReferenceNode]:
        """Convert LLM JSON {"nodes": [...]} to a list of ReferenceNode.

        LLM field name → ReferenceNode field mapping (per-dim):
            character:    name | first_appearance_chapter | aliases | traits | confidence
            foreshadow:   keyword | planted_chapter | description | confidence
            setting:      name | first_appearance_chapter | category | description | confidence
            plot_point:   event | chapter | summary | involved_characters | confidence

        LLM `dimension` and `node_id` fields are IGNORED — we use `dim` arg and
        let ReferenceNode auto-generate the uuid `id` field.
        """
        raw_nodes = parsed.get("nodes", []) if isinstance(parsed, dict) else []
        if not isinstance(raw_nodes, list):
            return []

        nodes: list[ReferenceNode] = []
        for n in raw_nodes:
            if not isinstance(n, dict):
                continue
            title = (
                n.get("name")
                or n.get("keyword")
                or n.get("event")
                or ""
            )
            chapter_n = (
                n.get("first_appearance_chapter")
                or n.get("chapter")
                or n.get("planted_chapter")
                or chapter_id
            )
            description = n.get("description") or n.get("summary") or ""
            # description max 200 chars per ReferenceNode.__post_init__ contract
            if len(description) > 200:
                description = description[:200]

            # Serialize dim-specific extras into payload
            payload: dict[str, Any] = {}
            if "aliases" in n:
                payload["aliases"] = n["aliases"]
            if "traits" in n:
                payload["traits"] = n["traits"]
            if "category" in n:
                payload["category"] = n["category"]
            if "involved_characters" in n:
                payload["involved_characters"] = n["involved_characters"]
            if "expected_payoff_chapter" in n:
                payload["expected_payoff_chapter"] = n["expected_payoff_chapter"]

            confidence = n.get("confidence", 1)
            if not isinstance(confidence, int) or confidence < 1 or confidence > 5:
                confidence = 1

            try:
                node = ReferenceNode(
                    dimension=dim,
                    volume=1,
                    chapter=int(chapter_n) if chapter_n is not None else chapter_id,
                    title=str(title),
                    description=description,
                    payload=payload,
                    created_by="llm_scanner",
                    confidence=confidence,
                )
                nodes.append(node)
            except ValueError as e:
                logger.warning("skipping invalid node for dim=%s: %s", dim, e)
                continue
        return nodes

    # --- Internal: fallback to rule extractors --------------------------

    def _fallback_extract(
        self,
        chapter_id: int,
        chapter_content: str,
        context: str,
        dim: DimensionT,
    ) -> list[ReferenceNode]:
        """Run the rule-based fallback extractor for one dim.

        The fallback_backfiller contract is duck-typed:
            fallback_backfiller.extractors[dim].extract(chapter_id, content, context)
        Returns a list of ReferenceNode.
        """
        try:
            extractor = self.fallback_backfiller.extractors[dim]
            return list(extractor.extract(chapter_id, chapter_content, context))
        except Exception as e:  # pragma: no cover - defensive
            logger.warning("fallback extractor failed for dim=%s: %s", dim, e)
            return []
