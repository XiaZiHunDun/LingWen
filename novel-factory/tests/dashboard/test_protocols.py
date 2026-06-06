"""Phase 8.13: per-tier budget extraction helper tests.

Mirror _extract_cost_by_scenario silent-degrade pattern (Phase 8.7):
- getattr(controller, "cost_tracker", None) 兜底无 cost_tracker 属性
- try/except (noqa: BLE001) 异常 → log warning + 返 {} empty dict
- ModelTier enum keys 序列化为 .value (e.g. HAIKU → "haiku")
"""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from dashboard.protocols import _extract_cost_by_tier


class TestExtractCostByTier:
    """Phase 8.13: Mirror _extract_cost_by_scenario silent-degrade pattern."""

    def test_returns_empty_dict_when_no_cost_tracker(self) -> None:
        """Backward compat: controller without cost_tracker attribute → empty dict."""

        class _StubController:
            pass

        assert _extract_cost_by_tier(_StubController()) == {}

    def test_returns_tier_value_keys_and_float_amounts(self) -> None:
        """ModelTier enum keys are serialized via .value; amounts as float."""

        from infra.ai_service.model_tiers import ModelTier

        stub = MagicMock()
        stub.cost_by_tier.return_value = {
            ModelTier.HAIKU: 0.05,
            ModelTier.SONNET: 0.50,
            ModelTier.OPUS: 1.20,
        }

        class _StubController:
            def __init__(self) -> None:
                self.cost_tracker = stub

        result = _extract_cost_by_tier(_StubController())
        assert result == {"haiku": 0.05, "sonnet": 0.50, "opus": 1.20}

    def test_returns_empty_dict_on_cost_tracker_exception(self) -> None:
        """Silent degrade: cost_tracker.cost_by_tier() raises → empty dict + log warning."""

        class _StubController:
            class cost_tracker:
                @staticmethod
                def cost_by_tier():
                    raise RuntimeError("db connection lost")

        result = _extract_cost_by_tier(_StubController())
        assert result == {}
