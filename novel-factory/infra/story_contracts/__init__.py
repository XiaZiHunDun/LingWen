"""Story Contracts - Genre routing + anti-pattern constraints for creative guidance."""

from .engine import StoryContractEngine
from .paths import StoryContractPaths
from .router import GenreRouter, RouteResult
from .anti_patterns import AntiPattern, AntiPatternAggregator
from .persister import ContractPayload, ContractPersister
from .injector import StoryContractInjector, inject_story_contract

__all__ = [
    "StoryContractEngine",
    "StoryContractPaths",
    "GenreRouter",
    "RouteResult",
    "AntiPattern",
    "AntiPatternAggregator",
    "ContractPayload",
    "ContractPersister",
    "StoryContractInjector",
    "inject_story_contract",
]