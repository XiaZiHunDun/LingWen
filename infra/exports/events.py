#!/usr/bin/env python3
"""TODO(Phase18): migrate event symbols to packages/lingwen-storage.

Phase 17.0 (Task 17.0 Step 7): the re-export chain
``infra.exports.events`` -> ``infra.event_sourcing.{models,store}``
has been severed. Event symbols will be re-introduced from
``packages/lingwen-storage`` in a later task.

This file remains so existing ``from infra.exports.events import ...``
imports do not raise ModuleNotFoundError; the symbols are temporarily
unavailable and any consumer must be migrated alongside the new
storage package.
"""
from __future__ import annotations

# Intentionally empty: re-exports removed in Phase 17.0.

__all__: list[str] = []
