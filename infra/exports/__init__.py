#!/usr/bin/env python3
"""TODO(Phase18): migrate infra.exports.* submodules into proper packages.

Phase 17.0 (Task 17.0 Step 7): wildcard imports from ``.core``, ``.events``,
``.persistence`` were removed because those subpackages transitively pulled
in ``infra.event_sourcing.*`` (the deferred deletion target). The full
migration to ``packages/lingwen-storage`` happens in a later task.

For Phase 17, this package exists only as a placeholder so callers that
import the path keep working without raising ModuleNotFoundError. The
submodules (``core``, ``events``, ``persistence``) themselves are unchanged
on disk and can still be imported by their full path if needed.
"""
from __future__ import annotations

__all__: list[str] = []
