"""Phase 101: Atomic Provider Fallback — regression guards + I093 invariant tests.

13 guards total:
- G1-G6, G8-G10: Phase 101 implementation guards (T13)
- G7 (and the 3 invariant checks below): I093 invariant in architecture.yml (T12)
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE_YML = ROOT / ".lingwen" / "architecture.yml"


# ---- I093 invariant guards (T12) ----

@pytest.fixture
def architecture_yml() -> dict:
    with open(ARCHITECTURE_YML) as f:
        return yaml.safe_load(f)


def test_i093_invariant_exists(architecture_yml: dict):
    """I093 NEW: fallback chain dispatch invariant in architecture.yml."""
    invariants = architecture_yml.get("invariants", [])
    # invariants may be a list of dicts OR dict-keyed
    if isinstance(invariants, list):
        ids = {entry.get("id") for entry in invariants}
    else:
        ids = set(invariants.keys())
    assert "I093" in ids, f"I093 missing; have ids: {sorted(ids)}"


def test_i093_describes_fallback_dispatch_entry_point(architecture_yml: dict):
    """I093 must mention dispatch_with_fallback as the only entry point."""
    invariants = architecture_yml["invariants"]
    if isinstance(invariants, list):
        i093 = next((e for e in invariants if e.get("id") == "I093"), None)
    else:
        i093 = invariants["I093"]
    rule = i093.get("rule", "")
    assert "dispatch_with_fallback" in rule
    assert "fallback.py" in rule or "lingwen_illustrations.fallback" in rule


def test_i093_severity_is_error(architecture_yml: dict):
    """Phase invariants are enforcement-level (severity=error)."""
    invariants = architecture_yml["invariants"]
    if isinstance(invariants, list):
        i093 = next((e for e in invariants if e.get("id") == "I093"), None)
    else:
        i093 = invariants["I093"]
    assert i093.get("severity") == "error"


# ---- G1: settings.yaml fallback_chain default ----

def test_g1_settings_yaml_fallback_chain_default():
    """ProjectSettings.fallback_chain defaults to []."""
    from apps.studio_api.routes.project_settings import ProjectSettings
    s = ProjectSettings()
    assert s.fallback_chain == []


# ---- G2: GenerateRequest has fallback_chain field ----

def test_g2_generate_request_has_fallback_chain():
    """GenerateRequest must have fallback_chain optional field."""
    from apps.studio_api.routes.illustrations import GenerateRequest
    fields = GenerateRequest.model_fields.keys()
    assert "fallback_chain" in fields
    field_info = GenerateRequest.model_fields["fallback_chain"]
    assert field_info.default is None


# ---- G3: pipeline.generate_illustration uses fallback ----

def test_g3_pipeline_generate_uses_fallback():
    """pipeline.generate_illustration must call dispatch_with_fallback."""
    pipeline_src = (ROOT / "packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py").read_text()
    gen_section = pipeline_src.split("async def generate_illustration")[1].split("async def regenerate_illustration")[0]
    assert "dispatch_with_fallback" in gen_section


# ---- G4: pipeline.regenerate_illustration uses fallback ----

def test_g4_pipeline_regenerate_uses_fallback():
    """pipeline.regenerate_illustration must call dispatch_with_fallback."""
    pipeline_src = (ROOT / "packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py").read_text()
    regen_section = pipeline_src.split("async def regenerate_illustration")[1]
    assert "dispatch_with_fallback" in regen_section


# ---- G5: ProviderExhaustedError class exists ----

def test_g5_provider_exhausted_error_in_exceptions():
    """ProviderExhaustedError must be importable from lingwen_illustrations.exceptions."""
    from lingwen_illustrations.exceptions import ProviderExhaustedError
    assert issubclass(ProviderExhaustedError, Exception)
    err = ProviderExhaustedError(
        "test",
        attempts=[{"provider": "a", "model": "b", "error": "c", "ts": "d"}],
        provider="a",
    )
    assert hasattr(err, "attempts")
    assert len(err.attempts) == 1


# ---- G6: audit_log.record_event receives attempts in extra ----

def test_g6_audit_extra_includes_attempts():
    """pipeline.generate_illustration record_event call must include attempts in extra."""
    pipeline_src = (ROOT / "packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py").read_text()
    gen_section = pipeline_src.split("async def generate_illustration")[1].split("async def regenerate_illustration")[0]
    assert re.search(r'attempts.*=.*\[.*__dict__', gen_section, re.DOTALL), \
        "record_event extra must include attempts list"


# ---- G8: Phase 100 G1-G9 guards preserved ----

def test_g8_phase_100_guard_files_present():
    """Phase 100 multi-model guards live in packages/lingwen-illustrations/tests/ (TDD pattern)."""
    # Phase 100 shipped its guards at the package level (test_phase100_*.py),
    # not at the repo root tests/. Verify the package-level files still exist.
    package_tests = ROOT / "packages/lingwen-illustrations/tests"
    expected = [
        package_tests / "test_phase100_exceptions.py",
        package_tests / "test_phase100_adapter.py",
        package_tests / "test_phase100_pipeline_resolve.py",
    ]
    for f in expected:
        assert f.exists(), f"Phase 100 guard file missing: {f}"


def test_g8b_phase_100_i092_invariant_present():
    """Phase 100 I092 invariant must still be in architecture.yml."""
    with open(ARCHITECTURE_YML) as f:
        arch = yaml.safe_load(f)
    invariants = arch["invariants"]
    if isinstance(invariants, list):
        ids = {entry.get("id") for entry in invariants}
    else:
        ids = set(invariants.keys())
    assert "I092" in ids


# ---- G9: i2i path does NOT enter fallback ----

def test_g9_i2i_path_does_not_call_fallback():
    """i2i branch (reference_image_bytes) must not call dispatch_with_fallback."""
    pipeline_src = (ROOT / "packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py").read_text()
    gen_section = pipeline_src.split("async def generate_illustration")[1].split("async def regenerate_illustration")[0]
    # Extract the i2i if-block (between reference_image_bytes check and else:)
    i2i_block_match = re.search(
        r'if reference_image_bytes is not None:.*?(?=\n    else:)',
        gen_section, re.DOTALL,
    )
    assert i2i_block_match is not None, "i2i branch not found in generate_illustration"
    i2i_block = i2i_block_match.group(0)
    assert "generate_with_reference" in i2i_block
    assert "dispatch_with_fallback" not in i2i_block, \
        "i2i branch must NOT use dispatch_with_fallback (provider-specific models)"


# ---- G10: route maps ProviderExhaustedError → 502 ----

def test_g10_route_maps_provider_exhausted_to_502():
    """STAGE_HTTP_CODES must have ProviderExhaustedError → 502."""
    from apps.studio_api.routes.illustrations import STAGE_HTTP_CODES
    from lingwen_illustrations.exceptions import ProviderExhaustedError
    assert STAGE_HTTP_CODES.get(ProviderExhaustedError) == 502