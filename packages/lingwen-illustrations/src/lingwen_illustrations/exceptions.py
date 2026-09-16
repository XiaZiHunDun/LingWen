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
    """Stage 3 image API failure (rate limit / network / timeout)."""

    def __init__(
        self,
        message: str,
        *,
        retry_after: int | None = None,
        provider: str = "unknown",
    ) -> None:
        super().__init__(Stage.GENERATE, message, retryable=True)
        self.retry_after = retry_after
        self.provider = provider


class StoreError(IllustrationError):
    """File system write failure (disk full / permission / invalid path)."""

    def __init__(self, message: str) -> None:
        super().__init__(Stage.STORE, message, retryable=False)


__all__ = [
    "Stage",
    "IllustrationError",
    "LoadError",
    "ExtractError",
    "ComposeError",
    "GenerateError",
    "StoreError",
]
