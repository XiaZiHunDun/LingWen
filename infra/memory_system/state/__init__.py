# State Management Package
# Tracks characters, timelines, plot threads, and facts

from infra.memory_system.state.character_tracker import CharacterTracker
from infra.memory_system.state.fact_base import FactBase
from infra.memory_system.state.plot_thread_tracker import PlotThreadTracker
from infra.memory_system.state.state_manager import MemoryStateManager, StateManager
from infra.memory_system.state.timeline_manager import TimelineManager

__all__ = [
    "MemoryStateManager",
    "StateManager",  # R2-019 向后兼容 alias,推荐用 MemoryStateManager
    "CharacterTracker",
    "TimelineManager",
    "PlotThreadTracker",
    "FactBase",
]
