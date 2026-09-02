"""LingWen hexagonal ports.

v16.1: declaration only. Enforcement is in v16.4 (LLMServicePort) / v16.5 (StoragePort).
v16.5 #N.12: removed TaskSpec + LLMResult from exports (declared but unused;
  LLMServicePort now uses LLMTask from lingwen_shared.contracts.python.llm).
"""

from lingwen_shared.ports.llm_service import LLMServicePort
from lingwen_shared.ports.storage import ConnectionPort, MarkdownRoundtripPort, StoragePort

__all__ = [
    "LLMServicePort",
    "ConnectionPort",
    "StoragePort",
    "MarkdownRoundtripPort",
]
