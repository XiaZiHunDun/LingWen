"""Custom exception hierarchy with stage-level error reporting.

Each exception maps to one Stage of the pipeline (load/extract/compose/
generate/store), enabling precise error reporting in API responses and
frontend retry logic.
"""

from __future__ import annotations

from enum import Enum


class Stage(str, Enum):
    """Pipeline stages. Used as error code in API responses."""

    LOAD = "load"
    EXTRACT = "extract"
    COMPOSE = "compose"
    GENERATE = "generate"
    STORE = "store"


class IllustrationError(Exception):
    """Base exception. All pipeline errors derive from this."""

    def __init__(self, stage: Stage, message: str, *, retryable: bool = False) -> None:
        super().__init__(f"[{stage.value}] {message}")
        self.stage = stage
        self.retryable = retryable
        self.message = message


class LoadError(IllustrationError):
    """Project / chapter / character bible loading failure."""

    def __init__(self, message: str) -> None:
        super().__init__(Stage.LOAD, message, retryable=False)


class ExtractError(IllustrationError):
    """Stage 1 LLM extraction failure. Usually transient."""

    def __init__(self, message: str) -> None:
        super().__init__(Stage.EXTRACT, message, retryable=True)


class ComposeError(IllustrationError):
    """Stage 2 prompt template compose failure (e.g. invalid preset)."""

    def __init__(self, message: str) -> None:
        super().__init__(Stage.COMPOSE, message, retryable=False)


class GenerateError(IllustrationError):
    """Stage 3 image API failure (rate limit / network / timeout).

    Phase 96 §5.4: ``retryable`` is now an explicit kwarg so adapters can
    differentiate 5xx/network/timeout/429 (retryable) from 4xx user errors
    (non-retryable). Default stays True for backward compat with existing
    callers that don't pass retryable explicitly.
    """

    def __init__(
        self,
        message: str,
        *,
        retry_after: int | None = None,
        provider: str = "unknown",
        retryable: bool = True,
    ) -> None:
        super().__init__(Stage.GENERATE, message, retryable=retryable)
        self.retry_after = retry_after
        self.provider = provider


class StoreError(IllustrationError):
    """File system write failure (disk full / permission / invalid path)."""

    def __init__(self, message: str) -> None:
        super().__init__(Stage.STORE, message, retryable=False)


class UnknownModelError(ValueError):
    """Raised when explicit model is not in provider's KNOWN_MODELS catalog.

    Phase 100: returned by provider adapters (minimax/openai/stability) when
    the `model` parameter is not in the module's KNOWN_MODELS tuple. Also
    raised by pipeline.resolve_model() when explicit model is invalid.

    Carries .provider / .model / .known attributes for structured error
    handling in routes/illustrations.py (mapped to HTTP 422).
    """

    def __init__(self, provider: str, model: str, known: tuple[str, ...]) -> None:
        self.provider = provider
        self.model = model
        self.known = known
        super().__init__(
            f"unknown model '{model}' for provider '{provider}', "
            f"expected one of {known}"
        )


__all__ = [
    "Stage",
    "IllustrationError",
    "LoadError",
    "ExtractError",
    "ComposeError",
    "GenerateError",
    "StoreError",
    "UnknownModelError",
]
