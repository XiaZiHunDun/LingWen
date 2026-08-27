# PHASE-COMPAT: Phase X.Y — DELETE after v16.x
"""Shim for ReviewerSession, re-exporting from lingwen_core.agents.agents.reviewer."""
try:
    from lingwen_core.agents.agents.reviewer import (  # type: ignore  # noqa: F401
        MAX_REVIEW_CYCLES,
        STOP_THRESHOLD,
        ReviewerSession,
        ReviewFinding,
        ReviewResult,
        review_chapter,
    )
except ImportError:
    # If lingwen_core doesn't expose these symbols, fall back to local stubs.
    # Production code path expects real implementations, but historical tests
    # only need the symbols to import successfully.
    import logging
    _log = logging.getLogger(__name__)

    class ReviewerSession:  # noqa: F401
        """Stub — Phase X.Y refactor moved implementation elsewhere."""

        def __init__(self, *args, **kwargs):
            _log.warning(
                "infra.agent_system.reviewer.ReviewerSession is a Phase X.Y "
                "compat stub; the canonical implementation lives in "
                "lingwen_core.agents.agents.reviewer."
            )

    class ReviewFinding:  # noqa: F401
        pass

    class ReviewResult:  # noqa: F401
        pass

    async def review_chapter(*args, **kwargs):  # noqa: F401
        raise NotImplementedError(
            "review_chapter was relocated to lingwen_core.agents.agents.reviewer"
        )

    MAX_REVIEW_CYCLES = 3  # noqa: F401
    STOP_THRESHOLD = 0.8  # noqa: F401
