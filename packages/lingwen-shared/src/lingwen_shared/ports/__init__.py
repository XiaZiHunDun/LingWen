"""Hexagonal ports (Hexagonal architecture interfaces).

v16.1: declaration only. Enforcement is in v16.4 (LLMServicePort) / v16.5 (StoragePort).
"""
from lingwen_shared.ports.llm_service import LLMResult, LLMServicePort, TaskSpec
from lingwen_shared.ports.storage import ConnectionPort, MarkdownRoundtripPort, StoragePort

__all__ = [
    "LLMServicePort",
    "TaskSpec",
    "LLMResult",
    "StoragePort",
    "ConnectionPort",
    "MarkdownRoundtripPort",
]
