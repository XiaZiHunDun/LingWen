# PHASE-COMPAT: Phase 15.0 P3-SPLIT — DELETE after v16.x
"""Compatibility shim re-exporting MasterController from lingwen_pipeline.

Phase 15.0 P3-SPLIT moved MasterController implementation from
``lingwen_core.agents.master_controller`` to ``lingwen_pipeline.master_controller``.
This shim preserves:
  - ``from lingwen_core.agents.master_controller import MasterController``
  - ``from lingwen_core.agents import master_controller as mc_mod``
"""

from lingwen_pipeline.master_controller import MasterController  # noqa: F401
