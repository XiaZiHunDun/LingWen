"""Story Contracts - Genre routing + anti-pattern constraints for creative guidance."""

from .anti_patterns import AntiPattern, AntiPatternAggregator
from .engine import StoryContractEngine
from .injector import StoryContractInjector, inject_story_contract
from .paths import StoryContractPaths
from .persister import ContractPayload, ContractPersister
from .router import GenreRouter, RouteResult

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
