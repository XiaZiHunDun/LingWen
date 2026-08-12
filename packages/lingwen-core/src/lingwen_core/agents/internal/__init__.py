"""Internal helpers for infra/agent_system/.

These modules live alongside the agent_system surface so that callers can
import without crossing the infra.cross_volume deletion boundary (Phase 17
deferred legacy). All functions here are TEMPORARY local stubs that will
be replaced by proper domain entities in Phase 18.

Anything in this package is NOT part of the public agent_system surface.
"""
