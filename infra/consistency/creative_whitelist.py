# PHASE-COMPAT: Phase 13.X — DELETE after v16.x
"""Shim for creative_whitelist module.

The canonical implementation is at ``lingwen_quality.consistency.creative_whitelist``.
Some symbols were renamed during Phase 13.X consolidation; this shim defines
compat aliases so historical tests can still import them.
"""
from lingwen_quality.consistency.creative_whitelist import (  # type: ignore  # noqa: F401
    add_whitelist,
    get_whitelisted_chapters,
    is_whitelisted,
    remove_whitelist,
)


# Historical symbols expected by older tests
class CreativeWhitelist:  # noqa: F401
    """Legacy class placeholder — use add_whitelist / is_whitelisted directly."""

    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "CreativeWhitelist was an instance-based API in Phase 11; "
            "Phase 13 refactored to module-level functions. See add_whitelist()."
        )


class WhitelistChapter:  # noqa: F401
    """Legacy dataclass placeholder — see add_whitelist() return value."""

    chapter_num: int
    reason: str
    expires_at: str | None = None


class WhitelistError(Exception):  # noqa: F401
    """Raised for creative whitelist issues."""


class ChapterAlreadyWhitelistedError(WhitelistError):  # noqa: F401
    """Raised when adding a chapter that's already whitelisted."""


class ChapterNotWhitelistedError(WhitelistError):  # noqa: F401
    """Raised when removing a chapter that's not whitelisted."""


DIAMOND = "DIAMOND"  # noqa: F401
GOLD = "GOLD"  # noqa: F401
SILVER = "SILVER"  # noqa: F401
DOWNGRADED_LEVELS = (GOLD, SILVER)  # noqa: F401
