"""Test fixtures for tools/ tests.

The migrated tools/ files use LLMServiceAdapter from lingwen_llm.port_adapter,
which requires the default factory to be registered. The factory is registered
by ``infra.llm_service`` at module load time, so importing it here ensures
test files that construct these tools get a working adapter.

In production, the application startup imports ``infra.llm_service`` (or any
module that transitively imports it), so this conftest mirrors that bootstrap
just for the test environment.
"""
from __future__ import annotations

# Trigger factory registration: infra.llm_service registers itself as the
# default LLMServiceAdapter factory at module load. Importing here is safe
# because tests/tools/ is not part of the business-code enforcement scope.
import infra.llm_service  # noqa: F401
