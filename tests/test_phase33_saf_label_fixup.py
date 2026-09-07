"""Phase 33 — regression guard for ``_safe_label`` import in polisher prompts.

The bug
-------
``packages/lingwen-core/src/lingwen_core/agents/agents/polisher/prompts.py``
originally had a lazy import inside ``build_merge_synthesis_prompt``:

    from lingwen_pipeline.master_controller import _safe_label  # Phase 8.1

But ``_safe_label`` is actually defined in
``packages/lingwen-core/src/lingwen_core/agents/mc_utils.py:25`` — never in
``master_controller``. The broken import only surfaced when
``build_merge_synthesis_prompt`` was *called* (not merely imported), which
is why it stayed latent.

Fix
---
Change the lazy import to::

    from lingwen_core.agents.mc_utils import _safe_label

(matching the pattern already used in ``mc_editing.py:202``).

Why two guards
--------------
1. ``test_phase33_build_merge_synthesis_prompt_runs`` — runtime call:
   actually invokes the function. The original broken import would
   raise ``ImportError`` here.
2. ``test_phase33_no_master_controller_safe_label_import`` — static
   text check on the source file. Defense in depth so a regression to
   the broken path is caught even if no runtime path exercises the
   function.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_PY = (
    REPO_ROOT
    / "packages/lingwen-core/src/lingwen_core/agents/agents/polisher/prompts.py"
)

BROKEN_IMPORT_LINE = (
    "from lingwen_pipeline.master_controller import _safe_label"
)


def test_phase33_build_merge_synthesis_prompt_runs() -> None:
    """Calling build_merge_synthesis_prompt must succeed and use _safe_label."""
    from lingwen_core.agents.agents.polisher.prompts import (
        build_merge_synthesis_prompt,
    )

    # Use labels with non-alphanumeric chars to prove _safe_label ran.
    # Default labels are ("A", "B") — already safe, would not differentiate
    # a working `_safe_label` from a hardcoded "A"/"B".
    prompt = build_merge_synthesis_prompt(
        content_a="variant A body",
        content_b="variant B body",
        labels=("polish_emotional_pacing", "polish_dialogue_natural"),
    )

    # Sanitized labels: hyphens → underscores
    assert "scores_polish_emotional_pacing" in prompt, (
        f"Expected sanitized label 'scores_polish_emotional_pacing' in prompt; "
        f"_safe_label was likely not called (or wrong import). Got first 400 chars:\n"
        f"{prompt[:400]}"
    )
    assert "scores_polish_dialogue_natural" in prompt, (
        f"Expected sanitized label 'scores_polish_dialogue_natural' in prompt. "
        f"Got first 400 chars:\n{prompt[:400]}"
    )
    # Sanity: original hyphenated labels should NOT appear as JSON keys
    assert '"scores_polish-emotional-pacing"' not in prompt, (
        "JSON key still contains unsafe hyphen — _safe_label did not sanitize"
    )


def test_phase33_no_master_controller_safe_label_import() -> None:
    """Source file must not contain the broken import path."""
    assert PROMPTS_PY.exists(), f"Expected file at {PROMPTS_PY}"
    text = PROMPTS_PY.read_text(encoding="utf-8")
    assert BROKEN_IMPORT_LINE not in text, (
        f"{PROMPTS_PY.relative_to(REPO_ROOT)} still contains broken import:\n"
        f"    {BROKEN_IMPORT_LINE}\n"
        f"_safe_label lives in lingwen_core.agents.mc_utils, not master_controller."
    )
