"""Provider adapters for image generation APIs (Phase 96).

This subpackage hosts the canonical adapters for each supported image
provider (MiniMax, OpenAI, Stability). Each adapter implements a uniform
``ImageProvider`` protocol (Task 6) so the dispatch layer can swap
providers without coupling to a specific API.

Helpers shared across adapters (b64_json envelope decoder, etc.) live
alongside the adapters in this subpackage.
"""
