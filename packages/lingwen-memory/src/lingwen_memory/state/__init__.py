# State Management Package
# Tracks characters, timelines, plot threads, and facts

from lingwen_memory.state.character_tracker import CharacterTracker
from lingwen_memory.state.fact_base import FactBase
from lingwen_memory.state.plot_thread_tracker import PlotThreadTracker
from lingwen_memory.state.state_manager import MemoryStateManager, StateManager
from lingwen_memory.state.timeline_manager import TimelineManager

__all__ = [
    "MemoryStateManager",
    "StateManager",  # R2-019 向后兼容 alias,推荐用 MemoryStateManager
    "CharacterTracker",
    "TimelineManager",
    "PlotThreadTracker",
    "FactBase",
]
